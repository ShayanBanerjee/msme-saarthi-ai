# Relevance judgment review packet v1

**Status:** Awaiting named human reviewer  
**Corpus:** 31 reviewed sources, 12,090 semantic chunks  
**Tuning set:** `datasets/msme-rag-v1.json` — 31 cases  
**Held-out set:** `datasets/msme-rag-heldout-v1.json` — 20 cases

## Reviewer instructions

For every case in both JSON files, inspect the synthetic query and `expected_document_ids` against the reviewed source labels in `apps/worker/sources/official-central.json`.

Approve only when:

1. every listed source is relevant to the query;
2. no clearly relevant reviewed source is missing;
3. official and business-guide evidence classes are never mixed;
4. the query contains no eligibility decision or unsupported factual assertion;
5. the held-out labels were not changed in response to retrieval output.

Record corrections directly in the dataset, then set these fields in both datasets:

```json
"judgment_status": "human_approved",
"reviewed_by": "<reviewer name or controlled reviewer ID>",
"reviewed_at": "2026-07-17"
```

Any change alters the dataset SHA-256. Regenerate both reports after approval; the release gate rejects stale reports automatically.

## Candidate-result context — not a labeling guide

- Tuning hybrid: hit@5 96.77%, MRR 0.782, nDCG@10 0.830.
- Held-out hybrid: hit@5 95.00%, MRR 0.700, nDCG@10 0.764.
- Held-out official: hit@5 90.00%.
- Held-out books: hit@5 100.00%.
- All returned held-out citations: 100% resolvable and metadata-complete.
- Current held-out miss: `heldout-seed-incubators`.

Do not approve a judgment merely to improve these numbers. The release alias remains unchanged until a reviewed, hash-bound rerun passes `release-gates-v1.json`.
