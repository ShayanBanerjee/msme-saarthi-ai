# ADR-0003: Separate Evidence from Structured Rules

**Status:** Accepted  
**Date:** 2026-07-13

## Context

Official pages and documents are unstructured, versioned, and potentially hostile. Eligibility evaluation requires typed executable semantics. Treating chunks as executable criteria would allow ambiguity and prompt injection to affect decisions.

## Decision

Store immutable source snapshots, evidence chunks, and citations separately from human-reviewed structured scheme and rule versions. OpenSearch indexes published evidence for retrieval; PostgreSQL stores authoritative rules and version/effective-date metadata. Each material claim and eligibility criterion references approved evidence.

## Consequences

Publication needs human review and synchronization between authoritative records and a derived index. In exchange, retrieval content cannot directly execute and historical claims/rules remain traceable.

## Alternatives considered

- Evaluate directly from retrieved prose: rejected for ambiguity and injection risk.
- Store only normalized rules: rejected because claims would lose source provenance and explanatory context.

