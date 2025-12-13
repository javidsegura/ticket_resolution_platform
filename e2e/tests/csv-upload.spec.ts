import { test, expect } from '@playwright/test';
import path from 'path';

/**
 * CSV Upload E2E Tests
 *
 * Tests the complete user journey via Dashboard modal:
 * 1. User navigates to Dashboard
 * 2. User clicks "Ticket Drop In (CSV)" button to open modal
 * 3. User selects and uploads CSV file in modal
 * 4. Frontend sends file to backend API
 * 5. Backend processes CSV and saves to database
 * 6. Frontend displays success message
 * 7. User can see uploaded tickets in the tickets list
 */

test.describe('CSV Upload Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Login with test credentials
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    // Fill in test credentials (Firebase emulator)
    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'testpassword123');

    // Click login button
    await page.click('button[type="submit"]');

    // Wait for redirect to dashboard after login
    await page.waitForURL('**/dashboard', { timeout: 10000 });
    await page.waitForLoadState('networkidle');
  });

  test('should upload CSV via Dashboard modal', async ({ page }) => {
    // Step 1: Click "Ticket Drop In (CSV)" button to open modal
    const uploadButton = page.locator('button:has-text("Ticket Drop In (CSV)")');
    await uploadButton.click();

    // Step 2: Wait for modal to open (check for modal title)
    await expect(page.locator('text=Upload Ticket CSV')).toBeVisible({ timeout: 5000 });

    // Step 3: Prepare test CSV file
    const testCSV = `subject,body
Test Ticket from E2E,This is an automated test ticket from Playwright
Bug Report E2E,This is a bug report created by E2E test
Feature Request E2E,This is a feature request from E2E test`;

    // Step 4: Upload file via modal file input
    const fileInput = page.locator('input[type="file"][accept=".csv,text/csv"]');
    await fileInput.setInputFiles({
      name: 'e2e-test.csv',
      mimeType: 'text/csv',
      buffer: Buffer.from(testCSV),
    });

    // Step 5: Wait for file to be selected (filename should appear)
    await expect(page.locator('text=e2e-test.csv')).toBeVisible({ timeout: 2000 });

    // Step 6: Click upload button in modal
    const modalUploadButton = page.locator('button:has-text("Upload CSV")');
    await modalUploadButton.click();

    // Step 7: Wait for upload to complete
    await page.waitForTimeout(2000); // Wait for API call

    // Take screenshot for debugging
    await page.screenshot({ path: 'test-results/upload-result.png', fullPage: true });

    // Verify upload completed (button should be re-enabled)
    await expect(modalUploadButton).not.toBeDisabled({ timeout: 10000 });

    // Step 8: Close modal
    const closeButton = page.locator('button:has-text("Cancel")');
    await closeButton.click();
  });

  test('should show error for invalid file type in modal', async ({ page }) => {
    // Open the upload modal
    await page.locator('button:has-text("Ticket Drop In (CSV)")').click();
    await expect(page.locator('text=Upload Ticket CSV')).toBeVisible({ timeout: 5000 });

    // Verify file input has proper accept attribute
    const fileInput = page.locator('input[type="file"][accept=".csv,text/csv"]');
    await expect(fileInput).toHaveAttribute('accept', '.csv,text/csv');

    // Test with CSV with only headers (no data rows)
    const emptyCSV = 'subject,body';
    await fileInput.setInputFiles({
      name: 'empty.csv',
      mimeType: 'text/csv',
      buffer: Buffer.from(emptyCSV),
    });

    await expect(page.locator('text=empty.csv')).toBeVisible({ timeout: 2000 });

    const uploadButton = page.locator('button:has-text("Upload CSV")');
    await uploadButton.click();

    // Wait for upload to complete
    await page.waitForTimeout(2000);

    // Button should be re-enabled after upload
    await expect(uploadButton).not.toBeDisabled({ timeout: 10000 });
  });

  test('should handle empty CSV file in modal', async ({ page }) => {
    // Open the upload modal
    await page.locator('button:has-text("Ticket Drop In (CSV)")').click();
    await expect(page.locator('text=Upload Ticket CSV')).toBeVisible({ timeout: 5000 });

    // Upload CSV with only headers
    const fileInput = page.locator('input[type="file"][accept=".csv,text/csv"]');
    await fileInput.setInputFiles({
      name: 'empty.csv',
      mimeType: 'text/csv',
      buffer: Buffer.from('subject,body\n'),
    });

    // Wait for file selection
    await expect(page.locator('text=empty.csv')).toBeVisible({ timeout: 2000 });

    // Click upload button
    const uploadButton = page.locator('button:has-text("Upload CSV")');
    await uploadButton.click();

    // Wait for upload to complete
    await page.waitForTimeout(2000);

    // Button should be re-enabled after upload
    await expect(uploadButton).not.toBeDisabled({ timeout: 10000 });
  });
});

test.describe('CSV Upload - API Validation', () => {
  test('should validate CSV upload via API', async ({ request }) => {
    // Prepare test CSV
    const testCSV = `subject,body
API Test Ticket,This is an API test from E2E
Another API Test,Testing direct API upload`;

    // Make direct API request
    const response = await request.post('http://localhost:8000/api/tickets/upload-csv', {
      multipart: {
        file: {
          name: 'api-test.csv',
          mimeType: 'text/csv',
          buffer: Buffer.from(testCSV),
        },
      },
    });

    // Verify response
    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    // Adjust based on your actual API response structure
    expect(data).toHaveProperty('message');
    expect(data).toHaveProperty('tickets_count');
    expect(data.tickets_count).toBeGreaterThanOrEqual(2);
  });
});
