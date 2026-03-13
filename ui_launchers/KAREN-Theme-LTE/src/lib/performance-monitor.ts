/**
 * Performance Monitor
 * Provides performance monitoring functionality
 */

export interface PerformanceStats {
  fps: number;
  memoryUsage: {
    used: number;
    total: number;
    percentage: number;
  };
  renderTime: {
    average: number;
    max: number;
    min: number;
  };
  networkRequests: {
    total: number;
    successful: number;
    failed: number;
    averageResponseTime: number;
  };
  timestamp: Date;
}

export interface PerformanceAlert {
  id: string;
  type: 'fps' | 'memory' | 'render' | 'network';
  severity: 'warning' | 'error' | 'critical';
  message: string;
  threshold: number;
  actualValue: number;
  timestamp: Date;
  acknowledged?: boolean;
}

class PerformanceMonitor {
  private stats: PerformanceStats;
  private alerts: PerformanceAlert[] = [];
  private isMonitoring = false;
  private frameCount = 0;
  private lastFrameTime = 0;
  private renderTimes: number[] = [];
  private networkRequests: Array<{ startTime: number; endTime: number; success: boolean }> = [];
  private listeners: Record<string, ((data: unknown) => void)[]> = {};

  constructor() {
    this.stats = this.getDefaultStats();
  }

  private getDefaultStats(): PerformanceStats {
    return {
      fps: 0,
      memoryUsage: {
        used: 0,
        total: 0,
        percentage: 0,
      },
      renderTime: {
        average: 0,
        max: 0,
        min: 0,
      },
      networkRequests: {
        total: 0,
        successful: 0,
        failed: 0,
        averageResponseTime: 0,
      },
      timestamp: new Date(),
    };
  }

  getStats(): PerformanceStats {
    return { ...this.stats };
  }

  getAlerts(limit?: number): PerformanceAlert[] {
    if (limit && limit > 0) {
      return this.alerts.slice(0, limit);
    }
    return [...this.alerts];
  }

  start(): void {
    if (this.isMonitoring) return;

    this.isMonitoring = true;
    this.lastFrameTime = performance.now();
    this.frameCount = 0;

    // Start monitoring loop
    const monitorFrame = () => {
      const currentTime = performance.now();
      const deltaTime = currentTime - this.lastFrameTime;

      // Calculate FPS
      this.frameCount++;
      if (this.frameCount % 30 === 0) { // Update FPS every 30 frames
        const fps = 1000 / deltaTime;
        this.stats.fps = Math.round(fps);
        this.checkPerformanceThresholds();
        this.emit('stats-updated', this.stats);
      }

      // Track render times
      if (deltaTime > 16.67) { // More than 60fps (16.67ms per frame)
        this.renderTimes.push(deltaTime);
        if (this.renderTimes.length > 100) {
          this.renderTimes = this.renderTimes.slice(-100);
        }
        this.updateRenderTimeStats();
      }

      this.lastFrameTime = currentTime;
      requestAnimationFrame(monitorFrame);
    };

    requestAnimationFrame(monitorFrame);
    this.emit('monitoring-started');
  }

  stop(): void {
    this.isMonitoring = false;
    this.emit('monitoring-stopped');
  }

  onStatsUpdate(callback: (stats: PerformanceStats) => void): () => void {
    return this.addEventListener('stats-updated', callback as (data: unknown) => void);
  }

  onAlert(callback: (alert: PerformanceAlert) => void): () => void {
    return this.addEventListener('alert', callback as (data: unknown) => void);
  }

  private addEventListener(event: string, callback: (data: PerformanceStats | PerformanceAlert) => void): () => void {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    
    this.listeners[event].push(callback as (data: unknown) => void);
    
    return () => {
      const listeners = this.listeners[event];
      if (listeners) {
        const index = listeners.indexOf(callback as (data: unknown) => void);
        if (index > -1) {
          listeners.splice(index, 1);
        }
      }
    };
  }

  private emit(event: string, data?: unknown): void {
    const listeners = this.listeners[event];
    if (listeners) {
      listeners.forEach(listener => {
        try {
          listener(data);
        } catch (error) {
          console.error(`Error in performance monitor event listener for ${event}:`, error);
        }
      });
    }
  }

  private updateMemoryStats(): void {
    if (typeof performance !== 'undefined' && (performance as unknown as { memory?: { usedJSHeapSize?: number; totalJSHeapSize?: number } }).memory) {
      const memory = (performance as unknown as { memory: { usedJSHeapSize?: number; totalJSHeapSize?: number } }).memory;
      const used = memory.usedJSHeapSize || 0;
      const total = memory.totalJSHeapSize || 1;
      const percentage = (used / total) * 100;

      this.stats.memoryUsage = {
        used,
        total,
        percentage: Math.round(percentage * 100) / 100,
      };

      // Check memory threshold
      if (percentage > 90) {
        this.createAlert('memory', 'critical', 'Memory usage is critical', 90, percentage);
      } else if (percentage > 75) {
        this.createAlert('memory', 'error', 'Memory usage is high', 75, percentage);
      } else if (percentage > 50) {
        this.createAlert('memory', 'warning', 'Memory usage is elevated', 50, percentage);
      }
    }
  }

  private updateRenderTimeStats(): void {
    if (this.renderTimes.length === 0) return;

    const sum = this.renderTimes.reduce((acc, time) => acc + time, 0);
    const average = sum / this.renderTimes.length;
    const max = Math.max(...this.renderTimes);
    const min = Math.min(...this.renderTimes);

    this.stats.renderTime = {
      average: Math.round(average * 100) / 100,
      max: Math.round(max * 100) / 100,
      min: Math.round(min * 100) / 100,
    };

    // Check render time thresholds
    if (average > 33.33) { // More than 30fps (33.33ms per frame)
      this.createAlert('render', 'error', 'Render time is too slow', 33.33, average);
    } else if (average > 16.67) { // More than 60fps (16.67ms per frame)
      this.createAlert('render', 'warning', 'Render time is elevated', 16.67, average);
    }
  }

  private updateNetworkStats(): void {
    const recentRequests = this.networkRequests.slice(-100); // Last 100 requests
    const total = recentRequests.length;
    const successful = recentRequests.filter(req => req.success).length;
    const failed = total - successful;
    
    this.stats.networkRequests = {
      total,
      successful,
      failed,
      averageResponseTime: this.calculateAverageResponseTime(recentRequests),
    };

    // Check network thresholds
    const failureRate = total > 0 ? (failed / total) * 100 : 0;
    if (failureRate > 10) {
      this.createAlert('network', 'critical', 'Network failure rate is too high', 10, failureRate);
    } else if (failureRate > 5) {
      this.createAlert('network', 'error', 'Network failure rate is elevated', 5, failureRate);
    }

    const avgResponseTime = this.stats.networkRequests.averageResponseTime;
    if (avgResponseTime > 5000) { // 5 seconds
      this.createAlert('network', 'error', 'Network response time is too slow', 5000, avgResponseTime);
    } else if (avgResponseTime > 2000) { // 2 seconds
      this.createAlert('network', 'warning', 'Network response time is elevated', 2000, avgResponseTime);
    }
  }

  private calculateAverageResponseTime(requests: Array<{ startTime: number; endTime: number; success: boolean }>): number {
    const successfulRequests = requests.filter(req => req.success);
    if (successfulRequests.length === 0) return 0;

    const totalTime = successfulRequests.reduce((acc, req) => acc + (req.endTime - req.startTime), 0);
    return totalTime / successfulRequests.length;
  }

  private checkPerformanceThresholds(): void {
    this.updateMemoryStats();
    this.updateNetworkStats();
    this.stats.timestamp = new Date();
  }

  private createAlert(type: PerformanceAlert['type'], severity: PerformanceAlert['severity'], message: string, threshold: number, actualValue: number): void {
    const existingAlert = this.alerts.find(alert => 
      alert.type === type && 
      !alert.acknowledged &&
      Date.now() - alert.timestamp.getTime() < 60000 // Only consider alerts from last minute
    );

    if (!existingAlert) {
      const alert: PerformanceAlert = {
        id: this.generateAlertId(),
        type,
        severity,
        message,
        threshold,
        actualValue,
        timestamp: new Date(),
      };

      this.alerts.unshift(alert);
      
      // Keep only last 50 alerts
      if (this.alerts.length > 50) {
        this.alerts = this.alerts.slice(0, 50);
      }

      this.emit('alert', alert);
    }
  }

  private generateAlertId(): string {
    return `perf-alert-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  // Public method to track network requests
  trackNetworkRequest(startTime: number, endTime: number, success: boolean): void {
    this.networkRequests.push({
      startTime,
      endTime,
      success,
    });

    // Keep only last 1000 requests for memory efficiency
    if (this.networkRequests.length > 1000) {
      this.networkRequests = this.networkRequests.slice(-1000);
    }

    this.updateNetworkStats();
  }
}

// Singleton instance
let performanceMonitor: PerformanceMonitor | null = null;

export const getPerformanceMonitor = (): PerformanceMonitor => {
  if (!performanceMonitor) {
    performanceMonitor = new PerformanceMonitor();
  }
  return performanceMonitor;
};

export default PerformanceMonitor;
