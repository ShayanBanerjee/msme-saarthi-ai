# MSME Saarthi AI

MSME Saarthi AI is a production-shaped MVP for Indian entrepreneurs to discover officially sourced MSME support, structure a growth plan, explore a venture thesis, and run deterministic eligibility assessments.

The language model is not allowed to decide eligibility. Material scheme claims must resolve to approved official evidence, and users must verify programme details at the linked government source before acting.

## Current implementation status

The repository currently provides:

- an animated React 19, TypeScript, Vite, Tailwind CSS and shadcn-style frontend;
- a public, scheme-first discovery experience with conservative official-source summaries;
- a 36-jurisdiction State and Union Territory startup-policy atlas sourced from Startup India's June 2026 playbook;
- self-service registration, login, logout and session restoration;
- AES-256-GCM encryption for email, personal name, business name and tenant display name;
- Argon2id password hashing and opaque revocable server-side sessions;
- tenant, owner membership and enterprise-profile bootstrap during registration;
- SQLAlchemy 2 persistence with Alembic migrations and PostgreSQL support;
- a local encrypted SQLite fallback for single-developer preview environments;
- a FastAPI modular monolith with standardized errors and structured logging;
- a protected, streamed LangGraph RAG assistant with curated official evidence and an optional OpenAI Responses API adapter;
- PostgreSQL-backed completed chat history in shared-development and production configurations;
- an allowlisted ingestion worker that extracts untrusted web text, chunks it, derives embeddings and writes a versioned OpenSearch index;
- an OpenSearch hybrid-retrieval adapter with BM25, vector retrieval and reciprocal-rank fusion;
- a standalone deterministic eligibility engine; and
- a curated, date-stamped official-source scheme discovery preview.

Public visitors can browse the curated programme library and State/UT source atlas before creating an account. Government information is not paywalled. The planned paid experience is a guided business-to-scheme fit map, comparison workflow and evidence-gap tracker; it is clearly marked as coming soon and no checkout is active.

MSME Saarthi AI is independent and is not a Government of India portal. The product does not display the State Emblem or imply government affiliation. Links labeled as official sources open the responsible authority or an official national source registry; users must confirm current terms and application windows there.

This is not yet a production launch. Source review/publication is operator-controlled, paid checkout is not active, and Terraform/GitHub Actions deployment automation has not been implemented.

## Repository layout

```text
apps/
  api/                      FastAPI modular monolith and Alembic migrations
  web/                      React/Vite frontend
  worker/                   Allowlisted source extraction and OpenSearch indexing
packages/
  eligibility-engine/       Pure deterministic rules and evaluation
infrastructure/
  compose.yaml              Local PostgreSQL, Redis and OpenSearch
scripts/
  bootstrap-local.sh        Creates a restricted local API environment
  check-local.sh            Verifies API health and frontend routes
docs/                       Product, architecture, AI, security and testing contracts
```

Shared generated contracts, Terraform and deployment workflows are planned but not present.

## Architecture at a glance

```text
Browser
  │ secure HttpOnly session cookie
  ▼
React/Vite ───────► FastAPI modular monolith
                       ├── PostgreSQL: identity/profile/session authority
                       ├── Eligibility engine: deterministic decisions only
                       ├── LangGraph: guided orchestration
                       ├── OpenSearch: derived retrieval index
                       └── Redis: planned cache/coordination boundary
```

The Vite development server proxies `/api` to `http://127.0.0.1:8000`, keeping browser authentication same-origin during local development.

## Prerequisites

- macOS, Linux or WSL with a POSIX-compatible shell
- Python 3.12 or 3.13
- Node.js 22 or newer and npm
- OpenSSL for local encryption-key generation
- Docker Desktop or a compatible Docker engine for PostgreSQL, Redis and OpenSearch
- at least 2 GB of free memory when running OpenSearch locally

Docker is optional for the single-process SQLite preview. PostgreSQL is the supported shared-development and production database.

## Quick start: local SQLite preview

Use this path when Docker is unavailable. SQLite is persistent but intended only for one local API process.

```bash
git clone <repository-url>
cd msme-saarthi-ai

python3.12 -m venv .venv
source .venv/bin/activate

make api-install PYTHON="$PWD/.venv/bin/python"
make eligibility-install PYTHON="$PWD/.venv/bin/python"
make web-install

make local-bootstrap
make api-migrate PYTHON="$PWD/.venv/bin/python"
```

`make local-bootstrap` creates `apps/api/.env` with a new 256-bit encryption key and a SQLite URL. It refuses to overwrite an existing file because replacing the key would make existing encrypted values unreadable.

Start the API in terminal one:

```bash
make api-run PYTHON="$PWD/.venv/bin/python"
```

Start the web application in terminal two:

```bash
make web-run
```

### Enable the GPT-backed RAG answer adapter

The default remains deterministic and does not require a provider account. To use OpenAI, create a key at the [OpenAI API key page](https://platform.openai.com/api-keys), set it only in `apps/api/.env`, and restart the API:

```dotenv
MSME_SAARTHI_LLM_PROVIDER=openai
MSME_SAARTHI_OPENAI_API_KEY=<set-locally-never-commit>
MSME_SAARTHI_OPENAI_MODEL=gpt-5.4-mini
```

The key is server-side only. The browser never receives it. The adapter uses the Responses API behind the application-owned provider interface; retrieved text is delimited as untrusted evidence and the model is prohibited from deciding eligibility.

Open:

- application: http://127.0.0.1:5173
- API documentation: http://127.0.0.1:8000/docs
- API liveness: http://127.0.0.1:8000/api/v1/health/live
- API readiness: http://127.0.0.1:8000/api/v1/health/ready

## Full local services with PostgreSQL

Start Docker Desktop first, then configure the API for PostgreSQL:

```bash
python3.12 -m venv .venv
source .venv/bin/activate

make api-install PYTHON="$PWD/.venv/bin/python"
make eligibility-install PYTHON="$PWD/.venv/bin/python"
make web-install

./scripts/bootstrap-local.sh postgres
make infra-up
make api-migrate PYTHON="$PWD/.venv/bin/python"
```

The Compose stack binds development services only to loopback:

| Service | Address | Purpose |
|---|---|---|
| PostgreSQL | `127.0.0.1:5432` | Authoritative identity, tenant, profile and session data |
| Redis | `127.0.0.1:6379` | Future cache, rate limits and job coordination |
| OpenSearch | `127.0.0.1:9200` | Hybrid-retrieval development service |

The Compose credentials and disabled OpenSearch security are local-only. Never expose these ports or reuse these settings in staging or production.

Inspect service state with:

```bash
docker compose -f infrastructure/compose.yaml ps
```

Stop services without deleting their named volumes:

```bash
make infra-down
```

## Existing local environments

If `apps/api/.env` already exists, do not rerun the bootstrap script. Confirm that it contains the intended database URL and keep its encryption key stable:

```dotenv
MSME_SAARTHI_DATABASE_URL=postgresql+asyncpg://msme_saarthi:local-development-only@127.0.0.1:5432/msme_saarthi
MSME_SAARTHI_DATA_ENCRYPTION_KEY=<base64-encoded-32-byte-key>
MSME_SAARTHI_DATA_ENCRYPTION_KEY_VERSION=v1
MSME_SAARTHI_WEB_ORIGIN=http://127.0.0.1:5173
MSME_SAARTHI_SESSION_COOKIE_SECURE=false
```

Never commit `.env`, database files, session secrets or encryption keys. Local `.env` and runtime database files are ignored by Git.

## Database migrations

Alembic is the only supported schema-change mechanism outside tests.

Apply migrations:

```bash
make api-migrate PYTHON="$PWD/.venv/bin/python"
```

Check that models and migration history agree:

```bash
make api-migration-check PYTHON="$PWD/.venv/bin/python"
```

Create a reviewed migration after changing persistence models:

```bash
cd apps/api
../../.venv/bin/python -m alembic revision --autogenerate -m "describe change"
../../.venv/bin/python -m alembic upgrade head
```

Review generated migrations manually. Autogeneration does not validate data migration safety, tenant invariants or rollback strategy.

## RAG source ingestion

The worker pipeline is deliberately explicit:

```text
reviewed allowlist manifest
  → HTTPS fetch with redirect/host/size controls
  → visible-text extraction (retrieved instructions ignored)
  → deterministic chunks + checksums + citation metadata
  → embedding boundary
  → versioned OpenSearch evidence index
  → hybrid retrieval → LangGraph → cited streamed answer
```

Install and validate the manifest without network or index writes:

```bash
make worker-install PYTHON="$PWD/.venv/bin/python"
make ingestion-validate PYTHON="$PWD/.venv/bin/python"
```

After reviewing the manifest and starting OpenSearch, run ingestion explicitly:

```bash
cd apps/worker
../../.venv/bin/python -m worker.cli sources/official-central.json \
  --opensearch-url http://127.0.0.1:9200
```

Indexed pages remain untrusted evidence. This command does not create structured eligibility rules or publish an eligibility decision. Production requires immutable object snapshots, malware/content scanning, reviewer approval and durable ingestion-job records before scheduled ingestion is enabled.

## Authentication and data protection

- Passwords are one-way hashed with Argon2id and are never encrypted or logged.
- Sensitive identity/profile fields are encrypted with AES-256-GCM before persistence.
- Normalized email lookup uses a domain-separated HMAC blind index rather than plaintext email.
- The browser receives a high-entropy opaque session secret in an `HttpOnly`, `SameSite=Strict` cookie.
- Only the SHA-256 session-token hash is stored in the database.
- Sessions enforce idle and absolute expiry and are revoked on logout.
- Browser mutations with an unexpected `Origin` are rejected.
- Production must use HTTPS, `MSME_SAARTHI_SESSION_COOKIE_SECURE=true`, PostgreSQL TLS, KMS-backed storage encryption and a managed secret store.

Losing the application encryption key makes encrypted fields unrecoverable. Production key creation, access, rotation and recovery must be managed and audited.

## API endpoints implemented

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
GET  /api/v1/auth/me
POST /api/v1/auth/logout

GET  /api/v1/health/live
GET  /api/v1/health/ready

POST /api/v1/chat/conversations/{conversation_id}/messages
```

The chat endpoint streams Server-Sent Events and requires a valid session. Its current retriever and model provider are deterministic development adapters.

## Verification and tests

Verify a running API and every frontend route:

```bash
make local-check
```

Run frontend gates:

```bash
make web-lint
make web-typecheck
make web-test
make web-build
```

Run API gates:

```bash
make api-lint PYTHON="$PWD/.venv/bin/python"
make api-typecheck PYTHON="$PWD/.venv/bin/python"
make api-test PYTHON="$PWD/.venv/bin/python"
make api-test-integration PYTHON="$PWD/.venv/bin/python"
make api-migration-check PYTHON="$PWD/.venv/bin/python"
```

Run deterministic eligibility gates:

```bash
make eligibility-lint PYTHON="$PWD/.venv/bin/python"
make eligibility-typecheck PYTHON="$PWD/.venv/bin/python"
make eligibility-test PYTHON="$PWD/.venv/bin/python"
```

Focused retrieval checks:

```bash
make retrieval-test PYTHON="$PWD/.venv/bin/python"
make retrieval-test-integration PYTHON="$PWD/.venv/bin/python"
```

Do not report a command as passing unless it was executed in the current environment.

## Production build

Build the frontend artifact:

```bash
make web-build
```

The output is written to `apps/web/dist`. It must be served behind HTTPS with SPA fallback routing, immutable caching for hashed assets, a restrictive Content Security Policy and no secrets injected into browser code.

The installed API exposes the ASGI application as `app.main:app`. Production should run immutable application images behind a managed load balancer; do not use Uvicorn `--reload` or the Vite development server.

## Deployment status and AWS target

There is currently no production deployment command. The repository does not yet contain:

- application Dockerfiles or an image build/release workflow;
- `infrastructure/terraform` modules or remote-state configuration;
- GitHub Actions deployment workflows;
- an AWS environment/account strategy;
- database backup/restore automation; or
- reviewed SLO, RPO and RTO values.

The intended initial AWS topology, pending ADRs and Terraform implementation, is:

```text
DNS / TLS / WAF
       │
       ├── static web delivery for the compiled Vite assets
       └── managed load balancer ──► containerized FastAPI service
                                      ├── managed PostgreSQL with KMS encryption
                                      ├── managed Redis
                                      ├── managed OpenSearch
                                      ├── object storage for immutable source snapshots
                                      └── managed secrets, logs, metrics and alarms
```

Production data stores must use private networking, least-privilege identities, encryption in transit and at rest, automated backups, restore testing, and environment-specific keys. CI/CD should use short-lived cloud federation rather than static AWS credentials.

### Required deployment sequence once infrastructure exists

1. Build, test, scan and publish immutable web/API/worker artifacts.
2. Plan Terraform against an isolated environment and review all security/network/database changes.
3. Apply infrastructure using protected CI credentials and remote locked state.
4. Run backward-compatible Alembic migrations as a controlled one-off task.
5. Deploy the API and worker, then verify readiness, logs, metrics and dependency connectivity.
6. Deploy versioned static frontend assets and switch traffic only after API compatibility checks.
7. Run authentication, tenant-isolation, citation, eligibility and rollback smoke tests.
8. Promote gradually and monitor error rate, latency, auth failures and provider spend.

Rollback must use the previous immutable application artifact. Database changes require an explicitly reviewed roll-forward or downgrade strategy; never improvise destructive schema rollback in production.

## Production launch gates

Before accepting real customer data, complete at minimum:

- email verification, password reset and account recovery;
- login throttling, abuse detection and security-event audit logging;
- MFA/OIDC and fresh authentication for privileged roles;
- PostgreSQL tenant-isolation integration tests;
- reviewed retention, deletion, privacy and encryption-key rotation policies;
- PostgreSQL-backed chat/profile version history and append-only audit events;
- reviewed source ingestion, immutable snapshots and publication workflow;
- production model/provider adapters with citation validation and budget controls;
- backup restoration, disaster recovery and incident-response exercises;
- accessibility, dependency, container, IaC and penetration testing; and
- payment/compliance architecture before enabling paid checkout.

See [the implementation backlog](docs/planning/BACKLOG.md), [architecture overview](docs/architecture/OVERVIEW.md), [threat model](docs/security/THREAT_MODEL.md) and [ADR-0006](docs/architecture/adr/0006-first-party-identity-and-encrypted-profiles.md).

## Troubleshooting

### Registration returns `503 identity_unavailable`

The API did not load both `MSME_SAARTHI_DATABASE_URL` and `MSME_SAARTHI_DATA_ENCRYPTION_KEY`. Confirm that `apps/api/.env` exists and restart the API.

### PostgreSQL connection fails

Start Docker Desktop, run `make infra-up`, wait for the PostgreSQL health check, verify the URL in `apps/api/.env`, then run the migration.

### Encrypted fields cannot be read

The configured key or key version differs from the one used to write the data. Restore the correct key from the approved secret store; do not generate a replacement for an existing database.

### Port 5173 or 8000 is already in use

Stop the stale development process or use the already running instance. The smoke script expects the default ports unless `WEB_URL` and `API_URL` are overridden.

### OpenSearch exits during local startup

Increase Docker Desktop memory and inspect `docker compose -f infrastructure/compose.yaml logs opensearch`. OpenSearch is not required for the current curated frontend preview or mocked chat slice.

## Contributing and security

Read [AGENTS.md](AGENTS.md) and the relevant document under `docs/` before substantial changes. Use synthetic test data only, never commit credentials, and report suspected vulnerabilities according to [SECURITY.md](SECURITY.md).
