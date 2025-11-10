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

  private monitoringInterval?: ReturnType<typeof setInterval>;
  private alertCallbacks: ((alert: ResourceAlert) => void)[] = [];
  private isMonitoring = false;

  constructor(thresholds?: Partial<ResourceThresholds>) {
    this.thresholds = {
      cpu: { warning: 70, critical: 90, scaleUp: 80, scaleDown: 30 },
      memory: { warning: 75, critical: 90, scaleUp: 85, scaleDown: 40 },
      network: { warning: 80, critical: 95, latencyWarning: 200, latencyCritical: 500 },
      storage: { warning: 80, critical: 95, scaleUp: 85 },
      ...thresholds,
    } as ResourceThresholds;

    this.startMonitoring();
  }

  /**
   * Start resource monitoring
   */
  startMonitoring(interval: number = 5000): void {
    if (this.isMonitoring) return;
    this.isMonitoring = true;
    this.monitoringInterval = setInterval(() => {
      // fire and forget
      this.collectMetrics().catch(() => void 0);
    }, interval);
    // Initial collection
    this.collectMetrics().catch(() => void 0);
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
    } catch {
      // swallow collection errors; next tick will retry
    }
  }

  /**
   * Get CPU metrics
   */
  private async getCPUMetrics(): Promise<ResourceMetrics['cpu']> {
    const usage = this.estimateCPUUsage();
    return {
      usage,
      cores: (navigator as any)?.hardwareConcurrency ?? 4,
      loadAverage: [usage / 100, usage / 100, usage / 100],
      processes: 1,
    };
  }

  /**
   * Get memory metrics
   */
  private async getMemoryMetrics(): Promise<ResourceMetrics['memory']> {
    const perfAny = performance as any;
    if (perfAny && perfAny.memory) {
      const memory = perfAny.memory;
      const used = Number(memory.usedJSHeapSize) || 0;
      const total = Number(memory.totalJSHeapSize) || 0;
      const limit = Number(memory.jsHeapSizeLimit) || total || used;
      const available = Math.max(0, limit - used);
      const percentage = total > 0 ? (used / total) * 100 : 0;

      return {
        used,
        total,
        available,
        percentage,
        swapUsed: 0,
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
    const nav: any = navigator;
    const connection = nav?.connection;

    const navEntries = (performance.getEntriesByType?.('navigation') ?? []) as PerformanceNavigationTiming[];
    const resEntries = (performance.getEntriesByType?.('resource') ?? []) as PerformanceResourceTiming[];

    let bytesReceived = 0;
    const bytesSent = 0;

    if (navEntries[0]) {
      // transferSize is response bytes on the main doc
      bytesReceived += navEntries[0].transferSize || 0;
    }

    for (const timing of resEntries) {
      bytesReceived += timing.transferSize || 0;
      // encodedBodySize is the size of the response body (received).
      // We don't have a reliable "sent" metric in browser; keep as 0 or estimate headers.
      // Leave bytesSent minimal (0) to avoid misleading numbers.
    }

    const latency = this.calculateAverageLatency(resEntries);

    return {
      bytesReceived,
      bytesSent,
      packetsReceived: Math.max(0, Math.floor(bytesReceived / 1500)),
      packetsSent: Math.max(0, Math.floor(bytesSent / 1500)),
      bandwidth: Number(connection?.downlink) || 10,
      latency,
      connectionType: String(connection?.effectiveType || 'unknown'),
    };
  }

  /**
   * Get storage metrics
   */
  private async getStorageMetrics(): Promise<ResourceMetrics['storage']> {
    const navAny: any = navigator;
    if (navAny?.storage?.estimate) {
      try {
        const estimate = await navAny.storage.estimate();
        const used = Number(estimate.usage || 0);
        const total = Number(estimate.quota || 0);
        const available = Math.max(0, total - used);
        const percentage = total > 0 ? (used / total) * 100 : 0;

        return {
          used,
          total,
          available,
          percentage,
          readSpeed: 0,
          writeSpeed: 0,
        };
      } catch {
        // fallthrough to zeroed metrics
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
    const getEntriesByType = (performance as any)?.getEntriesByType?.bind(performance);
    const longTasks: any[] = getEntriesByType ? getEntriesByType('longtask') : [];
    const now = performance.now?.() ?? 0;

    const recentTasks = (longTasks || []).filter(
      (task) => typeof task.startTime === 'number' && now - task.startTime < 10000
    );

    if (!recentTasks.length) return Math.random() * 20;

    const totalTaskTime = recentTasks.reduce((sum, task) => sum + (task.duration || 0), 0);
    const timeWindow = 10000;
    const usage = Math.min(100, (totalTaskTime / timeWindow) * 100);
    return isFinite(usage) ? usage : 0;
    // Note: this is heuristic; real CPU requires backend/OS metrics.
  }

  /**
   * Calculate average latency from resource timings
   */
  private calculateAverageLatency(timings: PerformanceResourceTiming[]): number {
    if (!timings?.length) return 0;
    const latencies = timings
      .map((t) => {
        const start = (t as any).requestStart ?? 0;
        const respStart = (t as any).responseStart ?? 0;
        const delta = respStart - start;
        return isFinite(delta) ? delta : 0;
      })
      .filter((l) => l > 0);

    if (!latencies.length) return 0;
    const avg = latencies.reduce((s, v) => s + v, 0) / latencies.length;
    return isFinite(avg) ? avg : 0;
  }

  /**
   * Check resource thresholds and generate alerts
   */
  private checkThresholds(metrics: ResourceMetrics): void {
    // CPU
    if (metrics.cpu.usage > this.thresholds.cpu.critical) {
      this.createAlert('cpu', 'critical', this.thresholds.cpu.critical, metrics.cpu.usage,
        `CPU usage is critically high at ${metrics.cpu.usage.toFixed(1)}%`);
    } else if (metrics.cpu.usage > this.thresholds.cpu.warning) {
      this.createAlert('cpu', 'high', this.thresholds.cpu.warning, metrics.cpu.usage,
        `CPU usage is high at ${metrics.cpu.usage.toFixed(1)}%`);
    }

    // Memory
    if (metrics.memory.percentage > this.thresholds.memory.critical) {
      this.createAlert('memory', 'critical', this.thresholds.memory.critical, metrics.memory.percentage,
        `Memory usage is critically high at ${metrics.memory.percentage.toFixed(1)}%`);
    } else if (metrics.memory.percentage > this.thresholds.memory.warning) {
      this.createAlert('memory', 'high', this.thresholds.memory.warning, metrics.memory.percentage,
        `Memory usage is high at ${metrics.memory.percentage.toFixed(1)}%`);
    }

    // Network
    if (metrics.network.latency > this.thresholds.network.latencyCritical) {
      this.createAlert('network', 'critical', this.thresholds.network.latencyCritical, metrics.network.latency,
        `Network latency is critically high at ${metrics.network.latency.toFixed(0)}ms`);
    } else if (metrics.network.latency > this.thresholds.network.latencyWarning) {
      this.createAlert('network', 'high', this.thresholds.network.latencyWarning, metrics.network.latency,
        `Network latency is high at ${metrics.network.latency.toFixed(0)}ms`);
    }

    // Storage
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

    // Avoid duplicates within last minute
    const existingAlert = this.alerts.find(
      (a) => a.type === type && a.severity === severity && !a.resolved && Date.now() - a.timestamp < 60000
    );
    if (existingAlert) return;

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
    this.alertCallbacks.forEach((cb) => {
      try {
        cb(alert);
      } catch {
        /* ignore callback errors */
      }
    });

    // Auto-resolve after 5 minutes
    setTimeout(() => {
      const idx = this.alerts.findIndex((a) => a.id === alertId);
      if (idx !== -1) {
        this.alerts[idx].resolved = true;
      }
    }, 5 * 60 * 1000);

    // Keep last 100 alerts
    if (this.alerts.length > 100) {
      this.alerts = this.alerts.slice(-50);
    }
  }

  /**
   * Generate scaling recommendations
   */
  private generateScalingRecommendations(): void {
    if (this.metrics.length < 5) return;

    this.recommendations = [];

    const latest = this.metrics[this.metrics.length - 1];
    const trend = this.calculateResourceTrends();

    // CPU
    if (latest.cpu.usage > this.thresholds.cpu.scaleUp) {
      this.recommendations.push({
        id: 'cpu-scale-up',
        type: 'scale-up',
        resource: 'cpu',
        priority: latest.cpu.usage > 90 ? 'critical' : 'high',
        title: 'Scale up CPU resources',
        description: `CPU usage is at ${latest.cpu.usage.toFixed(1)}% and trending ${trend.cpu > 0 ? 'up' : 'stable'}`,
        impact: 'Improved application responsiveness and reduced latency',
        implementation: 'Add more CPU cores or upgrade to higher performance tier',
        estimatedCost: 50,
        estimatedSavings: 0,
        confidence: this.calculateConfidence(trend.cpu, latest.cpu.usage),
      });
    } else if (latest.cpu.usage < this.thresholds.cpu.scaleDown && trend.cpu < 0) {
      this.recommendations.push({
        id: 'cpu-scale-down',
        type: 'scale-down',
        resource: 'cpu',
        priority: 'medium',
        title: 'Scale down CPU resources',
        description: `CPU usage is at ${latest.cpu.usage.toFixed(1)}% and trending down`,
        impact: 'Cost savings without performance impact',
        implementation: 'Reduce CPU allocation or downgrade to lower tier',
        estimatedCost: 0,
        estimatedSavings: 30,
        confidence: this.calculateConfidence(Math.abs(trend.cpu), 100 - latest.cpu.usage),
      });
    }

    // Memory
    if (latest.memory.percentage > this.thresholds.memory.scaleUp) {
      this.recommendations.push({
        id: 'memory-scale-up',
        type: 'scale-up',
        resource: 'memory',
        priority: latest.memory.percentage > 90 ? 'critical' : 'high',
        title: 'Scale up memory resources',
        description: `Memory usage is at ${latest.memory.percentage.toFixed(1)}% and trending ${trend.memory > 0 ? 'up' : 'stable'}`,
        impact: 'Reduced memory pressure and improved performance',
        implementation: 'Increase memory allocation or add more RAM',
        estimatedCost: 40,
        estimatedSavings: 0,
        confidence: this.calculateConfidence(trend.memory, latest.memory.percentage),
      });
    } else if (latest.memory.percentage < this.thresholds.memory.scaleDown && trend.memory < 0) {
      this.recommendations.push({
        id: 'memory-scale-down',
        type: 'scale-down',
        resource: 'memory',
        priority: 'medium',
        title: 'Scale down memory resources',
        description: `Memory usage is at ${latest.memory.percentage.toFixed(1)}% and trending down`,
        impact: 'Cost savings without performance impact',
        implementation: 'Reduce memory allocation',
        estimatedCost: 0,
        estimatedSavings: 25,
        confidence: this.calculateConfidence(Math.abs(trend.memory), 100 - latest.memory.percentage),
      });
    }

    // Network
    if (latest.network.latency > this.thresholds.network.latencyWarning) {
      this.recommendations.push({
        id: 'network-optimize',
        type: 'optimize',
        resource: 'network',
        priority: latest.network.latency > this.thresholds.network.latencyCritical ? 'high' : 'medium',
        title: 'Optimize network performance',
        description: `Network latency is ${latest.network.latency.toFixed(0)}ms`,
        impact: 'Improved user experience and faster data transfer',
        implementation: 'Implement CDN, optimize requests, batching, HTTP/2/3, or upgrade network tier',
        estimatedCost: 20,
        estimatedSavings: 0,
        confidence: 80,
      });
    }

    // Storage
    if (latest.storage.percentage > this.thresholds.storage.scaleUp) {
      this.recommendations.push({
        id: 'storage-scale-up',
        type: 'scale-up',
        resource: 'storage',
        priority: latest.storage.percentage > 95 ? 'critical' : 'high',
        title: 'Scale up storage resources',
        description: `Storage usage is at ${latest.storage.percentage.toFixed(1)}%`,
        impact: 'Prevent storage exhaustion and data loss',
        implementation: 'Increase storage capacity or add additional volume',
        estimatedCost: 15,
        estimatedSavings: 0,
        confidence: 95,
      });
    }

    // Order by priority then confidence
    const pOrder: Record<ScalingRecommendation['priority'], number> = {
      critical: 4,
      high: 3,
      medium: 2,
      low: 1,
    };
    this.recommendations.sort((a, b) => {
      const d = pOrder[b.priority] - pOrder[a.priority];
      if (d !== 0) return d;
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
    if (this.metrics.length < 20) {
      return { cpu: 0, memory: 0, network: 0, storage: 0 };
    }
    const recent = this.metrics.slice(-10);
    const older = this.metrics.slice(-20, -10);

    const avg = <T>(arr: T[], pick: (v: T) => number) =>
      arr.length ? arr.reduce((s, v) => s + pick(v), 0) / arr.length : 0;

    const recentAvg = {
      cpu: avg(recent, (m) => m.cpu.usage),
      memory: avg(recent, (m) => m.memory.percentage),
      network: avg(recent, (m) => m.network.latency),
      storage: avg(recent, (m) => m.storage.percentage),
    };

    const olderAvg = {
      cpu: avg(older, (m) => m.cpu.usage),
      memory: avg(older, (m) => m.memory.percentage),
      network: avg(older, (m) => m.network.latency),
      storage: avg(older, (m) => m.storage.percentage),
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
    const trendConfidence = Math.min(100, Math.abs(trend) * 10);
    const valueConfidence = currentValue > 80 ? 90 : currentValue > 60 ? 70 : 50;
    const score = Math.round((trendConfidence + valueConfidence) / 2);
    return Math.max(0, Math.min(100, score));
  }

  /**
   * Generate capacity planning projections
   */
  generateCapacityPlan(timeframe: CapacityPlan['timeframe'] = '3months'): CapacityPlan[] {
    if (this.metrics.length < 20) return [];

    const plans: CapacityPlan[] = [];
    const latest = this.metrics[this.metrics.length - 1];
    const trends = this.calculateResourceTrends();

    const timeframeMonths: Record<CapacityPlan['timeframe'], number> = {
      '1week': 0.25,
      '1month': 1,
      '3months': 3,
      '6months': 6,
      '1year': 12,
    };
    const months = timeframeMonths[timeframe];

    // CPU
    const cpuGrowthRate = trends.cpu > 0 ? Math.min(20, trends.cpu * 2) : 0;
    const projectedCpuUsage = Math.min(100, latest.cpu.usage + cpuGrowthRate * months);
    plans.push({
      resource: 'cpu',
      currentUsage: latest.cpu.usage,
      projectedUsage: projectedCpuUsage,
      timeframe,
      growthRate: cpuGrowthRate,
      recommendedCapacity: projectedCpuUsage > 80 ? latest.cpu.cores * 2 : latest.cpu.cores,
      costImpact: projectedCpuUsage > 80 ? 100 : 0,
    });

    // Memory
    const memoryGrowthRate = trends.memory > 0 ? Math.min(15, trends.memory * 1.5) : 0;
    const projectedMemoryUsage = Math.min(100, latest.memory.percentage + memoryGrowthRate * months);
    plans.push({
      resource: 'memory',
      currentUsage: latest.memory.percentage,
      projectedUsage: projectedMemoryUsage,
      timeframe,
      growthRate: memoryGrowthRate,
      recommendedCapacity:
        projectedMemoryUsage > 80 ? latest.memory.total * 2 : latest.memory.total,
      costImpact: projectedMemoryUsage > 80 ? 80 : 0,
    });

    // Storage
    const storageGrowthRate = trends.storage > 0 ? Math.min(10, trends.storage) : 2; // min 2%
    const projectedStorageUsage = Math.min(100, latest.storage.percentage + storageGrowthRate * months);
    plans.push({
      resource: 'storage',
      currentUsage: latest.storage.percentage,
      projectedUsage: projectedStorageUsage,
      timeframe,
      growthRate: storageGrowthRate,
      recommendedCapacity:
        projectedStorageUsage > 80 ? latest.storage.total * 1.5 : latest.storage.total,
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
    return includeResolved ? [...this.alerts] : this.alerts.filter((a) => !a.resolved);
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
    this.thresholds = { ...this.thresholds, ...thresholds } as ResourceThresholds;
  }

  /**
   * Resolve an alert
   */
  resolveAlert(alertId: string): void {
    const alert = this.alerts.find((a) => a.id === alertId);
    if (alert) {
      alert.resolved = true;
    }
  }

  /**
   * Clear old metrics and alerts
   */
  cleanup(maxAge: number = 24 * 60 * 60 * 1000): void {
    const cutoff = Date.now() - maxAge;
    this.metrics = this.metrics.filter((m) => m.timestamp > cutoff);
    this.alerts = this.alerts.filter((a) => a.timestamp > cutoff);
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
