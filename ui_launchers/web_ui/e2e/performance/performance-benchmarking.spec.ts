import { test, expect } from '@playwright/test';
import { AuthenticationHelper } from '../utils/authentication-helper';
import { TestDataManager } from '../utils/test-data-manager';

test.describe('Performance Benchmarking', () => {
  let authHelper: AuthenticationHelper;
  let testData: TestDataManager;

  test.beforeEach(async ({ page }) => {
    authHelper = new AuthenticationHelper(page);
    testData = new TestDataManager();
  });

  test.describe('Baseline Performance Establishment', () => {
    test('should establish page load time baselines', async ({ page }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      
      const pages = [
        { path: '/dashboard', name: 'Dashboard' },
        { path: '/memory', name: 'Memory' },
        { path: '/plugins', name: 'Plugins' },
        { path: '/models', name: 'Models' },
        { path: '/settings', name: 'Settings' }
      ];
      
      const performanceBaselines = {};
      
      for (const pageInfo of pages) {
        const measurements = [];
        const iterations = 5;
        
        for (let i = 0; i < iterations; i++) {
          const startTime = Date.now();
          
          await page.goto(pageInfo.path);
          await page.waitForLoadState('networkidle');
          
          // Wait for page-specific indicators
          switch (pageInfo.path) {
            case '/dashboard':
              await expect(page.locator('[data-testid="dashboard-loaded"]')).toBeVisible();
              break;
            case '/memory':
              await expect(page.locator('[data-testid="memory-analytics"]')).toBeVisible();
              break;
            case '/plugins':
              await expect(page.locator('[data-testid="plugin-list"]')).toBeVisible();
              break;
            case '/models':
              await expect(page.locator('[data-testid="model-selector"]')).toBeVisible();
              break;
            case '/settings':
              await expect(page.locator('[data-testid="settings-page"]')).toBeVisible();
              break;
          }
          
          const loadTime = Date.now() - startTime;
          measurements.push(loadTime);
          
          console.log(`${pageInfo.name} load ${i + 1}: ${loadTime}ms`);
        }
        
        const average = measurements.reduce((a, b) => a + b, 0) / measurements.length;
        const min = Math.min(...measurements);
        const max = Math.max(...measurements);
        const median = measurements.sort((a, b) => a - b)[Math.floor(measurements.length / 2)];
        
        performanceBaselines[pageInfo.name] = {
          average,
          min,
          max,
          median,
          measurements
        };
        
        console.log(`${pageInfo.name} Performance Baseline:`);
        console.log(`  Average: ${average.toFixed(2)}ms`);
        console.log(`  Min: ${min}ms`);
        console.log(`  Max: ${max}ms`);
        console.log(`  Median: ${median}ms`);
        
        // Performance assertions
        expect(average).toBeLessThan(3000); // 3 second average
        expect(max).toBeLessThan(5000); // 5 second maximum
      }
      
      // Store baselines for regression testing
      console.log('\nPerformance Baselines Summary:');
      console.log(JSON.stringify(performanceBaselines, null, 2));
    });

    test('should establish interaction response time baselines', async ({ page }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      
      const interactions = [
        {
          name: 'Navigation Click',
          setup: () => page.goto('/dashboard'),
          action: () => page.click('[data-testid="memory-nav-link"]'),
          verify: () => expect(page).toHaveURL(/\/memory/)
        },
        {
          name: 'Button Click',
          setup: () => page.goto('/dashboard'),
          action: () => page.click('[data-testid="refresh-metrics-button"]'),
          verify: () => expect(page.locator('[data-testid="metrics-refreshed"]')).toBeVisible()
        },
        {
          name: 'Form Input',
          setup: () => page.goto('/memory'),
          action: () => {
            page.click('[data-testid="search-tab"]');
            return page.fill('[data-testid="semantic-search-input"]', 'test query');
          },
          verify: () => expect(page.locator('[data-testid="semantic-search-input"]')).toHaveValue('test query')
        },
        {
          name: 'Dropdown Selection',
          setup: () => page.goto('/plugins'),
          action: () => page.selectOption('[data-testid="plugin-filter-dropdown"]', 'active'),
          verify: () => expect(page.locator('[data-testid="plugin-status-active"]').first()).toBeVisible()
        },
        {
          name: 'Modal Open',
          setup: () => page.goto('/memory'),
          action: () => {
            page.click('[data-testid="management-tab"]');
            return page.click('[data-testid="add-memory-button"]');
          },
          verify: () => expect(page.locator('[data-testid="memory-creation-modal"]')).toBeVisible()
        }
      ];
      
      const interactionBaselines = {};
      
      for (const interaction of interactions) {
        const measurements = [];
        const iterations = 10;
        
        for (let i = 0; i < iterations; i++) {
          await interaction.setup();
          await page.waitForLoadState('networkidle');
          
          const startTime = Date.now();
          await interaction.action();
          await interaction.verify();
          const responseTime = Date.now() - startTime;
          
          measurements.push(responseTime);
          
          if (i % 3 === 0) {
            console.log(`${interaction.name} response ${i + 1}: ${responseTime}ms`);
          }
        }
        
        const average = measurements.reduce((a, b) => a + b, 0) / measurements.length;
        const min = Math.min(...measurements);
        const max = Math.max(...measurements);
        const p95 = measurements.sort((a, b) => a - b)[Math.floor(measurements.length * 0.95)];
        
        interactionBaselines[interaction.name] = {
          average,
          min,
          max,
          p95,
          measurements
        };
        
        console.log(`${interaction.name} Response Time Baseline:`);
        console.log(`  Average: ${average.toFixed(2)}ms`);
        console.log(`  Min: ${min}ms`);
        console.log(`  Max: ${max}ms`);
        console.log(`  95th percentile: ${p95}ms`);
        
        // Performance assertions
        expect(average).toBeLessThan(500); // 500ms average response
        expect(p95).toBeLessThan(1000); // 1 second 95th percentile
      }
      
      console.log('\nInteraction Response Time Baselines Summary:');
      console.log(JSON.stringify(interactionBaselines, null, 2));
    });

    test('should establish memory usage baselines', async ({ page }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      
      const scenarios = [
        {
          name: 'Dashboard Idle',
          action: async () => {
            await page.goto('/dashboard');
            await page.waitForLoadState('networkidle');
            await page.waitForTimeout(5000); // Idle for 5 seconds
          }
        },
        {
          name: 'Memory Network Visualization',
          action: async () => {
            await page.goto('/memory');
            await page.click('[data-testid="network-tab"]');
            await expect(page.locator('[data-testid="memory-network-graph"]')).toBeVisible();
            await page.waitForTimeout(3000);
          }
        },
        {
          name: 'Plugin List with Filtering',
          action: async () => {
            await page.goto('/plugins');
            await page.selectOption('[data-testid="plugin-filter-dropdown"]', 'active');
            await page.fill('[data-testid="plugin-search-input"]', 'test');
            await page.waitForTimeout(2000);
          }
        },
        {
          name: 'Model Comparison',
          action: async () => {
            await page.goto('/models');
            await page.click('[data-testid="model-comparison-tab"]');
            await page.check('[data-testid="compare-model-gpt-4"]');
            await page.check('[data-testid="compare-model-claude-3"]');
            await page.waitForTimeout(2000);
          }
        }
      ];
      
      const memoryBaselines = {};
      
      for (const scenario of scenarios) {
        const memorySnapshots = [];
        
        // Take initial memory snapshot
        let initialMemory = await page.evaluate(() => {
          if ('memory' in performance) {
            return (performance as any).memory.usedJSHeapSize;
          }
          return null;
        });
        
        if (!initialMemory) {
          console.log(`Memory API not available for ${scenario.name}`);
          continue;
        }
        
        memorySnapshots.push({ phase: 'initial', memory: initialMemory });
        
        // Execute scenario
        await scenario.action();
        
        // Take post-action memory snapshot
        const postActionMemory = await page.evaluate(() => {
          return (performance as any).memory.usedJSHeapSize;
        });
        
        memorySnapshots.push({ phase: 'post-action', memory: postActionMemory });
        
        // Force garbage collection if available
        await page.evaluate(() => {
          if (window.gc) {
            window.gc();
          }
        });
        
        await page.waitForTimeout(1000);
        
        // Take post-GC memory snapshot
        const postGCMemory = await page.evaluate(() => {
          return (performance as any).memory.usedJSHeapSize;
        });
        
        memorySnapshots.push({ phase: 'post-gc', memory: postGCMemory });
        
        const memoryIncrease = postActionMemory - initialMemory;
        const memoryRetained = postGCMemory - initialMemory;
        
        memoryBaselines[scenario.name] = {
          initial: initialMemory,
          postAction: postActionMemory,
          postGC: postGCMemory,
          increase: memoryIncrease,
          retained: memoryRetained,
          snapshots: memorySnapshots
        };
        
        console.log(`${scenario.name} Memory Baseline:`);
        console.log(`  Initial: ${(initialMemory / 1024 / 1024).toFixed(2)}MB`);
        console.log(`  Post-action: ${(postActionMemory / 1024 / 1024).toFixed(2)}MB`);
        console.log(`  Post-GC: ${(postGCMemory / 1024 / 1024).toFixed(2)}MB`);
        console.log(`  Memory increase: ${(memoryIncrease / 1024 / 1024).toFixed(2)}MB`);
        console.log(`  Memory retained: ${(memoryRetained / 1024 / 1024).toFixed(2)}MB`);
        
        // Memory usage assertions
        expect(postActionMemory).toBeLessThan(200 * 1024 * 1024); // 200MB limit
        expect(memoryRetained).toBeLessThan(50 * 1024 * 1024); // 50MB retained limit
      }
      
      console.log('\nMemory Usage Baselines Summary:');
      console.log(JSON.stringify(memoryBaselines, null, 2));
    });
  });

  test.describe('Performance Regression Detection', () => {
    test('should detect page load time regressions', async ({ page }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      
      // Baseline performance expectations (from previous runs)
      const expectedBaselines = {
        Dashboard: { average: 1500, max: 2500 },
        Memory: { average: 2000, max: 3000 },
        Plugins: { average: 1800, max: 2800 },
        Models: { average: 1600, max: 2600 },
        Settings: { average: 1200, max: 2000 }
      };
      
      const pages = [
        { path: '/dashboard', name: 'Dashboard' },
        { path: '/memory', name: 'Memory' },
        { path: '/plugins', name: 'Plugins' },
        { path: '/models', name: 'Models' },
        { path: '/settings', name: 'Settings' }
      ];
      
      const regressionResults = {};
      
      for (const pageInfo of pages) {
        const measurements = [];
        const iterations = 3;
        
        for (let i = 0; i < iterations; i++) {
          const startTime = Date.now();
          
          await page.goto(pageInfo.path);
          await page.waitForLoadState('networkidle');
          
          // Wait for page-specific indicators
          switch (pageInfo.path) {
            case '/dashboard':
              await expect(page.locator('[data-testid="dashboard-loaded"]')).toBeVisible();
              break;
            case '/memory':
              await expect(page.locator('[data-testid="memory-analytics"]')).toBeVisible();
              break;
            case '/plugins':
              await expect(page.locator('[data-testid="plugin-list"]')).toBeVisible();
              break;
            case '/models':
              await expect(page.locator('[data-testid="model-selector"]')).toBeVisible();
              break;
            case '/settings':
              await expect(page.locator('[data-testid="settings-page"]')).toBeVisible();
              break;
          }
          
          const loadTime = Date.now() - startTime;
          measurements.push(loadTime);
        }
        
        const average = measurements.reduce((a, b) => a + b, 0) / measurements.length;
        const max = Math.max(...measurements);
        
        const baseline = expectedBaselines[pageInfo.name];
        const averageRegression = ((average - baseline.average) / baseline.average) * 100;
        const maxRegression = ((max - baseline.max) / baseline.max) * 100;
        
        regressionResults[pageInfo.name] = {
          current: { average, max },
          baseline: baseline,
          regression: { average: averageRegression, max: maxRegression },
          measurements
        };
        
        console.log(`${pageInfo.name} Regression Analysis:`);
        console.log(`  Current average: ${average.toFixed(2)}ms (${averageRegression.toFixed(2)}% change)`);
        console.log(`  Current max: ${max}ms (${maxRegression.toFixed(2)}% change)`);
        
        // Regression detection assertions
        expect(averageRegression).toBeLessThan(20); // No more than 20% regression in average
        expect(maxRegression).toBeLessThan(30); // No more than 30% regression in max
        
        // Absolute performance assertions
        expect(average).toBeLessThan(baseline.average * 1.5); // No more than 50% slower
        expect(max).toBeLessThan(baseline.max * 1.5);
      }
      
      console.log('\nRegression Detection Summary:');
      console.log(JSON.stringify(regressionResults, null, 2));
    });

    test('should detect interaction response time regressions', async ({ page }) => {
      const credentials = testData.getValidCredentials();
      await authHelper.login(credentials.username, credentials.password);
      
      // Baseline expectations
      const expectedBaselines = {
        'Navigation Click': { average: 200, p95: 400 },
        'Button Click': { average: 150, p95: 300 },
        'Form Input': { average: 100, p95: 200 },
        'Dropdown Selection': { average: 250, p95: 500 },
        'Modal Open': { average: 300, p95: 600 }
      };
      
      const interactions = [
        {
          name: 'Navigation Click',
          setup: () => page.goto('/dashboard'),
          action: () => page.click('[data-testid="memory-nav-link"]'),
          verify: () => expect(page).toHaveURL(/\/memory/)
        },
        {
          name: 'Button Click',
          setup: () => page.goto('/dashboard'),
          action: () => page.click('[data-testid="refresh-metrics-button"]'),
          verify: () => page.waitForTimeout(500) // Simplified verification
        },
        {
          name: 'Form Input',
          setup: () => {
            page.goto('/memory');
            return page.click('[data-testid="search-tab"]');
          },
          action: () => page.fill('[data-testid="semantic-search-input"]', 'test'),
          verify: () => expect(page.locator('[data-testid="semantic-search-input"]')).toHaveValue('test')
        }
      ];
      
      const regressionResults = {};
      
      for (const interaction of interactions) {
        const measurements = [];
        const iterations = 5;
        
        for (let i = 0; i < iterations; i++) {
          await interaction.setup();
          await page.waitForLoadState('networkidle');
          
          const startTime = Date.now();
          await interaction.action();
          await interaction.verify();
          const responseTime = Date.now() - startTime;
          
          measurements.push(responseTime);
        }
        
        const average = measurements.reduce((a, b) => a + b, 0) / measurements.length;
        const p95 = measurements.sort((a, b) => a - b)[Math.floor(measurements.length * 0.95)];
        
        const baseline = expectedBaselines[interaction.name];
        const averageRegression = ((average - baseline.average) / baseline.average) * 100;
        const p95Regression = ((p95 - baseline.p95) / baseline.p95) * 100;
        
        regressionResults[interaction.name] = {
          current: { average, p95 },
          baseline: baseline,
          regression: { average: averageRegression, p95: p95Regression },
          measurements
        };
        
        console.log(`${interaction.name} Response Time Regression:`);
        console.log(`  Current average: ${average.toFixed(2)}ms (${averageRegression.toFixed(2)}% change)`);
        console.log(`  Current p95: ${p95}ms (${p95Regression.toFixed(2)}% change)`);
        
        // Regression detection assertions
        expect(averageRegression).toBeLessThan(25); // No more than 25% regression
        expect(p95Regression).toBeLessThan(30); // No more than 30% regression in p95
      }
      
      console.log('\nInteraction Response Time Regression Summary:');
      console.log(JSON.stringify(regressionResults, null, 2));
    });
  });

  test.describe('Capacity Testing', () => {
    test('should validate system capacity under normal load', async ({ browser }) => {
      const normalLoad = {
        concurrentUsers: 20,
        operationsPerUser: 10,
        operationInterval: 2000 // 2 seconds between operations
      };
      
      console.log(`Testing normal load capacity: ${normalLoad.concurrentUsers} users`);
      
      const userSessions = [];
      const performanceMetrics = [];
      
      // Create concurrent user sessions
      for (let i = 0; i < normalLoad.concurrentUsers; i++) {
        const context = await browser.newContext();
        const page = await context.newPage();
        const userAuthHelper = new AuthenticationHelper(page);
        
        const credentials = testData.getValidCredentials();
        await userAuthHelper.login(credentials.username, credentials.password);
        
        userSessions.push({
          page,
          context,
          userId: i + 1,
          authHelper: userAuthHelper
        });
      }
      
      console.log(`Created ${userSessions.length} user sessions`);
      
      // Execute normal load operations
      const loadTestStartTime = Date.now();
      
      const userOperations = userSessions.map(async (session) => {
        const operations = [
          () => session.page.goto('/dashboard'),
          () => session.page.goto('/memory'),
          () => session.page.goto('/plugins'),
          () => session.page.goto('/models'),
          () => {
            session.page.goto('/memory');
            session.page.click('[data-testid="search-tab"]');
            return session.page.fill('[data-testid="semantic-search-input"]', 'test query');
          }
        ];
        
        const userMetrics = [];
        
        for (let i = 0; i < normalLoad.operationsPerUser; i++) {
          const operation = operations[i % operations.length];
          const operationStartTime = Date.now();
          
          try {
            await operation();
            await session.page.waitForLoadState('networkidle');
            
            const operationTime = Date.now() - operationStartTime;
            userMetrics.push({
              userId: session.userId,
              operation: i + 1,
              duration: operationTime,
              success: true
            });
            
            await session.page.waitForTimeout(normalLoad.operationInterval);
            
          } catch (error) {
            userMetrics.push({
              userId: session.userId,
              operation: i + 1,
              duration: -1,
              success: false,
              error: error.message
            });
          }
        }
        
        return userMetrics;
      });
      
      const allUserMetrics = await Promise.all(userOperations);
      const flatMetrics = allUserMetrics.flat();
      
      const loadTestDuration = Date.now() - loadTestStartTime;
      
      // Analyze capacity test results
      const successfulOperations = flatMetrics.filter(m => m.success);
      const failedOperations = flatMetrics.filter(m => !m.success);
      const averageOperationTime = successfulOperations.reduce((sum, m) => sum + m.duration, 0) / successfulOperations.length;
      const maxOperationTime = Math.max(...successfulOperations.map(m => m.duration));
      
      console.log(`Normal Load Capacity Test Results:`);
      console.log(`  Total duration: ${loadTestDuration}ms`);
      console.log(`  Total operations: ${flatMetrics.length}`);
      console.log(`  Successful operations: ${successfulOperations.length}`);
      console.log(`  Failed operations: ${failedOperations.length}`);
      console.log(`  Success rate: ${(successfulOperations.length / flatMetrics.length * 100).toFixed(2)}%`);
      console.log(`  Average operation time: ${averageOperationTime.toFixed(2)}ms`);
      console.log(`  Max operation time: ${maxOperationTime}ms`);
      
      // Cleanup
      await Promise.all(userSessions.map(session => session.context.close()));
      
      // Capacity assertions
      expect(successfulOperations.length / flatMetrics.length).toBeGreaterThan(0.95); // 95% success rate
      expect(averageOperationTime).toBeLessThan(3000); // 3 second average
      expect(maxOperationTime).toBeLessThan(10000); // 10 second maximum
    });

    test('should identify scaling requirements', async ({ browser }) => {
      const scalingTests = [
        { users: 10, name: 'Light Load' },
        { users: 25, name: 'Medium Load' },
        { users: 50, name: 'Heavy Load' }
      ];
      
      const scalingResults = {};
      
      for (const scalingTest of scalingTests) {
        console.log(`Testing ${scalingTest.name}: ${scalingTest.users} users`);
        
        const userSessions = [];
        
        // Create user sessions
        for (let i = 0; i < scalingTest.users; i++) {
          try {
            const context = await browser.newContext();
            const page = await context.newPage();
            const userAuthHelper = new AuthenticationHelper(page);
            
            const credentials = testData.getValidCredentials();
            await userAuthHelper.login(credentials.username, credentials.password);
            
            userSessions.push({ page, context, userId: i + 1 });
          } catch (error) {
            console.error(`Failed to create user session ${i + 1}:`, error.message);
          }
        }
        
        const actualUsers = userSessions.length;
        console.log(`Created ${actualUsers}/${scalingTest.users} user sessions`);
        
        // Perform concurrent operations
        const testStartTime = Date.now();
        
        const operationPromises = userSessions.map(async (session) => {
          const operationStartTime = Date.now();
          
          try {
            await session.page.goto('/dashboard');
            await session.page.waitForLoadState('networkidle');
            await expect(session.page.locator('[data-testid="dashboard-loaded"]')).toBeVisible();
            
            const operationTime = Date.now() - operationStartTime;
            return { userId: session.userId, duration: operationTime, success: true };
          } catch (error) {
            return { userId: session.userId, duration: -1, success: false, error: error.message };
          }
        });
        
        const operationResults = await Promise.all(operationPromises);
        const testDuration = Date.now() - testStartTime;
        
        const successfulOperations = operationResults.filter(r => r.success);
        const averageResponseTime = successfulOperations.reduce((sum, r) => sum + r.duration, 0) / successfulOperations.length;
        const maxResponseTime = Math.max(...successfulOperations.map(r => r.duration));
        
        scalingResults[scalingTest.name] = {
          targetUsers: scalingTest.users,
          actualUsers,
          successfulOperations: successfulOperations.length,
          successRate: successfulOperations.length / actualUsers,
          averageResponseTime,
          maxResponseTime,
          totalTestDuration: testDuration
        };
        
        console.log(`${scalingTest.name} Results:`);
        console.log(`  Success rate: ${(successfulOperations.length / actualUsers * 100).toFixed(2)}%`);
        console.log(`  Average response time: ${averageResponseTime.toFixed(2)}ms`);
        console.log(`  Max response time: ${maxResponseTime}ms`);
        console.log(`  Total test duration: ${testDuration}ms`);
        
        // Cleanup
        await Promise.all(userSessions.map(session => session.context.close()));
        
        // Brief pause between scaling tests
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
      
      console.log('\nScaling Analysis Summary:');
      console.log(JSON.stringify(scalingResults, null, 2));
      
      // Analyze scaling patterns
      const lightLoad = scalingResults['Light Load'];
      const heavyLoad = scalingResults['Heavy Load'];
      
      if (lightLoad && heavyLoad) {
        const responseTimeDegradation = (heavyLoad.averageResponseTime - lightLoad.averageResponseTime) / lightLoad.averageResponseTime;
        const successRateDegradation = lightLoad.successRate - heavyLoad.successRate;
        
        console.log(`Scaling Impact Analysis:`);
        console.log(`  Response time degradation: ${(responseTimeDegradation * 100).toFixed(2)}%`);
        console.log(`  Success rate degradation: ${(successRateDegradation * 100).toFixed(2)}%`);
        
        // Scaling assertions
        expect(responseTimeDegradation).toBeLessThan(2.0); // No more than 200% degradation
        expect(successRateDegradation).toBeLessThan(0.1); // No more than 10% success rate drop
      }
    });
  });
});