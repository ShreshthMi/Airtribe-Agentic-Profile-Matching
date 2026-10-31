"""
Build the resume index for Round 1 with any embedding provider (see embedders.py).

    python scripts/build_index.py                                   # EMBEDDING_PROVIDER, default huggingface
    python scripts/build_index.py --provider ollama                 # into chroma_db_ollama
    python scripts/build_index.py --provider voyage --model voyage-3.5

It runs Milestone 2's build_index() with the provider's model, then measures that model's
similarity band over the job descriptions (embedders.calibrate) and saves it beside the
index, so every provider is scored on its own scale.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

import corpus  # noqa: E402  (installs the provider-aware Embedder into Milestone 2)
import embedders  # noqa: E402


def job_description_texts(folder: Path) -> list[str]:
    files = sorted(p for p in folder.iterdir() if p.suffix in (".txt", ".md") and not p.name.startswith("."))
    return [p.read_text(encoding="utf-8") for p in files]


def build(provider: str, model: str | None, resumes: Path, db: Path, as_of: date | None, calibrate_with: Path) -> dict:
    """Build the index and its calibration; return the calibration."""
    spec = embedders.model_spec(provider, model)
    with embedders.documents():
        report = corpus.resume_rag.build_index(resumes, db, spec, reset=True, today=as_of)
    print(f"Indexed {len(report.records)} resumes / {report.chunk_count} chunks into {db} with {spec}")
    texts = job_description_texts(calibrate_with)
    band = embedders.calibrate(corpus.JobMatcher(db), texts)
    (db / embedders.CALIBRATION_FILE).write_text(json.dumps(band, indent=2) + "\n")
    print(f"Similarity band {band['floor']} - {band['ceil']}, from {band['scores']} scores over "
          f"{len(texts)} job descriptions")
    return band


def main(argv: list[str] | None = None) -> None:
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser(description="Build the Round 1 resume index with an embedding provider.")
    parser.add_argument("--provider", default=corpus.provider_from_env(), choices=embedders.PROVIDERS)
    parser.add_argument("--model", help="model name; defaults to " + ", ".join(
        f"{p}: {m}" for p, m in embedders.DEFAULT_MODELS.items()))
    parser.add_argument("--resumes", type=Path, default=ROOT / "resumes")
    parser.add_argument("--db", type=Path, help="index folder; defaults to chroma_db or chroma_db_<provider>")
    parser.add_argument("--as-of", type=date.fromisoformat, help="reference date for 'Present' roles (YYYY-MM-DD)")
    parser.add_argument("--calibrate-with", type=Path, default=ROOT / "job_descriptions",
                        help="folder of job descriptions used to measure the similarity band")
    args = parser.parse_args(argv)
    db = args.db or corpus.index_dir(args.provider)
    try:
        build(args.provider, args.model, args.resumes, db, args.as_of, args.calibrate_with)
    except embedders.EmbeddingError as exc:
        parser.exit(1, f"error: {exc}\n")


if __name__ == "__main__":
    main()
