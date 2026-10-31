# Evaluation against human labels (2026-10-31)

| Posting | Provider | Unlabelled in top 10 | R1 P@5 | R1 P@10 | R1 nDCG@10 | R1 R@10 | R2 P@5 | R2 nDCG@10 | Hire precision | R3 agreement |
|---|---|---|---|---|---|---|---|---|---|---|
| real_backend | huggingface | 0 | 0.80 | 0.60 | 0.69 | n/a | 0.40 | 0.47 | n/a | 0.40 |
| real_backend | ollama | 0 | 0.60 | 0.70 | 0.59 | n/a | 0.60 | 0.57 | n/a | 0.30 |
| real_data | huggingface | 0 | 0.80 | 0.70 | 0.68 | n/a | 0.60 | 0.73 | n/a | 0.30 |
| real_data | ollama | 0 | 0.80 | 0.80 | 0.75 | n/a | 0.60 | 0.80 | n/a | 0.20 |
| real_sre | huggingface | 0 | 0.80 | 0.70 | 0.88 | n/a | 0.80 | 0.88 | n/a | 0.30 |
| real_sre | ollama | 0 | 0.60 | 0.70 | 0.87 | n/a | 1.00 | 0.90 | n/a | 0.30 |
| **mean** | huggingface | 0 | 0.80 | 0.67 | 0.75 | n/a | 0.60 | 0.69 | n/a | 0.33 |
| **mean** | ollama | 0 | 0.67 | 0.73 | 0.74 | n/a | 0.73 | 0.75 | n/a | 0.27 |

Labellers: real_backend: self; real_data: self; real_sre: self

How to read this:
- R1 is Round 1's ranking on its own; R2 is after Claude's judgements re-rank the top 10. Round 2 only reorders the top 10, so P@10 and R@10 are the same for both: compare P@5 and nDCG@10.
- Compare providers on R1, which is the only round the embedding model affects. R@10 needs a sheet grading every resume (human_eval.py template --all).
- Hire precision: of the agent's Hire calls, the share the labellers graded 1 or 2. R3 agreement: how often the agent's hire / borderline / no hire equals the labellers' rounded mean grade.
- Metrics skip candidates nobody graded. If 'Unlabelled in top 10' is not 0, a provider found people the labellers never saw; grade them too, or the comparison favours the provider the sheets came from.
- A handful of postings and two labellers show a direction, not a statistically significant result.
