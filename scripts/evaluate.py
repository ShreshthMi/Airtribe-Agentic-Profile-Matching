"""
Measure the screening against human labels, and compare embedding providers.

    python scripts/evaluate.py --providers huggingface ollama
    python scripts/evaluate.py --providers huggingface ollama --make-sheets A B --postings real_sre real_data

For every job posting with label sheets in evaluation/labels/, and every provider:

  Round 1  the provider's index ranks all resumes          -> P@5, P@10, nDCG@10, R@10
  Round 2  Claude judges that top 10 and re-ranks them      -> P@5, nDCG@10, hire precision

Sheets are named <posting>_<labeller>.csv, where job_descriptions/<posting>.txt is the
posting. A candidate's relevance is the mean of the labellers' grades (0-2); 1 or more
counts as relevant. Recall needs a sheet that grades every resume (human_eval.py template
--all); without one it is reported as n/a.

Two things are held fixed so the labels match what is measured. Each posting's
requirements are extracted once and frozen in evaluation/private/requirements/, since a
second extraction can word them differently and so change the ranking. And --make-sheets
writes a shortlist sheet that pools every compared provider's top 10, so no provider is
measured on candidates nobody graded.

Each provider's index must be built with scripts/build_index.py, so that each is scored on
its own measured similarity band; comparing a calibrated index with an uncalibrated one
would not be fair. This calls Claude: one requirement extraction per posting, and one
judging call per candidate in any provider's top 10 (judgements are shared between
providers, so a candidate both rank highly is judged once).
"""
from __future__ import annotations

import argparse
import json
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
REQUIREMENTS_DIR = ROOT / "evaluation" / "private" / "requirements"


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
    """posting -> labeller -> candidate_id -> grade, from <posting>_<labeller>.csv files.

    Sheets nobody has started are skipped with a note, so the evaluation can run on the
    labellers who have finished; a sheet that is started but has a problem stops it.
    """
    labels: dict[str, dict[str, dict[str, int]]] = defaultdict(dict)
    ungraded = []
    for path in sorted(folder.glob("*.csv")):
        posting, _, labeller = path.stem.rpartition("_")
        if not posting:
            raise ValueError(f"{path.name}: name label sheets <posting>_<labeller>.csv")
        try:
            labels[posting][labeller] = human_eval.grades_from(path)
        except human_eval.UngradedSheet:
            ungraded.append(path.name)
    if ungraded and not labels:
        raise ValueError(f"None of the {len(ungraded)} sheets in {folder.name}/ has been graded yet. Send the "
                         "labelling packs in evaluation/private/packs/ and save the returned sheets over these.")
    if ungraded:
        print(f"skipping {len(ungraded)} sheet(s) not graded yet: {', '.join(ungraded)}", flush=True)
    return dict(labels)


def mean_grades(by_labeller: dict[str, dict[str, int]]) -> dict[str, float]:
    graded: dict[str, list[int]] = defaultdict(list)
    for grades in by_labeller.values():
        for cid, grade in grades.items():
            graded[cid].append(grade)
    return {cid: sum(g) / len(g) for cid, g in graded.items()}


# --------------------------------------------------------------------------- #
# Frozen requirements and pooled shortlists
# --------------------------------------------------------------------------- #
def frozen_requirements(posting: str, job_description: str, claude, folder: Path = REQUIREMENTS_DIR) -> dict:
    """The posting's requirements: extracted on first use, then read back unchanged every time."""
    path = folder / f"{posting}.json"
    if path.is_file():
        return json.loads(path.read_text())
    reqs = claude_tasks.extract_requirements(claude, job_description)
    if not weighted_requirements(reqs):
        raise ValueError(f"No requirements found in {posting} ({reqs['notes']}).")
    folder.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(reqs, indent=2, ensure_ascii=False) + "\n")
    return reqs


def pooled_shortlist(job_description: str, reqs: dict, corpora: dict) -> list[dict]:
    """Everyone any provider ranks in its Round 1 top 10: the candidates a shortlist sheet must cover."""
    pool = {}
    for corpus in corpora.values():
        for c in corpus.search(search_query(job_description, reqs), k=TOP, must_haves=reqs["must_have"]):
            pool.setdefault(c["candidate_id"], c)
    return list(pool.values())


def write_sheets(posting: str, candidates: list[dict], labellers: list[str], folder: Path) -> list[Path]:
    """Blank sheets for each labeller; refuses to overwrite one that already has grades."""
    paths = [folder / f"{posting}_{who}.csv" for who in labellers]
    for path in paths:
        if path.is_file() and any((row.get("human_grade") or "").strip() for row in human_eval.read_sheet(path)):
            raise ValueError(f"{path} already has grades; not overwriting it.")
    folder.mkdir(parents=True, exist_ok=True)
    for path in paths:
        with path.open("w", newline="", encoding="utf-8") as f:
            human_eval.write_template(candidates, f)
    return paths


# --------------------------------------------------------------------------- #
# One posting, every provider
# --------------------------------------------------------------------------- #
def evaluate_posting(job_description: str, reqs: dict, gains: dict[str, float], corpora: dict, claude, today: date,
                     verdicts: dict) -> tuple[dict[str, dict], dict]:
    """Metrics per provider for one posting, and the verdict cache (extended, not modified)."""
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
        labelled = [e for e in judged if e["candidate_id"] in gains]
        complete = len(gains) >= corpus.size
        results[provider] = {
            "unlabelled_in_top": sum(c not in gains for c in round1[:TOP]),
            "r1_p5": precision_at(round1, gains, 5), "r1_p10": precision_at(round1, gains, TOP),
            "r1_ndcg10": ndcg_at(round1, gains, TOP),
            "r1_r10": recall_at(round1, gains, TOP) if complete else None,
            "r2_p5": precision_at(round2, gains, 5), "r2_ndcg10": ndcg_at(round2, gains, TOP),
            "hire_precision": (sum(gains[c] >= RELEVANT_GRADE for c in hires) / len(hires)) if hires else None,
            # Round 3 against people: the agent's hire / borderline / no hire as 2 / 1 / 0, versus the
            # labellers' mean grade rounded to the nearest whole grade
            "r3_agreement": (sum(human_eval.AGENT_GRADE[e["recommendation"]] == round(gains[e["candidate_id"]])
                                 for e in labelled) / len(labelled)) if labelled else None,
            "unjudged": len(failures)}
    return results, verdicts


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #
COLUMNS = [("unlabelled_in_top", "Unlabelled in top 10"), ("r1_p5", "R1 P@5"), ("r1_p10", "R1 P@10"),
           ("r1_ndcg10", "R1 nDCG@10"), ("r1_r10", "R1 R@10"), ("r2_p5", "R2 P@5"), ("r2_ndcg10", "R2 nDCG@10"),
           ("hire_precision", "Hire precision"), ("r3_agreement", "R3 agreement")]


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
              "- Hire precision: of the agent's Hire calls, the share the labellers graded 1 or 2. R3 agreement: how "
              "often the agent's hire / borderline / no hire equals the labellers' rounded mean grade.",
              "- Metrics skip candidates nobody graded. If 'Unlabelled in top 10' is not 0, a provider found people "
              "the labellers never saw; grade them too, or the comparison favours the provider the sheets came from.",
              "- A handful of postings and two labellers show a direction, not a statistically significant result."]
    return "\n".join(lines) + "\n"


def find_posting(name: str, folder: Path) -> Path:
    for suffix in JD_SUFFIXES:
        if (folder / f"{name}{suffix}").is_file():
            return folder / f"{name}{suffix}"
    raise ValueError(f"No job description {name}.txt in {folder} for the label sheets named {name}_*.csv")


def _shown(path: Path) -> str:
    """A path relative to the project when it is inside it, for shorter messages."""
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def open_corpora(providers: list[str]) -> dict:
    """Each provider's index; refuses one without a measured similarity band, since that comparison is unfair."""
    corpora = {}
    for provider in providers:
        db = index_dir(provider)
        if not (db / embedders.CALIBRATION_FILE).is_file():
            raise ValueError(f"{db} has no measured similarity band. Build it with:\n"
                             f"  python scripts/build_index.py --provider {provider}")
        corpora[provider] = Corpus(db_path=db)
    return corpora


def make_sheets(args, corpora: dict, claude) -> None:
    for posting in args.postings:
        jd = find_posting(posting, args.jobs).read_text(encoding="utf-8")
        candidates = pooled_shortlist(jd, frozen_requirements(posting, jd, claude, REQUIREMENTS_DIR), corpora)
        for path in write_sheets(posting, candidates, args.make_sheets, args.labels):
            print(f"wrote {_shown(path)} ({len(candidates)} candidates, pooled from "
                  f"{', '.join(corpora)})")


def run_evaluation(args, corpora: dict, claude) -> str:
    labels = load_labels(args.labels) if args.labels.is_dir() else {}
    if not labels:
        raise ValueError(f"No label sheets in {args.labels}. Make them with scripts/human_eval.py template.")
    today, verdicts, results = date.today(), {}, {}
    for posting, by_labeller in labels.items():
        print(f"evaluating {posting} ({len(by_labeller)} labeller(s)) ...", flush=True)
        jd = find_posting(posting, args.jobs).read_text(encoding="utf-8")
        reqs = frozen_requirements(posting, jd, claude, REQUIREMENTS_DIR)
        results[posting], verdicts = evaluate_posting(jd, reqs, mean_grades(by_labeller), corpora, claude, today,
                                                      verdicts)
    report = render(results, {p: sorted(by) for p, by in labels.items()}, today)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report)
    return report


def main(argv: list[str] | None = None) -> None:
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser(description="Evaluate the screening against human labels.")
    parser.add_argument("--labels", type=Path, default=ROOT / "evaluation" / "labels")
    parser.add_argument("--providers", nargs="+", default=["huggingface"], choices=embedders.PROVIDERS)
    parser.add_argument("--jobs", type=Path, default=ROOT / "job_descriptions")
    parser.add_argument("--out", type=Path, default=ROOT / "evaluation" / "results.md")
    parser.add_argument("--make-sheets", nargs="+", metavar="LABELLER",
                        help="instead of evaluating, write blank pooled shortlist sheets for these labellers")
    parser.add_argument("--postings", nargs="+", default=[], help="postings to make sheets for (with --make-sheets)")
    args = parser.parse_args(argv)
    if args.make_sheets and not args.postings:
        parser.error("--make-sheets needs --postings")
    claude = None
    try:
        corpora = open_corpora(args.providers)
        claude = Claude()
        if args.make_sheets:
            make_sheets(args, corpora, claude)
        else:
            print(run_evaluation(args, corpora, claude))
            print(f"wrote {_shown(args.out)}")
    except (ValueError, CorpusError, LLMError) as exc:
        parser.exit(1, f"error: {exc}\n")
    finally:
        if claude is not None:
            print(f"(Claude usage: {claude.usage['calls']} calls)")


if __name__ == "__main__":
    main()
