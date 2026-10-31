"""embedders.py, scripts/build_index.py and the provider handling in corpus.py, all offline."""
import hashlib
import importlib.util
import io
import json
import math
import sys
import types
import urllib.error
from pathlib import Path

import pytest

import corpus
import embedders
from corpus import Corpus, CorpusError, index_dir

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("build_index", ROOT / "scripts" / "build_index.py")
build_index = importlib.util.module_from_spec(_spec)
sys.modules["build_index"] = build_index
_spec.loader.exec_module(build_index)


class FakePost:
    """Stands in for embedders._post_json, recording each request."""

    def __init__(self, dims: int = 3):
        self.calls, self.dims = [], dims

    def __call__(self, url, payload, headers, service, hint=""):
        self.calls.append({"url": url, "payload": payload, "headers": headers})
        texts = payload["input"]
        vectors = [[float(len(t)), 1.0, 0.0][: self.dims] for t in texts]
        if "/api/embed" in url:
            return {"embeddings": vectors}
        return {"data": [{"index": i, "embedding": v} for i, v in reversed(list(enumerate(vectors)))]}


# ---- choosing a provider ----------------------------------------------------- #
def test_model_names_carry_the_provider_and_huggingface_names_pass_through():
    assert embedders.model_spec("voyage") == "voyage:voyage-3.5"
    assert embedders.model_spec("huggingface") == "sentence-transformers/all-MiniLM-L6-v2"
    assert embedders.parse_spec("ollama:nomic-embed-text:latest") == ("ollama", "nomic-embed-text:latest")
    assert embedders.parse_spec("BAAI/bge-small-en-v1.5") == ("huggingface", "BAAI/bge-small-en-v1.5")
    with pytest.raises(embedders.EmbeddingError, match="Unknown embedding provider 'cohere'"):
        embedders.model_spec("cohere")


def test_install_swaps_the_embedder_once_and_keeps_milestone2s_for_huggingface(monkeypatch):
    class M2Embedder:
        backend = "sentence-transformers"

        def __init__(self, model_name):
            self.model_name = model_name

        def embed(self, texts):
            return [[1.0, 0.0]] * len(texts)

    monkeypatch.setattr(embedders, "_original_embedder", None)
    a, b = types.SimpleNamespace(Embedder=M2Embedder), types.SimpleNamespace(Embedder=M2Embedder)

    embedders.install(a, b)
    embedders.install(a)

    assert a.Embedder is embedders.Embedder and b.Embedder is embedders.Embedder
    hf = embedders.Embedder("sentence-transformers/all-MiniLM-L6-v2")
    assert hf.backend == "sentence-transformers" and hf.embed(["x"]) == [[1.0, 0.0]]


def test_corpus_has_already_installed_it_into_milestone2():
    assert corpus.resume_rag.Embedder is embedders.Embedder and corpus.job_matcher.Embedder is embedders.Embedder


# ---- the providers ------------------------------------------------------------ #
def test_voyage_marks_documents_and_queries_and_returns_unit_vectors_in_order(monkeypatch):
    post = FakePost()
    monkeypatch.setattr(embedders, "_post_json", post)
    monkeypatch.setenv("VOYAGE_API_KEY", "test-key")
    voyage = embedders.Embedder("voyage:voyage-3.5")

    with embedders.documents():
        docs = voyage.embed(["aa", "bbbb"])
    query = voyage.embed(["c"])

    assert [c["payload"]["input_type"] for c in post.calls] == ["document", "query"]
    assert post.calls[0]["headers"]["Authorization"] == "Bearer test-key"
    assert docs[0][0] < docs[1][0]                          # order kept although the reply was reversed
    assert all(math.isclose(sum(x * x for x in v), 1.0) for v in docs + query)


def test_requests_are_batched(monkeypatch):
    post = FakePost()
    monkeypatch.setattr(embedders, "_post_json", post)
    monkeypatch.setattr(embedders, "BATCH_SIZE", 2)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    vectors = embedders.Embedder("openai:text-embedding-3-small").embed(["a", "b", "c", "d", "e"])

    assert len(vectors) == 5 and [len(c["payload"]["input"]) for c in post.calls] == [2, 2, 1]


def test_ollama_adds_nomic_task_prefixes_and_accepts_a_bare_host(monkeypatch):
    post = FakePost()
    monkeypatch.setattr(embedders, "_post_json", post)
    monkeypatch.setenv("OLLAMA_HOST", "127.0.0.1:11434")

    with embedders.documents():
        embedders.Embedder("ollama:nomic-embed-text").embed(["React apps"])
    embedders.Embedder("ollama:mxbai-embed-large").embed(["React apps"])

    assert post.calls[0]["url"] == "http://127.0.0.1:11434/api/embed"
    assert post.calls[0]["payload"]["input"] == ["search_document: React apps"]
    assert post.calls[1]["payload"]["input"] == ["React apps"]


def test_a_missing_key_says_which_setting_to_add(monkeypatch):
    monkeypatch.delenv("VOYAGE_API_KEY", raising=False)

    with pytest.raises(embedders.EmbeddingError, match="Set VOYAGE_API_KEY in .env"):
        embedders.Embedder("voyage:voyage-3.5").embed(["x"])


def test_network_and_http_failures_become_readable_errors(monkeypatch):
    def refuse(request, timeout):
        raise urllib.error.URLError("Connection refused")
    monkeypatch.setattr(embedders.urllib.request, "urlopen", refuse)
    with pytest.raises(embedders.EmbeddingError, match=r"Could not reach Ollama \(Connection refused\)\. Is `ollama"):
        embedders.Embedder("ollama:nomic-embed-text").embed(["x"])

    def not_found(request, timeout):
        raise urllib.error.HTTPError(request.full_url, 404, "Not Found", {}, io.BytesIO(b'{"error":"model not found"}'))
    monkeypatch.setattr(embedders.urllib.request, "urlopen", not_found)
    with pytest.raises(embedders.EmbeddingError, match="returned an error \\(404\\).*model not found.*ollama pull"):
        embedders.Embedder("ollama:nomic-embed-text").embed(["x"])


# ---- calibration ---------------------------------------------------------------- #
def test_calibration_takes_percentiles_of_milestone2s_raw_score():
    hits = {f"c{i}": [{"similarity": i / 20}] for i in range(20)}  # raw score = similarity for one hit
    matcher = types.SimpleNamespace(collection=types.SimpleNamespace(count=lambda: 20),
                                    semantic_search=lambda jd, n_chunks: hits)

    band = embedders.calibrate(matcher, ["jd one"])

    assert band["floor"] == 0.05 and band["ceil"] == 0.9 and band["scores"] == 20


def test_calibration_refuses_too_little_data():
    matcher = types.SimpleNamespace(collection=types.SimpleNamespace(count=lambda: 1),
                                    semantic_search=lambda jd, n_chunks: {"a": [{"similarity": 0.5}]})

    with pytest.raises(embedders.EmbeddingError, match="Too few similarity scores"):
        embedders.calibrate(matcher, ["jd"])


# ---- building an index end to end, with a fake provider ------------------------- #
class HashedWords(embedders._Client):
    """A deterministic bag-of-words embedding, so a real index can be built offline."""

    def _embed_batch(self, texts):
        vectors = []
        for text in texts:
            v = [0.0] * 64
            for word in text.lower().split():
                v[int(hashlib.md5(word.encode()).hexdigest(), 16) % 64] += 1.0
            vectors.append(v)
        return vectors


def test_build_index_writes_an_index_and_its_calibration(tmp_path, monkeypatch):
    monkeypatch.setattr(embedders, "PROVIDERS", embedders.PROVIDERS + ("fake",))
    monkeypatch.setattr(embedders, "CLIENTS", {**embedders.CLIENTS, "fake": HashedWords})
    resumes, jds = tmp_path / "resumes", tmp_path / "jds"
    resumes.mkdir()
    jds.mkdir()
    for i, skill in enumerate(["React", "Java", "Python", "Kotlin", "Go"]):
        (resumes / f"person_{i}.md").write_text(f"# Person {i}\n\n## Experience\nEngineer, Acme\nJan 2020 - Present\n"
                                                f"- Built {skill} services.\n\n## Skills\n{skill}\n")
    (jds / "a.txt").write_text("React engineer\nRequirements\n- React")
    (jds / "b.txt").write_text("Java engineer\nRequirements\n- Java")

    band = build_index.build("fake", "words-v1", resumes, tmp_path / "db", None, jds)

    registry = json.loads((tmp_path / "db" / "candidates.json").read_text())
    assert registry["model"] == "fake:words-v1" and len(registry["candidates"]) == 5
    assert json.loads((tmp_path / "db" / "calibration.json").read_text()) == band
    opened = Corpus(root=tmp_path, db_path=tmp_path / "db")
    assert opened.band == (band["floor"], band["ceil"])
    assert opened.search("React engineer", k=1)[0]["candidate_id"] == "person_0"


# ---- corpus: which index, which band ---------------------------------------------- #
def test_each_provider_has_its_own_index_folder(monkeypatch):
    assert index_dir("huggingface").name == "chroma_db" and index_dir("voyage").name == "chroma_db_voyage"
    monkeypatch.setenv("EMBEDDING_PROVIDER", "Ollama ")
    assert corpus.provider_from_env() == "ollama"
    with pytest.raises(CorpusError, match="Unknown EMBEDDING_PROVIDER 'cohere'"):
        index_dir("cohere")


def _index(tmp_path: Path, calibration: str | None = None) -> Path:
    db = tmp_path / "db"
    db.mkdir()
    (db / "candidates.json").write_text(json.dumps({"candidates": [{"candidate_name": "Ana",
                                                                    "resume_path": "resumes/ana.md"}]}))
    if calibration is not None:
        (db / "calibration.json").write_text(calibration)
    return db


def test_an_index_without_calibration_keeps_milestone2s_band(tmp_path):
    assert Corpus(root=tmp_path, db_path=_index(tmp_path)).band == (0.15, 0.65)


def test_a_broken_calibration_file_is_reported(tmp_path):
    with pytest.raises(CorpusError, match="calibration.json is unreadable"):
        Corpus(root=tmp_path, db_path=_index(tmp_path, "{oops"))


def test_search_applies_this_indexs_band_and_reports_provider_failures(tmp_path):
    opened = Corpus(root=tmp_path, db_path=_index(tmp_path, '{"floor": 0.3, "ceil": 0.7}'))
    seen = {}

    def match(query, **kwargs):
        seen["band"] = (corpus.job_matcher.SIM_FLOOR, corpus.job_matcher.SIM_CEIL)
        raise embedders.EmbeddingError("Could not reach Voyage AI")
    opened._matcher = types.SimpleNamespace(match=match)

    with pytest.raises(CorpusError, match="Could not reach Voyage AI"):
        opened.search("React")
    assert seen["band"] == (0.3, 0.7)


def test_build_index_command_reports_an_unreachable_provider_without_a_traceback(tmp_path, monkeypatch, capsys):
    def refuse(request, timeout):
        raise urllib.error.URLError("Connection refused")
    monkeypatch.setattr(embedders.urllib.request, "urlopen", refuse)
    resumes = tmp_path / "resumes"
    resumes.mkdir()
    (resumes / "ana.md").write_text("# Ana\n\n## Experience\nEngineer, Acme\nJan 2020 - Present\n- Built React apps.\n")

    with pytest.raises(SystemExit) as exit_info:
        build_index.main(["--provider", "ollama", "--resumes", str(resumes), "--db", str(tmp_path / "db")])

    assert exit_info.value.code == 1
    assert "error: Could not reach Ollama (Connection refused). Is `ollama serve` running" in capsys.readouterr().err
