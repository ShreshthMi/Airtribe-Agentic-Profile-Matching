"""
Blind human labelling of a screening round: the independent check Milestone 2's review asked for.

1. Make a labelling sheet. Candidates are listed alphabetically, with no rank, score or
   verdict, so the labeller is not anchored on what the agent concluded:
     python scripts/human_eval.py template reports/<round>.json > real_frontend_alice.csv
     python scripts/human_eval.py template --all > real_frontend_all_alice.csv   # every resume: needed for recall
2. Each labeller fills in human_grade on their own copy, without seeing the agent's output:
     2 = would interview, 1 = borderline, 0 = would not interview
3. Check the labellers agree with each other before trusting their labels:
     python scripts/human_eval.py agreement real_frontend_alice.csv real_frontend_bob.csv
4. Score the agent's recommendations against each labeller, and against the rows they agree on:
     python scripts/human_eval.py score reports/<round>.json real_frontend_alice.csv real_frontend_bob.csv

scripts/evaluate.py uses the same sheets to measure the rankings themselves (precision,
recall, nDCG) and to compare embedding providers.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COLUMNS = ["candidate_id", "name", "resume_path", "human_grade", "notes"]
GRADES = (0, 1, 2)
AGENT_GRADE = {"hire": 2, "borderline": 1, "no_hire": 0}
# Landis and Koch's reading of kappa, the usual yardstick for agreement between annotators
KAPPA_BANDS = ((0.8, "almost perfect"), (0.6, "substantial"), (0.4, "moderate"), (0.2, "fair"), (0.0, "slight"))
MAX_PROBLEMS_LISTED = 10


class UngradedSheet(ValueError):
    """A sheet nobody has started: every human_grade is still blank."""


# --------------------------------------------------------------------------- #
# Sheets
# --------------------------------------------------------------------------- #
def write_template(candidates: list[dict], out) -> None:
    """A blank sheet; `candidates` need candidate_id, name and resume_path."""
    writer = csv.DictWriter(out, fieldnames=COLUMNS)
    writer.writeheader()
    for c in sorted(candidates, key=lambda c: c["candidate_id"]):
        writer.writerow({"candidate_id": c["candidate_id"], "name": c["name"], "resume_path": c["resume_path"],
                         "human_grade": "", "notes": ""})


def all_candidates(db: Path) -> list[dict]:
    """Every resume in an index, for a sheet that covers the whole corpus."""
    entries = json.loads((db / "candidates.json").read_text())["candidates"]
    return [{"candidate_id": Path(e["resume_path"]).stem, "name": e["candidate_name"],
             "resume_path": e["resume_path"]} for e in entries]


def read_sheet(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_grades(rows: list[dict], required: set[str] = frozenset()) -> dict[str, int]:
    """Grades by candidate_id. Refuses blanks, grades other than 0/1/2, repeats, and missing required rows."""
    grades, problems = {}, []
    for line, row in enumerate(rows, start=2):
        cid, grade = (row.get("candidate_id") or "").strip(), (row.get("human_grade") or "").strip()
        if cid in grades:
            problems.append(f"line {line}: {cid} is graded twice")
        elif grade not in {"0", "1", "2"}:
            problems.append(f"line {line}: human_grade for {cid or '?'} must be 0, 1 or 2, not {grade!r}")
        else:
            grades[cid] = int(grade)
    listed = {(row.get("candidate_id") or "").strip() for row in rows}
    problems += [f"no row for {cid}" for cid in sorted(required - listed)]
    if len(problems) > MAX_PROBLEMS_LISTED:
        problems = problems[:MAX_PROBLEMS_LISTED] + [f"... and {len(problems) - MAX_PROBLEMS_LISTED} more"]
    if problems:
        raise ValueError("The labelling sheet has problems:\n  " + "\n  ".join(problems))
    return grades


def grades_from(path: Path, required: set[str] = frozenset()) -> dict[str, int]:
    """Grades from one sheet file. Errors name the file; a sheet nobody has started is one line."""
    rows = read_sheet(path)
    if rows and not any((row.get("human_grade") or "").strip() for row in rows):
        raise UngradedSheet(f"{_shown(path)} hasn't been graded yet: all {len(rows)} rows are blank.")
    try:
        return read_grades(rows, required)
    except ValueError as exc:
        raise ValueError(f"{_shown(path)}: {exc}") from exc


def _shown(path: Path) -> str:
    """A path relative to the project when it is inside it, for shorter messages."""
    path = path.resolve()
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


# --------------------------------------------------------------------------- #
# Agreement between two labellers
# --------------------------------------------------------------------------- #
def cohens_kappa(a: list[int], b: list[int], weighted: bool = False) -> float:
    """Agreement beyond chance between two graders: 1 is perfect, 0 is what chance alone gives.

    The weighted form (quadratic weights) treats grades as ordered, so a 2-versus-0
    disagreement costs four times a 2-versus-1. With 0/1/2 grades that is usually the
    fairer of the two; both are reported.
    """
    n = len(a)
    if n == 0 or n != len(b):
        raise ValueError("kappa needs two equally long, non-empty lists of grades")
    observed = Counter(zip(a, b))
    count_a, count_b = Counter(a), Counter(b)

    def weight(i: int, j: int) -> float:
        if weighted:
            return (i - j) ** 2 / (len(GRADES) - 1) ** 2
        return 0.0 if i == j else 1.0

    disagreement = sum(weight(i, j) * observed[(i, j)] / n for i in GRADES for j in GRADES)
    by_chance = sum(weight(i, j) * (count_a[i] / n) * (count_b[j] / n) for i in GRADES for j in GRADES)
    return 1.0 if by_chance == 0 else 1 - disagreement / by_chance


def kappa_reading(kappa: float) -> str:
    return next((label for floor, label in KAPPA_BANDS if kappa > floor), "no better than chance")


def agreement(first: dict[str, int], second: dict[str, int], names: tuple[str, str]) -> str:
    shared = sorted(first.keys() & second.keys())
    if not shared:
        raise ValueError("The two sheets have no candidates in common.")
    a, b = [first[c] for c in shared], [second[c] for c in shared]
    plain, weighted = cohens_kappa(a, b), cohens_kappa(a, b, weighted=True)
    same = sum(x == y for x, y in zip(a, b))
    lines = [f"{len(shared)} candidates graded by both {names[0]} and {names[1]}",
             f"Same grade: {same}/{len(shared)} ({same / len(shared):.0%})",
             f"Cohen's kappa: {plain:.2f} ({kappa_reading(plain)})",
             f"Weighted kappa: {weighted:.2f} ({kappa_reading(weighted)})"]
    far_apart = [c for c in shared if abs(first[c] - second[c]) == 2]
    if far_apart:
        lines += ["", "Graded 2 by one and 0 by the other - discuss these before re-grading:",
                  *[f"  {c}: {names[0]} {first[c]}, {names[1]} {second[c]}" for c in far_apart]]
    if weighted < 0.4:
        lines += ["", "Agreement is too low to judge the agent against. Talk through a few of the "
                      "disagreements, agree on how to read the rubric, and grade again."]
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# The agent against the labels
# --------------------------------------------------------------------------- #
def score(report: dict, grades: dict[str, int], who: str) -> str:
    """The agent's hire / borderline / no hire against one set of grades, on the shortlist."""
    agent = {e["candidate_id"]: AGENT_GRADE[e["recommendation"]] for e in report["shortlist"]}
    pairs = Counter((agent[cid], grades[cid]) for cid in agent if cid in grades)
    total = sum(pairs.values())
    if not total:
        return f"{who}: no shortlisted candidate is graded."
    agree = sum(n for (a, h), n in pairs.items() if a == h)
    relevant = sum(n for (_, h), n in pairs.items() if h >= 1)
    lines = [f"{who} ({total} shortlisted candidates)",
             f"  Shortlist precision (graded 1 or 2): {relevant}/{total} ({relevant / total:.0%})",
             f"  Same grade as the agent's recommendation: {agree}/{total} ({agree / total:.0%})",
             f"  Agent said hire, {who} would not interview: {pairs[(2, 0)]}",
             f"  Agent said no hire, {who} would interview: {pairs[(0, 2)]}",
             "  agent \\ human    0    1    2"]
    for a, label in ((2, "hire       "), (1, "borderline "), (0, "no hire    ")):
        lines.append(f"  {label}  " + "".join(f"{pairs[(a, h)]:5d}" for h in GRADES))
    return "\n".join(lines)


def consensus(sheets: dict[str, dict[str, int]]) -> dict[str, int]:
    """The candidates every labeller gave the same grade."""
    first, *others = sheets.values()
    return {c: g for c, g in first.items() if all(other.get(c) == g for other in others)}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Blind human labelling of a screening round.")
    sub = parser.add_subparsers(dest="command", required=True)
    template = sub.add_parser("template", help="print a blank labelling sheet as CSV")
    template.add_argument("report", type=Path, nargs="?", help="a screening round's .json report")
    template.add_argument("--all", action="store_true", help="list every resume in the index, not just the shortlist")
    template.add_argument("--db", type=Path, default=ROOT / "chroma_db", help="the index to list resumes from")
    agree = sub.add_parser("agreement", help="how far two labellers agree (Cohen's kappa)")
    agree.add_argument("first", type=Path)
    agree.add_argument("second", type=Path)
    scoring = sub.add_parser("score", help="compare the agent's recommendations with one or more sheets")
    scoring.add_argument("report", type=Path)
    scoring.add_argument("labels", type=Path, nargs="+")
    args = parser.parse_args(argv)

    try:
        if args.command == "template":
            if args.all:
                write_template(all_candidates(args.db), sys.stdout)
            elif args.report:
                write_template(json.loads(args.report.read_text())["shortlist"], sys.stdout)
            else:
                parser.error("give a report, or --all for every resume")
        elif args.command == "agreement":
            print(agreement(grades_from(args.first), grades_from(args.second), (args.first.stem, args.second.stem)))
        else:
            report = json.loads(args.report.read_text())
            shortlist = {e["candidate_id"] for e in report["shortlist"]}
            sheets = {path.stem: grades_from(path, shortlist) for path in args.labels}
            sections = [f"Screening round for: {report['requirements'].get('role_title')}", ""]
            sections += [score(report, grades, who) + "\n" for who, grades in sheets.items()]
            if len(sheets) > 1:
                sections.append(score(report, consensus(sheets), "rows where all labellers agree"))
            print("\n".join(sections).rstrip())
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    main()
