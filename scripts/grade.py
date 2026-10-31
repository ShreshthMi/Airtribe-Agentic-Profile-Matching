"""
Grade a label sheet in the terminal: each resume is shown as text, you type a grade, and the
sheet is saved after every answer.

    python scripts/grade.py real_sre self      # grades evaluation/labels/real_sre_self.csv

Only the posting and the resumes are shown, never the agent's ranking or verdicts, so the
grades stay your own. Type q to stop; run it again to carry on where you left off.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "milestone2_rag"))
import resume_loader  # noqa: E402  (Milestone 1's reader: .txt, .md, .pdf and .docx)

LABELS = ROOT / "evaluation" / "labels"
JOBS = ROOT / "job_descriptions"
COLUMNS = ["candidate_id", "name", "resume_path", "human_grade", "notes"]
RULE = "-" * 78
PROMPT = "Grade 2 (interview) / 1 (borderline) / 0 (no)   p = posting, s = skip, q = quit: "


def load(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save(path: Path, rows: list[dict]) -> None:
    """Write the whole sheet to a temporary file, then swap it in, so a crash never half-writes it."""
    temporary = path.with_suffix(".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows({c: row.get(c, "") for c in COLUMNS} for row in rows)
    os.replace(temporary, path)


def grade(rows: list[dict], posting: str, read_resume, ask, show, on_change) -> list[dict]:
    """Ask for a grade on every ungraded row; returns the sheet with the new grades."""
    rows = [dict(r) for r in rows]
    show(f"{RULE}\nPOSTING\n{RULE}\n{posting}")
    pending = [i for i, r in enumerate(rows) if not (r.get("human_grade") or "").strip()]
    for done, i in enumerate(pending, start=1):
        row = rows[i]
        show(f"\n{RULE}\n[{len(rows) - len(pending) + done}/{len(rows)}] {row['name']}  ({row['resume_path']})\n"
             f"{RULE}\n{read_resume(row['resume_path'])}")
        while True:
            answer = ask(PROMPT).strip().lower()
            if answer == "p":
                show(posting)
            elif answer in {"s", "q"} or answer in {"0", "1", "2"}:
                break
        if answer == "q":
            break
        if answer == "s":
            continue
        rows[i] = {**row, "human_grade": answer, "notes": ask("Note (optional, Enter to skip): ").strip()}
        on_change(rows)
    return rows


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Grade a label sheet in the terminal.")
    parser.add_argument("posting", help="e.g. real_sre, for job_descriptions/real_sre.txt")
    parser.add_argument("labeller", help="e.g. self, for evaluation/labels/real_sre_self.csv")
    args = parser.parse_args(argv)
    sheet, job = LABELS / f"{args.posting}_{args.labeller}.csv", JOBS / f"{args.posting}.txt"
    for needed in (sheet, job):
        if not needed.is_file():
            parser.exit(2, f"error: {needed} not found\n")

    def read_resume(relative: str) -> str:
        try:
            return resume_loader.load_text_file(ROOT / relative).strip()
        except resume_loader.LoaderError as exc:
            return f"(could not read this resume: {exc})"

    rows = grade(load(sheet), job.read_text(encoding="utf-8").strip(), read_resume, input, print,
                 lambda current: save(sheet, current))
    graded = sum(bool((r.get("human_grade") or "").strip()) for r in rows)
    print(f"\n{graded}/{len(rows)} graded in {sheet.relative_to(ROOT)}"
          + ("" if graded < len(rows) else " - done."))


if __name__ == "__main__":
    main()
