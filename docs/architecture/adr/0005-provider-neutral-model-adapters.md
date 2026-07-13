# ADR-0005: Provider-Neutral Model Adapters

**Status:** Accepted  
**Date:** 2026-07-13

## Context

The platform must support OpenAI and Gemini while model capabilities, cost, availability, privacy controls, and APIs evolve. Provider SDK types distributed through business code would make evaluation and migration difficult.

## Decision

Define application-owned typed interfaces for generation, streaming, embeddings, usage, and normalized errors. Implement OpenAI and Gemini adapters that contain all provider-specific SDK/configuration behavior. LangGraph nodes and services depend only on the interfaces. Prompt/model configuration is explicit and versioned; deterministic fake adapters support tests.

## Consequences

Common contracts improve testability and controlled provider selection but expose only a deliberately shared capability subset. Provider-specific capabilities require an explicit interface extension and evaluation rather than ad hoc branching.

## Alternatives considered

- One provider only: rejected by requirement and concentration risk.
- Direct SDK calls in graph nodes: rejected due to coupling and poor testability.
- Automatic transparent fallback for every call: rejected because semantics and state-changing retries can differ.

