import { test, expect, Page } from '@playwright/test';

/**
 * Visual Regression Tests
 * Tests UI consistency and visual changes across different states and interactions
 */

// Helper functions
async function loginUser(page: Page) {
  await page.goto('/login');
  await page.fill('[data-testid="email-input"]', 'test@example.com');
  await page.fill('[data-testid="password-input"]', 'testpassword123');
  await page.click('[data-testid="login-button"]');
  await page.waitForURL('/chat');
}

async function setupMockResponses(page: Page) {
  // Mock API responses for consistent visual testing
  await page.route('**/api/chat/**', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        message: 'This is a consistent mock response for visual testing purposes.',
        id: 'mock-response-id',
        timestamp: '2024-01-01T00:00:00Z'
      })
    });
  });
}

test.describe('Visual Regression Tests', () => {
  test.beforeEach(async ({ page }) => {
    await setupMockResponses(page);
  });

  test('Login page visual consistency', async ({ page }) => {
    await page.goto('/login');
    
    // Wait for page to fully load
    await page.waitForLoadState('networkidle');
    
    // Take screenshot of login page
    await expect(page).toHaveScreenshot('login-page.png');
    
    // Test with validation errors
    await page.click('[data-testid="login-button"]');
    await page.waitForSelector('[data-testid="email-error"]');
    
    await expect(page).toHaveScreenshot('login-page-with-errors.png');
    
    // Test loading state
    await page.fill('[data-testid="email-input"]', 'test@example.com');
    await page.fill('[data-testid="password-input"]', 'testpassword123');
    
    // Mock slow login to capture loading state
    await page.route('**/api/auth/login', async route => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ token: 'mock-token', user: { id: '1', email: 'test@example.com' } })
      });
    });
    
    await page.click('[data-testid="login-button"]');
    await page.waitForSelector('[data-testid="login-loading"]');
    
    await expect(page).toHaveScreenshot('login-page-loading.png');
  });

  test('Chat interface visual consistency', async ({ page }) => {
    await loginUser(page);
    
    // Empty chat state
    await expect(page).toHaveScreenshot('chat-empty-state.png');
    
    // Send a message
    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill('Hello, this is a test message for visual regression testing');
    await page.click('[data-testid="send-button"]');
    
    // Chat with user message
    await expect(page).toHaveScreenshot('chat-with-user-message.png');
    
    // Wait for AI response
    await page.waitForSelector('[data-testid="assistant-message"]');
    
    // Chat with conversation
    await expect(page).toHaveScreenshot('chat-with-conversation.png');
  });  te
st('Theme variations visual consistency', async ({ page }) => {
    await loginUser(page);
    
    // Light theme
    await expect(page).toHaveScreenshot('chat-light-theme.png');
    
    // Switch to dark theme
    await page.click('[data-testid="settings-button"]');
    await page.click('[data-testid="theme-selector"]');
    await page.click('[data-testid="dark-theme-option"]');
    await page.click('[data-testid="close-settings-button"]');
    
    // Dark theme
    await expect(page).toHaveScreenshot('chat-dark-theme.png');
    
    // High contrast theme
    await page.click('[data-testid="settings-button"]');
    await page.click('[data-testid="theme-selector"]');
    await page.click('[data-testid="high-contrast-theme-option"]');
    await page.click('[data-testid="close-settings-button"]');
    
    await expect(page).toHaveScreenshot('chat-high-contrast-theme.png');
  });

  test('Responsive design visual consistency', async ({ page }) => {
    await loginUser(page);
    
    // Send a message for content
    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill('Test message for responsive design');
    await page.click('[data-testid="send-button"]');
    await page.waitForSelector('[data-testid="assistant-message"]');
    
    // Desktop view (default)
    await expect(page).toHaveScreenshot('chat-desktop-view.png');
    
    // Tablet view
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page).toHaveScreenshot('chat-tablet-view.png');
    
    // Mobile view
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page).toHaveScreenshot('chat-mobile-view.png');
    
    // Mobile landscape
    await page.setViewportSize({ width: 667, height: 375 });
    await expect(page).toHaveScreenshot('chat-mobile-landscape.png');
  });

  test('Error states visual consistency', async ({ page }) => {
    await loginUser(page);
    
    // Network error state
    await page.route('**/api/chat/**', route => {
      route.abort('failed');
    });
    
    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill('This will fail');
    await page.click('[data-testid="send-button"]');
    
    await page.waitForSelector('[data-testid="error-message"]');
    await expect(page).toHaveScreenshot('chat-network-error.png');
    
    // Server error state
    await page.unroute('**/api/chat/**');
    await page.route('**/api/chat/**', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' })
      });
    });
    
    await page.click('[data-testid="retry-button"]');
    await page.waitForSelector('[data-testid="server-error-message"]');
    await expect(page).toHaveScreenshot('chat-server-error.png');
    
    // Rate limit error state
    await page.unroute('**/api/chat/**');
    await page.route('**/api/chat/**', route => {
      route.fulfill({
        status: 429,
        contentType: 'application/json',
        headers: { 'Retry-After': '60' },
        body: JSON.stringify({ error: 'Rate limit exceeded' })
      });
    });
    
    await page.click('[data-testid="retry-button"]');
    await page.waitForSelector('[data-testid="rate-limit-error"]');
    await expect(page).toHaveScreenshot('chat-rate-limit-error.png');
  });

  test('Loading states visual consistency', async ({ page }) => {
    await loginUser(page);
    
    // Mock slow response for loading state
    await page.route('**/api/chat/**', async route => {
      await new Promise(resolve => setTimeout(resolve, 2000));
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Response after loading' })
      });
    });
    
    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill('This will show loading state');
    await page.click('[data-testid="send-button"]');
    
    // Capture loading state
    await page.waitForSelector('[data-testid="sending-indicator"]');
    await expect(page).toHaveScreenshot('chat-loading-state.png');
    
    // Capture streaming state
    await page.unroute('**/api/chat/**');
    await page.route('**/api/chat/stream/**', route => {
      // Mock streaming response
      route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: 'data: {"token": "This"}\n\ndata: {"token": " is"}\n\ndata: {"token": " streaming"}\n\n'
      });
    });
    
    await messageInput.fill('Show streaming');
    await page.click('[data-testid="send-button"]');
    await page.waitForSelector('[data-testid="streaming-indicator"]');
    
    await expect(page).toHaveScreenshot('chat-streaming-state.png');
  }); 
 test('Component states visual consistency', async ({ page }) => {
    await loginUser(page);
    
    // Send message with code block
    await page.route('**/api/chat/**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'Here is a code example:\n\n```javascript\nfunction hello() {\n  console.log("Hello, world!");\n}\n```\n\nThis demonstrates syntax highlighting.'
        })
      });
    });
    
    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill('Show me some code');
    await page.click('[data-testid="send-button"]');
    await page.waitForSelector('[data-testid="code-block"]');
    
    // Code block visual
    await expect(page).toHaveScreenshot('chat-with-code-block.png');
    
    // Hover states
    await page.locator('[data-testid="code-block"]').hover();
    await expect(page).toHaveScreenshot('chat-code-block-hover.png');
    
    // Copy button clicked
    await page.click('[data-testid="copy-button"]');
    await page.waitForSelector('[data-testid="copy-success-toast"]');
    await expect(page).toHaveScreenshot('chat-copy-success.png');
  });

  test('Modal and overlay visual consistency', async ({ page }) => {
    await loginUser(page);
    
    // Settings modal
    await page.click('[data-testid="settings-button"]');
    await page.waitForSelector('[data-testid="settings-modal"]');
    await expect(page).toHaveScreenshot('settings-modal.png');
    
    // Close settings
    await page.click('[data-testid="close-settings-button"]');
    
    // Conversation list modal
    await page.click('[data-testid="conversation-list-button"]');
    await page.waitForSelector('[data-testid="conversation-list-modal"]');
    await expect(page).toHaveScreenshot('conversation-list-modal.png');
    
    // Close conversation list
    await page.click('[data-testid="close-conversation-list"]');
    
    // Help modal
    await page.click('[data-testid="help-button"]');
    await page.waitForSelector('[data-testid="help-modal"]');
    await expect(page).toHaveScreenshot('help-modal.png');
  });

  test('Accessibility visual indicators', async ({ page }) => {
    await loginUser(page);
    
    // Focus states
    await page.keyboard.press('Tab'); // Focus on message input
    await expect(page).toHaveScreenshot('chat-input-focused.png');
    
    await page.keyboard.press('Tab'); // Focus on send button
    await expect(page).toHaveScreenshot('chat-send-button-focused.png');
    
    // High contrast mode focus
    await page.click('[data-testid="settings-button"]');
    await page.click('[data-testid="theme-selector"]');
    await page.click('[data-testid="high-contrast-theme-option"]');
    await page.click('[data-testid="close-settings-button"]');
    
    await page.keyboard.press('Tab'); // Focus on message input in high contrast
    await expect(page).toHaveScreenshot('chat-input-focused-high-contrast.png');
  });

  test('Animation states visual consistency', async ({ page }) => {
    await loginUser(page);
    
    // Test reduced motion preference
    await page.emulateMedia({ reducedMotion: 'reduce' });
    
    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill('Test with reduced motion');
    await page.click('[data-testid="send-button"]');
    
    await expect(page).toHaveScreenshot('chat-reduced-motion.png');
    
    // Test normal motion
    await page.emulateMedia({ reducedMotion: 'no-preference' });
    
    await messageInput.fill('Test with normal motion');
    await page.click('[data-testid="send-button"]');
    
    await expect(page).toHaveScreenshot('chat-normal-motion.png');
  });

  test('Print styles visual consistency', async ({ page }) => {
    await loginUser(page);
    
    // Send some messages for content
    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill('First message for printing');
    await page.click('[data-testid="send-button"]');
    await page.waitForSelector('[data-testid="assistant-message"]');
    
    await messageInput.fill('Second message for printing');
    await page.click('[data-testid="send-button"]');
    await page.waitForSelector('[data-testid="assistant-message"]');
    
    // Emulate print media
    await page.emulateMedia({ media: 'print' });
    
    await expect(page).toHaveScreenshot('chat-print-view.png');
  });
});