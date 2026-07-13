# Architecture Overview

**Status:** Pre-implementation baseline  
**Last updated:** 2026-07-13  
**Related:** [Data model](DATA_MODEL.md), [API conventions](../api/API_CONVENTIONS.md), [Threat model](../security/THREAT_MODEL.md)

## 1. Architectural goals

The architecture prioritizes deterministic eligibility, evidence provenance, tenant isolation, reviewable content publication, and independently testable modules. It starts as a modular monolith plus worker in a modular monorepo; package boundaries should remain valid if scaling later requires separation. This choice is recorded in [ADR-0001](adr/0001-modular-monolith-first.md).

## 2. System context

```text
User / Reviewer
      |
      v
React web application
      |
      v
FastAPI application ---- PostgreSQL (system of record)
      |       |  \------ Redis (cache, rate limit, job coordination)
      |       \--------- OpenSearch (published discovery and retrieval index)
      |
      +---- Eligibility engine (pure deterministic package)
      +---- LangGraph orchestration ---- provider-neutral adapters ---- OpenAI / Gemini
      |
      v
Worker / ingestion ---- allowlisted official source websites

Observability, object storage, secrets, and AWS controls span all runtime services.
```

## 3. Monorepo boundaries

| Path | Responsibility | Must not own |
|---|---|---|
| `apps/web` | React UI, accessibility, client validation, server-state integration | Business rules, direct database/model access |
| `apps/api` | Modular-monolith HTTP layer, secure sessions, feature services/repositories, graph entry points, administration, later payment/referral modules | Eligibility logic inside routes; provider SDK types outside adapters |
| `apps/worker` | Fetching, extraction, indexing, scheduled and asynchronous jobs | Automatic publication of unreviewed rules |
| `packages/eligibility-engine` | Typed rule schema, validation, pure evaluation, explanations as structured facts | LLM calls, database/network access |
| `packages/shared-contracts` | Shared schemas and generated API types | Runtime business workflows |
| `packages/evaluation` | Offline RAG, citation, safety, and eligibility evaluation fixtures/metrics | Production decisions |
| `infrastructure` | Docker, Terraform, GitHub Actions, AWS configuration | Application domain policy |
| `docs` | Authoritative product and engineering contracts | Secrets or environment-specific credentials |

## 4. Runtime components

### Web

React, TypeScript, Vite, Tailwind CSS, and shadcn/ui. Features own their UI and API adapters. TanStack Query manages server state; React Hook Form and Zod manage forms. The browser treats assistant text as untrusted and never renders unsanitized HTML.

### API

FastAPI with Pydantic v2 and asynchronous SQLAlchemy 2. Each feature follows:

```text
route -> service (authorization + use case) -> repository -> PostgreSQL
                    |-> eligibility engine
                    |-> retrieval / graph adapter
```

Routes translate HTTP concerns. Services enforce tenant authorization and transactions. Repositories encapsulate persistence. Domain packages remain framework-independent.

### Worker

Runs ingestion, extraction, embedding, indexing, freshness checks, and retryable maintenance work. Jobs are idempotent and keyed by source version/checksum. Redis coordinates queues and locks; PostgreSQL records durable job and publication state. A failed index update must be retryable from system-of-record data.

### PostgreSQL

Authoritative store for identity/session references, tenants, profiles, sources, immutable versions, citations, rules, prompts, assessments, conversations, jobs, audit events, and later payment/referral ledgers. Alembic is the only production schema migration mechanism.

### OpenSearch

Derived read model containing only published, authorized discovery/RAG content. Documents carry tenant/visibility, scheme version, source version, citation locator, language, and publication metadata. The index is never the authority for eligibility rules or publication state.

### Redis

Ephemeral cache, distributed coordination, rate-limit state, and job transport. Durable business records do not exist only in Redis. Cache keys include tenant and relevant version identifiers.

### Eligibility engine

A pure, deterministic package that validates a versioned rule set and evaluates normalized profile facts. It returns structured outcomes; it does not retrieve sources, call models, or persist data. See [ELIGIBILITY_ENGINE.md](../ai/ELIGIBILITY_ENGINE.md).

### AI orchestration

LangGraph coordinates intent classification, safe retrieval, missing-field collection, eligibility tool invocation, citation verification, and response generation. Model output is advisory data until validated. Application-owned interfaces isolate OpenAI and Gemini adapters. See [LANGGRAPH_DESIGN.md](../ai/LANGGRAPH_DESIGN.md) and [ADR-0005](adr/0005-provider-neutral-model-adapters.md).

## 5. Source-of-truth rules

| Concern | Authority |
|---|---|
| User/tenant/profile data | PostgreSQL |
| Source snapshots and metadata | PostgreSQL plus immutable object content referenced by checksum |
| Published scheme and rule versions | PostgreSQL |
| Eligibility decision | Eligibility engine output persisted with exact inputs/versions |
| Search/RAG documents | OpenSearch derived from published PostgreSQL records |
| Queue/cache/locks | Redis, non-authoritative |
| Generated explanations | Persisted output plus citations; never the decision authority |
| Secure sessions and prompt versions | PostgreSQL; secrets/provider credentials remain in managed secret storage |
| Payment/referral entitlements (later) | PostgreSQL ledger reconciled with provider records |

## 6. Critical flows

### Eligibility assessment

1. API authenticates the actor and authorizes profile/scheme access.
2. Service loads the current published rule set and creates an immutable normalized profile snapshot.
3. Engine validates and evaluates the rule set.
4. Service persists assessment, per-rule outcomes, versions, and input hash atomically.
5. Optional LLM explanation receives only the persisted structured result and approved evidence.
6. API returns the engine result; explanation failure cannot change it.

### Ingestion and publication

1. Scheduler creates a fetch job for an allowlisted source.
2. Worker validates the final URL after redirects, fetches within limits, and stores content/checksum/provenance.
3. Parsing and extraction produce draft chunks and candidate structured facts.
4. Reviewer verifies material claims, citation locators, scheme metadata, and rule definitions.
5. Publish transaction activates immutable scheme/rule versions and emits an outbox event.
6. Worker indexes only active published content; consumers tolerate duplicate events.

### RAG response

1. API applies authentication, rate limits, and input validation.
2. Retrieval uses structured filters and published-content constraints.
3. System reranks, checks evidence sufficiency, and builds a bounded context with untrusted-data delimiters.
4. Model generates a constrained response with citation identifiers.
5. Validator removes or rejects unsupported material claims and resolves citations.
6. Response is returned with an uncertainty/fallback state when evidence is insufficient.

## 7. Consistency and failure handling

- PostgreSQL transactions protect local state changes.
- An outbox pattern coordinates publication/index jobs without distributed transactions.
- Job handlers use stable idempotency keys and bounded exponential backoff.
- Search may be eventually consistent after publication; the API rechecks publication state for detail and assessment operations.
- Model, embedding, or OpenSearch failure degrades to deterministic/filter-based capabilities where possible.
- Circuit breakers/timeouts prevent external providers from consuming request capacity indefinitely.
- Every request/job propagates a correlation ID; logs exclude secrets, raw profile values, and retrieved full documents.

## 8. Deployment baseline

- Docker Compose provides local PostgreSQL, Redis, OpenSearch, API, worker, and web services.
- GitHub Actions performs lint, type, unit, integration, security, migration, and build checks.
- Terraform provisions AWS environments using separate state and least-privilege roles.
- Expected AWS building blocks are managed compute, PostgreSQL, Redis, OpenSearch, object storage, KMS, secrets management, WAF/load balancing, logging, and monitoring; exact services require an ADR before implementation.
- Production uses private networking for data stores, TLS at boundaries, encrypted storage, immutable artifacts, health checks, and rolling or blue/green deployment.

## 9. Architecture constraints

- No eligibility rule in prompts, UI-only code, or route handlers.
- No LLM-produced rule may be published without human verification and deterministic encoding.
- No public response may expose draft/unapproved content.
- No direct model or database calls from the browser.
- No cross-tenant cache or search result reuse without tenant-scoped keys/filters.
- No hard deletion of a version referenced by an assessment or audit record; use lifecycle state and retention policy.
- No model-driven publication, role change, payment/refund, or referral award.

## 10. Decisions still requiring ADRs

- Authentication/identity provider and tenancy model.
- Queue implementation compatible with Redis and operational needs.
- Model and embedding provider abstraction, regions, and data-processing terms.
- Object storage snapshot format and malware/content scanning controls.
- OpenSearch index and alias versioning strategy.
- AWS compute topology and disaster-recovery targets.
