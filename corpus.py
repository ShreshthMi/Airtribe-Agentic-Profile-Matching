"""
The resume corpus, seen through the two earlier milestones.

* Milestone 1's file tools - read_file, list_files, search_in_file, write_file - read and
  write files inside a sandbox folder, refusing '..', absolute paths and hidden files.
* Milestone 2's hybrid RAG search (JobMatcher) ranks every resume against a query using
  embeddings in ChromaDB, BM25 and exact skill matching.

Both are vendored unchanged in milestone2_rag/ (see its PROVENANCE.md). This file is the
only one that imports them, and it narrows the file tools further: the agent may read
resumes, job descriptions and reports, and may write only into reports/.

Round 1 can use any embedding provider in embedders.py. EMBEDDING_PROVIDER in .env picks
which index is opened (chroma_db for Milestone 2's MiniLM, chroma_db_<provider> for the
others); the index itself records the model it was built with.
"""
from __future__ import annotations

import json
import os
import sys
import threading
from collections import Counter
from pathlib import Path, PurePosixPath

PROJECT_ROOT = Path(__file__).resolve().parent
MILESTONE2_DIR = PROJECT_ROOT / "milestone2_rag"
READABLE_FOLDERS = ("resumes", "job_descriptions", "reports")
WRITABLE_FOLDER = "reports"
ROUND1_SIZE = 10

# The vendored modules import each other by top-level name (`from resume_rag import ...`),
# so their folders go on sys.path instead of being edited into a package.
sys.path.insert(0, str(MILESTONE2_DIR))
import job_matcher  # noqa: E402
import resume_loader  # noqa: E402
import resume_rag  # noqa: E402
from job_matcher import JobMatcher, parse_requirement  # noqa: E402
from resume_rag import extract_skills  # noqa: E402

sys.path.insert(0, str(resume_loader.tools_dir()))
import fs_tools  # noqa: E402

import embedders  # noqa: E402

embedders.install(resume_rag, job_matcher)  # Milestone 2 now builds its embedder through embedders.py
MILESTONE2_BAND = (job_matcher.SIM_FLOOR, job_matcher.SIM_CEIL)  # hand-set for MiniLM in Milestone 2

# Milestone 1 reads its sandbox folder from a process-wide environment variable, which
# sandbox_root() sets and restores. Round 2 runs in threads, so every use takes this lock.
_SANDBOX = threading.Lock()


class CorpusError(Exception):
    """The resume index is missing, or a resume could not be read."""


def index_dir(provider: str, root: Path = PROJECT_ROOT) -> Path:
    """Where the index for an embedding provider lives; MiniLM keeps Milestone 2's folder."""
    if provider not in embedders.PROVIDERS:
        raise CorpusError(f"Unknown EMBEDDING_PROVIDER {provider!r}; use one of {', '.join(embedders.PROVIDERS)}.")
    return Path(root) / ("chroma_db" if provider == "huggingface" else f"chroma_db_{provider}")


def provider_from_env() -> str:
    return (os.environ.get("EMBEDDING_PROVIDER") or "huggingface").strip().lower()


class Corpus:
    def __init__(self, root: Path = PROJECT_ROOT, db_path: Path | None = None):
        self.root = Path(root)
        self.db_path = Path(db_path) if db_path else index_dir(provider_from_env(), self.root)
        registry_file = self.db_path / "candidates.json"
        if not registry_file.is_file():
            raise CorpusError(f"No resume index at {self.db_path}. Build it first:\n"
                              f"  python scripts/build_index.py --provider {provider_from_env()}")
        try:
            entries = json.loads(registry_file.read_text())["candidates"]
        except (json.JSONDecodeError, KeyError, OSError) as exc:
            raise CorpusError(f"The resume index at {registry_file} is unreadable ({exc}); rebuild it.") from exc
        # Candidate ids are resume file names without the extension ("grace_liu"):
        # readable in a chat, and unlike names (two people here share one) unique.
        stems = Counter(Path(c["resume_path"]).stem for c in entries)
        if clashes := sorted(stem for stem, n in stems.items() if n > 1):
            raise CorpusError(f"Several resumes share a file name, so their ids would collide: {clashes}")
        self.candidates = {Path(c["resume_path"]).stem: c for c in entries}
        self.band = self._similarity_band()
        self._matcher = None

    def _similarity_band(self) -> tuple[float, float]:
        """The index's measured similarity band (embedders.calibrate), else Milestone 2's."""
        calibration = self.db_path / embedders.CALIBRATION_FILE
        if not calibration.is_file():
            return MILESTONE2_BAND
        try:
            band = json.loads(calibration.read_text())
            return float(band["floor"]), float(band["ceil"])
        except (json.JSONDecodeError, KeyError, TypeError, ValueError, OSError) as exc:
            raise CorpusError(f"{calibration} is unreadable ({exc}); rebuild the index.") from exc

    # ---- who is in the corpus -------------------------------------------- #
    @property
    def size(self) -> int:
        return len(self.candidates)

    def name(self, candidate_id: str) -> str:
        return self.candidates[candidate_id]["candidate_name"]

    def find(self, name_or_id: str) -> list[str]:
        """Candidate ids matching an id, a full name, or a unique part of a name."""
        wanted = name_or_id.strip().lower()
        if wanted in self.candidates:
            return [wanted]
        exact = [cid for cid, c in self.candidates.items() if c["candidate_name"].lower() == wanted]
        return exact or [cid for cid, c in self.candidates.items() if wanted in c["candidate_name"].lower()]

    def resume_text(self, candidate_id: str) -> str:
        result = self.read_file(self.candidates[candidate_id]["resume_path"])
        if not result.get("success"):
            raise CorpusError(f"Could not read the resume for {candidate_id}: {result.get('error')}")
        return result["content"]

    # ---- Milestone 2: RAG search (Round 1) --------------------------------- #
    @property
    def matcher(self) -> JobMatcher:
        if self._matcher is None:  # loading the embedding model takes a few seconds, so only once
            try:
                self._matcher = JobMatcher(self.db_path)
            except embedders.EmbeddingError as exc:
                raise CorpusError(str(exc)) from exc
        return self._matcher

    def search(self, query: str, k: int = ROUND1_SIZE, must_haves: list[str] = ()) -> list[dict]:
        """Rank every resume against `query` and return the top `k`.

        Must-haves are passed to Milestone 2 only to annotate each candidate with its rule
        checks; nobody is filtered out, because those checks rest on a fixed skill
        vocabulary and date arithmetic that Round 2 exists to improve on.
        """
        checkable = [m for m in must_haves if parse_requirement(m)]
        critical = list(dict.fromkeys(s for m in must_haves for s in extract_skills(m))) or None
        matcher = self.matcher
        # Milestone 2 reads its similarity band from module globals; set this index's band
        # before every search, since another index (another model) may have set its own.
        job_matcher.SIM_FLOOR, job_matcher.SIM_CEIL = self.band
        try:
            result = matcher.match(query, k=k, must_haves=checkable, auto_requirements=False,
                                   critical_skills=critical, apply_filters=False)
        except embedders.EmbeddingError as exc:
            raise CorpusError(str(exc)) from exc
        return [{"candidate_id": Path(m["resume_path"]).stem, "name": m["candidate_name"],
                 "resume_path": m["resume_path"], "rag_score": m["match_score"],
                 "experience_years": m["experience_years"], "matched_skills": m["matched_skills"],
                 "rule_check_failures": m["failed_requirements"]} for m in result["top_matches"]]

    # ---- Milestone 1: file tools ------------------------------------------ #
    def read_file(self, filepath: str) -> dict:
        refused = self._refuse(filepath, READABLE_FOLDERS)
        if refused:
            return refused
        with _SANDBOX, resume_loader.sandbox_root(self.root):
            return fs_tools.read_file(filepath)

    def list_files(self, directory: str, extension: str | None = None) -> list[dict]:
        refused = self._refuse(f"{directory.rstrip('/')}/x", READABLE_FOLDERS)
        if refused:
            return [{"error": refused["error"]}]
        with _SANDBOX, resume_loader.sandbox_root(self.root):
            return fs_tools.list_files(directory, extension or None)

    def search_in_file(self, filepath: str, keyword: str) -> dict:
        refused = self._refuse(filepath, READABLE_FOLDERS)
        if refused:
            return refused
        with _SANDBOX, resume_loader.sandbox_root(self.root):
            return fs_tools.search_in_file(filepath, keyword)

    def write_file(self, filepath: str, content: str) -> dict:
        """Save a new file into reports/. Existing files are never replaced, so neither a tool
        call nor a later session can rewrite a screening report after the fact."""
        refused = self._refuse(filepath, (WRITABLE_FOLDER,))
        if refused:
            return refused
        if self.exists(filepath):
            return {"success": False, "filepath": filepath, "error": f"{filepath} already exists; choose a new name"}
        (self.root / WRITABLE_FOLDER).mkdir(exist_ok=True)
        with _SANDBOX, resume_loader.sandbox_root(self.root):
            return fs_tools.write_file(filepath, content)

    def exists(self, filepath: str) -> bool:
        return self._refuse(filepath, READABLE_FOLDERS) is None and (self.root / filepath).is_file()

    @staticmethod
    def _refuse(filepath: str, folders: tuple[str, ...]) -> dict | None:
        """An error result unless `filepath` is inside one of `folders`.

        Milestone 1 still enforces its own sandbox ('..', symlinks, hidden files); this
        only keeps the agent away from the project's code and configuration.
        """
        parts = PurePosixPath(str(filepath).replace("\\", "/")).parts
        if len(parts) >= 2 and parts[0] in folders and ".." not in parts:
            return None
        allowed = ", ".join(f"{f}/" for f in folders)
        return {"success": False, "filepath": str(filepath), "error": f"Access is limited to {allowed}"}
