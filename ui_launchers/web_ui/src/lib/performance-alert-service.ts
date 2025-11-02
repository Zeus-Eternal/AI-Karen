/**
 * Performance Alert Service for Karen
 * Handles performance alerts gracefully through Karen's toast system
 */

import { toast } from '@/hooks/use-toast';
import type { PerformanceAlert } from './performance-monitor';

export interface PerformanceAlertConfig {
  showSlowRequestAlerts: boolean;
  showErrorRateAlerts: boolean;
  showDegradationAlerts: boolean;
  slowRequestThreshold: number; // in milliseconds
  maxAlertsPerMinute: number;
}

class PerformanceAlertService {
  private config: PerformanceAlertConfig = {
    showSlowRequestAlerts: true,
    showErrorRateAlerts: true,
    showDegradationAlerts: true,
    slowRequestThreshold: 5000, // 5 seconds
    maxAlertsPerMinute: 3,
  };

  private alertHistory: Array<{ timestamp: number; type: string }> = [];

  /**
   * Handle a performance alert gracefully
   */
  handleAlert(alert: PerformanceAlert): void {
    // Check if we should show this type of alert
    if (!this.shouldShowAlert(alert)) {
      return;
    }

    // Check rate limiting
    if (!this.isWithinRateLimit(alert)) {
      return;
    }

    // Record the alert
    this.recordAlert(alert);

    // Show appropriate toast based on alert type and severity
    this.showToast(alert);

    // Log for debugging (but not as an error)
    this.logAlert(alert);
  }

  /**
   * Show a toast notification for the performance alert
   */
  private showToast(alert: PerformanceAlert): void {
    const { title, description, variant, duration } = this.getToastConfig(alert);

    toast({
      title,
      description,
      variant,
      duration,

  }

  /**
   * Get toast configuration based on alert type and severity
   */
  private getToastConfig(alert: PerformanceAlert): {
    title: string;
    description: string;
    variant: 'default' | 'destructive';
    duration: number;
  } {
    switch (alert.type) {
      case 'slow_request':
        return {
          title: '⏱️ Karen is thinking...',
          description: 'Your request is taking longer than usual. Karen is working on it!',
          variant: 'default',
          duration: 4000,
        };

      case 'high_error_rate':
        return {
          title: '🔧 Connection Issues',
          description: 'Karen is experiencing some connectivity issues. Please try again.',
          variant: alert.severity === 'high' ? 'destructive' : 'default',
          duration: 6000,
        };

      case 'performance_degradation':
        return {
          title: '🐌 Performance Notice',
          description: 'Karen might be a bit slower than usual. Thanks for your patience!',
          variant: 'default',
          duration: 5000,
        };

      default:
        return {
          title: '📊 Performance Notice',
          description: alert.message,
          variant: alert.severity === 'high' ? 'destructive' : 'default',
          duration: 4000,
        };
    }
  }

  /**
   * Check if we should show this type of alert
   */
  private shouldShowAlert(alert: PerformanceAlert): boolean {
    switch (alert.type) {
      case 'slow_request':
        return this.config.showSlowRequestAlerts;
      case 'high_error_rate':
        return this.config.showErrorRateAlerts;
      case 'performance_degradation':
        return this.config.showDegradationAlerts;
      default:
        return true;
    }
  }

  /**
   * Check if the alert is within rate limits
   */
  private isWithinRateLimit(alert: PerformanceAlert): boolean {
    const now = Date.now();
    const oneMinuteAgo = now - 60000;

    // Clean old alerts
    this.alertHistory = this.alertHistory.filter(
      (entry) => entry.timestamp > oneMinuteAgo
    );

    // Check if we're within the rate limit
    const recentAlerts = this.alertHistory.filter(
      (entry) => entry.type === alert.type
    );

    return recentAlerts.length < this.config.maxAlertsPerMinute;
  }

  /**
   * Record the alert in history for rate limiting
   */
  private recordAlert(alert: PerformanceAlert): void {
    this.alertHistory.push({
      timestamp: Date.now(),
      type: alert.type,

  }

  /**
   * Log the alert for debugging (not as an error)
   */
  private logAlert(alert: PerformanceAlert): void {
    const logLevel = alert.severity === 'high' ? 'warn' : 'info';
    const emoji = this.getAlertEmoji(alert.type);
    
    console[logLevel](
      `${emoji} Karen Performance: ${alert.message}`,
      {
        type: alert.type,
        severity: alert.severity,
        timestamp: alert.timestamp,
        // Don't log the full metrics object to keep logs clean
        endpoint: (alert.metrics as any)?.endpoint || 'unknown',
        duration: (alert.metrics as any)?.duration || 'unknown',
      }
    );
  }

  /**
   * Get appropriate emoji for alert type
   */
  private getAlertEmoji(type: string): string {
    switch (type) {
      case 'slow_request':
        return '⏱️';
      case 'high_error_rate':
        return '🔧';
      case 'performance_degradation':
        return '🐌';
      default:
        return '📊';
    }
  }

  /**
   * Update configuration
   */
  updateConfig(newConfig: Partial<PerformanceAlertConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }

  /**
   * Get current configuration
   */
  getConfig(): PerformanceAlertConfig {
    return { ...this.config };
  }

  /**
   * Clear alert history (useful for testing)
   */
  clearHistory(): void {
    this.alertHistory = [];
  }

  /**
   * Get alert statistics
   */
  getStats(): {
    totalAlerts: number;
    alertsByType: Record<string, number>;
    recentAlerts: number;
  } {
    const now = Date.now();
    const oneMinuteAgo = now - 60000;
    const recentAlerts = this.alertHistory.filter(
      (entry) => entry.timestamp > oneMinuteAgo
    );

    const alertsByType = this.alertHistory.reduce((acc, entry) => {
      acc[entry.type] = (acc[entry.type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return {
      totalAlerts: this.alertHistory.length,
      alertsByType,
      recentAlerts: recentAlerts.length,
    };
  }
}

// Create and export singleton instance
export const performanceAlertService = new PerformanceAlertService();

// Export the class for testing
export { PerformanceAlertService };