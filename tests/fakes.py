"""
Stand-ins for the two things the agent depends on, so every test runs offline in seconds.

FakeCorpus     same methods as corpus.Corpus, over twelve short in-memory resumes
ScriptedClaude same methods as llm.Claude; judges resumes from a fixed verdict table and
               plays back a scripted list of chat replies, recording every call it gets
"""
from __future__ import annotations

import re
from collections import deque

from anthropic.types.beta import BetaMessage

from claude_tasks import (CandidateAssessment, ExtractedRequirements, InterviewQuestion, InterviewQuestions,
                          RequirementVerdict, Suggestions)
from llm import LLMError
from screening import requirement_key

RESUMES = {
    "ana_ruiz": ("Ana Ruiz", "Ana Ruiz\nSenior Frontend Engineer, 2019 - Present\n"
                             "Built React and TypeScript apps for 6 years.\nUsed Next.js for server rendering."),
    "ben_ito": ("Ben Ito", "Ben Ito\nMobile Engineer, 2020 - Present\nBuilt React Native apps for iOS and Android."),
    "cara_lee": ("Cara Lee", "Cara Lee\nFrontend Developer, 2025 - Present\nBuilt React components in JavaScript."),
    "dev_shah": ("Dev Shah", "Dev Shah\nFrontend Engineer, 2018 - Present\nBuilt Vue apps with TypeScript."),
    "eve_moss": ("Eve Moss", "Eve Moss\nFull-Stack Engineer, 2020 - Present\n"
                             "Shipped React features with Node.js and TypeScript."),
    "finn_oak": ("Finn Oak", "Finn Oak\nBackend Engineer, 2017 - Present\nBuilt Go services and React dashboards."),
    "gia_park": ("Gia Park", "Gia Park\nDesigner, 2019 - Present\nDesigned React component libraries in Figma."),
    "hal_reed": ("Hal Reed", "Hal Reed\nData Engineer, 2016 - Present\nBuilt Spark pipelines in Python."),
    "ivy_chen": ("Ivy Chen", "Ivy Chen\nQA Engineer, 2021 - Present\nTested React apps with Cypress."),
    "jo_kim": ("Jo Kim", "Jo Kim\nDevOps Engineer, 2018 - Present\nRan Kubernetes clusters on AWS."),
    "kai_lund": ("Kai Lund", "Kai Lund\nAndroid Engineer, 2019 - Present\nBuilt Kotlin apps."),
    "lia_ross": ("Lia Ross", "Lia Ross\nFrontend Engineer, 2022 - Present\nBuilt Angular apps with TypeScript."),
    "mo_sato": ("Mo Sato", "Mo Sato\nBackend Engineer, 2015 - Present\nBuilt Java services with Spring Boot and Next.js."),
}

# (candidate_id, requirement key) -> (verdict, evidence quoted from the resume above)
VERDICTS = {
    ("ana_ruiz", "3+ years of react"): ("met", "Built React and TypeScript apps for 6 years."),
    ("ben_ito", "3+ years of react"): ("partial", "Built React Native apps for iOS and Android."),
    ("cara_lee", "3+ years of react"): ("partial", "Built React components in JavaScript."),
    ("eve_moss", "3+ years of react"): ("met", "Shipped React features with Node.js and TypeScript."),
    ("finn_oak", "3+ years of react"): ("met", "Built Go services and React dashboards."),
    ("gia_park", "3+ years of react"): ("partial", "Designed React component libraries in Figma."),
    ("ivy_chen", "3+ years of react"): ("partial", "Tested React apps with Cypress."),
    ("ana_ruiz", "typescript"): ("met", "Built React and TypeScript apps for 6 years."),
    ("dev_shah", "typescript"): ("met", "Built Vue apps with TypeScript."),
    ("eve_moss", "typescript"): ("met", "Shipped React features with Node.js and TypeScript."),
    ("lia_ross", "typescript"): ("met", "Built Angular apps with TypeScript."),
    ("ana_ruiz", "next.js"): ("met", "Used Next.js for server rendering."),
    ("mo_sato", "next.js"): ("met", "Built Java services with Spring Boot and Next.js."),
    ("mo_sato", "java"): ("met", "Built Java services with Spring Boot and Next.js."),
    ("jo_kim", "kubernetes"): ("met", "Ran Kubernetes clusters on AWS."),
    # A "met" whose quote is not in the resume: must be scored as partial.
    ("finn_oak", "typescript"): ("met", "Wrote TypeScript for ten years."),
}

REACT_ROLE = {"role_title": "React Developer", "must_have": ["3+ years of React"], "nice_to_have": [], "notes": ""}
BACKEND_ROLE = {"role_title": "Backend Engineer", "must_have": ["Java"], "nice_to_have": ["Kubernetes"], "notes": ""}


class FakeCorpus:
    def __init__(self, files: dict[str, str] | None = None):
        self.candidates = {cid: {"candidate_name": name, "resume_path": f"resumes/{cid}.txt"}
                           for cid, (name, _) in RESUMES.items()}
        self.files = {f"resumes/{cid}.txt": text for cid, (_, text) in RESUMES.items()} | (files or {})
        self.searches: list[str] = []

    @property
    def size(self) -> int:
        return len(self.candidates)

    def name(self, cid: str) -> str:
        return self.candidates[cid]["candidate_name"]

    def find(self, name_or_id: str) -> list[str]:
        wanted = name_or_id.lower()
        if wanted in self.candidates:
            return [wanted]
        return [cid for cid, c in self.candidates.items() if wanted in c["candidate_name"].lower()]

    def resume_text(self, cid: str) -> str:
        return RESUMES[cid][1]

    def search(self, query: str, k: int = 10, must_haves: list[str] = ()) -> list[dict]:
        """Rank by how many query words each resume contains; deterministic, and sensitive to the query."""
        self.searches.append(query)
        words = set(re.findall(r"[a-z.]+", query.lower())) - {"of", "and", "with", "years", "a", "the"}
        scored = []
        for cid, (name, text) in RESUMES.items():
            hits = len(words & set(re.findall(r"[a-z.]+", text.lower())))
            scored.append({"candidate_id": cid, "name": name, "resume_path": f"resumes/{cid}.txt",
                           "rag_score": 50 + 5 * hits, "experience_years": 5.0, "matched_skills": [],
                           "rule_check_failures": []})
        scored.sort(key=lambda c: (-c["rag_score"], c["candidate_id"]))
        return scored[:k]

    def read_file(self, filepath: str) -> dict:
        if filepath not in self.files:
            return {"success": False, "filepath": filepath, "error": f"File not found: {filepath}"}
        return {"success": True, "filepath": filepath, "content": self.files[filepath]}

    def list_files(self, directory: str, extension: str | None = None) -> list[dict]:
        return [{"path": p} for p in sorted(self.files) if p.startswith(directory.rstrip("/") + "/")]

    def search_in_file(self, filepath: str, keyword: str) -> dict:
        text = self.files.get(filepath, "")
        return {"success": filepath in self.files, "filepath": filepath, "keyword": keyword,
                "match_count": text.lower().count(keyword.lower()), "error": None}

    def write_file(self, filepath: str, content: str) -> dict:
        if not filepath.startswith("reports/"):
            return {"success": False, "filepath": filepath, "error": "Access is limited to reports/"}
        if filepath in self.files:
            return {"success": False, "filepath": filepath, "error": f"{filepath} already exists; choose a new name"}
        self.files[filepath] = content
        return {"success": True, "filepath": filepath}

    def exists(self, filepath: str) -> bool:
        return filepath in self.files


def reply(*parts) -> BetaMessage:
    """A scripted Claude response: strings become text blocks, (name, input) tuples tool calls."""
    content, has_tool = [], False
    for i, part in enumerate(parts):
        if isinstance(part, str):
            content.append({"type": "text", "text": part})
        else:
            has_tool = True
            content.append({"type": "tool_use", "id": f"toolu_{i}", "name": part[0], "input": part[1]})
    return BetaMessage.model_validate({
        "id": "msg_test", "type": "message", "role": "assistant", "model": "scripted", "content": content,
        "stop_reason": "tool_use" if has_tool else "end_turn", "stop_sequence": None,
        "usage": {"input_tokens": 1, "output_tokens": 1}})


class ScriptedClaude:
    model = "scripted"

    def __init__(self, requirements: list[dict] | None = None, replies: list[BetaMessage] | None = None):
        self.requirements = deque(requirements or [REACT_ROLE])
        self.replies = deque(replies or [])
        self.judged: list[tuple[str, list[str]]] = []   # (candidate name, requirement texts) per judging call
        self.conversations: list[list[dict]] = []       # messages passed to each converse() call
        self.prompts: list[str] = []                     # prompts passed to each structured() call
        self.fail_next: str | None = None
        self.refuse_to_judge: set[str] = set()   # candidate names whose judging always fails
        self.skip_once: set[str] = set()         # requirement texts left out of the first answer that asks them
        self.usage = {"calls": 0, "input_tokens": 0, "cache_read_input_tokens": 0, "output_tokens": 0}

    def structured(self, *, system: str, prompt: str, schema):
        self.prompts.append(prompt)
        if self.fail_next:
            message, self.fail_next = self.fail_next, None
            raise LLMError(message)
        if schema is ExtractedRequirements:
            return ExtractedRequirements(**{"interview_only": [], **self.requirements.popleft()})
        if schema is CandidateAssessment:
            return self._judge(prompt)
        if schema is Suggestions:
            return Suggestions(suggestions=["Ask how long they have used React in production."])
        if schema is InterviewQuestions:
            count = int(re.search(r"Write (\d+) questions", prompt).group(1))
            return InterviewQuestions(questions=[InterviewQuestion(question=f"Question {i}?", requirement="React",
                                                                   why="Thin evidence.") for i in range(1, count + 1)])
        raise AssertionError(f"unexpected schema {schema}")

    def _judge(self, prompt: str) -> CandidateAssessment:
        name = re.search(r"Candidate: (.+)\n<resume>", prompt).group(1)
        cid = next(c for c, (n, _) in RESUMES.items() if n == name)
        block = re.search(r"<requirements>\n(.*?)\n</requirements>", prompt, re.S).group(1)
        reqs = [re.sub(r"^\d+\. ", "", line) for line in block.splitlines()]
        self.judged.append((name, reqs))
        if name in self.refuse_to_judge:
            raise LLMError("Claude declined this request (category: unspecified).")
        verdicts = []
        for i, text in enumerate(reqs, start=1):
            if text in self.skip_once:
                self.skip_once.discard(text)
                continue
            verdict, evidence = VERDICTS.get((cid, requirement_key(text)), ("missing", ""))
            verdicts.append(RequirementVerdict(requirement_number=i, verdict=verdict, evidence=evidence,
                                               reasoning=f"{name}: {verdict}."))
        return CandidateAssessment(verdicts=verdicts)

    def converse(self, *, system: str, messages: list[dict], tools: list[dict]) -> BetaMessage:
        self.conversations.append(list(messages))
        if self.fail_next:
            message, self.fail_next = self.fail_next, None
            raise LLMError(message)
        return self.replies.popleft()
