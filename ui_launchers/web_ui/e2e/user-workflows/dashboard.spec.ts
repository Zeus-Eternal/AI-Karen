import { test, expect } from '@playwright/test';
import { AuthenticationHelper } from '../utils/authentication-helper';
import { DashboardHelper } from '../utils/dashboard-helper';
import { TestDataManager } from '../utils/test-data-manager';

test.describe('Dashboard Workflows', () => {
  let authHelper: AuthenticationHelper;
  let dashboardHelper: DashboardHelper;
  let testData: TestDataManager;

  test.beforeEach(async ({ page }) => {
    authHelper = new AuthenticationHelper(page);
    dashboardHelper = new DashboardHelper(page);
    testData = new TestDataManager();
    
    // Login before each test
    const credentials = testData.getValidCredentials();
    await authHelper.login(credentials.username, credentials.password);
    await page.goto('/dashboard');
  });

  test.describe('Dashboard Overview', () => {
    test('should display system metrics correctly', async ({ page }) => {
      // Verify key metrics are visible
      await expect(page.locator('[data-testid="cpu-usage-metric"]')).toBeVisible();
      await expect(page.locator('[data-testid="memory-usage-metric"]')).toBeVisible();
      await expect(page.locator('[data-testid="active-models-metric"]')).toBeVisible();
      await expect(page.locator('[data-testid="plugin-status-metric"]')).toBeVisible();
      
      // Verify metrics have valid values
      const cpuUsage = await page.locator('[data-testid="cpu-usage-value"]').textContent();
      expect(cpuUsage).toMatch(/^\d+(\.\d+)?%$/);
      
      const memoryUsage = await page.locator('[data-testid="memory-usage-value"]').textContent();
      expect(memoryUsage).toMatch(/^\d+(\.\d+)?\s*(MB|GB)$/);
    });

    test('should update metrics in real-time', async ({ page }) => {
      const initialCpuValue = await page.locator('[data-testid="cpu-usage-value"]').textContent();
      
      // Wait for real-time update
      await page.waitForTimeout(5000);
      
      const updatedCpuValue = await page.locator('[data-testid="cpu-usage-value"]').textContent();
      
      // Values should be different (real-time updates)
      expect(initialCpuValue).not.toBe(updatedCpuValue);
    });

    test('should display alerts when thresholds are exceeded', async ({ page }) => {
      // Simulate high CPU usage
      await page.route('**/api/metrics/system', route => {
        route.fulfill({
          json: {
            cpu: { usage: 95, threshold: 80 },
            memory: { usage: 60, threshold: 80 },
            alerts: [
              { type: 'warning', message: 'High CPU usage detected', severity: 'high' }
            ]
          }
        });
      });
      
      await page.reload();
      
      // Verify alert display
      await expect(page.locator('[data-testid="system-alert"]')).toBeVisible();
      await expect(page.locator('[data-testid="alert-message"]')).toContainText('High CPU usage detected');
      await expect(page.locator('[data-testid="alert-severity-high"]')).toBeVisible();
    });
  });

  test.describe('Widget Management', () => {
    test('should allow widget customization', async ({ page }) => {
      await dashboardHelper.enterCustomizationMode();
      
      // Verify customization controls are visible
      await expect(page.locator('[data-testid="widget-add-button"]')).toBeVisible();
      await expect(page.locator('[data-testid="widget-remove-button"]')).toBeVisible();
      await expect(page.locator('[data-testid="widget-resize-handle"]')).toBeVisible();
    });

    test('should support drag and drop widget rearrangement', async ({ page }) => {
      await dashboardHelper.enterCustomizationMode();
      
      const sourceWidget = page.locator('[data-testid="cpu-metric-widget"]');
      const targetPosition = page.locator('[data-testid="widget-drop-zone-2"]');
      
      await sourceWidget.dragTo(targetPosition);
      
      // Verify widget moved
      await expect(page.locator('[data-testid="widget-drop-zone-2"] [data-testid="cpu-metric-widget"]')).toBeVisible();
    });

    test('should persist widget layout changes', async ({ page }) => {
      await dashboardHelper.enterCustomizationMode();
      await dashboardHelper.moveWidget('cpu-metric-widget', 'widget-drop-zone-2');
      await dashboardHelper.saveLayout();
      
      await page.reload();
      
      // Verify layout persistence
      await expect(page.locator('[data-testid="widget-drop-zone-2"] [data-testid="cpu-metric-widget"]')).toBeVisible();
    });

    test('should add new widgets', async ({ page }) => {
      await dashboardHelper.enterCustomizationMode();
      await dashboardHelper.addWidget('network-usage');
      
      // Verify new widget added
      await expect(page.locator('[data-testid="network-usage-widget"]')).toBeVisible();
      await expect(page.locator('[data-testid="network-usage-metric"]')).toBeVisible();
    });
  });

  test.describe('Interactive Charts', () => {
    test('should display performance charts', async ({ page }) => {
      await page.click('[data-testid="performance-tab"]');
      
      // Verify charts are rendered
      await expect(page.locator('[data-testid="cpu-usage-chart"]')).toBeVisible();
      await expect(page.locator('[data-testid="memory-usage-chart"]')).toBeVisible();
      await expect(page.locator('[data-testid="response-time-chart"]')).toBeVisible();
    });

    test('should support time range selection', async ({ page }) => {
      await page.click('[data-testid="performance-tab"]');
      await page.selectOption('[data-testid="time-range-selector"]', '24h');
      
      // Verify chart updates
      await expect(page.locator('[data-testid="chart-loading"]')).toBeVisible();
      await expect(page.locator('[data-testid="chart-loading"]')).not.toBeVisible();
      
      // Verify time range label
      await expect(page.locator('[data-testid="chart-time-range"]')).toContainText('Last 24 hours');
    });

    test('should support chart zoom and pan', async ({ page }) => {
      await page.click('[data-testid="performance-tab"]');
      
      const chart = page.locator('[data-testid="cpu-usage-chart"]');
      
      // Test zoom functionality
      await chart.hover();
      await page.mouse.wheel(0, -100); // Zoom in
      
      // Verify zoom controls appear
      await expect(page.locator('[data-testid="chart-zoom-reset"]')).toBeVisible();
      
      // Test pan functionality
      await chart.dragTo(chart, { sourcePosition: { x: 100, y: 100 }, targetPosition: { x: 200, y: 100 } });
      
      // Verify pan indicator
      await expect(page.locator('[data-testid="chart-pan-indicator"]')).toBeVisible();
    });
  });

  test.describe('System Health Monitoring', () => {
    test('should display component health status', async ({ page }) => {
      await page.click('[data-testid="health-tab"]');
      
      // Verify health components
      await expect(page.locator('[data-testid="database-health"]')).toBeVisible();
      await expect(page.locator('[data-testid="api-health"]')).toBeVisible();
      await expect(page.locator('[data-testid="model-health"]')).toBeVisible();
      await expect(page.locator('[data-testid="plugin-health"]')).toBeVisible();
      
      // Verify health indicators
      const healthStatuses = await page.locator('[data-testid*="health-status"]').all();
      for (const status of healthStatuses) {
        const statusText = await status.textContent();
        expect(['healthy', 'warning', 'critical']).toContain(statusText?.toLowerCase());
      }
    });

    test('should show detailed health information on click', async ({ page }) => {
      await page.click('[data-testid="health-tab"]');
      await page.click('[data-testid="database-health"]');
      
      // Verify detailed health modal
      await expect(page.locator('[data-testid="health-detail-modal"]')).toBeVisible();
      await expect(page.locator('[data-testid="health-detail-metrics"]')).toBeVisible();
      await expect(page.locator('[data-testid="health-detail-logs"]')).toBeVisible();
    });

    test('should handle health check failures', async ({ page }) => {
      // Simulate health check failure
      await page.route('**/api/health/database', route => {
        route.fulfill({
          status: 503,
          json: { status: 'critical', message: 'Database connection failed' }
        });
      });
      
      await page.click('[data-testid="health-tab"]');
      await page.click('[data-testid="refresh-health-button"]');
      
      // Verify failure display
      await expect(page.locator('[data-testid="database-health-critical"]')).toBeVisible();
      await expect(page.locator('[data-testid="health-error-message"]')).toContainText('Database connection failed');
    });
  });
});