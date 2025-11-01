import { test, expect } from '@playwright/test';
import { AuthenticationHelper } from '../utils/authentication-helper';
import { MemoryHelper } from '../utils/memory-helper';
import { TestDataManager } from '../utils/test-data-manager';

test.describe('Memory Management Workflows', () => {
  let authHelper: AuthenticationHelper;
  let memoryHelper: MemoryHelper;
  let testData: TestDataManager;

  test.beforeEach(async ({ page }) => {
    authHelper = new AuthenticationHelper(page);
    memoryHelper = new MemoryHelper(page);
    testData = new TestDataManager();
    
    // Login and navigate to memory management
    const credentials = testData.getValidCredentials();
    await authHelper.login(credentials.username, credentials.password);
    await page.goto('/memory');
  });

  test.describe('Memory Analytics', () => {
    test('should display memory statistics', async ({ page }) => {
      // Verify memory analytics components
      await expect(page.locator('[data-testid="total-embeddings-count"]')).toBeVisible();
      await expect(page.locator('[data-testid="storage-size-metric"]')).toBeVisible();
      await expect(page.locator('[data-testid="average-latency-metric"]')).toBeVisible();
      await expect(page.locator('[data-testid="search-accuracy-metric"]')).toBeVisible();
      
      // Verify metrics have valid values
      const embeddingCount = await page.locator('[data-testid="total-embeddings-value"]').textContent();
      expect(embeddingCount).toMatch(/^\d+$/);
      
      const storageSize = await page.locator('[data-testid="storage-size-value"]').textContent();
      expect(storageSize).toMatch(/^\d+(\.\d+)?\s*(MB|GB|TB)$/);
    });

    test('should display memory decay patterns', async ({ page }) => {
      await page.click('[data-testid="decay-patterns-tab"]');
      
      // Verify decay visualization
      await expect(page.locator('[data-testid="decay-pattern-chart"]')).toBeVisible();
      await expect(page.locator('[data-testid="retention-curve"]')).toBeVisible();
      await expect(page.locator('[data-testid="forgetting-curve"]')).toBeVisible();
      
      // Verify decay metrics
      await expect(page.locator('[data-testid="retention-rate"]')).toBeVisible();
      await expect(page.locator('[data-testid="decay-rate"]')).toBeVisible();
    });

    test('should show memory usage breakdown by content type', async ({ page }) => {
      await page.click('[data-testid="usage-breakdown-tab"]');
      
      // Verify content type breakdown
      await expect(page.locator('[data-testid="conversation-memories"]')).toBeVisible();
      await expect(page.locator('[data-testid="document-memories"]')).toBeVisible();
      await expect(page.locator('[data-testid="code-memories"]')).toBeVisible();
      await expect(page.locator('[data-testid="image-memories"]')).toBeVisible();
      
      // Verify breakdown chart
      await expect(page.locator('[data-testid="memory-breakdown-chart"]')).toBeVisible();
    });
  });

  test.describe('Semantic Search', () => {
    test('should perform semantic search with results', async ({ page }) => {
      await page.click('[data-testid="search-tab"]');
      
      const searchQuery = 'machine learning algorithms';
      await page.fill('[data-testid="semantic-search-input"]', searchQuery);
      await page.click('[data-testid="search-button"]');
      
      // Verify search results
      await expect(page.locator('[data-testid="search-results"]')).toBeVisible();
      await expect(page.locator('[data-testid="search-result-item"]')).toHaveCount({ min: 1 });
      
      // Verify result components
      const firstResult = page.locator('[data-testid="search-result-item"]').first();
      await expect(firstResult.locator('[data-testid="similarity-score"]')).toBeVisible();
      await expect(firstResult.locator('[data-testid="content-snippet"]')).toBeVisible();
      await expect(firstResult.locator('[data-testid="result-timestamp"]')).toBeVisible();
    });

    test('should display similarity scores correctly', async ({ page }) => {
      await page.click('[data-testid="search-tab"]');
      await memoryHelper.performSearch('neural networks');
      
      // Verify similarity scores
      const similarityScores = await page.locator('[data-testid="similarity-score"]').all();
      
      for (const score of similarityScores) {
        const scoreText = await score.textContent();
        const scoreValue = parseFloat(scoreText?.replace('%', '') || '0');
        expect(scoreValue).toBeGreaterThanOrEqual(0);
        expect(scoreValue).toBeLessThanOrEqual(100);
      }
      
      // Verify results are sorted by similarity
      const scores = await Promise.all(
        similarityScores.map(async (score) => {
          const text = await score.textContent();
          return parseFloat(text?.replace('%', '') || '0');
        })
      );
      
      for (let i = 1; i < scores.length; i++) {
        expect(scores[i]).toBeLessThanOrEqual(scores[i - 1]);
      }
    });

    test('should support advanced search filters', async ({ page }) => {
      await page.click('[data-testid="search-tab"]');
      await page.click('[data-testid="advanced-filters-toggle"]');
      
      // Verify filter options
      await expect(page.locator('[data-testid="date-range-filter"]')).toBeVisible();
      await expect(page.locator('[data-testid="content-type-filter"]')).toBeVisible();
      await expect(page.locator('[data-testid="confidence-filter"]')).toBeVisible();
      await expect(page.locator('[data-testid="tag-filter"]')).toBeVisible();
      
      // Apply filters
      await page.selectOption('[data-testid="content-type-filter"]', 'conversation');
      await page.fill('[data-testid="confidence-min-filter"]', '0.8');
      await memoryHelper.performSearch('deep learning');
      
      // Verify filtered results
      const results = await page.locator('[data-testid="search-result-item"]').all();
      for (const result of results) {
        await expect(result.locator('[data-testid="content-type-conversation"]')).toBeVisible();
      }
    });

    test('should save and load search history', async ({ page }) => {
      await page.click('[data-testid="search-tab"]');
      
      // Perform multiple searches
      await memoryHelper.performSearch('artificial intelligence');
      await memoryHelper.performSearch('machine learning');
      await memoryHelper.performSearch('deep learning');
      
      // Check search history
      await page.click('[data-testid="search-history-button"]');
      await expect(page.locator('[data-testid="search-history-modal"]')).toBeVisible();
      
      const historyItems = await page.locator('[data-testid="search-history-item"]').all();
      expect(historyItems.length).toBe(3);
      
      // Verify history content
      await expect(page.locator('[data-testid="search-history-item"]').first()).toContainText('deep learning');
      await expect(page.locator('[data-testid="search-history-item"]').nth(1)).toContainText('machine learning');
      await expect(page.locator('[data-testid="search-history-item"]').nth(2)).toContainText('artificial intelligence');
    });
  });

  test.describe('Memory Network Visualization', () => {
    test('should display interactive memory network', async ({ page }) => {
      await page.click('[data-testid="network-tab"]');
      
      // Verify network visualization components
      await expect(page.locator('[data-testid="memory-network-graph"]')).toBeVisible();
      await expect(page.locator('[data-testid="network-controls"]')).toBeVisible();
      await expect(page.locator('[data-testid="cluster-legend"]')).toBeVisible();
      
      // Verify network nodes are rendered
      await expect(page.locator('[data-testid="memory-node"]')).toHaveCount({ min: 1 });
      await expect(page.locator('[data-testid="memory-edge"]')).toHaveCount({ min: 1 });
    });

    test('should support node interaction', async ({ page }) => {
      await page.click('[data-testid="network-tab"]');
      
      const firstNode = page.locator('[data-testid="memory-node"]').first();
      await firstNode.hover();
      
      // Verify hover details
      await expect(page.locator('[data-testid="node-tooltip"]')).toBeVisible();
      await expect(page.locator('[data-testid="node-content-preview"]')).toBeVisible();
      await expect(page.locator('[data-testid="node-connections-count"]')).toBeVisible();
      
      // Test node click
      await firstNode.click();
      await expect(page.locator('[data-testid="node-detail-panel"]')).toBeVisible();
      await expect(page.locator('[data-testid="node-full-content"]')).toBeVisible();
      await expect(page.locator('[data-testid="related-memories"]')).toBeVisible();
    });

    test('should support network filtering and search', async ({ page }) => {
      await page.click('[data-testid="network-tab"]');
      
      // Test cluster filtering
      await page.click('[data-testid="cluster-filter-button"]');
      await page.check('[data-testid="cluster-ai-concepts"]');
      await page.uncheck('[data-testid="cluster-general-knowledge"]');
      
      // Verify filtered network
      const visibleNodes = await page.locator('[data-testid="memory-node"]:visible').count();
      const totalNodes = await page.locator('[data-testid="memory-node"]').count();
      expect(visibleNodes).toBeLessThan(totalNodes);
      
      // Test network search
      await page.fill('[data-testid="network-search-input"]', 'neural');
      await page.click('[data-testid="network-search-button"]');
      
      // Verify search highlighting
      await expect(page.locator('[data-testid="highlighted-node"]')).toHaveCount({ min: 1 });
    });

    test('should support network layout algorithms', async ({ page }) => {
      await page.click('[data-testid="network-tab"]');
      
      // Test different layout algorithms
      await page.selectOption('[data-testid="layout-algorithm-selector"]', 'force-directed');
      await expect(page.locator('[data-testid="layout-applying"]')).toBeVisible();
      await expect(page.locator('[data-testid="layout-applying"]')).not.toBeVisible();
      
      await page.selectOption('[data-testid="layout-algorithm-selector"]', 'hierarchical');
      await expect(page.locator('[data-testid="layout-applying"]')).toBeVisible();
      await expect(page.locator('[data-testid="layout-applying"]')).not.toBeVisible();
      
      // Verify layout controls
      await expect(page.locator('[data-testid="zoom-in-button"]')).toBeVisible();
      await expect(page.locator('[data-testid="zoom-out-button"]')).toBeVisible();
      await expect(page.locator('[data-testid="reset-view-button"]')).toBeVisible();
    });
  });

  test.describe('Memory Management Operations', () => {
    test('should create new memory entries', async ({ page }) => {
      await page.click('[data-testid="management-tab"]');
      await page.click('[data-testid="add-memory-button"]');
      
      // Fill memory creation form
      await page.fill('[data-testid="memory-content-input"]', 'Test memory content about quantum computing');
      await page.selectOption('[data-testid="memory-type-select"]', 'knowledge');
      await page.fill('[data-testid="memory-tags-input"]', 'quantum, computing, physics');
      
      await page.click('[data-testid="save-memory-button"]');
      
      // Verify memory creation
      await expect(page.locator('[data-testid="memory-created-success"]')).toBeVisible();
      await expect(page.locator('[data-testid="memory-list"]')).toContainText('quantum computing');
    });

    test('should edit existing memory entries', async ({ page }) => {
      await page.click('[data-testid="management-tab"]');
      
      const firstMemory = page.locator('[data-testid="memory-item"]').first();
      await firstMemory.locator('[data-testid="edit-memory-button"]').click();
      
      // Edit memory content
      await page.fill('[data-testid="memory-content-input"]', 'Updated memory content');
      await page.click('[data-testid="save-memory-button"]');
      
      // Verify update
      await expect(page.locator('[data-testid="memory-updated-success"]')).toBeVisible();
      await expect(firstMemory).toContainText('Updated memory content');
    });

    test('should delete memory entries with confirmation', async ({ page }) => {
      await page.click('[data-testid="management-tab"]');
      
      const initialCount = await page.locator('[data-testid="memory-item"]').count();
      
      const firstMemory = page.locator('[data-testid="memory-item"]').first();
      await firstMemory.locator('[data-testid="delete-memory-button"]').click();
      
      // Verify confirmation dialog
      await expect(page.locator('[data-testid="delete-confirmation-modal"]')).toBeVisible();
      await page.click('[data-testid="confirm-delete-button"]');
      
      // Verify deletion
      await expect(page.locator('[data-testid="memory-deleted-success"]')).toBeVisible();
      const finalCount = await page.locator('[data-testid="memory-item"]').count();
      expect(finalCount).toBe(initialCount - 1);
    });

    test('should support batch operations', async ({ page }) => {
      await page.click('[data-testid="management-tab"]');
      
      // Select multiple memories
      await page.check('[data-testid="memory-checkbox-1"]');
      await page.check('[data-testid="memory-checkbox-2"]');
      await page.check('[data-testid="memory-checkbox-3"]');
      
      // Verify batch controls appear
      await expect(page.locator('[data-testid="batch-operations-bar"]')).toBeVisible();
      await expect(page.locator('[data-testid="batch-delete-button"]')).toBeVisible();
      await expect(page.locator('[data-testid="batch-tag-button"]')).toBeVisible();
      
      // Test batch tagging
      await page.click('[data-testid="batch-tag-button"]');
      await page.fill('[data-testid="batch-tag-input"]', 'batch-processed');
      await page.click('[data-testid="apply-batch-tags-button"]');
      
      // Verify batch operation success
      await expect(page.locator('[data-testid="batch-operation-success"]')).toBeVisible();
    });
  });
});