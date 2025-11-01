import { test, expect } from '@playwright/test';
import { AuthenticationHelper } from '../utils/authentication-helper';
import { TestDataManager } from '../utils/test-data-manager';

test.describe('Stress Testing', () => {
  let authHelper: AuthenticationHelper;
  let testData: TestDataManager;

  test.beforeEach(async ({ page }) => {
    authHelper = new AuthenticationHelper(page);
    testData = new TestDataManager();
  });

  test.describe('System Limit Identification', () => {
    test('should identify maximum concurrent WebSocket connections', async ({ browser }) => {
      const credentials = testData.getValidCredentials();
      const maxConnections = 50;
      const connections = [];
      let successfulConnections = 0;
      let failedConnections = 0;
      
      console.log(`Testing up to ${maxConnections} concurrent WebSocket connections...`);
      
      for (let i = 0; i < maxConnections; i++) {
        try {
          const context = await browser.newContext();
          const page = await context.newPage();
          const userAuthHelper = new AuthenticationHelper(page);
          
          await userAuthHelper.login(credentials.username, credentials.password);
          await page.goto('/dashboard');
          
          // Test WebSocket connection
          const wsConnected = await page.evaluate(() => {
            return new Promise((resolve) => {
              try {
                const ws = new WebSocket('ws://localhost:8010/ws/metrics');
                
                ws.onopen = () => {
                  resolve(true);
                };
                
                ws.onerror = () => {
                  resolve(false);
                };
                
                setTimeout(() => {
                  ws.close();
                  resolve(false);
                }, 5000);
              } catch (error) {
                resolve(false);
              }
            });
          });
          
          if (wsConnected) {
            successfulConnections++;
            connections.push({ page, context, connected: true });
          } else {
            failedConnections++;
            connections.push({ page, context, connected: false });
            await context.close();
          }
          
          if (i % 10 === 0) {
            console.log(`Connection ${i + 1}: ${wsConnected ? 'Success' : 'Failed'}`);
          }
          
        } catch (error) {
          failedConnections++;
          console.error(`Connection ${i + 1} error:`, error.message);
        }
      }
      
      console.log(`Successful connections: ${successfulConnections}`);
      console.log(`Failed connections: ${failedConnections}`);
      console.log(`Connection success rate: ${(successfulConnections / maxConnections * 100).toFixed(2)}%`);
      
      // Cleanup
      for (const connection of connections) {
        if (connection.connected) {
          await connection.context.close();
        }
      }
      
      // Assertions
      expect(successfulConnections).toBeGreaterThan(20); // At least 20 concurrent connections
      expect(successfulConnections / maxConnections).toBeGreaterThan(0.8); // 80% success rate
    });

    test('should identify memory usage limits', async ({ page }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      
      const memorySnapshots = [];
      let operationCount = 0;
      const maxOperations = 100;
      
      // Monitor memory usage during intensive operations
      const monitorMemory = async () => {
        const memoryInfo = await page.evaluate(() => {
          if ('memory' in performance) {
            const memory = (performance as any).memory;
            return {
              usedJSHeapSize: memory.usedJSHeapSize,
              totalJSHeapSize: memory.totalJSHeapSize,
              jsHeapSizeLimit: memory.jsHeapSizeLimit
            };
          }
          return null;
        });
        
        if (memoryInfo) {
          memorySnapshots.push({
            operation: operationCount,
            ...memoryInfo,
            timestamp: Date.now()
          });
        }
      };
      
      await page.goto('/memory');
      await page.click('[data-testid="network-tab"]');
      await expect(page.locator('[data-testid="memory-network-graph"]')).toBeVisible();
      
      await monitorMemory(); // Initial snapshot
      
      // Perform memory-intensive operations
      for (let i = 0; i < maxOperations; i++) {
        operationCount = i + 1;
        
        try {
          // Cycle through different layouts to stress memory
          await page.selectOption('[data-testid="layout-algorithm-selector"]', 'force-directed');
          await page.waitForTimeout(200);
          
          await page.selectOption('[data-testid="layout-algorithm-selector"]', 'hierarchical');
          await page.waitForTimeout(200);
          
          // Zoom operations
          await page.click('[data-testid="zoom-in-button"]');
          await page.waitForTimeout(100);
          
          await page.click('[data-testid="zoom-out-button"]');
          await page.waitForTimeout(100);
          
          // Search operations
          await page.fill('[data-testid="network-search-input"]', `search-${i}`);
          await page.click('[data-testid="network-search-button"]');
          await page.waitForTimeout(200);
          
          // Monitor memory every 10 operations
          if (i % 10 === 0) {
            await monitorMemory();
            
            const currentMemory = memorySnapshots[memorySnapshots.length - 1];
            console.log(`Operation ${i}: ${(currentMemory.usedJSHeapSize / 1024 / 1024).toFixed(2)}MB`);
            
            // Break if memory usage is too high
            if (currentMemory.usedJSHeapSize > 400 * 1024 * 1024) { // 400MB limit
              console.log(`Memory limit reached at operation ${i}`);
              break;
            }
          }
          
        } catch (error) {
          console.error(`Operation ${i} failed:`, error.message);
          break;
        }
      }
      
      await monitorMemory(); // Final snapshot
      
      // Analyze memory usage patterns
      if (memorySnapshots.length > 1) {
        const initialMemory = memorySnapshots[0].usedJSHeapSize;
        const finalMemory = memorySnapshots[memorySnapshots.length - 1].usedJSHeapSize;
        const maxMemory = Math.max(...memorySnapshots.map(s => s.usedJSHeapSize));
        const memoryGrowth = finalMemory - initialMemory;
        const averageGrowthPerOperation = memoryGrowth / operationCount;
        
        console.log(`Memory Analysis:`);
        console.log(`  Initial: ${(initialMemory / 1024 / 1024).toFixed(2)}MB`);
        console.log(`  Final: ${(finalMemory / 1024 / 1024).toFixed(2)}MB`);
        console.log(`  Peak: ${(maxMemory / 1024 / 1024).toFixed(2)}MB`);
        console.log(`  Growth: ${(memoryGrowth / 1024 / 1024).toFixed(2)}MB`);
        console.log(`  Avg growth per operation: ${(averageGrowthPerOperation / 1024).toFixed(2)}KB`);
        console.log(`  Operations completed: ${operationCount}`);
        
        // Memory leak detection
        const memoryLeakThreshold = 200 * 1024 * 1024; // 200MB
        expect(memoryGrowth).toBeLessThan(memoryLeakThreshold);
        expect(maxMemory).toBeLessThan(500 * 1024 * 1024); // 500MB absolute limit
      }
    });

    test('should identify API rate limits', async ({ page }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      
      await page.goto('/dashboard');
      
      const requestResults = [];
      const maxRequests = 200;
      const requestInterval = 50; // 50ms between requests
      
      console.log(`Testing API rate limits with ${maxRequests} requests...`);
      
      for (let i = 0; i < maxRequests; i++) {
        const startTime = Date.now();
        
        try {
          const response = await page.request.get('/api/metrics/system');
          const endTime = Date.now();
          
          requestResults.push({
            requestNumber: i + 1,
            status: response.status(),
            duration: endTime - startTime,
            timestamp: startTime
          });
          
          if (i % 20 === 0) {
            console.log(`Request ${i + 1}: ${response.status()} (${endTime - startTime}ms)`);
          }
          
          // Check for rate limiting
          if (response.status() === 429) {
            console.log(`Rate limit hit at request ${i + 1}`);
            break;
          }
          
          await page.waitForTimeout(requestInterval);
          
        } catch (error) {
          requestResults.push({
            requestNumber: i + 1,
            status: 0,
            duration: -1,
            error: error.message,
            timestamp: startTime
          });
          
          console.error(`Request ${i + 1} failed:`, error.message);
        }
      }
      
      // Analyze results
      const successfulRequests = requestResults.filter(r => r.status === 200);
      const rateLimitedRequests = requestResults.filter(r => r.status === 429);
      const failedRequests = requestResults.filter(r => r.status !== 200 && r.status !== 429);
      
      const averageResponseTime = successfulRequests.reduce((sum, r) => sum + r.duration, 0) / successfulRequests.length;
      const maxResponseTime = Math.max(...successfulRequests.map(r => r.duration));
      
      console.log(`API Rate Limit Analysis:`);
      console.log(`  Total requests: ${requestResults.length}`);
      console.log(`  Successful: ${successfulRequests.length}`);
      console.log(`  Rate limited: ${rateLimitedRequests.length}`);
      console.log(`  Failed: ${failedRequests.length}`);
      console.log(`  Average response time: ${averageResponseTime.toFixed(2)}ms`);
      console.log(`  Max response time: ${maxResponseTime}ms`);
      console.log(`  Success rate: ${(successfulRequests.length / requestResults.length * 100).toFixed(2)}%`);
      
      // Assertions
      expect(successfulRequests.length).toBeGreaterThan(100); // At least 100 successful requests
      expect(averageResponseTime).toBeLessThan(1000); // Average under 1 second
      expect(maxResponseTime).toBeLessThan(5000); // Max under 5 seconds
    });
  });

  test.describe('Failure Point Analysis', () => {
    test('should handle database connection failures', async ({ page }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      
      // Simulate database connection failure
      await page.route('**/api/memory/**', route => {
        route.fulfill({
          status: 503,
          json: { error: 'Database connection failed' }
        });
      });
      
      await page.goto('/memory');
      
      // Verify graceful error handling
      await expect(page.locator('[data-testid="database-error"]')).toBeVisible();
      await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();
      
      // Test error recovery
      await page.unroute('**/api/memory/**');
      await page.click('[data-testid="retry-button"]');
      
      // Verify recovery
      await expect(page.locator('[data-testid="memory-analytics"]')).toBeVisible();
    });

    test('should handle memory exhaustion scenarios', async ({ page }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      
      // Create memory pressure by loading large datasets
      await page.route('**/api/memory/network', route => {
        const largeNetwork = {
          nodes: Array(10000).fill(null).map((_, i) => ({
            id: `node-${i}`,
            label: `Node ${i}`,
            cluster: `cluster-${i % 100}`,
            data: Array(1000).fill(i).join('') // Large data payload
          })),
          edges: Array(50000).fill(null).map((_, i) => ({
            source: `node-${i % 10000}`,
            target: `node-${(i + 1) % 10000}`,
            weight: Math.random()
          }))
        };
        
        route.fulfill({
          json: largeNetwork,
          headers: { 'Content-Type': 'application/json' }
        });
      });
      
      await page.goto('/memory');
      await page.click('[data-testid="network-tab"]');
      
      // Monitor for memory exhaustion
      let memoryExhausted = false;
      
      try {
        await expect(page.locator('[data-testid="memory-network-graph"]')).toBeVisible({ timeout: 30000 });
        
        // Check if the application handled the large dataset
        const nodeCount = await page.locator('[data-testid="memory-node"]').count();
        console.log(`Rendered nodes: ${nodeCount}`);
        
        // Test interaction with large dataset
        await page.click('[data-testid="zoom-in-button"]');
        await page.waitForTimeout(2000);
        
      } catch (error) {
        memoryExhausted = true;
        console.log('Memory exhaustion detected:', error.message);
        
        // Verify error handling
        await expect(page.locator('[data-testid="memory-error"]')).toBeVisible();
      }
      
      // Check final memory state
      const finalMemory = await page.evaluate(() => {
        if ('memory' in performance) {
          return (performance as any).memory.usedJSHeapSize;
        }
        return null;
      });
      
      if (finalMemory) {
        console.log(`Final memory usage: ${(finalMemory / 1024 / 1024).toFixed(2)}MB`);
        
        // Even under stress, memory should not exceed reasonable limits
        expect(finalMemory).toBeLessThan(1000 * 1024 * 1024); // 1GB limit
      }
    });

    test('should handle network partition scenarios', async ({ page }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      
      await page.goto('/dashboard');
      await expect(page.locator('[data-testid="dashboard-loaded"]')).toBeVisible();
      
      // Simulate network partition
      await page.route('**/api/**', route => route.abort());
      await page.route('**/ws/**', route => route.abort());
      
      // Test application behavior during network partition
      await page.click('[data-testid="refresh-metrics-button"]');
      
      // Verify offline handling
      await expect(page.locator('[data-testid="offline-indicator"]')).toBeVisible();
      await expect(page.locator('[data-testid="network-error-message"]')).toBeVisible();
      
      // Test cached data availability
      await expect(page.locator('[data-testid="cached-data-indicator"]')).toBeVisible();
      
      // Simulate network recovery
      await page.unroute('**/api/**');
      await page.unroute('**/ws/**');
      
      await page.click('[data-testid="retry-connection-button"]');
      
      // Verify recovery
      await expect(page.locator('[data-testid="online-indicator"]')).toBeVisible();
      await expect(page.locator('[data-testid="dashboard-loaded"]')).toBeVisible();
    });

    test('should handle concurrent user limit', async ({ browser }) => {
      const maxUsers = 100;
      const userSessions = [];
      let successfulLogins = 0;
      let failedLogins = 0;
      
      console.log(`Testing concurrent user limit with ${maxUsers} users...`);
      
      // Create concurrent user sessions
      const loginPromises = Array(maxUsers).fill(null).map(async (_, i) => {
        try {
          const context = await browser.newContext();
          const page = await context.newPage();
          const userAuthHelper = new AuthenticationHelper(page);
          
          const credentials = testData.getValidCredentials();
          await userAuthHelper.login(credentials.username, credentials.password);
          
          // Verify successful login
          await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });
          
          successfulLogins++;
          userSessions.push({ page, context, userId: i + 1, success: true });
          
          if (i % 10 === 0) {
            console.log(`User ${i + 1}: Login successful`);
          }
          
        } catch (error) {
          failedLogins++;
          console.error(`User ${i + 1}: Login failed -`, error.message);
          userSessions.push({ userId: i + 1, success: false, error: error.message });
        }
      });
      
      await Promise.allSettled(loginPromises);
      
      console.log(`Concurrent User Analysis:`);
      console.log(`  Successful logins: ${successfulLogins}`);
      console.log(`  Failed logins: ${failedLogins}`);
      console.log(`  Success rate: ${(successfulLogins / maxUsers * 100).toFixed(2)}%`);
      
      // Test system stability with concurrent users
      const activeUsers = userSessions.filter(s => s.success && s.page);
      
      if (activeUsers.length > 0) {
        console.log(`Testing system stability with ${activeUsers.length} active users...`);
        
        // Perform concurrent operations
        const operationPromises = activeUsers.map(async (session, index) => {
          try {
            // Different operations for different users
            switch (index % 4) {
              case 0:
                await session.page.goto('/memory');
                await session.page.click('[data-testid="search-tab"]');
                break;
              case 1:
                await session.page.goto('/plugins');
                await session.page.selectOption('[data-testid="plugin-filter-dropdown"]', 'active');
                break;
              case 2:
                await session.page.goto('/models');
                await session.page.click('[data-testid="model-comparison-tab"]');
                break;
              case 3:
                await session.page.goto('/settings');
                break;
            }
            
            return { userId: session.userId, success: true };
          } catch (error) {
            return { userId: session.userId, success: false, error: error.message };
          }
        });
        
        const operationResults = await Promise.allSettled(operationPromises);
        const successfulOperations = operationResults.filter(r => 
          r.status === 'fulfilled' && r.value.success
        ).length;
        
        console.log(`Concurrent operations: ${successfulOperations}/${activeUsers.length} successful`);
        
        // Cleanup
        await Promise.all(activeUsers.map(session => session.context.close()));
      }
      
      // Assertions
      expect(successfulLogins).toBeGreaterThan(50); // At least 50% success rate
      expect(successfulLogins / maxUsers).toBeGreaterThan(0.7); // 70% success rate minimum
    });
  });

  test.describe('Recovery Testing', () => {
    test('should recover from temporary service outages', async ({ page }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      
      await page.goto('/dashboard');
      await expect(page.locator('[data-testid="dashboard-loaded"]')).toBeVisible();
      
      // Simulate temporary service outage
      let outageActive = true;
      
      await page.route('**/api/metrics/system', route => {
        if (outageActive) {
          route.fulfill({
            status: 503,
            json: { error: 'Service temporarily unavailable' }
          });
        } else {
          route.continue();
        }
      });
      
      // Trigger request during outage
      await page.click('[data-testid="refresh-metrics-button"]');
      await expect(page.locator('[data-testid="service-outage-error"]')).toBeVisible();
      
      // Simulate service recovery after 5 seconds
      setTimeout(() => {
        outageActive = false;
      }, 5000);
      
      // Test automatic retry mechanism
      await page.click('[data-testid="retry-button"]');
      
      // Verify recovery
      await expect(page.locator('[data-testid="dashboard-loaded"]')).toBeVisible();
      await expect(page.locator('[data-testid="cpu-usage-metric"]')).toBeVisible();
    });

    test('should handle graceful degradation', async ({ page }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      
      // Simulate partial service failure
      await page.route('**/api/memory/**', route => {
        route.fulfill({
          status: 503,
          json: { error: 'Memory service unavailable' }
        });
      });
      
      await page.goto('/memory');
      
      // Verify graceful degradation
      await expect(page.locator('[data-testid="degraded-mode-indicator"]')).toBeVisible();
      await expect(page.locator('[data-testid="limited-functionality-notice"]')).toBeVisible();
      
      // Verify core functionality still works
      await page.goto('/dashboard');
      await expect(page.locator('[data-testid="dashboard-loaded"]')).toBeVisible();
      
      // Test navigation still works
      await page.goto('/settings');
      await expect(page.locator('[data-testid="settings-page"]')).toBeVisible();
    });
  });
});