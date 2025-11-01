import { test, expect } from '@playwright/test';
import { AuthenticationHelper } from '../utils/authentication-helper';
import { PluginHelper } from '../utils/plugin-helper';
import { TestDataManager } from '../utils/test-data-manager';

test.describe('Plugin Management Workflows', () => {
  let authHelper: AuthenticationHelper;
  let pluginHelper: PluginHelper;
  let testData: TestDataManager;

  test.beforeEach(async ({ page }) => {
    authHelper = new AuthenticationHelper(page);
    pluginHelper = new PluginHelper(page);
    testData = new TestDataManager();
    
    // Login with admin credentials for plugin management
    const adminCredentials = testData.getAdminCredentials();
    await authHelper.login(adminCredentials.username, adminCredentials.password);
    await page.goto('/plugins');
  });

  test.describe('Plugin Overview', () => {
    test('should display installed plugins with status', async ({ page }) => {
      // Verify plugin list components
      await expect(page.locator('[data-testid="plugin-list"]')).toBeVisible();
      await expect(page.locator('[data-testid="plugin-search-input"]')).toBeVisible();
      await expect(page.locator('[data-testid="plugin-filter-dropdown"]')).toBeVisible();
      
      // Verify plugin items
      const pluginItems = await page.locator('[data-testid="plugin-item"]').all();
      expect(pluginItems.length).toBeGreaterThan(0);
      
      // Verify plugin information
      const firstPlugin = pluginItems[0];
      await expect(firstPlugin.locator('[data-testid="plugin-name"]')).toBeVisible();
      await expect(firstPlugin.locator('[data-testid="plugin-version"]')).toBeVisible();
      await expect(firstPlugin.locator('[data-testid="plugin-status"]')).toBeVisible();
      await expect(firstPlugin.locator('[data-testid="plugin-actions"]')).toBeVisible();
    });

    test('should filter plugins by status', async ({ page }) => {
      // Test active filter
      await page.selectOption('[data-testid="plugin-filter-dropdown"]', 'active');
      
      const activePlugins = await page.locator('[data-testid="plugin-item"]').all();
      for (const plugin of activePlugins) {
        await expect(plugin.locator('[data-testid="plugin-status-active"]')).toBeVisible();
      }
      
      // Test inactive filter
      await page.selectOption('[data-testid="plugin-filter-dropdown"]', 'inactive');
      
      const inactivePlugins = await page.locator('[data-testid="plugin-item"]').all();
      for (const plugin of inactivePlugins) {
        await expect(plugin.locator('[data-testid="plugin-status-inactive"]')).toBeVisible();
      }
    });

    test('should search plugins by name', async ({ page }) => {
      const searchTerm = 'analytics';
      await page.fill('[data-testid="plugin-search-input"]', searchTerm);
      
      // Verify search results
      const searchResults = await page.locator('[data-testid="plugin-item"]').all();
      for (const result of searchResults) {
        const pluginName = await result.locator('[data-testid="plugin-name"]').textContent();
        expect(pluginName?.toLowerCase()).toContain(searchTerm.toLowerCase());
      }
    });

    test('should display plugin details on click', async ({ page }) => {
      const firstPlugin = page.locator('[data-testid="plugin-item"]').first();
      await firstPlugin.click();
      
      // Verify detail panel
      await expect(page.locator('[data-testid="plugin-detail-panel"]')).toBeVisible();
      await expect(page.locator('[data-testid="plugin-description"]')).toBeVisible();
      await expect(page.locator('[data-testid="plugin-dependencies"]')).toBeVisible();
      await expect(page.locator('[data-testid="plugin-permissions"]')).toBeVisible();
      await expect(page.locator('[data-testid="plugin-logs"]')).toBeVisible();
    });
  });

  test.describe('Plugin Installation', () => {
    test('should open installation wizard', async ({ page }) => {
      await page.click('[data-testid="install-plugin-button"]');
      
      // Verify wizard steps
      await expect(page.locator('[data-testid="installation-wizard"]')).toBeVisible();
      await expect(page.locator('[data-testid="wizard-step-1"]')).toBeVisible();
      await expect(page.locator('[data-testid="plugin-selection-step"]')).toBeVisible();
    });

    test('should complete plugin installation workflow', async ({ page }) => {
      await pluginHelper.startInstallation();
      
      // Step 1: Plugin Selection
      await page.click('[data-testid="plugin-marketplace-tab"]');
      await page.click('[data-testid="select-plugin-test-analytics"]');
      await page.click('[data-testid="next-step-button"]');
      
      // Step 2: Dependency Resolution
      await expect(page.locator('[data-testid="wizard-step-2"]')).toBeVisible();
      await expect(page.locator('[data-testid="dependency-list"]')).toBeVisible();
      
      // Verify no conflicts
      await expect(page.locator('[data-testid="dependency-conflicts"]')).not.toBeVisible();
      await page.click('[data-testid="next-step-button"]');
      
      // Step 3: Permission Configuration
      await expect(page.locator('[data-testid="wizard-step-3"]')).toBeVisible();
      await expect(page.locator('[data-testid="permission-list"]')).toBeVisible();
      
      // Configure permissions
      await page.check('[data-testid="permission-read-analytics"]');
      await page.check('[data-testid="permission-write-reports"]');
      await page.click('[data-testid="next-step-button"]');
      
      // Step 4: Installation
      await expect(page.locator('[data-testid="wizard-step-4"]')).toBeVisible();
      await page.click('[data-testid="install-button"]');
      
      // Verify installation progress
      await expect(page.locator('[data-testid="installation-progress"]')).toBeVisible();
      await expect(page.locator('[data-testid="installation-success"]')).toBeVisible({ timeout: 30000 });
      
      // Verify plugin appears in list
      await page.click('[data-testid="close-wizard-button"]');
      await expect(page.locator('[data-testid="plugin-test-analytics"]')).toBeVisible();
    });

    test('should handle installation errors gracefully', async ({ page }) => {
      // Mock installation failure
      await page.route('**/api/plugins/install', route => {
        route.fulfill({
          status: 500,
          json: { error: 'Installation failed: Dependency conflict' }
        });
      });
      
      await pluginHelper.startInstallation();
      await pluginHelper.selectPlugin('test-plugin');
      await pluginHelper.proceedThroughSteps();
      
      // Verify error handling
      await expect(page.locator('[data-testid="installation-error"]')).toBeVisible();
      await expect(page.locator('[data-testid="error-message"]')).toContainText('Dependency conflict');
      await expect(page.locator('[data-testid="retry-installation-button"]')).toBeVisible();
    });

    test('should validate plugin dependencies', async ({ page }) => {
      await pluginHelper.startInstallation();
      
      // Select plugin with missing dependencies
      await page.click('[data-testid="select-plugin-advanced-analytics"]');
      await page.click('[data-testid="next-step-button"]');
      
      // Verify dependency validation
      await expect(page.locator('[data-testid="dependency-conflicts"]')).toBeVisible();
      await expect(page.locator('[data-testid="missing-dependency"]')).toBeVisible();
      await expect(page.locator('[data-testid="resolve-dependencies-button"]')).toBeVisible();
      
      // Test dependency resolution
      await page.click('[data-testid="resolve-dependencies-button"]');
      await expect(page.locator('[data-testid="dependency-resolution-progress"]')).toBeVisible();
    });
  });

  test.describe('Plugin Configuration', () => {
    test('should display dynamic configuration forms', async ({ page }) => {
      const configurablePlugin = page.locator('[data-testid="plugin-item-configurable"]');
      await configurablePlugin.click();
      await page.click('[data-testid="configure-plugin-button"]');
      
      // Verify dynamic form generation
      await expect(page.locator('[data-testid="plugin-config-form"]')).toBeVisible();
      await expect(page.locator('[data-testid="config-field-api-key"]')).toBeVisible();
      await expect(page.locator('[data-testid="config-field-endpoint-url"]')).toBeVisible();
      await expect(page.locator('[data-testid="config-field-timeout"]')).toBeVisible();
    });

    test('should validate configuration inputs', async ({ page }) => {
      await pluginHelper.openPluginConfiguration('test-plugin');
      
      // Test invalid URL
      await page.fill('[data-testid="config-field-endpoint-url"]', 'invalid-url');
      await page.click('[data-testid="save-config-button"]');
      
      await expect(page.locator('[data-testid="validation-error-endpoint-url"]')).toBeVisible();
      await expect(page.locator('[data-testid="validation-error-endpoint-url"]')).toContainText('Invalid URL format');
      
      // Test valid configuration
      await page.fill('[data-testid="config-field-endpoint-url"]', 'https://api.example.com');
      await page.fill('[data-testid="config-field-api-key"]', 'test-api-key-123');
      await page.click('[data-testid="save-config-button"]');
      
      await expect(page.locator('[data-testid="config-saved-success"]')).toBeVisible();
    });

    test('should test plugin configuration', async ({ page }) => {
      await pluginHelper.openPluginConfiguration('test-plugin');
      await pluginHelper.fillConfiguration({
        'endpoint-url': 'https://api.example.com',
        'api-key': 'test-key'
      });
      
      await page.click('[data-testid="test-config-button"]');
      
      // Verify configuration test
      await expect(page.locator('[data-testid="config-test-progress"]')).toBeVisible();
      await expect(page.locator('[data-testid="config-test-result"]')).toBeVisible({ timeout: 10000 });
      
      // Check test results
      const testResult = await page.locator('[data-testid="config-test-status"]').textContent();
      expect(['success', 'failure']).toContain(testResult?.toLowerCase());
    });
  });

  test.describe('Plugin Monitoring', () => {
    test('should display plugin performance metrics', async ({ page }) => {
      await page.click('[data-testid="monitoring-tab"]');
      
      // Verify monitoring dashboard
      await expect(page.locator('[data-testid="plugin-metrics-dashboard"]')).toBeVisible();
      await expect(page.locator('[data-testid="cpu-usage-chart"]')).toBeVisible();
      await expect(page.locator('[data-testid="memory-usage-chart"]')).toBeVisible();
      await expect(page.locator('[data-testid="request-count-chart"]')).toBeVisible();
      await expect(page.locator('[data-testid="error-rate-chart"]')).toBeVisible();
    });

    test('should show plugin health status', async ({ page }) => {
      await page.click('[data-testid="monitoring-tab"]');
      
      const pluginHealthItems = await page.locator('[data-testid="plugin-health-item"]').all();
      
      for (const item of pluginHealthItems) {
        await expect(item.locator('[data-testid="plugin-name"]')).toBeVisible();
        await expect(item.locator('[data-testid="health-status"]')).toBeVisible();
        await expect(item.locator('[data-testid="last-check-time"]')).toBeVisible();
        
        const healthStatus = await item.locator('[data-testid="health-status"]').textContent();
        expect(['healthy', 'warning', 'critical']).toContain(healthStatus?.toLowerCase());
      }
    });

    test('should display plugin logs with filtering', async ({ page }) => {
      const firstPlugin = page.locator('[data-testid="plugin-item"]').first();
      await firstPlugin.click();
      await page.click('[data-testid="view-logs-button"]');
      
      // Verify log viewer
      await expect(page.locator('[data-testid="plugin-log-viewer"]')).toBeVisible();
      await expect(page.locator('[data-testid="log-entries"]')).toBeVisible();
      
      // Test log filtering
      await page.selectOption('[data-testid="log-level-filter"]', 'error');
      
      const logEntries = await page.locator('[data-testid="log-entry"]').all();
      for (const entry of logEntries) {
        await expect(entry.locator('[data-testid="log-level-error"]')).toBeVisible();
      }
      
      // Test log search
      await page.fill('[data-testid="log-search-input"]', 'initialization');
      const searchResults = await page.locator('[data-testid="log-entry"]').all();
      
      for (const result of searchResults) {
        const logContent = await result.locator('[data-testid="log-message"]').textContent();
        expect(logContent?.toLowerCase()).toContain('initialization');
      }
    });

    test('should handle plugin alerts and notifications', async ({ page }) => {
      // Simulate plugin alert
      await page.route('**/api/plugins/*/alerts', route => {
        route.fulfill({
          json: {
            alerts: [
              {
                id: 'alert-1',
                severity: 'high',
                message: 'Plugin memory usage exceeded threshold',
                timestamp: new Date().toISOString()
              }
            ]
          }
        });
      });
      
      await page.click('[data-testid="monitoring-tab"]');
      await page.reload();
      
      // Verify alert display
      await expect(page.locator('[data-testid="plugin-alert"]')).toBeVisible();
      await expect(page.locator('[data-testid="alert-severity-high"]')).toBeVisible();
      await expect(page.locator('[data-testid="alert-message"]')).toContainText('memory usage exceeded threshold');
      
      // Test alert acknowledgment
      await page.click('[data-testid="acknowledge-alert-button"]');
      await expect(page.locator('[data-testid="alert-acknowledged"]')).toBeVisible();
    });
  });

  test.describe('Plugin Security and RBAC', () => {
    test('should enforce plugin permissions', async ({ page }) => {
      // Login as regular user
      await authHelper.logout();
      const userCredentials = testData.getUserCredentials();
      await authHelper.login(userCredentials.username, userCredentials.password);
      await page.goto('/plugins');
      
      // Verify limited access
      await expect(page.locator('[data-testid="install-plugin-button"]')).not.toBeVisible();
      await expect(page.locator('[data-testid="plugin-config-button"]')).not.toBeVisible();
      
      // Verify read-only access
      await expect(page.locator('[data-testid="plugin-list"]')).toBeVisible();
      await expect(page.locator('[data-testid="plugin-status"]')).toBeVisible();
    });

    test('should display plugin security information', async ({ page }) => {
      const firstPlugin = page.locator('[data-testid="plugin-item"]').first();
      await firstPlugin.click();
      await page.click('[data-testid="security-tab"]');
      
      // Verify security information
      await expect(page.locator('[data-testid="plugin-permissions-list"]')).toBeVisible();
      await expect(page.locator('[data-testid="security-sandbox-status"]')).toBeVisible();
      await expect(page.locator('[data-testid="plugin-signature-verification"]')).toBeVisible();
      await expect(page.locator('[data-testid="security-audit-log"]')).toBeVisible();
    });

    test('should audit plugin activities', async ({ page }) => {
      await page.click('[data-testid="audit-tab"]');
      
      // Verify audit log
      await expect(page.locator('[data-testid="plugin-audit-log"]')).toBeVisible();
      
      const auditEntries = await page.locator('[data-testid="audit-entry"]').all();
      expect(auditEntries.length).toBeGreaterThan(0);
      
      // Verify audit entry components
      const firstEntry = auditEntries[0];
      await expect(firstEntry.locator('[data-testid="audit-timestamp"]')).toBeVisible();
      await expect(firstEntry.locator('[data-testid="audit-user"]')).toBeVisible();
      await expect(firstEntry.locator('[data-testid="audit-action"]')).toBeVisible();
      await expect(firstEntry.locator('[data-testid="audit-plugin"]')).toBeVisible();
    });
  });
});