# ADR-0002: Deterministic Eligibility Boundary

**Status:** Accepted  
**Date:** 2026-07-13

## Context

Eligibility answers must be reproducible, reviewable, versioned, and grounded in official criteria. Model generation is probabilistic and can be influenced by user or retrieved text.

## Decision

Only a pure deterministic rule engine may emit `eligible`, `ineligible`, or `insufficient_information`. It evaluates validated profile snapshots against reviewed, cited, immutable rule-set versions. Models may collect typed missing facts and explain persisted results, but cannot author runtime rules, infer authoritative facts, or change outcomes.

## Consequences

Assessments are reproducible and testable, but qualitative/discretionary schemes may be discovery-only until reviewers encode safe deterministic rules. Rule authoring and review become explicit product capabilities.

## Alternatives considered

- LLM-only decisions: rejected as non-deterministic and unsafe.
- Model decision with rule validation: rejected because authority would remain ambiguous.
