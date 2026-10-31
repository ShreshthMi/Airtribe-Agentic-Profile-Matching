"""scripts/evaluate.py: ranking metrics, label loading, and a two-provider run on the stand-ins."""
import csv
import importlib.util
import math
import sys
from datetime import date
from pathlib import Path

import pytest

from tests.fakes import FakeCorpus, ScriptedClaude

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

    results, verdicts = evaluate.evaluate_posting("React developer, 3+ years", gains,
                                                  {"minilm": FakeCorpus(), "other": ReversedCorpus()},
                                                  claude, TODAY, {})

    first, second = results["minilm"], results["other"]
    assert first["unlabelled_in_top"] == 0 and first["r1_r10"] is not None   # every resume graded
    assert first["r1_p10"] > second["r1_p10"]                                # the reversed ranking is worse
    assert first["r2_ndcg10"] >= first["r1_ndcg10"]                           # Round 2 puts the met ones first
    assert first["hire_precision"] == 1.0                                    # its hires are all graded relevant
    judged = [name for name, _ in claude.judged]
    assert len(judged) == len(set(judged)) == 13                             # nobody is judged twice
    assert set(verdicts) == set(gains)


def test_recall_is_not_reported_when_the_labels_cover_only_a_shortlist():
    results, _ = evaluate.evaluate_posting("React developer", {"ana_ruiz": 2, "ben_ito": 1},
                                           {"minilm": FakeCorpus()}, ScriptedClaude(), TODAY, {})

    assert results["minilm"]["r1_r10"] is None and results["minilm"]["unlabelled_in_top"] == 8


def test_the_report_has_a_row_per_provider_and_a_mean():
    metrics = {key: 0.5 for key, _ in evaluate.COLUMNS} | {"unlabelled_in_top": 1, "r1_r10": None, "unjudged": 0}

    report = evaluate.render({"real_frontend": {"minilm": metrics, "voyage": metrics}},
                             {"real_frontend": ["alice", "bob"]}, TODAY)

    assert "| real_frontend | minilm | 1 | 0.50 | 0.50 | 0.50 | n/a | 0.50 | 0.50 | 0.50 |" in report
    assert "| **mean** | voyage |" in report and "real_frontend: alice, bob" in report


# ---- refusing to run unfairly or without data ------------------------------------------- #
def test_main_needs_label_sheets(tmp_path):
    with pytest.raises(SystemExit) as exit_info:
        evaluate.main(["--labels", str(tmp_path / "none")])
    assert exit_info.value.code == 1


def test_main_refuses_an_index_without_a_measured_band(tmp_path, monkeypatch, capsys):
    write_sheet(tmp_path / "real_frontend_alice.csv", {"ana_ruiz": 2})
    (tmp_path / "db").mkdir()
    monkeypatch.setattr(evaluate, "index_dir", lambda provider: tmp_path / "db")

    with pytest.raises(SystemExit):
        evaluate.main(["--labels", str(tmp_path), "--providers", "ollama"])

    assert "python scripts/build_index.py --provider ollama" in capsys.readouterr().err
