# Milestone 2 RAG code (vendored)

`resume_rag.py`, `job_matcher.py`, `resume_loader.py` and `milestone1_tools/` are
**verbatim copies** of the Milestone 2 deliverable, which itself vendors the Milestone 1
file tools (see `milestone1_tools/PROVENANCE.md`). Nothing in this folder was edited.

| | |
|---|---|
| Source repository | `Airtribe-RAG-based-profile-matching` |
| Commit | `cfb3cc540482cbefa3c8669ff3e87723b1421576` (`cfb3cc5`, 2026-10-18) |
| Copied on | 2026-10-31 |
| `resume_rag.py` | sha256 `e526d5ac38c0b3519a835bd081a9ce4490783d2b400131ddce362af5a9426762` |
| `job_matcher.py` | sha256 `25caa1bdce50491118959f7917dea33de2d40d8bfbf4efe5af6ddda5d0eecaf8` |
| `resume_loader.py` | sha256 `53491ab32323d5683c0a480c6ef52b2320500f9357ad5a1e3d4436baa52c1b77` |
| `milestone1_tools/fs_tools.py` | sha256 `9d7ea00f75843ec863dfa722d7d0442a1a5651b39890c93acc62a803b8464e38` |
| `milestone1_tools/extractors.py` | sha256 `239a72f23c5ba5b8d731a0d89773c85ef58de49e973a1278c06277960ef84cda` |

Check the copies are still verbatim:

```bash
shasum -a 256 milestone2_rag/*.py milestone2_rag/milestone1_tools/*.py
```

## How this project uses them

Only `corpus.py` imports this folder. It puts the folder on `sys.path` (the modules import
each other by top-level name, so turning them into a package would mean editing them) and
uses:

* `job_matcher.JobMatcher.match()` for Round 1, with `apply_filters=False`: Milestone 2's
  must-have checks rest on a fixed 73-skill vocabulary and date arithmetic, so in this
  project they annotate candidates instead of rejecting them, and Round 2 decides.
* `resume_rag.py`'s CLI to build the ChromaDB index over `resumes/`.
* `milestone1_tools/fs_tools.py` (`read_file`, `list_files`, `search_in_file`,
  `write_file`) for every file the agent reads or writes, confined by
  `resume_loader.sandbox_root()`.
