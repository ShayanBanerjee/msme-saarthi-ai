# ADR-0006: First-party identity and encrypted profiles

**Status:** Accepted for MVP implementation  
**Date:** 2026-07-13

## Context

The product requires self-service account registration before an external OIDC provider has been selected. Account credentials, sessions, names, and business-profile identifiers are sensitive. The browser must not hold reusable bearer tokens, and PostgreSQL must remain the system of record.

## Decision

Implement a replaceable first-party identity module inside the modular monolith:

- Passwords are hashed with Argon2id and are never encrypted or logged.
- Email addresses, personal names, business names, and tenant display names are encrypted with AES-256-GCM. A keyed, domain-separated HMAC blind index supports normalized email lookup without storing the address in plaintext.
- Encryption keys are supplied externally, carry a version identifier, and are never stored in the database or repository. Production keys belong in AWS Secrets Manager and require an explicit rotation runbook.
- Browser sessions use a high-entropy opaque secret in an `HttpOnly`, `SameSite=Lax`, production-`Secure` cookie. PostgreSQL stores only a SHA-256 token hash, idle/absolute expiry, and revocation metadata.
- State-changing authenticated requests enforce an allowed browser origin. Service and repository boundaries remain tenant-scoped.
- PostgreSQL storage must use TLS in transit and KMS-backed encryption at rest in AWS. Application encryption is defense in depth, not a replacement for storage encryption, backups, or access controls.

The identity interfaces must remain replaceable by an approved OIDC adapter. Privileged accounts and administration still require OIDC/MFA before production.

## Consequences

- Local development needs a stable 32-byte base64 encryption key; losing it makes encrypted fields unrecoverable.
- Email lookup uses a blind index and cannot support prefix search.
- Key rotation requires decrypt-and-reencrypt migration with both old and new keys available during the transition.
- Password reset, email verification, abuse throttling, MFA, retention, and recovery workflows remain production launch gates.

## Alternatives considered

- **Wait for OIDC selection:** safest operationally, but blocks requested self-service onboarding.
- **Store profile fields only with disk encryption:** simpler, but weaker against database-only disclosure.
- **Put access tokens in browser storage:** rejected because script compromise would expose reusable credentials.
