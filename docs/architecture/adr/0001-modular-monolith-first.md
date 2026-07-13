# ADR-0001: Modular Monolith First

**Status:** Accepted  
**Date:** 2026-07-13

## Context

The product spans identity, profiles, schemes, chat, eligibility, content administration, payments, and referrals, but begins without validated scale or team boundaries. Premature distributed services would add network contracts, deployment coordination, and consistency failure modes.

## Decision

Start with a FastAPI modular monolith and separate worker process in one monorepo. Feature packages expose typed service interfaces and own API/service/repository/domain layers. PostgreSQL is the transactional system of record; Redis and OpenSearch are supporting stores. The pure eligibility engine remains an independent package. Modules must not reach into another module's repositories or tables except through an owned service contract.

## Consequences

Local transactions and deployments are simpler, and vertical slices remain reviewable. Boundaries require enforcement by conventions/tests rather than networks. Modules can be extracted later based on observed scaling, security, ownership, or availability needs.

## Alternatives considered

- Microservices now: rejected due to operational and consistency cost before evidence.
- Unstructured single application package: rejected because it obscures business/security boundaries.

