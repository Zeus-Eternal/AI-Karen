import { test, expect, Page } from '@playwright/test';

/**
 * End-to-End Tests for Network Failure Scenarios
 * Tests application resilience under various network conditions
 */

// Helper functions
async function loginUser(page: Page) {
  await page.goto('/login');
  await page.fill('[data-testid="email-input"]', 'test@example.com');
  await page.fill('[data-testid="password-input"]', 'testpassword123');
  await page.click('[data-testid="login-button"]');
  await page.waitForURL('/chat');
}

async function simulateNetworkFailure(page: Page, pattern: string = '**/api/**') {
  await page.route(pattern, route => {
    route.abort('failed');
  });
}

async function simulateSlowNetwork(page: Page, delay: number = 5000) {
  await page.route('**/api/**', async route => {
    await new Promise(resolve => setTimeout(resolve, delay));
    route.continue();
  });
}

async function simulateIntermittentNetwork(page: Page) {
  let requestCount = 0;
  await page.route('**/api/**', route => {
    requestCount++;
    if (requestCount % 3 === 0) {
      route.abort('failed');
    } else {
      route.continue();
    }
  });
}

test.describe('Network Failure Scenarios', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('Complete network failure during chat', async ({ page }) => {
    await loginUser(page);
    
    // Start a normal conversation
    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill('Hello, this should work');
    await page.click('[data-testid="send-button"]');
    
    // Wait for successful response
    await page.waitForSelector('[data-testid="assistant-message"]', { timeout: 10000 });
    
    // Simulate complete network failure
    await simulateNetworkFailure(page);
    
    // Try to send another message
    await messageInput.fill('This message will fail');
    await page.click('[data-testid="send-button"]');
    
    // Verify error handling
    await expect(page.locator('[data-testid="network-error-banner"]')).toBeVisible();
    await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();
    await expect(page.locator('[data-testid="offline-indicator"]')).toBeVisible();
    
    // Verify message is queued for retry
    await expect(page.locator('[data-testid="queued-message"]')).toContainText('This message will fail');
    
    // Restore network
    await page.unroute('**/api/**');
    
    // Retry should work
    await page.click('[data-testid="retry-button"]');
    await page.waitForSelector('[data-testid="assistant-message"]', { timeout: 10000 });
    
    // Verify recovery
    await expect(page.locator('[data-testid="network-error-banner"]')).not.toBeVisible();
    await expect(page.locator('[data-testid="offline-indicator"]')).not.toBeVisible();
  }); 
 test('Slow network with timeout handling', async ({ page }) => {
    await loginUser(page);
    
    // Simulate very slow network
    await simulateSlowNetwork(page, 8000);
    
    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill('This will be slow');
    await page.click('[data-testid="send-button"]');
    
    // Verify loading states
    await expect(page.locator('[data-testid="sending-indicator"]')).toBeVisible();
    await expect(page.locator('[data-testid="slow-network-warning"]')).toBeVisible();
    
    // Wait for timeout
    await expect(page.locator('[data-testid="timeout-error"]')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();
    
    // Remove slow network simulation
    await page.unroute('**/api/**');
    
    // Retry should be faster
    await page.click('[data-testid="retry-button"]');
    await page.waitForSelector('[data-testid="assistant-message"]', { timeout: 5000 });
  });

  test('Intermittent network connectivity', async ({ page }) => {
    await loginUser(page);
    
    // Simulate intermittent network (every 3rd request fails)
    await simulateIntermittentNetwork(page);
    
    const messageInput = page.locator('[data-testid="message-input"]');
    
    // Send multiple messages
    for (let i = 1; i <= 5; i++) {
      await messageInput.fill(`Message ${i}`);
      await page.click('[data-testid="send-button"]');
      
      // Some will succeed, some will fail
      try {
        await page.waitForSelector('[data-testid="assistant-message"]', { timeout: 3000 });
      } catch {
        // Expected for failed requests
        await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();
        await page.click('[data-testid="retry-button"]');
        await page.waitForSelector('[data-testid="assistant-message"]', { timeout: 5000 });
      }
    }
    
    // Verify all messages eventually succeeded
    await expect(page.locator('[data-testid="user-message"]')).toHaveCount(5);
    await expect(page.locator('[data-testid="assistant-message"]')).toHaveCount(5);
  });

  test('Network failure during streaming response', async ({ page }) => {
    await loginUser(page);
    
    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill('Tell me a long story');
    await page.click('[data-testid="send-button"]');
    
    // Wait for streaming to start
    await expect(page.locator('[data-testid="streaming-indicator"]')).toBeVisible();
    
    // Simulate network failure mid-stream
    await page.waitForTimeout(2000); // Let some content stream
    await simulateNetworkFailure(page, '**/api/chat/stream/**');
    
    // Verify partial content is preserved
    const partialResponse = page.locator('[data-testid="assistant-message"]').last();
    const partialText = await partialResponse.textContent();
    expect(partialText).toBeTruthy();
    
    // Verify error state
    await expect(page.locator('[data-testid="stream-interrupted-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="continue-response-button"]')).toBeVisible();
    
    // Restore network and continue
    await page.unroute('**/api/chat/stream/**');
    await page.click('[data-testid="continue-response-button"]');
    
    // Verify response continues from where it left off
    await page.waitForSelector('[data-testid="streaming-indicator"]', { state: 'hidden' });
    const finalText = await partialResponse.textContent();
    expect(finalText!.length).toBeGreaterThan(partialText!.length);
  });

  test('Authentication failure during session', async ({ page }) => {
    await loginUser(page);
    
    // Simulate auth token expiry
    await page.route('**/api/**', route => {
      route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Token expired' })
      });
    });
    
    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill('This should trigger auth error');
    await page.click('[data-testid="send-button"]');
    
    // Verify auth error handling
    await expect(page.locator('[data-testid="auth-expired-modal"]')).toBeVisible();
    await expect(page.locator('[data-testid="relogin-button"]')).toBeVisible();
    
    // Click relogin
    await page.click('[data-testid="relogin-button"]');
    
    // Should redirect to login
    await expect(page).toHaveURL('/login');
    await expect(page.locator('[data-testid="session-expired-message"]')).toBeVisible();
  });  test('C
ORS and cross-origin issues', async ({ page }) => {
    await loginUser(page);
    
    // Simulate CORS error
    await page.route('**/api/**', route => {
      route.fulfill({
        status: 0, // CORS error typically shows as status 0
        body: ''
      });
    });
    
    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill('This will trigger CORS error');
    await page.click('[data-testid="send-button"]');
    
    // Verify CORS error handling
    await expect(page.locator('[data-testid="cors-error-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="cors-help-link"]')).toBeVisible();
    
    // Verify helpful error message
    const errorMessage = page.locator('[data-testid="cors-error-message"]');
    await expect(errorMessage).toContainText('cross-origin');
    await expect(errorMessage).toContainText('CORS');
  });

  test('Rate limiting and throttling', async ({ page }) => {
    await loginUser(page);
    
    // Simulate rate limiting
    await page.route('**/api/chat/**', route => {
      route.fulfill({
        status: 429,
        contentType: 'application/json',
        headers: {
          'Retry-After': '60'
        },
        body: JSON.stringify({ 
          error: 'Rate limit exceeded',
          retryAfter: 60
        })
      });
    });
    
    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill('This will be rate limited');
    await page.click('[data-testid="send-button"]');
    
    // Verify rate limit handling
    await expect(page.locator('[data-testid="rate-limit-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="rate-limit-countdown"]')).toBeVisible();
    
    // Verify retry button is disabled during cooldown
    const retryButton = page.locator('[data-testid="retry-button"]');
    await expect(retryButton).toBeDisabled();
    
    // Verify countdown display
    await expect(page.locator('[data-testid="rate-limit-countdown"]')).toContainText('60');
  });

  test('Server error recovery (5xx errors)', async ({ page }) => {
    await loginUser(page);
    
    // Simulate server error
    await page.route('**/api/chat/**', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ 
          error: 'Internal server error',
          requestId: 'req-123'
        })
      });
    });
    
    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill('This will cause server error');
    await page.click('[data-testid="send-button"]');
    
    // Verify server error handling
    await expect(page.locator('[data-testid="server-error-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-request-id"]')).toContainText('req-123');
    await expect(page.locator('[data-testid="report-error-button"]')).toBeVisible();
    
    // Test error reporting
    await page.click('[data-testid="report-error-button"]');
    await expect(page.locator('[data-testid="error-report-modal"]')).toBeVisible();
    
    // Fill error report
    await page.fill('[data-testid="error-description"]', 'Server returned 500 error');
    await page.click('[data-testid="submit-error-report"]');
    
    await expect(page.locator('[data-testid="error-report-success"]')).toBeVisible();
  });

  test('Offline mode and service worker', async ({ page }) => {
    await loginUser(page);
    
    // Send a successful message first
    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill('This works online');
    await page.click('[data-testid="send-button"]');
    await page.waitForSelector('[data-testid="assistant-message"]');
    
    // Go offline
    await page.context().setOffline(true);
    
    // Try to send another message
    await messageInput.fill('This should work offline');
    await page.click('[data-testid="send-button"]');
    
    // Verify offline mode
    await expect(page.locator('[data-testid="offline-mode-banner"]')).toBeVisible();
    await expect(page.locator('[data-testid="queued-messages-count"]')).toContainText('1');
    
    // Verify message is queued
    await expect(page.locator('[data-testid="queued-message"]')).toContainText('This should work offline');
    
    // Go back online
    await page.context().setOffline(false);
    
    // Verify automatic sync
    await expect(page.locator('[data-testid="syncing-indicator"]')).toBeVisible();
    await page.waitForSelector('[data-testid="assistant-message"]', { timeout: 10000 });
    
    // Verify offline banner disappears
    await expect(page.locator('[data-testid="offline-mode-banner"]')).not.toBeVisible();
    await expect(page.locator('[data-testid="queued-messages-count"]')).toContainText('0');
  });
});