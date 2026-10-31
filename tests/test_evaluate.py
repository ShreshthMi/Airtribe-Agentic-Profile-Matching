"""scripts/evaluate.py: ranking metrics, label loading, and a two-provider run on the stand-ins."""
import csv
import importlib.util
import math
import sys
from datetime import date
from pathlib import Path

import pytest

from tests.fakes import REACT_ROLE, FakeCorpus, ScriptedClaude

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("evaluate", ROOT / "scripts" / "evaluate.py")
evaluate = importlib.util.module_from_spec(_spec)
sys.modules["evaluate"] = evaluate
_spec.loader.exec_module(evaluate)

TODAY = date(2026, 10, 31)


# ---- metrics ---------------------------------------------------------------------- #
def test_precision_and_recall_skip_unlabelled_candidates():
    gains = {"a": 2, "b": 0, "c": 1, "d": 2}
    order = ["a", "x", "b", "c", "y", "d"]   # x and y were never graded

    assert evaluate.precision_at(order, gains, 2) == 0.5      # a, b
    assert evaluate.precision_at(order, gains, 10) == 0.75    # a, b, c, d
    assert evaluate.recall_at(order, gains, 2) == pytest.approx(1 / 3)
    assert evaluate.precision_at(["x"], gains, 5) is None


def test_ndcg_is_one_for_the_ideal_order_and_lower_otherwise():
    gains = {"a": 2, "b": 1, "c": 0}

    assert evaluate.ndcg_at(["a", "b", "c"], gains, 3) == pytest.approx(1.0)
    worst = evaluate.ndcg_at(["c", "b", "a"], gains, 3)
    assert worst == pytest.approx((1 / math.log2(3) + 2 / math.log2(4)) / (2 + 1 / math.log2(3)))
    assert evaluate.ndcg_at(["a"], {"a": 0}, 3) is None


# ---- labels -------------------------------------------------------------------------- #
def write_sheet(path: Path, grades: dict[str, int]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["candidate_id", "name", "resume_path", "human_grade", "notes"])
        writer.writeheader()
        for cid, grade in grades.items():
            writer.writerow({"candidate_id": cid, "name": cid, "resume_path": "", "human_grade": grade, "notes": ""})


def test_labels_are_grouped_by_posting_and_averaged_across_labellers(tmp_path):
    write_sheet(tmp_path / "real_frontend_alice.csv", {"ana_ruiz": 2, "ben_ito": 0})
    write_sheet(tmp_path / "real_frontend_bob.csv", {"ana_ruiz": 1, "ben_ito": 0, "cara_lee": 1})

    labels = evaluate.load_labels(tmp_path)

    assert list(labels) == ["real_frontend"] and sorted(labels["real_frontend"]) == ["alice", "bob"]
    assert evaluate.mean_grades(labels["real_frontend"]) == {"ana_ruiz": 1.5, "ben_ito": 0.0, "cara_lee": 1.0}


def test_a_sheet_without_a_labeller_in_its_name_is_refused(tmp_path):
    write_sheet(tmp_path / "frontend.csv", {"ana_ruiz": 2})

    with pytest.raises(ValueError, match="<posting>_<labeller>.csv"):
        evaluate.load_labels(tmp_path)


# ---- one posting, two providers ------------------------------------------------------- #
class ReversedCorpus(FakeCorpus):
    """A second 'provider' whose Round 1 ranking is the first one's, reversed."""

    def search(self, query, k=10, must_haves=()):
        ranking = super().search(query, k=self.size, must_haves=must_haves)[::-1]
        return ranking[:k]


def test_a_posting_is_scored_for_each_provider_and_judgements_are_shared():
    claude = ScriptedClaude()  # extracts "3+ years of React" as the only must-have
    gains = {"ana_ruiz": 2, "eve_moss": 2, "finn_oak": 1, "ben_ito": 1, "cara_lee": 0, "dev_shah": 0,
             "hal_reed": 0, "jo_kim": 0, "gia_park": 0, "ivy_chen": 1, "kai_lund": 0, "lia_ross": 0, "mo_sato": 0}

    results, verdicts = evaluate.evaluate_posting("React developer, 3+ years", REACT_ROLE, gains,
                                                  {"minilm": FakeCorpus(), "other": ReversedCorpus()},
                                                  claude, TODAY, {})

    first, second = results["minilm"], results["other"]
    assert first["unlabelled_in_top"] == 0 and first["r1_r10"] is not None   # every resume graded
    assert first["r1_p10"] > second["r1_p10"]                                # the reversed ranking is worse
    assert first["r2_ndcg10"] >= first["r1_ndcg10"]                           # Round 2 puts the met ones first
    assert first["hire_precision"] == 1.0                                    # its hires are all graded relevant
    # hires (met) are graded 2 or 1, so of the 3 hires only Finn (graded 1) disagrees on grade
    assert 0 < first["r3_agreement"] < 1
    judged = [name for name, _ in claude.judged]
    assert len(judged) == len(set(judged)) == 13                             # nobody is judged twice
    assert set(verdicts) == set(gains)


def test_recall_is_not_reported_when_the_labels_cover_only_a_shortlist():
    results, _ = evaluate.evaluate_posting("React developer", REACT_ROLE, {"ana_ruiz": 2, "ben_ito": 1},
                                           {"minilm": FakeCorpus()}, ScriptedClaude(), TODAY, {})

    assert results["minilm"]["r1_r10"] is None and results["minilm"]["unlabelled_in_top"] == 8


def test_the_report_has_a_row_per_provider_and_a_mean():
    metrics = {key: 0.5 for key, _ in evaluate.COLUMNS} | {"unlabelled_in_top": 1, "r1_r10": None, "unjudged": 0}

    report = evaluate.render({"real_frontend": {"minilm": metrics, "voyage": metrics}},
                             {"real_frontend": ["alice", "bob"]}, TODAY)

    assert "| real_frontend | minilm | 1 | 0.50 | 0.50 | 0.50 | n/a | 0.50 | 0.50 | 0.50 |" in report
    assert "| **mean** | voyage |" in report and "real_frontend: alice, bob" in report


# ---- refusing to run unfairly or without data ------------------------------------------- #
def calibrated_index(tmp_path: Path, monkeypatch) -> None:
    db = tmp_path / "db"
    db.mkdir()
    (db / "candidates.json").write_text('{"candidates": [{"candidate_name": "Ana", "resume_path": "resumes/a.md"}]}')
    (db / "calibration.json").write_text('{"floor": 0.3, "ceil": 0.7}')
    monkeypatch.setattr(evaluate, "index_dir", lambda provider: db)
    monkeypatch.setattr(evaluate, "Claude", ScriptedClaude)


def test_main_needs_label_sheets(tmp_path, monkeypatch, capsys):
    calibrated_index(tmp_path, monkeypatch)

    with pytest.raises(SystemExit) as exit_info:
        evaluate.main(["--labels", str(tmp_path / "none")])

    assert exit_info.value.code == 1 and "No label sheets" in capsys.readouterr().err


def test_main_refuses_an_index_without_a_measured_band(tmp_path, monkeypatch, capsys):
    write_sheet(tmp_path / "real_frontend_alice.csv", {"ana_ruiz": 2})
    (tmp_path / "db").mkdir()
    monkeypatch.setattr(evaluate, "index_dir", lambda provider: tmp_path / "db")

    with pytest.raises(SystemExit):
        evaluate.main(["--labels", str(tmp_path), "--providers", "ollama"])

    assert "python scripts/build_index.py --provider ollama" in capsys.readouterr().err


# ---- frozen requirements and pooled sheets ---------------------------------------------- #
def test_requirements_are_extracted_once_and_then_read_back(tmp_path):
    claude = ScriptedClaude()  # holds exactly one extraction

    first = evaluate.frozen_requirements("real_frontend", "React developer", claude, tmp_path)
    second = evaluate.frozen_requirements("real_frontend", "React developer", claude, tmp_path)

    assert first == second and first["must_have"] == ["3+ years of React"]
    assert (tmp_path / "real_frontend.json").is_file()


def test_the_pooled_shortlist_covers_every_providers_top_10():
    pool = evaluate.pooled_shortlist("React developer", REACT_ROLE, {"a": FakeCorpus(), "b": ReversedCorpus()})

    ids = {c["candidate_id"] for c in pool}
    assert len(ids) == 13 and len(pool) == 13   # 10 + 10 overlapping in 7, so all 13 resumes


def test_sheets_with_grades_are_never_overwritten(tmp_path):
    write_sheet(tmp_path / "real_sre_A.csv", {"ana_ruiz": 2})
    candidates = [{"candidate_id": "ben_ito", "name": "Ben Ito", "resume_path": "resumes/ben_ito.txt"}]

    with pytest.raises(ValueError, match="already has grades"):
        evaluate.write_sheets("real_sre", candidates, ["A", "B"], tmp_path)
    assert not (tmp_path / "real_sre_B.csv").exists()

    paths = evaluate.write_sheets("real_data", candidates, ["A", "B"], tmp_path)
    assert [p.name for p in paths] == ["real_data_A.csv", "real_data_B.csv"]


def test_make_sheets_writes_pooled_blank_sheets(tmp_path, monkeypatch, capsys):
    jobs, labels = tmp_path / "jobs", tmp_path / "labels"
    jobs.mkdir()
    (jobs / "real_frontend.txt").write_text("React developer, 3+ years")
    monkeypatch.setattr(evaluate, "open_corpora", lambda providers: {"a": FakeCorpus(), "b": ReversedCorpus()})
    monkeypatch.setattr(evaluate, "Claude", ScriptedClaude)
    monkeypatch.setattr(evaluate, "REQUIREMENTS_DIR", tmp_path / "frozen")

    evaluate.main(["--jobs", str(jobs), "--labels", str(labels), "--make-sheets", "A", "B",
                   "--postings", "real_frontend"])

    rows = evaluate.human_eval.read_sheet(labels / "real_frontend_B.csv")
    assert len(rows) == 13 and all(r["human_grade"] == "" for r in rows)
    assert (tmp_path / "frozen" / "real_frontend.json").is_file()


def test_sheets_not_yet_graded_are_skipped_with_a_note(tmp_path, capsys):
    write_sheet(tmp_path / "real_sre_A.csv", {"ana_ruiz": 2, "ben_ito": 0})
    write_sheet(tmp_path / "real_sre_B.csv", {"ana_ruiz": "", "ben_ito": ""})

    labels = evaluate.load_labels(tmp_path)

    assert labels == {"real_sre": {"A": {"ana_ruiz": 2, "ben_ito": 0}}}
    assert "skipping 1 sheet(s) not graded yet: real_sre_B.csv" in capsys.readouterr().out


def test_when_no_sheet_is_graded_the_evaluation_says_what_to_do(tmp_path):
    write_sheet(tmp_path / "real_sre_A.csv", {"ana_ruiz": ""})

    with pytest.raises(ValueError, match="None of the 1 sheets .* has been graded yet. Send the labelling packs"):
        evaluate.load_labels(tmp_path)
