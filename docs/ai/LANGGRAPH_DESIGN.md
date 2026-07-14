# LangGraph Orchestration Design

**Status:** Living design; minimal cited-chat graph implemented
**Last updated:** 2026-07-15
**Related:** [RAG design](RAG_DESIGN.md), [Eligibility engine](ELIGIBILITY_ENGINE.md), [API conventions](../api/API_CONVENTIONS.md)

## 1. Purpose

LangGraph coordinates bounded conversational workflows: discovery, cited questions, profile field collection, deterministic assessment invocation, and explanation of stored results. It is orchestration, not a source of truth. Graph nodes call typed application services; they do not directly access PostgreSQL/OpenSearch or embed business rules in prompts.

### Implementation snapshot

The current graph is intentionally smaller than the target graph below: typed state carries a user-confirmed business brief, one of four allowlisted advisor modes, response depth, and up to twelve prior visible messages. Retrieval prepares validated state, then the API forwards provider-native generation deltas. Retrieval and generation remain injected behind application-owned interfaces. Disconnect closes upstream provider work; a bounded model deadline uses a deterministic fallback. Claim-level citation validation runs before assistant persistence and the authoritative final event. The prompt separates official programme paths from general growth techniques and never infers eligibility.

The allowlisted modes are `business_analyst`, `scheme_navigator`, `growth_strategist`, and `funding_readiness`; depth is `concise`, `balanced`, or `deep`. Clients select IDs only. They cannot submit system-prompt text. These compile-time prompt fragments are a first prompt-registry boundary, not the durable reviewed prompt-version store described below.

Intent routing, profile-field collection, deterministic assessment invocation, durable graph checkpoints, prompt-registry persistence, and Gemini are not implemented yet. The fuller graph below remains the target contract.

## 2. MVP graph

```text
START
  -> validate_input_and_session
  -> classify_intent
       -> discover_or_answer -> retrieve -> assess_evidence -> generate -> validate_citations
       -> assess -> determine_missing_fields -> collect_or_invoke_engine -> explain_result
       -> profile_help -> collect_typed_fields
       -> unsupported
  -> persist_safe_turn
  -> END

Any node -> policy/error fallback -> END
```

Intent classification can be model-assisted but its output is validated against an enum and policy. Sensitive/privileged actions (publication, refunds, role changes, source approval) are excluded from the user graph.

## 3. Typed graph state

State is a Pydantic schema containing IDs and bounded data:

- conversation, turn, tenant, actor, profile, and correlation IDs;
- validated intent and requested as-of date;
- safe normalized user message;
- missing profile field descriptors and user-confirmed typed values;
- retrieved citation/chunk IDs with scores and version metadata;
- existing assessment ID and immutable structured decision (when applicable);
- prompt version, adapter/model configuration, safety flags, retry counters;
- response segments, citations, and completion/error state.

Do not place access tokens, provider keys, unrestricted documents, hidden reasoning, payment data, or raw database models in graph state. Persist only the state required for chat history and replay/debug under the approved retention policy.

## 4. Nodes and trust boundaries

### Deterministic nodes

Input validation, authorization, filters, profile schema validation, missing-field calculation, eligibility invocation, citation resolution, output validation, persistence, and policy routing are code-defined. Model output cannot bypass them.

### Model nodes

Intent suggestion, query reformulation, grounded response drafting, and plain-language explanation use the provider-neutral adapter. Each has a narrow structured output schema, bounded input, explicit prompt version, timeout, retry policy, and safe fallback.

### Service tools

The graph receives an allowlisted tool registry through dependency injection. MVP tools are read/search published schemes, read/update permitted profile facts with explicit confirmation, create deterministic assessment, and load assessment/citations. There is no arbitrary HTTP, SQL, shell, file, admin, payment, referral-credit, or publish tool.

## 5. Provider-neutral adapters

Application interfaces cover `generate`, `stream`, `embed` (used by retrieval services), capability discovery, and normalized errors/usage. OpenAI and Gemini implementations translate these contracts. Provider configuration selects an adapter/model by use case without conditional logic throughout the graph.

Requirements:

- provider SDK objects remain inside adapters;
- every call identifies provider, model, prompt version, parameters, timeout, and correlation ID;
- retry only safe transient failures with bounded jitter and total budget;
- no automatic cross-provider failover for a state-changing tool sequence; safe answer-generation fallback may occur when policy permits and is recorded;
- validate structured output after every provider response;
- enforce provider privacy, region, retention, and safety settings in deployment configuration.

## 6. Prompt registry and versioning

Prompts are immutable versioned assets, not inline strings scattered through nodes. Each record/artifact has a stable name, semantic version, content hash, input/output schema versions, supported provider capabilities, status (`draft`, `active`, `retired`), owner, review metadata, and evaluation result reference.

Activating a prompt requires review and the relevant synthetic evaluation suite. Each message/assessment explanation stores the prompt version and model configuration used. Rollback changes the active pointer; it does not mutate prior versions. Prompts contain no secrets or real personal data.

## 7. Profile collection and assessment

1. Load the selected scheme's published rule-set metadata without giving rules to the model as authority.
2. Deterministic service identifies unknown required fact paths.
3. Model may turn typed field descriptors into conversational questions.
4. User input is parsed into a candidate typed value, validated, and shown/confirmed before profile persistence.
5. Service creates a new profile version and calls the eligibility engine.
6. Graph receives a persisted assessment ID and structured result.
7. Explanation is generated only from that result and approved cited evidence, then validated.

The graph never silently infers a missing business fact from conversation or evidence. A derived fact requires a separately approved deterministic derivation.

## 8. Checkpointing, concurrency, and replay

- Store graph checkpoints in PostgreSQL for durable conversational workflows; Redis may coordinate locks/short-lived streaming state.
- Checkpoints carry graph and state-schema versions.
- Use per-conversation/turn idempotency keys and optimistic concurrency to prevent duplicate messages or assessments.
- Resume only from allowlisted safe nodes after transient failure; external calls/tool effects record completion before retry.
- Historical replay uses recorded IDs/versions and must not re-execute state-changing tools.
- Chat history is tenant-scoped and subject to user-visible retention/deletion rules.

## 9. Safety and fallback

- Retrieved/user text is placed only in data fields, never concatenated as system/tool instructions.
- Tool arguments are constructed from validated structured output and reauthorized at the service boundary.
- Reject excessive length, nested content, invalid encodings, forged citations, unknown tools, and unsupported intents.
- Redact secrets and minimize profile data before model calls.
- If retrieval evidence is weak, say that evidence is insufficient and show safe official discovery links when available.
- If a provider fails, return deterministic assessment/profile functionality and a retryable assistant error.
- If citation validation fails, do not stream/finalize unsupported material claims.

## 10. Streaming

For assistant text, the API uses SSE with typed events: `status`, `text_delta`, `citation_preview`, `text_replace`, `final`, and `error`. Deltas and previews are provisional. `text_replace` atomically retracts provisional text when timeout or citation validation selects a safe fallback. The `final` event contains only authoritative citations plus `completion_status` and an optional stable `fallback_reason`. The UI must not treat provisional text as an authoritative eligibility result.

## 11. Observability and evaluation

Trace node names, duration, sanitized transition/retry reasons, retrieval IDs, adapter/model/prompt version, token/usage totals, validation status, and correlation ID. Do not log raw prompts, conversations, profile facts, tokens, or hidden model content by default.

Synthetic tests cover each route, invalid structured output, provider timeout/rate limit, prompt injection, unauthorized tool requests, missing facts, duplicate/resumed turns, citation failure, evidence conflict, and model attempts to alter engine decisions. Graph changes require offline evaluation and state-schema/checkpoint compatibility review.

## 12. Later phases

Possible later graphs include reviewer assistance, proactive alerts, multilingual conversations, advisor batch workflows, referral support, and payment support. Privileged or financial workflows require separate graphs/tools, explicit user confirmation, service-boundary authorization, audit logging, and dedicated threat review. A model must never autonomously approve content, move money, grant access, or award referral benefits.

## 13. Open decisions

- LangGraph checkpoint schema and retention.
- Which model capabilities are required for each node and fallback policy.
- Human handoff/support escalation UX.
- Streaming protocol details and moderation policy.
- Prompt approval roles and evaluation thresholds.
