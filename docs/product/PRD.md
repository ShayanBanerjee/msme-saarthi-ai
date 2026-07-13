# Product Requirements Document

**Status:** Living product contract; MVP partially implemented
**Last updated:** 2026-07-13  
**Owner:** Product and engineering  
**Related:** [Architecture overview](../architecture/OVERVIEW.md), [Backlog](../planning/BACKLOG.md)

## 1. Product summary

MSME Saarthi AI helps Indian micro, small, and medium enterprises discover government schemes, understand cited scheme information, and assess potential eligibility. It combines approved-source retrieval with deterministic eligibility rules. It is decision support, not an application portal, legal opinion, or guarantee of approval.

The core product promise is traceability: a user can see which profile facts and versioned rules produced an eligibility result, and which approved source supports every material scheme claim.

The current product implements public scheme discovery, State/UT official-source navigation, self-service accounts and secure sessions, a founder shell, streamed cited chat, OpenSearch retrieval, explicit source ingestion, and the standalone eligibility engine. Saved profile editing, persisted assessments, reviewer administration/publication, audit views, recovery/MFA, payments/referrals, and production deployment remain incomplete. “Pro” is presentation and waitlist positioning only; no paid entitlement or checkout is active.

## 2. Problem

Scheme information is fragmented across government websites and documents, can change over time, and is often difficult to compare with an enterprise's circumstances. Users need a reliable way to:

- find relevant programmes without knowing their formal names;
- distinguish current, authoritative information from unsupported summaries;
- identify missing profile data and documents;
- understand why they appear eligible, ineligible, or cannot yet be assessed; and
- return to the official source to verify details and apply.

## 3. Users

### Primary users

- **MSME owner or operator:** discovers schemes and checks an enterprise profile.
- **Advisor or facilitator:** assists multiple enterprises and needs reproducible results.

### Operational users

- **Content reviewer:** approves sources, scheme versions, claims, and rule versions.
- **Platform administrator:** manages access and operational configuration.
- **Auditor/support operator:** investigates result provenance without changing it.

## 4. Product principles

1. **Rules decide eligibility.** The LLM must never create, override, or independently evaluate eligibility criteria.
2. **Claims require citations.** Material claims about scope, benefits, dates, eligibility, or application steps must cite an approved source and its captured version.
3. **Uncertainty is explicit.** Missing information, conflicting sources, stale content, and unsupported claims are shown rather than guessed.
4. **Official action stays official.** The product links to the approved official source; it does not imply submission or approval unless a future authorized integration provides it.
5. **Data minimization.** Collect only profile fields necessary for discovery and assessment; do not request sensitive documents in the MVP.
6. **Accessible by default.** Core flows support keyboard navigation, clear language, responsive layouts, and assistive technology.

## 5. MVP scope

### 5.1 Account and enterprise profile

- Sign in and sign out.
- Use secure, revocable, expiring browser sessions and record security-relevant session events.
- Create and update an enterprise profile using structured, validated fields.
- Record field provenance and user confirmation time.
- Keep separate enterprises isolated by tenant and authorization boundaries.
- Show which profile fields are missing for an assessment.

### 5.2 Scheme catalogue and discovery

- Browse, filter, search, and paginate published scheme versions.
- Filter by supported structured facets such as geography, administering authority, sector, enterprise classification, and benefit type.
- Show scheme summaries, status, last verified date, official links, and inline citations.
- Exclude drafts and unapproved sources from public results.

### 5.3 Eligibility assessment

- Evaluate a selected published scheme version against a saved profile snapshot.
- Return exactly one result: `eligible`, `ineligible`, or `insufficient_information`.
- Show satisfied, failed, and unevaluated rule outcomes and required missing fields.
- Preserve the profile snapshot, rule-set version, scheme version, and outcome for auditability.
- Never describe `eligible` as guaranteed approval.

### 5.4 Guided assistant

- Accept natural-language discovery questions.
- Retrieve only from published scheme content backed by approved source versions.
- Ask for missing profile information using typed fields.
- Explain an existing deterministic assessment result.
- Produce cited comparisons, summaries, and checklists.
- Decline or qualify an answer when supporting evidence is unavailable.

### 5.5 Content ingestion and publishing

- Register allowlisted official sources.
- Fetch and store immutable source snapshots and provenance.
- Extract text, create chunks, and index published content.
- Require human review before a new or changed scheme/rule version is published.
- Re-index or withdraw content when publication status changes.

### 5.6 Administration and audit

- Provide role-gated workflows for source, scheme, rule, and prompt review and publication.
- Record append-only audit events for authentication, authorization failures, content lifecycle changes, assessment creation, and privileged actions.
- Expose only the minimum audit metadata needed by authorized reviewers and support staff.

### 5.7 Founder growth and membership presentation

- Give founders an educational, non-predictive roadmap from idea definition through formalisation, funding readiness, and initial market validation.
- Present Free and proposed Pro capabilities clearly without manufacturing urgency, outcomes, savings, or approval claims.
- Allow a non-transactional Pro waitlist during MVP validation. Do not collect payment details or grant paid entitlements before the later payment architecture is approved.
- Keep growth guidance distinct from legal, tax, investment, credit, or application advice.

## 6. Out of scope for MVP

- Filing applications or uploading documents to government portals.
- Approval predictions, benefit guarantees, or legal/financial advice.
- Rules inferred solely from an LLM extraction.
- Autonomous web crawling outside approved domains.
- OCR and storage of identity, banking, tax, or other sensitive application documents.
- Automated rule publication without a reviewer.
- Native mobile applications, payment collection, referral rewards, lender marketplace, or multilingual generation beyond explicitly validated languages.

## 6.1 Later phases

- **Payments:** provider-hosted checkout, subscription/entitlement ledger, invoices, refunds, signed webhooks, and reconciliation. The platform must not store card or bank credentials.
- **Referrals:** opaque referral codes, consented attribution, abuse controls, versioned reward rules, and an auditable idempotent reward ledger.
- **Expanded administration:** operational dashboards, staged publication approvals, finance operations, and reviewed support tooling.
- **Personalization:** proactive alerts and advisor batch workflows, always preserving citations and the deterministic eligibility boundary.

## 7. Key user journeys

### Journey A: discover and assess

1. User creates or selects an enterprise profile.
2. User searches or asks a discovery question.
3. System returns published schemes with citations and verification dates.
4. User selects a scheme and starts an assessment.
5. Eligibility engine evaluates a frozen profile snapshot against a published rule set.
6. UI explains the outcome and links every material scheme statement to evidence.
7. User follows the official source to verify or apply.

### Journey B: complete missing information

1. Assessment returns `insufficient_information` with field identifiers.
2. UI or assistant asks only for those typed fields.
3. User validates and saves the profile changes.
4. System starts a new assessment; it does not mutate the historical result.

### Journey C: publish a scheme update

1. Worker captures an approved source snapshot.
2. Extraction creates a draft scheme/source representation.
3. Reviewer verifies claims, citations, dates, and deterministic rules.
4. Publishing creates immutable versions and triggers indexing.
5. New assessments use the new published rule version; historical assessments retain the prior version.

## 8. Functional requirements

| ID | Requirement | Acceptance signal |
|---|---|---|
| FR-01 | Only published scheme versions are user-visible. | Draft/withdrawn versions cannot be returned by public APIs. |
| FR-02 | Material scheme claims contain citations. | Contract and UI tests reject uncited material claims. |
| FR-03 | Eligibility is deterministic and versioned. | Same normalized input and rule version produce the same result. |
| FR-04 | Missing inputs do not default to false. | Required unknown facts produce `insufficient_information`. |
| FR-05 | Results are explainable. | Response includes per-rule outcomes and profile/rule version identifiers. |
| FR-06 | Assistant cannot overwrite an engine result. | Graph state and API schemas accept results only from the engine service. |
| FR-07 | External inputs are validated. | Invalid bodies, filters, rule definitions, and source URLs fail safely. |
| FR-08 | Published evidence is traceable. | A citation resolves to source snapshot, locator, checksum, and capture time. |
| FR-09 | Tenant data is isolated. | Service and repository tests deny cross-tenant access. |
| FR-10 | Historical assessments are immutable. | Profile edits create a new assessment rather than changing old evidence. |
| FR-11 | Sessions are secure and revocable. | Expired/revoked sessions fail and privileged actions are audited. |
| FR-12 | Prompts are versioned. | Each generated response records the immutable active prompt version. |
| FR-13 | Privileged workflows are role-gated and audited. | Unauthorized transitions fail; successful transitions have attributable audit events. |
| FR-14 | Later payment/referral state is ledger-based and idempotent. | Duplicate provider/referral events do not duplicate entitlements or rewards. |

## 9. Non-functional requirements

- **Availability target:** 99.5% monthly for user-facing MVP APIs, excluding planned maintenance.
- **Performance target:** p95 under 500 ms for catalogue reads and under 2 seconds for non-LLM eligibility evaluation, measured server-side under the documented load profile.
- **Assistant latency:** stream an initial status within 2 seconds when the model provider is reachable; enforce an overall timeout and graceful fallback.
- **Security:** follow [THREAT_MODEL.md](../security/THREAT_MODEL.md), encrypt data in transit and at rest, and audit privileged actions.
- **Privacy:** define retention by data class before production; support account/profile deletion subject to audit and legal requirements.
- **Observability:** propagate correlation IDs and record metrics, structured logs, and traces without profile values or secrets.
- **Accessibility:** target WCAG 2.2 AA for core journeys.
- **Recovery:** define and test production RPO/RTO before launch; backups alone do not satisfy recovery readiness.

Targets are launch gates to validate, not claims about the unimplemented system.

## 10. Success measures

Initial instrumentation should measure:

- percentage of surfaced material claims with resolvable approved citations (target: 100%);
- percentage of assessments reproducible from stored snapshots and versions (target: 100%);
- search-to-scheme-detail and detail-to-assessment conversion;
- proportion of `insufficient_information` assessments subsequently completed;
- citation-open rate and official-link click-through rate;
- zero known cases where LLM output changes an engine decision;
- content freshness and time from detected source change to reviewed publication.

Business targets require a baseline and product approval before numeric goals are set.

## 11. Launch gates

- Critical and high threat-model controls are implemented or explicitly risk-accepted.
- A representative golden rule suite passes with reviewer-approved expected results.
- Citation coverage and resolution checks pass for all published schemes.
- Authorization, tenant isolation, prompt-injection, backup restore, and withdrawal runbooks are tested.
- Accessibility review covers profile, discovery, detail, and assessment flows.
- Disclaimers and privacy/retention policy are reviewed by the appropriate owners.

## 12. Open product decisions

- Identity provider and whether advisors may manage multiple client organizations.
- Initial languages and the review process for translated official content.
- Exact profile taxonomy and supported scheme categories for the pilot.
- Retention periods and regional data residency requirements.
- Reviewer separation-of-duties and publication approval count.
- Pilot load assumptions and final SLO/RPO/RTO values.
