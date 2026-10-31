"""The screening rules in screening.py: pure functions, so every rule is pinned down exactly."""
from datetime import date

from screening import (candidate_report, comparison_table, current_verdicts, describe_change, effective_verdict,
                       evidence_found, explain_pair, fit_score, rank_by_fit, ranking_changes, recommendation,
                       render_report, requirement_changes, requirement_key, suggestion_key)

REQS = {"role_title": "Frontend", "must_have": ["React", "TypeScript"], "nice_to_have": ["Next.js"], "notes": ""}


def v(verdict: str, verified: bool = True, requirement: str = "x") -> dict:
    return {"requirement": requirement, "verdict": verdict, "evidence": "quote" if verdict != "missing" else "",
            "reasoning": f"judged {verdict}.", "evidence_verified": verified and verdict != "missing"}


def verdicts(react: str, ts: str, nextjs: str, unverified: tuple[str, ...] = ()) -> dict:
    """Verdicts on REQS; requirements named in `unverified` get a quote that was not found."""
    return {"react": v(react, "react" not in unverified, "React"),
            "typescript": v(ts, "ts" not in unverified, "TypeScript"),
            "next.js": v(nextjs, "nextjs" not in unverified, "Next.js")}


def candidate(cid: str, rag: int = 80) -> dict:
    return {"candidate_id": cid, "name": cid.title(), "resume_path": f"resumes/{cid}.md", "rag_score": rag}


# ---- requirements --------------------------------------------------------------- #
def test_requirement_key_ignores_case_spacing_and_a_final_full_stop():
    assert requirement_key("  3+ Years   of React. ") == "3+ years of react"


def test_requirement_changes_reports_added_moved_and_removed():
    new = {"must_have": ["React", "Next.js"], "nice_to_have": ["GraphQL"]}

    changes = requirement_changes(REQS, new)

    assert changes == {"added_must": [], "added_nice": ["GraphQL"], "now_must": ["Next.js"], "now_nice": [],
                       "removed": ["TypeScript"]}


def test_requirement_changes_from_nothing_treats_everything_as_added():
    assert requirement_changes(None, REQS)["added_must"] == ["React", "TypeScript"]


def test_current_verdicts_drops_cached_verdicts_for_requirements_no_longer_asked():
    cached = {**verdicts("met", "met", "met"), "graphql": v("met")}

    assert list(current_verdicts(REQS, cached)) == ["react", "typescript", "next.js"]


def test_suggestion_key_changes_when_a_requirement_moves_between_must_and_nice():
    moved = {"must_have": ["React"], "nice_to_have": ["TypeScript", "Next.js"]}

    assert suggestion_key("ana", REQS) != suggestion_key("ana", moved)


# ---- evidence ------------------------------------------------------------------- #
def test_evidence_found_tolerates_case_spacing_and_typographic_quotes():
    resume = "Led the  migration to React,\ncutting the bundle by 30%. Worked on “Design” systems."

    assert evidence_found("led the migration to react, cutting the bundle", resume)
    assert evidence_found('worked on "design" systems', resume)


def test_evidence_found_accepts_elisions_only_in_order():
    resume = "Built React apps. Mentored three engineers. Shipped Next.js pages."

    assert evidence_found("Built React apps ... Shipped Next.js pages", resume)
    assert not evidence_found("Shipped Next.js pages ... Built React apps", resume)


def test_evidence_found_rejects_invented_and_empty_quotes():
    assert not evidence_found("Ten years of React at Google", "Two years of React at Bluefinch.")
    assert not evidence_found("  ...  ", "anything")


RESUME = ("Senior Frontend Engineer, Silverpine Energy\nSep 2025 - Present\n"
          "- Reviewed React pull requests for a team of 4 engineers.\n"
          "- Built JavaScript apps for the internet with Node.js.\n"
          "Worked on naïve caching and eﬃcient builds.\n" + "unrelated filler text " * 20 +
          "\nMentored 4 engineers on testing.")


def test_evidence_found_rejects_quotes_too_short_to_prove_anything():
    for quote in ("C", "go", "a ... e", ".NET", "Java", "efficient builds"):
        assert not evidence_found(quote, RESUME), quote


def test_evidence_found_matches_whole_words_only():
    assert not evidence_found("Built Java apps for", RESUME)       # the resume says JavaScript
    assert evidence_found("Built JavaScript apps for the internet with Node.js", RESUME)


def test_evidence_found_refuses_fragments_stitched_from_across_the_resume():
    assert not evidence_found("Senior Frontend Engineer ... Mentored 4 engineers on testing", RESUME)
    assert not evidence_found("Senior Frontend Engineer ... Reviewed React pull ... Built JavaScript apps ... "
                              "naive caching and", RESUME)    # more than three fragments


def test_evidence_found_accepts_quotes_across_bullets_and_other_ellipses():
    assert evidence_found("Silverpine Energy Sep 2025 - Present - Reviewed React pull requests", RESUME)
    assert evidence_found("Reviewed React pull requests [...] team of 4 engineers", RESUME)
    assert evidence_found("Reviewed React pull requests .. team of 4 engineers", RESUME)
    assert evidence_found("naïve caching and efficient builds", RESUME)  # ligature and combining accent


def test_an_unverified_met_counts_only_as_partial():
    assert effective_verdict(v("met", verified=False)) == "partial"
    assert effective_verdict(v("met")) == "met"
    assert effective_verdict(v("missing")) == "missing"


# ---- fit score and recommendation ----------------------------------------------- #
def test_fit_score_weights_must_haves_double_and_partial_as_half():
    assert fit_score(REQS, verdicts("met", "met", "met")) == 100
    assert fit_score(REQS, verdicts("met", "met", "missing")) == 80     # 4 of 5
    assert fit_score(REQS, verdicts("met", "partial", "missing")) == 60  # 3 of 5
    assert fit_score(REQS, verdicts("missing", "missing", "met")) == 20


def test_fit_score_is_zero_without_requirements():
    assert fit_score({"must_have": [], "nice_to_have": []}, {}) == 0


def test_recommendation_is_decided_by_must_haves_alone():
    assert recommendation(REQS, verdicts("met", "met", "missing"))[0] == "hire"
    assert recommendation(REQS, verdicts("met", "partial", "met")) == (
        "borderline", "Only partly meets must-have: TypeScript.")
    assert recommendation(REQS, verdicts("met", "missing", "met")) == ("no_hire", "Misses must-have: TypeScript.")


def test_recommendation_without_must_haves_is_borderline():
    assert recommendation({"must_have": [], "nice_to_have": ["React"]}, {"react": v("met")})[0] == "borderline"


def test_unverified_evidence_on_a_must_have_blocks_a_hire():
    assert recommendation(REQS, verdicts("met", "met", "met", unverified=("ts",)))[0] == "borderline"


# ---- ranking ---------------------------------------------------------------------- #
def test_rank_by_fit_breaks_ties_on_round1_score_then_id():
    pool = [candidate("cid_b", 70), candidate("cid_a", 70), candidate("cid_c", 90), candidate("cid_d", 99)]
    judged = {"cid_a": verdicts("met", "met", "met"), "cid_b": verdicts("met", "met", "met"),
              "cid_c": verdicts("met", "met", "met"), "cid_d": verdicts("met", "missing", "met")}

    ranked = rank_by_fit(pool, REQS, judged)

    assert [(e["candidate_id"], e["rank"]) for e in ranked] == [("cid_c", 1), ("cid_a", 2), ("cid_b", 3), ("cid_d", 4)]
    assert ranked[3]["must_haves_met"] == "1/2" and ranked[3]["recommendation"] == "no_hire"


def test_ranking_changes_explains_movers_newcomers_and_leavers():
    react_only = {"must_have": ["React"], "nice_to_have": []}
    old = rank_by_fit([candidate("ana"), candidate("ben"), candidate("cy")], react_only,
                      {c: {"react": v("met")} for c in ("ana", "ben", "cy")})
    judged = {"ana": verdicts("met", "met", "met"), "ben": verdicts("met", "missing", "missing"),
              "cy": verdicts("met", "met", "missing"), "dee": verdicts("met", "met", "met")}
    ranked = rank_by_fit([candidate("ana"), candidate("ben"), candidate("cy"), candidate("dee", 10)], REQS, judged)

    changes = {c["candidate_id"]: c for c in ranking_changes(old, ranked, react_only, REQS, judged, size=3)}

    assert "ana" not in changes  # still #1 with fit 100
    assert describe_change(changes["dee"]) == ("Dee: new -> #2 (new to the shortlist, fit 100; "
                                               "changed requirements: TypeScript met, Next.js met)")
    assert describe_change(changes["ben"]) == ("Ben: #2 -> off the shortlist (now #4) (fit 100 -> 40; "
                                               "changed requirements: TypeScript missing, Next.js missing)")
    assert changes["cy"]["old_rank"] == 3 and changes["cy"]["new_rank"] == 3
    assert describe_change(changes["cy"]).startswith("Cy: stays #3 (fit 100 -> 80;")


def test_ranking_changes_names_dropped_requirements_as_a_cause():
    judged = {"ana": verdicts("met", "missing", "met"), "ben": verdicts("met", "met", "missing")}
    old = rank_by_fit([candidate("ana", 90), candidate("ben", 80)], REQS, judged)
    without_ts = {"must_have": ["React"], "nice_to_have": ["Next.js"]}
    ranked = rank_by_fit([candidate("ana", 90), candidate("ben", 80)], without_ts, judged)

    [ana, ben] = ranking_changes(old, ranked, REQS, without_ts, judged, size=2)

    assert ana["reasons"] == ["fit 60 -> 100", "dropped requirements: TypeScript missing"]
    assert ben["reasons"] == ["fit 80 -> 67", "dropped requirements: TypeScript met"]


# ---- explanations ------------------------------------------------------------------ #
def test_explain_pair_lists_differences_largest_effect_first():
    judged = {"ana": verdicts("met", "met", "partial"), "ben": verdicts("met", "missing", "met")}
    ana, ben = rank_by_fit([candidate("ana"), candidate("ben")], REQS, judged)

    text = explain_pair(ana, ben, REQS, judged)

    lines = text.splitlines()
    assert lines[0] == "Ana is #1 with fit 90; Ben is #2 with fit 60."
    assert lines[2].startswith("- TypeScript (must-have, weight 2): Ana met, Ben missing.")
    assert lines[3].startswith("- Next.js (nice-have, weight 1): Ana partial, Ben met.")


def test_explain_pair_says_when_round1_broke_a_tie():
    judged = {"ana": verdicts("met", "met", "met"), "ben": verdicts("met", "met", "met")}
    ana, ben = rank_by_fit([candidate("ana", 90), candidate("ben", 80)], REQS, judged)

    assert "Their fit scores tie, so Round 1's RAG score decided it: 90 vs 80." in explain_pair(ana, ben, REQS, judged)


def test_comparison_table_flags_quotes_that_were_not_found():
    judged = {"ana": verdicts("met", "met", "met", unverified=("ts",)), "ben": verdicts("met", "missing", "met")}
    ranked = rank_by_fit([candidate("ana"), candidate("ben")], REQS, judged)

    table = comparison_table(ranked, REQS, judged)

    assert "| TypeScript (must) | ~ partial (quote not found) | ✗ missing |" in table
    assert table.splitlines()[0] == "| | Ana (#1) | Ben (#2) |"


def test_candidate_report_splits_strengths_from_gaps_and_shows_rule_checks():
    judged = verdicts("met", "partial", "met", unverified=("nextjs",))
    [entry] = rank_by_fit([{**candidate("ana"), "rule_check_failures": ["3+ years React (has 1.2 yrs React)"]}],
                          REQS, {"ana": judged})

    report = candidate_report(entry, REQS, judged, ["Ask about TypeScript."])

    strengths, gaps = report.split("**Gaps**")
    assert "**React** (must-have)" in strengths and "**TypeScript**" in gaps
    assert "could not be found in the resume" in gaps  # the unverified Next.js
    assert "has 1.2 yrs React" in report and "- Ask about TypeScript." in report


def test_render_report_has_every_section():
    judged = {"ana": verdicts("met", "met", "met"), "ben": verdicts("met", "missing", "met")}
    ranked = rank_by_fit([candidate("ana"), candidate("ben")], REQS, judged)

    report = render_report(requirements={**REQS, "notes": "Read years as React years."}, shortlist=ranked[:1],
                           verdicts_by_cid=judged, suggestions={}, changes=[], screening_round=2,
                           corpus_size=100, today=date(2026, 10, 31), also_judged=ranked[1:])

    assert report.startswith("# Screening report: Frontend\nScreening round 2 · 2026-10-31 · 100 resumes searched")
    assert "_Assumptions made reading the request: Read years as React years._" in report
    assert "Also re-judged this round, now below the top 10: Ben (#2, fit 60, No hire)" in report
    assert "## How to read this report" in report and "## What changed" not in report
