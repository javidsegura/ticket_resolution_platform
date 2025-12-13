# End-to-End (E2E) Tests

This directory contains **true end-to-end tests** that test the complete user journey across the entire stack:

```
User Browser (Playwright) → React Frontend → FastAPI Backend → MySQL Database
```

## What E2E Tests Do

E2E tests simulate real user interactions:
- ✅ User clicks buttons in the UI
- ✅ Frontend sends API requests
- ✅ Backend processes and saves to database
- ✅ Frontend receives response and updates UI
- ✅ User sees the updated interface

**Example**: CSV Upload E2E Test
1. User navigates to `/upload` page
2. User selects CSV file
3. User clicks "Upload" button
4. Frontend sends file to backend API
5. Backend parses CSV and saves tickets to MySQL
6. Frontend shows success message
7. User navigates to `/tickets` page
8. User sees uploaded tickets in the list

## Difference from Backend Tests

| Test Type | What It Tests | Tools |
|-----------|---------------|-------|
| **Backend Unit Tests** | Individual functions with mocks | pytest |
| **Backend Integration Tests** | API endpoints with real database | pytest + Docker |
| **Backend Workflow Tests** | Multi-step API calls | pytest + Docker |
| **E2E Tests** (this) | Complete user journey through UI | Playwright + Browser |

## Setup

### Prerequisites
- Node.js ≥18
- Frontend running on `http://localhost:3000`
- Backend running on `http://localhost:8000`
- Docker services running (MySQL, Redis)

### Install Dependencies

```bash
cd e2e
npm install
npx playwright install chromium  # Install browser
```

## Running Tests

### Local Development (Auto-starts services)

```bash
# Run all tests (starts frontend + backend automatically)
npm test

# Run tests with visible browser
npm run test:headed

# Run tests in UI mode (interactive)
npm run test:ui

# Run tests in debug mode
npm run test:debug
```

### CI/CD (Services already running)

```bash
# Set environment variable
export FRONTEND_URL=http://localhost:3000

# Run tests (expects services to be running)
npm test
```

### Run Specific Tests

```bash
# Run only health tests
npx playwright test health

# Run only CSV upload tests
npx playwright test csv-upload

# Run tests matching pattern
npx playwright test --grep "upload"
```

## View Test Reports

```bash
# After tests run, view HTML report
npm run report
```

Report includes:
- Screenshots of failures
- Videos of failed tests
- Trace files for debugging

## Writing New E2E Tests

### Test Structure

```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    // Setup before each test
    await page.goto('/');
  });

  test('should do something user wants', async ({ page }) => {
    // Step 1: Navigate
    await page.goto('/feature-page');

    // Step 2: Interact with UI
    await page.click('button:has-text("Click Me")');

    // Step 3: Verify result
    await expect(page.locator('.result')).toBeVisible();
    await expect(page.locator('.result')).toContainText('Expected Text');
  });
});
```

### Best Practices

1. **Test User Journeys, Not Implementation**
   - ❌ Bad: Test if API was called with specific params
   - ✅ Good: Test if user sees expected result after action

2. **Use Data Test IDs**
   ```tsx
   // In React component
   <button data-testid="upload-button">Upload</button>

   // In test
   await page.click('[data-testid="upload-button"]');
   ```

3. **Wait for Network to Settle**
   ```typescript
   await page.waitForLoadState('networkidle');
   ```

4. **Use Meaningful Test Names**
   - ❌ Bad: `test('test upload')`
   - ✅ Good: `test('should upload CSV and display tickets in UI')`

5. **Clean Up Test Data**
   ```typescript
   test.afterEach(async ({ request }) => {
     // Clean up test data via API
     await request.delete('http://localhost:8000/api/test-data/cleanup');
   });
   ```

## Debugging Failed Tests

### Option 1: Run in Headed Mode
```bash
npm run test:headed
```

### Option 2: Use Debug Mode
```bash
npm run test:debug
```

### Option 3: View Trace
```bash
# After test failure, traces are automatically saved
npx playwright show-trace playwright-report/trace.zip
```

### Option 4: Check Screenshots/Videos
Test failures automatically capture:
- Screenshots: `test-results/*/test-failed-1.png`
- Videos: `test-results/*/video.webm`

## CI/CD Integration

E2E tests run in GitHub Actions as the final stage:

```yaml
Stage 1-6: Backend tests
   ↓
Stage 7: E2E Tests (Full Stack)
  - Start frontend (React app)
  - Start backend (FastAPI)
  - Start Docker services (MySQL, Redis)
  - Run Playwright tests
  - Upload test reports as artifacts
```

## Troubleshooting

### Tests Can't Find Elements
**Problem**: `Error: locator.click: Target closed`
**Solution**: Add explicit waits
```typescript
await page.waitForSelector('button:has-text("Upload")');
await page.click('button:has-text("Upload")');
```

### Backend Not Responding
**Problem**: Tests fail with connection refused
**Solution**: Verify backend is running
```bash
curl http://localhost:8000/api/health/ping
```

### Frontend Not Loading
**Problem**: Tests timeout waiting for frontend
**Solution**: Check frontend dev server
```bash
cd frontend && npm run dev
```

### Flaky Tests
**Problem**: Tests pass sometimes, fail other times
**Solution**:
1. Add more specific selectors
2. Increase timeouts for slow operations
3. Use `waitForLoadState('networkidle')`
4. Enable retries in CI: `retries: 2`

## Directory Structure

```
e2e/
├── package.json              # Dependencies
├── playwright.config.ts      # Playwright configuration
├── tests/
│   ├── health.spec.ts       # Basic health checks
│   ├── csv-upload.spec.ts   # CSV upload user journey
│   └── tickets.spec.ts      # Ticket management flows
├── fixtures/                 # Test data files
│   └── sample.csv
└── README.md                # This file
```

## Resources

- [Playwright Documentation](https://playwright.dev)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [Writing E2E Tests Guide](https://playwright.dev/docs/writing-tests)
- [CI/CD with Playwright](https://playwright.dev/docs/ci)
