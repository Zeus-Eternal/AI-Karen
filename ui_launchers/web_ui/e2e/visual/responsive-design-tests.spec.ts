import { test, expect, devices } from '@playwright/test';
import { AuthenticationHelper } from '../utils/authentication-helper';
import { TestDataManager } from '../utils/test-data-manager';

test.describe('Responsive Design Visual Testing', () => {
  let authHelper: AuthenticationHelper;
  let testData: TestDataManager;

  test.beforeEach(async ({ page }) => {
    authHelper = new AuthenticationHelper(page);
    testData = new TestDataManager();
    
    // Setup consistent visual testing environment
    await page.addInitScript(() => {
      const style = document.createElement('style');
      style.textContent = `
        *, *::before, *::after {
          animation-duration: 0s !important;
          animation-delay: 0s !important;
          transition-duration: 0s !important;
          transition-delay: 0s !important;
        }
      `;
      document.head.appendChild(style);
    });

    // Login for authenticated pages
    const credentials = testData.getValidCredentials();
    await authHelper.login(credentials.username, credentials.password);
  });

  test.describe('Mobile Viewport (375x667)', () => {
    test.beforeEach(async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
    });

    test('should match mobile dashboard layout', async ({ page }) => {
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');
      
      // Wait for mobile layout to activate
      await expect(page.locator('[data-testid="mobile-layout"]')).toBeVisible();
      
      await expect(page).toHaveScreenshot('mobile-dashboard-375.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should match mobile navigation menu', async ({ page }) => {
      await page.goto('/dashboard');
      
      // Open mobile menu
      await page.click('[data-testid="mobile-menu-toggle"]');
      await expect(page.locator('[data-testid="mobile-navigation-menu"]')).toBeVisible();
      
      await expect(page).toHaveScreenshot('mobile-navigation-375.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should match mobile memory interface', async ({ page }) => {
      await page.goto('/memory');
      await page.waitForLoadState('networkidle');
      
      await expect(page).toHaveScreenshot('mobile-memory-375.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should match mobile plugin management', async ({ page }) => {
      await page.goto('/plugins');
      await page.waitForLoadState('networkidle');
      
      await expect(page).toHaveScreenshot('mobile-plugins-375.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should match mobile settings page', async ({ page }) => {
      await page.goto('/settings');
      await page.waitForLoadState('networkidle');
      
      await expect(page).toHaveScreenshot('mobile-settings-375.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });
  });

  test.describe('Large Mobile Viewport (414x896)', () => {
    test.beforeEach(async ({ page }) => {
      await page.setViewportSize({ width: 414, height: 896 });
    });

    test('should match large mobile dashboard', async ({ page }) => {
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');
      
      await expect(page).toHaveScreenshot('mobile-dashboard-414.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should match large mobile memory search', async ({ page }) => {
      await page.goto('/memory');
      await page.click('[data-testid="search-tab"]');
      
      // Perform search to show results
      await page.fill('[data-testid="semantic-search-input"]', 'machine learning');
      await page.click('[data-testid="search-button"]');
      await expect(page.locator('[data-testid="search-results"]')).toBeVisible();
      
      await expect(page).toHaveScreenshot('mobile-memory-search-414.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });
  });

  test.describe('Tablet Portrait (768x1024)', () => {
    test.beforeEach(async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
    });

    test('should match tablet dashboard layout', async ({ page }) => {
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');
      
      await expect(page).toHaveScreenshot('tablet-dashboard-768.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should match tablet memory network view', async ({ page }) => {
      await page.goto('/memory');
      await page.click('[data-testid="network-tab"]');
      
      // Wait for network visualization
      await expect(page.locator('[data-testid="memory-network-graph"]')).toBeVisible();
      await page.waitForTimeout(2000);
      
      await expect(page).toHaveScreenshot('tablet-memory-network-768.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should match tablet plugin installation wizard', async ({ page }) => {
      await page.goto('/plugins');
      await page.click('[data-testid="install-plugin-button"]');
      
      await expect(page.locator('[data-testid="installation-wizard"]')).toBeVisible();
      
      await expect(page).toHaveScreenshot('tablet-plugin-wizard-768.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should match tablet model comparison', async ({ page }) => {
      await page.goto('/models');
      await page.click('[data-testid="model-comparison-tab"]');
      
      // Select models for comparison
      await page.check('[data-testid="compare-model-gpt-4"]');
      await page.check('[data-testid="compare-model-claude-3"]');
      await page.click('[data-testid="start-comparison-button"]');
      
      await expect(page.locator('[data-testid="comparison-table"]')).toBeVisible();
      
      await expect(page).toHaveScreenshot('tablet-model-comparison-768.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });
  });

  test.describe('Tablet Landscape (1024x768)', () => {
    test.beforeEach(async ({ page }) => {
      await page.setViewportSize({ width: 1024, height: 768 });
    });

    test('should match tablet landscape dashboard', async ({ page }) => {
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');
      
      await expect(page).toHaveScreenshot('tablet-landscape-dashboard-1024.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should match tablet landscape memory management', async ({ page }) => {
      await page.goto('/memory');
      await page.click('[data-testid="management-tab"]');
      
      await expect(page.locator('[data-testid="memory-list"]')).toBeVisible();
      
      await expect(page).toHaveScreenshot('tablet-landscape-memory-1024.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });
  });

  test.describe('Small Desktop (1366x768)', () => {
    test.beforeEach(async ({ page }) => {
      await page.setViewportSize({ width: 1366, height: 768 });
    });

    test('should match small desktop dashboard', async ({ page }) => {
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');
      
      await expect(page).toHaveScreenshot('small-desktop-dashboard-1366.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should match small desktop plugin monitoring', async ({ page }) => {
      await page.goto('/plugins');
      await page.click('[data-testid="monitoring-tab"]');
      
      await expect(page.locator('[data-testid="plugin-metrics-dashboard"]')).toBeVisible();
      
      // Normalize chart data
      await page.addStyleTag({
        content: `canvas, svg { filter: blur(1px) !important; }`
      });
      
      await expect(page).toHaveScreenshot('small-desktop-plugin-monitoring-1366.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });
  });

  test.describe('Standard Desktop (1920x1080)', () => {
    test.beforeEach(async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 });
    });

    test('should match standard desktop dashboard', async ({ page }) => {
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');
      
      await expect(page).toHaveScreenshot('desktop-dashboard-1920.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should match desktop memory analytics with charts', async ({ page }) => {
      await page.goto('/memory');
      await page.waitForLoadState('networkidle');
      
      // Normalize dynamic values
      await page.addStyleTag({
        content: `
          [data-testid*="metric-value"] {
            color: transparent !important;
          }
          [data-testid*="metric-value"]:after {
            content: "1,234" !important;
            color: var(--text-color) !important;
          }
        `
      });
      
      await expect(page).toHaveScreenshot('desktop-memory-analytics-1920.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should match desktop model provider configuration', async ({ page }) => {
      await page.goto('/models');
      await page.click('[data-testid="provider-config-tab"]');
      
      await expect(page.locator('[data-testid="provider-config-list"]')).toBeVisible();
      
      await expect(page).toHaveScreenshot('desktop-provider-config-1920.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });
  });

  test.describe('Large Desktop (2560x1440)', () => {
    test.beforeEach(async ({ page }) => {
      await page.setViewportSize({ width: 2560, height: 1440 });
    });

    test('should match large desktop dashboard', async ({ page }) => {
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');
      
      await expect(page).toHaveScreenshot('large-desktop-dashboard-2560.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should match large desktop memory network visualization', async ({ page }) => {
      await page.goto('/memory');
      await page.click('[data-testid="network-tab"]');
      
      await expect(page.locator('[data-testid="memory-network-graph"]')).toBeVisible();
      await page.waitForTimeout(2000);
      
      await expect(page).toHaveScreenshot('large-desktop-memory-network-2560.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });
  });

  test.describe('Ultra-wide Desktop (3440x1440)', () => {
    test.beforeEach(async ({ page }) => {
      await page.setViewportSize({ width: 3440, height: 1440 });
    });

    test('should match ultra-wide desktop dashboard', async ({ page }) => {
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');
      
      await expect(page).toHaveScreenshot('ultrawide-desktop-dashboard-3440.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should match ultra-wide desktop plugin management', async ({ page }) => {
      await page.goto('/plugins');
      await page.waitForLoadState('networkidle');
      
      await expect(page).toHaveScreenshot('ultrawide-desktop-plugins-3440.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });
  });

  test.describe('Responsive Breakpoint Testing', () => {
    const breakpoints = [
      { name: 'xs', width: 320, height: 568 },
      { name: 'sm', width: 640, height: 480 },
      { name: 'md', width: 768, height: 1024 },
      { name: 'lg', width: 1024, height: 768 },
      { name: 'xl', width: 1280, height: 720 },
      { name: '2xl', width: 1536, height: 864 }
    ];

    for (const breakpoint of breakpoints) {
      test(`should match dashboard at ${breakpoint.name} breakpoint (${breakpoint.width}x${breakpoint.height})`, async ({ page }) => {
        await page.setViewportSize({ width: breakpoint.width, height: breakpoint.height });
        await page.goto('/dashboard');
        await page.waitForLoadState('networkidle');
        
        await expect(page).toHaveScreenshot(`dashboard-${breakpoint.name}-${breakpoint.width}x${breakpoint.height}.png`, {
          fullPage: true,
          animations: 'disabled'
        });
      });
    }
  });

  test.describe('Orientation Changes', () => {
    test('should handle portrait to landscape transition', async ({ page }) => {
      // Start in portrait
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');
      
      await expect(page).toHaveScreenshot('orientation-portrait-768x1024.png', {
        fullPage: true,
        animations: 'disabled'
      });
      
      // Switch to landscape
      await page.setViewportSize({ width: 1024, height: 768 });
      await page.waitForTimeout(500); // Allow layout to adjust
      
      await expect(page).toHaveScreenshot('orientation-landscape-1024x768.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should handle mobile orientation changes', async ({ page }) => {
      // Mobile portrait
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto('/memory');
      await page.waitForLoadState('networkidle');
      
      await expect(page).toHaveScreenshot('mobile-portrait-375x667.png', {
        fullPage: true,
        animations: 'disabled'
      });
      
      // Mobile landscape
      await page.setViewportSize({ width: 667, height: 375 });
      await page.waitForTimeout(500);
      
      await expect(page).toHaveScreenshot('mobile-landscape-667x375.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });
  });

  test.describe('Touch Target Validation', () => {
    test('should have appropriate touch targets on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');
      
      // Highlight touch targets for visual validation
      await page.addStyleTag({
        content: `
          button, a, [role="button"], input, select, textarea {
            outline: 2px solid red !important;
            outline-offset: 2px !important;
          }
        `
      });
      
      await expect(page).toHaveScreenshot('mobile-touch-targets-375.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should have appropriate touch targets on tablet', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.goto('/plugins');
      await page.waitForLoadState('networkidle');
      
      // Highlight touch targets
      await page.addStyleTag({
        content: `
          button, a, [role="button"], input, select, textarea {
            outline: 2px solid blue !important;
            outline-offset: 2px !important;
          }
        `
      });
      
      await expect(page).toHaveScreenshot('tablet-touch-targets-768.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });
  });

  test.describe('Content Reflow Testing', () => {
    test('should handle text reflow at different widths', async ({ page }) => {
      const widths = [320, 480, 768, 1024, 1280, 1920];
      
      for (const width of widths) {
        await page.setViewportSize({ width, height: 800 });
        await page.goto('/memory');
        await page.click('[data-testid="search-tab"]');
        
        // Add sample text content
        await page.fill('[data-testid="semantic-search-input"]', 'This is a long search query that should reflow properly at different viewport widths to ensure readability');
        
        await expect(page).toHaveScreenshot(`text-reflow-${width}.png`, {
          fullPage: true,
          animations: 'disabled'
        });
      }
    });

    test('should handle table responsiveness', async ({ page }) => {
      await page.goto('/plugins');
      await page.waitForLoadState('networkidle');
      
      const widths = [375, 768, 1024, 1920];
      
      for (const width of widths) {
        await page.setViewportSize({ width, height: 800 });
        await page.waitForTimeout(300); // Allow layout adjustment
        
        await expect(page).toHaveScreenshot(`table-responsive-${width}.png`, {
          fullPage: true,
          animations: 'disabled'
        });
      }
    });
  });
});