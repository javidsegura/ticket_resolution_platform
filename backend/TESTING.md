# Testing Guide

## Overview

This project includes comprehensive unit tests and integration tests:

### Feature Branches
1. **feature/clustering** - Ticket clustering with LLM integration
2. **feature/csv-uploader** - CSV parsing, orchestration, and database integration
3. **feature/CompanyDoc** - Document labeling, classification, and company file management

### Services Tested
- **Clustering Service** - Automatic ticket clustering and grouping
- **CSV Uploader Service** - CSV file parsing and ticket import workflow
- **Labeling Service** - PDF document processing and LLM-based classification
- **Documents Router** - API endpoint for PDF document uploads
- **Company File CRUD** - Database operations for company documents

**Test Statistics:**
- **Total Tests:** 170 (unit) + 8 (integration/infrastructure) = 178 total
- **Code Coverage:** 97% on feature branch services
- **Status:** All tests passing ✓
- **Uncovered Lines:** 11 (edge cases in csv_parser.py)

### Test Hierarchy (By Type)

```
Testing Pyramid:
                    E2E Tests (User Workflows) [NOT YET IMPLEMENTED]
                          /
                         /  Business Logic Tests (5 planned)
                        /
                  Integration Tests (8 current - infrastructure)
                      /
                     /  Unit Tests (170 - services & logic)
                    /
           Infrastructure (Docker, fixtures)
```

**Current Test Breakdown:**
- **Unit Tests:** 170 tests (service logic, CRUD operations)
- **Integration Tests (Infrastructure):** 6 passing (CSV, Redis, MySQL)
  - Direct database/cache testing (no HTTP endpoints needed)
  - Docker services verification
- **Integration Tests (Business Logic):** 5 planned (BLOCKED - waiting for endpoints)
  - End-to-end workflow testing (CSV→Clustering→Caching)
  - Requires cluster & ticket GET endpoints
- **E2E Tests:** Next phase (user journey from UI perspective)

## Running Tests

### Basic Commands

```bash
# Navigate to backend directory
cd backend

# Run all feature branch tests
python3 -m pytest tests/unit/ -v

# Run all tests with quiet output
python3 -m pytest tests/unit/ -q

# Run tests for specific feature branch
python3 -m pytest tests/unit/clustering/ -v          # feature/clustering
python3 -m pytest tests/unit/csv_uploader/ -v        # feature/csv-uploader
python3 -m pytest tests/unit/labeling/ -v            # feature/CompanyDoc (labeling)
python3 -m pytest tests/unit/routers/test_documents_router.py -v         # feature/CompanyDoc (router)
python3 -m pytest tests/unit/database/test_company_file_crud.py -v       # feature/CompanyDoc (database)
```

## Coverage Reports

### Option 1: Simple Terminal Report
```bash
python3 -m pytest tests/unit/ --cov=src/ai_ticket_platform/services --cov-report=term
```

Shows a clean coverage table with percentages for each module.

### Option 2: Detailed Terminal Report (with missing lines)
```bash
python3 -m pytest tests/unit/ --cov=src/ai_ticket_platform/services --cov-report=term-missing
```

Shows which specific lines are not covered by tests.

### Option 3: HTML Report (Best for Visual Review)
```bash
python3 -m pytest tests/unit/ --cov=src/ai_ticket_platform/services --cov-report=html
```

Generates an interactive HTML report at `htmlcov/index.html` that you can open in a browser. Shows:
- Overall coverage percentage
- Per-file breakdown
- Line-by-line coverage highlighting

### Option 4: Core Services Only (97% Coverage)
```bash
python3 -m pytest tests/unit/ \
  --cov=src/ai_ticket_platform/services/csv_uploader \
  --cov=src/ai_ticket_platform/services/clustering \
  --cov=src/ai_ticket_platform/services/labeling \
  --cov-report=term
```

Focuses on the three main services, showing the 97% coverage achievement.

## Test Organization

### CSV Uploader Tests (48 tests)
- **test_csv_parser.py** (32 tests)
  - CSV parsing validation (subject/body vs title/content columns)
  - Output structure validation
  - Edge cases (special characters, multiline content)
  - Data validation (empty fields, whitespace)
  - Date handling (ISO format, datetime, invalid dates)
  - Encoding detection
  - Error handling and collection

- **test_csv_orchestrator.py** (8 tests)
  - Complete upload workflow
  - Error handling at each step
  - Temp file cleanup

- **test_csv_uploader.py** (8 tests)
  - Clustering with cache integration
  - Database saving operations

### Clustering Tests (35 tests)
- **test_cluster_service.py** (11 tests)
  - Hash computation for deduplication
  - Ticket text extraction
  - Cache hit/miss scenarios
  - LLM integration

- **test_llm_clusterer.py** (8 tests)
  - LLM clustering with validation
  - Ticket assignment verification
  - Error handling

- **test_prompt_builder.py** (16 tests)
  - Clustering prompt generation
  - Output schema validation
  - Field definitions

### Labeling Tests (61 tests) - CompanyDoc Feature
- **test_label_service.py** (10 tests)
  - Document labeling with LLM
  - Empty content handling
  - Error cases
  - Additional field preservation

- **test_document_decoder.py** (11 tests)
  - PDF text extraction using pdfplumber
  - MAX_CHARS limit (25,000 chars) enforcement
  - Multiple page support
  - Empty/None page handling
  - Corrupted PDF exception handling
  - Content stripping and newline insertion

- **test_document_processor.py** (10 tests)
  - Complete processing workflow (decode → label → save)
  - Decode failures and recovery
  - Labeling failures and recovery
  - Database persistence failures
  - Async thread execution with asyncio.to_thread()
  - File ID and area label extraction

- **test_prompt_builder.py** (30 tests)
  - Labeling prompt generation
  - Output schema and task configuration
  - Field descriptions
  - System prompt content
  - Department examples (Tech, Finance, HR, etc.)

### CompanyDoc API & Database Tests (29 tests)
- **test_documents_router.py** (14 tests)
  - Single/multiple PDF file uploads via `POST /api/documents/upload`
  - PDF file type validation (rejects non-PDF files)
  - Mixed PDF/non-PDF handling
  - File size and content validation
  - Sequential file processing (not concurrent)
  - Processing failure handling
  - Response structure validation
  - Case-insensitive PDF detection

- **test_company_file_crud.py** (15 tests)
  - Create company file with all fields
  - Create with optional area field
  - Create with empty blob_path
  - Retrieve by ID (found/not found scenarios)
  - Get all files with pagination support
  - Delete operations (success/not found)
  - Exception handling and rollback
  - Database transaction management

## Coverage Breakdown

### By Service Module (Feature Branch Services Only)
| Module | Coverage | Tests | Status |
|--------|----------|-------|--------|
| **CSV Uploader Services** | | | |
| CSV Parser | 85% | 32 | ✓ |
| CSV Uploader | 100% | 8 | ✓ |
| CSV Orchestrator | 100% | 8 | ✓ |
| **Clustering Services** | | | |
| Cluster Service | 100% | 11 | ✓ |
| LLM Clusterer | 100% | 8 | ✓ |
| Clustering Prompt | 100% | 16 | ✓ |
| **Labeling Services (CompanyDoc)** | | | |
| Label Service | 100% | 10 | ✓ |
| Document Decoder | 100% | 11 | ✓ |
| Document Processor | 100% | 10 | ✓ |
| Labeling Prompt | 100% | 30 | ✓ |
| **CompanyDoc API & Database** | | | |
| Documents Router | 100% | 14 | ✓ |
| Company File CRUD | 100% | 15 | ✓ |
| **Feature Branches Total** | **97%** | **170** | **✓** |

## Running Specific Tests

```bash
# Run a specific test class
python3 -m pytest tests/unit/csv_uploader/test_csv_parser.py::TestCSVParserValidation -v

# Run a specific test function
python3 -m pytest tests/unit/csv_uploader/test_csv_parser.py::TestCSVParserValidation::test_parse_csv_with_subject_body_columns -v

# Run tests matching a pattern
python3 -m pytest tests/unit/ -k "encoding" -v

# Run with more verbose output
python3 -m pytest tests/unit/ -vv

# Run with print statements
python3 -m pytest tests/unit/ -v -s

# Run CompanyDoc feature tests
python3 -m pytest tests/unit/labeling/ -v                    # All labeling tests
python3 -m pytest tests/unit/routers/test_documents_router.py -v  # Router tests
python3 -m pytest tests/unit/database/test_company_file_crud.py -v # Database tests

# Run all CompanyDoc-related tests
python3 -m pytest tests/unit/labeling tests/unit/routers tests/unit/database -v
```

## CompanyDoc Feature Architecture

The CompanyDoc feature enables automatic document classification for ticket routing. Here's how it works:

```
PDF Upload (user)
    ↓
[POST /api/documents/upload] (documents router)
    ↓
For each file:
  1. Validate file is PDF
  2. [decode_document()] Extract text up to 25,000 chars
  3. [label_document()] Use LLM to classify department
  4. [create_company_file()] Save metadata + area label to database
    ↓
Return: {"total_processed": 3, "successful": 3, "failed": 0, "results": [...]}
```

**Key Components:**
- **Router** (`routers/documents.py`) - Accepts file uploads, orchestrates processing
- **Label Service** (`services/labeling/label_service.py`) - Uses LLM for classification
- **Document Decoder** (`services/labeling/document_decoder.py`) - Extracts text from PDF
- **Document Processor** (`services/labeling/document_processor.py`) - Orchestrates the workflow
- **CRUD** (`database/CRUD/company_file.py`) - Database persistence
- **Model** (`database/generated_models.py::CompanyFile`) - Database schema

**Design Decisions:**
1. **Sequential Processing** - Files processed one-at-a-time (not concurrent) to avoid AsyncSession conflicts
2. **Character Limit** - MAX_CHARS = 25,000 prevents LLM token overflow
3. **Temperature = 0.3** - Low temperature ensures consistent department classification
4. **Async with Threading** - Uses `asyncio.to_thread()` for CPU/I/O-bound operations
5. **Graceful Degradation** - Returns "Unknown" area if classification fails, still saves file

---

## Test Architecture

### Mocking Strategy
All tests use proper mocking of external dependencies:
- **LLM Client** - Mocked to avoid API calls and control responses
- **Database** - Mocked with SQLAlchemy AsyncSession spec for CRUD tests
- **File System** - Uses pytest's tmp_path fixture for isolation
- **Cache Manager** - Mocked for cache testing
- **PDF Files** - Created as binary fixtures for document decoder tests

### Test Categories
1. **Success Path Tests** - Normal operation scenarios
2. **Error Handling Tests** - Exception propagation and handling
3. **Edge Case Tests** - Boundary conditions and unusual inputs
4. **Integration Tests** - Multiple components working together
5. **Data Validation Tests** - Input validation and sanitization

## Continuous Integration

To run tests in CI/CD pipelines for the feature branch services:

```bash
# Run tests on feature branch services with 70% minimum coverage requirement
python3 -m pytest tests/unit/ \
  --cov=src/ai_ticket_platform/services/csv_uploader \
  --cov=src/ai_ticket_platform/services/clustering \
  --cov=src/ai_ticket_platform/services/labeling \
  --cov=src/ai_ticket_platform/routers/documents \
  --cov=src/ai_ticket_platform/database/CRUD/company_file \
  --cov-fail-under=70 \
  --cov-report=term

# Generate JUnit XML report for CI systems
python3 -m pytest tests/unit/ \
  --cov=src/ai_ticket_platform/services/csv_uploader \
  --cov=src/ai_ticket_platform/services/clustering \
  --cov=src/ai_ticket_platform/services/labeling \
  --cov=src/ai_ticket_platform/routers/documents \
  --cov=src/ai_ticket_platform/database/CRUD/company_file \
  --junitxml=test-results.xml \
  --cov-report=xml
```

## Common Issues & Solutions

### Issue: "No module named 'ai_ticket_platform'"
**Solution:** Make sure you're in the backend directory and have installed dependencies:
```bash
cd backend
pip install -e .
```

### Issue: "ModuleNotFoundError" for test dependencies
**Solution:** Install test dependencies:
```bash
pip install pytest pytest-cov pytest-asyncio
```

### Issue: Tests hanging or timing out
**Solution:** Some tests involve async operations. If tests hang:
```bash
# Run with timeout
pytest tests/unit/ --timeout=10
```

---

## Integration Tests (Docker-Based)

### Overview

Integration tests verify real Docker services (MySQL, Redis, Firebase) and test actual system behavior end-to-end.

**Current Tests:** 8 tests covering infrastructure and data persistence
**Location:** `tests/integration/`
**Running:** `make test-integration-services-docker` (from backend dir)

### Available Endpoints - Implementation Status

#### ✅ **Recently Implemented** (From Main Branch Integration)
```
TICKETS (NOW TESTABLE):
  GET /api/tickets               # List tickets with pagination (skip, limit) ✅ [5 tests]
  GET /api/tickets/{id}          # Get single ticket by ID ✅ [2 tests]
  POST /api/tickets/upload-csv   # Upload CSV file (WORKING) ✅ [1 test]

INTENTS (NOW TESTABLE):
  GET /api/intents               # List intents with pagination & filtering ✅ [3 tests]
  GET /api/intents/{id}          # Get single intent by ID ✅ [2 tests]

ANALYTICS (NOW TESTABLE):
  POST /api/external/collect     # Record impression/resolution events ✅ [2 tests]
  GET /api/external/analytics/{intent_id} # Get intent-specific metrics ✅ [1 test]
  GET /api/external/analytics/totals     # Get aggregated A/B testing data ✅ [1 test]

DOCUMENTS:
  POST /api/documents/upload     # Upload PDF documents (WORKING)

HEALTH:
  GET /api/health/ping           # API health check (WORKING)
  GET /api/health/dependencies   # Service health check (WORKING)

SLACK:
  POST /api/slack/send-message
  POST /api/slack/send-article-proposal
  POST /api/slack/send-approval-confirmation
  POST /api/slack/receive-answer
  GET /api/slack/ping
```

#### ❌ **STILL NEEDED FOR BUSINESS LOGIC TESTS** (Not Yet Implemented)
```
CLUSTERS (CRITICAL - Required by 8 tests):
  GET /api/clusters              # List all clusters [REQUIRED]
  GET /api/clusters/:id          # Get single cluster [REQUIRED]
```

### Current Integration Tests (22 tests total)

#### Infrastructure Tests (8 tests - Existing)

**File: `test_csv_upload_docker.py` (2 tests)**
- `test_csv_upload_persists_to_mysql` - Verifies CSV data correctly persists to MySQL
- `test_health_endpoint_works` - Verifies API health endpoint accessibility

**File: `test_caching_docker.py` (4 tests)**
- `test_redis_cache_operations` - Verifies SET/GET operations and data persistence
- `test_redis_ttl_expiration_works` - Verifies automatic TTL eviction after 2s timeout
- `test_redis_connection_and_basic_operations` - Comprehensive Redis connectivity and INCR/DECR
- (Demonstrates cache-aside pattern foundation)

**File: `test_persistence_docker.py` (3 tests)**
- `test_mysql_transaction_acid_compliance` - Verifies ACID guarantees (Atomicity, Durability, Consistency)
- `test_concurrent_database_operations_and_pooling` - Tests 10 concurrent insert/read/update with pooling
- `test_database_connection_health` - Verifies connection health, transactions, table existence

#### Endpoint Integration Tests (14 tests - New)

**File: `test_tickets_endpoints.py` (5 tests)**
- `test_get_tickets_empty_list` - Tests GET /api/tickets with empty database
- `test_get_tickets_pagination` - Tests pagination with skip/limit parameters
- `test_get_ticket_by_id_success` - Tests successful single ticket retrieval
- `test_get_ticket_by_id_not_found` - Tests 404 error handling for missing tickets
- `test_csv_upload_then_get_tickets` - End-to-end flow: CSV upload → GET /api/tickets

**File: `test_intents_endpoints.py` (5 tests)**
- `test_list_intents_empty` - Tests empty database handling
- `test_list_intents_pagination` - Tests pagination support
- `test_get_intent_by_id` - Tests single intent retrieval
- `test_get_intent_by_id_not_found` - Tests 404 error handling
- `test_filter_intents_by_processed_status` - Tests is_processed filtering

**File: `test_external_analytics.py` (4 tests)**
- `test_collect_impression_event` - Tests impression event collection and counter increments
- `test_collect_resolution_event` - Tests resolution event collection
- `test_get_intent_analytics` - Tests intent-specific A/B testing metrics retrieval
- `test_get_analytics_totals` - Tests aggregated analytics across all intents

### Still Missing - Blocked Integration Tests (8 tests)

**Status:** BLOCKED - Waiting for GET /api/clusters endpoint implementation
**Scope:** Clustering cache tests and E2E pipeline validation
**Impact:** Cannot test clustering without the endpoint

#### Blocked Tests That Will Be Added (8 tests when /api/clusters is implemented)
- Clustering cache hit/miss performance tests (3 tests)
- E2E CSV → Clustering → Cache pipeline (3 tests)
- Concurrent operations and load testing (2 tests)

---

### How to Run All Integration Tests

#### Option 1: Run All Integration Tests with Docker (Recommended)
```bash
cd backend
ENVIRONMENT=test make test-integration-services-docker
```

This command:
1. Starts Docker containers (MySQL, Redis, Firebase)
2. Runs all 22 integration tests (8 infrastructure + 14 endpoint)
3. Generates coverage report
4. Cleans up Docker containers
5. Displays pass/fail summary

**Expected output:** All 22 tests passing with coverage report

#### Option 2: Run Specific Test File
```bash
cd backend
ENVIRONMENT=test pytest tests/integration/test_tickets_endpoints.py -v
ENVIRONMENT=test pytest tests/integration/test_intents_endpoints.py -v
ENVIRONMENT=test pytest tests/integration/test_external_analytics.py -v
```

#### Option 3: Run Single Test
```bash
cd backend
ENVIRONMENT=test pytest tests/integration/test_tickets_endpoints.py::test_get_tickets_empty_list -v
```

#### Option 4: Run with Coverage Report
```bash
cd backend
ENVIRONMENT=test pytest tests/integration/ \
  --cov=ai_ticket_platform \
  --cov-report=term-missing \
  --cov-report=html
```

Generates detailed HTML coverage report at `htmlcov/index.html`

#### Option 5: Run Infrastructure Tests Only
```bash
cd backend
ENVIRONMENT=test make test-integration-services-docker
# Then manually run only these files:
ENVIRONMENT=test pytest tests/integration/test_csv_upload_docker.py \
                        tests/integration/test_caching_docker.py \
                        tests/integration/test_persistence_docker.py -v
```

#### Option 6: Run Endpoint Tests Only
```bash
cd backend
ENVIRONMENT=test pytest tests/integration/test_tickets_endpoints.py \
                        tests/integration/test_intents_endpoints.py \
                        tests/integration/test_external_analytics.py -v
```

### Planned Business Logic Integration Tests (8 blocked tests)

**Status:** BLOCKED - Waiting for /api/clusters endpoint implementation
**Scope:** End-to-end CSV processing flow with clustering
**Approach:** Will test actual business logic workflows using real Docker services

```
Target Flow (Implemented by teammates):
  1. Upload CSV file → POST /api/tickets/upload-csv
     ↓
  2. Parse CSV → MySQL (tickets table)
     ↓
  3. Trigger clustering → GET /api/clusters (uses uploaded tickets)
     ↓
  4. Cache clustering results in Redis
     ↓
  5. Retrieve clusters → GET /api/clusters/:id (with cache verification)
     ↓
  [STOP before: Slack notification/approval workflow]
```

#### Test 1: Clustering Cache Test
**File:** `test_cluster_caching_docker.py`
**Endpoints Required:** `GET /api/clusters`
**Test Flow:**
```python
# Scenario: Verify clustering results are cached in Redis
Setup:
  - Ensure tickets exist in MySQL (from previous CSV upload)

First Call (Cache Miss):
  - GET /api/clusters
  - Record response time
  - Verify HTTP 200
  - Store clustering results in variable
  - Verify Redis cache is populated with results

Second Call (Cache Hit):
  - GET /api/clusters
  - Record response time
  - Verify HTTP 200
  - Verify results match first call
  - Verify response time is faster (proves cache hit)

Assertions:
  - Response structure valid (contains clusters array)
  - Cache key exists in Redis after first call
  - Second call response time < first call response time
  - Data consistency across both calls
```

**Verifies:**
- Clustering endpoint works correctly
- Redis caching of clustering results works
- Cache-aside pattern: First miss → MySQL, second hit → Redis
- Performance improvement from caching

---

#### Test 2: Cache-Aside Pattern (Ticket Search) Test
**File:** `test_ticket_search_cache_docker.py`
**Endpoints Required:** `GET /api/tickets?search=query`
**Test Flow:**
```python
# Scenario: Verify search results use cache-aside pattern
Setup:
  - Upload CSV with known tickets
  - Verify tickets in MySQL
  - Clear Redis cache

First Call (Cache Miss):
  - GET /api/tickets?search=test
  - Verify HTTP 200
  - Store results in variable
  - Verify cache miss (came from MySQL)
  - Verify Redis cache now populated

Second Call (Cache Hit):
  - GET /api/tickets?search=test
  - Verify HTTP 200
  - Verify results match first call
  - Verify cache hit (came from Redis)

Assertions:
  - Search results structure valid
  - First call fetches from MySQL
  - Redis populated after first call
  - Second call fetches from Redis
  - Response times: second call faster than first
  - Data consistency across both calls
```

**Verifies:**
- Ticket search endpoint works
- Cache-aside pattern implementation correct
- MySQL → Redis flow works
- Cache invalidation works correctly

---

#### Test 3: End-to-End CSV→Clustering Pipeline Test
**File:** `test_csv_to_clusters_pipeline_docker.py`
**Endpoints Required:** `POST /api/tickets/upload-csv`, `GET /api/clusters`
**Test Flow:**
```python
# Scenario: Complete workflow from CSV upload through clustering
Setup:
  - Prepare test CSV file with known data

Step 1: Upload CSV
  - POST /api/tickets/upload-csv
  - Verify HTTP 200
  - Verify tickets inserted into MySQL
  - Record number of tickets uploaded

Step 2: Trigger Clustering
  - GET /api/clusters
  - Verify HTTP 200
  - Verify clusters created from uploaded tickets
  - Verify Redis cache populated

Step 3: Verify Cache
  - Check Redis contains clustering results
  - Verify cache structure valid

Step 4: Verify Data Integrity
  - GET /api/clusters (should come from Redis now)
  - Verify results match first clustering call

Assertions:
  - Correct number of tickets inserted
  - Clusters created with proper structure
  - All tickets assigned to clusters
  - Redis cache contains results
  - Response times: second call faster
  - No data loss in pipeline
```

**Verifies:**
- Complete CSV upload flow works
- Clustering triggered automatically/on-demand
- Data flows correctly through pipeline
- Caching works end-to-end
- No data loss or corruption

---

#### Test 4: Document Upload Workflow Test
**File:** `test_document_upload_workflow_docker.py`
**Endpoints Required:** `POST /api/documents/upload`
**Test Flow:**
```python
# Scenario: Document upload with automatic labeling
Setup:
  - Create test PDF file

Step 1: Upload Document
  - POST /api/documents/upload (multipart form-data)
  - Verify HTTP 200
  - Verify response contains upload details

Step 2: Verify Database Storage
  - Query company_files table
  - Verify metadata stored
  - Verify area label assigned (from LLM)

Step 3: Verify File Processing
  - Verify document text extracted (up to 25K chars)
  - Verify labeling completed
  - Verify no errors in processing

Assertions:
  - Document inserted into database
  - Metadata complete (file_id, area, blob_path)
  - Area label is valid department (Tech, Finance, HR, etc.)
  - Processing completed without errors
  - File status is "processed" or "success"
```

**Verifies:**
- Document upload endpoint works
- PDF processing pipeline works
- LLM-based labeling assigns correct department
- Database persistence works
- File metadata stored correctly

---

#### Test 5: Concurrent CSV Uploads Test
**File:** `test_concurrent_csv_uploads_docker.py`
**Endpoints Required:** `POST /api/tickets/upload-csv`, `GET /api/clusters`
**Test Flow:**
```python
# Scenario: Multiple CSV uploads simultaneously don't conflict in caching
Setup:
  - Prepare 3+ test CSV files with different data
  - Clear Redis cache

Concurrent Operations:
  - Upload CSV 1 (asyncio task)
  - Upload CSV 2 (asyncio task)
  - Upload CSV 3 (asyncio task)
  - All execute in parallel

Step 1: Verify All Uploads Succeeded
  - All HTTP 200 responses
  - All tickets in MySQL
  - Total count = sum of all CSV rows

Step 2: Trigger Clustering
  - GET /api/clusters
  - Verify all tickets included in clusters
  - Verify Redis cache populated

Step 3: Verify No Cache Conflicts
  - Redis contains ONE clustering result (not multiple)
  - Result includes ALL uploaded tickets
  - Cache structure valid

Step 4: Verify No Race Conditions
  - Retrieve clustering twice
  - Verify identical results (cache working)
  - No partial/corrupted data

Assertions:
  - All concurrent uploads succeed (0 failures)
  - No connection pool exhaustion
  - All tickets persisted correctly
  - Clustering includes all uploaded tickets
  - Single unified cache entry (not per-upload)
  - Data integrity maintained
  - Response times consistent
```

**Verifies:**
- Concurrent operations handled safely
- No race conditions in clustering
- Cache handles concurrent updates correctly
- Connection pooling works under load
- Data integrity with concurrent writes

---

### Endpoint Specifications (Required for Business Logic Tests)

#### **TIER 1: GET /api/clusters** (CRITICAL - Blocks 3 tests)
**Purpose:** List all clusters for caching and pipeline tests
**Used By:** Tests 1, 3, 5
**Method:** GET
**Path:** `/api/clusters`
**Query Params:** None
**Status Code:** 200 OK
**Response Schema:**
```json
{
  "clusters": [
    {
      "id": 1,
      "title": "Password Reset Issues",
      "summary": "Users experiencing difficulties with password reset functionality",
      "ticketCount": 12,
      "mainTopics": ["Reset link location", "Email delivery issues"],
      "priority": "high",
      "status": "active",
      "createdAt": "2025-01-10T08:00:00Z",
      "updatedAt": "2025-01-15T14:30:00Z"
    },
    {
      "id": 2,
      "title": "Order History Navigation",
      "summary": "Users cannot locate their order history",
      "ticketCount": 8,
      "mainTopics": ["Account dashboard layout", "Navigation menu structure"],
      "priority": "medium",
      "status": "active",
      "createdAt": "2025-01-08T10:15:00Z",
      "updatedAt": "2025-01-14T09:20:00Z"
    }
  ],
  "total": 7
}
```

#### **TIER 2: GET /api/clusters/:id** (HIGH - Blocks cluster detail test)
**Purpose:** Get single cluster with full resolution details
**Used By:** Test 1 (advanced flow)
**Method:** GET
**Path:** `/api/clusters/{cluster_id}`
**Query Params:** None
**Status Code:** 200 OK (or 404 if not found)
**Response Schema:**
```json
{
  "id": 1,
  "title": "Password Reset Issues",
  "summary": "Users experiencing difficulties...",
  "ticketCount": 12,
  "mainTopics": ["Reset link location", "Email delivery"],
  "priority": "high",
  "status": "active",
  "resolution": "# Website Improvement Recommendation\n\nAdd a prominent 'Forgot Password?' link...",
  "createdAt": "2025-01-10T08:00:00Z",
  "updatedAt": "2025-01-15T14:30:00Z"
}
```

#### **TIER 3: GET /api/tickets** (CRITICAL - Blocks 2 tests)
**Purpose:** List/search tickets with optional filtering
**Used By:** Tests 2, 5
**Method:** GET
**Path:** `/api/tickets`
**Query Params:**
- `search` (optional): String to search in subject/body
- `limit` (optional): Number of results to return (default: 100)
- `offset` (optional): Pagination offset (default: 0)

**Status Code:** 200 OK
**Response Schema:**
```json
{
  "tickets": [
    {
      "id": 1,
      "subject": "Test Ticket 1",
      "body": "This is the first test ticket",
      "createdAt": "2025-11-27T10:00:00Z",
      "status": "open"
    },
    {
      "id": 2,
      "subject": "Test Ticket 2",
      "body": "This is the second test ticket",
      "createdAt": "2025-11-27T10:05:00Z",
      "status": "open"
    }
  ],
  "total": 150,
  "limit": 100,
  "offset": 0
}
```

**Example Queries:**
- `GET /api/tickets` - Get all tickets
- `GET /api/tickets?search=password` - Search for "password" in tickets
- `GET /api/tickets?search=reset&limit=10` - Search with limit
- `GET /api/tickets?limit=50&offset=50` - Pagination

#### **TIER 4: GET /api/tickets/:id** (HIGH - Blocks ticket detail test)
**Purpose:** Get single ticket details
**Used By:** Test 2 (advanced flow)
**Method:** GET
**Path:** `/api/tickets/{ticket_id}`
**Query Params:** None
**Status Code:** 200 OK (or 404 if not found)
**Response Schema:**
```json
{
  "id": 1,
  "subject": "Test Ticket 1",
  "body": "This is the first test ticket",
  "createdAt": "2025-11-27T10:00:00Z",
  "status": "open",
  "clusterId": 1
}
```

#### **TIER 5: POST /api/documents/upload** (Already Implemented)
**Purpose:** Upload PDF documents with LLM labeling
**Used By:** Test 4
**Method:** POST
**Path:** `/api/documents/upload`
**Content-Type:** `multipart/form-data`
**Body:** Multiple PDF files
**Status Code:** 200 OK
**Response Schema:**
```json
{
  "total_processed": 3,
  "successful": 3,
  "failed": 0,
  "results": [
    {
      "filename": "document1.pdf",
      "success": true,
      "department": "Support",
      "summary": "Customer support documentation"
    },
    {
      "filename": "document2.pdf",
      "success": true,
      "department": "Engineering",
      "summary": "Technical implementation guide"
    }
  ]
}
```

---

### Implementation Timeline

**When teammates complete:**
1. ✅ Cluster endpoints → Implement Tests 1 & 3
2. ✅ Ticket search endpoint → Implement Test 2
3. ✅ Document upload endpoint → Implement Test 4
4. ✅ All of above working → Implement Test 5

**Estimated effort per test:**
- Test 1 (Clustering Cache): 1-2 hours
- Test 2 (Search Cache): 1-2 hours
- Test 3 (CSV→Clusters): 2-3 hours
- Test 4 (Document Workflow): 1.5-2 hours
- Test 5 (Concurrent Uploads): 2-3 hours

**Total:** ~8-12 hours after endpoints are ready

### Running Integration Tests

**Option 1: Automated (Recommended)**
```bash
cd backend
make test-integration-services-docker
```

This command:
- Starts Docker services (ENVIRONMENT=test)
- Runs all infrastructure tests (8 tests)
- Cleans up containers
- Reports pass/fail

**Option 2: Manual Control**
```bash
cd backend

# Terminal 1: Start services
ENVIRONMENT=test make test-docker-compose-start

# Terminal 2: Run tests
ENVIRONMENT=test pytest -s -vv tests/integration/test_csv_upload_docker.py

# Terminal 1: Stop services
ENVIRONMENT=test make test-docker-compose-stop
```

**Option 3: Run Individual Test File**
```bash
cd backend

# With services already running:
ENVIRONMENT=test pytest -s -vv tests/integration/test_caching_docker.py
```

### Docker Infrastructure

**Services Used:**
- **MySQL 8.0** - Port 3307 (host) / 3306 (container)
- **Redis 7.2** - Port 6379
- **Firebase Emulator** - Port 9099 (auth), 4000 (firestore)
- **Nginx** - Reverse proxy

**Configuration:**
- Located in `deployment/docker-compose.yml` and `deployment/docker-compose.test.yml`
- Test env variables in `.env.test` (gitignored)
- Database migrations run automatically

### Test Fixtures (conftest.py)

```python
@pytest_asyncio.fixture
async def async_client() -> AsyncClient:
    """HTTP client to FastAPI app via ASGI transport"""
    # Already existed, unchanged

@pytest_asyncio.fixture
async def db_connection() -> AsyncSession:
    """Direct async MySQL connection for verification queries"""
    # Newly added for integration tests

@pytest_asyncio.fixture
async def redis_client() -> redis.Redis:
    """Direct Redis client for cache verification"""
    # Newly added for integration tests
```

---

## E2E Tests (End-to-End User Workflows)

### Overview

E2E tests verify complete user workflows from UI interaction through final output. Tests focus on:
- **Real Docker services** (MySQL, Redis, Firebase)
- **Complete request pipelines** (not just individual endpoints)
- **User journeys** (CSV upload → draft → approval → publish → widget)
- **State transitions** (DB state changes throughout workflow)
- **Background tasks** (async operations, notifications)

**Total Tests:** 25 E2E tests across 5 workflows
**Running:** `make test-e2e` (when implemented)
**Location:** `tests/e2e/`

---

### Test 1: CSV → Draft Pipeline (4 tests)
**File:** `test_csv_draft_pipeline.py`
**Purpose:** Validate transformation from raw CSV to initial draft object
**User Journey:** User uploads CSV → System processes → Draft created

#### Tests:
1. **test_csv_upload_triggers_pipeline** - Verify CSV upload initiates pipeline
   - Upload CSV via `POST /api/tickets/upload-csv`
   - Verify HTTP 200
   - Check that backend processes file automatically

2. **test_data_validation_and_normalization** - Verify data is validated & cleaned
   - Upload CSV with various formats (mixed case, extra spaces, special chars)
   - Verify normalization (lowercase, trimmed, escaped)
   - Check validation rules applied (no empty subjects, etc.)
   - Verify invalid rows handled gracefully

3. **test_draft_created_in_database** - Verify draft object persists
   - Upload CSV
   - Query drafts table
   - Verify draft exists with correct ticket data
   - Check draft status = "draft"

4. **test_draft_metadata_correct** - Verify all metadata stored properly
   - Check `source_file` = uploaded filename
   - Check `row_count` = number of uploaded rows
   - Check `summary` field (auto-generated or provided)
   - Check `created_at` timestamp present
   - Check `version` = 1.0

---

### Test 2: CSV → Complete Flow (8 tests)
**File:** `test_csv_complete_flow.py`
**Purpose:** Full pipeline from CSV → clustering → caching → draft → markdown output
**User Journey:** User uploads CSV → System clusters → Generates markdown

#### Tests:
1. **test_csv_ingestion_succeeds** - CSV upload completes without errors
   - Upload CSV file
   - Verify all rows parsed
   - Verify tickets inserted into DB
   - Check response contains row count

2. **test_clustering_runs_and_stores** - Clustering triggered and saved
   - Upload CSV triggers clustering
   - Verify clusters created (via `GET /api/clusters`)
   - Check cluster data in DB
   - Verify ticket→cluster mappings

3. **test_redis_clustering_cache_hit** - Cached clustering results returned
   - Upload CSV → Triggers clustering
   - Call `GET /api/clusters` first time (cache miss)
   - Call `GET /api/clusters` second time (cache hit)
   - Verify both return identical results
   - Verify response time improves on cache hit

4. **test_draft_created_with_clustering_data** - Draft includes cluster info
   - Upload CSV + clustering complete
   - Query draft from DB
   - Verify draft contains cluster references
   - Verify ticket assignments to clusters stored

5. **test_draft_converted_to_markdown** - Draft → Markdown conversion works
   - Draft exists with clustering data
   - Trigger markdown generation
   - Verify `.md` file created
   - Check markdown contains cluster summaries
   - Verify formatting (headers, lists, etc.)

6. **test_background_tasks_complete** - All async operations finish
   - Upload CSV
   - Wait for processing (async clustering, markdown gen)
   - Verify no tasks stuck in "pending" state
   - Check completion timestamps recorded
   - Verify success status for all tasks

7. **test_db_entries_updated_throughout** - Data flows correctly through pipeline
   - Track DB state at each stage
   - Verify tickets table populated
   - Verify clusters table populated
   - Verify drafts table updated
   - Verify draft_markdown table populated

8. **test_end_state_matches_expected** - Final output structure correct
   - Verify draft status = "ready_for_approval"
   - Verify markdown file valid
   - Verify all data relationships intact
   - Verify no orphaned records

---

### Test 3: Approval Workflow (4 tests)
**File:** `test_approval_flow.py`
**Purpose:** Validate manual/automated approval process and state transitions
**User Journey:** Draft created → Approver reviews → Approval/rejection → State updated

#### Tests:
1. **test_draft_enters_awaiting_approval_state** - Draft transitions to approval queue
   - Create draft from CSV upload
   - Trigger approval workflow
   - Verify draft status = "awaiting_approval"
   - Check draft locked for editing
   - Verify notification sent to approver

2. **test_approver_can_approve_draft** - Approval action succeeds
   - Get draft in "awaiting_approval" state
   - Call approval endpoint (e.g., `POST /api/drafts/{id}/approve`)
   - Verify HTTP 200
   - Check draft status changed to "approved"
   - Verify timestamp recorded

3. **test_approver_can_reject_draft** - Rejection action succeeds
   - Get draft in "awaiting_approval" state
   - Call reject endpoint (e.g., `POST /api/drafts/{id}/reject`)
   - Verify HTTP 200
   - Check draft status = "rejected"
   - Verify rejection reason stored
   - Check draft reverts to editable state

4. **test_state_transitions_update_correctly** - DB reflects all state changes
   - Track draft state throughout approval flow
   - Verify audit trail (who, when, what changed)
   - Check timestamps update on each transition
   - Verify no duplicate state entries
   - Verify notifications triggered on state change

---

### Test 4: Publishing Workflow (6 tests)
**File:** `test_publish_flow.py`
**Purpose:** Validate approved drafts move to production and publish correctly
**User Journey:** Draft approved → Publishing triggered → Content live

#### Tests:
1. **test_publishing_triggers_background_job** - Publish action queues processing
   - Get approved draft
   - Call publish endpoint (e.g., `POST /api/drafts/{id}/publish`)
   - Verify HTTP 200
   - Check background job created
   - Verify job status = "processing"

2. **test_markdown_to_html_conversion** - Markdown converted to valid HTML
   - Draft markdown exists
   - Trigger HTML generation
   - Verify HTML file created
   - Check HTML is valid (well-formed, no broken tags)
   - Verify all markdown elements converted (headers, lists, code blocks)

3. **test_static_microsite_generated** - Static site assets created
   - Trigger publish
   - Verify microsite directory created
   - Check index.html generated
   - Verify CSS files present
   - Check images/assets copied

4. **test_files_written_to_correct_directory** - Output written to proper location
   - Publish triggers file writes
   - Verify files in `/public/` or configured output dir
   - Check directory structure matches expected layout
   - Verify file permissions correct (readable, not writable)

5. **test_publish_metadata_persisted** - Publication info stored in DB
   - Publish completes
   - Query published_articles table
   - Verify `publish_timestamp` recorded
   - Check `version` field (e.g., "1.0.0")
   - Verify `author` field populated
   - Check `publish_status` = "live"
   - Verify `url_slug` generated

6. **test_publish_endpoint_returns_final_content** - API serves published content
   - Publish succeeds
   - Call `GET /api/published/{article_id}` (or similar)
   - Verify HTTP 200
   - Check response contains full HTML/rendered content
   - Verify metadata (title, author, date) in response
   - Check SEO fields (meta tags, OG tags)

---

### Test 5: Widget Rendering Tests ⏳ (FUTURE WORK - Not Currently in Scope)
**Status:** Widget feature not yet implemented - marked for future development
**File:** `test_js_widget.py` (template only, no tests implemented)
**Purpose:** Verify JS widget correctly renders published content externally
**User Journey:** External site loads widget → Widget fetches & renders content

**⚠️ NOTE:** This test suite is held in reserve for when the widget feature is actually built. Currently:
- No widget exists in backend
- No widget code in frontend
- No widget router implemented
- Test only serves as documentation of expected behavior

#### Planned Tests (When Widget is Implemented):
1. **test_widget_fetches_data_from_api** - Widget API calls succeed
2. **test_widget_handles_missing_data_gracefully** - Widget doesn't break on errors
3. **test_widget_rendering_matches_expected_dom** - Widget HTML structure correct

---

### E2E Test Infrastructure Requirements

**Endpoints Needed (in addition to Integration Tests):**
- `POST /api/drafts` - Create draft
- `GET /api/drafts/:id` - Retrieve draft
- `POST /api/drafts/:id/approve` - Approve draft
- `POST /api/drafts/:id/reject` - Reject draft
- `POST /api/drafts/:id/publish` - Publish draft
- `GET /api/published/:id` - Get published article

**Endpoints NOT needed (widget feature future work):**
- ~~`GET /api/widget/:id`~~ - Widget endpoint (removed from scope, no widget implementation)

**Test Database Setup:**
- Pre-populate test users with approval roles
- Create test drafts in various states
- Populate sample published articles

**Async Task Monitoring:**
- Tests must wait for background jobs (clustering, markdown generation, publishing)
- Track job status in background_jobs or similar table
- Verify completion before assertions

**File System Access:**
- Tests need access to markdown output directory
- Tests need access to published microsite directory
- Verify files created with correct permissions

---

### Running E2E Tests

**Full Suite:**
```bash
cd backend
make test-e2e
```

**Individual Workflow:**
```bash
ENVIRONMENT=test pytest -s -vv tests/e2e/test_csv_draft_pipeline.py
ENVIRONMENT=test pytest -s -vv tests/e2e/test_csv_complete_flow.py
ENVIRONMENT=test pytest -s -vv tests/e2e/test_approval_flow.py
ENVIRONMENT=test pytest -s -vv tests/e2e/test_publish_flow.py
ENVIRONMENT=test pytest -s -vv tests/e2e/test_js_widget.py
```

**Single Test:**
```bash
ENVIRONMENT=test pytest -s -vv tests/e2e/test_csv_complete_flow.py::test_csv_ingestion_succeeds
```

---

### E2E Test Timeline

**Prerequisites:** All integration test endpoints implemented + passing

**Implementation Order:**
1. Test 1 (CSV→Draft): 2-3 hours - Foundation for other tests
2. Test 2 (CSV→Complete): 3-4 hours - Full pipeline testing
3. Test 3 (Approval): 2-3 hours - State machine testing
4. Test 4 (Publishing): 3-4 hours - File generation testing
5. ⏳ Test 5 (Widget): Future work - Blocked by widget feature not yet implemented

**Total:** ~10-14 hours after all endpoints ready (4 active test suites)

---

## COMPLETE ENDPOINT REQUIREMENTS SUMMARY

### All Endpoints Needed (Integration + E2E Testing)

#### ✅ **Already Implemented** (5 endpoints - WORKING)
```
TICKETS:
  POST /api/tickets/upload-csv              # Upload CSV file

DOCUMENTS:
  POST /api/documents/upload                # Upload PDF documents

HEALTH:
  GET /api/health/ping                      # API health check
  GET /api/health/dependencies              # Service health check

SLACK (utility, not required for testing):
  POST /api/slack/send-message
  POST /api/slack/send-article-proposal
  POST /api/slack/send-approval-confirmation
  POST /api/slack/receive-answer
  GET /api/slack/ping
```

#### ❌ **NEEDED FOR INTEGRATION TESTS** (4 endpoints - BLOCKED)
```
CLUSTERS (CRITICAL - Blocks 3 integration tests):
  GET /api/clusters                         # List all clusters [CRITICAL]
  GET /api/clusters/:id                     # Get single cluster [HIGH]

TICKETS (CRITICAL - Blocks 2 integration tests):
  GET /api/tickets                          # List/search tickets with ?search= [CRITICAL]
  GET /api/tickets/:id                      # Get single ticket [HIGH]
```

#### ❌ **NEEDED FOR E2E TESTS** (6 endpoints - BLOCKED)
```
DRAFTS (Required by E2E tests 1, 2, 3, 4):
  POST /api/drafts                          # Create draft [CRITICAL]
  GET /api/drafts/:id                       # Retrieve draft [CRITICAL]
  POST /api/drafts/:id/approve              # Approve draft [CRITICAL]
  POST /api/drafts/:id/reject               # Reject draft [CRITICAL]
  POST /api/drafts/:id/publish              # Publish draft [CRITICAL]

PUBLISHED (Required by E2E tests 2, 4):
  GET /api/published/:id                    # Get published article [CRITICAL]

WIDGET (⏳ FUTURE WORK - Not in current scope):
  GET /api/widget/:id                       # [REMOVED - Widget feature not implemented]
```

---

### Priority-Based Implementation Roadmap

#### 🔴 **PHASE 1: CRITICAL** (Unblocks most tests)
**Endpoints:** 2 CRITICAL endpoints
**Impact:** Unblocks 5+ tests
**Effort:** ~4-6 hours

1. `GET /api/clusters` - List clusters
   - Used by: Integration tests 1, 3, 5 + E2E tests 2, 4, 5
   - Blocks: 5 tests total

2. `GET /api/tickets` - List/search tickets
   - Used by: Integration test 2 + E2E tests 2, 5
   - Blocks: 3 tests total

#### 🟠 **PHASE 2: HIGH** (Completes integration testing)
**Endpoints:** 2 HIGH endpoints
**Impact:** Unblocks 2 integration tests
**Effort:** ~2-4 hours

3. `GET /api/clusters/:id` - Get single cluster
   - Used by: Integration test 1 (detail flow) + E2E tests 2, 4
   - Blocks: 2 tests

4. `GET /api/tickets/:id` - Get single ticket
   - Used by: Integration test 2 (detail flow) + E2E tests 2, 5
   - Blocks: 2 tests

#### 🟡 **PHASE 3: MAJOR** (Enables E2E testing)
**Endpoints:** 6 CRITICAL endpoints
**Impact:** Unblocks 22 E2E tests (4 active test suites, Test 5 future work)
**Effort:** ~8-10 hours

5. `POST /api/drafts` - Create draft
   - Used by: E2E tests 1, 2, 3, 4
   - Blocking: 15 E2E tests

6. `GET /api/drafts/:id` - Retrieve draft
   - Used by: E2E tests 2, 3, 4
   - Blocking: 12 E2E tests

7. `POST /api/drafts/:id/approve` - Approve draft
   - Used by: E2E test 3
   - Blocking: 4 E2E tests

8. `POST /api/drafts/:id/reject` - Reject draft
   - Used by: E2E test 3
   - Blocking: 4 E2E tests

9. `POST /api/drafts/:id/publish` - Publish draft
   - Used by: E2E test 4
   - Blocking: 6 E2E tests

10. `GET /api/published/:id` - Get published article
    - Used by: E2E tests 2, 4
    - Blocking: 8 E2E tests

**NOT IMPLEMENTING (Future Work):**
- ~~`GET /api/widget/:id`~~ - Widget feature not yet implemented

---

### Testing Coverage Matrix

| Endpoint | Integration Tests | E2E Tests | Total Impact |
|----------|---|---|---|
| ✅ `POST /api/tickets/upload-csv` | 1 | 4 | 5 ✓ PASSING |
| ✅ `POST /api/documents/upload` | 0 | 1 | 1 ✓ PASSING |
| ✅ `GET /api/health/ping` | 1 | 0 | 1 ✓ PASSING |
| ❌ `GET /api/clusters` | 3 | 3 | 6 BLOCKED |
| ❌ `GET /api/clusters/:id` | 1 | 2 | 3 BLOCKED |
| ❌ `GET /api/tickets` | 2 | 2 | 4 BLOCKED |
| ❌ `GET /api/tickets/:id` | 1 | 2 | 3 BLOCKED |
| ❌ `POST /api/drafts` | 0 | 4 | 4 BLOCKED |
| ❌ `GET /api/drafts/:id` | 0 | 3 | 3 BLOCKED |
| ❌ `POST /api/drafts/:id/approve` | 0 | 1 | 1 BLOCKED |
| ❌ `POST /api/drafts/:id/reject` | 0 | 1 | 1 BLOCKED |
| ❌ `POST /api/drafts/:id/publish` | 0 | 2 | 2 BLOCKED |
| ❌ `GET /api/published/:id` | 0 | 2 | 2 BLOCKED |
| ⏳ ~~`GET /api/widget/:id`~~ | 0 | 0 | 0 FUTURE WORK |
| **TOTAL** | **9/13** | **0/22** | **9/35** |

---

### Current Testing Status

**Unit Tests:** 170 ✅ (all passing)
**Integration Tests (Infrastructure):** 6/8 ✅ (passing)
**Integration Tests (Business Logic):** 0/5 ❌ (blocked - need 4 endpoints)
**E2E Tests:** 0/22 ❌ (blocked - need 6 endpoints, 4 active test suites only)
**E2E Tests (Future Work):** 0/3 ⏳ (widget feature not implemented)

**Total:** 176/210 tests in active scope (84%)
**Total Including Future Work:** 176/213 (83%)

---

## Development Workflow

When adding new features:

1. **Write tests first** (TDD approach)
2. **Run tests to verify they fail**
3. **Implement the feature**
4. **Run tests to verify they pass**
5. **Check coverage hasn't decreased**
6. **Commit with test updates**

```bash
# Typical workflow
python3 -m pytest tests/unit/ -v              # Run tests
python3 -m pytest tests/unit/ --cov=...       # Check coverage
python3 -m pytest tests/unit/ -k "new_test"   # Test specific feature
```

## Testing Gaps & Future Improvements

### Coverage Achievement Summary
✓ **Achieved**: 97% code coverage on feature branch services (170 tests)
✓ **Exceeded**: 70% minimum coverage requirement
✓ **All Tests Passing**: 100% test pass rate
✓ **Feature Branches**: Complete unit test coverage for all 3 branches

### Uncovered Lines (11 total)
The 11 uncovered lines are edge case error conditions in `csv_parser.py`:
- **Lines 118-121**: Row parsing errors when CSV has corrupted data
- **Lines 173-178**: Encoding detection edge cases for rare character encodings

These are intentionally left untested as they represent extremely rare error paths that are difficult to trigger in practice.

### Testing Gaps for Future Consideration

**CompanyDoc Feature (feature/CompanyDoc):**
- [ ] **End-to-End Integration Tests** - Testing router → document_processor → database with real containers
- [ ] **Real Database Tests** - Current CRUD tests use mocks; consider testcontainers for MySQL integration
- [ ] **Actual LLM API Calls** - Tests mock LLM responses; staging deployment should validate real API calls
- [ ] **Blob Storage Implementation** - Document storage in Azure blob (currently has TODO comment)

**CSV Uploader Feature (feature/csv-uploader):**
- [ ] **Large File Testing** - Files > 100 MB for memory efficiency validation
- [ ] **Special Encoding Edge Cases** - The 11 uncovered lines relate to rare encoding scenarios

**Clustering Feature (feature/clustering):**
- [ ] **Real LLM Integration** - Tests mock LLM responses; validate with actual clustering API
- [ ] **Performance Benchmarks** - Clustering speed with large ticket datasets

### Recommended Next Steps (Post-Feature-Release)

**High Priority:**
1. Integration tests with testcontainers for MySQL + real database operations
2. End-to-end tests combining router → services → database → blob storage
3. Validation of actual LLM API responses (not just mocks)

**Medium Priority:**
1. Performance benchmarks for document processing and clustering
2. Load testing for concurrent PDF uploads
3. Memory profiling for large PDF handling

**Low Priority:**
1. Support for encrypted PDFs (customer feature request dependent)
2. OCR capabilities for image-only PDFs
3. Multi-language document classification

---

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [pytest-asyncio for async tests](https://pytest-asyncio.readthedocs.io/)
- [unittest.mock for mocking](https://docs.python.org/3/library/unittest.mock.html)
- [pdfplumber Documentation](https://github.com/jsvine/pdfplumber) - Used for PDF text extraction
- [FastAPI Testing Documentation](https://fastapi.tiangolo.com/advanced/testing-databases/)
