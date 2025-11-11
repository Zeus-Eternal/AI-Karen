/**
 * Core AlertManager Service for Karen's Graceful Alert System
 * 
 * This service provides centralized alert management with queue handling,
 * rate limiting, prioritization, and user preference management.
 */
import { toast } from '@/hooks/use-toast';
import type { AlertAction, KarenAlert, AlertSettings, AlertHistory, StoredAlert, AlertMetrics, AlertResult, AlertType, AlertPriority, ErrorRecoveryConfig } from '@/types/karen-alerts';
import { DEFAULT_ALERT_SETTINGS, DEFAULT_ERROR_RECOVERY_CONFIG } from '@/types/karen-alerts';
// Storage keys for persistence
const ALERT_SETTINGS_KEY = 'karen-alert-settings';
const ALERT_HISTORY_KEY = 'karen-alert-history';
const ALERT_METRICS_KEY = 'karen-alert-metrics';
/**
 * Event types for the alert system
 */
export type AlertEventType = 'alert-shown' | 'alert-dismissed' | 'alert-action-clicked' | 'settings-updated';
/**
 * Event listener interface
 */
export interface AlertEventListener {
  type: AlertEventType;
  callback: (data: unknown) => void;
}
/**
 * Rate limiting tracker
 */
export interface RateLimitTracker {
  [key: string]: {
    count: number;
    lastReset: number;
  };
}
/**
 * Core AlertManager class that handles all alert operations
 */
class AlertManager {
  private alertQueue: KarenAlert[] = [];
  private activeAlerts: Map<string, KarenAlert> = new Map();
  private toastInstances: Map<string, { dismiss: () => void }> = new Map();
  private settings: AlertSettings = DEFAULT_ALERT_SETTINGS;
  private history: AlertHistory = {
    alerts: [],
    maxHistory: 100,
    retentionDays: 30,
  };
  private metrics: AlertMetrics = {
    totalShown: 0,
    totalDismissed: 0,
    averageViewTime: 0,
    actionClickRate: 0,
    categoryBreakdown: {
      system: 0,
      performance: 0,
      health: 0,
      'user-action': 0,
      validation: 0,
      success: 0,
      info: 0,
    },
  };
  private eventListeners: AlertEventListener[] = [];
  private rateLimitTracker: RateLimitTracker = {};
  private errorRecoveryConfig: ErrorRecoveryConfig = DEFAULT_ERROR_RECOVERY_CONFIG;
  private isInitialized = false;
  /**
   * Initialize the AlertManager
   */
  public async initialize(): Promise<void> {
    if (this.isInitialized) return;
    try {
      await this.loadSettings();
      await this.loadHistory();
      await this.loadMetrics();
      this.cleanupExpiredHistory();
      this.isInitialized = true;
    } catch (error) {
      this.handleError('initialization-failed', error);
    }
  }
  /**
   * Show an alert with queue management and rate limiting
   */
  public async showAlert(alertData: Omit<KarenAlert, 'id' | 'timestamp'>): Promise<AlertResult> {
    try {
      // Generate unique ID and timestamp
      const alert: KarenAlert = {
        ...alertData,
        id: this.generateAlertId(),
        timestamp: Date.now(),
      };
      // Check rate limiting
      if (!this.checkRateLimit(alert)) {
        return {
          success: false,
          error: 'Rate limit exceeded',
          alertId: alert.id,
        };
      }
      // Check if category is enabled
      if (!this.isCategoryEnabled(alert.type)) {
        return {
          success: false,
          error: 'Alert category disabled',
          alertId: alert.id,
        };
      }
      // Add to queue with prioritization
      this.addToQueue(alert);
      // Process queue
      await this.processQueue();
      // Update metrics
      this.updateMetrics('shown', alert);
      // Emit event
      this.emitEvent('alert-shown', alert);
      return {
        success: true,
        alertId: alert.id,
      };
    } catch (error) {
      return this.handleError('show-alert-failed', error, alertData.title || 'Unknown Alert');
    }
  }
  /**
   * Dismiss a specific alert
   */
  public async dismissAlert(alertId: string): Promise<AlertResult> {
    try {
      const alert = this.activeAlerts.get(alertId);
      if (!alert) {
        return {
          success: false,
          error: 'Alert not found',
          alertId,
        };
      }
      // Remove from active alerts
      this.activeAlerts.delete(alertId);
      // Dismiss the toast using the stored instance
      const toastInstance = this.toastInstances.get(alertId);
      if (toastInstance) {
        toastInstance.dismiss();
        this.toastInstances.delete(alertId);
      }
      // Add to history
      this.addToHistory(alert, true);
      // Update metrics
      this.updateMetrics('dismissed', alert);
      // Emit event
      this.emitEvent('alert-dismissed', { alertId, alert });
      return {
        success: true,
        alertId,
      };
    } catch (error) {
      return this.handleError('dismiss-alert-failed', error, alertId);
    }
  }
  /**
   * Dismiss all active alerts
   */
  public async dismissAllAlerts(): Promise<AlertResult[]> {
    const results: AlertResult[] = [];
    const activeAlertIds = Array.from(this.activeAlerts.keys());
    for (const alertId of activeAlertIds) {
      const result = await this.dismissAlert(alertId);
      results.push(result);
    }
    return results;
  }
  /**
   * Get queued alerts
   */
  public getQueuedAlerts(): KarenAlert[] {
    return [...this.alertQueue];
  }
  /**
   * Clear the alert queue
   */
  public clearQueue(): void {
    this.alertQueue = [];
  }
  /**
   * Get active alerts
   */
  public getActiveAlerts(): KarenAlert[] {
    return Array.from(this.activeAlerts.values());
  }
  /**
   * Update alert settings
   */
  public async updateSettings(newSettings: Partial<AlertSettings>): Promise<AlertResult> {
    try {
      this.settings = { ...this.settings, ...newSettings };
      await this.saveSettings();
      this.emitEvent('settings-updated', this.settings);
      return {
        success: true,
        alertId: 'settings-update',
        data: this.settings,
      };
    } catch (error) {
      return this.handleError('settings-update-failed', error, 'Settings Update');
    }
  }
  /**
   * Get current settings
   */
  public getSettings(): AlertSettings {
    return { ...this.settings };
  }
  /**
   * Get alert history
   */
  public getHistory(): AlertHistory {
    return { ...this.history };
  }
  /**
   * Get alert metrics
   */
  public getMetrics(): AlertMetrics {
    return { ...this.metrics };
  }
  /**
   * Add event listener
   */
  public addEventListener(type: AlertEventType, callback: (data: unknown) => void): () => void {
    const listener: AlertEventListener = { type, callback };
    this.eventListeners.push(listener);
    // Return unsubscribe function
    return () => {
      const index = this.eventListeners.indexOf(listener);
      if (index > -1) {
        this.eventListeners.splice(index, 1);
      }
    };
  }
  /**
   * Convenience methods for common alert types
   */
  public async showSuccess(title: string, message: string, options?: Partial<KarenAlert>): Promise<AlertResult> {
    return this.showAlert({
      type: 'success',
      variant: 'karen-success',
      title,
      message,
      emoji: '✅',
      priority: 'normal',
      source: 'user-action',
      ...options,
    });

  }
  public async showError(title: string, message: string, options?: Partial<KarenAlert>): Promise<AlertResult> {
    return this.showAlert({
      type: 'validation',
      variant: 'karen-error',
      title,
      message,
      emoji: '❌',
      priority: 'high',
      source: 'system',
      ...options,
    });

  }
  public async showWarning(title: string, message: string, options?: Partial<KarenAlert>): Promise<AlertResult> {
    return this.showAlert({
      type: 'info',
      variant: 'karen-warning',
      title,
      message,
      emoji: '⚠️',
      priority: 'normal',
      source: 'system',
      ...options,
    });

  }
  public async showInfo(title: string, message: string, options?: Partial<KarenAlert>): Promise<AlertResult> {
    return this.showAlert({
      type: 'info',
      variant: 'karen-info',
      title,
      message,
      emoji: 'ℹ️',
      priority: 'low',
      source: 'system',
      ...options,
    });

  }
  // Private methods
  private generateAlertId(): string {
    return `karen-alert-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }
  private checkRateLimit(alert: KarenAlert): boolean {
    const key = `${alert.type}-${alert.variant}`;
    const now = Date.now();
    const oneMinute = 60 * 1000;
    if (!this.rateLimitTracker[key]) {
      this.rateLimitTracker[key] = { count: 0, lastReset: now };
    }
    const tracker = this.rateLimitTracker[key];
    // Reset counter if more than a minute has passed
    if (now - tracker.lastReset > oneMinute) {
      tracker.count = 0;
      tracker.lastReset = now;
    }
    // Check if we're within limits (max 5 alerts per minute per type)
    if (tracker.count >= 5) {
      return false;
    }
    tracker.count++;
    return true;
  }
  private isCategoryEnabled(type: AlertType): boolean {
    switch (type) {
      case 'performance':
        return this.settings.categories.performance;
      case 'health':
        return this.settings.categories.health;
      case 'system':
        return this.settings.categories.system;
      case 'validation':
        return this.settings.categories.validation;
      default:
        return true; // Enable success, info, user-action by default
    }
  }
  private addToQueue(alert: KarenAlert): void {
    // Insert alert based on priority
    const priorityOrder: AlertPriority[] = ['critical', 'high', 'normal', 'low'];
    const alertPriorityIndex = priorityOrder.indexOf(alert.priority);
    let insertIndex = this.alertQueue.length;
    for (let i = 0; i < this.alertQueue.length; i++) {
      const queuedPriorityIndex = priorityOrder.indexOf(this.alertQueue[i].priority);
      if (alertPriorityIndex < queuedPriorityIndex) {
        insertIndex = i;
        break;
      }
    }
    this.alertQueue.splice(insertIndex, 0, alert);
  }
  private async processQueue(): Promise<void> {
    // Check if we can show more alerts
    const maxConcurrent = this.settings.maxConcurrentAlerts;
    const currentActive = this.activeAlerts.size;
    if (currentActive >= maxConcurrent || this.alertQueue.length === 0) {
      return;
    }
    // Get next alert from queue
    const alert = this.alertQueue.shift();
    if (!alert) return;
    // Add to active alerts
    this.activeAlerts.set(alert.id, alert);
    // Show the toast
    const duration = alert.duration || this.getDurationForType(alert.type);
    const toastInstance = toast({
      title: `${alert.emoji || ''} ${alert.title}`.trim(),
      description: alert.message,
      variant: alert.variant === 'karen-error' ? 'destructive' : 'default',
      duration,
    });

    // Store the toast instance for dismissal
    this.toastInstances.set(alert.id, toastInstance);
    // Auto-dismiss after duration
    setTimeout(() => {
      if (this.activeAlerts.has(alert.id)) {
        this.dismissAlert(alert.id);
      }
    }, duration);
    // Process next alert if queue has more
    if (this.alertQueue.length > 0) {
      setTimeout(() => this.processQueue(), 100);
    }
  }
  private getDurationForType(type: AlertType): number {
    switch (type) {
      case 'success':
        return this.settings.durations.success;
      case 'info':
        return this.settings.durations.info;
      case 'validation':
        return this.settings.durations.error;
      case 'system':
      case 'performance':
      case 'health':
        return this.settings.durations.system;
      default:
        return this.settings.durations.info;
    }
  }
  private async handleAlertAction(alert: KarenAlert, action: AlertAction): Promise<void> {
    try {
      await action.action();
      this.updateMetrics('action-clicked', alert);
      this.emitEvent('alert-action-clicked', { alert, action });
    } catch (error) {
      console.debug('Alert action failed', error);
    }
  }
  private addToHistory(alert: KarenAlert, dismissed: boolean): void {
    const storedAlert: StoredAlert = {
      ...alert,
      dismissed,
      dismissedAt: dismissed ? Date.now() : undefined,
      interactionCount: 0,
      lastInteraction: Date.now(),
    };
    this.history.alerts.unshift(storedAlert);
    // Trim history to max size
    if (this.history.alerts.length > this.history.maxHistory) {
      this.history.alerts = this.history.alerts.slice(0, this.history.maxHistory);
    }
    this.saveHistory();
  }
  private updateMetrics(action: 'shown' | 'dismissed' | 'action-clicked', alert: KarenAlert): void {
    switch (action) {
      case 'shown':
        this.metrics.totalShown++;
        this.metrics.categoryBreakdown[alert.type]++;
        break;
      case 'dismissed':
        this.metrics.totalDismissed++;
        break;
      case 'action-clicked':
        // Update action click rate
        this.metrics.actionClickRate =
          (this.metrics.actionClickRate * (this.metrics.totalShown - 1) + 1) / this.metrics.totalShown;
        break;
    }
    this.saveMetrics();
  }
  private emitEvent(type: AlertEventType, data: unknown): void {
    this.eventListeners
      .filter(listener => listener.type === type)
      .forEach(listener => {
        try {
          listener.callback(data);
        } catch (error) {
          console.warn('AlertManager listener failed', { type, error });
        }
      });
  }
  private cleanupExpiredHistory(): void {
    if (!this.history.alerts || !Array.isArray(this.history.alerts)) {
      this.history.alerts = [];
      return;
    }
    const cutoffDate = Date.now() - (this.history.retentionDays * 24 * 60 * 60 * 1000);
    this.history.alerts = this.history.alerts.filter(alert => alert.timestamp > cutoffDate);
    this.saveHistory();
  }
  private handleError(type: string, error: unknown, context?: string): AlertResult {
    const errorMessage = error instanceof Error ? error.message : String(error);
    // Log error for debugging
    // Apply fallback behavior
    switch (this.errorRecoveryConfig.fallbackBehavior) {
      case 'console':
        console.error(`[AlertManager:${type}]`, errorMessage, { context, error });
        break;
      case 'basic-alert':
        if (typeof window !== 'undefined' && window.alert) {
          window.alert(`Karen Alert: ${context || 'Alert'} - ${errorMessage}`);
        }
        break;
      case 'silent':
      default:
        console.debug(`[AlertManager:${type}] silent fallback`, { context, error });
        break;
    }
    return {
      success: false,
      error: errorMessage,
      alertId: 'error-' + Date.now(),
    };
  }
  // Storage methods
  private async loadSettings(): Promise<void> {
    try {
      const stored = localStorage.getItem(ALERT_SETTINGS_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        this.settings = { ...DEFAULT_ALERT_SETTINGS, ...parsed.settings };
      }
    } catch (error) {
      console.debug('AlertManager failed to load settings', error);
      this.settings = DEFAULT_ALERT_SETTINGS;
    }
  }
  private async saveSettings(): Promise<void> {
    try {
      const data = {
        version: '1.0.0',
        settings: this.settings,
        lastUpdated: Date.now(),
      };
      localStorage.setItem(ALERT_SETTINGS_KEY, JSON.stringify(data));
    } catch (error) {
      console.debug('AlertManager failed to save settings', error);
    }
  }
  private async loadHistory(): Promise<void> {
    try {
      const stored = localStorage.getItem(ALERT_HISTORY_KEY);
      if (stored) {
        this.history = JSON.parse(stored);
      }
    } catch (error) {
      console.debug('AlertManager failed to load history', error);
    }
  }
  private async saveHistory(): Promise<void> {
    try {
      localStorage.setItem(ALERT_HISTORY_KEY, JSON.stringify(this.history));
    } catch (error) {
      console.debug('AlertManager failed to save history', error);
    }
  }
  private async loadMetrics(): Promise<void> {
    try {
      const stored = localStorage.getItem(ALERT_METRICS_KEY);
      if (stored) {
        this.metrics = { ...this.metrics, ...JSON.parse(stored) };
      }
    } catch (error) {
      console.debug('AlertManager failed to load metrics', error);
    }
  }
  private async saveMetrics(): Promise<void> {
    try {
      localStorage.setItem(ALERT_METRICS_KEY, JSON.stringify(this.metrics));
    } catch (error) {
      console.debug('AlertManager failed to save metrics', error);
    }
  }
}
// Create and export singleton instance
export const alertManager = new AlertManager();
// Export the class for testing
export { AlertManager };
// Export convenience methods
export const {
  showAlert,
  showSuccess,
  showError,
  showWarning,
  showInfo,
  dismissAlert,
  dismissAllAlerts,
  getSettings,
  updateSettings,
  getHistory,
  getMetrics,
  addEventListener,
} = alertManager;
