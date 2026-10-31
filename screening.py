"""
Multi-round screening rules: how candidates are scored, ranked, recommended and explained.

Nothing in this file calls Claude or touches the disk, so every rule is a plain function
that can be read and tested on its own. Claude's job (claude_tasks.py) is narrow: judge
each requirement against a resume as met, partial or missing, quoting the resume as
evidence. This file turns those judgements into numbers and sentences.

  Round 1  rank all 100 resumes with Milestone 2's hybrid RAG search; keep the top 10
  Round 2  Claude judges the 10 against every requirement; fit score; re-rank
  Round 3  hire / borderline / no-hire, from the must-have judgements alone

Because the score is a fixed formula over the judgements, "why did A rank above B?" always
has an exact answer: the requirements where their judgements differ.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import date

MUST_WEIGHT = 2
NICE_WEIGHT = 1
CREDIT = {"met": 1.0, "partial": 0.5, "missing": 0.0}
SYMBOL = {"met": "✓ met", "partial": "~ partial", "missing": "✗ missing"}
LABEL = {"hire": "Hire", "borderline": "Borderline", "no_hire": "No hire"}


# --------------------------------------------------------------------------- #
# Requirements
# --------------------------------------------------------------------------- #
def requirement_key(text: str) -> str:
    """Stable id for a requirement, so 'React ' and 'react' share one cached verdict."""
    return re.sub(r"\s+", " ", text).strip().rstrip(".").lower()


def weighted_requirements(requirements: dict) -> list[tuple[str, str, int]]:
    """[(requirement text, 'must'|'nice', weight), ...] in display order."""
    return ([(r, "must", MUST_WEIGHT) for r in requirements.get("must_have", [])]
            + [(r, "nice", NICE_WEIGHT) for r in requirements.get("nice_to_have", [])])


def current_verdicts(requirements: dict, verdicts: dict[str, dict]) -> dict[str, dict]:
    """A candidate's verdicts on the current requirements only, in display order.

    The cache keeps verdicts on requirements the user has since dropped, so that adding
    one back costs nothing; anything shown to Claude or the user must leave those out.
    """
    keys = [requirement_key(text) for text, _, _ in weighted_requirements(requirements)]
    return {k: verdicts[k] for k in keys if k in verdicts}


def interview_checks(requirements: dict) -> list[str]:
    """Requirements a resume cannot show: listed for the interview, never scored."""
    return list(requirements.get("interview_only", []))


def suggestion_key(candidate_id: str, requirements: dict) -> str:
    """Cache key for Round 3 suggestions, which depend on the whole requirement set."""
    keys = sorted(f"{kind}:{requirement_key(text)}" for text, kind, _ in weighted_requirements(requirements))
    return candidate_id + "|" + "|".join(keys)


def requirement_changes(old: dict | None, new: dict) -> dict[str, list[str]]:
    """What the user changed between two requirement sets."""
    old = old or {"must_have": [], "nice_to_have": []}
    old_must = {requirement_key(r): r for r in old["must_have"]}
    old_nice = {requirement_key(r): r for r in old["nice_to_have"]}
    new_must = {requirement_key(r): r for r in new["must_have"]}
    new_nice = {requirement_key(r): r for r in new["nice_to_have"]}
    return {
        "added_must": [r for k, r in new_must.items() if k not in old_must and k not in old_nice],
        "added_nice": [r for k, r in new_nice.items() if k not in old_must and k not in old_nice],
        "now_must": [r for k, r in new_must.items() if k in old_nice],
        "now_nice": [r for k, r in new_nice.items() if k in old_must],
        "removed": [r for k, r in {**old_must, **old_nice}.items() if k not in new_must and k not in new_nice],
    }


# --------------------------------------------------------------------------- #
# Evidence
# --------------------------------------------------------------------------- #
MIN_QUOTE_WORDS = 3      # a fragment shorter than this ("C", "Java") proves nothing
MAX_FRAGMENTS = 3        # a quote may skip text with "..." at most twice
MAX_SKIPPED_WORDS = 40   # and only within one passage, not across the whole resume
# A word: letters and digits, keeping "c++", "c#", "node.js" and "o'neill" whole. Matching
# whole words means "Java" can never be found inside "JavaScript", nor ".NET" in "internet".
_WORD = re.compile(r"[^\W_]+(?:[+#]+|(?:[.'’][^\W_]+)+)?")
_ELLIPSIS = re.compile(r"\[?\s*(?:\.\s*){2,}\]?|\[?…\]?")


def _words(text: str) -> list[str]:
    """Lower-cased words, ignoring punctuation, bullets and line breaks; NFKC folds ligatures and accents."""
    return _WORD.findall(unicodedata.normalize("NFKC", text).casefold())


def evidence_found(quote: str, resume_text: str) -> bool:
    """True when the quoted evidence really is in the resume.

    This is the guard against an invented qualification: a 'met' judgement whose quote
    cannot be found counts only as 'partial' and is flagged in the report. Quotes are
    compared word by word, so a quote that spans a line break or a bullet still matches.
    A quote may skip text with '...', but every fragment must be at least three words and
    the fragments must sit close together, in order, so unrelated phrases from different
    parts of the resume cannot be stitched into a claim.
    """
    fragments = [f for f in (_words(part) for part in _ELLIPSIS.split(quote)) if f]
    if not fragments or len(fragments) > MAX_FRAGMENTS or min(map(len, fragments)) < MIN_QUOTE_WORDS:
        return False
    return _in_order(_words(resume_text), fragments, start=0, stop=None)


def _in_order(words: list[str], fragments: list[list[str]], start: int, stop: int | None) -> bool:
    """Do the fragments occur in `words` in order, the first starting in [start, stop]?"""
    if not fragments:
        return True
    first, rest = fragments[0], fragments[1:]
    last_start = len(words) - len(first) if stop is None else min(stop, len(words) - len(first))
    for i in range(start, last_start + 1):
        end = i + len(first)
        if words[i:end] == first and _in_order(words, rest, end, end + MAX_SKIPPED_WORDS):
            return True
    return False


def effective_verdict(verdict: dict) -> str:
    """The verdict the score uses: an unverifiable 'met' only counts as 'partial'."""
    if verdict["verdict"] == "met" and not verdict.get("evidence_verified", False):
        return "partial"
    return verdict["verdict"]


# --------------------------------------------------------------------------- #
# Round 2: fit score and ranking.   Round 3: recommendation.
# --------------------------------------------------------------------------- #
def fit_score(requirements: dict, verdicts: dict[str, dict]) -> int:
    """Weighted share of requirements met, 0-100. Must-haves count double."""
    weighted = weighted_requirements(requirements)
    total = sum(weight for _, _, weight in weighted)
    if not total:
        return 0
    earned = sum(weight * CREDIT[effective_verdict(verdicts[requirement_key(text)])]
                 for text, _, weight in weighted)
    return round(100 * earned / total)


def recommendation(requirements: dict, verdicts: dict[str, dict]) -> tuple[str, str]:
    """(hire | borderline | no_hire, reason), decided by the must-haves alone."""
    musts = requirements.get("must_have", [])
    if not musts:
        return "borderline", "No must-haves were set, so there is nothing to decide hire or no-hire on."
    status = {r: effective_verdict(verdicts[requirement_key(r)]) for r in musts}
    missing = [r for r, v in status.items() if v == "missing"]
    partial = [r for r, v in status.items() if v == "partial"]
    if missing:
        return "no_hire", "Misses must-have: " + "; ".join(missing) + "."
    if partial:
        return "borderline", "Only partly meets must-have: " + "; ".join(partial) + "."
    return "hire", "Meets every must-have, with evidence quoted from the resume."


def rank_by_fit(candidates: list[dict], requirements: dict, verdicts_by_cid: dict[str, dict]) -> list[dict]:
    """Rank judged candidates by fit; Round 1's RAG score breaks ties. The caller keeps the top 10."""
    entries = []
    for cand in candidates:
        verdicts = verdicts_by_cid[cand["candidate_id"]]
        rec, reason = recommendation(requirements, verdicts)
        musts = [effective_verdict(verdicts[requirement_key(r)]) for r in requirements.get("must_have", [])]
        entries.append({**cand, "fit_score": fit_score(requirements, verdicts), "recommendation": rec,
                        "recommendation_reason": reason,
                        "must_haves_met": f"{musts.count('met')}/{len(musts)}"})
    entries.sort(key=lambda e: (-e["fit_score"], -e["rag_score"], e["candidate_id"]))
    return [{**e, "rank": i} for i, e in enumerate(entries, start=1)]


# --------------------------------------------------------------------------- #
# Explanations
# --------------------------------------------------------------------------- #
def explain_pair(higher: dict, lower: dict, requirements: dict, verdicts_by_cid: dict[str, dict]) -> str:
    """Why `higher` is ranked above `lower`: the requirements where their judgements differ."""
    lines = [f"{higher['name']} is #{higher['rank']} with fit {higher['fit_score']}; "
             f"{lower['name']} is #{lower['rank']} with fit {lower['fit_score']}."]
    a, b = verdicts_by_cid[higher["candidate_id"]], verdicts_by_cid[lower["candidate_id"]]
    differences = []
    for text, kind, weight in weighted_requirements(requirements):
        va, vb = a[requirement_key(text)], b[requirement_key(text)]
        if effective_verdict(va) != effective_verdict(vb):
            gap = weight * (CREDIT[effective_verdict(va)] - CREDIT[effective_verdict(vb)])
            differences.append((gap, f"- {text} ({kind}-have, weight {weight}): "
                                     f"{higher['name']} {effective_verdict(va)}, {lower['name']} {effective_verdict(vb)}."
                                     f" {higher['name']}: {va['reasoning']} {lower['name']}: {vb['reasoning']}"))
    if differences:
        lines.append("Requirements where they differ (largest effect first):")
        lines += [line for _, line in sorted(differences, key=lambda d: -abs(d[0]))]
    if higher["fit_score"] == lower["fit_score"]:
        lines.append(f"Their fit scores tie, so Round 1's RAG score decided it: "
                     f"{higher['rag_score']} vs {lower['rag_score']}.")
    return "\n".join(lines)


def ranking_changes(old: list[dict], ranked: list[dict], old_reqs: dict | None, new_reqs: dict,
                    verdicts_by_cid: dict[str, dict], size: int) -> list[dict]:
    """Who moved between two screening rounds, and the requirement changes that moved them.

    `old` is the previous shortlist; `ranked` is everyone judged this round, best first,
    of whom the top `size` form the new shortlist. Previous shortlist members are always
    re-judged, so leaving the list is explained by fit, never by a change in the search.
    """
    before = {e["candidate_id"]: e for e in old}
    changed = requirement_changes(old_reqs, new_reqs)
    changes = []
    for entry in ranked:
        prev, listed = before.get(entry["candidate_id"]), entry["rank"] <= size
        if _nothing_to_report(prev, entry, listed):
            continue
        changes.append({"candidate_id": entry["candidate_id"], "name": entry["name"],
                        "old_rank": prev["rank"] if prev else None, "new_rank": entry["rank"] if listed else None,
                        "ranked_at": entry["rank"],
                        "reasons": _reasons(prev, entry, changed, verdicts_by_cid.get(entry["candidate_id"], {}))})
    return sorted(changes, key=lambda c: (c["new_rank"] is None, c["new_rank"] or 0, c["old_rank"] or 0))


def _nothing_to_report(prev: dict | None, entry: dict, listed: bool) -> bool:
    """Skip people who were never on the shortlist, and people whose rank and fit did not move."""
    if prev is None:
        return not listed
    return listed and (prev["rank"], prev["fit_score"]) == (entry["rank"], entry["fit_score"])


def _reasons(prev: dict | None, entry: dict, changed: dict[str, list[str]], verdicts: dict[str, dict]) -> list[str]:
    """Why one candidate moved: their fit, then their verdicts on each requirement that changed."""
    if prev is None:
        fit = f"new to the shortlist, fit {entry['fit_score']}"
    elif prev["fit_score"] == entry["fit_score"]:
        fit = f"fit unchanged at {entry['fit_score']}"
    else:
        fit = f"fit {prev['fit_score']} -> {entry['fit_score']}"

    def judged(requirements: list[str]) -> str:
        return ", ".join(f"{r} {effective_verdict(verdicts[requirement_key(r)])}"
                         for r in requirements if requirement_key(r) in verdicts)

    now_counted = judged(changed["added_must"] + changed["added_nice"] + changed["now_must"] + changed["now_nice"])
    no_longer_counted = judged(changed["removed"])
    return ([fit] + ([f"changed requirements: {now_counted}"] if now_counted else [])
            + ([f"dropped requirements: {no_longer_counted}"] if no_longer_counted else []))


def describe_change(change: dict) -> str:
    """One line such as 'Kenji Watanabe: #3 -> #8 (fit 80 -> 50; changed requirements: TypeScript missing)'."""
    reasons = "; ".join(change["reasons"])
    if change["old_rank"] and change["old_rank"] == change["new_rank"]:
        return f"{change['name']}: stays #{change['new_rank']} ({reasons})"
    old = f"#{change['old_rank']}" if change["old_rank"] else "new"
    if change["new_rank"]:
        new = f"#{change['new_rank']}"
    elif change["ranked_at"]:
        new = f"off the shortlist (now #{change['ranked_at']})"
    else:
        new = "not ranked this round"
    return f"{change['name']}: {old} -> {new} ({reasons})"


def comparison_table(entries: list[dict], requirements: dict, verdicts_by_cid: dict[str, dict]) -> str:
    """Side-by-side Markdown table: one column per candidate, one row per requirement."""
    header = "| | " + " | ".join(f"{e['name']} (#{e['rank']})" if e.get("rank") else e["name"] for e in entries) + " |"
    rows = [header, "|---" * (len(entries) + 1) + "|",
            "| Fit score | " + " | ".join(str(e["fit_score"]) for e in entries) + " |",
            "| Recommendation | " + " | ".join(LABEL[e["recommendation"]] for e in entries) + " |",
            "| Round 1 RAG score | " + " | ".join(str(e["rag_score"]) for e in entries) + " |"]
    for text, kind, _ in weighted_requirements(requirements):
        cells = []
        for e in entries:
            v = verdicts_by_cid[e["candidate_id"]][requirement_key(text)]
            flag = "" if v["verdict"] != "met" or v["evidence_verified"] else " (quote not found)"
            cells.append(SYMBOL[effective_verdict(v)] + flag)
        rows.append(f"| {text} ({kind}) | " + " | ".join(cells) + " |")
    return "\n".join(rows)


def candidate_report(entry: dict, requirements: dict, verdicts: dict[str, dict],
                     suggestions: list[str] | None = None) -> str:
    """Strengths, gaps and evidence for one candidate, as Markdown."""
    strengths, gaps = [], []
    for text, kind, _ in weighted_requirements(requirements):
        v = verdicts[requirement_key(text)]
        quote = f' - "{" ".join(v["evidence"].split())}"' if v["evidence"] else ""  # quotes can span lines
        line = f"- **{text}** ({kind}-have): {v['reasoning']}{quote}"
        if v["verdict"] == "met" and not v["evidence_verified"]:
            line += " _(the quoted evidence could not be found in the resume, so this counts as partial)_"
        (strengths if effective_verdict(v) == "met" else gaps).append(line)
    parts = [f"### {entry.get('rank') or '-'}. {entry['name']} ({entry['candidate_id']}) - "
             f"{LABEL[entry['recommendation']]}, fit {entry['fit_score']}",
             f"{entry['recommendation_reason']} Resume: `{entry['resume_path']}`. "
             f"Round 1 RAG score {entry['rag_score']}.",
             "**Strengths**", *(strengths or ["- none of the requirements is clearly met"]),
             "**Gaps**", *(gaps or ["- none"])]
    if entry.get("rule_check_failures"):
        parts += ["**Round 1 rule checks** (Milestone 2's vocabulary and date arithmetic, shown for comparison; "
                  "Round 2's judgement above is the one that counts)",
                  *[f"- {f}" for f in entry["rule_check_failures"]]]
    if suggestions:
        parts += ["**Improvement suggestions**", *[f"- {s}" for s in suggestions]]
    return "\n".join(parts)


def render_report(*, requirements: dict, shortlist: list[dict], verdicts_by_cid: dict[str, dict],
                  suggestions: dict[str, list[str]], changes: list[dict], screening_round: int,
                  corpus_size: int, today: date, also_judged: list[dict] = ()) -> str:
    """The full Markdown report written after every screening round.

    `also_judged` lists candidates judged this round who did not make the shortlist
    (previous shortlist members who fell below the top 10 after a change).
    """
    title = requirements.get("role_title") or "Untitled role"
    parts = [f"# Screening report: {title}",
             f"Screening round {screening_round} · {today.isoformat()} · {corpus_size} resumes searched", "",
             "## Requirements",
             *[f"- {text} ({kind}-have)" for text, kind, _ in weighted_requirements(requirements)],
             *[f"- {text} (check in the interview; not screened)" for text in interview_checks(requirements)]]
    if requirements.get("notes"):
        parts.append(f"\n_Assumptions made reading the request: {requirements['notes']}_")
    if changes:
        parts += ["", "## What changed since the last round", *[f"- {describe_change(c)}" for c in changes]]
    parts += ["", "## Shortlist", "| # | Candidate | Fit | Must-haves met | Round 1 RAG | Recommendation |",
              "|---|---|---|---|---|---|",
              *[f"| {e['rank']} | {e['name']} (`{e['candidate_id']}`) | {e['fit_score']} | {e['must_haves_met']} | "
                f"{e['rag_score']} | {LABEL[e['recommendation']]} |" for e in shortlist]]
    if also_judged:
        parts += ["", "Also re-judged this round, now below the top 10: " + ", ".join(
            f"{e['name']} (#{e['rank']}, fit {e['fit_score']}, {LABEL[e['recommendation']]})" for e in also_judged)]
    parts += ["", "## Candidates"]
    for entry in shortlist:
        parts += [candidate_report(entry, requirements, verdicts_by_cid[entry["candidate_id"]],
                                   suggestions.get(entry["candidate_id"])), ""]
    parts += ["## How to read this report",
              "- **Round 1** ranked every resume with Milestone 2's hybrid search (embeddings, BM25, skill match) "
              "and kept the top 10; on a re-screen the previous shortlist is carried forward too, so nobody "
              "leaves the list because the search changed. Nobody is rejected at this stage.",
              f"- **Round 2**: Claude judged each requirement as met, partial or missing, quoting the resume. "
              f"Fit = weighted share met (must-have x{MUST_WEIGHT}, nice-to-have x{NICE_WEIGHT}; partial = half). "
              "A 'met' whose quote is not in the resume counts as partial.",
              "- **Round 3**: Hire = every must-have met; No hire = a must-have missing; Borderline = in between.",
              "- Requirements a resume cannot show (communication, attitude, working style) are interview "
              "checks: listed above, but they affect neither the fit score nor the recommendation.",
              "- These are screening recommendations for a human decision-maker, not hiring decisions."]
    return "\n".join(parts) + "\n"
