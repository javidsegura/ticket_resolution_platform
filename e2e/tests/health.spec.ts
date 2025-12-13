import { test, expect } from '@playwright/test';

/**
 * Health Check E2E Tests
 *
 * These tests verify that the frontend and backend are running and communicating.
 */

test.describe('Health Check', () => {
  test('should load the homepage', async ({ page }) => {
    // Navigate to the app
    await page.goto('/');

    // Verify page loaded (adjust selector based on your actual homepage)
    await expect(page).toHaveTitle(/AI Ticket Platform/i);
  });

  test('should verify backend API is accessible', async ({ request }) => {
    // Make API request directly to backend health endpoint
    const response = await request.get('http://localhost:8000/api/health/ping');

    // Verify response
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data).toEqual({ response: 'pong' });
  });

  test('should display health status in UI', async ({ page }) => {
    // Navigate to health or dashboard page (adjust route as needed)
    await page.goto('/');

    // Wait for page to be fully loaded
    await page.waitForLoadState('networkidle');

    // Verify the app loaded successfully
    // Adjust this selector to match your actual UI
    const content = await page.textContent('body');
    expect(content).toBeTruthy();
  });
});
