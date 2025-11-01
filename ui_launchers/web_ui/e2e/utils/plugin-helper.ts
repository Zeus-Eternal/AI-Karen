import { Page, expect } from '@playwright/test';

export class PluginHelper {
  constructor(private page: Page) {}

  async startInstallation(): Promise<void> {
    await this.page.click('[data-testid="install-plugin-button"]');
    await expect(this.page.locator('[data-testid="installation-wizard"]')).toBeVisible();
  }

  async selectPlugin(pluginId: string): Promise<void> {
    await this.page.click(`[data-testid="select-plugin-${pluginId}"]`);
    await expect(this.page.locator(`[data-testid="plugin-selected-${pluginId}"]`)).toBeVisible();
  }

  async proceedThroughSteps(): Promise<void> {
    // Step 1 to 2: Plugin Selection to Dependencies
    await this.page.click('[data-testid="next-step-button"]');
    await expect(this.page.locator('[data-testid="wizard-step-2"]')).toBeVisible();
    
    // Step 2 to 3: Dependencies to Permissions
    await this.page.click('[data-testid="next-step-button"]');
    await expect(this.page.locator('[data-testid="wizard-step-3"]')).toBeVisible();
    
    // Step 3 to 4: Permissions to Installation
    await this.page.click('[data-testid="next-step-button"]');
    await expect(this.page.locator('[data-testid="wizard-step-4"]')).toBeVisible();
    
    // Start installation
    await this.page.click('[data-testid="install-button"]');
  }

  async waitForInstallationComplete(): Promise<void> {
    await expect(this.page.locator('[data-testid="installation-progress"]')).toBeVisible();
    await expect(this.page.locator('[data-testid="installation-success"]')).toBeVisible({ timeout: 60000 });
  }

  async configurePermissions(permissions: string[]): Promise<void> {
    for (const permission of permissions) {
      await this.page.check(`[data-testid="permission-${permission}"]`);
    }
  }

  async resolveDependencies(): Promise<void> {
    const conflictsExist = await this.page.locator('[data-testid="dependency-conflicts"]').isVisible();
    
    if (conflictsExist) {
      await this.page.click('[data-testid="resolve-dependencies-button"]');
      await expect(this.page.locator('[data-testid="dependency-resolution-progress"]')).toBeVisible();
      await expect(this.page.locator('[data-testid="dependencies-resolved"]')).toBeVisible({ timeout: 30000 });
    }
  }

  async openPluginConfiguration(pluginId: string): Promise<void> {
    await this.page.click(`[data-testid="plugin-item-${pluginId}"]`);
    await this.page.click('[data-testid="configure-plugin-button"]');
    await expect(this.page.locator('[data-testid="plugin-config-form"]')).toBeVisible();
  }

  async fillConfiguration(config: Record<string, string>): Promise<void> {
    for (const [field, value] of Object.entries(config)) {
      await this.page.fill(`[data-testid="config-field-${field}"]`, value);
    }
  }

  async saveConfiguration(): Promise<void> {
    await this.page.click('[data-testid="save-config-button"]');
    await expect(this.page.locator('[data-testid="config-saved-success"]')).toBeVisible();
  }

  async testConfiguration(): Promise<boolean> {
    await this.page.click('[data-testid="test-config-button"]');
    await expect(this.page.locator('[data-testid="config-test-progress"]')).toBeVisible();
    await expect(this.page.locator('[data-testid="config-test-result"]')).toBeVisible({ timeout: 15000 });
    
    const testStatus = await this.page.locator('[data-testid="config-test-status"]').textContent();
    return testStatus?.toLowerCase() === 'success';
  }

  async enablePlugin(pluginId: string): Promise<void> {
    await this.page.click(`[data-testid="enable-plugin-${pluginId}"]`);
    await expect(this.page.locator(`[data-testid="plugin-status-active-${pluginId}"]`)).toBeVisible();
  }

  async disablePlugin(pluginId: string): Promise<void> {
    await this.page.click(`[data-testid="disable-plugin-${pluginId}"]`);
    await expect(this.page.locator(`[data-testid="plugin-status-inactive-${pluginId}"]`)).toBeVisible();
  }

  async uninstallPlugin(pluginId: string): Promise<void> {
    await this.page.click(`[data-testid="uninstall-plugin-${pluginId}"]`);
    await expect(this.page.locator('[data-testid="uninstall-confirmation-modal"]')).toBeVisible();
    
    await this.page.click('[data-testid="confirm-uninstall-button"]');
    await expect(this.page.locator('[data-testid="uninstall-progress"]')).toBeVisible();
    await expect(this.page.locator('[data-testid="uninstall-success"]')).toBeVisible({ timeout: 30000 });
  }

  async viewPluginLogs(pluginId: string): Promise<void> {
    await this.page.click(`[data-testid="plugin-item-${pluginId}"]`);
    await this.page.click('[data-testid="view-logs-button"]');
    await expect(this.page.locator('[data-testid="plugin-log-viewer"]')).toBeVisible();
  }

  async filterLogs(level: string): Promise<void> {
    await this.page.selectOption('[data-testid="log-level-filter"]', level);
    await expect(this.page.locator(`[data-testid="log-level-${level}"]`).first()).toBeVisible();
  }

  async searchLogs(query: string): Promise<void> {
    await this.page.fill('[data-testid="log-search-input"]', query);
    await this.page.press('[data-testid="log-search-input"]', 'Enter');
  }

  async getPluginMetrics(pluginId: string): Promise<{
    cpuUsage: string;
    memoryUsage: string;
    requestCount: string;
    errorRate: string;
  }> {
    await this.page.click(`[data-testid="plugin-item-${pluginId}"]`);
    await this.page.click('[data-testid="metrics-tab"]');
    
    const cpuUsage = await this.page.locator('[data-testid="plugin-cpu-usage"]').textContent() || '';
    const memoryUsage = await this.page.locator('[data-testid="plugin-memory-usage"]').textContent() || '';
    const requestCount = await this.page.locator('[data-testid="plugin-request-count"]').textContent() || '';
    const errorRate = await this.page.locator('[data-testid="plugin-error-rate"]').textContent() || '';
    
    return { cpuUsage, memoryUsage, requestCount, errorRate };
  }

  async checkPluginHealth(pluginId: string): Promise<string> {
    await this.page.click(`[data-testid="plugin-item-${pluginId}"]`);
    const healthStatus = await this.page.locator('[data-testid="plugin-health-status"]').textContent();
    return healthStatus?.toLowerCase() || 'unknown';
  }

  async restartPlugin(pluginId: string): Promise<void> {
    await this.page.click(`[data-testid="restart-plugin-${pluginId}"]`);
    await expect(this.page.locator('[data-testid="plugin-restarting"]')).toBeVisible();
    await expect(this.page.locator('[data-testid="plugin-restart-success"]')).toBeVisible({ timeout: 30000 });
  }

  async updatePlugin(pluginId: string): Promise<void> {
    await this.page.click(`[data-testid="update-plugin-${pluginId}"]`);
    await expect(this.page.locator('[data-testid="update-confirmation-modal"]')).toBeVisible();
    
    await this.page.click('[data-testid="confirm-update-button"]');
    await expect(this.page.locator('[data-testid="update-progress"]')).toBeVisible();
    await expect(this.page.locator('[data-testid="update-success"]')).toBeVisible({ timeout: 60000 });
  }

  async searchMarketplace(query: string): Promise<void> {
    await this.page.click('[data-testid="marketplace-tab"]');
    await this.page.fill('[data-testid="marketplace-search-input"]', query);
    await this.page.press('[data-testid="marketplace-search-input"]', 'Enter');
    await expect(this.page.locator('[data-testid="marketplace-results"]')).toBeVisible();
  }

  async filterMarketplace(category: string): Promise<void> {
    await this.page.selectOption('[data-testid="marketplace-category-filter"]', category);
    await expect(this.page.locator(`[data-testid="category-${category}"]`).first()).toBeVisible();
  }

  async viewPluginDetails(pluginId: string): Promise<void> {
    await this.page.click(`[data-testid="marketplace-plugin-${pluginId}"]`);
    await expect(this.page.locator('[data-testid="plugin-detail-modal"]')).toBeVisible();
  }

  async installFromMarketplace(pluginId: string): Promise<void> {
    await this.viewPluginDetails(pluginId);
    await this.page.click('[data-testid="install-from-marketplace-button"]');
    await this.waitForInstallationComplete();
  }

  async ratePlugin(pluginId: string, rating: number): Promise<void> {
    await this.viewPluginDetails(pluginId);
    await this.page.click(`[data-testid="star-rating-${rating}"]`);
    await this.page.click('[data-testid="submit-rating-button"]');
    await expect(this.page.locator('[data-testid="rating-submitted"]')).toBeVisible();
  }

  async reportPlugin(pluginId: string, reason: string): Promise<void> {
    await this.viewPluginDetails(pluginId);
    await this.page.click('[data-testid="report-plugin-button"]');
    await this.page.selectOption('[data-testid="report-reason-select"]', reason);
    await this.page.fill('[data-testid="report-details-textarea"]', 'Test report details');
    await this.page.click('[data-testid="submit-report-button"]');
    await expect(this.page.locator('[data-testid="report-submitted"]')).toBeVisible();
  }

  async exportPluginList(): Promise<void> {
    await this.page.click('[data-testid="export-plugins-button"]');
    await this.page.selectOption('[data-testid="export-format-selector"]', 'json');
    await this.page.click('[data-testid="download-export-button"]');
    
    const downloadPromise = this.page.waitForEvent('download');
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toContain('plugins.json');
  }

  async importPluginConfiguration(filePath: string): Promise<void> {
    await this.page.click('[data-testid="import-config-button"]');
    await this.page.setInputFiles('[data-testid="import-file-input"]', filePath);
    await this.page.click('[data-testid="upload-import-button"]');
    await expect(this.page.locator('[data-testid="import-success"]')).toBeVisible();
  }

  async acknowledgeAlert(alertId: string): Promise<void> {
    await this.page.click(`[data-testid="acknowledge-alert-${alertId}"]`);
    await expect(this.page.locator(`[data-testid="alert-acknowledged-${alertId}"]`)).toBeVisible();
  }

  async setPluginAlertThreshold(pluginId: string, metric: string, threshold: string): Promise<void> {
    await this.page.click(`[data-testid="plugin-item-${pluginId}"]`);
    await this.page.click('[data-testid="alert-settings-button"]');
    
    await this.page.fill(`[data-testid="threshold-${metric}"]`, threshold);
    await this.page.click('[data-testid="save-thresholds-button"]');
    await expect(this.page.locator('[data-testid="thresholds-saved"]')).toBeVisible();
  }
}