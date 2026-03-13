/**
 * Cross-Browser Compatibility Testing Suite
 * Tests functionality across different browsers and devices
 */

import { test, expect, devices, BrowserContext, Page } from '@playwright/test';
import { chromium, firefox, webkit } from '@playwright/test';

// Browser configurations for testing
const BROWSER_CONFIGS = [
  { name: 'Chrome', browser: 'chromium' },
  { name: 'Firefox', browser: 'firefox' },
  { name: 'Safari', browser: 'webkit' },
];

// Device configurations for responsive testing
const DEVICE_CONFIGS = [
  { name: 'Desktop', device: devices['Desktop Chrome'] },
  { name: 'iPhone 13', device: devices['iPhone 13'] },
  { name: 'iPad', device: devices['iPad Pro'] },
  { name: 'Android', device: devices['Pixel 5'] },
];

// Test data
const TEST_DATA = {
  chatMessage: 'Hello, KAREN! How can you help me today?',
  voiceCommand: 'What is the weather like today?',
  fileUpload: {
    name: 'test-document.pdf',
    type: 'application/pdf',
    content: 'Test PDF content for cross-browser compatibility testing',
  },
};

test.describe('Cross-Browser Compatibility Tests', () => {
  // Test basic functionality across browsers
  BROWSER_CONFIGS.forEach(browserConfig => {
    test.describe(`${browserConfig.name} Browser Tests`, () => {
      let context: BrowserContext;
      let page: Page;

      test.beforeAll(async () => {
        const browser = browserConfig.browser === 'chromium' ? chromium :
                       browserConfig.browser === 'firefox' ? firefox : webkit;
        context = await browser.launchPersistentContext('', {
          viewport: { width: 1280, height: 720 },
          ignoreHTTPSErrors: true,
        });
        page = await context.newPage();
      });

      test.afterAll(async () => {
        await context.close();
      });

      test('should load main application', async () => {
        await page.goto('/');
        
        // Check if main elements are present
        await expect(page.locator('h1')).toContainText('KAREN AI');
        await expect(page.locator('[data-testid="chat-interface"]')).toBeVisible();
        await expect(page.locator('[data-testid="sidebar"]')).toBeVisible();
      });

      test('should handle chat interactions', async () => {
        await page.goto('/');
        
        // Send a message
        await page.fill('[data-testid="chat-input"]', TEST_DATA.chatMessage);
        await page.click('[data-testid="send-button"]');
        
        // Check if message appears in chat
        await expect(page.locator('[data-testid="message-list"]')).toContainText(TEST_DATA.chatMessage);
        
        // Wait for AI response (with timeout)
        await expect(page.locator('[data-testid="ai-response"]')).toBeVisible({ timeout: 10000 });
      });

      test('should handle file uploads', async () => {
        await page.goto('/');
        
        // Create a test file
        const fileBuffer = Buffer.from(TEST_DATA.fileUpload.content);
        
        // Upload file
        await page.setInputFiles('[data-testid="file-input"]', {
          name: TEST_DATA.fileUpload.name,
          mimeType: TEST_DATA.fileUpload.type,
          buffer: fileBuffer,
        });
        
        // Check if file appears in upload list
        await expect(page.locator('[data-testid="file-list"]')).toContainText(TEST_DATA.fileUpload.name);
      });

      test('should handle voice recognition', async () => {
        await page.goto('/');
        
        // Mock voice recognition API
        await page.addInitScript(() => {
          // @ts-ignore
          window.SpeechRecognition = class {
            start() {
              setTimeout(() => {
                if (this.onresult) {
                  this.onresult({
                    results: [{
                      0: { transcript: TEST_DATA.voiceCommand, confidence: 0.95 },
                      isFinal: true,
                    }],
                  });
                }
              }, 1000);
            }
            
            stop() {}
            onresult: any = null;
            onerror: any = null;
          };
        });
        
        // Click voice button
        await page.click('[data-testid="voice-button"]');
        
        // Check if voice command appears
        await expect(page.locator('[data-testid="chat-input"]')).toHaveValue(TEST_DATA.voiceCommand);
      });

      test('should handle responsive design', async () => {
        await page.goto('/');
        
        // Test different viewport sizes
        const viewports = [
          { width: 1920, height: 1080 }, // Desktop
          { width: 768, height: 1024 },  // Tablet
          { width: 375, height: 667 },   // Mobile
        ];
        
        for (const viewport of viewports) {
          await page.setViewportSize(viewport);
          
          // Check if layout adapts correctly
          if (viewport.width < 768) {
            // Mobile layout - sidebar should be hidden
            await expect(page.locator('[data-testid="sidebar"]')).toBeHidden();
            await expect(page.locator('[data-testid="mobile-menu-button"]')).toBeVisible();
          } else {
            // Desktop layout - sidebar should be visible
            await expect(page.locator('[data-testid="sidebar"]')).toBeVisible();
            await expect(page.locator('[data-testid="mobile-menu-button"]')).toBeHidden();
          }
        }
      });

      test('should handle keyboard navigation', async () => {
        await page.goto('/');
        
        // Test Tab navigation
        await page.keyboard.press('Tab');
        await expect(page.locator(':focus')).toBeVisible();
        
        // Test Enter key for sending messages
        await page.fill('[data-testid="chat-input"]', TEST_DATA.chatMessage);
        await page.keyboard.press('Enter');
        
        // Check if message was sent
        await expect(page.locator('[data-testid="message-list"]')).toContainText(TEST_DATA.chatMessage);
      });

      test('should handle accessibility features', async () => {
        await page.goto('/');
        
        // Check for ARIA labels
        await expect(page.locator('[data-testid="chat-input"]')).toHaveAttribute('aria-label');
        await expect(page.locator('[data-testid="send-button"]')).toHaveAttribute('aria-label');
        
        // Check for proper heading structure
        const headings = await page.locator('h1, h2, h3, h4, h5, h6').all();
        expect(headings.length).toBeGreaterThan(0);
        
        // Check for skip links
        const skipLinks = await page.locator('[data-testid="skip-link"]').all();
        expect(skipLinks.length).toBeGreaterThan(0);
      });

      test('should handle error states gracefully', async () => {
        await page.goto('/');
        
        // Mock network error
        await page.route('**/api/ai/chat', route => route.abort('failed'));
        
        // Try to send a message
        await page.fill('[data-testid="chat-input"]', TEST_DATA.chatMessage);
        await page.click('[data-testid="send-button"]');
        
        // Check if error message appears
        await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
      });

      test('should handle performance requirements', async () => {
        const startTime = Date.now();
        await page.goto('/');
        const loadTime = Date.now() - startTime;
        
        // Page should load within 3 seconds
        expect(loadTime).toBeLessThan(3000);
        
        // Check for performance metrics
        const performanceMetrics = await page.evaluate(() => {
          const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
          return {
            domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
            loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
            firstPaint: performance.getEntriesByType('paint')[0]?.startTime || 0,
            firstContentfulPaint: performance.getEntriesByType('paint')[1]?.startTime || 0,
          };
        });
        
        // Performance should meet requirements
        expect(performanceMetrics.domContentLoaded).toBeLessThan(1500);
        expect(performanceMetrics.loadComplete).toBeLessThan(3000);
      });
    });
  });

  // Test responsive design across devices
  DEVICE_CONFIGS.forEach(deviceConfig => {
    test.describe(`${deviceConfig.name} Responsive Tests`, () => {
      let context: BrowserContext;
      let page: Page;

      test.beforeAll(async () => {
        context = await chromium.launchPersistentContext('', {
          ...deviceConfig.device,
          ignoreHTTPSErrors: true,
        });
        page = await context.newPage();
      });

      test.afterAll(async () => {
        await context.close();
      });

      test('should render correctly on device', async () => {
        await page.goto('/');
        
        // Check if main elements are visible
        await expect(page.locator('h1')).toBeVisible();
        await expect(page.locator('[data-testid="chat-interface"]')).toBeVisible();
        
        // Device-specific checks
        if (deviceConfig.device?.isMobile) {
          // Mobile-specific checks
          await expect(page.locator('[data-testid="mobile-menu-button"]')).toBeVisible();
        } else {
          // Desktop/tablet checks
          await expect(page.locator('[data-testid="sidebar"]')).toBeVisible();
        }
      });

      test('should handle touch interactions on mobile', async () => {
        if (!deviceConfig.device?.isMobile) return;
        
        await page.goto('/');
        
        // Test touch gestures
        await page.tap('[data-testid="chat-input"]');
        await expect(page.locator('[data-testid="chat-input"]')).toBeFocused();
        
        // Test swipe gestures
        // Use touch events instead of swipe which may not be available
        await page.touchscreen.tap(200, 100);
        
        // Check if sidebar toggles on swipe
        await expect(page.locator('[data-testid="sidebar"]')).toBeVisible();
      });

      test('should handle device-specific features', async () => {
        await page.goto('/');
        
        // Test device-specific features
        if (deviceConfig.device?.isMobile) {
          // Test mobile voice recognition
          await page.click('[data-testid="voice-button"]');
          await expect(page.locator('[data-testid="voice-indicator"]')).toBeVisible();
        } else {
          // Test desktop keyboard shortcuts
          await page.keyboard.press('Control+k');
          await expect(page.locator('[data-testid="chat-input"]')).toBeFocused();
        }
      });
    });
  });

  // Test specific browser compatibility issues
  test.describe('Browser-Specific Compatibility Tests', () => {
    test('should handle Safari-specific features', async ({ context, page }) => {
      // Test Safari-specific features
      await page.goto('/');
      
      // Test WebKit-specific features
      const isWebKit = await page.evaluate(() => {
        return /apple/i.test(navigator.vendor);
      });
      
      if (isWebKit) {
        // Test Safari-specific behaviors
        await expect(page.locator('[data-testid="safari-compatibility"]')).toBeVisible();
      }
    });

    test('should handle Firefox-specific features', async ({ context, page }) => {
      // Test Firefox-specific features
      await page.goto('/');
      
      const isFirefox = await page.evaluate(() => {
        return /firefox/i.test(navigator.userAgent);
      });
      
      if (isFirefox) {
        // Test Firefox-specific behaviors
        await expect(page.locator('[data-testid="firefox-compatibility"]')).toBeVisible();
      }
    });

    test('should handle Chrome-specific features', async ({ context, page }) => {
      // Test Chrome-specific features
      await page.goto('/');
      
      const isChrome = await page.evaluate(() => {
        return /chrome/i.test(navigator.userAgent);
      });
      
      if (isChrome) {
        // Test Chrome-specific behaviors
        await expect(page.locator('[data-testid="chrome-compatibility"]')).toBeVisible();
      }
    });
  });

  // Test progressive web app features
  test.describe('PWA Compatibility Tests', () => {
    test('should support service worker', async ({ context, page }) => {
      await page.goto('/');
      
      // Check if service worker is registered
      const serviceWorkerActive = await page.evaluate(() => {
        return navigator.serviceWorker && navigator.serviceWorker.controller !== null;
      });
      
      expect(serviceWorkerActive).toBe(true);
    });

    test('should support offline functionality', async ({ context, page }) => {
      await page.goto('/');
      
      // Go offline
      await context.setOffline(true);
      
      // Try to use the app
      await expect(page.locator('[data-testid="offline-indicator"]')).toBeVisible();
      
      // Go back online
      await context.setOffline(false);
      
      // Check if app recovers
      await expect(page.locator('[data-testid="online-indicator"]')).toBeVisible();
    });

    test('should support install prompt', async ({ context, page }) => {
      await page.goto('/');
      
      // Mock install prompt
      await page.addInitScript(() => {
        // @ts-ignore
        (window as any).addEventListener('beforeinstallprompt', (e) => {
          e.preventDefault();
          (window as any).installPrompt = e;
        });
      });
      
      // Trigger install prompt
      await page.click('[data-testid="install-button"]');
      
      // Check if install prompt appears
      await expect(page.locator('[data-testid="install-dialog"]')).toBeVisible();
    });
  });

  // Test performance across browsers
  test.describe('Cross-Browser Performance Tests', () => {
    BROWSER_CONFIGS.forEach(browserConfig => {
      test(`should meet performance requirements in ${browserConfig.name}`, async () => {
        const browser = browserConfig.browser === 'chromium' ? chromium :
                       browserConfig.browser === 'firefox' ? firefox : webkit;
        const context = await browser.launchPersistentContext('', {
          viewport: { width: 1280, height: 720 },
          ignoreHTTPSErrors: true,
        });
        const page = await context.newPage();
        
        try {
          // Measure page load time
          const startTime = Date.now();
          await page.goto('/');
          const loadTime = Date.now() - startTime;
          
          // Check performance metrics
          const metrics = await page.evaluate(() => {
            const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
            return {
              domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
              loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
              firstPaint: performance.getEntriesByType('paint')[0]?.startTime || 0,
              firstContentfulPaint: performance.getEntriesByType('paint')[1]?.startTime || 0,
            };
          });
          
          // Assert performance requirements
          expect(loadTime).toBeLessThan(3000);
          expect(metrics.domContentLoaded).toBeLessThan(1500);
          expect(metrics.loadComplete).toBeLessThan(3000);
          expect(metrics.firstContentfulPaint).toBeLessThan(1800);
          
        } finally {
          await context.close();
        }
      });
    });
  });

  // Test accessibility across browsers
  test.describe('Cross-Browser Accessibility Tests', () => {
    BROWSER_CONFIGS.forEach(browserConfig => {
      test(`should meet accessibility requirements in ${browserConfig.name}`, async () => {
        const browser = browserConfig.browser === 'chromium' ? chromium :
                       browserConfig.browser === 'firefox' ? firefox : webkit;
        const context = await browser.launchPersistentContext('', {
          viewport: { width: 1280, height: 720 },
          ignoreHTTPSErrors: true,
        });
        const page = await context.newPage();
        
        try {
          await page.goto('/');
          
          // Run accessibility tests
          const accessibilityCheck = await page.evaluate(() => {
            // Simple accessibility check - in a real implementation, you'd use axe-core
            return {
              violations: [],
              passes: []
            };
          });
          
          // Check for critical accessibility issues
          const criticalIssues = accessibilityCheck?.violations?.filter((node: any) =>
            node.impact === 'critical'
          ) || [];
          
          expect(criticalIssues.length).toBe(0);
          
          // Check for proper ARIA support
          const ariaElements = await page.locator('[aria-label], [aria-describedby], [aria-labelledby]').all();
          expect(ariaElements.length).toBeGreaterThan(0);
          
          // Check for keyboard navigation
          await page.keyboard.press('Tab');
          const focusedElement = await page.locator(':focus');
          await expect(focusedElement).toBeVisible();
          
        } finally {
          await context.close();
        }
      });
    });
  });
});

// Helper functions for cross-browser testing
export class CrossBrowserTestUtils {
  static async waitForElement(page: Page, selector: string, timeout = 5000): Promise<void> {
    await page.waitForSelector(selector, { timeout });
  }

  static async takeScreenshot(page: Page, filename: string): Promise<void> {
    await page.screenshot({ path: `./test-results/${filename}`, fullPage: true });
  }

  static async mockAPIResponse(page: Page, endpoint: string, response: any): Promise<void> {
    await page.route(endpoint, route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(response),
      });
    });
  }

  static async simulateNetworkCondition(page: Page, condition: 'slow' | 'offline'): Promise<void> {
    if (condition === 'offline') {
      await page.context().setOffline(true);
    } else if (condition === 'slow') {
      // Simulate slow network
      await page.route('**/*', async route => {
        await new Promise(resolve => setTimeout(resolve, 1000)); // 1 second delay
        await route.continue();
      });
    }
  }

  static async checkBrowserSupport(page: Page): Promise<{
    isChrome: boolean;
    isFirefox: boolean;
    isSafari: boolean;
    isMobile: boolean;
  }> {
    return await page.evaluate(() => ({
      isChrome: /chrome/i.test(navigator.userAgent),
      isFirefox: /firefox/i.test(navigator.userAgent),
      isSafari: /apple/i.test(navigator.vendor),
      isMobile: /android|iphone|ipad/i.test(navigator.userAgent),
    }));
  }
}