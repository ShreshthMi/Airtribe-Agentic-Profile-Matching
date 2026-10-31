"""The 57 generated resumes: in step with the script, and carrying the traps DATASET.md describes."""
import importlib.util
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("generate_resumes", ROOT / "scripts" / "generate_resumes.py")
gen = importlib.util.module_from_spec(_spec)
sys.modules["generate_resumes"] = gen  # dataclasses look their module up here while the class is built
_spec.loader.exec_module(gen)

PEOPLE = {p.slug: p for p in gen.PEOPLE}
RENDER = {"md": gen.render_markdown, "txt": gen.render_text}


def text_of(slug: str) -> str:
    person = PEOPLE[slug]
    return RENDER.get(person.fmt, gen.render_markdown)(gen.build_resume(person))


def test_the_corpus_is_100_resumes_43_carried_over_and_57_generated():
    files = sorted(p for p in (ROOT / "resumes").iterdir() if not p.name.startswith("."))
    assert len(files) == 100 and len(PEOPLE) == 57
    assert {p.stem for p in files} >= set(PEOPLE)


@pytest.mark.parametrize("slug", sorted(s for s, p in PEOPLE.items() if p.fmt in RENDER))
def test_committed_text_resumes_match_the_generator(slug):
    person = PEOPLE[slug]
    assert (ROOT / "resumes" / f"{slug}.{person.fmt}").read_text(encoding="utf-8") == text_of(slug)


def test_no_summary_claims_more_years_than_the_roles_add_up_to():
    for person in gen.PEOPLE:
        summary = gen.build_resume(person).summary
        claimed = re.search(r"with (\d+) years", summary)
        worked = sum(r.years for r in person.roles if not r.gap_note)
        assert claimed is None or int(claimed.group(1)) <= worked, person.slug


def test_the_most_recent_role_runs_to_present_and_careers_end_in_october_2026():
    for person in gen.PEOPLE:
        assert gen.build_resume(person).jobs[0].dates.endswith(" - Present"), person.slug


def test_trap_react_native_developers_never_mention_react_for_the_web():
    for slug in ("kenji_watanabe", "minh_nguyen"):
        text = text_of(slug)
        assert "React Native" in text and not re.search(r"React(?! Native)", text)


def test_trap_recent_switch_to_react_has_it_only_in_the_latest_role():
    jobs = gen.build_resume(PEOPLE["chloe_martin"]).jobs
    assert jobs[0].dates == "Sep 2025 - Present" and any("React" in b for b in jobs[0].bullets)
    assert not any("React" in b for job in jobs[1:] for b in job.bullets)


def test_trap_side_project_react_is_only_in_the_side_projects_section():
    resume = gen.build_resume(PEOPLE["tomasz_kowalski"])
    assert "React" not in " ".join(resume.skills) and not any("React" in b for j in resume.jobs for b in j.bullets)
    assert resume.extras[0][0] == "Side Projects" and "React" in resume.extras[0][1][0]


def test_trap_career_break_is_shown_as_its_own_entry():
    jobs = gen.build_resume(PEOPLE["natalia_popescu"]).jobs
    assert [j.heading for j in jobs][1] == "Career break"


def test_every_format_writes_a_file_milestone1_can_read(tmp_path):
    import docx  # noqa: PLC0415
    from pypdf import PdfReader  # noqa: PLC0415

    for person in (PEOPLE["lucas_moreau"], PEOPLE["clara_jensen"], PEOPLE["grace_liu"], PEOPLE["ethan_walsh"]):
        gen.write(person, tmp_path)
    assert "Lucas Moreau" in "\n".join(p.text for p in docx.Document(tmp_path / "lucas_moreau.docx").paragraphs)
    assert "Clara Jensen" in PdfReader(tmp_path / "clara_jensen.pdf").pages[0].extract_text()
    assert (tmp_path / "ethan_walsh.txt").read_text().startswith("Name: Ethan Walsh")


def test_main_refuses_to_shadow_a_resume_in_another_format(tmp_path, monkeypatch):
    (tmp_path / "grace_liu.pdf").write_bytes(b"someone else's resume")
    monkeypatch.setattr("sys.argv", ["generate_resumes.py", "--out", str(tmp_path)])

    with pytest.raises(SystemExit, match="grace_liu"):
        gen.main()


def test_generation_is_deterministic_and_independent_per_person():
    first = text_of("grace_liu")
    assert text_of("grace_liu") == first
    assert gen.build_resume(PEOPLE["grace_liu"]) == gen.build_resume(PEOPLE["grace_liu"])
