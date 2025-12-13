.PHONY: help dev install e2e-install e2e-test e2e-test-docker e2e-test-full e2e-clean
.DEFAULT_GOAL := help



# VARIABLES
# Colors for output
RED = \033[31m
GREEN = \033[32m
YELLOW = \033[33m
BLUE = \033[34m
RESET = \033[0m

BACKEND_ENV_FILE_SYNCED_PATH = backend/env_config/synced/.env.$(ENVIRONMENT)
FROTNEND_ENV_FILE_SYNCED_PATH = frontend/env_config/synced/.env.$(ENVIRONMENT)
TERRAFORM_PATH = ./infra/terraform/environment/$(ENVIRONMENT)
PROJECT_NAME = url-shortener



help: ## Show this help message
	@echo "$(BLUE)Available commands:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-15s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# 1) Installation
install: ## Install project-wide dependencies
	@echo "$(YELLOW)Installing all project dependencies...$(RESET)"
	$(MAKE) check-enviroment-variables
	$(MAKE) -C backend install
	$(MAKE) -C frontend install
	$(MAKE) -C infra install
	brew install jq

install-packages: ## Install only packages
	@echo "$(YELLOW)Installing all project dependencies...$(RESET)"
	$(MAKE) check-enviroment-variables
	$(MAKE) -C backend install
	$(MAKE) -C frontend install


install-ci-cd: ## Install dependencies for CI environment (no brew)
	@echo "$(YELLOW)Installing CI dependencies...$(RESET)"
	$(MAKE) check-enviroment-variables
	sudo apt-get update && sudo apt-get install -y jq ansible
	$(MAKE) -C backend install
	$(MAKE) -C frontend install
	$(MAKE) -C infra install-ci-cd

# 2) Dev environment
dev-start: ## Hot reload enabled for both backend and frontend
	$(MAKE) check-enviroment-variables
	BACKEND_ENV_FILE=$(BACKEND_ENV_FILE_SYNCED_PATH) docker compose -f deployment/docker-compose.yml -f deployment/docker-compose.dev.yml -p $(PROJECT_NAME) up --build

dev-stop: ## Stop development environment
	$(MAKE) check-enviroment-variables
	@echo "$(YELLOW)Stopping development environment...$(RESET)"
	docker compose -f deployment/docker-compose.yml -f deployment/docker-compose.dev.yml -p $(PROJECT_NAME) down -v || true
	pkill -f "uvicorn" || true
	pkill -f "vite" || true
	pkill -f "npm run dev" || true

dev-restart-docker-compose: ## Restart docker compose for dev
	@echo "Restarting docker compose"
	docker compose -f deployment/docker-compose.yml -f deployment/docker-compose.dev.yml -p $(PROJECT_NAME) down -v || true
	pkill -f "uvicorn" || true
	pkill -f "vite" || true
	pkill -f "npm run dev" || true
	docker volume prune -f
	BACKEND_ENV_FILE=$(BACKEND_ENV_FILE_SYNCED_PATH) docker compose -f deployment/docker-compose.yml -f deployment/docker-compose.dev.yml -p $(PROJECT_NAME) up --build

dev-start-infra: ## Deploy terraform infra for development environmnet
	$(MAKE) -C infra terraform-apply
	$(MAKE) -C infra sync_envs

dev-destroy-infra: ## Destroy terraform infra for development environmnet
	$(MAKE) check-enviroment-variables
	@echo "$(YELLOW)Stopping development environment...$(RESET)"
	$(MAKE) -C infra terraform-stop

# 3) Deployment environment
deploy-start-artifacts: ## Deploy to production (process: build artifacts + ansible)
	@echo "$(GREEN)Starting production deployment (app only)...$(RESET)"
	$(MAKE) check-enviroment-variables
	$(MAKE) check-backend-version
	$(MAKE) -C infra sync_all
	$(MAKE) -C frontend build
	$(MAKE) -C backend push_docker
	$(MAKE) -C infra ansible-start
	@echo "$(GREEN)✅ Deployment complete - version $(BACKEND_VERSION)$(RESET)"
deploy-start-ansible: ## Deploy to production (process: ansible)
	@echo "$(GREEN)Starting production deployment (app only)...$(RESET)"
	$(MAKE) check-enviroment-variables
	$(MAKE) check-backend-version
	$(MAKE) -C infra ansible-start
	@echo "$(GREEN)✅ Deployment complete - version $(BACKEND_VERSION)$(RESET)"
deploy-start-infra: ## Deploy to production (process: infra + build artifacts + ansible)
	@echo "$(GREEN)Starting production deployment (infra + app)...$(RESET)"
	$(MAKE) check-enviroment-variables
	$(MAKE) check-backend-version
	$(MAKE) -C infra terraform-apply
	$(MAKE) -C infra sync_all
	$(MAKE) -C frontend build
	$(MAKE) -C backend push_docker
	$(MAKE) -C infra ansible-start
	@echo "$(GREEN)✅ Deployment complete with infra - version $(BACKEND_VERSION)$(RESET)"

deploy-stop-infra: ## Stop development environment
	@echo "$(YELLOW)Stopping development environment...$(RESET)"
	$(MAKE) check-enviroment-variables
	$(MAKE) -C infra terraform-stop ENVIRONMENT="$(ENVIRONMENT)"
	$(MAKE) delete_ci_artifacts

# 4) E2E Testing
e2e-install: ## Install E2E test dependencies
	@echo "$(YELLOW)Installing E2E dependencies...$(RESET)"
	$(MAKE) -C e2e install
	@echo "$(GREEN)✅ E2E dependencies installed$(RESET)"

e2e-test: ## Run E2E tests (requires services to be running)
	@echo "$(BLUE)Running E2E tests...$(RESET)"
	@echo "$(YELLOW)Verifying services are running...$(RESET)"
	@$(MAKE) -C e2e verify-services || (echo "$(RED)Services not running. Run 'make e2e-test-full' to start everything$(RESET)" && exit 1)
	@echo "$(GREEN)✓ Services verified$(RESET)"
	$(MAKE) -C e2e test
	@echo "$(GREEN)✅ E2E tests completed$(RESET)"

e2e-test-docker: ## Run E2E tests with Docker services (auto-start backend services)
	@echo "$(BLUE)Running E2E tests with Docker...$(RESET)"
	@echo "$(YELLOW)Starting Docker services...$(RESET)"
	ENVIRONMENT=test $(MAKE) -C backend test-start
	@echo "Waiting for services to stabilize..."
	@sleep 15
	@echo "$(GREEN)✓ Docker services started$(RESET)"
	@echo "$(YELLOW)NOTE: You still need to manually start frontend and backend servers$(RESET)"
	@echo "  Terminal 1: cd backend && source ../.venv/bin/activate && ENVIRONMENT=test make dev"
	@echo "  Terminal 2: cd frontend && npm run dev"
	@echo "  Terminal 3: make e2e-test"
	@echo ""
	@echo "Or use 'make e2e-test-full' to run everything automatically"

e2e-test-full: ## Run complete E2E test suite (start all services, run tests, cleanup)
	@echo "$(BLUE)=== Starting Full E2E Test Suite ===$(RESET)"
	@echo ""
	@echo "$(YELLOW)Step 1/5: Starting Docker services...$(RESET)"
	ENVIRONMENT=test $(MAKE) -C backend test-start
	@echo "Waiting for services to stabilize..."
	@sleep 20
	@echo "$(GREEN)✓ Docker services running$(RESET)"
	@echo ""
	@echo "$(YELLOW)Step 2/5: Starting backend server...$(RESET)"
	@cd backend && source ../.venv/bin/activate && export $$(cat env_config/synced/.env.test | xargs) && nohup uvicorn src.ai_ticket_platform.main:app --host 0.0.0.0 --port 8000 > ../e2e-backend.log 2>&1 & echo $$! > ../e2e-backend.pid
	@sleep 5
	@echo "$(GREEN)✓ Backend server started (PID: $$(cat e2e-backend.pid))$(RESET)"
	@echo ""
	@echo "$(YELLOW)Step 3/5: Starting frontend server...$(RESET)"
	@cd frontend/app && nohup npm run dev > ../../e2e-frontend.log 2>&1 & echo $$! > ../../e2e-frontend.pid
	@sleep 10
	@echo "$(GREEN)✓ Frontend server started (PID: $$(cat e2e-frontend.pid))$(RESET)"
	@echo ""
	@echo "$(YELLOW)Step 4/5: Verifying services...$(RESET)"
	@timeout 60 bash -c 'until curl -f http://localhost:8000/api/health/ping > /dev/null 2>&1; do sleep 2; echo "Waiting for backend..."; done' || (echo "$(RED)Backend failed to start$(RESET)" && $(MAKE) e2e-cleanup && exit 1)
	@timeout 60 bash -c 'until curl -f http://localhost:5173 > /dev/null 2>&1; do sleep 2; echo "Waiting for frontend..."; done' || (echo "$(RED)Frontend failed to start$(RESET)" && $(MAKE) e2e-cleanup && exit 1)
	@echo "$(GREEN)✓ All services ready$(RESET)"
	@echo ""
	@echo "$(YELLOW)Step 5/5: Running E2E tests...$(RESET)"
	@$(MAKE) -C e2e test || TEST_FAILED=1
	@echo ""
	@echo "$(YELLOW)Cleaning up...$(RESET)"
	@$(MAKE) e2e-cleanup
	@if [ "$$TEST_FAILED" = "1" ]; then \
		echo "$(RED)✗ E2E tests failed$(RESET)"; \
		echo "Check logs:"; \
		echo "  Backend: e2e-backend.log"; \
		echo "  Frontend: e2e-frontend.log"; \
		exit 1; \
	fi
	@echo ""
	@echo "$(GREEN)✅ E2E test suite completed successfully!$(RESET)"

e2e-cleanup: ## Stop all E2E test services
	@echo "$(YELLOW)Stopping E2E services...$(RESET)"
	@if [ -f e2e-backend.pid ]; then \
		kill $$(cat e2e-backend.pid) 2>/dev/null || true; \
		rm e2e-backend.pid; \
		echo "$(GREEN)✓ Backend server stopped$(RESET)"; \
	fi
	@if [ -f e2e-frontend.pid ]; then \
		kill $$(cat e2e-frontend.pid) 2>/dev/null || true; \
		rm e2e-frontend.pid; \
		echo "$(GREEN)✓ Frontend server stopped$(RESET)"; \
	fi
	@ENVIRONMENT=test $(MAKE) -C backend test-stop 2>/dev/null || true
	@echo "$(GREEN)✓ Docker services stopped$(RESET)"
	@pkill -f "uvicorn.*ai_ticket_platform" || true
	@pkill -f "vite.*3000" || true
	@echo "$(GREEN)✓ Cleanup complete$(RESET)"

e2e-clean: ## Clean E2E test artifacts
	@echo "$(YELLOW)Cleaning E2E artifacts...$(RESET)"
	$(MAKE) -C e2e clean
	@rm -f e2e-backend.log e2e-frontend.log
	@echo "$(GREEN)✓ E2E artifacts cleaned$(RESET)"

e2e-report: ## View E2E test report
	$(MAKE) -C e2e report

# 5) Uitls function
delete_ci_artifacts:
	rm -rf $(BACKEND_ENV_FILE_SYNCED_PATH)
	rm -rf $(FROTNEND_ENV_FILE_SYNCED_PATH)
	docker volume prune -f


check-enviroment-variables:
	@if [ -z "$$ENVIRONMENT" ]; then \
		echo "Error: ENVIRONMENT must be defined"; \
		exit 1; \
	fi
	echo "Environment is: $(ENVIRONMENT)"

check-backend-version:
	@if [ -z "$$BACKEND_VERSION" ]; then \
		echo "$(RED)Error: BACKEND_VERSION must be defined$(RESET)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Backend version: $(BACKEND_VERSION)$(RESET)"
