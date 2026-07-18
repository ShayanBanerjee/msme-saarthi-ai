# Semantic retrieval release audit — 2026-07-17

## Source remediation

- MeitY TIDE 2.0 now uses the directly fetchable official administrative-approval PDF from MeitY Startup Hub: 15 chunks.
- ASPIRE now uses the directly fetchable official Ministry of MSME scheme page: 2 chunks.
- `msme-saarthi-semantic-v1` contains 12,090 chunks across all 31 reviewed sources.

## Tuning selection

Nine fusion/diversity configurations were compared on the 31-case tuning set only. The selected configuration keeps RRF rank constant 60, weights lexical at 0.8 and vector at 1.0, and limits each pre-fusion list to one chunk per document.

| Tuning configuration | Hit@5 | MRR | nDCG@10 |
|---|---:|---:|---:|
| Previous: lexical 1.6, no document cap | 93.55% | 0.772 | 0.808 |
| Selected: lexical 0.8, one chunk/document | **96.77%** | **0.782** | **0.830** |

## Untouched held-out result

| Cohort | Cases | Hit@5 | Recall@10 | MRR | nDCG@10 | Citation resolution |
|---|---:|---:|---:|---:|---:|---:|
| Overall | 20 | 95.00% | 95.00% | 0.700 | 0.764 | 100% |
| Official sources | 10 | 90.00% | 90.00% | 0.567 | 0.652 | 100% |
| Business books | 10 | 100.00% | 100.00% | 0.833 | 0.876 | 100% |

The only held-out miss is `heldout-seed-incubators`. All numerical thresholds in `release-gates-v1.json` pass.

## Promotion status

**Not promoted.** Both tuning and held-out labels are explicitly marked `candidate`. The release CLI rejected alias promotion because no named human reviewer has approved the relevance judgments. `msme-saarthi-semantic-read` remains unchanged/absent. After review, both reports must be regenerated because report hashes bind them to the exact reviewed datasets.
