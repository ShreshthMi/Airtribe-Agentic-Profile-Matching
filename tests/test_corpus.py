"""corpus.py over the real Milestone 1 file tools, in a throwaway project folder."""
import json

import pytest

from corpus import Corpus, CorpusError


@pytest.fixture
def corpus(tmp_path):
    (tmp_path / "resumes").mkdir()
    (tmp_path / "resumes" / "ana_ruiz.md").write_text("# Ana Ruiz\nBuilt React apps.\n")
    (tmp_path / "job_descriptions").mkdir()
    (tmp_path / "job_descriptions" / "fe.txt").write_text("Frontend Engineer\n")
    (tmp_path / "secret.txt").write_text("not for the agent")
    db = tmp_path / "db"
    db.mkdir()
    people = [("Ana Ruiz", "resumes/ana_ruiz.md"), ("Priya Sharma", "resumes/priya_sharma.md"),
              ("Priya Sharma", "resumes/resume_priya_sharma.pdf")]
    (db / "candidates.json").write_text(json.dumps({"candidates": [
        {"candidate_id": f"hash{i}", "candidate_name": name, "resume_path": path}
        for i, (name, path) in enumerate(people)]}))
    return Corpus(root=tmp_path, db_path=db)


def test_a_missing_index_says_how_to_build_one(tmp_path):
    with pytest.raises(CorpusError, match="python milestone2_rag/resume_rag.py"):
        Corpus(root=tmp_path, db_path=tmp_path / "nowhere")


def test_candidate_ids_are_resume_file_names_so_namesakes_stay_apart(corpus):
    assert sorted(corpus.candidates) == ["ana_ruiz", "priya_sharma", "resume_priya_sharma"]
    assert corpus.find("Priya Sharma") == ["priya_sharma", "resume_priya_sharma"]
    assert corpus.find("ana_ruiz") == ["ana_ruiz"] and corpus.find("ruiz") == ["ana_ruiz"]
    assert corpus.size == 3 and corpus.name("ana_ruiz") == "Ana Ruiz"


def test_resume_text_is_read_through_milestone1(corpus):
    assert corpus.resume_text("ana_ruiz") == "# Ana Ruiz\nBuilt React apps.\n"
    with pytest.raises(CorpusError, match="Could not read the resume for priya_sharma"):
        corpus.resume_text("priya_sharma")  # listed in the index but not on disk


@pytest.mark.parametrize("path", ["secret.txt", "resumes/../secret.txt", "milestone2_rag/job_matcher.py",
                                  "/etc/passwd", "resumes"])
def test_reads_outside_the_data_folders_are_refused(corpus, path):
    result = corpus.read_file(path)

    assert result["success"] is False and "Access is limited to resumes/, job_descriptions/, reports/" in result["error"]


def test_milestone1_still_refuses_hidden_files_inside_an_allowed_folder(corpus, tmp_path):
    (tmp_path / "resumes" / ".env").write_text("ANTHROPIC_API_KEY=x")

    assert corpus.read_file("resumes/.env")["success"] is False


def test_writes_go_only_into_reports(corpus, tmp_path):
    saved = corpus.write_file("reports/round-1.md", "# Report\n")

    assert saved["success"] and (tmp_path / "reports" / "round-1.md").read_text() == "# Report\n"
    assert corpus.write_file("resumes/ana_ruiz.md", "overwritten")["success"] is False
    assert (tmp_path / "resumes" / "ana_ruiz.md").read_text().startswith("# Ana Ruiz")


def test_list_and_search_files(corpus):
    assert [e["path"] for e in corpus.list_files("resumes")] == ["resumes/ana_ruiz.md"]
    assert "error" in corpus.list_files("milestone2_rag")[0]
    found = corpus.search_in_file("resumes/ana_ruiz.md", "react")
    assert found["success"] and len(found["matches"]) == 1


class FakeMatcher:
    def __init__(self):
        self.kwargs = None

    def match(self, query, **kwargs):
        self.kwargs = {"query": query, **kwargs}
        return {"top_matches": [{"candidate_name": "Ana Ruiz", "resume_path": "resumes/ana_ruiz.md",
                                 "match_score": 91, "experience_years": 6.0, "matched_skills": ["React"],
                                 "failed_requirements": ["3+ years React (has 2 yrs React)"]}]}


def test_search_ranks_without_filtering_and_maps_milestone2_results(corpus):
    corpus._matcher = matcher = FakeMatcher()

    [hit] = corpus.search("React role", k=5, must_haves=["3+ years of React", "Strong communication"])

    assert hit == {"candidate_id": "ana_ruiz", "name": "Ana Ruiz", "resume_path": "resumes/ana_ruiz.md",
                   "rag_score": 91, "experience_years": 6.0, "matched_skills": ["React"],
                   "rule_check_failures": ["3+ years React (has 2 yrs React)"]}
    assert matcher.kwargs["apply_filters"] is False and matcher.kwargs["auto_requirements"] is False
    # Only must-haves Milestone 2 can parse are passed on; it would print a warning for the rest
    assert matcher.kwargs["must_haves"] == ["3+ years of React"]
    assert matcher.kwargs["critical_skills"] == ["React"] and matcher.kwargs["k"] == 5


def test_existing_files_are_never_overwritten(corpus):
    assert corpus.write_file("reports/a.md", "first")["success"]

    second = corpus.write_file("reports/a.md", "second")

    assert second["success"] is False and "already exists" in second["error"]
    assert corpus.exists("reports/a.md") and not corpus.exists("reports/b.md")


def test_a_malformed_index_is_reported_not_raised_as_a_traceback(tmp_path):
    (tmp_path / "candidates.json").write_text("{not json")

    with pytest.raises(CorpusError, match="unreadable"):
        Corpus(root=tmp_path, db_path=tmp_path)


def test_two_resumes_with_the_same_file_name_are_refused(tmp_path):
    (tmp_path / "candidates.json").write_text(json.dumps({"candidates": [
        {"candidate_name": "Ana", "resume_path": "resumes/ana.txt"},
        {"candidate_name": "Ana", "resume_path": "resumes/ana.pdf"}]}))

    with pytest.raises(CorpusError, match="ids would collide: \\['ana'\\]"):
        Corpus(root=tmp_path, db_path=tmp_path)
