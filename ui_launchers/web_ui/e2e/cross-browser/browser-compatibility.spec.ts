import { test, expect, devices } from '@playwright/test';
import { AuthenticationHelper } from '../utils/authentication-helper';
import { TestDataManager } from '../utils/test-data-manager';

// Cross-browser compatibility tests
test.describe('Cross-Browser Compatibility', () => {
  let authHelper: AuthenticationHelper;
  let testData: TestDataManager;

  test.beforeEach(async ({ page }) => {
    authHelper = new AuthenticationHelper(page);
    testData = new TestDataManager();
  });

  test.describe('Core Functionality Across Browsers', () => {
    test('should login successfully across all browsers', async ({ page, browserName }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      
      // Verify successful login regardless of browser
      await expect(page).toHaveURL(/\/dashboard/);
      await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
      
      // Browser-specific checks
      if (browserName === 'webkit') {
        // Safari-specific checks
        await expect(page.locator('[data-testid="safari-compatible-elements"]')).toBeVisible();
      }
    });

    test('should render dashboard correctly across browsers', async ({ page, browserName }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      await page.goto('/dashboard');
      
      // Core dashboard elements should be visible
      await expect(page.locator('[data-testid="dashboard-container"]')).toBeVisible();
      await expect(page.locator('[data-testid="sidebar-navigation"]')).toBeVisible();
      await expect(page.locator('[data-testid="main-content"]')).toBeVisible();
      
      // Check browser-specific rendering
      const dashboardBounds = await page.locator('[data-testid="dashboard-container"]').boundingBox();
      expect(dashboardBounds).toBeTruthy();
      expect(dashboardBounds!.width).toBeGreaterThan(800);
      
      // Browser-specific CSS compatibility
      if (browserName === 'firefox') {
        // Firefox-specific CSS checks
        const computedStyle = await page.evaluate(() => {
          const element = document.querySelector('[data-testid="dashboard-container"]');
          return window.getComputedStyle(element!).display;
        });
        expect(computedStyle).toBe('flex');
      }
    });

    test('should handle JavaScript features across browsers', async ({ page, browserName }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      await page.goto('/dashboard');
      
      // Test modern JavaScript features
      const jsFeatureTest = await page.evaluate(() => {
        // Test ES6+ features
        const testArrowFunction = () => 'arrow function works';
        const testDestructuring = { a: 1, b: 2 };
        const { a, b } = testDestructuring;
        const testTemplateString = `Template string: ${a + b}`;
        
        // Test async/await
        const testAsync = async () => {
          return new Promise(resolve => setTimeout(() => resolve('async works'), 100));
        };
        
        return {
          arrowFunction: testArrowFunction(),
          destructuring: a + b === 3,
          templateString: testTemplateString.includes('Template string: 3'),
          promiseSupport: typeof Promise !== 'undefined'
        };
      });
      
      expect(jsFeatureTest.arrowFunction).toBe('arrow function works');
      expect(jsFeatureTest.destructuring).toBe(true);
      expect(jsFeatureTest.templateString).toBe(true);
      expect(jsFeatureTest.promiseSupport).toBe(true);
    });
  });

  test.describe('Responsive Design Across Devices', () => {
    test('should adapt to mobile viewport', async ({ page }) => {
      await page.setViewportSize(devices['iPhone 12'].viewport);
      
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      await page.goto('/dashboard');
      
      // Mobile-specific layout checks
      await expect(page.locator('[data-testid="mobile-sidebar-toggle"]')).toBeVisible();
      await expect(page.locator('[data-testid="sidebar-navigation"]')).not.toBeVisible();
      
      // Test mobile navigation
      await page.click('[data-testid="mobile-sidebar-toggle"]');
      await expect(page.locator('[data-testid="sidebar-navigation"]')).toBeVisible();
      
      // Verify mobile-optimized components
      await expect(page.locator('[data-testid="mobile-dashboard-layout"]')).toBeVisible();
    });

    test('should adapt to tablet viewport', async ({ page }) => {
      await page.setViewportSize(devices['iPad'].viewport);
      
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      await page.goto('/dashboard');
      
      // Tablet-specific layout checks
      await expect(page.locator('[data-testid="tablet-layout"]')).toBeVisible();
      await expect(page.locator('[data-testid="sidebar-navigation"]')).toBeVisible();
      
      // Verify touch-friendly elements
      const touchTargets = await page.locator('[data-testid*="button"]').all();
      for (const target of touchTargets) {
        const bounds = await target.boundingBox();
        if (bounds) {
          expect(bounds.height).toBeGreaterThanOrEqual(44); // Minimum touch target size
        }
      }
    });

    test('should handle high-DPI displays', async ({ page }) => {
      // Simulate high-DPI display
      await page.emulateMedia({ reducedMotion: 'no-preference' });
      await page.setViewportSize({ width: 1920, height: 1080 });
      
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      await page.goto('/dashboard');
      
      // Check image rendering on high-DPI
      const images = await page.locator('img').all();
      for (const img of images) {
        const naturalWidth = await img.evaluate((el: HTMLImageElement) => el.naturalWidth);
        const displayWidth = await img.evaluate((el: HTMLImageElement) => el.offsetWidth);
        
        // High-DPI images should have higher natural resolution
        if (naturalWidth > 0 && displayWidth > 0) {
          expect(naturalWidth).toBeGreaterThanOrEqual(displayWidth);
        }
      }
    });
  });

  test.describe('Browser-Specific Feature Tests', () => {
    test('should handle WebSocket connections across browsers', async ({ page, browserName }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      await page.goto('/dashboard');
      
      // Test WebSocket connection
      const wsConnectionTest = await page.evaluate(() => {
        return new Promise((resolve) => {
          if (typeof WebSocket === 'undefined') {
            resolve({ supported: false, error: 'WebSocket not supported' });
            return;
          }
          
          try {
            const ws = new WebSocket('ws://localhost:8010/ws/test');
            ws.onopen = () => {
              ws.close();
              resolve({ supported: true, connected: true });
            };
            ws.onerror = () => {
              resolve({ supported: true, connected: false });
            };
            
            setTimeout(() => {
              ws.close();
              resolve({ supported: true, connected: false, timeout: true });
            }, 5000);
          } catch (error) {
            resolve({ supported: false, error: error.message });
          }
        });
      });
      
      expect(wsConnectionTest.supported).toBe(true);
    });

    test('should handle local storage across browsers', async ({ page, browserName }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      
      // Test localStorage functionality
      const storageTest = await page.evaluate(() => {
        try {
          const testKey = 'browser-test-key';
          const testValue = 'browser-test-value';
          
          localStorage.setItem(testKey, testValue);
          const retrievedValue = localStorage.getItem(testKey);
          localStorage.removeItem(testKey);
          
          return {
            supported: true,
            setValue: testValue,
            getValue: retrievedValue,
            matches: testValue === retrievedValue
          };
        } catch (error) {
          return {
            supported: false,
            error: error.message
          };
        }
      });
      
      expect(storageTest.supported).toBe(true);
      expect(storageTest.matches).toBe(true);
    });

    test('should handle CSS Grid and Flexbox across browsers', async ({ page, browserName }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      await page.goto('/dashboard');
      
      // Test CSS Grid support
      const cssSupport = await page.evaluate(() => {
        const testElement = document.createElement('div');
        document.body.appendChild(testElement);
        
        // Test CSS Grid
        testElement.style.display = 'grid';
        const gridSupported = window.getComputedStyle(testElement).display === 'grid';
        
        // Test Flexbox
        testElement.style.display = 'flex';
        const flexSupported = window.getComputedStyle(testElement).display === 'flex';
        
        // Test CSS Custom Properties
        testElement.style.setProperty('--test-var', 'test-value');
        const customPropsSupported = testElement.style.getPropertyValue('--test-var') === 'test-value';
        
        document.body.removeChild(testElement);
        
        return {
          grid: gridSupported,
          flex: flexSupported,
          customProperties: customPropsSupported
        };
      });
      
      expect(cssSupport.grid).toBe(true);
      expect(cssSupport.flex).toBe(true);
      expect(cssSupport.customProperties).toBe(true);
    });
  });

  test.describe('Performance Across Browsers', () => {
    test('should load within acceptable time limits', async ({ page, browserName }) => {
      const startTime = Date.now();
      
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      await page.goto('/dashboard');
      
      // Wait for dashboard to be fully loaded
      await expect(page.locator('[data-testid="dashboard-loaded"]')).toBeVisible({ timeout: 10000 });
      
      const loadTime = Date.now() - startTime;
      
      // Performance expectations by browser
      const maxLoadTime = browserName === 'webkit' ? 8000 : 6000; // Safari might be slower
      expect(loadTime).toBeLessThan(maxLoadTime);
    });

    test('should handle memory usage efficiently', async ({ page, browserName }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      
      // Navigate through multiple pages to test memory usage
      const pages = ['/dashboard', '/memory', '/plugins', '/models', '/settings'];
      
      for (const pagePath of pages) {
        await page.goto(pagePath);
        await page.waitForLoadState('networkidle');
        
        // Check for memory leaks (simplified test)
        const memoryInfo = await page.evaluate(() => {
          if ('memory' in performance) {
            return (performance as any).memory;
          }
          return null;
        });
        
        if (memoryInfo && browserName === 'chromium') {
          // Chrome-specific memory checks
          expect(memoryInfo.usedJSHeapSize).toBeLessThan(100 * 1024 * 1024); // 100MB limit
        }
      }
    });
  });

  test.describe('Accessibility Across Browsers', () => {
    test('should maintain keyboard navigation across browsers', async ({ page, browserName }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      await page.goto('/dashboard');
      
      // Test tab navigation
      await page.keyboard.press('Tab');
      const firstFocusedElement = await page.evaluate(() => document.activeElement?.getAttribute('data-testid'));
      expect(firstFocusedElement).toBeTruthy();
      
      // Navigate through several elements
      for (let i = 0; i < 5; i++) {
        await page.keyboard.press('Tab');
      }
      
      const lastFocusedElement = await page.evaluate(() => document.activeElement?.getAttribute('data-testid'));
      expect(lastFocusedElement).toBeTruthy();
      expect(lastFocusedElement).not.toBe(firstFocusedElement);
    });

    test('should support screen reader attributes across browsers', async ({ page, browserName }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      await page.goto('/dashboard');
      
      // Check ARIA attributes
      const ariaElements = await page.locator('[aria-label], [aria-labelledby], [role]').all();
      expect(ariaElements.length).toBeGreaterThan(0);
      
      // Verify specific ARIA implementations
      await expect(page.locator('[role="main"]')).toBeVisible();
      await expect(page.locator('[role="navigation"]')).toBeVisible();
      
      // Check heading hierarchy
      const headings = await page.locator('h1, h2, h3, h4, h5, h6').all();
      expect(headings.length).toBeGreaterThan(0);
      
      // Verify first heading is h1
      const firstHeading = headings[0];
      const tagName = await firstHeading.evaluate(el => el.tagName.toLowerCase());
      expect(tagName).toBe('h1');
    });
  });
});