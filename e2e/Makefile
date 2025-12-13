.PHONY: help install test test-headed test-ui test-debug report clean

# Colors for output
RED = \033[31m
GREEN = \033[32m
YELLOW = \033[33m
BLUE = \033[34m
RESET = \033[0m

.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "$(BLUE)E2E Testing Commands:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install E2E test dependencies
	@echo "$(YELLOW)Installing E2E dependencies...$(RESET)"
	npm install
	@echo "$(YELLOW)Installing Playwright browsers...$(RESET)"
	npx playwright install chromium --with-deps
	@echo "$(GREEN)✓ E2E dependencies installed$(RESET)"

test: ## Run all E2E tests
	@echo "$(YELLOW)Running E2E tests...$(RESET)"
	npm test

test-headed: ## Run E2E tests with visible browser
	@echo "$(YELLOW)Running E2E tests in headed mode...$(RESET)"
	npm run test:headed

test-ui: ## Run E2E tests in interactive UI mode
	@echo "$(YELLOW)Opening Playwright UI...$(RESET)"
	npm run test:ui

test-debug: ## Run E2E tests in debug mode
	@echo "$(YELLOW)Running E2E tests in debug mode...$(RESET)"
	npm run test:debug

report: ## Show Playwright test report
	@echo "$(YELLOW)Opening test report...$(RESET)"
	npm run report

codegen: ## Generate test code using Playwright codegen
	@echo "$(YELLOW)Starting Playwright codegen...$(RESET)"
	npm run codegen

clean: ## Clean test artifacts
	@echo "$(YELLOW)Cleaning test artifacts...$(RESET)"
	rm -rf test-results/
	rm -rf playwright-report/
	rm -rf playwright/.cache/
	@echo "$(GREEN)✓ Test artifacts cleaned$(RESET)"

verify-services: ## Verify backend and frontend are running
	@echo "$(YELLOW)Verifying services...$(RESET)"
	@echo "Checking backend..."
	@curl -f http://localhost:8000/api/health/ping > /dev/null 2>&1 || (echo "$(RED)✗ Backend not running on localhost:8000$(RESET)" && exit 1)
	@echo "$(GREEN)✓ Backend is running$(RESET)"
	@echo "Checking frontend..."
	@curl -f http://localhost:3000 > /dev/null 2>&1 || (echo "$(RED)✗ Frontend not running on localhost:3000$(RESET)" && exit 1)
	@echo "$(GREEN)✓ Frontend is running$(RESET)"
	@echo "$(GREEN)✓ All services ready for E2E tests$(RESET)"
