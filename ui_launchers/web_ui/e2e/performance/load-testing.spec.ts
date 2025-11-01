import { test, expect } from '@playwright/test';
import { AuthenticationHelper } from '../utils/authentication-helper';
import { TestDataManager } from '../utils/test-data-manager';

test.describe('Load Testing', () => {
  let authHelper: AuthenticationHelper;
  let testData: TestDataManager;

  test.beforeEach(async ({ page }) => {
    authHelper = new AuthenticationHelper(page);
    testData = new TestDataManager();
  });

  test.describe('Concurrent User Load Testing', () => {
    test('should handle 10 concurrent users on dashboard', async ({ browser }) => {
      const credentials = testData.getValidCredentials();
      const concurrentUsers = 10;
      const userSessions = [];
      
      // Create concurrent user sessions
      for (let i = 0; i < concurrentUsers; i++) {
        const context = await browser.newContext();
        const page = await context.newPage();
        const userAuthHelper = new AuthenticationHelper(page);
        
        userSessions.push({
          page,
          context,
          authHelper: userAuthHelper,
          userId: i + 1
        });
      }
      
      // Measure concurrent login performance
      const loginStartTime = Date.now();
      
      await Promise.all(userSessions.map(async (session) => {
        await session.authHelper.login(credentials.username, credentials.password);
        await expect(session.page).toHaveURL(/\/dashboard/);
      }));
      
      const loginDuration = Date.now() - loginStartTime;
      console.log(`Concurrent login duration: ${loginDuration}ms for ${concurrentUsers} users`);
      
      // Measure concurrent dashboard loading
      const dashboardStartTime = Date.now();
      
      await Promise.all(userSessions.map(async (session) => {
        await session.page.goto('/dashboard');
        await session.page.waitForLoadState('networkidle');
        await expect(session.page.locator('[data-testid="dashboard-loaded"]')).toBeVisible();
      }));
      
      const dashboardDuration = Date.now() - dashboardStartTime;
      console.log(`Concurrent dashboard load duration: ${dashboardDuration}ms for ${concurrentUsers} users`);
      
      // Verify all users can interact with dashboard
      await Promise.all(userSessions.map(async (session) => {
        await expect(session.page.locator('[data-testid="cpu-usage-metric"]')).toBeVisible();
        await expect(session.page.locator('[data-testid="memory-usage-metric"]')).toBeVisible();
      }));
      
      // Performance assertions
      expect(loginDuration).toBeLessThan(30000); // 30 seconds for all logins
      expect(dashboardDuration).toBeLessThan(20000); // 20 seconds for all dashboard loads
      
      // Cleanup
      await Promise.all(userSessions.map(session => session.context.close()));
    });

    test('should handle concurrent memory searches', async ({ browser }) => {
      const credentials = testData.getValidCredentials();
      const concurrentUsers = 5;
      const userSessions = [];
      
      // Setup concurrent users
      for (let i = 0; i < concurrentUsers; i++) {
        const context = await browser.newContext();
        const page = await context.newPage();
        const userAuthHelper = new AuthenticationHelper(page);
        
        await userAuthHelper.login(credentials.username, credentials.password);
        await page.goto('/memory');
        await page.click('[data-testid="search-tab"]');
        
        userSessions.push({ page, context, userId: i + 1 });
      }
      
      // Perform concurrent searches
      const searchQueries = [
        'machine learning',
        'neural networks',
        'deep learning',
        'artificial intelligence',
        'natural language processing'
      ];
      
      const searchStartTime = Date.now();
      
      await Promise.all(userSessions.map(async (session, index) => {
        const query = searchQueries[index % searchQueries.length];
        await session.page.fill('[data-testid="semantic-search-input"]', query);
        await session.page.click('[data-testid="search-button"]');
        await expect(session.page.locator('[data-testid="search-results"]')).toBeVisible();
      }));
      
      const searchDuration = Date.now() - searchStartTime;
      console.log(`Concurrent search duration: ${searchDuration}ms for ${concurrentUsers} users`);
      
      // Verify search results quality
      for (const session of userSessions) {
        const resultCount = await session.page.locator('[data-testid="search-result-item"]').count();
        expect(resultCount).toBeGreaterThan(0);
      }
      
      // Performance assertion
      expect(searchDuration).toBeLessThan(15000); // 15 seconds for all searches
      
      // Cleanup
      await Promise.all(userSessions.map(session => session.context.close()));
    });

    test('should handle concurrent plugin operations', async ({ browser }) => {
      const adminCredentials = testData.getAdminCredentials();
      const concurrentAdmins = 3;
      const adminSessions = [];
      
      // Setup concurrent admin sessions
      for (let i = 0; i < concurrentAdmins; i++) {
        const context = await browser.newContext();
        const page = await context.newPage();
        const adminAuthHelper = new AuthenticationHelper(page);
        
        await adminAuthHelper.login(adminCredentials.username, adminCredentials.password);
        await page.goto('/plugins');
        
        adminSessions.push({ page, context, adminId: i + 1 });
      }
      
      // Perform concurrent plugin operations
      const operationStartTime = Date.now();
      
      await Promise.all(adminSessions.map(async (session, index) => {
        // Different operations for each admin
        switch (index % 3) {
          case 0:
            // View plugin list
            await expect(session.page.locator('[data-testid="plugin-list"]')).toBeVisible();
            await session.page.selectOption('[data-testid="plugin-filter-dropdown"]', 'active');
            break;
          case 1:
            // View plugin monitoring
            await session.page.click('[data-testid="monitoring-tab"]');
            await expect(session.page.locator('[data-testid="plugin-metrics-dashboard"]')).toBeVisible();
            break;
          case 2:
            // View plugin details
            const firstPlugin = session.page.locator('[data-testid="plugin-item"]').first();
            await firstPlugin.click();
            await expect(session.page.locator('[data-testid="plugin-detail-panel"]')).toBeVisible();
            break;
        }
      }));
      
      const operationDuration = Date.now() - operationStartTime;
      console.log(`Concurrent plugin operations duration: ${operationDuration}ms for ${concurrentAdmins} admins`);
      
      // Performance assertion
      expect(operationDuration).toBeLessThan(10000); // 10 seconds for all operations
      
      // Cleanup
      await Promise.all(adminSessions.map(session => session.context.close()));
    });
  });

  test.describe('High Volume Data Load Testing', () => {
    test('should handle large memory dataset', async ({ page }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      
      // Mock large dataset response
      await page.route('**/api/memory/list', route => {
        const largeDataset = {
          memories: Array(1000).fill(null).map((_, i) => ({
            id: `memory-${i}`,
            content: `Memory content ${i} with detailed information about various topics`,
            type: ['knowledge', 'conversation', 'document'][i % 3],
            tags: [`tag-${i % 10}`, `category-${i % 5}`],
            timestamp: new Date(Date.now() - i * 60000).toISOString(),
            similarity: Math.random()
          })),
          total: 1000,
          page: 1,
          pageSize: 50
        };
        
        route.fulfill({
          json: largeDataset,
          headers: { 'Content-Type': 'application/json' }
        });
      });
      
      const loadStartTime = Date.now();
      
      await page.goto('/memory');
      await page.click('[data-testid="management-tab"]');
      
      // Wait for large dataset to load
      await expect(page.locator('[data-testid="memory-list"]')).toBeVisible();
      await expect(page.locator('[data-testid="memory-item"]')).toHaveCount({ min: 50 });
      
      const loadDuration = Date.now() - loadStartTime;
      console.log(`Large dataset load duration: ${loadDuration}ms for 1000 items`);
      
      // Test pagination performance
      const paginationStartTime = Date.now();
      
      await page.click('[data-testid="next-page-button"]');
      await expect(page.locator('[data-testid="memory-item"]')).toHaveCount({ min: 50 });
      
      const paginationDuration = Date.now() - paginationStartTime;
      console.log(`Pagination duration: ${paginationDuration}ms`);
      
      // Performance assertions
      expect(loadDuration).toBeLessThan(5000); // 5 seconds for initial load
      expect(paginationDuration).toBeLessThan(2000); // 2 seconds for pagination
    });

    test('should handle large plugin list', async ({ page }) => {
      const adminCredentials = testData.getAdminCredentials();
      await authHelper.login(adminCredentials.username, adminCredentials.password);
      
      // Mock large plugin dataset
      await page.route('**/api/plugins', route => {
        const largePluginList = {
          plugins: Array(200).fill(null).map((_, i) => ({
            id: `plugin-${i}`,
            name: `Plugin ${i}`,
            version: `1.${i % 10}.0`,
            status: ['active', 'inactive', 'error'][i % 3],
            category: ['analytics', 'utility', 'integration'][i % 3],
            description: `Description for plugin ${i}`,
            metrics: {
              cpuUsage: Math.random() * 100,
              memoryUsage: Math.random() * 1000,
              requestCount: Math.floor(Math.random() * 10000)
            }
          })),
          total: 200
        };
        
        route.fulfill({
          json: largePluginList,
          headers: { 'Content-Type': 'application/json' }
        });
      });
      
      const loadStartTime = Date.now();
      
      await page.goto('/plugins');
      await expect(page.locator('[data-testid="plugin-list"]')).toBeVisible();
      
      const loadDuration = Date.now() - loadStartTime;
      console.log(`Large plugin list load duration: ${loadDuration}ms for 200 plugins`);
      
      // Test filtering performance
      const filterStartTime = Date.now();
      
      await page.selectOption('[data-testid="plugin-filter-dropdown"]', 'active');
      await expect(page.locator('[data-testid="plugin-status-active"]').first()).toBeVisible();
      
      const filterDuration = Date.now() - filterStartTime;
      console.log(`Plugin filtering duration: ${filterDuration}ms`);
      
      // Test search performance
      const searchStartTime = Date.now();
      
      await page.fill('[data-testid="plugin-search-input"]', 'Plugin 1');
      await page.press('[data-testid="plugin-search-input"]', 'Enter');
      
      const searchDuration = Date.now() - searchStartTime;
      console.log(`Plugin search duration: ${searchDuration}ms`);
      
      // Performance assertions
      expect(loadDuration).toBeLessThan(3000); // 3 seconds for large list
      expect(filterDuration).toBeLessThan(1000); // 1 second for filtering
      expect(searchDuration).toBeLessThan(1000); // 1 second for search
    });
  });

  test.describe('Stress Testing', () => {
    test('should handle rapid navigation between pages', async ({ page }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      
      const pages = ['/dashboard', '/memory', '/plugins', '/models', '/settings'];
      const navigationCount = 20;
      const navigationTimes = [];
      
      for (let i = 0; i < navigationCount; i++) {
        const targetPage = pages[i % pages.length];
        const startTime = Date.now();
        
        await page.goto(targetPage);
        await page.waitForLoadState('networkidle');
        
        const duration = Date.now() - startTime;
        navigationTimes.push(duration);
        
        console.log(`Navigation ${i + 1} to ${targetPage}: ${duration}ms`);
      }
      
      const averageNavigationTime = navigationTimes.reduce((a, b) => a + b, 0) / navigationTimes.length;
      const maxNavigationTime = Math.max(...navigationTimes);
      
      console.log(`Average navigation time: ${averageNavigationTime}ms`);
      console.log(`Max navigation time: ${maxNavigationTime}ms`);
      
      // Performance assertions
      expect(averageNavigationTime).toBeLessThan(2000); // 2 seconds average
      expect(maxNavigationTime).toBeLessThan(5000); // 5 seconds max
    });

    test('should handle rapid API requests', async ({ page }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      
      await page.goto('/dashboard');
      
      // Simulate rapid refresh requests
      const requestCount = 50;
      const requestTimes = [];
      
      for (let i = 0; i < requestCount; i++) {
        const startTime = Date.now();
        
        await page.click('[data-testid="refresh-metrics-button"]');
        await page.waitForResponse(response => 
          response.url().includes('/api/metrics/system') && response.status() === 200
        );
        
        const duration = Date.now() - startTime;
        requestTimes.push(duration);
        
        if (i % 10 === 0) {
          console.log(`Request ${i + 1}: ${duration}ms`);
        }
        
        // Small delay to prevent overwhelming the server
        await page.waitForTimeout(100);
      }
      
      const averageRequestTime = requestTimes.reduce((a, b) => a + b, 0) / requestTimes.length;
      const maxRequestTime = Math.max(...requestTimes);
      const failedRequests = requestTimes.filter(time => time > 10000).length;
      
      console.log(`Average request time: ${averageRequestTime}ms`);
      console.log(`Max request time: ${maxRequestTime}ms`);
      console.log(`Failed requests (>10s): ${failedRequests}`);
      
      // Performance assertions
      expect(averageRequestTime).toBeLessThan(1000); // 1 second average
      expect(failedRequests).toBe(0); // No failed requests
    });

    test('should handle memory-intensive operations', async ({ page }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      
      await page.goto('/memory');
      await page.click('[data-testid="network-tab"]');
      
      // Wait for network visualization to load
      await expect(page.locator('[data-testid="memory-network-graph"]')).toBeVisible();
      
      // Simulate memory-intensive operations
      const operations = [
        () => page.click('[data-testid="zoom-in-button"]'),
        () => page.click('[data-testid="zoom-out-button"]'),
        () => page.selectOption('[data-testid="layout-algorithm-selector"]', 'force-directed'),
        () => page.selectOption('[data-testid="layout-algorithm-selector"]', 'hierarchical'),
        () => page.fill('[data-testid="network-search-input"]', 'test search'),
        () => page.click('[data-testid="reset-view-button"]')
      ];
      
      const operationTimes = [];
      
      for (let i = 0; i < 30; i++) {
        const operation = operations[i % operations.length];
        const startTime = Date.now();
        
        await operation();
        await page.waitForTimeout(500); // Allow operation to complete
        
        const duration = Date.now() - startTime;
        operationTimes.push(duration);
        
        if (i % 5 === 0) {
          console.log(`Memory operation ${i + 1}: ${duration}ms`);
        }
      }
      
      const averageOperationTime = operationTimes.reduce((a, b) => a + b, 0) / operationTimes.length;
      const maxOperationTime = Math.max(...operationTimes);
      
      console.log(`Average memory operation time: ${averageOperationTime}ms`);
      console.log(`Max memory operation time: ${maxOperationTime}ms`);
      
      // Check for memory leaks (simplified)
      const memoryInfo = await page.evaluate(() => {
        if ('memory' in performance) {
          return (performance as any).memory;
        }
        return null;
      });
      
      if (memoryInfo) {
        console.log(`JS Heap Size: ${memoryInfo.usedJSHeapSize / 1024 / 1024}MB`);
        expect(memoryInfo.usedJSHeapSize).toBeLessThan(200 * 1024 * 1024); // 200MB limit
      }
      
      // Performance assertions
      expect(averageOperationTime).toBeLessThan(2000); // 2 seconds average
      expect(maxOperationTime).toBeLessThan(5000); // 5 seconds max
    });
  });

  test.describe('Resource Usage Testing', () => {
    test('should monitor CPU and memory usage during heavy operations', async ({ page }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      
      // Start monitoring
      const performanceMetrics = [];
      
      const monitorPerformance = async () => {
        const metrics = await page.evaluate(() => {
          if ('memory' in performance) {
            const memory = (performance as any).memory;
            return {
              timestamp: Date.now(),
              usedJSHeapSize: memory.usedJSHeapSize,
              totalJSHeapSize: memory.totalJSHeapSize,
              jsHeapSizeLimit: memory.jsHeapSizeLimit
            };
          }
          return null;
        });
        
        if (metrics) {
          performanceMetrics.push(metrics);
        }
      };
      
      // Monitor performance during heavy operations
      const monitoringInterval = setInterval(monitorPerformance, 1000);
      
      try {
        // Perform heavy operations
        await page.goto('/memory');
        await monitorPerformance();
        
        await page.click('[data-testid="network-tab"]');
        await expect(page.locator('[data-testid="memory-network-graph"]')).toBeVisible();
        await monitorPerformance();
        
        // Simulate complex network interactions
        for (let i = 0; i < 10; i++) {
          await page.selectOption('[data-testid="layout-algorithm-selector"]', 'force-directed');
          await page.waitForTimeout(1000);
          await page.selectOption('[data-testid="layout-algorithm-selector"]', 'hierarchical');
          await page.waitForTimeout(1000);
          await monitorPerformance();
        }
        
        // Navigate to other heavy pages
        await page.goto('/plugins');
        await page.click('[data-testid="monitoring-tab"]');
        await expect(page.locator('[data-testid="plugin-metrics-dashboard"]')).toBeVisible();
        await monitorPerformance();
        
      } finally {
        clearInterval(monitoringInterval);
      }
      
      // Analyze performance metrics
      if (performanceMetrics.length > 0) {
        const initialMemory = performanceMetrics[0].usedJSHeapSize;
        const finalMemory = performanceMetrics[performanceMetrics.length - 1].usedJSHeapSize;
        const maxMemory = Math.max(...performanceMetrics.map(m => m.usedJSHeapSize));
        const memoryGrowth = finalMemory - initialMemory;
        
        console.log(`Initial memory: ${initialMemory / 1024 / 1024}MB`);
        console.log(`Final memory: ${finalMemory / 1024 / 1024}MB`);
        console.log(`Max memory: ${maxMemory / 1024 / 1024}MB`);
        console.log(`Memory growth: ${memoryGrowth / 1024 / 1024}MB`);
        
        // Performance assertions
        expect(maxMemory).toBeLessThan(300 * 1024 * 1024); // 300MB max
        expect(memoryGrowth).toBeLessThan(100 * 1024 * 1024); // 100MB growth max
      }
    });

    test('should handle network latency simulation', async ({ page }) => {
      const credentials = testData.getValidCredentials();
      
      // Simulate slow network conditions
      await page.route('**/api/**', async route => {
        // Add artificial delay
        await new Promise(resolve => setTimeout(resolve, 1000));
        route.continue();
      });
      
      const startTime = Date.now();
      
      await authHelper.login(credentials.username, credentials.password);
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');
      
      const loadTime = Date.now() - startTime;
      console.log(`Load time with network latency: ${loadTime}ms`);
      
      // Verify application still functions under slow network
      await expect(page.locator('[data-testid="dashboard-loaded"]')).toBeVisible();
      await expect(page.locator('[data-testid="cpu-usage-metric"]')).toBeVisible();
      
      // Test interaction responsiveness
      const interactionStartTime = Date.now();
      
      await page.click('[data-testid="memory-nav-link"]');
      await expect(page).toHaveURL(/\/memory/);
      
      const interactionTime = Date.now() - interactionStartTime;
      console.log(`Interaction time with network latency: ${interactionTime}ms`);
      
      // Performance assertions (adjusted for network latency)
      expect(loadTime).toBeLessThan(15000); // 15 seconds with latency
      expect(interactionTime).toBeLessThan(5000); // 5 seconds for navigation
    });
  });
});