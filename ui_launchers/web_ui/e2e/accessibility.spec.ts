import { test, expect, Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

/**
 * Accessibility End-to-End Tests
 * Tests WCAG compliance, keyboard navigation, and screen reader compatibility
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
  await page.route('**/api/chat/**', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        message: 'This is a mock response for accessibility testing.',
        id: 'mock-response-id'
      })
    });
  });
}

test.describe('Accessibility Tests', () => {
  test.beforeEach(async ({ page }) => {
    await setupMockResponses(page);
  });

  test('Login page accessibility compliance', async ({ page }) => {
    await page.goto('/login');
    
    // Run axe accessibility scan
    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();
    expect(accessibilityScanResults.violations).toEqual([]);
    
    // Test keyboard navigation
    await page.keyboard.press('Tab'); // Email input
    await expect(page.locator('[data-testid="email-input"]')).toBeFocused();
    
    await page.keyboard.press('Tab'); // Password input
    await expect(page.locator('[data-testid="password-input"]')).toBeFocused();
    
    await page.keyboard.press('Tab'); // Login button
    await expect(page.locator('[data-testid="login-button"]')).toBeFocused();
    
    // Test form submission with Enter key
    await page.fill('[data-testid="email-input"]', 'test@example.com');
    await page.fill('[data-testid="password-input"]', 'testpassword123');
    await page.keyboard.press('Enter');
    
    await page.waitForURL('/chat');
  });

  test('Chat interface accessibility compliance', async ({ page }) => {
    await loginUser(page);
    
    // Run axe accessibility scan on chat interface
    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();
    expect(accessibilityScanResults.violations).toEqual([]);
    
    // Test ARIA live regions for streaming content
    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill('Test message for accessibility');
    await page.keyboard.press('Enter');
    
    // Verify ARIA live region updates
    const liveRegion = page.locator('[aria-live="polite"]');
    await expect(liveRegion).toBeVisible();
    
    // Wait for response and verify it's announced
    await page.waitForSelector('[data-testid="assistant-message"]');
    
    // Test message list accessibility
    const messageList = page.locator('[data-testid="message-list"]');
    await expect(messageList).toHaveAttribute('role', 'log');
    await expect(messageList).toHaveAttribute('aria-label', /conversation history/i);
  });  test('
Keyboard navigation throughout chat interface', async ({ page }) => {
    await loginUser(page);
    
    // Test Tab order
    const expectedTabOrder = [
      '[data-testid="message-input"]',
      '[data-testid="send-button"]',
      '[data-testid="voice-input-button"]',
      '[data-testid="file-upload-button"]',
      '[data-testid="settings-button"]',
      '[data-testid="conversation-list-button"]'
    ];
    
    for (const selector of expectedTabOrder) {
      await page.keyboard.press('Tab');
      await expect(page.locator(selector)).toBeFocused();
    }
    
    // Test Shift+Tab reverse navigation
    for (let i = expectedTabOrder.length - 2; i >= 0; i--) {
      await page.keyboard.press('Shift+Tab');
      await expect(page.locator(expectedTabOrder[i])).toBeFocused();
    }
    
    // Test keyboard shortcuts
    await page.keyboard.press('Control+Enter'); // Should send message
    await page.keyboard.press('Escape'); // Should clear input or close modals
    
    // Test message input keyboard behavior
    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.focus();
    
    // Enter should send message
    await messageInput.fill('Test message');
    await page.keyboard.press('Enter');
    await page.waitForSelector('[data-testid="user-message"]');
    
    // Shift+Enter should add new line
    await messageInput.fill('Line 1');
    await page.keyboard.press('Shift+Enter');
    await messageInput.type('Line 2');
    
    const inputValue = await messageInput.inputValue();
    expect(inputValue).toContain('\n');
  });

  test('Screen reader compatibility', async ({ page }) => {
    await loginUser(page);
    
    // Test message announcements
    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill('Screen reader test message');
    await page.keyboard.press('Enter');
    
    // Verify user message has proper ARIA labels
    const userMessage = page.locator('[data-testid="user-message"]').last();
    await expect(userMessage).toHaveAttribute('role', 'article');
    await expect(userMessage).toHaveAttribute('aria-label', /user message/i);
    
    // Wait for AI response
    await page.waitForSelector('[data-testid="assistant-message"]');
    
    // Verify AI message has proper ARIA labels
    const aiMessage = page.locator('[data-testid="assistant-message"]').last();
    await expect(aiMessage).toHaveAttribute('role', 'article');
    await expect(aiMessage).toHaveAttribute('aria-label', /assistant message/i);
    
    // Test streaming content announcements
    await page.route('**/api/chat/stream/**', route => {
      route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: 'data: {"token": "Streaming"}\n\ndata: {"token": " content"}\n\ndata: {"token": " test"}\n\n'
      });
    });
    
    await messageInput.fill('Test streaming');
    await page.keyboard.press('Enter');
    
    // Verify streaming indicator is announced
    const streamingIndicator = page.locator('[data-testid="streaming-indicator"]');
    await expect(streamingIndicator).toHaveAttribute('aria-live', 'polite');
    await expect(streamingIndicator).toHaveAttribute('aria-label', /generating response/i);
  });

  test('Focus management in modals and overlays', async ({ page }) => {
    await loginUser(page);
    
    // Test settings modal focus management
    await page.click('[data-testid="settings-button"]');
    await page.waitForSelector('[data-testid="settings-modal"]');
    
    // Focus should be trapped in modal
    const modal = page.locator('[data-testid="settings-modal"]');
    await expect(modal).toHaveAttribute('role', 'dialog');
    await expect(modal).toHaveAttribute('aria-modal', 'true');
    
    // First focusable element should be focused
    const firstFocusable = modal.locator('button, input, select, textarea, [tabindex]:not([tabindex="-1"])').first();
    await expect(firstFocusable).toBeFocused();
    
    // Tab should cycle within modal
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    
    // Escape should close modal and restore focus
    await page.keyboard.press('Escape');
    await expect(modal).not.toBeVisible();
    await expect(page.locator('[data-testid="settings-button"]')).toBeFocused();
    
    // Test conversation list modal
    await page.click('[data-testid="conversation-list-button"]');
    await page.waitForSelector('[data-testid="conversation-list-modal"]');
    
    const conversationModal = page.locator('[data-testid="conversation-list-modal"]');
    await expect(conversationModal).toHaveAttribute('role', 'dialog');
    
    // Close with Escape
    await page.keyboard.press('Escape');
    await expect(conversationModal).not.toBeVisible();
    await expect(page.locator('[data-testid="conversation-list-button"]')).toBeFocused();
  });  test
('Color contrast and visual accessibility', async ({ page }) => {
    await loginUser(page);
    
    // Test different themes for contrast compliance
    const themes = ['light', 'dark', 'high-contrast'];
    
    for (const theme of themes) {
      // Switch theme
      await page.click('[data-testid="settings-button"]');
      await page.click('[data-testid="theme-selector"]');
      await page.click(`[data-testid="${theme}-theme-option"]`);
      await page.click('[data-testid="close-settings-button"]');
      
      // Run accessibility scan for each theme
      const accessibilityScanResults = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
        .analyze();
      
      expect(accessibilityScanResults.violations).toEqual([]);
    }
    
    // Test focus indicators visibility
    await page.keyboard.press('Tab'); // Focus message input
    
    // Verify focus outline is visible
    const focusedElement = page.locator('[data-testid="message-input"]');
    const focusOutline = await focusedElement.evaluate(el => {
      const styles = window.getComputedStyle(el);
      return {
        outline: styles.outline,
        outlineWidth: styles.outlineWidth,
        outlineColor: styles.outlineColor
      };
    });
    
    expect(focusOutline.outlineWidth).not.toBe('0px');
    expect(focusOutline.outline).not.toBe('none');
  });

  test('Reduced motion preferences', async ({ page }) => {
    // Test with reduced motion preference
    await page.emulateMedia({ reducedMotion: 'reduce' });
    await loginUser(page);
    
    // Send a message to test animations
    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill('Test reduced motion');
    await page.keyboard.press('Enter');
    
    // Verify animations are reduced/disabled
    const userMessage = page.locator('[data-testid="user-message"]').last();
    const animationDuration = await userMessage.evaluate(el => {
      const styles = window.getComputedStyle(el);
      return styles.animationDuration;
    });
    
    // Should be 0s or very short for reduced motion
    expect(parseFloat(animationDuration)).toBeLessThanOrEqual(0.1);
    
    // Test with normal motion preference
    await page.emulateMedia({ reducedMotion: 'no-preference' });
    
    await messageInput.fill('Test normal motion');
    await page.keyboard.press('Enter');
    
    // Run accessibility scan to ensure no violations with animations
    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('Form validation and error announcements', async ({ page }) => {
    await page.goto('/login');
    
    // Test form validation accessibility
    await page.click('[data-testid="login-button"]'); // Submit empty form
    
    // Verify error messages are properly announced
    const emailError = page.locator('[data-testid="email-error"]');
    await expect(emailError).toBeVisible();
    await expect(emailError).toHaveAttribute('role', 'alert');
    await expect(emailError).toHaveAttribute('aria-live', 'assertive');
    
    const passwordError = page.locator('[data-testid="password-error"]');
    await expect(passwordError).toBeVisible();
    await expect(passwordError).toHaveAttribute('role', 'alert');
    
    // Test field association with errors
    const emailInput = page.locator('[data-testid="email-input"]');
    const emailErrorId = await emailError.getAttribute('id');
    await expect(emailInput).toHaveAttribute('aria-describedby', emailErrorId!);
    
    // Test error correction
    await emailInput.fill('test@example.com');
    await expect(emailError).not.toBeVisible();
    
    // Verify aria-describedby is updated
    const describedBy = await emailInput.getAttribute('aria-describedby');
    expect(describedBy).not.toContain(emailErrorId!);
  });

  test('Dynamic content and live regions', async ({ page }) => {
    await loginUser(page);
    
    // Test toast notifications accessibility
    await page.route('**/api/chat/**', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Server error' })
      });
    });
    
    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.fill('This will cause an error');
    await page.keyboard.press('Enter');
    
    // Verify error toast is announced
    const errorToast = page.locator('[data-testid="error-toast"]');
    await expect(errorToast).toBeVisible();
    await expect(errorToast).toHaveAttribute('role', 'alert');
    await expect(errorToast).toHaveAttribute('aria-live', 'assertive');
    
    // Test success notifications
    await page.unroute('**/api/chat/**');
    await setupMockResponses(page);
    
    await page.click('[data-testid="retry-button"]');
    
    const successToast = page.locator('[data-testid="success-toast"]');
    await expect(successToast).toHaveAttribute('aria-live', 'polite');
  });

  test('Mobile accessibility', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await loginUser(page);
    
    // Run accessibility scan on mobile
    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();
    expect(accessibilityScanResults.violations).toEqual([]);
    
    // Test touch targets are large enough (44px minimum)
    const touchTargets = [
      '[data-testid="send-button"]',
      '[data-testid="voice-input-button"]',
      '[data-testid="file-upload-button"]',
      '[data-testid="settings-button"]'
    ];
    
    for (const selector of touchTargets) {
      const element = page.locator(selector);
      const boundingBox = await element.boundingBox();
      
      expect(boundingBox!.width).toBeGreaterThanOrEqual(44);
      expect(boundingBox!.height).toBeGreaterThanOrEqual(44);
    }
    
    // Test mobile keyboard navigation
    await page.keyboard.press('Tab');
    await expect(page.locator('[data-testid="message-input"]')).toBeFocused();
    
    // Test mobile-specific interactions
    const messageInput = page.locator('[data-testid="message-input"]');
    await messageInput.tap();
    await messageInput.fill('Mobile accessibility test');
    
    // Test send button tap
    await page.locator('[data-testid="send-button"]').tap();
    await page.waitForSelector('[data-testid="user-message"]');
  });
});