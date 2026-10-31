"""scripts/human_eval.py: the blind labelling sheet and the agreement score."""
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


def test_template_hides_rank_and_verdict_and_sorts_by_id():
    out = io.StringIO()

    human_eval.write_template(REPORT, out)

    rows = list(csv.DictReader(io.StringIO(out.getvalue())))
    assert [r["candidate_id"] for r in rows] == ["amy", "bo", "zoe"]
    assert set(rows[0]) == {"candidate_id", "name", "resume_path", "human_grade", "notes"}
    assert "hire" not in out.getvalue() and all(r["human_grade"] == "" for r in rows)


def test_score_reports_precision_agreement_and_the_costly_disagreements():
    grades = {"zoe": 0, "amy": 1, "bo": 2}

    text = human_eval.score(REPORT, grades)

    assert "Shortlist precision (human grade 1 or 2): 67%" in text
    assert "Exact agreement with the agent's recommendation: 1/3 (33%)" in text
    assert "Agent said hire, human said would not interview: 1" in text
    assert "Agent said no hire, human said would interview: 1" in text


def test_a_sheet_with_blanks_bad_grades_or_strangers_is_refused():
    rows = [{"candidate_id": "zoe", "human_grade": "3"}, {"candidate_id": "amy", "human_grade": ""},
            {"candidate_id": "eve", "human_grade": "1"}]

    with pytest.raises(ValueError) as error:
        human_eval.read_grades(rows, {"zoe", "amy", "bo"})

    message = str(error.value)
    assert "must be 0, 1 or 2, not '3'" in message and "not ''" in message
    assert "'eve' is not on this shortlist" in message and "no row for bo" in message


def test_command_line_round_trip(tmp_path, capsys):
    report = tmp_path / "round-1.json"
    report.write_text(json.dumps(REPORT))
    human_eval.main(["template", str(report)])
    sheet = capsys.readouterr().out.replace("amy,Amy,resumes/amy.md,,", "amy,Amy,resumes/amy.md,1,")
    sheet = sheet.replace("bo,Bo,resumes/bo.md,,", "bo,Bo,resumes/bo.md,0,").replace("zoe,Zoe,resumes/zoe.md,,",
                                                                                         "zoe,Zoe,resumes/zoe.md,2,")
    labels = tmp_path / "labels.csv"
    labels.write_text(sheet)

    human_eval.main(["score", str(labels), str(report)])

    assert "Exact agreement with the agent's recommendation: 3/3 (100%)" in capsys.readouterr().out
