/**
 * Resource Utilization Monitor
 * Tracks CPU, memory, network, and storage utilization with predictive scaling
 */

export interface ResourceMetrics {
  cpu: {
    usage: number; // percentage
    cores: number;
    loadAverage: number[];
    processes: number;
  };
  memory: {
    used: number; // bytes
    total: number; // bytes
    available: number; // bytes
    percentage: number;
    swapUsed: number;
    swapTotal: number;
  };
  network: {
    bytesReceived: number;
    bytesSent: number;
    packetsReceived: number;
    packetsSent: number;
    bandwidth: number; // Mbps
    latency: number; // ms
    connectionType: string;
  };
  storage: {
    used: number; // bytes
    total: number; // bytes
    available: number; // bytes
    percentage: number;
    readSpeed: number; // MB/s
    writeSpeed: number; // MB/s
  };
  timestamp: number;
}

export interface ResourceAlert {
  id: string;
  type: 'cpu' | 'memory' | 'network' | 'storage';
  severity: 'low' | 'medium' | 'high' | 'critical';
  threshold: number;
  currentValue: number;
  message: string;
  timestamp: number;
  resolved: boolean;
}

export interface ScalingRecommendation {
  id: string;
  type: 'scale-up' | 'scale-down' | 'optimize';
  resource: 'cpu' | 'memory' | 'network' | 'storage';
  priority: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  impact: string;
  implementation: string;
  estimatedCost: number;
  estimatedSavings: number;
  confidence: number; // 0-100
}

export interface CapacityPlan {
  resource: 'cpu' | 'memory' | 'network' | 'storage';
  currentUsage: number;
  projectedUsage: number;
  timeframe: '1week' | '1month' | '3months' | '6months' | '1year';
  growthRate: number; // percentage per month
  recommendedCapacity: number;
  costImpact: number;
}

export interface ResourceThresholds {
  cpu: {
    warning: number;
    critical: number;
    scaleUp: number;
    scaleDown: number;
  };
  memory: {
    warning: number;
    critical: number;
    scaleUp: number;
    scaleDown: number;
  };
  network: {
    warning: number;
    critical: number;
    latencyWarning: number;
    latencyCritical: number;
  };
  storage: {
    warning: number;
    critical: number;
    scaleUp: number;
  };
}

export class ResourceMonitor {
  private metrics: ResourceMetrics[] = [];
  private alerts: ResourceAlert[] = [];
  private recommendations: ScalingRecommendation[] = [];
  private thresholds: ResourceThresholds;
  private monitoringInterval?: NodeJS.Timeout;
  private alertCallbacks: ((alert: ResourceAlert) => void)[] = [];
  private isMonitoring = false;

  constructor(thresholds?: Partial<ResourceThresholds>) {
    this.thresholds = {
      cpu: {
        warning: 70,
        critical: 90,
        scaleUp: 80,
        scaleDown: 30,
      },
      memory: {
        warning: 75,
        critical: 90,
        scaleUp: 85,
        scaleDown: 40,
      },
      network: {
        warning: 80,
        critical: 95,
        latencyWarning: 200,
        latencyCritical: 500,
      },
      storage: {
        warning: 80,
        critical: 95,
        scaleUp: 85,
      },
      ...thresholds,
    };

    this.startMonitoring();
  }

  /**
   * Start resource monitoring
   */
  startMonitoring(interval: number = 5000): void {
    if (this.isMonitoring) return;

    this.isMonitoring = true;
    this.monitoringInterval = setInterval(() => {
      this.collectMetrics();
    }, interval);

    // Initial collection
    this.collectMetrics();
  }

  /**
   * Stop resource monitoring
   */
  stopMonitoring(): void {
    this.isMonitoring = false;
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = undefined;
    }
  }

  /**
   * Collect current resource metrics
   */
  private async collectMetrics(): Promise<void> {
    try {
      const metrics: ResourceMetrics = {
        cpu: await this.getCPUMetrics(),
        memory: await this.getMemoryMetrics(),
        network: await this.getNetworkMetrics(),
        storage: await this.getStorageMetrics(),
        timestamp: Date.now(),
      };

      this.metrics.push(metrics);

      // Keep only last 1000 metrics to prevent memory leaks
      if (this.metrics.length > 1000) {
        this.metrics = this.metrics.slice(-500);
      }

      // Check thresholds and generate alerts
      this.checkThresholds(metrics);

      // Generate scaling recommendations
      this.generateScalingRecommendations();

    } catch (error) {
      console.error('Failed to collect resource metrics:', error);
    }
  }

  /**
   * Get CPU metrics
   */
  private async getCPUMetrics(): Promise<ResourceMetrics['cpu']> {
    // In a browser environment, we can't get true CPU metrics
    // This would typically be provided by a backend service
    
    // Simulate CPU usage based on performance timing
    const now = performance.now();
    const usage = this.estimateCPUUsage();
    
    return {
      usage,
      cores: navigator.hardwareConcurrency || 4,
      loadAverage: [usage / 100, usage / 100, usage / 100],
      processes: 1, // Browser context
    };
  }

  /**
   * Get memory metrics
   */
  private async getMemoryMetrics(): Promise<ResourceMetrics['memory']> {
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      const used = memory.usedJSHeapSize;
      const total = memory.totalJSHeapSize;
      const limit = memory.jsHeapSizeLimit;

      return {
        used,
        total,
        available: limit - used,
        percentage: (used / total) * 100,
        swapUsed: 0, // Not available in browser
        swapTotal: 0,
      };
    }

    // Fallback for browsers without memory API
    return {
      used: 0,
      total: 0,
      available: 0,
      percentage: 0,
      swapUsed: 0,
      swapTotal: 0,
    };
  }

  /**
   * Get network metrics
   */
  private async getNetworkMetrics(): Promise<ResourceMetrics['network']> {
    const connection = (navigator as any).connection;
    
    // Get network timing from recent navigation
    const navTiming = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    const resourceTimings = performance.getEntriesByType('resource') as PerformanceResourceTiming[];

    // Calculate total bytes transferred
    let bytesReceived = 0;
    let bytesSent = 0;

    if (navTiming) {
      bytesReceived += navTiming.transferSize || 0;
    }

    resourceTimings.forEach(timing => {
      bytesReceived += timing.transferSize || 0;
      bytesSent += timing.encodedBodySize || 0;
    });

    // Estimate latency from recent requests
    const latency = this.calculateAverageLatency(resourceTimings);

    return {
      bytesReceived,
      bytesSent,
      packetsReceived: Math.floor(bytesReceived / 1500), // Estimate packets
      packetsSent: Math.floor(bytesSent / 1500),
      bandwidth: connection?.downlink || 10,
      latency,
      connectionType: connection?.effectiveType || 'unknown',
    };
  }

  /**
   * Get storage metrics
   */
  private async getStorageMetrics(): Promise<ResourceMetrics['storage']> {
    if ('storage' in navigator && 'estimate' in navigator.storage) {
      try {
        const estimate = await navigator.storage.estimate();
        const used = estimate.usage || 0;
        const total = estimate.quota || 0;

        return {
          used,
          total,
          available: total - used,
          percentage: total > 0 ? (used / total) * 100 : 0,
          readSpeed: 0, // Not available in browser
          writeSpeed: 0,
        };
      } catch (error) {
        console.warn('Failed to get storage estimate:', error);
      }
    }

    return {
      used: 0,
      total: 0,
      available: 0,
      percentage: 0,
      readSpeed: 0,
      writeSpeed: 0,
    };
  }

  /**
   * Estimate CPU usage based on performance metrics
   */
  private estimateCPUUsage(): number {
    // Use long task entries to estimate CPU pressure
    const longTasks = performance.getEntriesByType('longtask');
    const recentTasks = longTasks.filter(task => 
      Date.now() - task.startTime < 10000 // Last 10 seconds
    );

    if (recentTasks.length === 0) return Math.random() * 20; // Low usage

    const totalTaskTime = recentTasks.reduce((sum, task) => sum + task.duration, 0);
    const timeWindow = 10000; // 10 seconds
    const usage = Math.min(100, (totalTaskTime / timeWindow) * 100);

    return usage;
  }

  /**
   * Calculate average latency from resource timings
   */
  private calculateAverageLatency(timings: PerformanceResourceTiming[]): number {
    if (timings.length === 0) return 0;

    const latencies = timings.map(timing => 
      timing.responseStart - timing.requestStart
    ).filter(latency => latency > 0);

    if (latencies.length === 0) return 0;

    return latencies.reduce((sum, latency) => sum + latency, 0) / latencies.length;
  }

  /**
   * Check resource thresholds and generate alerts
   */
  private checkThresholds(metrics: ResourceMetrics): void {
    // Check CPU thresholds
    if (metrics.cpu.usage > this.thresholds.cpu.critical) {
      this.createAlert('cpu', 'critical', this.thresholds.cpu.critical, metrics.cpu.usage,
        `CPU usage is critically high at ${metrics.cpu.usage.toFixed(1)}%`);
    } else if (metrics.cpu.usage > this.thresholds.cpu.warning) {
      this.createAlert('cpu', 'high', this.thresholds.cpu.warning, metrics.cpu.usage,
        `CPU usage is high at ${metrics.cpu.usage.toFixed(1)}%`);
    }

    // Check memory thresholds
    if (metrics.memory.percentage > this.thresholds.memory.critical) {
      this.createAlert('memory', 'critical', this.thresholds.memory.critical, metrics.memory.percentage,
        `Memory usage is critically high at ${metrics.memory.percentage.toFixed(1)}%`);
    } else if (metrics.memory.percentage > this.thresholds.memory.warning) {
      this.createAlert('memory', 'high', this.thresholds.memory.warning, metrics.memory.percentage,
        `Memory usage is high at ${metrics.memory.percentage.toFixed(1)}%`);
    }

    // Check network thresholds
    if (metrics.network.latency > this.thresholds.network.latencyCritical) {
      this.createAlert('network', 'critical', this.thresholds.network.latencyCritical, metrics.network.latency,
        `Network latency is critically high at ${metrics.network.latency.toFixed(0)}ms`);
    } else if (metrics.network.latency > this.thresholds.network.latencyWarning) {
      this.createAlert('network', 'high', this.thresholds.network.latencyWarning, metrics.network.latency,
        `Network latency is high at ${metrics.network.latency.toFixed(0)}ms`);
    }

    // Check storage thresholds
    if (metrics.storage.percentage > this.thresholds.storage.critical) {
      this.createAlert('storage', 'critical', this.thresholds.storage.critical, metrics.storage.percentage,
        `Storage usage is critically high at ${metrics.storage.percentage.toFixed(1)}%`);
    } else if (metrics.storage.percentage > this.thresholds.storage.warning) {
      this.createAlert('storage', 'high', this.thresholds.storage.warning, metrics.storage.percentage,
        `Storage usage is high at ${metrics.storage.percentage.toFixed(1)}%`);
    }
  }

  /**
   * Create a resource alert
   */
  private createAlert(
    type: ResourceAlert['type'],
    severity: ResourceAlert['severity'],
    threshold: number,
    currentValue: number,
    message: string
  ): void {
    const alertId = `${type}-${severity}-${Date.now()}`;
    
    // Check if similar alert already exists
    const existingAlert = this.alerts.find(alert => 
      alert.type === type && 
      alert.severity === severity && 
      !alert.resolved &&
      Date.now() - alert.timestamp < 60000 // Within last minute
    );

    if (existingAlert) return; // Don't create duplicate alerts

    const alert: ResourceAlert = {
      id: alertId,
      type,
      severity,
      threshold,
      currentValue,
      message,
      timestamp: Date.now(),
      resolved: false,
    };

    this.alerts.push(alert);
    this.alertCallbacks.forEach(callback => callback(alert));

    // Auto-resolve alerts after 5 minutes
    setTimeout(() => {
      const alertIndex = this.alerts.findIndex(a => a.id === alertId);
      if (alertIndex !== -1) {
        this.alerts[alertIndex].resolved = true;
      }
    }, 5 * 60 * 1000);

    // Keep only last 100 alerts
    if (this.alerts.length > 100) {
      this.alerts = this.alerts.slice(-50);
    }
  }

  /**
   * Generate scaling recommendations
   */
  private generateScalingRecommendations(): void {
    if (this.metrics.length < 5) return; // Need some history

    this.recommendations = [];
    const latestMetrics = this.metrics[this.metrics.length - 1];
    const trend = this.calculateResourceTrends();

    // CPU scaling recommendations
    if (latestMetrics.cpu.usage > this.thresholds.cpu.scaleUp) {
      this.recommendations.push({
        id: 'cpu-scale-up',
        type: 'scale-up',
        resource: 'cpu',
        priority: latestMetrics.cpu.usage > 90 ? 'critical' : 'high',
        title: 'Scale up CPU resources',
        description: `CPU usage is at ${latestMetrics.cpu.usage.toFixed(1)}% and trending ${trend.cpu > 0 ? 'up' : 'stable'}`,
        impact: 'Improved application responsiveness and reduced latency',
        implementation: 'Add more CPU cores or upgrade to higher performance tier',
        estimatedCost: 50,
        estimatedSavings: 0,
        confidence: this.calculateConfidence(trend.cpu, latestMetrics.cpu.usage),
      });
    } else if (latestMetrics.cpu.usage < this.thresholds.cpu.scaleDown && trend.cpu < 0) {
      this.recommendations.push({
        id: 'cpu-scale-down',
        type: 'scale-down',
        resource: 'cpu',
        priority: 'medium',
        title: 'Scale down CPU resources',
        description: `CPU usage is at ${latestMetrics.cpu.usage.toFixed(1)}% and trending down`,
        impact: 'Cost savings without performance impact',
        implementation: 'Reduce CPU allocation or downgrade to lower tier',
        estimatedCost: 0,
        estimatedSavings: 30,
        confidence: this.calculateConfidence(Math.abs(trend.cpu), 100 - latestMetrics.cpu.usage),
      });
    }

    // Memory scaling recommendations
    if (latestMetrics.memory.percentage > this.thresholds.memory.scaleUp) {
      this.recommendations.push({
        id: 'memory-scale-up',
        type: 'scale-up',
        resource: 'memory',
        priority: latestMetrics.memory.percentage > 90 ? 'critical' : 'high',
        title: 'Scale up memory resources',
        description: `Memory usage is at ${latestMetrics.memory.percentage.toFixed(1)}% and trending ${trend.memory > 0 ? 'up' : 'stable'}`,
        impact: 'Reduced memory pressure and improved performance',
        implementation: 'Increase memory allocation or add more RAM',
        estimatedCost: 40,
        estimatedSavings: 0,
        confidence: this.calculateConfidence(trend.memory, latestMetrics.memory.percentage),
      });
    } else if (latestMetrics.memory.percentage < this.thresholds.memory.scaleDown && trend.memory < 0) {
      this.recommendations.push({
        id: 'memory-scale-down',
        type: 'scale-down',
        resource: 'memory',
        priority: 'medium',
        title: 'Scale down memory resources',
        description: `Memory usage is at ${latestMetrics.memory.percentage.toFixed(1)}% and trending down`,
        impact: 'Cost savings without performance impact',
        implementation: 'Reduce memory allocation',
        estimatedCost: 0,
        estimatedSavings: 25,
        confidence: this.calculateConfidence(Math.abs(trend.memory), 100 - latestMetrics.memory.percentage),
      });
    }

    // Network optimization recommendations
    if (latestMetrics.network.latency > this.thresholds.network.latencyWarning) {
      this.recommendations.push({
        id: 'network-optimize',
        type: 'optimize',
        resource: 'network',
        priority: latestMetrics.network.latency > 500 ? 'high' : 'medium',
        title: 'Optimize network performance',
        description: `Network latency is ${latestMetrics.network.latency.toFixed(0)}ms`,
        impact: 'Improved user experience and faster data transfer',
        implementation: 'Implement CDN, optimize requests, or upgrade network tier',
        estimatedCost: 20,
        estimatedSavings: 0,
        confidence: 80,
      });
    }

    // Storage scaling recommendations
    if (latestMetrics.storage.percentage > this.thresholds.storage.scaleUp) {
      this.recommendations.push({
        id: 'storage-scale-up',
        type: 'scale-up',
        resource: 'storage',
        priority: latestMetrics.storage.percentage > 95 ? 'critical' : 'high',
        title: 'Scale up storage resources',
        description: `Storage usage is at ${latestMetrics.storage.percentage.toFixed(1)}%`,
        impact: 'Prevent storage exhaustion and data loss',
        implementation: 'Increase storage capacity or add additional storage',
        estimatedCost: 15,
        estimatedSavings: 0,
        confidence: 95,
      });
    }

    // Sort recommendations by priority and confidence
    this.recommendations.sort((a, b) => {
      const priorityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
      const priorityDiff = priorityOrder[b.priority] - priorityOrder[a.priority];
      if (priorityDiff !== 0) return priorityDiff;
      return b.confidence - a.confidence;
    });
  }

  /**
   * Calculate resource usage trends
   */
  private calculateResourceTrends(): {
    cpu: number;
    memory: number;
    network: number;
    storage: number;
  } {
    if (this.metrics.length < 10) {
      return { cpu: 0, memory: 0, network: 0, storage: 0 };
    }

    const recent = this.metrics.slice(-10);
    const older = this.metrics.slice(-20, -10);

    const recentAvg = {
      cpu: recent.reduce((sum, m) => sum + m.cpu.usage, 0) / recent.length,
      memory: recent.reduce((sum, m) => sum + m.memory.percentage, 0) / recent.length,
      network: recent.reduce((sum, m) => sum + m.network.latency, 0) / recent.length,
      storage: recent.reduce((sum, m) => sum + m.storage.percentage, 0) / recent.length,
    };

    const olderAvg = {
      cpu: older.reduce((sum, m) => sum + m.cpu.usage, 0) / older.length,
      memory: older.reduce((sum, m) => sum + m.memory.percentage, 0) / older.length,
      network: older.reduce((sum, m) => sum + m.network.latency, 0) / older.length,
      storage: older.reduce((sum, m) => sum + m.storage.percentage, 0) / older.length,
    };

    return {
      cpu: recentAvg.cpu - olderAvg.cpu,
      memory: recentAvg.memory - olderAvg.memory,
      network: recentAvg.network - olderAvg.network,
      storage: recentAvg.storage - olderAvg.storage,
    };
  }

  /**
   * Calculate confidence score for recommendations
   */
  private calculateConfidence(trend: number, currentValue: number): number {
    // Higher confidence for stronger trends and extreme values
    const trendConfidence = Math.min(100, Math.abs(trend) * 10);
    const valueConfidence = currentValue > 80 ? 90 : currentValue > 60 ? 70 : 50;
    
    return Math.round((trendConfidence + valueConfidence) / 2);
  }

  /**
   * Generate capacity planning projections
   */
  generateCapacityPlan(timeframe: CapacityPlan['timeframe'] = '3months'): CapacityPlan[] {
    if (this.metrics.length < 20) {
      return []; // Need more historical data
    }

    const plans: CapacityPlan[] = [];
    const latestMetrics = this.metrics[this.metrics.length - 1];
    const trends = this.calculateResourceTrends();

    const timeframeMonths = {
      '1week': 0.25,
      '1month': 1,
      '3months': 3,
      '6months': 6,
      '1year': 12,
    };

    const months = timeframeMonths[timeframe];

    // CPU capacity planning
    const cpuGrowthRate = trends.cpu > 0 ? Math.min(20, trends.cpu * 2) : 0;
    const projectedCpuUsage = Math.min(100, latestMetrics.cpu.usage + (cpuGrowthRate * months));
    
    plans.push({
      resource: 'cpu',
      currentUsage: latestMetrics.cpu.usage,
      projectedUsage: projectedCpuUsage,
      timeframe,
      growthRate: cpuGrowthRate,
      recommendedCapacity: projectedCpuUsage > 80 ? latestMetrics.cpu.cores * 2 : latestMetrics.cpu.cores,
      costImpact: projectedCpuUsage > 80 ? 100 : 0,
    });

    // Memory capacity planning
    const memoryGrowthRate = trends.memory > 0 ? Math.min(15, trends.memory * 1.5) : 0;
    const projectedMemoryUsage = Math.min(100, latestMetrics.memory.percentage + (memoryGrowthRate * months));
    
    plans.push({
      resource: 'memory',
      currentUsage: latestMetrics.memory.percentage,
      projectedUsage: projectedMemoryUsage,
      timeframe,
      growthRate: memoryGrowthRate,
      recommendedCapacity: projectedMemoryUsage > 80 ? latestMetrics.memory.total * 2 : latestMetrics.memory.total,
      costImpact: projectedMemoryUsage > 80 ? 80 : 0,
    });

    // Storage capacity planning
    const storageGrowthRate = trends.storage > 0 ? Math.min(10, trends.storage) : 2; // Assume 2% growth minimum
    const projectedStorageUsage = Math.min(100, latestMetrics.storage.percentage + (storageGrowthRate * months));
    
    plans.push({
      resource: 'storage',
      currentUsage: latestMetrics.storage.percentage,
      projectedUsage: projectedStorageUsage,
      timeframe,
      growthRate: storageGrowthRate,
      recommendedCapacity: projectedStorageUsage > 80 ? latestMetrics.storage.total * 1.5 : latestMetrics.storage.total,
      costImpact: projectedStorageUsage > 80 ? 30 : 0,
    });

    return plans;
  }

  /**
   * Get current resource metrics
   */
  getCurrentMetrics(): ResourceMetrics | null {
    return this.metrics.length > 0 ? this.metrics[this.metrics.length - 1] : null;
  }

  /**
   * Get historical metrics
   */
  getHistoricalMetrics(limit?: number): ResourceMetrics[] {
    return limit ? this.metrics.slice(-limit) : [...this.metrics];
  }

  /**
   * Get active alerts
   */
  getAlerts(includeResolved: boolean = false): ResourceAlert[] {
    return includeResolved 
      ? [...this.alerts]
      : this.alerts.filter(alert => !alert.resolved);
  }

  /**
   * Get scaling recommendations
   */
  getScalingRecommendations(): ScalingRecommendation[] {
    return [...this.recommendations];
  }

  /**
   * Subscribe to alerts
   */
  onAlert(callback: (alert: ResourceAlert) => void): () => void {
    this.alertCallbacks.push(callback);
    return () => {
      const index = this.alertCallbacks.indexOf(callback);
      if (index > -1) {
        this.alertCallbacks.splice(index, 1);
      }
    };
  }

  /**
   * Update thresholds
   */
  updateThresholds(thresholds: Partial<ResourceThresholds>): void {
    this.thresholds = { ...this.thresholds, ...thresholds };
  }

  /**
   * Resolve an alert
   */
  resolveAlert(alertId: string): void {
    const alert = this.alerts.find(a => a.id === alertId);
    if (alert) {
      alert.resolved = true;
    }
  }

  /**
   * Clear old metrics and alerts
   */
  cleanup(maxAge: number = 24 * 60 * 60 * 1000): void {
    const cutoff = Date.now() - maxAge;
    
    this.metrics = this.metrics.filter(m => m.timestamp > cutoff);
    this.alerts = this.alerts.filter(a => a.timestamp > cutoff);
  }

  /**
   * Destroy the monitor
   */
  destroy(): void {
    this.stopMonitoring();
    this.alertCallbacks = [];
    this.metrics = [];
    this.alerts = [];
    this.recommendations = [];
  }
}

// Singleton instance
export const resourceMonitor = new ResourceMonitor();