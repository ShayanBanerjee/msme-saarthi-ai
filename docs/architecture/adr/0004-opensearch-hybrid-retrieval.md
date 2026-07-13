# ADR-0004: OpenSearch Hybrid Retrieval

**Status:** Accepted  
**Date:** 2026-07-13

## Context

Scheme queries combine exact terminology, natural-language intent, structured facets, effective dates, and citation metadata. Lexical or vector retrieval alone is insufficient across these cases.

## Decision

Use OpenSearch as a derived published-content index. Run BM25 and vector retrieval under identical mandatory filters and combine candidates with deterministic reciprocal-rank fusion. Preserve source/scheme versions and citation locators. PostgreSQL remains authoritative; versioned aliases support index rebuilds.

## Consequences

The system gains one operational dependency and must evaluate embeddings, fusion, filters, and index lag. Retrieval remains independently replaceable behind a typed interface and cannot decide eligibility.

## Alternatives considered

- PostgreSQL full-text/vector only: deferred; simpler but not the chosen production retrieval target.
- Vector-only retrieval: rejected due to exact-term and filter limitations.
- Managed proprietary RAG store: rejected due to provider coupling and provenance control.

