# Repository scripts

- `bootstrap-local.sh [sqlite|postgres]` creates a permission-restricted `apps/api/.env` with a newly generated encryption key. SQLite uses the built-in curated retriever; PostgreSQL mode selects the local OpenSearch index. The script never overwrites an existing environment.
- `check-local.sh` verifies the live API health endpoints and every frontend route.

Scripts are non-interactive, fail fast and accept `WEB_URL` and `API_URL` overrides.

For the shortest end-to-end setup, including source ingestion, see [the local quickstart](../docs/QUICKSTART.md).
