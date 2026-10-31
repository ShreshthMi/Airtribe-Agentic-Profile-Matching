"""
Measure the screening against human labels, and compare embedding providers.

    python scripts/evaluate.py --providers huggingface ollama

For every job posting with label sheets in evaluation/labels/, and every provider:

  Round 1  the provider's index ranks all resumes          -> P@5, P@10, nDCG@10, R@10
  Round 2  Claude judges that top 10 and re-ranks them      -> P@5, nDCG@10, hire precision

Sheets are named <posting>_<labeller>.csv, where job_descriptions/<posting>.txt is the
posting; make them with scripts/human_eval.py. A candidate's relevance is the mean of the
labellers' grades (0-2); 1 or more counts as relevant. Recall needs a sheet that grades
every resume (human_eval.py template --all); without one it is reported as n/a.

Each provider's index must be built with scripts/build_index.py, so that each is scored on
its own measured similarity band; comparing a calibrated index with an uncalibrated one
would not be fair. This calls Claude: one requirement extraction per posting, and one
judging call per candidate in any provider's top 10 (judgements are shared between
providers, so a candidate both rank highly is judged once).
"""
from __future__ import annotations

import argparse
import math
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from dotenv import load_dotenv  # noqa: E402

import claude_tasks  # noqa: E402
import embedders  # noqa: E402
import human_eval  # noqa: E402
from corpus import Corpus, CorpusError, index_dir  # noqa: E402
from llm import Claude, LLMError  # noqa: E402
from matching_agent import SHORTLIST_SIZE, search_query  # noqa: E402
from screening import rank_by_fit, weighted_requirements  # noqa: E402

RELEVANT_GRADE = 1.0
TOP = SHORTLIST_SIZE
JD_SUFFIXES = (".txt", ".md")


# --------------------------------------------------------------------------- #
# Ranking metrics over a "condensed" list: unlabelled candidates are skipped, and
# how many there were is reported, since a metric over unlabelled data is meaningless.
# --------------------------------------------------------------------------- #
def precision_at(order: list[str], gains: dict[str, float], k: int) -> float | None:
    top = [c for c in order if c in gains][:k]
    return sum(gains[c] >= RELEVANT_GRADE for c in top) / len(top) if top else None


def recall_at(order: list[str], gains: dict[str, float], k: int) -> float | None:
    relevant = {c for c, g in gains.items() if g >= RELEVANT_GRADE}
    top = [c for c in order if c in gains][:k]
    return sum(c in relevant for c in top) / len(relevant) if relevant else None


def ndcg_at(order: list[str], gains: dict[str, float], k: int) -> float | None:
    top = [gains[c] for c in order if c in gains][:k]
    ideal = sorted(gains.values(), reverse=True)[:k]
    ideal_dcg = sum(g / math.log2(i + 2) for i, g in enumerate(ideal))
    return sum(g / math.log2(i + 2) for i, g in enumerate(top)) / ideal_dcg if ideal_dcg else None


# --------------------------------------------------------------------------- #
# Labels
# --------------------------------------------------------------------------- #
def load_labels(folder: Path) -> dict[str, dict[str, dict[str, int]]]:
    """posting -> labeller -> candidate_id -> grade, from <posting>_<labeller>.csv files."""
    labels: dict[str, dict[str, dict[str, int]]] = defaultdict(dict)
    for path in sorted(folder.glob("*.csv")):
        posting, _, labeller = path.stem.rpartition("_")
        if not posting:
            raise ValueError(f"{path.name}: name label sheets <posting>_<labeller>.csv")
        labels[posting][labeller] = human_eval.read_grades(human_eval.read_sheet(path))
    return dict(labels)


def mean_grades(by_labeller: dict[str, dict[str, int]]) -> dict[str, float]:
    graded: dict[str, list[int]] = defaultdict(list)
    for grades in by_labeller.values():
        for cid, grade in grades.items():
            graded[cid].append(grade)
    return {cid: sum(g) / len(g) for cid, g in graded.items()}


# --------------------------------------------------------------------------- #
# One posting, every provider
# --------------------------------------------------------------------------- #
def evaluate_posting(job_description: str, gains: dict[str, float], corpora: dict, claude, today: date,
                     verdicts: dict) -> tuple[dict[str, dict], dict]:
    """Metrics per provider for one posting, and the verdict cache (extended, not modified)."""
    reqs = claude_tasks.extract_requirements(claude, job_description)
    if not weighted_requirements(reqs):
        raise ValueError(f"No requirements found in the posting ({reqs['notes']}).")
    texts = [t for t, _, _ in weighted_requirements(reqs)]
    query = search_query(job_description, reqs)
    results = {}
    for provider, corpus in corpora.items():
        ranking = corpus.search(query, k=corpus.size, must_haves=reqs["must_have"])
        round1 = [c["candidate_id"] for c in ranking]
        top = ranking[:TOP]
        resumes = {c["candidate_id"]: (c["name"], corpus.resume_text(c["candidate_id"])) for c in top}
        verdicts, failures = claude_tasks.judge_candidates(claude, texts, resumes, verdicts, today)
        judged = rank_by_fit([c for c in top if c["candidate_id"] not in failures], reqs, verdicts)
        round2 = [e["candidate_id"] for e in judged] + [c for c in round1[:TOP] if c in failures] + round1[TOP:]
        hires = [e["candidate_id"] for e in judged if e["recommendation"] == "hire" and e["candidate_id"] in gains]
        complete = len(gains) >= corpus.size
        results[provider] = {
            "unlabelled_in_top": sum(c not in gains for c in round1[:TOP]),
            "r1_p5": precision_at(round1, gains, 5), "r1_p10": precision_at(round1, gains, TOP),
            "r1_ndcg10": ndcg_at(round1, gains, TOP),
            "r1_r10": recall_at(round1, gains, TOP) if complete else None,
            "r2_p5": precision_at(round2, gains, 5), "r2_ndcg10": ndcg_at(round2, gains, TOP),
            "hire_precision": (sum(gains[c] >= RELEVANT_GRADE for c in hires) / len(hires)) if hires else None,
            "unjudged": len(failures)}
    return results, verdicts


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #
COLUMNS = [("unlabelled_in_top", "Unlabelled in top 10"), ("r1_p5", "R1 P@5"), ("r1_p10", "R1 P@10"),
           ("r1_ndcg10", "R1 nDCG@10"), ("r1_r10", "R1 R@10"), ("r2_p5", "R2 P@5"), ("r2_ndcg10", "R2 nDCG@10"),
           ("hire_precision", "Hire precision")]


def _cell(value) -> str:
    if value is None:
        return "n/a"
    return str(value) if isinstance(value, int) else f"{value:.2f}"


def render(results: dict[str, dict[str, dict]], labellers: dict[str, list[str]], today: date) -> str:
    header = "| Posting | Provider | " + " | ".join(label for _, label in COLUMNS) + " |"
    lines = [f"# Evaluation against human labels ({today.isoformat()})", "", header,
             "|" + "---|" * (len(COLUMNS) + 2)]
    for posting, by_provider in results.items():
        for provider, m in by_provider.items():
            lines.append(f"| {posting} | {provider} | " + " | ".join(_cell(m[key]) for key, _ in COLUMNS) + " |")
    providers = {p for by_provider in results.values() for p in by_provider}
    for provider in sorted(providers):
        rows = [by_provider[provider] for by_provider in results.values() if provider in by_provider]
        means = {key: [r[key] for r in rows if r[key] is not None] for key, _ in COLUMNS}
        lines.append(f"| **mean** | {provider} | " + " | ".join(
            _cell(sum(v) / len(v) if v else None) if key != "unlabelled_in_top" else _cell(sum(v))
            for key, v in means.items()) + " |")
    lines += ["", "Labellers: " + "; ".join(f"{p}: {', '.join(names)}" for p, names in labellers.items()), "",
              "How to read this:",
              "- R1 is Round 1's ranking on its own; R2 is after Claude's judgements re-rank the top 10. Round 2 "
              "only reorders the top 10, so P@10 and R@10 are the same for both: compare P@5 and nDCG@10.",
              "- Compare providers on R1, which is the only round the embedding model affects. R@10 needs a sheet "
              "grading every resume (human_eval.py template --all).",
              "- Metrics skip candidates nobody graded. If 'Unlabelled in top 10' is not 0, a provider found people "
              "the labellers never saw; grade them too, or the comparison favours the provider the sheets came from.",
              "- A handful of postings and two labellers show a direction, not a statistically significant result."]
    return "\n".join(lines) + "\n"


def find_posting(name: str, folder: Path) -> Path:
    for suffix in JD_SUFFIXES:
        if (folder / f"{name}{suffix}").is_file():
            return folder / f"{name}{suffix}"
    raise ValueError(f"No job description {name}.txt in {folder} for the label sheets named {name}_*.csv")


def main(argv: list[str] | None = None) -> None:
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser(description="Evaluate the screening against human labels.")
    parser.add_argument("--labels", type=Path, default=ROOT / "evaluation" / "labels")
    parser.add_argument("--providers", nargs="+", default=["huggingface"], choices=embedders.PROVIDERS)
    parser.add_argument("--jobs", type=Path, default=ROOT / "job_descriptions")
    parser.add_argument("--out", type=Path, default=ROOT / "evaluation" / "results.md")
    args = parser.parse_args(argv)
    try:
        labels = load_labels(args.labels) if args.labels.is_dir() else {}
        if not labels:
            raise ValueError(f"No label sheets in {args.labels}. Make them with scripts/human_eval.py template.")
        corpora = {}
        for provider in args.providers:
            db = index_dir(provider)
            if not (db / embedders.CALIBRATION_FILE).is_file():
                raise ValueError(f"{db} has no measured similarity band. Build it with:\n"
                                 f"  python scripts/build_index.py --provider {provider}")
            corpora[provider] = Corpus(db_path=db)
        claude, today, verdicts, results = Claude(), date.today(), {}, {}
        for posting, by_labeller in labels.items():
            print(f"evaluating {posting} ({len(by_labeller)} labeller(s)) ...", flush=True)
            jd = find_posting(posting, args.jobs).read_text(encoding="utf-8")
            results[posting], verdicts = evaluate_posting(jd, mean_grades(by_labeller), corpora, claude, today,
                                                          verdicts)
    except (ValueError, CorpusError, LLMError) as exc:
        parser.exit(1, f"error: {exc}\n")
    report = render(results, {p: sorted(by) for p, by in labels.items()}, today)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report)
    print(report)
    print(f"wrote {args.out.relative_to(ROOT)}  (Claude usage: {claude.usage['calls']} calls)")


if __name__ == "__main__":
    main()
