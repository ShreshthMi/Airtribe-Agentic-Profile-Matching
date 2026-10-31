Pilot run on labels written by an AI model, not by independent humans; for checking the pipeline only.

# Evaluation against human labels (2026-10-31)

| Posting | Provider | Unlabelled in top 10 | R1 P@5 | R1 P@10 | R1 nDCG@10 | R1 R@10 | R2 P@5 | R2 nDCG@10 | Hire precision | R3 agreement |
|---|---|---|---|---|---|---|---|---|---|---|
| real_backend | huggingface | 0 | 0.40 | 0.50 | 0.50 | n/a | 0.80 | 0.58 | n/a | 0.50 |
| real_backend | ollama | 0 | 1.00 | 1.00 | 1.00 | n/a | 1.00 | 0.99 | n/a | 0.00 |
| real_data | huggingface | 0 | 1.00 | 0.60 | 0.96 | n/a | 0.80 | 0.82 | n/a | 0.40 |
| real_data | ollama | 0 | 1.00 | 0.60 | 0.96 | n/a | 0.80 | 0.83 | n/a | 0.40 |
| real_frontend | huggingface | 0 | 1.00 | 1.00 | 0.92 | 0.56 | 1.00 | 0.93 | n/a | 0.00 |
| real_frontend | ollama | 0 | 0.80 | 0.90 | 0.86 | 0.50 | 1.00 | 0.90 | n/a | 0.10 |
| real_ml | huggingface | 0 | 0.00 | 0.40 | 0.25 | 0.27 | 0.60 | 0.50 | n/a | 0.60 |
| real_ml | ollama | 0 | 0.00 | 0.40 | 0.27 | 0.27 | 0.80 | 0.56 | n/a | 0.60 |
| real_sre | huggingface | 0 | 1.00 | 1.00 | 0.87 | n/a | 1.00 | 0.92 | n/a | 0.00 |
| real_sre | ollama | 0 | 1.00 | 1.00 | 0.97 | n/a | 1.00 | 0.97 | n/a | 0.00 |
| **mean** | huggingface | 0 | 0.68 | 0.70 | 0.70 | 0.41 | 0.84 | 0.75 | n/a | 0.30 |
| **mean** | ollama | 0 | 0.76 | 0.78 | 0.81 | 0.38 | 0.92 | 0.85 | n/a | 0.22 |

Labellers: real_backend: claude; real_data: claude; real_frontend: claude; real_ml: claude; real_sre: claude

How to read this:
- R1 is Round 1's ranking on its own; R2 is after Claude's judgements re-rank the top 10. Round 2 only reorders the top 10, so P@10 and R@10 are the same for both: compare P@5 and nDCG@10.
- Compare providers on R1, which is the only round the embedding model affects. R@10 needs a sheet grading every resume (human_eval.py template --all).
- Hire precision: of the agent's Hire calls, the share the labellers graded 1 or 2. R3 agreement: how often the agent's hire / borderline / no hire equals the labellers' rounded mean grade.
- Metrics skip candidates nobody graded. If 'Unlabelled in top 10' is not 0, a provider found people the labellers never saw; grade them too, or the comparison favours the provider the sheets came from.
- A handful of postings and two labellers show a direction, not a statistically significant result.
