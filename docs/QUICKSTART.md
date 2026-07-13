# Local Quickstart

This is the shortest path to the full local experience: persistent PostgreSQL accounts and conversations, OpenSearch-backed scheme retrieval, the ingestion worker, and the React application.

## 1. Install and configure

Prerequisites: Python 3.12+, Node.js 22+, npm, OpenSSL, and Docker Desktop with at least 2 GB available for OpenSearch.

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

The manifest contains reviewed official-source entries. Retrieved pages remain untrusted evidence and are not eligibility rules.

## 3. Run the application

In terminal one:

```bash
source .venv/bin/activate
make api-run PYTHON="$PWD/.venv/bin/python"
```

In terminal two:

```bash
make web-run
```

Open <http://127.0.0.1:5173>, register a synthetic local account, and open **AI Saarthi** to ask a scheme question. The API documentation is at <http://127.0.0.1:8000/docs>.

The answer provider is deterministic by default. To use OpenAI, add the following only to `apps/api/.env`, set the key locally, and restart the API:

```dotenv
MSME_SAARTHI_LLM_PROVIDER=openai
MSME_SAARTHI_OPENAI_API_KEY=<never-commit-this-value>
MSME_SAARTHI_OPENAI_MODEL=gpt-5.4-mini
```

## 4. Check and stop

With both applications running:

```bash
make local-check
```

Stop the API and web processes with `Ctrl+C`, then stop the data services without deleting their persistent named volumes:

```bash
make infra-down
```

For SQLite without Docker, advanced configuration, test commands, troubleshooting, and production constraints, see the root [README](../README.md).
