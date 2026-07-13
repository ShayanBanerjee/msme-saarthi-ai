.PHONY: local-bootstrap api-install api-run api-migrate api-migration-check api-lint api-typecheck api-test api-test-integration web-install web-run web-lint web-typecheck web-test web-build worker-install worker-lint worker-typecheck worker-test ingestion-validate infra-up infra-down local-check retrieval-test retrieval-test-integration eligibility-install eligibility-lint eligibility-typecheck eligibility-test

PYTHON ?= python3
API_DIR := apps/api
ELIGIBILITY_DIR := packages/eligibility-engine
WEB_DIR := apps/web
WORKER_DIR := apps/worker

local-bootstrap:
	./scripts/bootstrap-local.sh sqlite

api-install:
	$(PYTHON) -m pip install -e "$(API_DIR)[dev]"

api-run:
	cd $(API_DIR) && $(PYTHON) -m uvicorn app.main:app

api-migrate:
	cd $(API_DIR) && $(PYTHON) -m alembic upgrade head

api-migration-check:
	cd $(API_DIR) && $(PYTHON) -m alembic check

api-lint:
	cd $(API_DIR) && $(PYTHON) -m ruff check app tests

api-typecheck:
	cd $(API_DIR) && $(PYTHON) -m mypy app tests

api-test:
	cd $(API_DIR) && $(PYTHON) -m pytest -m "not integration"

api-test-integration:
	cd $(API_DIR) && $(PYTHON) -m pytest -m integration

web-install:
	cd $(WEB_DIR) && npm ci

web-run:
	cd $(WEB_DIR) && npm run dev

web-lint:
	cd $(WEB_DIR) && npm run lint

web-typecheck:
	cd $(WEB_DIR) && npm run typecheck

web-test:
	cd $(WEB_DIR) && npm run test

web-build:
	cd $(WEB_DIR) && npm run build

worker-install:
	$(PYTHON) -m pip install -e "$(WORKER_DIR)[dev]"

worker-lint:
	cd $(WORKER_DIR) && $(PYTHON) -m ruff check worker tests

worker-typecheck:
	cd $(WORKER_DIR) && $(PYTHON) -m mypy worker tests

worker-test:
	cd $(WORKER_DIR) && $(PYTHON) -m pytest

ingestion-validate:
	cd $(WORKER_DIR) && $(PYTHON) -m worker.cli sources/official-central.json --validate-only

infra-up:
	docker compose -f infrastructure/compose.yaml up -d

infra-down:
	docker compose -f infrastructure/compose.yaml down

local-check:
	./scripts/check-local.sh

retrieval-test:
	cd $(API_DIR) && $(PYTHON) -m pytest tests/retrieval -m "not integration"

retrieval-test-integration:
	cd $(API_DIR) && $(PYTHON) -m pytest tests/retrieval -m integration

eligibility-install:
	$(PYTHON) -m pip install -e "$(ELIGIBILITY_DIR)[dev]"

eligibility-lint:
	cd $(ELIGIBILITY_DIR) && $(PYTHON) -m ruff check eligibility_engine tests

eligibility-typecheck:
	cd $(ELIGIBILITY_DIR) && $(PYTHON) -m mypy eligibility_engine tests

eligibility-test:
	cd $(ELIGIBILITY_DIR) && $(PYTHON) -m pytest
