"""scripts/human_eval.py: blind sheets, agreement between labellers, and the agent's score."""
import csv
import importlib.util
import io
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("human_eval", ROOT / "scripts" / "human_eval.py")
human_eval = importlib.util.module_from_spec(_spec)
sys.modules["human_eval"] = human_eval
_spec.loader.exec_module(human_eval)

REPORT = {"requirements": {"role_title": "React Developer"}, "shortlist": [
    {"candidate_id": "zoe", "name": "Zoe", "resume_path": "resumes/zoe.md", "rank": 1, "recommendation": "hire"},
    {"candidate_id": "amy", "name": "Amy", "resume_path": "resumes/amy.md", "rank": 2, "recommendation": "borderline"},
    {"candidate_id": "bo", "name": "Bo", "resume_path": "resumes/bo.md", "rank": 3, "recommendation": "no_hire"}]}


def sheet(tmp_path: Path, name: str, grades: dict[str, int]) -> Path:
    path = tmp_path / f"{name}.csv"
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=human_eval.COLUMNS)
        writer.writeheader()
        for cid, grade in grades.items():
            writer.writerow({"candidate_id": cid, "name": cid, "resume_path": f"resumes/{cid}.md",
                             "human_grade": grade, "notes": ""})
    return path


# ---- sheets --------------------------------------------------------------------- #
def test_template_hides_rank_and_verdict_and_sorts_by_id():
    out = io.StringIO()

    human_eval.write_template(REPORT["shortlist"], out)

    rows = list(csv.DictReader(io.StringIO(out.getvalue())))
    assert [r["candidate_id"] for r in rows] == ["amy", "bo", "zoe"]
    assert set(rows[0]) == set(human_eval.COLUMNS)
    assert "hire" not in out.getvalue() and all(r["human_grade"] == "" for r in rows)


def test_template_all_lists_every_resume_in_the_index(tmp_path, capsys):
    (tmp_path / "candidates.json").write_text(json.dumps({"candidates": [
        {"candidate_name": f"P{i}", "resume_path": f"resumes/p{i}.md"} for i in range(5)]}))

    human_eval.main(["template", "--all", "--db", str(tmp_path)])

    rows = list(csv.DictReader(io.StringIO(capsys.readouterr().out)))
    assert [r["candidate_id"] for r in rows] == ["p0", "p1", "p2", "p3", "p4"]


def test_a_sheet_with_blanks_bad_grades_repeats_or_missing_rows_is_refused():
    rows = [{"candidate_id": "zoe", "human_grade": "3"}, {"candidate_id": "amy", "human_grade": ""},
            {"candidate_id": "eve", "human_grade": "1"}, {"candidate_id": "eve", "human_grade": "2"}]

    with pytest.raises(ValueError) as error:
        human_eval.read_grades(rows, {"zoe", "amy", "bo"})

    message = str(error.value)
    assert "must be 0, 1 or 2, not '3'" in message and "not ''" in message
    assert "eve is graded twice" in message and "no row for bo" in message


# ---- agreement -------------------------------------------------------------------- #
def test_kappa_is_one_for_identical_grades_and_zero_at_chance():
    assert human_eval.cohens_kappa([0, 1, 2, 2], [0, 1, 2, 2]) == 1.0
    # Each grader says 0 half the time, independently of the other: chance-level agreement
    assert human_eval.cohens_kappa([0, 0, 2, 2], [0, 2, 0, 2]) == pytest.approx(0.0)


def test_weighted_kappa_forgives_near_misses_more_than_far_ones():
    near = human_eval.cohens_kappa([0, 1, 2, 2, 1, 0], [0, 2, 2, 1, 1, 0], weighted=True)
    far = human_eval.cohens_kappa([0, 1, 2, 2, 1, 0], [2, 1, 2, 0, 1, 0], weighted=True)

    assert near > far
    # A textbook check: 2x2 table [[20, 5], [10, 15]] gives kappa 0.4
    a = [1] * 20 + [1] * 5 + [0] * 10 + [0] * 15
    b = [1] * 20 + [0] * 5 + [1] * 10 + [0] * 15
    assert human_eval.cohens_kappa(a, b) == pytest.approx(0.4)


def test_agreement_report_names_far_apart_grades_and_asks_for_a_regrade_when_low(tmp_path, capsys):
    alice = sheet(tmp_path, "alice", {"amy": 2, "bo": 0, "zoe": 2, "eve": 1})
    bob = sheet(tmp_path, "bob", {"amy": 0, "bo": 2, "zoe": 2, "eve": 1})

    human_eval.main(["agreement", str(alice), str(bob)])

    out = capsys.readouterr().out
    assert "4 candidates graded by both alice and bob" in out and "Same grade: 2/4 (50%)" in out
    assert "amy: alice 2, bob 0" in out and "Agreement is too low" in out


# ---- the agent against the labels ------------------------------------------------- #
def test_score_reports_each_labeller_and_their_consensus(tmp_path, capsys):
    report = tmp_path / "round-1.json"
    report.write_text(json.dumps(REPORT))
    alice = sheet(tmp_path, "alice", {"amy": 1, "bo": 0, "zoe": 2, "someone_else": 0})  # an --all sheet
    bob = sheet(tmp_path, "bob", {"amy": 2, "bo": 0, "zoe": 2})

    human_eval.main(["score", str(report), str(alice), str(bob)])

    out = capsys.readouterr().out
    assert "alice (3 shortlisted candidates)" in out
    assert "Same grade as the agent's recommendation: 3/3 (100%)" in out           # alice
    assert "rows where all labellers agree (2 shortlisted candidates)" in out       # amy is disputed
    assert "Shortlist precision (graded 1 or 2): 2/3 (67%)" in out


def test_score_counts_the_costly_disagreements():
    text = human_eval.score(REPORT, {"zoe": 0, "amy": 1, "bo": 2}, "carol")

    assert "Agent said hire, carol would not interview: 1" in text
    assert "Agent said no hire, carol would interview: 1" in text


def test_a_sheet_missing_a_shortlisted_candidate_is_an_error_not_a_traceback(tmp_path):
    report = tmp_path / "round-1.json"
    report.write_text(json.dumps(REPORT))
    partial = sheet(tmp_path, "dana", {"zoe": 2})

    with pytest.raises(SystemExit) as exit_info:
        human_eval.main(["score", str(report), str(partial)])

    assert exit_info.value.code == 2


def test_a_sheet_nobody_has_started_is_reported_in_one_line_naming_the_file(tmp_path):
    blank = tmp_path / "real_sre_A.csv"
    with blank.open("w", newline="") as f:
        human_eval.write_template(REPORT["shortlist"], f)

    with pytest.raises(human_eval.UngradedSheet, match=r"real_sre_A\.csv hasn't been graded yet: all 3 rows are blank"):
        human_eval.grades_from(blank)


def test_a_partly_graded_sheet_names_the_file_and_caps_the_list(tmp_path):
    rows = {f"p{i:02d}": ("" if i else 2) for i in range(30)}  # one graded, 29 blank
    path = sheet(tmp_path, "real_ml_B", rows)

    with pytest.raises(ValueError) as error:
        human_eval.grades_from(path)

    message = str(error.value)
    assert message.startswith(f"{path}: The labelling sheet has problems:")
    assert message.count("must be 0, 1 or 2") == human_eval.MAX_PROBLEMS_LISTED and "... and 19 more" in message
