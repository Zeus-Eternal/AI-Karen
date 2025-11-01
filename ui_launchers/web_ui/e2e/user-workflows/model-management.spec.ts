import { test, expect } from '@playwright/test';
import { AuthenticationHelper } from '../utils/authentication-helper';
import { TestDataManager } from '../utils/test-data-manager';

test.describe('Model Management Workflows', () => {
  let authHelper: AuthenticationHelper;
  let testData: TestDataManager;

  test.beforeEach(async ({ page }) => {
    authHelper = new AuthenticationHelper(page);
    testData = new TestDataManager();
    
    const credentials = testData.getValidCredentials();
    await authHelper.login(credentials.username, credentials.password);
    await page.goto('/models');
  });

  test.describe('Model Selection and Recommendations', () => {
    test('should display intelligent model recommendations', async ({ page }) => {
      await page.click('[data-testid="model-selector-tab"]');
      
      // Verify recommendation components
      await expect(page.locator('[data-testid="recommended-models"]')).toBeVisible();
      await expect(page.locator('[data-testid="task-based-recommendations"]')).toBeVisible();
      
      // Select a task type
      await page.selectOption('[data-testid="task-type-selector"]', 'text-generation');
      
      // Verify recommendations update
      await expect(page.locator('[data-testid="recommendation-loading"]')).toBeVisible();
      await expect(page.locator('[data-testid="recommendation-loading"]')).not.toBeVisible();
      
      const recommendations = await page.locator('[data-testid="model-recommendation"]').all();
      expect(recommendations.length).toBeGreaterThan(0);
      
      // Verify recommendation details
      const firstRecommendation = recommendations[0];
      await expect(firstRecommendation.locator('[data-testid="model-name"]')).toBeVisible();
      await expect(firstRecommendation.locator('[data-testid="performance-score"]')).toBeVisible();
      await expect(firstRecommendation.locator('[data-testid="cost-estimate"]')).toBeVisible();
      await expect(firstRecommendation.locator('[data-testid="latency-estimate"]')).toBeVisible();
    });

    test('should support model comparison', async ({ page }) => {
      await page.click('[data-testid="model-comparison-tab"]');
      
      // Select models for comparison
      await page.check('[data-testid="compare-model-gpt-4"]');
      await page.check('[data-testid="compare-model-claude-3"]');
      await page.check('[data-testid="compare-model-llama-2"]');
      
      await page.click('[data-testid="start-comparison-button"]');
      
      // Verify comparison table
      await expect(page.locator('[data-testid="comparison-table"]')).toBeVisible();
      await expect(page.locator('[data-testid="comparison-metrics"]')).toBeVisible();
      
      // Verify comparison metrics
      await expect(page.locator('[data-testid="latency-comparison"]')).toBeVisible();
      await expect(page.locator('[data-testid="accuracy-comparison"]')).toBeVisible();
      await expect(page.locator('[data-testid="cost-comparison"]')).toBeVisible();
      await expect(page.locator('[data-testid="capability-comparison"]')).toBeVisible();
    });

    test('should display model performance metrics', async ({ page }) => {
      await page.click('[data-testid="performance-metrics-tab"]');
      
      // Verify metrics dashboard
      await expect(page.locator('[data-testid="model-metrics-dashboard"]')).toBeVisible();
      await expect(page.locator('[data-testid="usage-statistics"]')).toBeVisible();
      await expect(page.locator('[data-testid="performance-trends"]')).toBeVisible();
      
      // Verify individual model metrics
      const modelCards = await page.locator('[data-testid="model-metric-card"]').all();
      
      for (const card of modelCards) {
        await expect(card.locator('[data-testid="model-name"]')).toBeVisible();
        await expect(card.locator('[data-testid="request-count"]')).toBeVisible();
        await expect(card.locator('[data-testid="average-latency"]')).toBeVisible();
        await expect(card.locator('[data-testid="success-rate"]')).toBeVisible();
        await expect(card.locator('[data-testid="cost-per-request"]')).toBeVisible();
      }
    });
  });

  test.describe('Provider Configuration', () => {
    test('should configure local providers', async ({ page }) => {
      await page.click('[data-testid="provider-config-tab"]');
      await page.click('[data-testid="add-provider-button"]');
      
      // Select local provider type
      await page.selectOption('[data-testid="provider-type-selector"]', 'local');
      await page.selectOption('[data-testid="local-provider-selector"]', 'ollama');
      
      // Configure Ollama settings
      await page.fill('[data-testid="ollama-host-input"]', 'localhost');
      await page.fill('[data-testid="ollama-port-input"]', '11434');
      
      await page.click('[data-testid="test-connection-button"]');
      await expect(page.locator('[data-testid="connection-test-success"]')).toBeVisible();
      
      await page.click('[data-testid="save-provider-button"]');
      await expect(page.locator('[data-testid="provider-saved-success"]')).toBeVisible();
    });

    test('should configure cloud providers', async ({ page }) => {
      await page.click('[data-testid="provider-config-tab"]');
      await page.click('[data-testid="add-provider-button"]');
      
      // Select cloud provider type
      await page.selectOption('[data-testid="provider-type-selector"]', 'cloud');
      await page.selectOption('[data-testid="cloud-provider-selector"]', 'openai');
      
      // Configure OpenAI settings
      await page.fill('[data-testid="openai-api-key-input"]', 'test-api-key');
      await page.selectOption('[data-testid="openai-model-selector"]', 'gpt-4');
      
      await page.click('[data-testid="test-connection-button"]');
      await expect(page.locator('[data-testid="connection-test-progress"]')).toBeVisible();
      
      // Mock successful connection
      await expect(page.locator('[data-testid="connection-test-success"]')).toBeVisible({ timeout: 10000 });
      
      await page.click('[data-testid="save-provider-button"]');
      await expect(page.locator('[data-testid="provider-saved-success"]')).toBeVisible();
    });

    test('should handle provider authentication errors', async ({ page }) => {
      await page.click('[data-testid="provider-config-tab"]');
      await page.click('[data-testid="add-provider-button"]');
      
      await page.selectOption('[data-testid="provider-type-selector"]', 'cloud');
      await page.selectOption('[data-testid="cloud-provider-selector"]', 'openai');
      
      // Use invalid API key
      await page.fill('[data-testid="openai-api-key-input"]', 'invalid-key');
      
      await page.click('[data-testid="test-connection-button"]');
      
      // Verify error handling
      await expect(page.locator('[data-testid="connection-test-error"]')).toBeVisible();
      await expect(page.locator('[data-testid="auth-error-message"]')).toContainText('Invalid API key');
    });

    test('should monitor provider health', async ({ page }) => {
      await page.click('[data-testid="provider-health-tab"]');
      
      // Verify health monitoring dashboard
      await expect(page.locator('[data-testid="provider-health-dashboard"]')).toBeVisible();
      
      const providerHealthItems = await page.locator('[data-testid="provider-health-item"]').all();
      
      for (const item of providerHealthItems) {
        await expect(item.locator('[data-testid="provider-name"]')).toBeVisible();
        await expect(item.locator('[data-testid="connection-status"]')).toBeVisible();
        await expect(item.locator('[data-testid="response-time"]')).toBeVisible();
        await expect(item.locator('[data-testid="last-check-time"]')).toBeVisible();
        
        const status = await item.locator('[data-testid="connection-status"]').textContent();
        expect(['connected', 'disconnected', 'error']).toContain(status?.toLowerCase());
      }
    });
  });

  test.describe('Cost Tracking and Optimization', () => {
    test('should display cost analytics', async ({ page }) => {
      await page.click('[data-testid="cost-tracking-tab"]');
      
      // Verify cost dashboard
      await expect(page.locator('[data-testid="cost-analytics-dashboard"]')).toBeVisible();
      await expect(page.locator('[data-testid="total-cost-metric"]')).toBeVisible();
      await expect(page.locator('[data-testid="cost-by-provider-chart"]')).toBeVisible();
      await expect(page.locator('[data-testid="cost-by-model-chart"]')).toBeVisible();
      await expect(page.locator('[data-testid="cost-trends-chart"]')).toBeVisible();
      
      // Verify cost breakdown
      const costBreakdown = await page.locator('[data-testid="cost-breakdown-item"]').all();
      
      for (const item of costBreakdown) {
        await expect(item.locator('[data-testid="provider-name"]')).toBeVisible();
        await expect(item.locator('[data-testid="request-count"]')).toBeVisible();
        await expect(item.locator('[data-testid="total-cost"]')).toBeVisible();
        await expect(item.locator('[data-testid="average-cost"]')).toBeVisible();
      }
    });

    test('should set budget alerts', async ({ page }) => {
      await page.click('[data-testid="cost-tracking-tab"]');
      await page.click('[data-testid="budget-alerts-button"]');
      
      // Configure budget alert
      await page.fill('[data-testid="monthly-budget-input"]', '1000');
      await page.fill('[data-testid="alert-threshold-input"]', '80');
      await page.check('[data-testid="email-notifications-checkbox"]');
      
      await page.click('[data-testid="save-budget-alert-button"]');
      await expect(page.locator('[data-testid="budget-alert-saved"]')).toBeVisible();
      
      // Verify alert configuration
      await expect(page.locator('[data-testid="budget-alert-active"]')).toBeVisible();
      await expect(page.locator('[data-testid="budget-threshold-display"]')).toContainText('80%');
    });

    test('should provide optimization recommendations', async ({ page }) => {
      await page.click('[data-testid="optimization-tab"]');
      
      // Verify optimization dashboard
      await expect(page.locator('[data-testid="optimization-recommendations"]')).toBeVisible();
      
      const recommendations = await page.locator('[data-testid="optimization-recommendation"]').all();
      expect(recommendations.length).toBeGreaterThan(0);
      
      // Verify recommendation details
      const firstRecommendation = recommendations[0];
      await expect(firstRecommendation.locator('[data-testid="recommendation-title"]')).toBeVisible();
      await expect(firstRecommendation.locator('[data-testid="potential-savings"]')).toBeVisible();
      await expect(firstRecommendation.locator('[data-testid="recommendation-description"]')).toBeVisible();
      await expect(firstRecommendation.locator('[data-testid="apply-recommendation-button"]')).toBeVisible();
    });
  });

  test.describe('Fallback Configuration', () => {
    test('should configure fallback chains', async ({ page }) => {
      await page.click('[data-testid="fallback-config-tab"]');
      
      // Create new fallback chain
      await page.click('[data-testid="create-fallback-chain-button"]');
      await page.fill('[data-testid="chain-name-input"]', 'Text Generation Fallback');
      
      // Configure primary provider
      await page.selectOption('[data-testid="primary-provider-selector"]', 'openai');
      await page.selectOption('[data-testid="primary-model-selector"]', 'gpt-4');
      
      // Add fallback providers
      await page.click('[data-testid="add-fallback-button"]');
      await page.selectOption('[data-testid="fallback-1-provider-selector"]', 'anthropic');
      await page.selectOption('[data-testid="fallback-1-model-selector"]', 'claude-3');
      
      await page.click('[data-testid="add-fallback-button"]');
      await page.selectOption('[data-testid="fallback-2-provider-selector"]', 'local');
      await page.selectOption('[data-testid="fallback-2-model-selector"]', 'llama-2');
      
      await page.click('[data-testid="save-fallback-chain-button"]');
      await expect(page.locator('[data-testid="fallback-chain-saved"]')).toBeVisible();
    });

    test('should test fallback scenarios', async ({ page }) => {
      await page.click('[data-testid="fallback-config-tab"]');
      
      // Select existing fallback chain
      await page.click('[data-testid="fallback-chain-text-generation"]');
      await page.click('[data-testid="test-fallback-button"]');
      
      // Verify fallback testing
      await expect(page.locator('[data-testid="fallback-test-progress"]')).toBeVisible();
      await expect(page.locator('[data-testid="fallback-test-results"]')).toBeVisible({ timeout: 30000 });
      
      // Verify test results
      await expect(page.locator('[data-testid="primary-provider-test"]')).toBeVisible();
      await expect(page.locator('[data-testid="fallback-provider-tests"]')).toBeVisible();
      
      const testResults = await page.locator('[data-testid="provider-test-result"]').all();
      for (const result of testResults) {
        const status = await result.locator('[data-testid="test-status"]').textContent();
        expect(['success', 'failure', 'timeout']).toContain(status?.toLowerCase());
      }
    });

    test('should monitor fallback usage', async ({ page }) => {
      await page.click('[data-testid="fallback-analytics-tab"]');
      
      // Verify fallback analytics
      await expect(page.locator('[data-testid="fallback-usage-chart"]')).toBeVisible();
      await expect(page.locator('[data-testid="fallback-frequency-metric"]')).toBeVisible();
      await expect(page.locator('[data-testid="fallback-success-rate"]')).toBeVisible();
      
      // Verify fallback events log
      await expect(page.locator('[data-testid="fallback-events-log"]')).toBeVisible();
      
      const fallbackEvents = await page.locator('[data-testid="fallback-event"]').all();
      
      for (const event of fallbackEvents) {
        await expect(event.locator('[data-testid="event-timestamp"]')).toBeVisible();
        await expect(event.locator('[data-testid="primary-provider"]')).toBeVisible();
        await expect(event.locator('[data-testid="fallback-provider"]')).toBeVisible();
        await expect(event.locator('[data-testid="fallback-reason"]')).toBeVisible();
      }
    });
  });

  test.describe('Model Warm-up Management', () => {
    test('should manage model preloading', async ({ page }) => {
      await page.click('[data-testid="warmup-management-tab"]');
      
      // Verify warm-up dashboard
      await expect(page.locator('[data-testid="warmup-dashboard"]')).toBeVisible();
      
      const modelWarmupItems = await page.locator('[data-testid="model-warmup-item"]').all();
      
      for (const item of modelWarmupItems) {
        await expect(item.locator('[data-testid="model-name"]')).toBeVisible();
        await expect(item.locator('[data-testid="warmup-status"]')).toBeVisible();
        await expect(item.locator('[data-testid="warmup-progress"]')).toBeVisible();
        await expect(item.locator('[data-testid="warmup-controls"]')).toBeVisible();
      }
    });

    test('should start model warm-up', async ({ page }) => {
      await page.click('[data-testid="warmup-management-tab"]');
      
      // Start warm-up for a cold model
      const coldModel = page.locator('[data-testid="model-warmup-item"]').filter({
        has: page.locator('[data-testid="warmup-status-cold"]')
      }).first();
      
      await coldModel.locator('[data-testid="start-warmup-button"]').click();
      
      // Verify warm-up progress
      await expect(coldModel.locator('[data-testid="warmup-status-warming"]')).toBeVisible();
      await expect(coldModel.locator('[data-testid="warmup-progress-bar"]')).toBeVisible();
      
      // Wait for warm-up completion
      await expect(coldModel.locator('[data-testid="warmup-status-ready"]')).toBeVisible({ timeout: 60000 });
    });

    test('should configure automatic warm-up', async ({ page }) => {
      await page.click('[data-testid="warmup-management-tab"]');
      await page.click('[data-testid="auto-warmup-settings-button"]');
      
      // Configure auto warm-up
      await page.check('[data-testid="enable-auto-warmup-checkbox"]');
      await page.fill('[data-testid="warmup-schedule-input"]', '0 8 * * *'); // Daily at 8 AM
      await page.selectOption('[data-testid="warmup-priority-selector"]', 'high-usage');
      
      await page.click('[data-testid="save-auto-warmup-button"]');
      await expect(page.locator('[data-testid="auto-warmup-saved"]')).toBeVisible();
      
      // Verify auto warm-up is enabled
      await expect(page.locator('[data-testid="auto-warmup-enabled"]')).toBeVisible();
    });
  });
});