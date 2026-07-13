# Data Model

**Status:** Logical pre-implementation model  
**Last updated:** 2026-07-13  
**Related:** [Architecture overview](OVERVIEW.md), [Eligibility engine](../ai/ELIGIBILITY_ENGINE.md), [RAG design](../ai/RAG_DESIGN.md)

## 1. Conventions

- PostgreSQL is authoritative; OpenSearch and Redis contain derived/ephemeral data.
- Primary identifiers are UUIDs. Public IDs are opaque and never encode tenant or sequence information.
- Mutable tables include `created_at`, `updated_at`, and optimistic concurrency (`version` or equivalent).
- Times are timezone-aware UTC; presentation converts to user locale.
- User-controlled text is Unicode-normalized and length-limited at the boundary.
- Enumerations are validated in shared schemas. Database constraints protect critical invariants.
- Tenant-owned rows carry `tenant_id`; repository queries and service authorization must both enforce scope.
- Published content and completed assessments are immutable. Corrections create new versions.
- Flexible JSON is allowed only for versioned, validated payloads; queryable identity, state, and relationship fields remain relational.

## 2. Core relationships

```text
Tenant 1---* Membership *---1 User
User 1---* Session
Tenant 1---* EnterpriseProfile 1---* ProfileVersion

Scheme 1---* SchemeVersion 1---* SchemeClaim *---1 Citation
Source 1---* SourceVersion 1---* Citation
SchemeVersion 1---* RuleSetVersion 1---* RuleDefinition

ProfileVersion 1---* Assessment *---1 RuleSetVersion
Assessment 1---* RuleOutcome

Conversation 1---* Message *---* Citation
Prompt 1---* PromptVersion
Tenant 1---* PaymentAccount 1---* PaymentTransaction
User 1---* ReferralAttribution
IngestionJob -> Source/SourceVersion
AuditEvent -> actor + typed resource reference
```

## 3. Identity and tenancy

### `users`

External or internal identity reference. Fields: `id`, `identity_provider`, `subject`, `email_normalized` (nullable where provider permits), `status`, timestamps. Unique on provider/subject. Authentication credentials are not stored unless an approved in-house identity design explicitly requires it.

### `tenants`

Organization/security boundary. Fields: `id`, `name`, `slug`, `status`, timestamps. A single-owner account may still receive its own tenant to keep authorization consistent.

### `memberships`

Fields: `tenant_id`, `user_id`, `role`, `status`, timestamps. Unique on tenant/user. Initial roles: `owner`, `advisor`, `viewer`, `content_reviewer`, `admin`, `auditor`; permissions are centrally mapped and deny by default.

### `sessions`

Server-side secure session metadata. Fields: `id`, `user_id`, `token_hash`, `created_at`, `last_seen_at`, `idle_expires_at`, `absolute_expires_at`, `revoked_at`, `auth_context`, and bounded device metadata. Store only a hash of an opaque session secret. Rotation replaces the identifier; logout/revocation is auditable.

## 4. Enterprise profiles

### `enterprise_profiles`

Stable profile identity and current-version pointer. Fields: `id`, `tenant_id`, `display_name`, `status`, `current_version_id`, timestamps. The pointer update and new version insert occur in one transaction.

### `profile_versions`

Immutable normalized facts used for assessment. Fields:

- `id`, `tenant_id`, `profile_id`, `version_number`;
- `schema_version`;
- `facts` JSONB validated by the versioned profile schema;
- `facts_hash` over canonical normalized facts;
- `created_by`, `created_at`, `supersedes_id`.

The MVP profile schema is finalized with the rule taxonomy. Likely categories include registration/classification, location, sector/activity, ownership attributes, enterprise age, financial bands, and existing-benefit facts. Sensitive identifiers and documents are excluded unless a reviewed requirement adds them.

Facts distinguish `unknown` from false/zero. Each fact may carry provenance (`user_asserted`, `verified_source`, `derived`) and confirmation time. Derived facts must name a deterministic derivation version.

## 5. Sources, schemes, and claims

### `sources`

Approved source identity. Fields: `id`, `canonical_url`, `domain`, `authority_name`, `source_type`, `approval_status`, `fetch_policy`, `created_by`, timestamps. Canonical URL is unique. Only approved sources may produce publishable citations.

### `source_versions`

Immutable capture. Fields: `id`, `source_id`, `retrieved_at`, `effective_date` (nullable), `content_checksum`, `content_type`, `storage_uri`, `http_metadata`, `parser_version`, `status`, `supersedes_id`. Store sanitized extracted text separately from original bytes. A unique source/checksum constraint prevents duplicate versions.

### `schemes`

Stable identity. Fields: `id`, `scheme_code`, `owning_authority`, `lifecycle_status`, timestamps. `scheme_code` is internal and does not imply an official identifier.

### `scheme_versions`

Immutable reviewed representation. Fields: `id`, `scheme_id`, `version_number`, `title`, `summary`, `language`, `geographic_scope`, `benefit_types`, `valid_from`, `valid_until`, `application_url`, `publication_status`, `reviewed_by`, `reviewed_at`, `published_at`, `supersedes_id`, timestamps.

At most one active published version per scheme/language/effective period is enforced by service logic and suitable constraints. Withdrawal stops new discovery/assessment but does not erase history.

### `scheme_claims`

Atomic material assertions. Fields: `id`, `scheme_version_id`, `claim_type`, `claim_text`, `normalized_value` (nullable), `review_status`, `display_order`. Material claim types include eligibility, benefit, deadline/effective period, coverage, required document, and application step.

### `citations`

Fields: `id`, `source_version_id`, `locator_type`, `locator` JSONB, `quoted_excerpt` (bounded), `excerpt_hash`, `label`. Locator examples are page/section, heading/paragraph, or character offsets against normalized captured text. A citation is resolvable only if its source version remains retained and approved.

### `claim_citations`

Join table: `claim_id`, `citation_id`, `support_type` (`supports`, `qualifies`, `conflicts`), reviewer metadata. A published material claim requires at least one `supports` citation from an approved source version.

## 6. Deterministic rules

### `rule_set_versions`

Immutable set associated with a scheme version. Fields: `id`, `scheme_version_id`, `version_number`, `engine_schema_version`, `root_rule_id`, `publication_status`, `reviewed_by`, `reviewed_at`, `rules_hash`, timestamps. A published scheme that supports assessment has exactly one active published rule set.

### `rule_definitions`

Fields: `id`, `rule_set_version_id`, `rule_key`, `rule_type`, `operator`, `fact_path`, `expected_value`, `children`, `missing_policy`, `explanation_template`, `display_order`, `citation_id`. The persisted representation must validate against the engine schema; exact JSON-versus-relational storage is an implementation ADR. Eligibility constants/operators require supporting citations.

## 7. Assessments

### `assessments`

Immutable evaluation header. Fields:

- `id`, `tenant_id`, `profile_id`, `profile_version_id`;
- `scheme_id`, `scheme_version_id`, `rule_set_version_id`;
- `status` (`pending`, `completed`, `failed`);
- `decision` (`eligible`, `ineligible`, `insufficient_information`, nullable until complete);
- `input_hash`, `engine_version`, `started_at`, `completed_at`, `requested_by`;
- `missing_fact_paths`, `failure_code` (non-sensitive), `correlation_id`.

Completed decision and version references cannot be updated. Retrying infrastructure failure creates an attempt record or a new assessment according to the service contract; it never silently changes a completed result.

### `rule_outcomes`

Fields: `id`, `assessment_id`, `rule_key`, `outcome` (`satisfied`, `failed`, `unknown`, `not_evaluated`), `actual_value_redacted`, `reason_code`, `citation_id`, `display_order`. Avoid duplicating sensitive profile values; store only what is needed for reproducibility and safe explanation.

## 8. Conversations

### `conversations`

Fields: `id`, `tenant_id`, `user_id`, optional `profile_id`, `status`, `created_at`, `updated_at`, `retention_expires_at`.

### `messages`

Fields: `id`, `conversation_id`, `role`, `content`, `content_format`, `model_metadata` (allowlisted fields only), `safety_status`, `created_at`. Do not store hidden reasoning, secrets, or unrestricted provider payloads.

### `message_citations`

Join table: `message_id`, `citation_id`, `claim_marker`, `display_order`. All material assistant claims must map to one or more citations or the message must explicitly state insufficient evidence.

### `prompts` and `prompt_versions`

`prompts` provides a stable name/use case and current-version pointer. Immutable `prompt_versions` contain semantic version, content hash, template content, input/output schema versions, compatible capabilities, lifecycle status, owner/reviewer, evaluation reference, and timestamps. Messages record the exact prompt version and provider/model configuration. Prompts contain no secrets or personal test data.

## 9. Later-phase commerce and referrals

### `payment_accounts`, `payment_transactions`, and `entitlement_ledger`

Store provider/customer/checkout/transaction/invoice/refund references, status, amount as exact decimal plus currency, provider event ID, idempotency key, and timestamps. Never store card or bank credentials. Entitlements are append-only ledger entries derived from verified/reconciled provider events; corrections use compensating entries.

### `referral_codes`, `referral_attributions`, and `referral_ledger`

Opaque codes map to referrers without exposing identity. Attributions record referred party, consent/time, campaign/rule version, status, and anti-abuse review. Rewards and reversals use an idempotent append-only ledger. Self-referral and duplicate policies are enforced by a versioned service rule, not a model.

## 10. Operations and audit

### `ingestion_jobs`

Fields: `id`, `job_type`, optional `source_id`/`source_version_id`, `idempotency_key`, `status`, `attempt_count`, `next_attempt_at`, `error_code`, `correlation_id`, timestamps. Error details are sanitized.

### `outbox_events`

Fields: `id`, `aggregate_type`, `aggregate_id`, `event_type`, `payload` (minimal and versioned), `created_at`, `published_at`, `attempt_count`. Consumers are idempotent.

### `audit_events`

Append-only fields: `id`, `occurred_at`, `actor_type`, `actor_id`, `tenant_id`, `action`, `resource_type`, `resource_id`, `outcome`, `correlation_id`, `metadata` (allowlisted). Audit events record authorization and state transitions, not raw profile/document content.

## 11. OpenSearch document model

One index document represents a publishable chunk and includes:

- `chunk_id`, `chunk_text`, `embedding`, `language`;
- `scheme_id`, `scheme_version_id`, structured discovery facets;
- `source_id`, `source_version_id`, `citation_id`, locator;
- `publication_status`, effective dates, visibility/tenant scope;
- `content_checksum`, `index_schema_version`, `indexed_at`.

Queries always filter publication state and visibility before ranking. Alias-based versioned indices allow atomic rebuilds. Indexed content must be reconstructible from authoritative records and snapshots.

## 12. Retention and deletion

Retention values are a pre-production policy decision. The design must support:

- soft deletion/deactivation for user-facing resources;
- deletion or anonymization of tenant profile/conversation data after an approved request;
- retention of minimal immutable audit and assessment evidence where legally justified;
- source/version retention while referenced by published claims or historical assessments;
- index/cache purge driven from authoritative deletion/withdrawal events; and
- backup expiry consistent with the published retention policy.

## 13. Required database invariants

- Foreign keys cannot cross tenant boundaries; enforce with composite keys or transaction/service checks plus tests.
- Version numbers are unique within their parent.
- Published rule sets and material claims have valid approved citations.
- Completed assessment version references and outcomes are immutable.
- Idempotency and outbox keys are unique in their documented scope.
- Lifecycle transitions use an allowlisted state machine.
- Migrations are forward-tested against representative production-scale data and include rollback or roll-forward guidance.
