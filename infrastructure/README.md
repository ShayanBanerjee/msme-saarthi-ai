# Local infrastructure

`compose.yaml` provisions development-only PostgreSQL, Redis and OpenSearch services on loopback interfaces. It does not represent a production deployment and none of its credentials may be reused outside local development.

The OpenSearch bootstrap password exists only because the upstream image requires one during startup. Security is disabled for this loopback-only development container; production must enable authentication, TLS and managed-secret delivery.

```bash
make infra-up
make infra-down
```

Identity, encrypted profiles, secure sessions and completed chat turns use PostgreSQL through SQLAlchemy and Alembic. Redis remains an ephemeral coordination boundary. OpenSearch is a derived evidence index populated by the explicit worker ingestion command; it is never the eligibility or publication authority.

Account, tenant, enterprise-profile, and secure-session persistence now uses SQLAlchemy and Alembic. PostgreSQL is the production and shared-development target. When Docker is unavailable, an explicitly configured SQLite URL may be used only as a single-process local preview; it is not a supported production topology.

Terraform and AWS delivery remain intentionally absent until compute topology, identity, environment isolation, state management and recovery requirements receive ADR approval.

## Database environments

Local Docker uses the loopback-only URL in `.env.example`. Run `make infra-up`, then `make api-migrate`. Named volumes preserve data across ordinary container restarts and `make infra-down`.

For AWS, replace only the connection URL with a private Amazon RDS/Aurora PostgreSQL endpoint and obtain credentials from Secrets Manager. Require TLS, KMS encryption, automated backups, Multi-AZ where required, connection pooling, private security groups and restore testing.

For Azure, use a private Azure Database for PostgreSQL Flexible Server endpoint with Key Vault-managed credentials, TLS, private networking, zone-redundant high availability where required, backups and restore testing. Application migrations remain Alembic-controlled in either cloud; do not run `create_all` in production.
