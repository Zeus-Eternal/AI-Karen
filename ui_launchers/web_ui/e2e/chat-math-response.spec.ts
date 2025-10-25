import { test, expect } from '@playwright/test';

const ADMIN_EMAIL = process.env.PLAYWRIGHT_ADMIN_EMAIL || 'admin@example.com';
const ADMIN_PASSWORD = process.env.PLAYWRIGHT_ADMIN_PASSWORD || 'password123';

test.describe('Chat math response', () => {
  test('returns 8 for 4+4 prompt', async ({ page }) => {
    // Navigate to login page
    await page.goto('/login');

    await page.fill('input#email', ADMIN_EMAIL);
    await page.fill('input#password', ADMIN_PASSWORD);

    await Promise.all([
      page.waitForURL((url) => url.pathname !== '/login', { timeout: 60_000 }),
      page.click('[data-testid="submit-button"]'),
    ]);

    // Ensure chat interface is visible
    await page.waitForSelector('#chat-input form', { timeout: 30_000 });

    // Send the math question
    const chatInput = page.locator('#chat-input input[aria-label="Type your message"]');
    await chatInput.fill('What is 4 + 4?');

    await Promise.all([
      page.waitForResponse(
        (response) =>
          response.url().includes('/api/chat') && response.request().method() === 'POST',
        { timeout: 60_000 }
      ).catch(() => {}),
      page.click('#chat-input button[type="submit"]'),
    ]);

    // Wait for assistant response containing the expected answer
    await expect
      .poll(
        async () => {
          const messages = await page.$$eval('[role="article"] p', (elements) =>
            elements.map((el) => el.textContent || '')
          );
          return messages.find((text) => /\b8\b/.test(text));
        },
        { timeout: 60_000 }
      )
      .not.toBeUndefined();
  });
});
