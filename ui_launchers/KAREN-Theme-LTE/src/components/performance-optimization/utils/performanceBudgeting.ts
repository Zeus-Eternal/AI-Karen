/**
 * Performance Budgeting and Alerts System
 * Comprehensive performance budgeting with intelligent alerting
 */

'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { PerformanceBudget, PerformanceAlert, PerformanceMetric } from '../types';

// Budget categories
export type BudgetCategory = 
  | 'total-size'
  | 'js-size'
  | 'css-size'
  | 'image-size'
  | 'font-size'
  | 'render-time'
  | 'load-time'
  | 'memory-usage'
  | 'network-requests';

// Alert severity levels
export type AlertSeverity = 'low' | 'medium' | 'high' | 'critical';

// Alert types
export type AlertType = 
  | 'budget-exceeded'
  | 'metric-poor'
  | 'bottleneck-detected'
  | 'memory-leak'
  | 'regression-detected'
  | 'threshold-approaching';

// Budget threshold configuration
interface BudgetThreshold {
  warning: number; // Warning threshold (percentage)
  critical: number; // Critical threshold (percentage)
  absolute?: number; // Absolute value threshold
}

// Budget configuration with thresholds
interface BudgetConfig {
  category: BudgetCategory;
  budget: PerformanceBudget;
  thresholds: Record<BudgetCategory, BudgetThreshold>;
  enabled: boolean;
}

// Budget manager class
class BudgetManager {
  private budgets: Map<BudgetCategory, BudgetConfig> = new Map();
  private currentUsage: Map<BudgetCategory, number> = new Map();
  private alerts: PerformanceAlert[] = [];
  private alertHistory: PerformanceAlert[] = [];
  private isMonitoring = false;
  private monitoringInterval: NodeJS.Timeout | null = null;
  private alertCallbacks: ((alert: PerformanceAlert) => void)[] = [];

  constructor() {
    this.initializeDefaultBudgets();
  }

  // Initialize default budgets
  private initializeDefaultBudgets(): void {
    // Mobile budgets
    this.setBudget('mobile', {
      totalSize: 250, // 250KB
      jsSize: 100, // 100KB
      cssSize: 50, // 50KB
      imageSize: 75, // 75KB
      fontSize: 25, // 25KB
      renderTime: 1000, // 1s
      loadTime: 3000, // 3s
    });

    // Desktop budgets
    this.setBudget('desktop', {
      totalSize: 500, // 500KB
      jsSize: 200, // 200KB
      cssSize: 100, // 100KB
      imageSize: 150, // 150KB
      fontSize: 50, // 50KB
      renderTime: 500, // 500ms
      loadTime: 2000, // 2s
    });
  }

  // Set budget for a device type
  setBudget(deviceType: 'mobile' | 'desktop', budget: PerformanceBudget): void {
    // Set individual category budgets
    Object.entries(budget).forEach(([category, value]) => {
      if (typeof value === 'number') {
        const budgetValue = value as number;
        const budgetKey = category as keyof PerformanceBudget;
        const budgetConfig: BudgetConfig = {
          category: category as BudgetCategory,
          budget: { [budgetKey]: budgetValue } as unknown as PerformanceBudget,
          thresholds: this.getThresholdsForCategory(),
          enabled: true,
        };
        
        this.budgets.set(category as BudgetCategory, budgetConfig);
      }
    });
  }

  // Get thresholds for a budget category
  private getThresholdsForCategory(): Record<BudgetCategory, BudgetThreshold> {
    const baseThresholds: Record<BudgetCategory, BudgetThreshold> = {
      'total-size': { warning: 80, critical: 100 },
      'js-size': { warning: 80, critical: 100 },
      'css-size': { warning: 80, critical: 100 },
      'image-size': { warning: 80, critical: 100 },
      'font-size': { warning: 80, critical: 100 },
      'render-time': { warning: 80, critical: 100 },
      'load-time': { warning: 80, critical: 100 },
      'memory-usage': { warning: 80, critical: 100 },
      'network-requests': { warning: 80, critical: 100 },
    };

    return baseThresholds;
  }

  // Update usage for a budget category
  updateUsage(category: BudgetCategory, value: number): void {
    this.currentUsage.set(category, value);
    
    // Check if this exceeds budget
    this.checkBudgetExceeded(category, value);
  }

  // Check if budget is exceeded
  private checkBudgetExceeded(category: BudgetCategory, value: number): void {
    const budgetConfig = this.budgets.get(category);
    if (!budgetConfig || !budgetConfig.enabled) return;

    const budgetValue = budgetConfig.budget[category as keyof PerformanceBudget] as number;
    const threshold = budgetConfig.thresholds[category];
    
    if (!budgetValue || !threshold) return;

    const percentage = (value / budgetValue) * 100;
    
    // Check critical threshold
    if (percentage >= threshold.critical) {
      this.createAlert({
        id: `budget-critical-${category}-${Date.now()}`,
        type: 'budget-exceeded',
        severity: 'critical',
        message: `Critical: ${category} budget exceeded by ${percentage - 100}%`,
        metric: category,
        threshold: budgetValue,
        actualValue: value,
        timestamp: new Date(),
      });
    }
    // Check warning threshold
    else if (percentage >= threshold.warning) {
      this.createAlert({
        id: `budget-warning-${category}-${Date.now()}`,
        type: 'threshold-approaching',
        severity: 'medium',
        message: `Warning: ${category} budget at ${percentage}% of limit`,
        metric: category,
        threshold: budgetValue,
        actualValue: value,
        timestamp: new Date(),
      });
    }
  }

  // Create an alert
  private createAlert(alert: PerformanceAlert): void {
    // Add to current alerts
    this.alerts.push(alert);
    
    // Add to history
    this.alertHistory.push(alert);
    
    // Limit history size
    if (this.alertHistory.length > 1000) {
      this.alertHistory = this.alertHistory.slice(-1000);
    }

    // Notify callbacks
    this.alertCallbacks.forEach(callback => callback(alert));
  }

  // Process metric and check for alerts
  processMetric(metric: PerformanceMetric): void {
    const category = this.mapMetricToCategory(metric.name);
    if (!category) return;

    // Update usage
    this.updateUsage(category, metric.value);

    // Check for poor performance
    if (metric.rating === 'poor') {
      this.createAlert({
        id: `metric-poor-${metric.name}-${Date.now()}`,
        type: 'metric-poor',
        severity: 'high',
        message: `Poor performance detected for ${metric.name}: ${metric.value}${metric.unit}`,
        metric: metric.name,
        threshold: metric.threshold?.poor,
        actualValue: metric.value,
        timestamp: new Date(),
      });
    }

    // Check for regression (compared to historical data)
    this.checkForRegression(metric);
  }

  // Map metric name to budget category
  private mapMetricToCategory(metricName: string): BudgetCategory | null {
    const mapping: Record<string, BudgetCategory> = {
      'page-load-time': 'load-time',
      'render-time': 'render-time',
      'memory-usage': 'memory-usage',
      'lcp': 'load-time',
      'fcp': 'load-time',
      'ttfb': 'load-time',
      'cls': 'render-time',
      'fid': 'render-time',
    };

    return mapping[metricName] || null;
  }

  // Check for performance regression
  private checkForRegression(currentMetric: PerformanceMetric): void {
    // Get historical metrics of the same type
    const historicalMetrics = this.alertHistory
      .filter(alert => alert.metric === currentMetric.name)
      .slice(-10); // Last 10 alerts

    if (historicalMetrics.length < 5) return; // Need enough data

    // Calculate average historical value
    const avgValue = historicalMetrics.reduce((sum, alert) => 
      sum + (alert.actualValue || 0), 0
    ) / historicalMetrics.length;

    // Check if current value is significantly worse
    const regressionThreshold = avgValue * 1.5; // 50% worse than average
    if (currentMetric.value > regressionThreshold) {
      this.createAlert({
        id: `regression-${currentMetric.name}-${Date.now()}`,
        type: 'regression-detected',
        severity: 'high',
        message: `Performance regression detected for ${currentMetric.name}: ${currentMetric.value}${currentMetric.unit} (avg: ${avgValue.toFixed(2)})`,
        metric: currentMetric.name,
        threshold: avgValue,
        actualValue: currentMetric.value,
        timestamp: new Date(),
      });
    }
  }

  // Start monitoring
  startMonitoring(intervalMs: number = 5000): void {
    if (this.isMonitoring) return;

    this.isMonitoring = true;
    
    this.monitoringInterval = setInterval(() => {
      this.performHealthCheck();
    }, intervalMs);
  }

  // Stop monitoring
  stopMonitoring(): void {
    if (!this.isMonitoring) return;

    this.isMonitoring = false;
    
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = null;
    }
  }

  // Perform health check
  private performHealthCheck(): void {
    // Check for memory leaks
    this.checkMemoryLeaks();
    
    // Check for bottlenecks
    this.checkBottlenecks();
  }

  // Check for memory leaks
  private checkMemoryLeaks(): void {
    // Type for memory API in browsers
    interface PerformanceMemory {
      usedJSHeapSize: number;
      totalJSHeapSize: number;
      jsHeapSizeLimit: number;
    }

    interface ExtendedPerformance extends Performance {
      memory?: PerformanceMemory;
    }

    const perf = performance as ExtendedPerformance;
    if (perf.memory) {
      const currentUsage = perf.memory.usedJSHeapSize;
      const totalUsage = perf.memory.totalJSHeapSize;
      
      // Check if memory usage is growing consistently
      const memoryGrowth = this.calculateMemoryGrowth();
      if (memoryGrowth > 0.1) { // 10% growth
        this.createAlert({
          id: `memory-leak-${Date.now()}`,
          type: 'memory-leak',
          severity: 'high',
          message: `Potential memory leak detected: ${Math.round(currentUsage / 1048576)}MB used, ${Math.round(memoryGrowth * 100)}% growth`,
          metric: 'memory-usage',
          threshold: totalUsage * 0.8,
          actualValue: currentUsage,
          timestamp: new Date(),
        });
      }
    }
  }

  // Calculate memory growth rate
  private calculateMemoryGrowth(): number {
    // This would track memory usage over time
    // For now, return 0
    return 0;
  }

  // Check for bottlenecks
  private checkBottlenecks(): void {
    // Type for performance entry with duration
    interface PerformanceEntryWithDuration extends PerformanceEntry {
      duration: number;
    }

    // Check for long tasks
    if ('PerformanceObserver' in window) {
      try {
        const observer = new PerformanceObserver((list) => {
          const entries = list.getEntries() as PerformanceEntryWithDuration[];
          entries.forEach((entry) => {
            if (entry.duration > 100) { // Long task
              this.createAlert({
                id: `bottleneck-${Date.now()}`,
                type: 'bottleneck-detected',
                severity: 'medium',
                message: `Long task detected: ${entry.duration}ms`,
                metric: 'long-task',
                threshold: 100,
                actualValue: entry.duration,
                timestamp: new Date(),
              });
            }
          });
        });
        
        observer.observe({ entryTypes: ['longtask'] });
        
        // Clean up after observation
        setTimeout(() => observer.disconnect(), 1000);
      } catch (e) {
        // Long task observation not supported
      }
    }
  }

  // Add alert callback
  addAlertCallback(callback: (alert: PerformanceAlert) => void): void {
    this.alertCallbacks.push(callback);
  }

  // Remove alert callback
  removeAlertCallback(callback: (alert: PerformanceAlert) => void): void {
    const index = this.alertCallbacks.indexOf(callback);
    if (index > -1) {
      this.alertCallbacks.splice(index, 1);
    }
  }

  // Resolve an alert
  resolveAlert(alertId: string): void {
    const alert = this.alerts.find(a => a.id === alertId);
    if (alert) {
      alert.resolved = true;
    }
  }

  // Get current alerts
  getAlerts(): PerformanceAlert[] {
    return [...this.alerts];
  }

  // Get alert history
  getAlertHistory(): PerformanceAlert[] {
    return [...this.alertHistory];
  }

  // Get budget status
  getBudgetStatus(): Record<BudgetCategory, {
    budget: number;
    used: number;
    percentage: number;
    status: 'good' | 'warning' | 'critical';
  }> {
    const result: Record<BudgetCategory, {
      budget: number;
      used: number;
      percentage: number;
      status: 'good' | 'warning' | 'critical';
    }> = {} as Record<BudgetCategory, {
      budget: number;
      used: number;
      percentage: number;
      status: 'good' | 'warning' | 'critical';
    }>;
    
    this.budgets.forEach((config, category) => {
      const budget = config.budget[category as keyof PerformanceBudget] as number;
      const used = this.currentUsage.get(category) || 0;
      const percentage = budget > 0 ? (used / budget) * 100 : 0;
      
      let currentStatus: 'good' | 'warning' | 'critical' = 'good';
      const threshold = config.thresholds[category];
      
      if (percentage >= threshold.critical) {
        currentStatus = 'critical';
      } else if (percentage >= threshold.warning) {
        currentStatus = 'warning';
      }
      
      result[category] = {
        budget,
        used,
        percentage,
        status: currentStatus,
      };
    });
    
    return result;
  }

  // Clear alerts
  clearAlerts(): void {
    this.alerts = [];
  }

  // Clear alert history
  clearAlertHistory(): void {
    this.alertHistory = [];
  }

  // Export configuration
  exportConfiguration(): string {
    const config = {
      budgets: Array.from(this.budgets.entries()),
      thresholds: Array.from(this.budgets.entries()).map(([category, config]) => [
        category,
        config.thresholds
      ]),
    };
    
    return JSON.stringify(config, null, 2);
  }

  // Import configuration
  importConfiguration(configJson: string): boolean {
    try {
      const config = JSON.parse(configJson);
      
      if (config.budgets) {
        config.budgets.forEach(([category, budgetConfig]: [BudgetCategory, BudgetConfig]) => {
          this.budgets.set(category, budgetConfig);
        });
      }
      
      return true;
    } catch (error) {
      console.error('Failed to import budget configuration:', error);
      return false;
    }
  }
}

// Hook for performance budgeting
export function usePerformanceBudgeting() {
  const [budgetStatus, setBudgetStatus] = useState<Record<BudgetCategory, {
    budget: number;
    used: number;
    percentage: number;
    status: 'good' | 'warning' | 'critical';
  }>>({} as Record<BudgetCategory, {
    budget: number;
    used: number;
    percentage: number;
    status: 'good' | 'warning' | 'critical';
  }>);
  const [alerts, setAlerts] = useState<PerformanceAlert[]>([]);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const budgetManagerRef = useRef<BudgetManager | null>(null);

  useEffect(() => {
    budgetManagerRef.current = new BudgetManager();
    
    // Set up alert callback
    budgetManagerRef.current.addAlertCallback((alert) => {
      setAlerts(prev => [...prev, alert]);
    });
    
    // Update status periodically
    const interval = setInterval(() => {
      if (budgetManagerRef.current) {
        setBudgetStatus(budgetManagerRef.current.getBudgetStatus());
        setAlerts(budgetManagerRef.current.getAlerts());
      }
    }, 2000);

    return () => {
      clearInterval(interval);
      if (budgetManagerRef.current) {
        budgetManagerRef.current.stopMonitoring();
      }
    };
  }, []);

  const startMonitoring = useCallback((intervalMs?: number) => {
    if (budgetManagerRef.current) {
      budgetManagerRef.current.startMonitoring(intervalMs);
      setIsMonitoring(true);
    }
  }, []);

  const stopMonitoring = useCallback(() => {
    if (budgetManagerRef.current) {
      budgetManagerRef.current.stopMonitoring();
      setIsMonitoring(false);
    }
  }, []);

  const updateBudget = useCallback((deviceType: 'mobile' | 'desktop', budget: PerformanceBudget) => {
    if (budgetManagerRef.current) {
      budgetManagerRef.current.setBudget(deviceType, budget);
    }
  }, []);

  const processMetric = useCallback((metric: PerformanceMetric) => {
    if (budgetManagerRef.current) {
      budgetManagerRef.current.processMetric(metric);
    }
  }, []);

  const resolveAlert = useCallback((alertId: string) => {
    if (budgetManagerRef.current) {
      budgetManagerRef.current.resolveAlert(alertId);
      setAlerts(prev => prev.map(alert => 
        alert.id === alertId ? { ...alert, resolved: true } : alert
      ));
    }
  }, []);

  const clearAlerts = useCallback(() => {
    if (budgetManagerRef.current) {
      budgetManagerRef.current.clearAlerts();
      setAlerts([]);
    }
  }, []);

  const exportConfiguration = useCallback(() => {
    if (budgetManagerRef.current) {
      return budgetManagerRef.current.exportConfiguration();
    }
    return '';
  }, []);

  const importConfiguration = useCallback((configJson: string) => {
    if (budgetManagerRef.current) {
      return budgetManagerRef.current.importConfiguration(configJson);
    }
    return false;
  }, []);

  return {
    budgetStatus,
    alerts,
    isMonitoring,
    startMonitoring,
    stopMonitoring,
    updateBudget,
    processMetric,
    resolveAlert,
    clearAlerts,
    exportConfiguration,
    importConfiguration,
  };
}

// Hook for alert notifications
export function useAlertNotifications() {
  const [permission, setPermission] = useState<NotificationPermission>('default');
  const [isSupported, setIsSupported] = useState(false);

  useEffect(() => {
    // Check if notifications are supported
    setIsSupported('Notification' in window);
    
    if ('Notification' in window) {
      setPermission(Notification.permission);
      
      // Request permission if not granted
      if (Notification.permission === 'default') {
        Notification.requestPermission().then(setPermission);
      }
    }
  }, []);

  const showAlert = useCallback((
    title: string,
    body: string,
    options?: NotificationOptions
  ) => {
    if (!isSupported || permission !== 'granted') return;

    try {
      new Notification(title, {
        body,
        icon: '/favicon.ico',
        ...options,
      });
    } catch (error) {
      console.error('Failed to show notification:', error);
    }
  }, [isSupported, permission]);

  const showAlertFromAlert = useCallback((alert: PerformanceAlert) => {
    const severityIcons = {
      low: '🟢',
      medium: '🟡',
      high: '🟠',
      critical: '🔴',
    };

    showAlert(
      `${severityIcons[alert.severity]} Performance Alert`,
      alert.message,
      {
        tag: alert.id,
        requireInteraction: alert.severity === 'critical',
      }
    );
  }, [showAlert]);

  return {
    isSupported,
    permission,
    showAlert,
    showAlertFromAlert,
  };
}

// Export singleton instance
export const budgetManager = new BudgetManager();

// Utility functions
export function createCustomBudget(
  category: BudgetCategory,
  value: number,
  warningThreshold: number = 80,
  criticalThreshold: number = 100
): PerformanceBudget {
  void warningThreshold;
  void criticalThreshold;
  const budgetKey = category as keyof PerformanceBudget;
  return {
    [budgetKey]: value,
  } as unknown as PerformanceBudget;
}

export function validateBudget(budget: PerformanceBudget): {
  isValid: boolean;
  errors: string[];
} {
  const errors: string[] = [];
  
  if (budget.totalSize && budget.totalSize < 100) {
    errors.push('Total size budget should be at least 100KB');
  }
  
  if (budget.jsSize && budget.jsSize < 50) {
    errors.push('JS size budget should be at least 50KB');
  }
  
  if (budget.cssSize && budget.cssSize < 20) {
    errors.push('CSS size budget should be at least 20KB');
  }
  
  if (budget.renderTime && budget.renderTime < 100) {
    errors.push('Render time budget should be at least 100ms');
  }
  
  if (budget.loadTime && budget.loadTime < 500) {
    errors.push('Load time budget should be at least 500ms');
  }
  
  return {
    isValid: errors.length === 0,
    errors,
  };
}

export function optimizeBudgetForDevice(
  baseBudget: PerformanceBudget,
  deviceType: 'mobile' | 'tablet' | 'desktop',
  connectionType: 'slow-2g' | '2g' | '3g' | '4g' | 'wifi'
): PerformanceBudget {
  const optimized = { ...baseBudget };
  
  // Adjust based on device type
  if (deviceType === 'mobile') {
    optimized.totalSize = Math.floor((optimized.totalSize || 0) * 0.6);
    optimized.jsSize = Math.floor((optimized.jsSize || 0) * 0.7);
    optimized.renderTime = Math.floor((optimized.renderTime || 0) * 1.5);
    optimized.loadTime = Math.floor((optimized.loadTime || 0) * 1.5);
  } else if (deviceType === 'tablet') {
    optimized.totalSize = Math.floor((optimized.totalSize || 0) * 0.8);
    optimized.jsSize = Math.floor((optimized.jsSize || 0) * 0.85);
  }
  
  // Adjust based on connection type
  if (connectionType === 'slow-2g' || connectionType === '2g') {
    optimized.totalSize = Math.floor((optimized.totalSize || 0) * 0.3);
    optimized.imageSize = Math.floor((optimized.imageSize || 0) * 0.2);
  } else if (connectionType === '3g') {
    optimized.totalSize = Math.floor((optimized.totalSize || 0) * 0.6);
    optimized.imageSize = Math.floor((optimized.imageSize || 0) * 0.5);
  }
  
  return optimized;
}
