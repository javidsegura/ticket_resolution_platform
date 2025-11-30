.PHONY: help dev dev-debug install db-models lint lint-check pytest-run  test-docker-compose-start

SHELL := /bin/bash


# Colors for output
RED = \033[31m
GREEN = \033[32m
YELLOW = \033[33m
BLUE = \033[34m
RESET = \033[0m

.DEFAULT_GOAL := help

# Variables
VENV = ../.venv
VENV_ACTIVATE = source $(VENV)/bin/activate
APP_PATH = src.ai_ticket_platform.main:app
PORT = 8000
BACKEND_ENV_FILE_SYNCED_PATH= ../backend/env_config/synced/.env.$(ENVIRONMENT)
PROJECT_NAME = url-shortener



help: ## Show this help message
	@echo "$(BLUE)Available commands:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-15s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)


# 0) Set-up
install: ## Install backend dependencies
	uv venv $(VENV) --python 3.11
	uv pip install -e ".[dev,tests]"
	$(VENV_ACTIVATE) && alembic init migrations || echo "alembic init already started"
install-full: ## Install backend dependices for client + dev usage
	uv venv $(VENV) --python 3.11
	uv pip install -e ".[dev,tests]"
	$(VENV_ACTIVATE) && alembic init migrations || echo "alembic init already started"
	@if command -v brew >/dev/null 2>&1; then \
		brew install k6 || echo "Note: k6 installation skipped (may already be installed)"; \
	else \
		echo "Note: Homebrew not found, skipping k6 installation. Install manually with: brew install k6"; \
	fi

# 1) Boot-up 
dev: ## Start backend development server. Note, the recommended usage is with make dev-start from parent Makefile. Flaky behavior warned.
	$(VENV_ACTIVATE) &&  ENVIRONMENT=dev uvicorn $(APP_PATH) --reload --host 0.0.0.0 --port $(PORT)


# 2) CI
lint: ## Run linting and formatting (local dev)
	@echo "$(YELLOW)Running linting and formatting...$(RESET)"
	@echo "$(BLUE)Formatting code with ruff...$(RESET)"
	$(VENV_ACTIVATE) && ruff format src/
	@echo "$(BLUE)Running ruff checks and fixes...$(RESET)"
	$(VENV_ACTIVATE) && ruff check --fix src/
	@echo "$(BLUE)Running security checks with bandit...$(RESET)"
	$(VENV_ACTIVATE) && bandit -r src/

lint-check: ## Run linting checks (CI)
	@echo "$(YELLOW)Running CI linting checks...$(RESET)"
	@echo "$(BLUE)Checking code formatting with ruff...$(RESET)"
	@$(VENV_ACTIVATE) && ruff format --check src/
	@echo "$(BLUE)Running ruff checks...$(RESET)"
	@$(VENV_ACTIVATE) && ruff check  src/
	@echo "$(BLUE)Running ruff checks with diff...$(RESET)"
	@$(VENV_ACTIVATE) && ruff check  --diff --fix src/ 
	@echo "$(BLUE)Running security checks with bandit...$(RESET)"
	@$(VENV_ACTIVATE) && bandit -r src/ 
format: ## Formats
	@echo "$(YELLOW)Running CI formatting$(RESET)"
	@echo "$(BLUE)Checking code formatting with ruff...$(RESET)"
	@$(VENV_ACTIVATE) && ruff format --check src/

format-fix: ## Format code (for pre-commit)
	@echo "$(YELLOW)Formatting code with ruff...$(RESET)"
	$(VENV_ACTIVATE) && ruff format src/

# 3) CD
## DB
db-create-migration-files:
	@if [ -z "$(MESSAGE)" ]; then echo "❌ Please provide MESSAGE='your description'"; exit 1; fi

	ENVIRONMENT=dev $(VENV_ACTIVATE) && ENVIRONMENT=dev alembic revision --autogenerate -m "$(MESSAGE)"
# ENVIRONMENT=dev.local && $(VENV_ACTIVATE) && alembic revision --autogenerate -m "$(MESSAGE)"

db-test-migration: ## Dev
	$(MAKE) db-create-migration-files
	$(VENV_ACTIVATE) && alembic upgrade head


db-safe-migration: ## Prod
	@echo "🔍 Pre-deployment checks..."
	$(VENV_ACTIVATE) && alembic check || (echo "❌ Validation failed!"; exit 1)
	@echo "Current status:"
	$(VENV_ACTIVATE) && alembic current
	@echo "Pending migrations:"
	$(VENV_ACTIVATE) && alembic history --verbose | head -10
	@echo ""
	$(VENV_ACTIVATE) && alembic upgrade head
	@echo "✅ Production deployment complete!"


db-downgrade-prior-version:
	$(VENV_ACTIVATE) && alembic downgrade -1

db-downgrade-specific-version:
	$(VENV_ACTIVATE) && alembic downgrade $(MIGRATION_ID)

# 4) Docker
push_docker:
	$(MAKE) check_enviroment_variables
	docker login
	docker buildx build -t javidsegura/ai_ticket_platform:$(ENVIRONMENT) -t javidsegura/ai_ticket_platform:latest --platform linux/amd64,linux/arm64 --push -f ./Dockerfile ./

# 5) Tests
# 5.1 ) Tests set-up
# 5) Tests set-up
test-start: ## Stats docker compose for integration tests of endpoints
	BACKEND_ENV_FILE=$(BACKEND_ENV_FILE_SYNCED_PATH) docker compose -f ../deployment/docker-compose.yml -f ../deployment/docker-compose.test.yml -p $(PROJECT_NAME) up --build -d

test-stop: ## Stops docker compose for integration tests of endpoints
	BACKEND_ENV_FILE=$(BACKEND_ENV_FILE_SYNCED_PATH) docker compose -f ../deployment/docker-compose.yml -f ../deployment/docker-compose.test.yml -p $(PROJECT_NAME) down -v
# 5.2) Tests run
pytest-run:
	$(VENV_ACTIVATE) && pytest -s -vv \
					test/smoke/endpoints

unit-test: ## Run all unit tests with coverage
	@echo "$(YELLOW)Running all tests...$(RESET)"
	$(VENV_ACTIVATE) && python3 -m pytest test/unit/ -v --cov=src/url_shortener --cov-report=term --cov-report=xml --cov-fail-under=70

integration-test: ## Runn all integration tests
	$(VENV_ACTIVATE) && python3 -m pytest -s -vv test/integration/

regression-test: ## Run all regression tests
	@echo "$(YELLOW)Running regression tests...$(RESET)"
	$(VENV_ACTIVATE) && python3 -m pytest test/regression/ -v

smoke-test: ## Run all smoke endpoint tests
	@echo "$(YELLOW)Running smoke endpoint tests...$(RESET)"
	$(VENV_ACTIVATE) && python3 -m pytest test/smoke/ -v

load-tests: ## Run load tests with k6
	@echo "$(YELLOW)Running load tests...$(RESET)"
	k6 run --out json=test/load/k6-results.json test/load/load_test.js

test-integration: ## Run all integration tests (CSV → Draft → Approval → Publish)
	@echo "$(YELLOW)Running integration tests...$(RESET)"
	$(VENV_ACTIVATE) && pytest -s -vv --cov=ai_ticket_platform --cov-report=term-missing tests/integration/

test-integration-docker: ## Run integration tests with Docker (full E2E with MySQL, Redis, Firebase)
	@echo "$(YELLOW)Starting Docker-based integration test suite...$(RESET)"
	ENVIRONMENT=dev $(MAKE) test-docker-compose-start
	@echo "$(BLUE)Running tests against Docker services...$(RESET)"
	$(VENV_ACTIVATE) && ENVIRONMENT=dev pytest -s -vv --cov=ai_ticket_platform --cov-report=term-missing tests/integration/ || TEST_FAILED=1
	@echo "$(YELLOW)Cleaning up Docker containers...$(RESET)"
	ENVIRONMENT=dev $(MAKE) test-docker-compose-stop
	@if [ "$$TEST_FAILED" = "1" ]; then echo "$(RED)Tests failed$(RESET)"; exit 1; fi
	@echo "$(GREEN)All integration tests passed!$(RESET)"

test-integration-csv: ## Run CSV→Draft pipeline tests
	@echo "$(YELLOW)Running CSV→Draft pipeline tests...$(RESET)"
	$(VENV_ACTIVATE) && pytest -s -vv tests/integration/test_csv_draft_pipeline.py

test-integration-approval: ## Run Slack approval flow tests
	@echo "$(YELLOW)Running Slack approval flow tests...$(RESET)"
	$(VENV_ACTIVATE) && pytest -s -vv tests/integration/test_approval_flow.py

test-integration-publish: ## Run publish→microsite flow tests
	@echo "$(YELLOW)Running publish flow tests...$(RESET)"
	$(VENV_ACTIVATE) && pytest -s -vv tests/integration/test_publish_flow.py

test-integration-widget: ## Run JS widget rendering tests
	@echo "$(YELLOW)Running widget tests...$(RESET)"
	$(VENV_ACTIVATE) && pytest -s -vv tests/integration/test_js_widget.py

# 6) Miscellaneous
check_enviroment_variables:
	@if [ -z "$$ENVIRONMENT" ]; then \
		echo "Error: ENVIRONMENT must be defined"; \
		exit 1; \
	fi
	echo "Environment is: $(ENVIRONMENT)"