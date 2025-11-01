import { Page, expect } from '@playwright/test';

export class DashboardHelper {
  constructor(private page: Page) {}

  async enterCustomizationMode(): Promise<void> {
    await this.page.click('[data-testid="customize-dashboard-button"]');
    await expect(this.page.locator('[data-testid="customization-mode-active"]')).toBeVisible();
  }

  async exitCustomizationMode(): Promise<void> {
    await this.page.click('[data-testid="exit-customization-button"]');
    await expect(this.page.locator('[data-testid="customization-mode-active"]')).not.toBeVisible();
  }

  async moveWidget(widgetId: string, targetZoneId: string): Promise<void> {
    const widget = this.page.locator(`[data-testid="${widgetId}"]`);
    const targetZone = this.page.locator(`[data-testid="${targetZoneId}"]`);
    
    await widget.dragTo(targetZone);
    await expect(targetZone.locator(`[data-testid="${widgetId}"]`)).toBeVisible();
  }

  async addWidget(widgetType: string): Promise<void> {
    await this.page.click('[data-testid="add-widget-button"]');
    await expect(this.page.locator('[data-testid="widget-selector-modal"]')).toBeVisible();
    
    await this.page.click(`[data-testid="widget-type-${widgetType}"]`);
    await this.page.click('[data-testid="add-selected-widget-button"]');
    
    await expect(this.page.locator(`[data-testid="${widgetType}-widget"]`)).toBeVisible();
  }

  async removeWidget(widgetId: string): Promise<void> {
    const widget = this.page.locator(`[data-testid="${widgetId}"]`);
    await widget.hover();
    await widget.locator('[data-testid="remove-widget-button"]').click();
    
    // Confirm removal
    await this.page.click('[data-testid="confirm-remove-widget"]');
    await expect(widget).not.toBeVisible();
  }

  async resizeWidget(widgetId: string, direction: 'expand' | 'shrink'): Promise<void> {
    const widget = this.page.locator(`[data-testid="${widgetId}"]`);
    await widget.hover();
    
    const resizeHandle = widget.locator('[data-testid="resize-handle"]');
    const boundingBox = await widget.boundingBox();
    
    if (boundingBox) {
      const startX = boundingBox.x + boundingBox.width;
      const startY = boundingBox.y + boundingBox.height;
      const offset = direction === 'expand' ? 50 : -50;
      
      await resizeHandle.dragTo(this.page.locator('body'), {
        sourcePosition: { x: 0, y: 0 },
        targetPosition: { x: startX + offset, y: startY + offset }
      });
    }
  }

  async saveLayout(): Promise<void> {
    await this.page.click('[data-testid="save-layout-button"]');
    await expect(this.page.locator('[data-testid="layout-saved-success"]')).toBeVisible();
  }

  async resetLayout(): Promise<void> {
    await this.page.click('[data-testid="reset-layout-button"]');
    await this.page.click('[data-testid="confirm-reset-layout"]');
    await expect(this.page.locator('[data-testid="layout-reset-success"]')).toBeVisible();
  }

  async setRefreshInterval(interval: string): Promise<void> {
    await this.page.selectOption('[data-testid="refresh-interval-selector"]', interval);
    await expect(this.page.locator('[data-testid="refresh-interval-updated"]')).toBeVisible();
  }

  async exportDashboard(): Promise<void> {
    await this.page.click('[data-testid="export-dashboard-button"]');
    await expect(this.page.locator('[data-testid="export-modal"]')).toBeVisible();
    
    await this.page.selectOption('[data-testid="export-format-selector"]', 'json');
    await this.page.click('[data-testid="download-export-button"]');
    
    // Wait for download to start
    const downloadPromise = this.page.waitForEvent('download');
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toContain('dashboard');
  }

  async importDashboard(filePath: string): Promise<void> {
    await this.page.click('[data-testid="import-dashboard-button"]');
    await expect(this.page.locator('[data-testid="import-modal"]')).toBeVisible();
    
    await this.page.setInputFiles('[data-testid="import-file-input"]', filePath);
    await this.page.click('[data-testid="upload-import-button"]');
    
    await expect(this.page.locator('[data-testid="import-success"]')).toBeVisible();
  }

  async filterMetrics(filterType: string, value: string): Promise<void> {
    await this.page.click('[data-testid="metrics-filter-button"]');
    await expect(this.page.locator('[data-testid="metrics-filter-panel"]')).toBeVisible();
    
    await this.page.selectOption(`[data-testid="filter-${filterType}"]`, value);
    await this.page.click('[data-testid="apply-filters-button"]');
    
    await expect(this.page.locator('[data-testid="filters-applied"]')).toBeVisible();
  }

  async setTimeRange(range: string): Promise<void> {
    await this.page.selectOption('[data-testid="time-range-selector"]', range);
    await expect(this.page.locator('[data-testid="time-range-updated"]')).toBeVisible();
  }

  async refreshDashboard(): Promise<void> {
    await this.page.click('[data-testid="refresh-dashboard-button"]');
    await expect(this.page.locator('[data-testid="dashboard-refreshing"]')).toBeVisible();
    await expect(this.page.locator('[data-testid="dashboard-refreshing"]')).not.toBeVisible();
  }

  async getMetricValue(metricId: string): Promise<string | null> {
    const metric = this.page.locator(`[data-testid="${metricId}-value"]`);
    return await metric.textContent();
  }

  async waitForMetricUpdate(metricId: string, timeout: number = 10000): Promise<void> {
    const initialValue = await this.getMetricValue(metricId);
    
    await this.page.waitForFunction(
      ({ metricId, initialValue }) => {
        const element = document.querySelector(`[data-testid="${metricId}-value"]`);
        return element && element.textContent !== initialValue;
      },
      { metricId, initialValue },
      { timeout }
    );
  }

  async checkAlertPresence(alertType: string): Promise<boolean> {
    try {
      await expect(this.page.locator(`[data-testid="alert-${alertType}"]`)).toBeVisible({ timeout: 2000 });
      return true;
    } catch {
      return false;
    }
  }

  async dismissAlert(alertId: string): Promise<void> {
    await this.page.click(`[data-testid="dismiss-alert-${alertId}"]`);
    await expect(this.page.locator(`[data-testid="alert-${alertId}"]`)).not.toBeVisible();
  }
}