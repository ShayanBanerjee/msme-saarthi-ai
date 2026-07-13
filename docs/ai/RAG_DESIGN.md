# Retrieval-Augmented Generation Design

**Status:** Living design; hybrid retrieval and explicit ingestion slice implemented
**Last updated:** 2026-07-13  
**Related:** [Eligibility engine](ELIGIBILITY_ENGINE.md), [LangGraph design](LANGGRAPH_DESIGN.md), [ADR-0004](../architecture/adr/0004-opensearch-hybrid-retrieval.md)

## 1. Purpose and boundary

RAG supports scheme discovery, cited summaries, comparisons, checklists, and explanations of already-computed eligibility results. It does not create or evaluate eligibility rules. Structured, reviewed rules are supplied to the deterministic engine; unstructured evidence supplies citations and explanatory context.

All retrieved content is untrusted input. It may contain errors, stale statements, or prompt-injection text. It is quoted as data within a bounded context and cannot issue instructions, select tools, modify graph policy, or change an eligibility result.

### Implementation snapshot

The API can select either a curated development retriever or the OpenSearch hybrid retriever. The latter runs BM25 and vector queries, applies validated filters, fuses rankings with reciprocal-rank fusion, deduplicates chunks, and retains citation metadata. The worker reads a reviewed allowlist manifest, applies HTTPS/redirect/host/streaming-size controls, extracts visible HTML or bounded text-bearing PDF pages, creates deterministic chunks and hash-derived development embeddings, and writes the versioned index. Evidence is typed as `official_scheme` or `business_guide`; only the former may support material scheme claims. The answer provider is deterministic by default with an optional OpenAI adapter.

The reviewed local manifest currently contains four official government sources and two CC BY business textbooks fetched from the Library of Congress. It is documented in `apps/worker/sources/README.md`. This slice does not yet provide immutable raw-content object snapshots, PostgreSQL-backed ingestion/publication jobs, reviewer approval UI, a production embedding provider, scheduled refresh, or the claim-level citation validator described below. Those remain launch gates, not implied current behavior.

## 2. MVP versus later phases

| Capability | MVP | Later phase |
|---|---|---|
| Sources | Allowlisted public official sources, human-approved | Additional approved institutional sources and negotiated feeds |
| Languages | Explicitly validated pilot languages | Evaluated multilingual/cross-lingual retrieval |
| Retrieval | OpenSearch BM25 + vector hybrid with structured filters | Learned reranking after offline/online validation |
| Ingestion | Text/HTML and text-bearing PDF within strict limits | OCR and complex tables after security/quality review |
| Answers | Cited discovery, summaries, comparisons, checklists | Personalized proactive alerts and richer advisor workflows |
| Eligibility | Explain deterministic result only | Same invariant; never delegated to a model |

## 3. Evidence and rule separation

```text
Official source snapshot (immutable bytes/text)
        |                            |
        v                            v
Unstructured evidence pipeline    Reviewed structured rule authoring
chunks + embeddings + citations   typed facts/operators + citations
        |                            |
        v                            v
OpenSearch retrieval              Deterministic eligibility engine
        \                            /
         \---- cited explanation --/
```

- Evidence chunks are descriptive source material and never executable rules.
- Rule definitions are typed, reviewed, versioned, and cite evidence.
- Extraction may propose candidate metadata/rules only in draft. A reviewer must verify and encode them before publication.
- A scheme version may be published for discovery without an assessable rule set, but the UI/API must label assessment unavailable.

## 4. Source admission and ingestion

### Admission

An administrator/reviewer records canonical URL, authority, source type, domain, language, fetch policy, and approval status. Publishing requires an approved source. The fetcher enforces scheme (`https` in production), allowlisted host, DNS/IP checks, redirect revalidation, content type, response size, timeout, and rate limits to reduce SSRF and resource-exhaustion risk.

### Pipeline

1. Fetch source into a quarantined immutable snapshot with retrieval metadata and checksum.
2. Scan and parse using sandboxed, resource-limited tooling; never execute active content, macros, scripts, or embedded instructions.
3. Normalize text while preserving headings, page/section locators, tables where reliable, and language.
4. Detect duplicate/near-duplicate content and source changes.
5. Produce draft chunks and candidate scheme metadata.
6. Reviewer validates material claims, effective dates, scheme linkage, citation spans, and publication state.
7. On publication, write an outbox event and index the approved scheme/source version.

Original content, normalized text, parser version, checksum, capture time, and final URL remain traceable. Indexing is reproducible and idempotent by source version plus index schema version.

## 5. Chunk and citation model

Chunks follow semantic document structure rather than arbitrary fixed windows where possible. Each chunk is bounded by model/index limits and includes enough local heading context to stand alone. Small overlap may preserve continuity, but citation locators refer to the immutable normalized source, not overlap-relative positions.

Required index metadata:

- chunk, source, source-version, scheme, and scheme-version IDs;
- citation ID and stable page/section/offset locator;
- authority, source type, language, geography, benefit/category facets;
- effective/expiry dates, capture and review times;
- publication/visibility state, checksum, embedding model/version;
- chunk text and vector.

A citation resolves to an approved URL, version/capture metadata, human-readable locator, and a short excerpt when allowed. Every material generated claim maps to one or more citation IDs.

## 6. Hybrid retrieval

OpenSearch performs lexical BM25 and approximate vector search. The service, not the model, constructs queries:

1. Validate and normalize the user query and typed filters.
2. Enforce publication, effective-date, visibility, language, and tenant constraints.
3. Run lexical and vector retrieval, with separately configurable candidate counts.
4. Fuse ranked lists using deterministic reciprocal-rank fusion (RRF) for the MVP.
5. Apply diversity limits so one source/version does not crowd out alternatives.
6. Optionally rerank with a provider-neutral adapter only if enabled and evaluated; reranking cannot bypass filters.
7. Apply relevance/evidence thresholds and return no-answer when support is insufficient.

The query builder never accepts raw OpenSearch DSL from users or models. Effective-date behavior is explicit: default to current published versions; historical queries must opt into an as-of date and return version dates visibly.

## 7. Context construction and generation

The context builder:

- uses an allowlisted template and prompt version;
- includes only the minimum relevant chunks within a token/size budget;
- delimiters label source text as untrusted evidence;
- assigns citation markers generated by the application, not accepted from source text;
- includes conflicts, dates, and source authority rather than silently merging them;
- excludes hidden credentials, raw profile fields not needed for the request, and unauthorized tenant data.

The model receives explicit constraints: use only supplied evidence for scheme facts, cite material claims, state when evidence is insufficient/conflicting, and never infer eligibility. These constraints are defense in depth; server-side validation is the enforcement boundary.

Provider-neutral OpenAI and Gemini adapters share typed interfaces for generation, streaming, embeddings, and optional reranking. Adapters translate provider-specific requests/errors into domain contracts, expose capability metadata, use explicit model/config versions, and capture safe usage/latency metrics. Business services and graphs do not import provider SDK types.

## 8. Claim and citation validation

Generation returns a structured response containing answer segments and citation IDs. The validator:

- rejects unknown, duplicate-forged, draft, withdrawn, or unauthorized citation IDs;
- requires citations on eligibility criteria, benefits, dates, scope, documents, and application steps;
- checks that cited versions match the scheme/as-of context;
- applies a bounded entailment/lexical check as a signal, never as sole publication approval;
- converts unsupported material output to a safe insufficient-evidence response;
- returns citations as separate safe UI objects rather than trusting model-formatted links.

For eligibility explanations, factual outcomes and missing fields come exclusively from the stored engine result. The model may simplify wording but the validator prevents changed decision labels, rule outcomes, values, or citations.

## 9. Freshness, conflict, and withdrawal

- Source schedules reflect expected update frequency and respectful fetch limits.
- Checksum changes create new source versions and review tasks; they do not overwrite evidence.
- Scheme versions preserve `valid_from`, `valid_until`, publication, review, and source capture dates.
- Conflicting approved sources are retained, surfaced to reviewers, and not synthesized into a new rule automatically.
- Withdrawal removes content from current retrieval through authoritative status filtering and an index event; historical assessments retain exact references.
- Freshness dashboards track overdue sources, indexing lag, orphan citations, and expiring scheme versions.

## 10. Prompt-injection and content safety

- Treat source text, metadata, URLs, filenames, user messages, and model output as untrusted.
- Retrieved documents cannot enable tools, alter system instructions, or contribute role-tagged messages.
- Graph tool selection is code-defined and allowlisted; models receive no general network, shell, database, publication, payment, or administration tool.
- Sanitize rendered content and URLs; never render active source HTML.
- Limit per-source chunks and detect common instruction-like content for logging/evaluation, but do not rely on detection alone.
- Use least-privilege provider credentials, egress allowlists, timeouts, content limits, and redacted telemetry.

## 11. Evaluation and release gates

Use a versioned synthetic golden corpus containing invented authorities and schemes only. Do not put real unsupported scheme facts into fixtures. Evaluate:

- lexical/vector/hybrid recall@k, MRR/nDCG, filter correctness, and diversity;
- citation precision/recall, citation resolvability, claim support, and version correctness;
- no-answer behavior, conflicting evidence, effective dates, and withdrawn content;
- prompt injection, malicious files/HTML, SSRF, cross-tenant leakage, and citation spoofing;
- latency, index lag, token/cost budgets, adapter fallback, and provider error handling.

Launch gates are 100% resolvable citations for published material claims, zero known eligibility decisions originating from a model, and approved thresholds recorded in the evaluation package. Threshold values must be set from a representative pilot corpus before launch.

## 12. Observability and privacy

Record query/result IDs, versions, ranks/scores, filters, latency, provider/model/prompt version, token counts, validation outcome, and correlation ID. Avoid raw user queries or profile facts in general logs; store evaluation/debug samples only under an approved access and retention policy. Provider data retention and region settings are deployment configuration and must be reviewed before production.

## 13. Open decisions

- Pilot source authorities, categories, languages, and freshness SLAs.
- Embedding models/dimensions and whether OpenAI/Gemini embedding parity is required.
- Initial hybrid weights/RRF constants and evidence thresholds based on evaluation.
- Parser/OCR boundary and safe document-processing service.
- Human review workflow for conflicts, translations, and urgent withdrawal.
