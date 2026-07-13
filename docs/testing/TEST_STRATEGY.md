# Test Strategy

**Status:** Pre-implementation baseline  
**Last updated:** 2026-07-13  
**Related:** [Product requirements](../product/PRD.md), [Threat model](../security/THREAT_MODEL.md)

## 1. Goals

Testing must demonstrate functional correctness, deterministic eligibility, citation traceability, authorization isolation, safe handling of untrusted evidence, and deployability. Tests use synthetic schemes, authorities, profiles, citations, conversations, users, referrals, and payment references only.

## 2. Test pyramid and ownership

| Layer | Scope | Typical tools | Owner |
|---|---|---|---|
| Static | Formatting, lint, type, schemas, dependency/IaC policy | Ruff, mypy, ESLint, TypeScript, Terraform validators | Every module |
| Unit | Pure rules, services with fakes, components/hooks, query builders | Pytest, Vitest, Testing Library | Feature/package |
| Contract | OpenAPI/generated client, provider/repository interfaces, events | Pytest, schema snapshots | API/shared contracts |
| Integration | PostgreSQL/Redis/OpenSearch, migrations, adapters at boundaries | Pytest, containers/fixtures | API/worker |
| End-to-end | Critical browser journeys against composed services | Playwright, Docker Compose | Cross-functional |
| Evaluation | Retrieval, citations, prompt safety, graph behavior, eligibility goldens | `packages/evaluation` | AI/content/engineering |
| Operational | Load, resilience, restore, migration, security exercises | Purpose-built scripts/tools | Platform/security |

Prefer the narrowest deterministic test. Mock third-party networks in normal CI; run explicitly controlled provider smoke tests separately without asserting nondeterministic prose.

## 3. Backend tests

- Route tests cover status, typed bodies, problem details, correlation IDs, validation, auth, and hidden cross-tenant resources.
- Service tests cover authorization at the boundary, transactions, idempotency, immutable versions, and error mapping.
- Repository integration tests use real PostgreSQL; no SQLite substitute for PostgreSQL behavior.
- Async code uses explicit fixtures and detects leaked tasks/resources.
- Migrations are tested from empty and representative prior schemas, including data constraints and roll-forward guidance.
- Health liveness checks process responsiveness only; readiness checks required dependencies as each is introduced.

## 4. Frontend tests

- Unit/component tests cover loading, empty, success, validation, error, permission, and responsive navigation states.
- Use semantic queries and keyboard interaction; include automated accessibility checks without treating them as a full manual audit.
- Mock API boundaries with contract-shaped responses, not internal component behavior.
- Playwright covers login/session expiry, profile, discovery, cited chat, assessment, and admin access denial.
- Build and browser checks fail on unexpected console errors.

## 5. Eligibility assurance

- Table tests for every operator and three-valued truth table.
- Boundary tests for exact decimals, dates, membership, normalization, missing facts, and nesting.
- Property/mutation tests for determinism and composition logic.
- Versioned synthetic golden schemes/profiles with reviewer-approved expected results.
- Replay tests prove stored assessment versions reproduce decisions across compatible releases.
- Tests prove model, prompt, retrieved text, and client fields cannot inject or override decisions.

Behavioral engine changes require versioning, compatibility tests, and full golden replay.

## 6. RAG and LangGraph evaluation

Synthetic corpora include lexical-only, semantic-only, conflicting, expired, withdrawn, duplicate, multilingual, and adversarial instruction-like documents. Measure lexical/vector/hybrid recall, nDCG/MRR, filters, deduplication, citation precision/recall/resolution, claim support, no-answer rate, latency, and cost.

Graph tests cover typed transitions, tool allowlists, retries/timeouts, checkpoints, duplicate turns, disconnects, provider errors, unauthorized access, missing-profile collection, and citation validation. OpenAI and Gemini adapters pass the same interface contract suite; deterministic fake providers drive CI.

## 7. Security, payment, and referral testing

- Cross-tenant and role matrix tests at service/repository/search/cache boundaries.
- Session fixation/rotation/expiry/logout, CSRF/origin, rate limit, and redaction tests.
- Prompt injection, citation spoofing, malicious HTML/PDF metadata, SSRF/redirect/DNS, parser limit, raw query DSL, and XSS cases.
- Later payment tests verify raw-body signatures, replay windows, idempotent duplicate/out-of-order webhooks, amount/currency reconciliation, refunds, and no card storage.
- Later referral tests verify self-referral, duplicate attribution, race conditions, reversal, ledger idempotency, and authorization.
- CI scans dependencies, secrets, source, containers, and Terraform; findings follow the threat-model release policy.

## 8. Environments and data

- Unit tests run without networks or shared services.
- Integration tests use pinned disposable containers or documented equivalent fixtures for PostgreSQL, Redis, and OpenSearch.
- Docker Compose supports local cross-service testing.
- Staging resembles production topology/configuration but uses synthetic data and non-production credentials.
- Test fixtures are deterministic, versioned, minimal, and contain no copied unsupported real-scheme claims or personal data.

## 9. CI pipeline

GitHub Actions should run, in increasing cost:

1. formatting/lint/type/schema and secret checks;
2. unit and contract tests in parallel;
3. builds and migration checks;
4. integration tests with pinned service images;
5. evaluation regression thresholds;
6. container/IaC security checks;
7. Playwright smoke tests on a composed artifact.

Protected branches require relevant checks. Scheduled pipelines run broader evaluation, dependency, resilience, and browser matrices. Release artifacts are built once and promoted.

## 10. Quality gates

- New behavior has tests at the lowest effective layer plus boundary integration where needed.
- Ruff, mypy, frontend lint/typecheck, unit tests, and builds pass for affected modules.
- No known path permits an LLM-generated eligibility decision.
- All published material synthetic fixture claims have resolvable citations.
- Critical/high security findings follow the threat-model gate.
- Flaky tests are fixed or quarantined with an owner/expiry; they are not silently retried into green.
- Coverage is used diagnostically; risk-based assertions and mutation/evaluation results matter more than a single global percentage.

## 11. Standard commands

```text
make lint
make typecheck
make test
make test-integration
make test-e2e
```

Modules may expose narrower targets such as `make api-test` and `make web-typecheck`. Commands must be local/CI equivalent, documented, and never reported as passing unless executed.

## 12. Exit reporting

Every task reports commands executed, result counts/status, skipped or unavailable checks, environment differences, coverage/evaluation changes where relevant, and remaining risks. A green test suite does not imply production readiness until operational launch gates also pass.

