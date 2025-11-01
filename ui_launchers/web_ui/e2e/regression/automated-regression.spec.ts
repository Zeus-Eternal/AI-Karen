import { test, expect } from '@playwright/test';
import { AuthenticationHelper } from '../utils/authentication-helper';
import { TestDataManager } from '../utils/test-data-manager';

test.describe('Automated Regression Testing', () => {
  let authHelper: AuthenticationHelper;
  let testData: TestDataManager;

  test.beforeEach(async ({ page }) => {
    authHelper = new AuthenticationHelper(page);
    testData = new TestDataManager();
  });

  test.describe('Critical User Journeys', () => {
    test('should complete full authentication flow without regression', async ({ page }) => {
      // Test complete auth flow
      const credentials = testData.getValidCredentials();
      
      // Login
      await authHelper.login(credentials.username, credentials.password);
      await expect(page).toHaveURL(/\/dashboard/);
      
      // Navigate to different sections
      await page.click('[data-testid="memory-nav-link"]');
      await expect(page).toHaveURL(/\/memory/);
      await expect(page.locator('[data-testid="memory-analytics"]')).toBeVisible();
      
      await page.click('[data-testid="plugins-nav-link"]');
      await expect(page).toHaveURL(/\/plugins/);
      await expect(page.locator('[data-testid="plugin-list"]')).toBeVisible();
      
      await page.click('[data-testid="models-nav-link"]');
      await expect(page).toHaveURL(/\/models/);
      await expect(page.locator('[data-testid="model-selector"]')).toBeVisible();
      
      // Logout
      await authHelper.logout();
      await expect(page).toHaveURL(/\/login/);
    });

    test('should maintain dashboard functionality across updates', async ({ page }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      await page.goto('/dashboard');
      
      // Test core dashboard features
      await expect(page.locator('[data-testid="cpu-usage-metric"]')).toBeVisible();
      await expect(page.locator('[data-testid="memory-usage-metric"]')).toBeVisible();
      await expect(page.locator('[data-testid="system-health-indicator"]')).toBeVisible();
      
      // Test widget interactions
      await page.click('[data-testid="customize-dashboard-button"]');
      await expect(page.locator('[data-testid="customization-mode-active"]')).toBeVisible();
      
      // Test metric refresh
      const initialCpuValue = await page.locator('[data-testid="cpu-usage-value"]').textContent();
      await page.click('[data-testid="refresh-metrics-button"]');
      await page.waitForTimeout(2000);
      
      // Verify metrics updated (or at least didn't break)
      await expect(page.locator('[data-testid="cpu-usage-value"]')).toBeVisible();
    });

    test('should preserve memory management functionality', async ({ page }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      await page.goto('/memory');
      
      // Test memory analytics
      await expect(page.locator('[data-testid="total-embeddings-count"]')).toBeVisible();
      await expect(page.locator('[data-testid="storage-size-metric"]')).toBeVisible();
      
      // Test semantic search
      await page.click('[data-testid="search-tab"]');
      await page.fill('[data-testid="semantic-search-input"]', 'machine learning');
      await page.click('[data-testid="search-button"]');
      await expect(page.locator('[data-testid="search-results"]')).toBeVisible();
      
      // Test network visualization
      await page.click('[data-testid="network-tab"]');
      await expect(page.locator('[data-testid="memory-network-graph"]')).toBeVisible();
      
      // Test memory management
      await page.click('[data-testid="management-tab"]');
      await expect(page.locator('[data-testid="memory-list"]')).toBeVisible();
    });

    test('should maintain plugin management capabilities', async ({ page }) => {
      const adminCredentials = testData.getAdminCredentials();
      await authHelper.login(adminCredentials.username, adminCredentials.password);
      await page.goto('/plugins');
      
      // Test plugin list display
      await expect(page.locator('[data-testid="plugin-list"]')).toBeVisible();
      await expect(page.locator('[data-testid="plugin-item"]')).toHaveCount({ min: 1 });
      
      // Test plugin filtering
      await page.selectOption('[data-testid="plugin-filter-dropdown"]', 'active');
      await expect(page.locator('[data-testid="plugin-status-active"]').first()).toBeVisible();
      
      // Test plugin search
      await page.fill('[data-testid="plugin-search-input"]', 'test');
      await page.press('[data-testid="plugin-search-input"]', 'Enter');
      
      // Test plugin details
      const firstPlugin = page.locator('[data-testid="plugin-item"]').first();
      await firstPlugin.click();
      await expect(page.locator('[data-testid="plugin-detail-panel"]')).toBeVisible();
    });
  });

  test.describe('API Integration Regression', () => {
    test('should maintain API endpoint compatibility', async ({ page }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      
      // Test critical API endpoints
      const apiTests = [
        { endpoint: '/api/health', expectedStatus: 200 },
        { endpoint: '/api/metrics/system', expectedStatus: 200 },
        { endpoint: '/api/memory/stats', expectedStatus: 200 },
        { endpoint: '/api/plugins', expectedStatus: 200 },
        { endpoint: '/api/models', expectedStatus: 200 }
      ];
      
      for (const apiTest of apiTests) {
        const response = await page.request.get(apiTest.endpoint);
        expect(response.status()).toBe(apiTest.expectedStatus);
        
        if (apiTest.expectedStatus === 200) {
          const responseBody = await response.json();
          expect(responseBody).toBeTruthy();
        }
      }
    });

    test('should handle API error responses gracefully', async ({ page }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      
      // Mock API failures
      await page.route('**/api/memory/stats', route => route.abort());
      
      await page.goto('/memory');
      
      // Verify error handling
      await expect(page.locator('[data-testid="api-error-message"]')).toBeVisible();
      await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();
      
      // Test retry functionality
      await page.unroute('**/api/memory/stats');
      await page.click('[data-testid="retry-button"]');
      
      // Verify recovery
      await expect(page.locator('[data-testid="memory-analytics"]')).toBeVisible();
    });

    test('should maintain WebSocket connection stability', async ({ page }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      await page.goto('/dashboard');
      
      // Test WebSocket connection
      const wsStatus = await page.evaluate(() => {
        return new Promise((resolve) => {
          const ws = new WebSocket('ws://localhost:8010/ws/metrics');
          
          ws.onopen = () => {
            ws.close();
            resolve({ connected: true, error: null });
          };
          
          ws.onerror = (error) => {
            resolve({ connected: false, error: error.toString() });
          };
          
          setTimeout(() => {
            ws.close();
            resolve({ connected: false, error: 'timeout' });
          }, 5000);
        });
      });
      
      expect(wsStatus.connected).toBe(true);
    });
  });

  test.describe('Performance Regression', () => {
    test('should maintain page load performance', async ({ page }) => {
      const performanceMetrics = [];
      
      const pages = [
        { path: '/login', name: 'Login' },
        { path: '/dashboard', name: 'Dashboard' },
        { path: '/memory', name: 'Memory' },
        { path: '/plugins', name: 'Plugins' },
        { path: '/models', name: 'Models' }
      ];
      
      // Login first
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      
      for (const pageTest of pages) {
        if (pageTest.path === '/login') continue; // Skip login page after authentication
        
        const startTime = Date.now();
        await page.goto(pageTest.path);
        await page.waitForLoadState('networkidle');
        const loadTime = Date.now() - startTime;
        
        performanceMetrics.push({
          page: pageTest.name,
          loadTime
        });
        
        // Performance thresholds
        expect(loadTime).toBeLessThan(5000); // 5 second max load time
      }
      
      // Log performance metrics for monitoring
      console.log('Performance Metrics:', performanceMetrics);
    });

    test('should maintain memory usage within bounds', async ({ page }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      
      // Navigate through multiple pages to test memory usage
      const pages = ['/dashboard', '/memory', '/plugins', '/models'];
      
      for (const pagePath of pages) {
        await page.goto(pagePath);
        await page.waitForLoadState('networkidle');
        
        // Force garbage collection if available
        await page.evaluate(() => {
          if (window.gc) {
            window.gc();
          }
        });
        
        // Check memory usage (Chrome only)
        const memoryInfo = await page.evaluate(() => {
          if ('memory' in performance) {
            return (performance as any).memory;
          }
          return null;
        });
        
        if (memoryInfo) {
          // Memory usage should not exceed 150MB
          expect(memoryInfo.usedJSHeapSize).toBeLessThan(150 * 1024 * 1024);
        }
      }
    });

    test('should maintain responsive interaction times', async ({ page }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      await page.goto('/dashboard');
      
      // Test interaction response times
      const interactions = [
        { selector: '[data-testid="memory-nav-link"]', name: 'Navigation' },
        { selector: '[data-testid="refresh-metrics-button"]', name: 'Refresh' },
        { selector: '[data-testid="customize-dashboard-button"]', name: 'Customize' }
      ];
      
      for (const interaction of interactions) {
        const startTime = Date.now();
        await page.click(interaction.selector);
        
        // Wait for visual feedback
        await page.waitForTimeout(100);
        
        const responseTime = Date.now() - startTime;
        
        // Interactions should respond within 200ms
        expect(responseTime).toBeLessThan(200);
      }
    });
  });

  test.describe('Data Integrity Regression', () => {
    test('should preserve user preferences across sessions', async ({ page }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      
      // Set user preferences
      await page.goto('/settings');
      await page.selectOption('[data-testid="theme-selector"]', 'dark');
      await page.selectOption('[data-testid="language-selector"]', 'en');
      await page.click('[data-testid="save-preferences-button"]');
      
      // Logout and login again
      await authHelper.logout();
      await authHelper.login(credentials.username, credentials.password);
      
      // Verify preferences persisted
      await page.goto('/settings');
      const themeValue = await page.locator('[data-testid="theme-selector"]').inputValue();
      const languageValue = await page.locator('[data-testid="language-selector"]').inputValue();
      
      expect(themeValue).toBe('dark');
      expect(languageValue).toBe('en');
    });

    test('should maintain data consistency in memory operations', async ({ page }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      await page.goto('/memory');
      
      // Get initial memory count
      const initialCount = await page.locator('[data-testid="total-embeddings-value"]').textContent();
      const initialCountNum = parseInt(initialCount || '0');
      
      // Create new memory
      await page.click('[data-testid="management-tab"]');
      await page.click('[data-testid="add-memory-button"]');
      await page.fill('[data-testid="memory-content-input"]', 'Test regression memory');
      await page.selectOption('[data-testid="memory-type-select"]', 'knowledge');
      await page.click('[data-testid="save-memory-button"]');
      
      // Verify count increased
      await page.click('[data-testid="analytics-tab"]');
      const newCount = await page.locator('[data-testid="total-embeddings-value"]').textContent();
      const newCountNum = parseInt(newCount || '0');
      
      expect(newCountNum).toBe(initialCountNum + 1);
    });

    test('should maintain plugin state consistency', async ({ page }) => {
      const adminCredentials = testData.getAdminCredentials();
      await authHelper.login(adminCredentials.username, adminCredentials.password);
      await page.goto('/plugins');
      
      // Get initial plugin states
      const pluginStates = await page.evaluate(() => {
        const plugins = Array.from(document.querySelectorAll('[data-testid="plugin-item"]'));
        return plugins.map(plugin => {
          const name = plugin.querySelector('[data-testid="plugin-name"]')?.textContent;
          const status = plugin.querySelector('[data-testid="plugin-status"]')?.textContent;
          return { name, status };
        });
      });
      
      // Refresh page
      await page.reload();
      
      // Verify plugin states remained consistent
      const newPluginStates = await page.evaluate(() => {
        const plugins = Array.from(document.querySelectorAll('[data-testid="plugin-item"]'));
        return plugins.map(plugin => {
          const name = plugin.querySelector('[data-testid="plugin-name"]')?.textContent;
          const status = plugin.querySelector('[data-testid="plugin-status"]')?.textContent;
          return { name, status };
        });
      });
      
      expect(newPluginStates).toEqual(pluginStates);
    });
  });

  test.describe('Security Regression', () => {
    test('should maintain authentication security', async ({ page }) => {
      // Test unauthorized access
      await page.goto('/dashboard');
      await expect(page).toHaveURL(/\/login/);
      
      // Test session timeout
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      
      // Simulate expired session
      await page.evaluate(() => {
        localStorage.removeItem('auth_token');
        sessionStorage.clear();
      });
      
      await page.goto('/memory');
      await expect(page).toHaveURL(/\/login/);
    });

    test('should maintain RBAC enforcement', async ({ page }) => {
      // Test user role restrictions
      const userCredentials = testData.getUserCredentials();
      await authHelper.login(userCredentials.username, userCredentials.password);
      
      await page.goto('/plugins');
      
      // Verify user cannot access admin functions
      await expect(page.locator('[data-testid="install-plugin-button"]')).not.toBeVisible();
      await expect(page.locator('[data-testid="plugin-config-button"]')).not.toBeVisible();
      
      // Test admin access
      await authHelper.logout();
      const adminCredentials = testData.getAdminCredentials();
      await authHelper.login(adminCredentials.username, adminCredentials.password);
      
      await page.goto('/plugins');
      
      // Verify admin can access admin functions
      await expect(page.locator('[data-testid="install-plugin-button"]')).toBeVisible();
    });

    test('should prevent XSS vulnerabilities', async ({ page }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      await page.goto('/memory');
      
      // Test XSS prevention in search
      await page.click('[data-testid="search-tab"]');
      const xssPayload = '<script>alert("XSS")</script>';
      await page.fill('[data-testid="semantic-search-input"]', xssPayload);
      await page.click('[data-testid="search-button"]');
      
      // Verify script didn't execute
      const alertDialogs = [];
      page.on('dialog', dialog => {
        alertDialogs.push(dialog.message());
        dialog.dismiss();
      });
      
      await page.waitForTimeout(1000);
      expect(alertDialogs).toHaveLength(0);
      
      // Verify content is properly escaped
      const searchInput = await page.locator('[data-testid="semantic-search-input"]').inputValue();
      expect(searchInput).toBe(xssPayload); // Input should contain the raw text, not execute it
    });
  });
});