# MSME RAG evaluation

This package measures production retrieval code against a versioned, reviewable pilot set. It does not use an LLM as a judge and it never evaluates or invents eligibility. Questions are synthetic user utterances; expected values are reviewed source identifiers, not factual scheme assertions.

## Dataset and provenance

`datasets/msme-rag-v1.json` is the 31-case tuning set covering all 16 official sources and all 15 business books. `datasets/msme-rag-heldout-v1.json` adds 20 untouched cases split evenly across official and business-guide evidence. Both store the SHA-256 of `apps/worker/sources/official-central.json`. Evaluation stops if the manifest changes, if a target is unknown, or if a target crosses evidence classes.

The labels remain `candidate` until a named human completes `judgment-review-v1.md`. Reports contain the exact dataset SHA-256, and alias promotion rejects candidate labels or reports generated before approval.

## Metrics

The runner executes the application-owned BM25 and vector query builders and its reciprocal-rank fusion. Rankings are deduplicated by `document_id` before measuring:

- hit rate and expected citation-source accuracy at 5;
- recall and nDCG at 10;
- mean reciprocal rank;
- expected-source coverage across the complete corpus;
- citation resolvability against the reviewed manifest URL;
- citation metadata completeness for ID, label, page and section.

Results are split into `official_scheme` and `business_guide` cohorts. Business guides are filtered separately and cannot be treated as support for scheme claims.

## Commands

```bash
make api-install evaluation-install PYTHON="$PWD/.venv/bin/python"
make evaluation-lint evaluation-typecheck evaluation-test PYTHON="$PWD/.venv/bin/python"
make evaluation-local PYTHON="$PWD/.venv/bin/python"
```

Create the separate semantic index only after source/licence, privacy, cost, and OpenAI data-control review:

```bash
cd apps/worker
../../.venv/bin/python -m worker.cli sources/official-central.json \
  --opensearch-url http://127.0.0.1:9200 \
  --index msme-saarthi-semantic-v1 \
  --index-profile production \
  --embedding-provider openai \
  --embedding-model text-embedding-3-large \
  --embedding-dimensions 1024
```

Evaluate it with the exact same model and dimensions:

```bash
cd packages/evaluation
PYTHONPATH=../../apps/api ../../.venv/bin/python -m rag_evaluation.cli \
  datasets/msme-rag-v1.json \
  --manifest ../../apps/worker/sources/official-central.json \
  --index msme-saarthi-semantic-v1 \
  --embedding-provider openai \
  --embedding-model text-embedding-3-large \
  --embedding-dimensions 1024 \
  --output reports/msme-saarthi-semantic-v1.json
```

The runner checks the live index dimension, embedding-model population, chunk count and unique source count before scoring. Provider-backed runs are controlled smoke/evaluation jobs and should not run in normal unit-test CI.

The tuning-selected production fusion contract is RRF rank constant 60, lexical weight 0.8, vector weight 1.0, and at most one chunk per document in each pre-fusion list. Candidate held-out results pass the numerical thresholds, but promotion remains blocked until human approval. After review, regenerate both reports and run:

```bash
../../.venv/bin/python -m rag_evaluation.release \
  --tuning-dataset datasets/msme-rag-v1.json \
  --heldout-dataset datasets/msme-rag-heldout-v1.json \
  --tuning-report reports/msme-saarthi-semantic-v1-tuning-approved.json \
  --heldout-report reports/msme-saarthi-semantic-v1-heldout-approved.json \
  --thresholds release-gates-v1.json \
  --promote
```

This atomically moves `msme-saarthi-semantic-read` only after every gate passes.
