# End-to-End (E2E) Testing Guide

> **Last Updated**: 2025-12-13
> **Framework**: Playwright
> **Coverage**: Full stack (React Frontend → FastAPI Backend → MySQL Database)

---

## Overview

End-to-end tests validate the **complete user journey** through your application, testing the entire stack as a real user would experience it.

### What E2E Tests Cover

```
User Browser (Playwright)
   ↓
React Frontend (localhost:3000)
   ↓
FastAPI Backend (localhost:8000)
   ↓
MySQL Database (Docker)
   ↓
Response back to Frontend
   ↓
User sees updated UI
```

### Example: CSV Upload E2E Test

```typescript
test('user uploads CSV and sees tickets', async ({ page }) => {
  // 1. User navigates to upload page
  await page.goto('/upload');

  // 2. User selects CSV file
  await page.setInputFiles('input[type="file"]', 'sample.csv');

  // 3. User clicks upload button
  await page.click('button:has-text("Upload")');

  // 4. User sees success message
  await expect(page.locator('.success')).toBeVisible();

  // 5. User navigates to tickets page
  await page.goto('/tickets');

  // 6. User sees uploaded tickets in UI
  await expect(page.locator('text=Test Ticket')).toBeVisible();
});
```

**What happened behind the scenes**:
- ✅ Frontend sent multipart form data to `/api/tickets/upload-csv`
- ✅ Backend parsed CSV and saved tickets to MySQL
- ✅ Backend returned success response
- ✅ Frontend displayed success message
- ✅ Tickets page fetched data from backend
- ✅ UI rendered the tickets

---

## Test Types Comparison

| Test Type | Scope | Speed | Confidence | Tools |
|-----------|-------|-------|------------|-------|
| **Unit Tests** | Single function | ⚡ Very Fast | Low | pytest |
| **Integration Tests** | API endpoints | 🚀 Fast | Medium | pytest + Docker |
| **Workflow Tests** | Multi-step APIs | 🏃 Medium | Medium | pytest + Docker |
| **E2E Tests** | Full user journey | 🐢 Slow | **High** | Playwright |

### When to Use Each

**Unit Tests**: Test business logic
```python
def test_validate_csv_format():
    result = validate_csv("subject,body\nTest,Description")
    assert result.is_valid == True
```

**Integration Tests**: Test API contracts
```python
async def test_upload_csv_endpoint(client):
    response = await client.post("/api/tickets/upload-csv", files=csv_file)
    assert response.status_code == 200
```

**E2E Tests**: Test user journeys
```typescript
test('user can upload CSV and see results', async ({ page }) => {
  // Simulate real user clicking through UI
});
```

---

## Quick Start

### Option 1: One Command (Recommended)

```bash
# Install E2E dependencies (first time only)
make e2e-install

# Run complete E2E test suite (starts everything, runs tests, cleans up)
make e2e-test-full
```

That's it! This single command will:
1. Start Docker services (MySQL, Redis)
2. Start backend server (FastAPI)
3. Start frontend server (React)
4. Wait for services to be ready
5. Run all E2E tests
6. Clean up and stop all services

### Option 2: Manual Control

```bash
# 1. Install dependencies (first time only)
make e2e-install

# 2. Start services manually
# Terminal 1: Docker Services
cd backend
export ENVIRONMENT=test
make test-start

# Terminal 2: Backend
cd backend
source ../.venv/bin/activate
export ENVIRONMENT=test
make dev

# Terminal 3: Frontend
cd frontend
npm run dev

# Terminal 4: Run E2E Tests
make e2e-test

# 5. Clean up when done
make e2e-cleanup
```

---

## Running Tests

### Local Development

```bash
# Run all E2E tests
cd e2e && npm test

# Run with visible browser
npm run test:headed

# Run in interactive UI mode
npm run test:ui

# Run in debug mode (step through)
npm run test:debug

# Run specific test file
npx playwright test csv-upload

# Run tests matching pattern
npx playwright test --grep "upload"
```

### View Results

```bash
# View HTML report
npm run report

# Generate test screenshots
npx playwright test --screenshot=on
```

---

## CI/CD Integration

E2E tests run automatically as part of the backend CI workflow on every push/PR via GitHub Actions:

### Workflow Stages

```
Backend CI Pipeline:
1. Lint & Security → Fast checks
2. Unit Tests (474 tests) → No Docker
3. Smoke Tests → Verify Docker services
4. Integration Tests (46 passing, 2 skipped) → API contracts
5. Regression Tests → Previously fixed bugs
6. Workflow & E2E Tests (Combined) → Complete workflows
   ├─ Start Docker (MySQL, Redis, ChromaDB, Firebase Emulator)
   ├─ Run Backend Workflow Tests (multi-step API flows)
   ├─ Start Backend Server (FastAPI on port 8000)
   ├─ Start Frontend Server (React on port 3000)
   ├─ Run Full-Stack E2E Tests (Playwright)
   └─ Upload test reports
```

**Key Points:**
- E2E tests are integrated into the backend CI workflow (not a separate workflow)
- Workflow tests (backend API flows) and E2E tests (full-stack) run together
- Backend workflow tests run first (faster, no frontend needed)
- Then full-stack E2E tests run with Playwright
- Frontend is built and started automatically in CI
- Test reports and screenshots are uploaded as artifacts

### View CI Results

1. Go to GitHub Actions tab
2. Click on latest workflow run
3. Scroll to the "Workflow & E2E Tests" job
4. Download artifacts:
   - "playwright-report" - HTML test report
   - "playwright-screenshots" - Screenshots of failures (if any)
   - "e2e-service-logs" - Backend/frontend logs (if tests failed)
5. Extract and open `playwright-report/index.html`

---

## Writing New E2E Tests

### Test Structure

```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  // Setup before each test
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  // Main test
  test('should do user action', async ({ page }) => {
    // 1. Navigate
    await page.goto('/feature-page');

    // 2. Interact
    await page.click('button:has-text("Click Me")');

    // 3. Verify
    await expect(page.locator('.result')).toContainText('Success');
  });

  // Cleanup
  test.afterEach(async ({ request }) => {
    // Clean test data if needed
    await request.delete('http://localhost:8000/api/test-cleanup');
  });
});
```

### Best Practices

#### 1. Use Data Test IDs

**Frontend (React)**:
```tsx
<button data-testid="upload-btn">Upload</button>
<div data-testid="ticket-list">...</div>
```

**E2E Test**:
```typescript
await page.click('[data-testid="upload-btn"]');
await expect(page.locator('[data-testid="ticket-list"]')).toBeVisible();
```

#### 2. Wait for Network Idle

```typescript
await page.goto('/tickets');
await page.waitForLoadState('networkidle');  // Wait for API calls to complete
```

#### 3. Use Meaningful Selectors

```typescript
// ❌ Bad: Fragile, breaks easily
await page.click('.MuiButton-root.css-1234');

// ✅ Good: Semantic, resilient
await page.click('button:has-text("Upload CSV")');
await page.click('[data-testid="upload-button"]');
```

#### 4. Add Timeouts for Async Operations

```typescript
// CSV processing might take time
await expect(page.locator('.success-message')).toBeVisible({ timeout: 30000 });
```

#### 5. Clean Up Test Data

```typescript
test.afterEach(async ({ request }) => {
  // Delete test tickets
  await request.post('http://localhost:8000/api/test/cleanup', {
    data: { test_run_id: 'e2e-test-123' }
  });
});
```

---

## Debugging Failed Tests

### Option 1: Run in Headed Mode

```bash
npm run test:headed
```
Watch the browser as tests run.

### Option 2: Use Debug Mode

```bash
npm run test:debug
```
Step through tests line by line with Playwright Inspector.

### Option 3: View Trace Files

```bash
# Traces are auto-generated on failure
npx playwright show-trace test-results/*/trace.zip
```

Interactive timeline showing:
- Network requests
- Console logs
- Screenshots at each step
- DOM snapshots

### Option 4: Check Artifacts

After test failure:
- **Screenshots**: `test-results/*/screenshot.png`
- **Videos**: `test-results/*/video.webm`
- **Logs**: Check terminal output

### Common Issues

**Issue**: `Error: page.goto: net::ERR_CONNECTION_REFUSED`
**Solution**: Frontend not running. Start with `cd frontend && npm run dev`

**Issue**: `Error: locator.click: Timeout 30000ms exceeded`
**Solution**: Element not found. Check selector or add wait:
```typescript
await page.waitForSelector('button:has-text("Upload")');
```

**Issue**: `Test passes locally but fails in CI`
**Solution**:
- Increase timeouts for CI: `{ timeout: 60000 }`
- Check CI logs for service startup issues
- Verify all environment variables are set

---

## Directory Structure

```
e2e/
├── package.json                # Dependencies (Playwright, TypeScript)
├── playwright.config.ts        # Test configuration
├── tsconfig.json              # TypeScript config (auto-generated)
├── tests/
│   ├── health.spec.ts         # Basic connectivity tests
│   ├── csv-upload.spec.ts     # CSV upload user journey
│   └── tickets.spec.ts        # Ticket management flows
├── fixtures/
│   └── sample-tickets.csv     # Test data files
├── test-results/              # Test outputs (gitignored)
├── playwright-report/         # HTML reports (gitignored)
└── README.md                  # E2E-specific documentation
```

---

## Makefile Commands

All E2E testing can be done from the root directory using Make commands:

### Installation
```bash
make e2e-install          # Install E2E dependencies and Playwright browsers
```

### Running Tests
```bash
make e2e-test-full        # Run complete E2E suite (starts all services, tests, cleanup)
make e2e-test             # Run tests (requires services to be running)
make e2e-test-docker      # Start Docker services only (manual frontend/backend start)
```

### Utilities
```bash
make e2e-report           # View Playwright test report
make e2e-clean            # Clean test artifacts (screenshots, videos, traces)
make e2e-cleanup          # Stop all E2E services (backend, frontend, Docker)
```

### E2E Makefile in `e2e/` Directory
```bash
cd e2e

make test                 # Run all tests
make test-headed          # Run tests with visible browser
make test-ui              # Run tests in interactive UI mode
make test-debug           # Run tests in debug mode
make report               # View test report
make codegen              # Generate test code with Playwright
make verify-services      # Check if backend and frontend are running
make clean                # Clean test artifacts
```

### Example Workflows

**Full automated run:**
```bash
make e2e-install          # First time only
make e2e-test-full        # Does everything
```

**Manual control:**
```bash
make e2e-test-docker      # Start Docker
# Manually start backend and frontend in separate terminals
make e2e-test             # Run tests
make e2e-cleanup          # Stop everything
```

**Just the tests (services already running):**
```bash
make e2e-test
```

---

## Coverage Analysis

E2E tests complement other test types:

```
Total Test Coverage
├── Unit Tests: 474 tests → Business logic
├── Integration Tests: 46 tests → API contracts
├── Workflow Tests: 9 tests → Multi-step APIs
└── E2E Tests: 5+ tests → Full user journeys ← NEW!
```

**Target Coverage**:
- Backend code: 70% (unit + integration)
- Critical user paths: 100% (E2E)

---

## Performance Considerations

### E2E Tests Are Slow

Average test times:
- Unit test: ~0.1 seconds
- Integration test: ~2 seconds
- E2E test: ~10-30 seconds

**Best Practices**:
- Run E2E tests on CI, not on every save
- Use `test.only` for debugging single tests
- Parallelize where possible (Playwright does this automatically)

### Optimize Test Speed

```typescript
// Share setup across tests
test.beforeAll(async ({ browser }) => {
  // Create context once
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.goto('/');
  // Reuse for all tests
});
```

---

## Resources

- **Playwright Docs**: https://playwright.dev
- **Best Practices**: https://playwright.dev/docs/best-practices
- **CI/CD Guide**: https://playwright.dev/docs/ci
- **Selectors Guide**: https://playwright.dev/docs/selectors
- **Video Tutorials**: https://www.youtube.com/c/Playwrightweb

---

## Next Steps

1. **Add More E2E Tests**: Cover critical user journeys
2. **Add Visual Regression**: Use `toHaveScreenshot()`
3. **Add Accessibility Tests**: Use `@axe-core/playwright`
4. **Add API Testing**: Use Playwright's `request` fixture
5. **Add Mobile Testing**: Add mobile viewport configs

---

**Status**: ✅ E2E testing infrastructure ready
**Next**: Write E2E tests for your critical user flows
