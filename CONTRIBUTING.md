# Contributing to MSME Saarthi AI

Thank you for helping build safer, clearer access to Indian MSME support. Contributions should be small, reviewable, evidence-aware, and consistent with the rule that an LLM never decides eligibility.

## Start here

1. Read [AGENTS.md](AGENTS.md) and the document under `docs/` that governs the area you will change.
2. Follow the [local quickstart](docs/QUICKSTART.md) for a working development environment.
3. Inspect the existing implementation and tests before proposing a new abstraction or dependency.
4. State one clear objective, the files you intend to own, dependencies, acceptance criteria, and verification commands.

Use synthetic users, businesses, profiles, rules, payments, and conversations in tests. Do not copy personal data into the repository. Scheme content intended for users must come from an approved official source and retain citation metadata; do not invent benefits, criteria, deadlines, or URLs.

## Development workflow

- Create a focused branch and make the smallest coherent change that satisfies the objective.
- Keep business rules outside FastAPI routes and React components.
- Preserve module boundaries: the web app calls APIs, services authorize use cases, repositories own persistence, and the eligibility package remains pure and deterministic.
- Treat web pages, documents, prompts, model output, and retrieved chunks as untrusted input.
- Explain every new dependency and prefer an existing project abstraction where one exists.
- Add or update tests and authoritative documentation in the same change.
- Use Alembic for schema changes. Never edit an applied migration or rely on ORM table creation in a deployed environment.
- Never commit `.env` files, API keys, session tokens, database files, source snapshots containing sensitive data, or production credentials.

## Code expectations

Python code is typed, uses Pydantic v2 at external boundaries, async SQLAlchemy for persistence, Ruff for linting, and mypy for type checks. Service boundaries enforce tenant authorization.

Frontend code is feature-oriented TypeScript without undocumented `any`. API calls stay outside UI components; server state uses TanStack Query and forms use React Hook Form with Zod where applicable. New user-facing behavior includes loading, empty, error, responsive, keyboard, and accessible-name states.

The ingestion worker accepts only reviewed allowlist entries, enforces network and content limits, and never converts retrieved instructions into executable actions or eligibility rules.

## Verification

Run the narrowest affected checks first. Common targets are:

```bash
make api-lint api-typecheck api-test
make api-test-integration
make web-lint web-typecheck web-test web-build
make worker-lint worker-typecheck worker-test
make retrieval-test retrieval-test-integration
make eligibility-lint eligibility-typecheck eligibility-test
```

Pass `PYTHON="$PWD/.venv/bin/python"` when your `make` environment does not already select the repository virtual environment. Integration checks may require `make infra-up`. A test may be reported as passing only when it was executed in the current environment.

## Pull request checklist

- The description names the objective, owned files, design choice, and user-visible result.
- Relevant tests cover success, validation, authorization, failure, and tenant isolation where applicable.
- Material scheme claims have resolvable approved-source citations.
- Eligibility decisions come only from the deterministic engine.
- No secrets, real personal data, or production credentials are present.
- Migrations, configuration examples, API contracts, and relevant docs are updated.
- Commands and exact results are reported, along with skipped checks and remaining risks.
- The change is normally reviewable as one commit; unrelated cleanup is excluded.

Report suspected vulnerabilities privately using [SECURITY.md](SECURITY.md), not a public issue.
