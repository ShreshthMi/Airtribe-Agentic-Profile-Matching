"""
Conversation flows, run end to end through the real compiled LangGraph graph.

Claude and the corpus are the scripted stand-ins from tests/fakes.py, so these tests
check the agent's plumbing - routing, state, tools, re-ranking, reports - and not
Claude's judgement. scenarios/ holds the same flows for running against the real model.
"""
import json
from datetime import date

import pytest
from langgraph.types import Command

from llm import LLMError
from matching_agent import MAX_TOOL_ROUNDS, MatchingAgent
from tests.fakes import BACKEND_ROLE, RESUMES, FakeCorpus, ScriptedClaude, reply

TODAY = date(2026, 10, 31)
REACT_QUERY = "Find me candidates with React and 3+ years experience"


class Session:
    """Drives the graph the way chat.py does: start, then resume at each interrupt."""

    def __init__(self, claude: ScriptedClaude, corpus: FakeCorpus | None = None):
        self.claude, self.corpus = claude, corpus or FakeCorpus()
        self.app = MatchingAgent(claude, self.corpus, TODAY).build()
        self.config = {"configurable": {"thread_id": "test"}}

    def start(self, text: str) -> dict:
        self.app.invoke({"messages": [{"role": "user", "content": text}], "jd_input": text}, self.config)
        return self.state

    def say(self, text: str) -> dict:
        self.app.invoke(Command(resume=text), self.config)
        return self.state

    @property
    def state(self) -> dict:
        return self.app.get_state(self.config).values

    @property
    def next(self) -> tuple:
        return self.app.get_state(self.config).next

    @property
    def last_reply(self) -> str:
        return self.state["messages"][-1]["content"]

    def tool_results(self, call: int) -> list[dict]:
        """The tool results sent back to Claude in its `call`-th converse() request."""
        return self.claude.conversations[call][-1]["content"]


def ids(entries: list[dict]) -> list[str]:
    return [e["candidate_id"] for e in entries]


# --------------------------------------------------------------------------- #
# Flow 1: a natural-language search runs all three screening rounds
# --------------------------------------------------------------------------- #
def test_flow1_natural_language_query_runs_three_rounds_and_waits_for_feedback():
    s = Session(ScriptedClaude())

    state = s.start(REACT_QUERY)

    assert s.next == ("human_feedback",)
    # Round 1: the top 10 of 13 by search score go forward
    assert len(state["round1"]) == 10 and "mo_sato" not in ids(state["round1"])
    # Round 2: one judging call per candidate, each against the single requirement
    assert len(s.claude.judged) == 10 and all(reqs == ["3+ years of React"] for _, reqs in s.claude.judged)
    # Ranked by fit; equal fits fall back to the Round 1 score, then the id
    assert ids(state["shortlist"][:3]) == ["ana_ruiz", "eve_moss", "finn_oak"]
    # Round 3: met -> hire, partial -> borderline (with suggestions), missing -> no hire
    by_id = {e["candidate_id"]: e for e in state["shortlist"]}
    assert by_id["ana_ruiz"]["recommendation"] == "hire"
    assert by_id["ben_ito"]["recommendation"] == "borderline"
    assert by_id["dev_shah"]["recommendation"] == "no_hire"
    assert len(state["suggestions"]) == 4
    # The report was written through the file tools, and the chat got a summary
    report = s.corpus.files["reports/react-developer-2026-10-31-round-1.md"]
    assert "## Shortlist" in report and "Ask how long they have used React" in report
    record = json.loads(s.corpus.files["reports/react-developer-2026-10-31-round-1.json"])
    assert [e["candidate_id"] for e in record["shortlist"]] == ids(state["shortlist"])
    assert record["shortlist"][0]["verdicts"][0]["evidence"] == "Built React and TypeScript apps for 6 years."
    assert "3 hire, 4 borderline, 3 no hire" in s.last_reply


# --------------------------------------------------------------------------- #
# Flow 2: "Compare the top 3 matches side by side"
# --------------------------------------------------------------------------- #
def test_flow2_compare_top_three_side_by_side():
    claude = ScriptedClaude(replies=[
        reply(("compare_candidates", {"candidate_ids": ["ana_ruiz", "Eve Moss", "finn_oak"]})),
        reply("Here they are side by side.")])
    s = Session(claude)
    s.start(REACT_QUERY)

    s.say("Compare the top 3 matches side by side")

    [result] = s.tool_results(1)
    assert not result["is_error"]
    assert "Ana Ruiz (#1)" in result["content"] and "Eve Moss (#2)" in result["content"]
    assert s.last_reply == "Here they are side by side."
    assert s.state["tool_trace"] == ['compare_candidates(candidate_ids=["ana_ruiz", "Eve Moss", "finn_oak"])']
    # Claude saw the screening state alongside the user's words
    snapshot, words = claude.conversations[0][-1]["content"]
    assert "<screening_state>" in snapshot["text"] and "1. Ana Ruiz `ana_ruiz`" in snapshot["text"]
    assert words["text"] == "Compare the top 3 matches side by side"
    assert s.next == ("human_feedback",)


# --------------------------------------------------------------------------- #
# Flow 3: "Why did Ana rank higher than Ben?" - and the question asked the wrong way round
# --------------------------------------------------------------------------- #
def test_flow3_explain_why_one_candidate_ranks_higher():
    claude = ScriptedClaude(replies=[
        reply(("explain_ranking", {"higher_candidate_id": "ana_ruiz", "lower_candidate_id": "ben_ito"})),
        reply("Ana met the React requirement; Ben only partly."),
        reply(("explain_ranking", {"higher_candidate_id": "Ben Ito", "lower_candidate_id": "Ana Ruiz"})),
        reply("It is the other way round.")])
    s = Session(claude)
    s.start(REACT_QUERY)

    s.say("Why did Ana rank higher than Ben?")
    s.say("Why did Ben rank higher than Ana?")

    explanation = s.tool_results(1)[0]["content"]
    assert "3+ years of React (must-have, weight 2): Ana Ruiz met, Ben Ito partial" in explanation
    assert s.tool_results(3)[0]["content"].startswith("Note: it is the other way round - Ana Ruiz ranks above Ben Ito")


# --------------------------------------------------------------------------- #
# Flow 4: changing the requirements mid-conversation re-ranks and explains the changes
# --------------------------------------------------------------------------- #
def test_flow4_refining_requirements_rescreens_and_explains_ranking_changes():
    claude = ScriptedClaude(replies=[
        reply(("update_requirements", {"must_have": ["3+ years of React", "TypeScript"], "nice_to_have": ["Next.js"],
                                       "change_summary": "TypeScript required, Next.js preferred"})),
        reply("Added TypeScript as a must-have and Next.js as a nice-to-have; re-screening now.")])
    s = Session(claude)
    s.start(REACT_QUERY)
    first_shortlist = ids(s.state["shortlist"])

    state = s.say("TypeScript is a must-have too, and Next.js would be nice. Re-rank.")

    assert state["screening_round"] == 2 and s.next == ("human_feedback",)
    assert state["requirements"]["must_have"] == ["3+ years of React", "TypeScript"]
    # Unchanged requirements are never re-judged: the first-round candidates were asked
    # only about the two new requirements, so ranking changes come from the user's change.
    second_round = dict(s.claude.judged[10:])
    first_names = {s.corpus.name(cid) for cid in first_shortlist}
    assert all(second_round[name] == ["TypeScript", "Next.js"] for name in first_names)
    assert all(reqs == ["3+ years of React", "TypeScript", "Next.js"]
               for name, reqs in second_round.items() if name not in first_names)
    # Every previous shortlist member was carried into Round 2 and re-judged
    assert set(first_shortlist) <= set(ids(state["screened"]))
    by_id = {e["candidate_id"]: e for e in state["screened"]}
    assert by_id["ana_ruiz"]["fit_score"] == 100 and by_id["ana_ruiz"]["rank"] == 1
    assert by_id["eve_moss"]["fit_score"] == 80              # React met, TypeScript met, Next.js missing
    assert by_id["finn_oak"]["fit_score"] == 60              # its TypeScript quote is not in the resume
    assert by_id["finn_oak"]["recommendation"] == "borderline"
    # The changes are explained in terms of the new requirements
    finn = next(c for c in state["ranking_changes"] if c["candidate_id"] == "finn_oak")
    assert finn["reasons"] == ["fit 100 -> 60", "changed requirements: TypeScript partial, Next.js missing"]
    assert "**What changed**" in s.last_reply
    assert "## What changed since the last round" in s.corpus.files["reports/react-developer-2026-10-31-round-2.md"]


# --------------------------------------------------------------------------- #
# Flow 5: interview questions aimed at a candidate's gaps
# --------------------------------------------------------------------------- #
def test_flow5_generate_interview_questions():
    claude = ScriptedClaude(replies=[
        reply(("generate_interview_questions", {"candidate_id": "Cara Lee", "count": 3})),
        reply("Here are three questions for Cara.")])
    s = Session(claude)
    s.start(REACT_QUERY)

    s.say("Draft interview questions for Cara Lee")

    content = s.tool_results(1)[0]["content"]
    assert content.count("Probes: React") == 3 and content.startswith("1. Question 1?")


# --------------------------------------------------------------------------- #
# Flow 6: a new job description mid-conversation starts a fresh screening
# --------------------------------------------------------------------------- #
def test_flow6_new_job_description_from_a_file_starts_over():
    corpus = FakeCorpus(files={"job_descriptions/backend.txt": "Backend Engineer\nRequirements\n- Java"})
    claude = ScriptedClaude(requirements=[{"role_title": "React Developer", "must_have": ["3+ years of React"],
                                           "nice_to_have": [], "notes": ""}, BACKEND_ROLE],
                            replies=[reply(("new_job_description", {"job_description": "job_descriptions/backend.txt"})),
                                     reply("Starting a new screening for the backend role.")])
    s = Session(claude, corpus)
    s.start(REACT_QUERY)

    state = s.say("Now screen for job_descriptions/backend.txt instead")

    assert state["job_description"] == "Backend Engineer\nRequirements\n- Java"  # read with the file tools
    assert state["requirements"]["role_title"] == "Backend Engineer"
    assert state["screening_round"] == 1 and state["ranking_changes"] == []   # nothing to diff against
    assert state["shortlist"][0]["candidate_id"] == "mo_sato"
    assert "reports/backend-engineer-2026-10-31-round-1.md" in corpus.files


# --------------------------------------------------------------------------- #
# Flow 7: saying quit ends the graph
# --------------------------------------------------------------------------- #
def test_flow7_quit_ends_the_conversation():
    s = Session(ScriptedClaude())
    s.start(REACT_QUERY)

    s.say("quit")

    assert s.next == ()   # reached END


# --------------------------------------------------------------------------- #
# Flow 8: input that is not a hiring request, or a file that does not exist
# --------------------------------------------------------------------------- #
def test_flow8_non_hiring_input_asks_for_a_job_description_without_searching():
    claude = ScriptedClaude(requirements=[{"role_title": "", "must_have": [], "nice_to_have": [],
                                           "notes": "That is a greeting, not a hiring request."}])
    s = Session(claude)

    s.start("hello there")

    assert s.next == ("human_feedback",)
    assert s.last_reply.startswith("I didn't find a job to screen for in that.")
    assert "job_descriptions/frontend_engineer.txt" in s.last_reply
    assert s.corpus.searches == []


def test_flow8_missing_job_description_file_is_reported():
    s = Session(ScriptedClaude())

    s.start("job_descriptions/missing.txt")

    assert s.next == ("human_feedback",)
    assert "I couldn't open `job_descriptions/missing.txt`" in s.last_reply


# --------------------------------------------------------------------------- #
# Flow 9: failures - a tool error goes back to Claude; a Claude outage can be retried
# --------------------------------------------------------------------------- #
def test_flow9_tool_error_is_returned_to_claude_not_raised():
    claude = ScriptedClaude(replies=[
        reply(("explain_ranking", {"higher_candidate_id": "nobody", "lower_candidate_id": "ana_ruiz"})),
        reply("I couldn't find anyone called 'nobody'.")])
    s = Session(claude)
    s.start(REACT_QUERY)

    s.say("Why is nobody above Ana?")

    [result] = s.tool_results(1)
    assert result["is_error"] and "No candidate matches 'nobody'" in result["content"]
    assert s.state["tool_trace"][0].endswith("[error]")


def test_flow9_claude_failure_mid_turn_can_be_retried():
    claude = ScriptedClaude(replies=[reply("Ana is the strongest.")])
    s = Session(claude)
    s.start(REACT_QUERY)
    claude.fail_next = "Rate limited by the Anthropic API."

    with pytest.raises(LLMError):
        s.say("Who is the strongest?")
    assert s.next == ("agent_turn",)   # the user's message is kept; only the failed step re-runs

    s.app.invoke(None, s.config)

    assert s.last_reply == "Ana is the strongest."
    assert [m["content"] for m in s.state["messages"]].count("Who is the strongest?") == 1


def test_flow9_runaway_tool_loop_is_cut_off():
    loop = [reply(("search_resumes", {"query": "react", "top_k": 3})) for _ in range(MAX_TOOL_ROUNDS)]
    s = Session(ScriptedClaude(replies=loop))
    s.start(REACT_QUERY)

    s.say("Keep searching")

    assert f"I stopped after {MAX_TOOL_ROUNDS} rounds of tool calls" in s.last_reply
    assert s.next == ("human_feedback",)


# --------------------------------------------------------------------------- #
# Robustness: a resume Claude will not judge, an oversized message, report names
# --------------------------------------------------------------------------- #
def test_a_candidate_claude_cannot_judge_is_left_out_and_retried_at_the_next_rescreen():
    claude = ScriptedClaude(replies=[
        reply(("update_requirements", {"must_have": ["3+ years of React", "TypeScript"], "nice_to_have": [],
                                       "change_summary": "add TypeScript"})),
        reply("Added TypeScript.")])
    claude.refuse_to_judge = {"Ben Ito"}
    s = Session(claude)

    state = s.start(REACT_QUERY)

    assert "ben_ito" not in ids(state["screened"]) and len(state["shortlist"]) == 9
    assert state["unjudged"] == [{"candidate_id": "ben_ito", "name": "Ben Ito",
                                  "reason": "Claude declined this request (category: unspecified)."}]
    assert "Could not be judged this round" in s.last_reply and "Ben Ito" in s.last_reply

    claude.refuse_to_judge = set()
    state = s.say("Add TypeScript as a must-have")

    assert ("Ben Ito", ["3+ years of React", "TypeScript"]) in s.claude.judged[10:]
    assert state["unjudged"] == []


def test_an_oversized_message_is_refused_and_kept_out_of_the_history():
    s = Session(ScriptedClaude())
    s.start(REACT_QUERY)
    before = len(s.state["messages"])

    s.say("x" * 9000)

    assert s.next == ("human_feedback",) and "9,000 characters" in s.last_reply
    assert len(s.state["messages"]) == before + 1  # only the agent's reply was added
    assert s.claude.conversations == []            # Claude was never called


def test_reports_are_never_overwritten():
    corpus = FakeCorpus(files={"reports/react-developer-2026-10-31-round-1.md": "an earlier session's report"})
    s = Session(ScriptedClaude(), corpus)

    s.start(REACT_QUERY)

    assert corpus.files["reports/react-developer-2026-10-31-round-1.md"] == "an earlier session's report"
    assert s.state["report_path"] == "reports/react-developer-2026-10-31-round-1-2.md"
    assert "reports/react-developer-2026-10-31-round-1-2.json" in corpus.files


def test_a_round_where_nobody_can_be_judged_fails_loudly_and_can_be_retried():
    claude = ScriptedClaude()
    claude.refuse_to_judge = {name for name, _ in RESUMES.values()}
    s = Session(claude)

    with pytest.raises(LLMError):
        s.start(REACT_QUERY)
    assert s.next == ("rank_candidates",)  # no empty "successful" round, no report written
    assert not any(path.startswith("reports/") for path in s.corpus.files)

    claude.refuse_to_judge = set()
    s.app.invoke(None, s.config)

    assert len(s.state["shortlist"]) == 10 and s.next == ("human_feedback",)


def test_a_shortlisted_candidate_who_cannot_be_rejudged_is_named_in_the_changes_and_can_be_retried():
    claude = ScriptedClaude(replies=[
        reply(("update_requirements", {"must_have": ["3+ years of React", "TypeScript"], "nice_to_have": [],
                                       "change_summary": "add TypeScript"})),
        reply("Added TypeScript."),
        reply(("update_requirements", {"must_have": ["3+ years of React", "TypeScript"], "nice_to_have": [],
                                       "change_summary": "re-screen"})),
        reply("Re-screening to try Ana again.")])
    s = Session(claude)
    s.start(REACT_QUERY)
    claude.refuse_to_judge = {"Ana Ruiz"}

    state = s.say("Add TypeScript as a must-have")

    ana = next(c for c in state["ranking_changes"] if c["candidate_id"] == "ana_ruiz")
    assert ana["old_rank"] == 1 and ana["new_rank"] is None
    assert "Ana Ruiz: #1 -> not ranked this round (could not be judged this round" in s.last_reply

    claude.refuse_to_judge = set()
    state = s.say("Please re-screen")

    assert state["screening_round"] == 3 and state["unjudged"] == []
    assert state["shortlist"][0]["candidate_id"] == "ana_ruiz"
