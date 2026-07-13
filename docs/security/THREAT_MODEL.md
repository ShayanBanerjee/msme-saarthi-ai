# Threat Model

**Status:** Pre-implementation baseline  
**Last updated:** 2026-07-13  
**Method:** STRIDE-informed, risk-ranked review  
**Related:** [Architecture overview](../architecture/OVERVIEW.md), [RAG design](../ai/RAG_DESIGN.md), [API conventions](../api/API_CONVENTIONS.md)

## 1. Scope and security objectives

This model covers the React client, FastAPI modular monolith, worker processes, PostgreSQL, Redis, OpenSearch, external identity and model providers, payment provider, official-source ingestion, AWS infrastructure, CI/CD, and administrative workflows.

Primary objectives are to:

- prevent cross-tenant or unauthorized access;
- preserve the integrity and provenance of published scheme evidence and rules;
- ensure only the deterministic engine produces eligibility decisions;
- prevent retrieved content from controlling the system;
- protect profile, conversation, session, payment-reference, and audit data;
- preserve scheme/rule versions and material citations; and
- keep privileged and financial operations attributable and reviewable.

## 2. Assets and data classes

| Asset | Sensitivity | Key protection |
|---|---|---|
| Session/token material and secrets | Critical | Never logged; encrypted secret storage; rotation; short lifetime |
| Business profiles and chat history | Confidential | Tenant authorization; minimization; encryption; retention/deletion |
| Payment customer/transaction references | Confidential | Provider tokenization; signed webhooks; no card storage |
| Published sources, claims, rules, prompt versions | Integrity-critical | Immutable versions; review; citations; audit trail |
| Assessments and rule outcomes | Integrity/confidential | Immutable inputs/versions; authorization; reproducibility |
| Audit events | Integrity-critical | Append-only access; restricted readers; retention |
| Search index and cache | Derived/confidential | Publication/tenant filters; scoped keys; rebuildability |
| Referral identifiers and rewards | Confidential/integrity | Abuse controls; idempotency; auditable ledger |

The MVP must avoid collecting identity, tax, banking, or application documents. A later requirement to collect them triggers a privacy impact assessment and threat-model update.

## 3. Trust boundaries

1. Browser to edge/API: all client data and headers are untrusted.
2. API/worker to PostgreSQL, Redis, and OpenSearch: private network and service identities; still validate responses and scope queries.
3. Ingestion to external websites/files: hostile input boundary, including redirects and parsers.
4. API/worker to OpenAI/Gemini: third-party processing and egress boundary.
5. Payment provider webhooks: unauthenticated internet traffic until signature and replay validation succeeds.
6. CI/CD to AWS: high-impact supply-chain and deployment boundary.
7. Reviewer/admin interfaces: privileged boundary requiring stronger authorization, audit, and session controls.

## 4. Threats and required mitigations

| ID | Threat | Risk | Required mitigations |
|---|---|---|---|
| T-01 | Account/session theft, fixation, token replay | Critical | Approved OIDC flow; secure short-lived sessions; rotation on login/privilege change; revoke/logout; CSRF controls for cookies; rate limits; MFA for privileged roles |
| T-02 | Broken object or tenant authorization | Critical | Service-boundary authorization; tenant-scoped repositories/keys/filters; opaque IDs; deny by default; cross-tenant tests; concealed `404` |
| T-03 | LLM decides or alters eligibility | Critical | Deterministic engine is sole decision authority; typed graph state; no model-supplied rules/facts; persist exact versions; invariant tests |
| T-04 | Prompt injection through sources or users | High | Treat content as data; fixed role separation; allowlisted tools; no general network/shell/SQL; bounded context; output/citation validation |
| T-05 | Malicious source fetch/file parsing and SSRF | Critical | Domain approval; HTTPS; DNS/IP and redirect revalidation; egress limits; size/type/time limits; sandboxed parser; malware scanning; never execute active content |
| T-06 | Fabricated, stale, or mismatched citations | High | Approved immutable source versions; locator/checksum; claim-citation validation; effective dates; withdrawal/index purge; no-answer fallback |
| T-07 | Scheme/rule/prompt tampering | Critical | Immutable versions; RBAC; human review; separation of duties where required; hashes; append-only audit; deploy/config review |
| T-08 | SQL/OpenSearch/log injection and XSS | High | Typed/parameterized queries; reject raw DSL; output encoding/sanitization; CSP; structured logs; neutralize log control characters |
| T-09 | Sensitive data leakage to logs/models/errors | High | Data minimization/redaction; provider adapter allowlists; safe errors; no body/prompt logging; retention and access policy |
| T-10 | Payment webhook forgery, replay, or duplicate charge | Critical (later) | Hosted/tokenized provider flow; signature over raw body; timestamp tolerance; event idempotency; amount/currency lookup; ledger reconciliation; no card data |
| T-11 | Referral fraud/self-referral/reward duplication | High (later) | Opaque codes; attribution rules; identity/device/rate signals; delayed eligibility; idempotent ledger; manual review; audit |
| T-12 | Admin/reviewer privilege abuse | High | Least privilege; MFA; fresh authentication for critical actions; four-eyes review where approved; audit/alerts; session expiry |
| T-13 | Dependency/CI artifact compromise | High | Locked dependencies; review/automated scanning; protected branches; pinned actions; provenance/SBOM; isolated builds; short-lived cloud federation |
| T-14 | Resource exhaustion/cost abuse | High | Body/query/token limits; per-actor rate/concurrency quotas; provider budgets; timeouts/circuit breakers; queue backpressure; WAF |
| T-15 | Backup/replica data exposure or unrecoverable loss | High | Encryption/KMS; access isolation; tested restore; retention; deletion propagation; documented RPO/RTO |
| T-16 | Audit repudiation or correlation failure | Medium | Trusted server timestamps; actor/resource/outcome/correlation IDs; append-only controls; time synchronization; restricted deletion |

## 5. Authentication and secure sessions

- Choose an OIDC provider through an ADR; validate issuer, audience, signature, nonce/state, expiry, and allowed algorithms.
- Prefer a Backend-for-Frontend secure session for browser use: opaque session identifier in `Secure`, `HttpOnly`, appropriately `SameSite` cookie; never browser storage for long-lived tokens.
- Rotate identifiers after authentication and privilege changes. Enforce idle and absolute expiry, explicit logout/revocation, and concurrent-session policy.
- State-changing cookie-authenticated requests require CSRF protection and origin checks.
- Privileged roles require MFA and step-up/fresh authentication for publication, role, refund, and security-sensitive actions.
- Password/reset storage and policy remain the identity provider's responsibility unless a future ADR accepts that scope.

## 6. Authorization and administration

Central permission definitions distinguish tenant user, advisor, reviewer, administrator, auditor, finance operator, and support roles. Route checks are insufficient: services reauthorize the action and all referenced resources. Reviewer/admin actions record actor, reason where required, before/after version references, outcome, and correlation ID. Support impersonation is prohibited in MVP; any later implementation needs explicit consent/notice, short duration, and complete audit.

## 7. AI and ingestion controls

- Model providers receive only the minimum data required and never session/payment credentials.
- Provider adapters expose fixed capabilities and cannot expand graph tools.
- Prompt versions are reviewed artifacts without secrets; model output is schema-validated.
- Retrieved text is isolated as untrusted evidence. Source content cannot modify instructions, prompt versions, roles, filters, or tool selection.
- Only published, approved, effective content enters user retrieval; the API rechecks sensitive operations against PostgreSQL.
- Models cannot publish sources/rules/prompts, grant roles, make payments/refunds, or award referral credit.

## 8. Payment and referral boundary (later phase)

Use a payment provider's hosted/tokenized flow; MSME Saarthi stores customer, checkout, transaction, invoice, and refund references, not card/account credentials. Webhooks are signature-verified before parsing into domain commands, replay-protected, idempotent, and reconciled. Entitlements derive from an auditable internal ledger, not a browser redirect alone.

Referral codes must reveal no user data. Attribution and reward rules are immutable/versioned, enforce self-referral and duplication policy, and post through an idempotent ledger only after qualifying conditions. Financial/admin reversals use reason codes and audit events.

## 9. Deployment and operations

- AWS data stores live in private subnets with least-privilege security groups and IAM roles.
- TLS is required in transit; KMS-backed encryption protects data at rest; secrets use a managed secret store and rotation.
- Separate accounts/environments and Terraform state; production access is temporary, approved, and logged.
- GitHub Actions uses pinned actions and OIDC federation rather than static AWS keys.
- WAF/load balancing, container/image scanning, patch policy, alarms, backup restore tests, and incident runbooks are production gates.
- Logs/traces use structured allowlists and restricted retention; alert on auth abuse, publication changes, webhook failures, cross-tenant denials, and unusual provider spend.

## 10. Verification and release gates

- Threat-focused unit/integration tests for auth, tenant isolation, injection, unsafe URLs, citations, eligibility invariants, webhooks, and idempotency.
- Dependency, secret, IaC, container, and static analysis in CI.
- Independent authorization and prompt-injection review before pilot.
- Restore, key/secret rotation, source withdrawal, compromised account, and provider outage exercises.
- No open critical findings; high findings require remediation or time-bounded written risk acceptance by the owner.

## 11. Residual risks and open decisions

- Identity/session provider and exact token/cookie topology.
- Provider data regions, retention, training use, and contractual controls.
- Retention/legal basis for profiles, chat, assessments, audit, payment, and referral records.
- Reviewer separation-of-duties and emergency publication/withdrawal process.
- Initial AWS services, RPO/RTO, and incident response ownership.
- Payment/referral provider and jurisdiction-specific compliance before those phases begin.

Review this model at each major architecture change, before production, after a material incident, and at least annually.

