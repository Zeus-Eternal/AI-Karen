import { test, expect } from '@playwright/test';
import { AuthenticationHelper } from '../utils/authentication-helper';
import { TestDataManager } from '../utils/test-data-manager';

test.describe('Visual Regression Testing', () => {
  let authHelper: AuthenticationHelper;
  let testData: TestDataManager;

  test.beforeEach(async ({ page }) => {
    authHelper = new AuthenticationHelper(page);
    testData = new TestDataManager();
    
    // Setup consistent visual testing environment
    await page.addInitScript(() => {
      // Disable animations for consistent screenshots
      const style = document.createElement('style');
      style.textContent = `
        *, *::before, *::after {
          animation-duration: 0s !important;
          animation-delay: 0s !important;
          transition-duration: 0s !important;
          transition-delay: 0s !important;
        }
        
        /* Hide dynamic content that changes between runs */
        [data-testid*="timestamp"],
        [data-testid*="time"],
        [data-testid*="date"] {
          visibility: hidden !important;
        }
      `;
      document.head.appendChild(style);
    });

    // Wait for fonts to load
    await page.waitForFunction(() => document.fonts.ready);
  });

  test.describe('Authentication Pages', () => {
    test('should match login page visual baseline', async ({ page }) => {
      await page.goto('/login');
      await page.waitForLoadState('networkidle');
      
      // Wait for all images to load
      await page.waitForFunction(() => {
        const images = Array.from(document.images);
        return images.every(img => img.complete);
      });
      
      await expect(page).toHaveScreenshot('login-page.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should match login page with error state', async ({ page }) => {
      await page.goto('/login');
      
      // Trigger error state
      await page.fill('[data-testid="username-input"]', 'invalid@test.com');
      await page.fill('[data-testid="password-input"]', 'wrongpassword');
      await page.click('[data-testid="login-button"]');
      
      // Wait for error message
      await expect(page.locator('[data-testid="login-error"]')).toBeVisible();
      
      await expect(page).toHaveScreenshot('login-page-error.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should match password reset page', async ({ page }) => {
      await page.goto('/reset-password');
      await page.waitForLoadState('networkidle');
      
      await expect(page).toHaveScreenshot('password-reset-page.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });
  });

  test.describe('Dashboard Views', () => {
    test.beforeEach(async ({ page }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
    });

    test('should match dashboard overview', async ({ page }) => {
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');
      
      // Wait for metrics to load
      await expect(page.locator('[data-testid="cpu-usage-metric"]')).toBeVisible();
      await expect(page.locator('[data-testid="memory-usage-metric"]')).toBeVisible();
      
      // Hide dynamic values for consistent screenshots
      await page.addStyleTag({
        content: `
          [data-testid*="usage-value"],
          [data-testid*="metric-value"] {
            color: transparent !important;
          }
          [data-testid*="usage-value"]:after,
          [data-testid*="metric-value"]:after {
            content: "XX.X%" !important;
            color: var(--text-color) !important;
          }
        `
      });
      
      await expect(page).toHaveScreenshot('dashboard-overview.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should match dashboard with alerts', async ({ page }) => {
      // Mock high usage to trigger alerts
      await page.route('**/api/metrics/system', route => {
        route.fulfill({
          json: {
            cpu: { usage: 95, threshold: 80 },
            memory: { usage: 88, threshold: 80 },
            alerts: [
              { type: 'warning', message: 'High CPU usage detected', severity: 'high' }
            ]
          }
        });
      });
      
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');
      
      // Wait for alert to appear
      await expect(page.locator('[data-testid="system-alert"]')).toBeVisible();
      
      await expect(page).toHaveScreenshot('dashboard-with-alerts.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should match dashboard customization mode', async ({ page }) => {
      await page.goto('/dashboard');
      await page.click('[data-testid="customize-dashboard-button"]');
      
      // Wait for customization mode to activate
      await expect(page.locator('[data-testid="customization-mode-active"]')).toBeVisible();
      
      await expect(page).toHaveScreenshot('dashboard-customization-mode.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });
  });

  test.describe('Memory Management Views', () => {
    test.beforeEach(async ({ page }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
    });

    test('should match memory analytics view', async ({ page }) => {
      await page.goto('/memory');
      await page.waitForLoadState('networkidle');
      
      // Wait for analytics to load
      await expect(page.locator('[data-testid="total-embeddings-count"]')).toBeVisible();
      
      // Normalize dynamic values
      await page.addStyleTag({
        content: `
          [data-testid*="embeddings-value"],
          [data-testid*="storage-size-value"],
          [data-testid*="latency-value"] {
            color: transparent !important;
          }
          [data-testid*="embeddings-value"]:after {
            content: "1,234" !important;
            color: var(--text-color) !important;
          }
          [data-testid*="storage-size-value"]:after {
            content: "256 MB" !important;
            color: var(--text-color) !important;
          }
          [data-testid*="latency-value"]:after {
            content: "45ms" !important;
            color: var(--text-color) !important;
          }
        `
      });
      
      await expect(page).toHaveScreenshot('memory-analytics.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should match memory search interface', async ({ page }) => {
      await page.goto('/memory');
      await page.click('[data-testid="search-tab"]');
      
      // Perform a search to show results
      await page.fill('[data-testid="semantic-search-input"]', 'machine learning');
      await page.click('[data-testid="search-button"]');
      
      // Wait for search results
      await expect(page.locator('[data-testid="search-results"]')).toBeVisible();
      
      await expect(page).toHaveScreenshot('memory-search-interface.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should match memory network visualization', async ({ page }) => {
      await page.goto('/memory');
      await page.click('[data-testid="network-tab"]');
      
      // Wait for network graph to render
      await expect(page.locator('[data-testid="memory-network-graph"]')).toBeVisible();
      await page.waitForTimeout(2000); // Allow graph to stabilize
      
      await expect(page).toHaveScreenshot('memory-network-visualization.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should match memory management interface', async ({ page }) => {
      await page.goto('/memory');
      await page.click('[data-testid="management-tab"]');
      
      // Wait for memory list to load
      await expect(page.locator('[data-testid="memory-list"]')).toBeVisible();
      
      await expect(page).toHaveScreenshot('memory-management-interface.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });
  });

  test.describe('Plugin Management Views', () => {
    test.beforeEach(async ({ page }) => {
      const adminCredentials = testData.getAdminCredentials();
      await authHelper.login(adminCredentials.username, adminCredentials.password);
    });

    test('should match plugin list view', async ({ page }) => {
      await page.goto('/plugins');
      await page.waitForLoadState('networkidle');
      
      // Wait for plugin list to load
      await expect(page.locator('[data-testid="plugin-list"]')).toBeVisible();
      
      await expect(page).toHaveScreenshot('plugin-list-view.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should match plugin installation wizard', async ({ page }) => {
      await page.goto('/plugins');
      await page.click('[data-testid="install-plugin-button"]');
      
      // Wait for wizard to open
      await expect(page.locator('[data-testid="installation-wizard"]')).toBeVisible();
      
      await expect(page).toHaveScreenshot('plugin-installation-wizard.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should match plugin configuration form', async ({ page }) => {
      await page.goto('/plugins');
      
      // Open configuration for first plugin
      const firstPlugin = page.locator('[data-testid="plugin-item"]').first();
      await firstPlugin.click();
      await page.click('[data-testid="configure-plugin-button"]');
      
      // Wait for config form
      await expect(page.locator('[data-testid="plugin-config-form"]')).toBeVisible();
      
      await expect(page).toHaveScreenshot('plugin-configuration-form.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should match plugin monitoring dashboard', async ({ page }) => {
      await page.goto('/plugins');
      await page.click('[data-testid="monitoring-tab"]');
      
      // Wait for monitoring dashboard
      await expect(page.locator('[data-testid="plugin-metrics-dashboard"]')).toBeVisible();
      
      // Normalize chart data for consistent screenshots
      await page.addStyleTag({
        content: `
          canvas, svg {
            filter: blur(1px) !important;
          }
        `
      });
      
      await expect(page).toHaveScreenshot('plugin-monitoring-dashboard.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });
  });

  test.describe('Model Management Views', () => {
    test.beforeEach(async ({ page }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
    });

    test('should match model selector interface', async ({ page }) => {
      await page.goto('/models');
      await page.waitForLoadState('networkidle');
      
      // Wait for model selector to load
      await expect(page.locator('[data-testid="model-selector"]')).toBeVisible();
      
      await expect(page).toHaveScreenshot('model-selector-interface.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should match model comparison view', async ({ page }) => {
      await page.goto('/models');
      await page.click('[data-testid="model-comparison-tab"]');
      
      // Select models for comparison
      await page.check('[data-testid="compare-model-gpt-4"]');
      await page.check('[data-testid="compare-model-claude-3"]');
      await page.click('[data-testid="start-comparison-button"]');
      
      // Wait for comparison table
      await expect(page.locator('[data-testid="comparison-table"]')).toBeVisible();
      
      await expect(page).toHaveScreenshot('model-comparison-view.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should match provider configuration', async ({ page }) => {
      await page.goto('/models');
      await page.click('[data-testid="provider-config-tab"]');
      
      // Wait for provider config to load
      await expect(page.locator('[data-testid="provider-config-list"]')).toBeVisible();
      
      await expect(page).toHaveScreenshot('provider-configuration.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });
  });

  test.describe('Settings and Configuration', () => {
    test.beforeEach(async ({ page }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
    });

    test('should match general settings page', async ({ page }) => {
      await page.goto('/settings');
      await page.waitForLoadState('networkidle');
      
      await expect(page).toHaveScreenshot('general-settings.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should match security settings page', async ({ page }) => {
      await page.goto('/settings/security');
      await page.waitForLoadState('networkidle');
      
      await expect(page).toHaveScreenshot('security-settings.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should match accessibility settings page', async ({ page }) => {
      await page.goto('/settings/accessibility');
      await page.waitForLoadState('networkidle');
      
      await expect(page).toHaveScreenshot('accessibility-settings.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });
  });

  test.describe('Responsive Design Screenshots', () => {
    test.beforeEach(async ({ page }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
    });

    test('should match mobile dashboard view', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');
      
      await expect(page).toHaveScreenshot('mobile-dashboard.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should match tablet dashboard view', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 }); // iPad
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');
      
      await expect(page).toHaveScreenshot('tablet-dashboard.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should match desktop dashboard view', async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 }); // Desktop
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');
      
      await expect(page).toHaveScreenshot('desktop-dashboard.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });
  });

  test.describe('Theme Variations', () => {
    test.beforeEach(async ({ page }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
    });

    test('should match light theme dashboard', async ({ page }) => {
      await page.goto('/settings');
      await page.selectOption('[data-testid="theme-selector"]', 'light');
      await page.click('[data-testid="save-preferences-button"]');
      
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');
      
      await expect(page).toHaveScreenshot('light-theme-dashboard.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should match dark theme dashboard', async ({ page }) => {
      await page.goto('/settings');
      await page.selectOption('[data-testid="theme-selector"]', 'dark');
      await page.click('[data-testid="save-preferences-button"]');
      
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');
      
      await expect(page).toHaveScreenshot('dark-theme-dashboard.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should match high contrast theme', async ({ page }) => {
      await page.goto('/settings/accessibility');
      await page.check('[data-testid="high-contrast-mode"]');
      await page.click('[data-testid="save-accessibility-settings"]');
      
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');
      
      await expect(page).toHaveScreenshot('high-contrast-dashboard.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });
  });

  test.describe('Error States', () => {
    test.beforeEach(async ({ page }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
    });

    test('should match network error state', async ({ page }) => {
      // Mock network failure
      await page.route('**/api/**', route => route.abort());
      
      await page.goto('/dashboard');
      
      // Wait for error state
      await expect(page.locator('[data-testid="network-error"]')).toBeVisible();
      
      await expect(page).toHaveScreenshot('network-error-state.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should match loading state', async ({ page }) => {
      // Mock slow API response
      await page.route('**/api/metrics/system', route => {
        setTimeout(() => {
          route.fulfill({
            json: { cpu: { usage: 45 }, memory: { usage: 60 } }
          });
        }, 5000);
      });
      
      await page.goto('/dashboard');
      
      // Capture loading state
      await expect(page.locator('[data-testid="dashboard-loading"]')).toBeVisible();
      
      await expect(page).toHaveScreenshot('loading-state.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });

    test('should match empty state', async ({ page }) => {
      // Mock empty data response
      await page.route('**/api/memory/list', route => {
        route.fulfill({
          json: { memories: [], total: 0 }
        });
      });
      
      await page.goto('/memory');
      await page.click('[data-testid="management-tab"]');
      
      // Wait for empty state
      await expect(page.locator('[data-testid="empty-memory-state"]')).toBeVisible();
      
      await expect(page).toHaveScreenshot('empty-memory-state.png', {
        fullPage: true,
        animations: 'disabled'
      });
    });
  });
});