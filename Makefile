.PHONY: help dev install
.DEFAULT_GOAL := help



# VARIABLES
# Colors for output
RED = \033[31m
GREEN = \033[32m
YELLOW = \033[33m
BLUE = \033[34m
RESET = \033[0m

BACKEND_ENV_FILE_SYNCED_PATH = ../backend/env_config/synced/.env.$(ENVIRONMENT)
FROTNEND_ENV_FILE_SYNCED_PATH = ../frontend/env_config/synced/.env.$(ENVIRONMENT)
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
	BACKEND_ENV_FILE=$(BACKEND_ENV_FILE_SYNCED_PATH)  docker compose -f deployment/docker-compose.yml -f deployment/docker-compose.dev.yml -p $(PROJECT_NAME) down -v
	pkill -f "uvicorn" || true
	pkill -f "vite" || true
	pkill -f "npm run dev" || true

dev-restart-docker-compose: ## Restart docker compose for dev
	@echo "Restarting docker compose"
	BACKEND_ENV_FILE=$(BACKEND_ENV_FILE_SYNCED_PATH)  docker compose -f deployment/docker-compose.yml -f deployment/docker-compose.dev.yml -p $(PROJECT_NAME) down -v
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
deploy-start: ## Deploy to production (no infra changes)
	@echo "$(GREEN)Starting production deployment (app only)...$(RESET)"
	$(MAKE) check-enviroment-variables
	$(MAKE) check-backend-version
	$(MAKE) -C infra sync_all
	$(MAKE) -C frontend build
	$(MAKE) -C backend push_docker
	$(MAKE) -C infra ansible-start
	@echo "$(GREEN)✅ Deployment complete - version $(BACKEND_VERSION)$(RESET)"
deploy-start-with-infra: ## Deploy to production (with infra changes)
	@echo "$(GREEN)Starting production deployment (infra + app)...$(RESET)"
	$(MAKE) check-enviroment-variables
	$(MAKE) check-backend-version
	$(MAKE) -C infra terraform-apply
	$(MAKE) -C infra sync_all
	$(MAKE) -C frontend build
	$(MAKE) -C backend push_docker
	$(MAKE) -C infra ansible-start
	@echo "$(GREEN)✅ Deployment complete with infra - version $(BACKEND_VERSION)$(RESET)"

deploy-stop: ## Stop development environment
	@echo "$(YELLOW)Stopping development environment...$(RESET)"
	$(MAKE) check-enviroment-variables
	$(MAKE) -C infra terraform-stop ENVIRONMENT="$(ENVIRONMENT)"
	$(MAKE) delete_ci_artifacts

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
