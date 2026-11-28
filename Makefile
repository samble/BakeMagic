# Common development tasks. Run `make` (or `make help`) to list them.

.DEFAULT_GOAL := help

UV ?= uv
NPM ?= npm
RUN := $(UV) run

.PHONY: help sync frontend-install setup dev dev-backend dev-frontend migrate db-reset seed-db \
	test test-backend test-frontend test-smoke lint

help: ## List the available commands
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "} {printf "  \033[36m%-17s\033[0m %s\n", $$1, $$2}'

# ---------- setup ----------

sync: ## Install the backend and dev tools into .venv with uv (from uv.lock)
	$(UV) sync

frontend-install: ## Install frontend dependencies
	cd frontend && $(NPM) install

setup: sync frontend-install ## sync + frontend-install

# ---------- run ----------

dev: ## Run the backend (:8000) and frontend (:5173) dev servers; Ctrl-C stops both
	@trap 'kill 0' INT TERM; \
	$(MAKE) --no-print-directory dev-backend & \
	$(MAKE) --no-print-directory dev-frontend & \
	wait

dev-backend: ## Run the API with auto-reload on :8000
	$(RUN) fastapi dev app/main.py --port 8000

dev-frontend: ## Run the Vite dev server on :5173 (proxies /api to :8000)
	cd frontend && $(NPM) run dev

# ---------- database ----------

migrate: ## Apply all pending migrations
	$(RUN) alembic upgrade head

db-reset: ## Drop ALL tables and data, then re-run migrations (asks first; YES=1 skips)
	$(RUN) python scripts/drop_tables.py $(if $(YES),--yes)
	$(MAKE) --no-print-directory migrate

seed-db: migrate ## Load the sample data in seed/ (after migrating); expects those ids to be free
	$(RUN) alembic -n seed upgrade head

# ---------- checks ----------

test: test-backend test-frontend test-smoke ## Run all tests

test-backend: ## Run the pytest suite (in-memory SQLite, no database needed)
	$(RUN) pytest

test-frontend: ## Lint and type-check the frontend
	cd frontend && $(NPM) run lint && $(NPM) exec -- tsc -b

test-smoke: ## Start the real API and built frontend on spare ports and check they respond
	NPM=$(NPM) scripts/smoke.sh

lint: ## Lint backend (ruff) and frontend (oxlint)
	$(RUN) ruff check .
	cd frontend && $(NPM) run lint
