# Testing Guide - AI Ticket Resolution Platform

> **Last Updated**: 2025-12-12
> **Current Coverage**: 70% ✅ (Target: 70-80%)
> **Total Tests**: 522 tests (all passing)
> **Test Directory**: `backend/tests/`

---

## Quick Start

### Run All Tests
```bash
cd backend
source ../.venv/bin/activate
export ENVIRONMENT=test

# Run unit tests only
python3 -m pytest tests/unit/ -v

# Run unit tests with coverage
python3 -m pytest tests/unit/ --cov=src/ai_ticket_platform --cov-report=term --cov-report=html

# Run integration tests (requires Docker)
make test-start  # Start Docker services
sleep 15         # Wait for services to stabilize
make integration-test
make test-stop   # Stop Docker services

# Run all test suites
make smoke-test       # Smoke tests
make integration-test # Integration tests
make workflow-test    # Multi-step workflow tests
make regression-test  # Regression tests
```

---

## Current Test Status

### Coverage Breakdown
- **Overall Coverage**: 70% (3,053 statements, 2,127 covered, 926 missed) ✅
- **Target**: 70-80% - **ACHIEVED**
- **All Tests Passing**: ✅ 522 tests

### Test Distribution
```
Total: 522 tests (Backend only)
├── Unit Tests: 474 tests (core business logic, mocked dependencies)
├── Smoke Tests: Verify Docker services (MySQL, Redis, ChromaDB, Firebase)
├── Integration Tests: 48 tests (endpoints + infrastructure with real dependencies)
│   └── Note: 2 tests (CSV upload flows) skipped in CI (require RQ workers + real API keys)
├── Workflow Tests: 9 tests (multi-step backend workflows + concurrent operations)
│   ├── Sequential workflows (health → CSV, dependencies → CSV, CSV → PDF, CSV → Slack)
│   └── Concurrent workflows (parallel health checks, concurrent uploads, mixed endpoints)
└── Regression Tests: Prevent previously fixed bugs from returning
```

**Important Distinction**:
- **Workflow Tests** (what we have): Multi-step backend API testing (multiple endpoints in sequence)
- **True E2E Tests** (not yet implemented): Frontend → Backend → Database → Frontend
  - Would require: Playwright/Cypress testing the React app
  - Would test: User clicks button → Form submission → API call → Database → UI update
  - Should be in: Separate E2E test suite that includes both frontend and backend

**Notes**:
- Manual testing scripts are located in `backend/scripts/` and are not included in the automated test count.
- Integration tests requiring RQ workers and real API keys are skipped in CI environments (run locally or in staging).
- Workflow tests validate multi-step backend processes and concurrent API operations.

### Coverage by Module Category

| Module Category | Coverage | Status |
|-----------------|----------|--------|
| **Main Application** | **100%** | ✅ Excellent |
| Core Services (Logger, Settings) | 97-100% | ✅ Excellent |
| Core Services (Cache, Redis, Clients) | 85-100% | ✅ Excellent |
| Database CRUD | 79-100% | ✅ Good |
| Routers (Health, External, Intents) | 80-100% | ✅ Good |
| Routers (Articles, Slack) | 56-58% | ⚠️ Moderate |
| **Routers (Tickets)** | **50%** | ⚠️ Needs Work |
| Schemas | 77-100% | ✅ Good |
| CSV Parser & Uploader | 90-100% | ✅ Excellent |
| Storage Factory | 90% | ✅ Excellent |
| Labeling Services | 85-100% | ✅ Excellent |
| **Services (Content Gen, Queue)** | **12-35%** | ⚠️ Low Priority |
| **Storage (AWS, Azure)** | **28-30%** | ⚠️ Low Priority |
| **Clustering Services** | **16-24%** | ⚠️ Low Priority |
| **Deployment Settings** | **21%** | ⚠️ Not Tested |

---

## Test Organization

### Directory Structure
```
backend/
├── scripts/                 # Manual testing scripts
│   └── manual_caching_test.py    # Manual cache performance test
└── tests/
    ├── conftest.py              # Shared fixtures
    ├── fixtures/                # Test data files
    │   ├── README.md
    │   └── sample_markdown_outputs/
    ├── unit/                    # Unit tests (474 tests) ✅
    │   ├── core/               # Core utilities (Redis, settings, logger, clients)
    │   ├── database/           # CRUD operations
    │   ├── dependencies/       # FastAPI dependencies
    │   ├── routers/            # API endpoint logic (NEW: tickets, articles, slack)
    │   ├── schemas/            # Pydantic validation
    │   ├── services/           # Business logic
    │   ├── labeling/           # Document labeling
    │   ├── test_main.py        # Main app tests (NEW: 6 tests)
    │   └── csv_uploader/       # CSV processing
    ├── integration/             # Integration tests (48 tests) ✅
    │   ├── test_*_endpoints.py      # Real API testing
    │   ├── test_*_docker.py         # Infrastructure testing
    │   ├── test_e2e_workflow.py     # E2E workflow tests
    │   └── conftest.py
    ├── regression/              # Regression tests (included in unit)
    │   ├── test_api_regressions.py
    │   ├── test_csv_upload_regressions.py
    │   └── test_database_regressions.py
    └── smoke/                   # Smoke tests (included in integration)
        └── test_docker_services.py
```

---

## Running Tests

### Prerequisites
```bash
# Install dependencies
cd backend
pip install -e ".[dev,tests]"

# Set environment
export ENVIRONMENT=test
```

### Unit Tests
```bash
# Run all unit tests
python3 -m pytest tests/unit/ -v

# Run specific test file
python3 -m pytest tests/unit/routers/test_articles_router.py -v

# Run with coverage
python3 -m pytest tests/unit/ \
  --cov=src/ai_ticket_platform \
  --cov-report=term-missing \
  --cov-report=html

# View HTML coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Integration Tests (Requires Docker)
```bash
# Start Docker services
export ENVIRONMENT=test
make test-start
sleep 15  # Wait for MySQL and Redis to be ready

# Run integration tests
make test-integration

# Stop Docker services
make test-stop
```

### Smoke Tests
```bash
# Verify Docker services are accessible
export ENVIRONMENT=test
make test-start
make test-smoke
make test-stop
```

### Regression Tests
```bash
export ENVIRONMENT=test
make test-regression
```

---

## Test Types Explained

### Unit Tests
**Purpose**: Test individual functions and classes in isolation
**Location**: `tests/unit/`
**Coverage Target**: 70%+
**Dependencies**: None (mocked)

**Example**: Test that `create_category()` validates input correctly
```python
async def test_create_category_invalid_level():
    """Test category creation with invalid level."""
    mock_db = MagicMock(spec=AsyncSession)

    with pytest.raises(ValueError, match="Category level must be between 1 and 3"):
        await create_category(db=mock_db, name="Test", level=4)
```

### Integration Tests
**Purpose**: Test multiple components working together
**Location**: `tests/integration/`
**Coverage Target**: N/A (focus on workflows)
**Dependencies**: Docker (MySQL, Redis)

**Example**: Test CSV upload → Database persistence → Cache invalidation
```python
async def test_csv_upload_e2e():
    """Test complete CSV upload workflow with real database."""
    # Upload CSV via API
    # Verify tickets created in MySQL
    # Verify cache updated in Redis
```

### Regression Tests
**Purpose**: Prevent previously fixed bugs from returning
**Location**: `tests/regression/`
**Coverage Target**: N/A

**Example**: Test that pagination doesn't break with large datasets

### Smoke Tests
**Purpose**: Verify Docker services are running and accessible
**Location**: `tests/smoke/`
**Coverage Target**: N/A

**Example**: Test MySQL connection, Redis connection

---

## Makefile Targets

### Test Commands
```makefile
make smoke-test         # Run smoke tests (verify Docker services)
make integration-test   # Run integration tests (with Docker)
make workflow-test      # Run multi-step workflow tests (backend API flows)
make regression-test    # Run regression tests
make test-start         # Start Docker test services
make test-stop          # Stop Docker test services
```

### Note on Unit Tests
There's currently no `make test-unit` target. Run unit tests directly with pytest:
```bash
python3 -m pytest tests/unit/ -v
```

---

## Writing New Tests

### Unit Test Template
```python
"""Unit tests for <module_name>."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.mark.asyncio
async def test_function_success():
    """Test successful case."""
    # Arrange
    mock_db = MagicMock(spec=AsyncSession)

    # Act
    result = await function_to_test(mock_db, param="value")

    # Assert
    assert result.status == "success"
    mock_db.commit.assert_called_once()
```

### Integration Test Template
```python
"""Integration tests for <endpoint_name>."""

import pytest
from httpx import AsyncClient, ASGITransport

@pytest.mark.asyncio
async def test_endpoint_integration():
    """Test endpoint with real database."""
    from ai_ticket_platform.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get("/api/endpoint")

        assert response.status_code == 200
        data = response.json()
        assert "expected_field" in data
```

### Testing Best Practices
1. **Use descriptive test names**: `test_create_category_invalid_level` not `test_error`
2. **Follow AAA pattern**: Arrange, Act, Assert
3. **Mock external dependencies**: Never hit real APIs or databases in unit tests
4. **Test edge cases**: Empty inputs, null values, boundary conditions
5. **Keep tests independent**: Each test should run in isolation
6. **Use fixtures**: Share common setup logic via pytest fixtures

---

## Coverage Improvement Strategy

### Current Gaps (69% → 70%+)

To reach 70% coverage, focus on these high-impact modules:

#### 🔴 **Quick Wins** (Add ~5-10 tests each)
1. **main.py** (73%) - Application setup tests
2. **tickets router** (50%) - CSV upload edge cases
3. **category CRUD** (79%) - Edge case handling

#### 🟡 **Medium Priority** (Not blocking 70%)
4. **Articles router** (35%) - Approval workflow
5. **Slack router** (35%) - Message sending
6. **Storage services** (28-30%) - Presigned URLs

#### ⚪ **Low Priority** (Complex, diminishing returns)
7. **Content generation** (12-35%) - LLM integration
8. **Queue management** (15-33%) - RQ tasks
9. **Clustering services** (16-19%) - ML workflows
10. **Deployment settings** (21%) - Production-only

### Recent Additions (2025-12-12)
- ✅ Added 9 tests for articles router
- ✅ Added 11 tests for slack router
- ✅ Added 4 tests for main.py application setup
- ✅ Added edge case tests for category CRUD
- ✅ Improved from 67% → 69% (+24 tests)

---

## Common Issues & Solutions

### Issue: Tests can't find modules
**Error**: `ModuleNotFoundError: No module named 'ai_ticket_platform'`
**Solution**:
```bash
cd backend
source ../.venv/bin/activate
pip install -e ".[dev,tests]"
```

### Issue: Docker services not accessible
**Error**: `Connection refused` when running integration tests
**Solution**:
```bash
# Check services are running
docker ps

# Restart if needed
export ENVIRONMENT=test
make test-stop
make test-start
sleep 15  # Wait for services
```

### Issue: Logging errors during tests
**Error**: `ValueError: I/O operation on closed file` in logging
**Solution**: This is a known issue with the async logging setup. It doesn't affect test results. To suppress:
```bash
python3 -m pytest tests/unit/ -q 2>&1 | grep -v "Logging error"
```

### Issue: Integration tests fail with "port already in use"
**Solution**:
```bash
# Kill existing test containers
make test-stop

# Check no containers are running
docker ps | grep test

# Restart clean
make test-start
```

---

## CI/CD Integration

### GitHub Actions Workflow
Tests run automatically on:
- Pull requests to `main`
- Pushes to `main`
- Manual workflow dispatch

### CI Test Execution Order (Backend Only)
```yaml
Stage 1: Lint & Security
- run: make format
- run: make static-security-analysis

Stage 2: Unit Tests (474 tests)
- run: make unit-test

Stage 3: Smoke Tests (Docker services verification)
- run: make test-start
- run: make smoke-test
- run: make test-stop

Stage 4: Integration Tests (46 tests in CI, 2 skipped)
- run: make test-start
- run: make integration-test
- run: make test-stop

Stage 5: Workflow Tests (9 tests - multi-step backend API flows)
- run: make test-start
- run: make workflow-test
- run: make test-stop

Stage 6: Regression Tests
- run: make test-start
- run: make regression-test
- run: make test-stop
```

**Note**: True end-to-end tests (Frontend → Backend → Database → Frontend) would require a separate CI workflow that:
- Builds and starts the React frontend
- Starts the backend services
- Uses Playwright or Cypress to test user interactions
- Validates the complete user journey

### Coverage Requirements
- **Unit tests**: Must maintain ≥70% coverage
- **All test stages**: Must pass (except skipped tests)
- **No failing tests allowed**

---

## Test Data & Fixtures

### Shared Fixtures (`tests/conftest.py`)
- Database session mocks
- Application settings mocks
- Test client configurations

### Test Data Files (`tests/fixtures/`)
- Sample CSV files
- Sample markdown outputs
- Mock API responses

---

## Module Coverage Details

### Modules with 100% Coverage ✅
- `core/clients/aws.py`
- `core/clients/azure.py`
- `core/clients/firebase.py`
- `core/clients/llm.py`
- `core/clients/redis.py`
- `core/clients/slack.py`
- `database/CRUD/article.py`
- `database/CRUD/company.py`
- `database/CRUD/company_file.py`
- `database/CRUD/intent.py`
- `database/CRUD/intents.py`
- `database/CRUD/ticket.py`
- `database/CRUD/user.py`
- `routers/documents.py`
- `routers/external.py`
- `routers/health.py`
- `routers/intents.py`
- All schemas

### Modules Under 70% Coverage ❌
| Module | Coverage | Statements | Missing |
|--------|----------|------------|---------|
| `services/csv_uploader/csv_orchestrator.py` | 0% | 36 | 36 |
| `services/content_generation/article_service.py` | 12% | 171 | 151 |
| `services/queue_manager/service_adapters.py` | 15% | 82 | 70 |
| `services/queue_manager/tasks.py` | 16% | 112 | 94 |
| `services/clustering/intent_matcher.py` | 16% | 56 | 47 |
| `services/clustering/cluster_interface.py` | 19% | 75 | 61 |
| `core/settings/environment/deployment.py` | 21% | 63 | 50 |
| `services/company_docs/company_doc_processing.py` | 23% | 52 | 40 |
| `core/clients/chroma_client.py` | 24% | 79 | 60 |
| `services/infra/storage/azure.py` | 28% | 68 | 49 |
| `routers/s3_test.py` | 29% | 41 | 29 |
| `services/content_generation/content_generation_interface.py` | 29% | 31 | 22 |
| `services/infra/storage/aws.py` | 30% | 64 | 45 |
| `services/queue_manager/async_helper.py` | 33% | 33 | 22 |
| `routers/articles.py` | 35% | 57 | 37 |
| `routers/slack.py` | 35% | 49 | 32 |
| `services/content_generation/langgraph_rag_workflow.py` | 35% | 106 | 69 |
| `routers/tickets.py` | 50% | 78 | 39 |

**Note**: Many low-coverage modules are complex service layers (LLM, queue management, clustering) that require extensive mocking and are lower priority for unit testing.

---

## Mock Endpoints

Some endpoints use mock implementations for development. See [MOCK_ENDPOINTS.md](./MOCK_ENDPOINTS.md) for details on:
- Which endpoints are mocked
- Migration plan to real implementations
- Testing limitations with mocks

---

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Project Coding Standards](../CLAUDE.md)
- [Manager Instructions](../MANAGER_INSTRUCTIONS.md)

---

**Status**: ✅ Testing infrastructure operational
**Next Steps**: Continue adding unit tests to reach 70% coverage target
