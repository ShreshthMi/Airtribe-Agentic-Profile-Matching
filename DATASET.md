# Dataset card

100 resumes and 7 job descriptions. Every person in the dataset is fictional.

| Path | What it holds |
|---|---|
| `resumes/` | 100 resumes in one flat folder: 47 `.md`, 39 `.txt`, 8 `.docx`, 6 `.pdf` |
| `job_descriptions/` | 7 job descriptions, carried over from Milestone 2 |

## Where the resumes come from

| Source | Count | Notes |
|---|---|---|
| Milestone 2 corpus | 43 | Copied unchanged from `Airtribe-RAG-based-profile-matching/resumes` (commit `cfb3cc5`); its own dataset card describes them |
| Generated for this milestone | 57 | `scripts/generate_resumes.py`; fictional people and employers, `example.com` emails |

Each generated person is written out by hand in the script as a career: a list of roles,
oldest first, each with its length and the stack used in it. Only the wording of the bullet
points comes from templates, so the text is more formulaic than a real resume, and the
script is deterministic (`.md`, `.txt` and `.pdf` files are byte-identical on every run;
`tests/test_generate_resumes.py` checks the committed files still match it).

## Coverage

| Role family | Milestone 2 | Added | Total |
|---|---|---|---|
| Frontend and full-stack JavaScript | 5 | 15 | 20 |
| ML and AI engineering | 10 | 6 | 16 |
| Backend | 6 | 9 | 15 |
| Data science and analytics | 5 | 5 | 10 |
| DevOps, SRE and cloud | 4 | 6 | 10 |
| Mobile | 4 | 5 | 9 |
| Data engineering | 3 | 5 | 8 |
| Product, design and engineering management | 4 | 2 | 6 |
| QA and test automation | 0 | 3 | 3 |
| Application security | 1 | 1 | 2 |
| Embedded systems | 1 | 0 | 1 |

Frontend was grown the most because the brief's example query is about React: twenty
JavaScript resumes give "React and 3+ years" a real top-10 cut from a field of near misses.

## Deliberate traps

Each of these is a resume where a keyword match and a careful reading disagree. They are
what Round 2 exists for: Milestone 2's rule checks rest on a fixed 73-skill vocabulary and
date arithmetic, and Round 1 deliberately does not reject anyone on them.

| Resume | The trap | Milestone 2's rule check | A careful reading |
|---|---|---|---|
| `kenji_watanabe.md`, `minh_nguyen.txt` | React Native only, 4.6-5.5 years | "React Native" matches the React vocabulary entry, so "3+ years React" passes | React Native is not React for the web: partial |
| `chloe_martin.md` | 4.5 years of Angular, then React since Sep 2025; the summary says "now building React" | 1.2 years React | Partial for "3+ years of React" |
| `jonas_weber.md` | 1.5 years of React, then 2.7 years of Svelte | Svelte is not in the vocabulary | Under 3 years of React; Svelte is invisible to the rules |
| `tomasz_kowalski.md` | Java backend; React only in a weekend side project | React counted as a skill | Not professional React experience |
| `benjamin_carter.md` | 6.5 years of React, but the last 3.2 years as an engineering manager | 6.5 years React passes | Met on years, but not hands-on recently |
| `patrick_oneill.txt` | Skills list names ten technologies; the only job is 2 years of WordPress and PHP | Every listed skill is credited | Most skills appear in no job: partial at best |
| `ayesha_siddiqui.txt` | QA engineer using "React Testing Library" | Counted towards React | Tests React apps; does not build them |
| `elif_yildiz.txt`, `lucas_moreau.docx` | Vue-only and Angular-only frontend engineers | No React (correct) | Strong frontend, wrong framework |
| `aaliyah_johnson.txt` | Bootcamp graduate, 1.1 years of React | 1.1 years | Partial |
| `natalia_popescu.txt` | 1.75-year career break between two Java roles, listed with its dates | 7.9 years: the break's date range is counted as work | 6.2 years worked |
| `oscar_mendes.md`, `jakub_novotny.md`, `kofi_asante.md` | Elixir/Phoenix, Flink, Databricks | Outside the vocabulary: invisible | Read like any other skill |

## Job descriptions

The seven job descriptions from Milestone 2 (senior ML engineer, backend, data engineer,
frontend, SRE, data scientist, mobile). The agent also accepts any pasted text or a
one-line description such as "Find me candidates with React and 3+ years experience".

## What this dataset cannot support

Milestone 2's review asked for evaluation against independent, human-labelled data. That
is still the gap: the resumes, the traps above and the agent were all written within this
project, so a trap the agent catches is a trap its author knew to set. The traps show the
agent behaves as designed, not that it generalises. `scripts/human_eval.py` (see the README)
sets up the blind labelling a human reviewer would need to measure it properly.
