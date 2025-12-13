# CI/CD Pipeline Summary

## Overview
Comprehensive automated testing pipeline for the AI Ticket Resolution Platform with **6 test stages** running on every push to any branch.

**Workflow File**: `.github/workflows/ci-backend.yml`
**Current Coverage**: 70% (474 unit tests, 46 integration tests, 7 E2E tests)
**Avg Runtime**: ~6-8 minutes

---

## Test Stages (Sequential Execution)

### 1. **Lint & Security** (~30s)
- **Tools**: Ruff (formatting/linting), Bandit (security scan)
- **Purpose**: Catch code style violations and security vulnerabilities before running tests
- **Runs On**: Python 3.11, no Docker
- **Artifacts**: `bandit-report.json` (security findings)

### 2. **Unit Tests** (~1-2 min)
- **Count**: 474 tests
- **Purpose**: Test individual functions in isolation with mocked dependencies
- **Runs On**: Python 3.11, no Docker (fast)
- **Coverage**: 70% overall, uploaded to Codecov
- **Artifacts**: `coverage.xml`, HTML coverage report

### 3. **Smoke Tests** (~30s)
- **Purpose**: Verify Docker services start successfully (MySQL, Redis, Firebase Emulator, ChromaDB)
- **Runs On**: Docker Compose (test profile)
- **Critical Check**: Ensures infrastructure is healthy before integration tests

### 4. **Integration Tests** (~2-3 min)
- **Count**: 46 passing, 2 skipped in CI
- **Purpose**: Test with real services (MySQL, Redis, ChromaDB)
- **Skipped Tests**: `test_csv_upload_docker.py` (requires real API keys for RQ workers)
- **Environment**: `ENVIRONMENT=test`, Docker services from smoke tests

### 5. **Regression Tests** (~1 min)
- **Purpose**: Prevent previously fixed bugs from reappearing
- **Scope**: Critical bug fixes from past sprints
- **Environment**: Same Docker services as integration tests

### 6. **Workflow & E2E Tests** (~3-4 min)
- **Workflow Tests**: Multi-step backend API flows (ticket creation → clustering → article generation)
- **E2E Tests**: Full-stack Playwright tests (Frontend → Backend → Database)
  - **Auth Flow**: Creates Firebase test user (`test@example.com`)
  - **Test Coverage**: CSV upload via Dashboard modal, login flow, health checks
  - **Current Status**: 4/7 passing (3 CSV upload tests timeout waiting for RQ background processing)

---

## Local Development

### Run Individual Test Stages
```bash
# Unit tests (fast, no Docker)
cd backend && pytest tests/unit -v

# Integration tests (requires Docker)
export ENVIRONMENT=test
cd backend && make test-start  # Start Docker services
pytest tests/integration -v
make test-stop  # Clean up

# E2E tests (requires backend + frontend servers)
export ENVIRONMENT=test
make e2e-test-full  # Starts all services, runs tests, cleans up
```

### Quick Commands
```bash
make install          # Install all dependencies
make dev-start        # Start dev environment (hot reload)
make e2e-test-docker  # Start Docker for E2E (manual server start needed)
```

---

## Key Configuration Files

| File | Purpose |
|------|---------|
| `.github/workflows/ci-backend.yml` | Main CI workflow definition |
| `backend/Makefile` | Test orchestration, Docker management |
| `deployment/docker-compose.test.yml` | Test environment services |
| `backend/env_config/synced/.env.test` | Test environment variables (generated in CI) |
| `e2e/playwright.config.ts` | E2E test configuration |

---

## Important Notes

### ⚠️ Known Issues
1. **CSV Upload E2E Tests**: Timeout waiting for background processing (RQ workers need real OpenAI/Gemini API keys)
2. **RQ Workers in CI**: Don't process jobs (fake API keys) - integration tests that require workers are skipped
3. **Firebase Emulator**: Runs on port 19099, test user auto-created before E2E tests

### 🔑 Required Environment Variables (CI)
- **Always Set**: `ENVIRONMENT=test`
- **Firebase**: `USING_FIREBASE_EMULATOR=true`, `FB_AUTH_EMULATOR_HOST=localhost:19099`
- **Database**: `MYSQL_HOST=localhost`, `MYSQL_PORT=3307`
- **Redis**: `REDIS_URL=redis://localhost:6379`
- **ChromaDB**: `CHROMA_HOST=localhost`, `CHROMA_PORT=8001`
- **Frontend**: `FRONTEND_URL=http://localhost:5173`

### 📊 Coverage Gaps (Priority Areas)
- **csv_orchestrator.py**: 0% (dead code, never called)
- **article_service.py**: 12% (core content generation)
- **tasks.py**: 16% (background job processing)
- **tickets.py router**: 50% (CSV upload endpoint)
- **intent_matcher.py**: 16% (clustering logic)

### 🚀 Performance Optimizations
- Unit tests run in parallel with pytest-xdist (2 workers)
- Docker services reused between integration/regression/workflow tests
- Aggressive caching: pip dependencies, npm packages, Playwright browsers
- E2E tests retry 3 times on failure (flaky network/timing issues)

---

## Workflow Triggers
- **Push**: Any branch, if paths match `backend/**`, `e2e/**`, or workflow file
- **Pull Request**: Any branch targeting any branch (same path filters)

---

## Next Steps to Improve Coverage
1. Add unit tests for `article_service.py` (12% → 70%+)
2. Add unit tests for `tasks.py` background job processing
3. Add unit tests for `tickets.py` CSV upload router (50% → 80%+)
4. Fix E2E CSV upload tests (add RQ worker with mock API or skip upload processing verification)
