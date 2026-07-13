# Repository scripts

- `bootstrap-local.sh [sqlite|postgres]` creates a permission-restricted `apps/api/.env` with a newly generated encryption key. It never overwrites an existing environment.
- `check-local.sh` verifies the live API health endpoints and every frontend route.

Scripts are non-interactive, fail fast and accept `WEB_URL` and `API_URL` overrides.
