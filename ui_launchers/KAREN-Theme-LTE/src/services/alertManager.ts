/**
 * Alert Manager Service
 * Provides centralized alert management functionality
 */

export interface KarenAlert {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  timestamp?: Date;
  duration?: number;
  actions?: Array<{
    label: string;
    action: () => void;
  }>;
  persistent?: boolean;
  priority?: 'low' | 'medium' | 'high' | 'critical';
}

export interface AlertSettings {
  maxAlerts: number;
  defaultDuration: number;
  enableSound: boolean;
  enableDesktopNotifications: boolean;
  position: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  grouping: boolean;
}

export interface AlertHistory {
  alerts: KarenAlert[];
  totalShown: number;
  totalDismissed: number;
  averageDisplayTime: number;
}

export interface AlertMetrics {
  totalAlerts: number;
  alertsByType: Record<string, number>;
  averageDismissalTime: number;
  mostCommonType: string;
}

export interface AlertResult {
  success: boolean;
  alertId?: string;
  message?: string;
}

type AlertEventListener = () => void;
type AlertEventListeners = Record<string, AlertEventListener[]>;

class AlertManager {
  private activeAlerts: KarenAlert[] = [];
  private queuedAlerts: KarenAlert[] = [];
  private settings: AlertSettings;
  private history: AlertHistory;
  private metrics: AlertMetrics;
  private eventListeners: AlertEventListeners = {};
  private isInitialized = false;

  constructor() {
    this.settings = this.getDefaultSettings();
    this.history = this.getDefaultHistory();
    this.metrics = this.getDefaultMetrics();
  }

  private getDefaultSettings(): AlertSettings {
    return {
      maxAlerts: 5,
      defaultDuration: 5000,
      enableSound: false,
      enableDesktopNotifications: true,
      position: 'top-right',
      grouping: true,
    };
  }

  private getDefaultHistory(): AlertHistory {
    return {
      alerts: [],
      totalShown: 0,
      totalDismissed: 0,
      averageDisplayTime: 0,
    };
  }

  private getDefaultMetrics(): AlertMetrics {
    return {
      totalAlerts: 0,
      alertsByType: {},
      averageDismissalTime: 0,
      mostCommonType: 'info',
    };
  }

  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    try {
      // Load settings from localStorage
      if (typeof localStorage !== 'undefined') {
        const savedSettings = localStorage.getItem('alert-settings');
        if (savedSettings) {
          this.settings = { ...this.settings, ...JSON.parse(savedSettings) };
        }

        const savedHistory = localStorage.getItem('alert-history');
        if (savedHistory) {
          this.history = { ...this.history, ...JSON.parse(savedHistory) };
        }

        const savedMetrics = localStorage.getItem('alert-metrics');
        if (savedMetrics) {
          this.metrics = { ...this.metrics, ...JSON.parse(savedMetrics) };
        }
      }

      this.isInitialized = true;
      this.emit('initialized');
    } catch (error) {
      console.error('Failed to initialize AlertManager:', error);
      throw error;
    }
  }

  getSettings(): AlertSettings {
    return { ...this.settings };
  }

  getActiveAlerts(): KarenAlert[] {
    return [...this.activeAlerts];
  }

  getQueuedAlerts(): KarenAlert[] {
    return [...this.queuedAlerts];
  }

  getHistory(): AlertHistory {
    return { ...this.history };
  }

  getMetrics(): AlertMetrics {
    return { ...this.metrics };
  }

  async showAlert(alertData: Omit<KarenAlert, 'id' | 'timestamp'>): Promise<AlertResult> {
    const alert: KarenAlert = {
      id: this.generateId(),
      timestamp: new Date(),
      ...alertData,
    };

    try {
      // Check if we should queue the alert
      if (this.activeAlerts.length >= this.settings.maxAlerts) {
        this.queuedAlerts.push(alert);
        this.emit('alert-queued');
        return { success: true, alertId: alert.id };
      }

      // Add to active alerts
      this.activeAlerts.push(alert);
      
      // Update history and metrics
      this.updateHistory(alert);
      this.updateMetrics(alert);

      // Auto-dismiss if not persistent
      if (!alert.persistent && alert.duration !== 0) {
        setTimeout(() => {
          this.dismissAlert(alert.id);
        }, alert.duration || this.settings.defaultDuration);
      }

      this.emit('alert-shown');
      return { success: true, alertId: alert.id };
    } catch (error) {
      console.error('Failed to show alert:', error);
      return { success: false, message: 'Failed to show alert' };
    }
  }

  async showSuccess(title: string, message: string, options?: Partial<KarenAlert>): Promise<AlertResult> {
    return this.showAlert({
      type: 'success',
      title,
      message,
      ...options,
    });
  }

  async showError(title: string, message: string, options?: Partial<KarenAlert>): Promise<AlertResult> {
    return this.showAlert({
      type: 'error',
      title,
      message,
      priority: 'high',
      ...options,
    });
  }

  async showWarning(title: string, message: string, options?: Partial<KarenAlert>): Promise<AlertResult> {
    return this.showAlert({
      type: 'warning',
      title,
      message,
      priority: 'medium',
      ...options,
    });
  }

  async showInfo(title: string, message: string, options?: Partial<KarenAlert>): Promise<AlertResult> {
    return this.showAlert({
      type: 'info',
      title,
      message,
      ...options,
    });
  }

  async dismissAlert(alertId: string): Promise<AlertResult> {
    try {
      const alertIndex = this.activeAlerts.findIndex(alert => alert.id === alertId);
      if (alertIndex === -1) {
        return { success: false, message: 'Alert not found' };
      }

      this.activeAlerts.splice(alertIndex, 1);

      // Process queued alerts
      if (this.queuedAlerts.length > 0) {
        const nextAlert = this.queuedAlerts.shift();
        if (nextAlert) {
          this.activeAlerts.push(nextAlert);
          this.emit('alert-queued-shown');
        }
      }

      // Update history
      this.history.totalDismissed++;
      this.saveToLocalStorage();

      this.emit('alert-dismissed');
      return { success: true, alertId };
    } catch (error) {
      console.error('Failed to dismiss alert:', error);
      return { success: false, message: 'Failed to dismiss alert' };
    }
  }

  async dismissAllAlerts(): Promise<AlertResult[]> {
    const results: AlertResult[] = [];
    const alertIds = this.activeAlerts.map(alert => alert.id);

    for (const alertId of alertIds) {
      const result = await this.dismissAlert(alertId);
      results.push(result);
    }

    return results;
  }

  clearQueue(): void {
    this.queuedAlerts = [];
    this.emit('queue-cleared');
  }

  async updateSettings(newSettings: Partial<AlertSettings>): Promise<AlertResult> {
    try {
      this.settings = { ...this.settings, ...newSettings };
      
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem('alert-settings', JSON.stringify(this.settings));
      }

      this.emit('settings-updated');
      return { success: true };
    } catch (error) {
      console.error('Failed to update settings:', error);
      return { success: false, message: 'Failed to update settings' };
    }
  }

  addEventListener(event: string, listener: AlertEventListener): () => void {
    if (!this.eventListeners[event]) {
      this.eventListeners[event] = [];
    }
    
    this.eventListeners[event].push(listener);
    
    // Return unsubscribe function
    return () => {
      const listeners = this.eventListeners[event];
      if (listeners) {
        const index = listeners.indexOf(listener);
        if (index > -1) {
          listeners.splice(index, 1);
        }
      }
    };
  }

  private emit(event: string): void {
    const listeners = this.eventListeners[event];
    if (listeners) {
      listeners.forEach(listener => {
        try {
          listener();
        } catch (error) {
          console.error(`Error in alert event listener for ${event}:`, error);
        }
      });
    }
  }

  private updateHistory(alert: KarenAlert): void {
    this.history.alerts.unshift(alert);
    this.history.totalShown++;
    
    // Keep only last 100 alerts in history
    if (this.history.alerts.length > 100) {
      this.history.alerts = this.history.alerts.slice(0, 100);
    }
  }

  private updateMetrics(alert: KarenAlert): void {
    this.metrics.totalAlerts++;
    this.metrics.alertsByType[alert.type] = (this.metrics.alertsByType[alert.type] || 0) + 1;
    
    // Update most common type
    let maxCount = 0;
    let mostCommon = 'info';
    for (const [type, count] of Object.entries(this.metrics.alertsByType)) {
      if (count > maxCount) {
        maxCount = count;
        mostCommon = type;
      }
    }
    this.metrics.mostCommonType = mostCommon;
  }

  private saveToLocalStorage(): void {
    if (typeof localStorage !== 'undefined') {
      try {
        localStorage.setItem('alert-settings', JSON.stringify(this.settings));
        localStorage.setItem('alert-history', JSON.stringify(this.history));
        localStorage.setItem('alert-metrics', JSON.stringify(this.metrics));
      } catch (error) {
        console.error('Failed to save alert data to localStorage:', error);
      }
    }
  }

  private generateId(): string {
    return `alert-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }
}

// Singleton instance
export const alertManager = new AlertManager();
export default alertManager;