"""
Blind human labelling of a shortlist: the independent check Milestone 2's review asked for.

1. Make a labelling sheet from a screening round's JSON report:
     python scripts/human_eval.py template reports/react-developer-2026-10-31-round-1.json > labels.csv
   The sheet lists the shortlisted candidates in alphabetical order with no rank, score or
   verdict, so the labeller is not anchored on what the agent concluded.
2. A person reads each resume and fills in human_grade:
     2 = would interview, 1 = borderline, 0 = would not interview
3. Score the agent against those grades:
     python scripts/human_eval.py score labels.csv reports/react-developer-2026-10-31-round-1.json

What this cannot measure is recall: a strong candidate Round 1 never surfaced is not on the
sheet. Measuring that needs someone to grade all 100 resumes for the role.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

COLUMNS = ["candidate_id", "name", "resume_path", "human_grade", "notes"]
AGENT_GRADE = {"hire": 2, "borderline": 1, "no_hire": 0}


def write_template(report: dict, out) -> None:
    writer = csv.DictWriter(out, fieldnames=COLUMNS)
    writer.writeheader()
    for entry in sorted(report["shortlist"], key=lambda e: e["candidate_id"]):
        writer.writerow({"candidate_id": entry["candidate_id"], "name": entry["name"],
                         "resume_path": entry["resume_path"], "human_grade": "", "notes": ""})


def read_grades(rows: list[dict], shortlist_ids: set[str]) -> dict[str, int]:
    """Validated human grades; refuses a sheet with blanks, bad grades or unknown candidates."""
    grades, problems = {}, []
    for line, row in enumerate(rows, start=2):
        cid, grade = row.get("candidate_id", "").strip(), row.get("human_grade", "").strip()
        if cid not in shortlist_ids:
            problems.append(f"line {line}: {cid!r} is not on this shortlist")
        elif grade not in {"0", "1", "2"}:
            problems.append(f"line {line}: human_grade for {cid} must be 0, 1 or 2, not {grade!r}")
        else:
            grades[cid] = int(grade)
    listed = {row.get("candidate_id", "").strip() for row in rows}
    problems += [f"no row for {cid}" for cid in sorted(shortlist_ids - listed)]
    if problems:
        raise ValueError("The labelling sheet has problems:\n  " + "\n  ".join(problems))
    return grades


def score(report: dict, grades: dict[str, int]) -> str:
    agent = {e["candidate_id"]: AGENT_GRADE[e["recommendation"]] for e in report["shortlist"]}
    pairs = Counter((agent[cid], grades[cid]) for cid in grades)
    total = len(grades)
    agree = sum(n for (a, h), n in pairs.items() if a == h)
    lines = [f"Shortlist of {total} for: {report['requirements'].get('role_title')}",
             f"Shortlist precision (human grade 1 or 2): {sum(g >= 1 for g in grades.values()) / total:.0%}",
             f"Exact agreement with the agent's recommendation: {agree}/{total} ({agree / total:.0%})",
             f"Agent said hire, human said would not interview: {pairs[(2, 0)]}",
             f"Agent said no hire, human said would interview: {pairs[(0, 2)]}",
             "", "agent \\ human    0    1    2"]
    for a, label in ((2, "hire       "), (1, "borderline "), (0, "no hire    ")):
        lines.append(f"{label}  " + "".join(f"{pairs[(a, h)]:5d}" for h in (0, 1, 2)))
    lines += ["", "Not measured: recall. Candidates Round 1 never surfaced are not on the sheet."]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Blind human labelling of a screening shortlist.")
    sub = parser.add_subparsers(dest="command", required=True)
    template = sub.add_parser("template", help="print a blank labelling sheet as CSV")
    template.add_argument("report", type=Path, help="a screening round's .json report")
    scoring = sub.add_parser("score", help="compare a filled-in sheet with the agent's recommendations")
    scoring.add_argument("labels", type=Path)
    scoring.add_argument("report", type=Path)
    args = parser.parse_args(argv)

    report = json.loads(args.report.read_text())
    if args.command == "template":
        write_template(report, sys.stdout)
        return
    with args.labels.open(newline="") as f:
        rows = list(csv.DictReader(f))
    try:
        grades = read_grades(rows, {e["candidate_id"] for e in report["shortlist"]})
    except ValueError as exc:
        parser.exit(2, f"{exc}\n")
    print(score(report, grades))


if __name__ == "__main__":
    main()
