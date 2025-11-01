import { Page, expect } from '@playwright/test';

export class MemoryHelper {
  constructor(private page: Page) {}

  async performSearch(query: string): Promise<void> {
    await this.page.fill('[data-testid="semantic-search-input"]', query);
    await this.page.click('[data-testid="search-button"]');
    await expect(this.page.locator('[data-testid="search-results"]')).toBeVisible();
  }

  async performAdvancedSearch(query: string, filters: {
    contentType?: string;
    dateRange?: { start: string; end: string };
    confidenceMin?: number;
    tags?: string[];
  }): Promise<void> {
    await this.page.click('[data-testid="advanced-filters-toggle"]');
    
    if (filters.contentType) {
      await this.page.selectOption('[data-testid="content-type-filter"]', filters.contentType);
    }
    
    if (filters.dateRange) {
      await this.page.fill('[data-testid="date-start-filter"]', filters.dateRange.start);
      await this.page.fill('[data-testid="date-end-filter"]', filters.dateRange.end);
    }
    
    if (filters.confidenceMin) {
      await this.page.fill('[data-testid="confidence-min-filter"]', filters.confidenceMin.toString());
    }
    
    if (filters.tags) {
      await this.page.fill('[data-testid="tag-filter"]', filters.tags.join(', '));
    }
    
    await this.performSearch(query);
  }

  async getSearchResults(): Promise<Array<{
    content: string;
    similarity: number;
    timestamp: string;
    type: string;
  }>> {
    const results = await this.page.locator('[data-testid="search-result-item"]').all();
    const searchResults = [];
    
    for (const result of results) {
      const content = await result.locator('[data-testid="content-snippet"]').textContent() || '';
      const similarityText = await result.locator('[data-testid="similarity-score"]').textContent() || '0%';
      const similarity = parseFloat(similarityText.replace('%', ''));
      const timestamp = await result.locator('[data-testid="result-timestamp"]').textContent() || '';
      const type = await result.locator('[data-testid="content-type"]').textContent() || '';
      
      searchResults.push({ content, similarity, timestamp, type });
    }
    
    return searchResults;
  }

  async saveSearch(name: string): Promise<void> {
    await this.page.click('[data-testid="save-search-button"]');
    await this.page.fill('[data-testid="saved-search-name"]', name);
    await this.page.click('[data-testid="confirm-save-search"]');
    await expect(this.page.locator('[data-testid="search-saved-success"]')).toBeVisible();
  }

  async loadSavedSearch(name: string): Promise<void> {
    await this.page.click('[data-testid="saved-searches-button"]');
    await this.page.click(`[data-testid="saved-search-${name}"]`);
    await expect(this.page.locator('[data-testid="search-results"]')).toBeVisible();
  }

  async createMemory(content: string, type: string, tags: string[] = []): Promise<void> {
    await this.page.click('[data-testid="add-memory-button"]');
    await expect(this.page.locator('[data-testid="memory-creation-modal"]')).toBeVisible();
    
    await this.page.fill('[data-testid="memory-content-input"]', content);
    await this.page.selectOption('[data-testid="memory-type-select"]', type);
    
    if (tags.length > 0) {
      await this.page.fill('[data-testid="memory-tags-input"]', tags.join(', '));
    }
    
    await this.page.click('[data-testid="save-memory-button"]');
    await expect(this.page.locator('[data-testid="memory-created-success"]')).toBeVisible();
  }

  async editMemory(memoryId: string, newContent: string): Promise<void> {
    await this.page.click(`[data-testid="edit-memory-${memoryId}"]`);
    await expect(this.page.locator('[data-testid="memory-edit-modal"]')).toBeVisible();
    
    await this.page.fill('[data-testid="memory-content-input"]', newContent);
    await this.page.click('[data-testid="save-memory-button"]');
    await expect(this.page.locator('[data-testid="memory-updated-success"]')).toBeVisible();
  }

  async deleteMemory(memoryId: string): Promise<void> {
    await this.page.click(`[data-testid="delete-memory-${memoryId}"]`);
    await expect(this.page.locator('[data-testid="delete-confirmation-modal"]')).toBeVisible();
    
    await this.page.click('[data-testid="confirm-delete-button"]');
    await expect(this.page.locator('[data-testid="memory-deleted-success"]')).toBeVisible();
  }

  async selectMultipleMemories(memoryIds: string[]): Promise<void> {
    for (const id of memoryIds) {
      await this.page.check(`[data-testid="memory-checkbox-${id}"]`);
    }
    await expect(this.page.locator('[data-testid="batch-operations-bar"]')).toBeVisible();
  }

  async batchDeleteMemories(memoryIds: string[]): Promise<void> {
    await this.selectMultipleMemories(memoryIds);
    await this.page.click('[data-testid="batch-delete-button"]');
    await this.page.click('[data-testid="confirm-batch-delete"]');
    await expect(this.page.locator('[data-testid="batch-delete-success"]')).toBeVisible();
  }

  async batchTagMemories(memoryIds: string[], tags: string[]): Promise<void> {
    await this.selectMultipleMemories(memoryIds);
    await this.page.click('[data-testid="batch-tag-button"]');
    await this.page.fill('[data-testid="batch-tag-input"]', tags.join(', '));
    await this.page.click('[data-testid="apply-batch-tags-button"]');
    await expect(this.page.locator('[data-testid="batch-tag-success"]')).toBeVisible();
  }

  async navigateNetworkGraph(): Promise<void> {
    await this.page.click('[data-testid="network-tab"]');
    await expect(this.page.locator('[data-testid="memory-network-graph"]')).toBeVisible();
  }

  async interactWithNetworkNode(nodeId: string): Promise<void> {
    const node = this.page.locator(`[data-testid="memory-node-${nodeId}"]`);
    await node.hover();
    await expect(this.page.locator('[data-testid="node-tooltip"]')).toBeVisible();
    
    await node.click();
    await expect(this.page.locator('[data-testid="node-detail-panel"]')).toBeVisible();
  }

  async filterNetworkByCluster(clusterName: string): Promise<void> {
    await this.page.click('[data-testid="cluster-filter-button"]');
    await this.page.check(`[data-testid="cluster-${clusterName}"]`);
    await this.page.click('[data-testid="apply-cluster-filter"]');
  }

  async searchInNetwork(query: string): Promise<void> {
    await this.page.fill('[data-testid="network-search-input"]', query);
    await this.page.click('[data-testid="network-search-button"]');
    await expect(this.page.locator('[data-testid="highlighted-node"]')).toBeVisible();
  }

  async changeNetworkLayout(layout: string): Promise<void> {
    await this.page.selectOption('[data-testid="layout-algorithm-selector"]', layout);
    await expect(this.page.locator('[data-testid="layout-applying"]')).toBeVisible();
    await expect(this.page.locator('[data-testid="layout-applying"]')).not.toBeVisible();
  }

  async zoomNetwork(direction: 'in' | 'out' | 'reset'): Promise<void> {
    const buttonId = direction === 'reset' ? 'reset-view-button' : `zoom-${direction}-button`;
    await this.page.click(`[data-testid="${buttonId}"]`);
  }

  async exportMemoryData(format: 'json' | 'csv'): Promise<void> {
    await this.page.click('[data-testid="export-memory-button"]');
    await this.page.selectOption('[data-testid="export-format-selector"]', format);
    await this.page.click('[data-testid="download-export-button"]');
    
    const downloadPromise = this.page.waitForEvent('download');
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toContain(`memory.${format}`);
  }

  async importMemoryData(filePath: string): Promise<void> {
    await this.page.click('[data-testid="import-memory-button"]');
    await this.page.setInputFiles('[data-testid="import-file-input"]', filePath);
    await this.page.click('[data-testid="upload-import-button"]');
    await expect(this.page.locator('[data-testid="import-success"]')).toBeVisible();
  }

  async getMemoryStatistics(): Promise<{
    totalEmbeddings: number;
    storageSize: string;
    averageLatency: string;
    searchAccuracy: string;
  }> {
    const totalEmbeddings = parseInt(
      await this.page.locator('[data-testid="total-embeddings-value"]').textContent() || '0'
    );
    const storageSize = await this.page.locator('[data-testid="storage-size-value"]').textContent() || '';
    const averageLatency = await this.page.locator('[data-testid="average-latency-value"]').textContent() || '';
    const searchAccuracy = await this.page.locator('[data-testid="search-accuracy-value"]').textContent() || '';
    
    return { totalEmbeddings, storageSize, averageLatency, searchAccuracy };
  }

  async validateMemoryIntegrity(): Promise<void> {
    await this.page.click('[data-testid="validate-memory-button"]');
    await expect(this.page.locator('[data-testid="validation-progress"]')).toBeVisible();
    await expect(this.page.locator('[data-testid="validation-complete"]')).toBeVisible({ timeout: 30000 });
  }

  async cleanupDuplicateMemories(): Promise<void> {
    await this.page.click('[data-testid="cleanup-duplicates-button"]');
    await this.page.click('[data-testid="confirm-cleanup"]');
    await expect(this.page.locator('[data-testid="cleanup-progress"]')).toBeVisible();
    await expect(this.page.locator('[data-testid="cleanup-complete"]')).toBeVisible({ timeout: 30000 });
  }
}