# Implementation Backlog

**Status:** Living implementation plan
**Last updated:** 2026-07-13  
**Planning rule:** Each task has one objective, limited file ownership, dependencies, observable acceptance criteria, and verification commands. A task should normally be one reviewable commit; split it if implementation exceeds that boundary.

All examples and fixtures must be synthetic. Tasks must follow `AGENTS.md` and the relevant design documents. Later-phase work is not authorized merely by appearing here.

## Implementation snapshot

| Task | State as of 2026-07-13 | Remaining boundary |
|---|---|---|
| API-01 | Implemented | Continue maintaining module gates and contracts |
| WEB-01 | Substantially implemented | Full browser E2E and accessibility audit remain |
| IDN-01 | Partially implemented via first-party ADR-0006 | Verification, recovery, throttling, MFA/OIDC, security audit events |
| ELIG-01 | Implemented as a standalone deterministic package | API/assessment integration belongs to ASM-01 |
| CHAT-01 | Implemented with PostgreSQL completed-turn persistence | Durable checkpoints and prompt registry remain |
| RET-01 | Implemented | Production embedding/reranking evaluation remains |
| ING-01 | Partially implemented | Immutable snapshots, durable jobs, reviewer publication and withdrawal workflow |
| PROF-01, CAT-01, ASM-01 | Not implemented | Core MVP persistence and review workflows |
| Later phases / OPS | Not implemented | Commerce, referrals, Terraform, CI/CD and production operations |

This table is a status aid, not an acceptance record. A task is complete only when its scoped acceptance criteria and verification commands have been satisfied; later work should split stale objectives rather than silently broadening them.

## Phase 0 — Foundation

### FND-01: Repository quality and local-service skeleton

**Objective:** Establish monorepo commands, lockfiles, Docker Compose service definitions, and CI entry points without feature behavior.  
**Owns:** root `Makefile`, ignore/editor files, dependency workspace files, `docker-compose.yml`, `.github/workflows/ci.yml`, `.env.example`.  
**Dependencies:** Planning documents and ADRs accepted.  
**Acceptance:** Narrow module targets exist; Compose configuration validates; CI invokes the same commands; example environment contains no secrets.  
**Verify:** `docker compose config`; `make lint`; `make typecheck`; `make test`.

### API-01: Bootstrap the FastAPI application

**Objective:** Create a runnable typed API foundation with health endpoints.  
**Owns:** `apps/api`, root `Makefile`, `.env.example`. Does not own database integration, frontend, or Terraform.  
**Dependencies:** FND-01 command conventions (may be delivered together only if repository bootstrap has not otherwise occurred).  
**Acceptance:** Python 3.12 `pyproject.toml`; application factory; Pydantic settings; structured logging; centralized safe exceptions; typed `/api/v1/health/live` and `/ready`; endpoint tests pass. Readiness checks only configured dependencies, so it is process-ready before databases are introduced.  
**Verify:** `make api-lint`; `make api-typecheck`; `make api-test`.

### WEB-01: Bootstrap the authenticated application shell

**Objective:** Create the responsive React shell and placeholder feature routes using synthetic data.  
**Owns:** `apps/web`. Does not own API or infrastructure.  
**Dependencies:** FND-01; PRD navigation approved.  
**Acceptance:** React/TypeScript/Vite, Tailwind, and shadcn/ui conventions configured; Dashboard, Chat, Assessments, Schemes, and Profile routes render; desktop/mobile keyboard navigation works; loading/error boundaries and navigation component tests exist; no browser console errors. Authentication is a typed placeholder boundary, not fake production security.  
**Verify:** `make web-lint`; `make web-typecheck`; `make web-test`; `make web-build`.

### IDN-01: Implement login and secure sessions

**Objective:** Add the approved OIDC login/logout/session lifecycle and service-boundary actor context.  
**Owns:** `apps/api/app/features/auth`, auth migrations/tests, corresponding `apps/web/src/features/auth`, shared auth contracts.  
**Dependencies:** API-01, WEB-01, identity/session ADR.  
**Acceptance:** State/nonce validation; secure cookie attributes; rotation, idle/absolute expiry, revocation, CSRF/origin protection; unauthorized access rejected; privileged MFA context exposed; auth events audited.  
**Verify:** `make api-lint`; `make api-typecheck`; `make api-test-integration`; `make web-test`; `make test-e2e`.

## Phase 1 — MVP vertical slices

### PROF-01: Persist versioned business profiles

**Objective:** Create authorized CRUD for structured profiles and immutable profile versions.  
**Owns:** profile API/service/repository/domain, profile migrations/tests, profile UI/API adapter.  
**Dependencies:** IDN-01, database foundation/migrations.  
**Acceptance:** External input validates; tenant isolation is tested; edits create versions with provenance/hash; loading/empty/error UI states work; sensitive-document fields are absent.  
**Verify:** `make api-test-integration`; `make web-test`; `make web-typecheck`.

### ELIG-01: Implement the deterministic eligibility engine

**Objective:** Evaluate typed synthetic profile facts against typed versioned scheme rules without any model dependency.  
**Owns:** `packages/eligibility-engine`. Does not own LangGraph, routes, or frontend.  
**Dependencies:** Eligibility design and initial profile/rule schema approved.  
**Acceptance:** Typed inputs; `all`/`any`/`not`; equals, membership, range/boundary, and existence operators; exact decimals; missing facts are unknown; invalid rules fail; result includes decision, passed/failed/unknown outcomes, and source-rule IDs; deterministic synthetic golden tests pass.  
**Verify:** `make eligibility-lint`; `make eligibility-typecheck`; `make eligibility-test`.

### CAT-01: Publish and browse versioned schemes

**Objective:** Implement reviewer-managed structured schemes, claims, citations, rule-set versions, and current catalogue reads.  
**Owns:** scheme/content-admin modules, migrations/tests, catalogue/admin UI feature folders.  
**Dependencies:** IDN-01, ELIG-01, database foundation.  
**Acceptance:** Draft/publish/withdraw transitions are role-gated and audited; effective dates and immutable versions persist; material claims/rules require approved citations; public APIs never expose drafts.  
**Verify:** `make api-test-integration`; `make web-test`; `make test-e2e`.

### CHAT-01: Implement a minimal LangGraph chat slice

**Objective:** Stream a persisted synthetic cited answer through the provider-neutral interface.  
**Owns:** `apps/api/app/agents`, `apps/api/app/features/chat`, related tests. Does not own eligibility, ingestion, frontend, or OpenSearch.  
**Dependencies:** API-01, IDN-01, prompt registry foundation.  
**Acceptance:** Typed graph state; one mock retriever and answer node; deterministic test provider; user/assistant messages persist; SSE handles disconnects; unauthorized access fails; synthetic citation returned.  
**Verify:** `make api-lint`; `make api-typecheck`; `make api-test`; `make api-test-integration`.

### RET-01: Implement OpenSearch hybrid retrieval

**Objective:** Implement filtered BM25/vector retrieval and RRF behind the Retriever interface.  
**Owns:** `apps/api/app/retrieval`, `apps/api/tests/retrieval`. Does not own chat routes, frontend, or eligibility.  
**Dependencies:** CHAT-01 interface, CAT-01 index contract, OpenSearch local fixture.  
**Acceptance:** Lexical/semantic matches; validated state/status/language/effective-date filters; typed results; deterministic RRF; source-chunk deduplication; document/page/section/source URL metadata preserved; no answer generation; container/documented integration fixture passes.  
**Verify:** `make retrieval-test`; `make retrieval-test-integration`.

### ING-01: Ingest and index approved sources safely

**Objective:** Fetch an allowlisted source into immutable snapshots and publish reviewed chunks to OpenSearch.  
**Owns:** `apps/worker` ingestion/index modules, source admin API/repository, migrations/tests.  
**Dependencies:** CAT-01, RET-01, worker/queue foundation.  
**Acceptance:** URL/redirect/DNS/content limits mitigate SSRF; parser treats content as hostile; checksum/idempotency/version metadata persist; review gates publication; withdrawal purges current index; retries use outbox events.  
**Verify:** `make worker-test`; `make test-integration`; `make security-test`.

### ASM-01: Integrate persisted assessments

**Objective:** Assess a frozen profile version against a published rule set and render traceable results.  
**Owns:** assessment API/service/repository/migrations/tests and assessment UI/API adapter.  
**Dependencies:** PROF-01, ELIG-01, CAT-01.  
**Acceptance:** Only engine output supplies the decision; completed assessments are immutable; exact profile/scheme/rule/engine versions and outcomes persist; cross-tenant access fails; eligible is not presented as approval.  
**Verify:** `make eligibility-test`; `make api-test-integration`; `make web-test`; `make test-e2e`.

### RAG-01: Ground and validate production chat answers

**Objective:** Replace mock retrieval with published hybrid evidence and enforce material-claim citations.  
**Owns:** chat/retrieval integration nodes, citation validator, prompt versions, evaluation fixtures/tests.  
**Dependencies:** CHAT-01, RET-01, ING-01, ASM-01.  
**Acceptance:** Effective/visibility filters enforced; retrieved text cannot control tools; unsupported claims fall back safely; assessment explanations cannot alter engine results; OpenAI/Gemini adapters pass common contracts; synthetic evaluation gates pass.  
**Verify:** `make api-test-integration`; `make evaluation-test`; `make security-test`.

### OPS-01: Production AWS delivery baseline

**Objective:** Provision and deploy the MVP safely to AWS using Terraform and GitHub Actions.  
**Owns:** `infrastructure`, deployment workflows/runbooks. Does not own feature behavior.  
**Dependencies:** FND-01, service images, infrastructure ADRs, approved RPO/RTO.  
**Acceptance:** Separate environments/state; private data stores; KMS/secrets/IAM least privilege; GitHub OIDC; monitoring/alerts; migration and rollback strategy; restore test documented; no credentials committed.  
**Verify:** `terraform fmt -check -recursive infrastructure`; `terraform validate`; `make infrastructure-test`; deployment smoke/restore commands documented per environment.

## Phase 2 — Post-MVP

### PAY-01: Add provider-hosted payments and entitlement ledger

**Objective:** Convert verified provider events into idempotent subscription/entitlement state without storing payment credentials.  
**Owns:** payment API/service/repository/migrations/tests, payment UI, provider adapter.  
**Dependencies:** MVP security review, provider/compliance ADR, IDN-01, audit foundation.  
**Acceptance:** Hosted checkout; raw-body webhook signature/replay validation; duplicate/out-of-order events safe; exact decimal/currency; reconciliation/refunds; finance role authorization; audit trail; no card/bank data.  
**Verify:** `make api-test-integration`; `make web-test`; `make payment-security-test`; `make test-e2e`.

### REF-01: Add consented referrals and reward ledger

**Objective:** Attribute referrals and award/reverse rewards through a versioned abuse-resistant ledger.  
**Owns:** referral API/service/repository/migrations/tests and referral UI.  
**Dependencies:** IDN-01, PAY-01 if rewards have monetary value, approved policy/privacy review.  
**Acceptance:** Opaque codes; consented attribution; self/duplicate/race protections; idempotent reward/reversal; admin review authorization; audit events; synthetic fraud tests.  
**Verify:** `make api-test-integration`; `make referral-security-test`; `make web-test`; `make test-e2e`.

### LOC-01: Add evaluated multilingual support

**Objective:** Serve an approved additional language without weakening citation/version fidelity.  
**Owns:** localization resources, multilingual retrieval/evaluation fixtures, affected UI copy.  
**Dependencies:** RAG-01, content-review language workflow.  
**Acceptance:** Human-reviewed terminology; language filters/fallback visible; citations resolve to the correct source language/version; accessibility and retrieval thresholds pass.  
**Verify:** `make evaluation-test`; `make web-test`; `make test-e2e`.

## Unresolved sequencing decisions

- Identity provider/session topology and whether advisors manage multiple client tenants.
- Pilot scheme taxonomy, source set, languages, and reviewer separation of duties.
- Payment/referral business model and compliance scope; both remain post-MVP by default.
- AWS compute topology, provider regions/retention, RPO/RTO, and production load profile.
- Numeric retrieval/evaluation thresholds, set only after a representative synthetic/pilot corpus is reviewed.
