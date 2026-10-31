"""scripts/grade.py: the terminal grader, driven with scripted answers."""
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("grade", ROOT / "scripts" / "grade.py")
grade_script = importlib.util.module_from_spec(_spec)
sys.modules["grade"] = grade_script
_spec.loader.exec_module(grade_script)

ROWS = [{"candidate_id": c, "name": c.title(), "resume_path": f"resumes/{c}.md", "human_grade": g, "notes": ""}
        for c, g in (("ana", ""), ("ben", "2"), ("cy", ""), ("dee", ""))]


def run(answers: list[str], rows=ROWS):
    replies, shown, saves = iter(answers), [], []
    result = grade_script.grade(rows, "POSTING TEXT", lambda path: f"resume of {path}", lambda _: next(replies),
                                shown.append, lambda current: saves.append([r["human_grade"] for r in current]))
    return result, shown, saves


def test_grades_only_ungraded_rows_and_saves_after_each():
    result, shown, saves = run(["2", "great fit", "x", "p", "0", "", "1", "close"])

    assert [r["human_grade"] for r in result] == ["2", "2", "0", "1"]
    assert result[0]["notes"] == "great fit" and result[3]["notes"] == "close"
    assert saves == [["2", "2", "", ""], ["2", "2", "0", ""], ["2", "2", "0", "1"]]
    assert shown.count("POSTING TEXT") == 1 and any("[4/4] Dee" in s for s in shown)  # 'p' re-shows it once more
    assert ROWS[0]["human_grade"] == ""                                              # input rows not modified


def test_skip_leaves_a_row_blank_and_quit_stops_early():
    result, _, saves = run(["s", "q"])

    assert [r["human_grade"] for r in result] == ["", "2", "", ""] and saves == []


def test_save_and_load_round_trip_through_a_csv(tmp_path):
    path = tmp_path / "real_sre_self.csv"

    grade_script.save(path, [{**ROWS[1], "notes": 'says "Kafka", in quotes'}])

    assert grade_script.load(path) == [{**ROWS[1], "notes": 'says "Kafka", in quotes'}]
    assert not path.with_suffix(".tmp").exists()


def test_main_refuses_a_missing_sheet(capsys):
    with pytest.raises(SystemExit) as exit_info:
        grade_script.main(["real_nothing", "self"])

    assert exit_info.value.code == 2 and "real_nothing_self.csv not found" in capsys.readouterr().err


def test_pdf_and_docx_resumes_are_shown_as_text():
    text = grade_script.resume_loader.load_text_file(ROOT / "resumes" / "clara_jensen.pdf")

    assert "Clara Jensen" in text and "Experience" in text
