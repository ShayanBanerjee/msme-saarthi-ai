# Local Quickstart

This is the shortest path to the full local experience: persistent PostgreSQL accounts and conversations, OpenSearch-backed scheme retrieval, the ingestion worker, and the React application.

## 1. Install and configure

Prerequisites: Python 3.12+, Node.js 22+, npm, OpenSSL, and Docker Engine, Docker Desktop, or a WSL-compatible Docker runtime with at least 2 GB available for OpenSearch. On Linux, the current user must have permission to access the Docker socket.

```bash
python3.12 -m venv .venv
source .venv/bin/activate

make api-install PYTHON="$PWD/.venv/bin/python"
make worker-install PYTHON="$PWD/.venv/bin/python"
make eligibility-install PYTHON="$PWD/.venv/bin/python"
make web-install

./scripts/bootstrap-local.sh postgres
make infra-up
make api-migrate PYTHON="$PWD/.venv/bin/python"
```

The bootstrap script creates a permission-restricted `apps/api/.env`, selects PostgreSQL and OpenSearch, and generates a unique local encryption key. It refuses to replace an existing file. Keep that key stable or existing encrypted values will become unreadable.

## 2. Load the reviewed local evidence index

```bash
make ingestion-validate PYTHON="$PWD/.venv/bin/python"

cd apps/worker
../../.venv/bin/python -m worker.cli sources/official-central.json \
  --opensearch-url http://127.0.0.1:9200
cd ../..
```

The manifest contains reviewed official government pages/PDFs and 15 open-access business books. Government material supports scheme discovery; books support general business techniques only. Retrieved pages remain untrusted evidence and are never eligibility rules. See the [source register](../apps/worker/sources/README.md).

## 3. Run the application

Start the complete local stack from one terminal:

```bash
make start
```

This Linux-style service command starts the Compose dependencies, applies Alembic migrations, launches the API and web server in the background, waits for both health endpoints, and writes process IDs and logs beneath the ignored `.local/` directory. It works with Docker Engine on Linux and WSL as well as Docker Desktop on macOS; it never calls `open`, `osascript`, Homebrew, or another platform-specific launcher.

Manage the running stack with:

```bash
make status
make logs
make logs-follow
make restart
make stop
```

`make` automatically selects `.venv/bin/python` when it exists. Set `PYTHON=/absolute/path/to/python` only when intentionally using a different environment.

The individual foreground commands remain available for debugging:

```bash
make api-run
make web-run
```

Open <http://127.0.0.1:5173>, register a synthetic local account, and open **AI Saarthi** to ask a scheme question. The API documentation is at <http://127.0.0.1:8000/docs>.

The answer provider is deterministic by default. To use OpenAI, add the following only to `apps/api/.env`, set the key locally, and restart the API:

```dotenv
MSME_SAARTHI_LLM_PROVIDER=openai
MSME_SAARTHI_OPENAI_API_KEY=<never-commit-this-value>
MSME_SAARTHI_OPENAI_MODEL=gpt-5.4-mini
MSME_SAARTHI_OPENAI_IMAGE_MODEL=gpt-image-2
```

## 4. Check and stop

With both applications running:

```bash
make local-check
```

Stop all application processes and data services without deleting their persistent named volumes:

```bash
make stop
```

For SQLite without Docker, advanced configuration, test commands, troubleshooting, and production constraints, see the root [README](../README.md).
