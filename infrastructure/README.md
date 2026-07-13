# Local infrastructure

`compose.yaml` provisions development-only PostgreSQL, Redis and OpenSearch services on loopback interfaces. It does not represent a production deployment and none of its credentials may be reused outside local development.

```bash
make infra-up
make infra-down
```

Chat still uses a process-local message adapter. Starting these containers makes PostgreSQL, Redis, and OpenSearch available, but only the identity/profile/session module is wired to SQL persistence today.

Account, tenant, enterprise-profile, and secure-session persistence now uses SQLAlchemy and Alembic. PostgreSQL is the production and shared-development target. When Docker is unavailable, an explicitly configured SQLite URL may be used only as a single-process local preview; it is not a supported production topology.

Terraform and AWS delivery remain intentionally absent until compute topology, identity, environment isolation, state management and recovery requirements receive ADR approval.
