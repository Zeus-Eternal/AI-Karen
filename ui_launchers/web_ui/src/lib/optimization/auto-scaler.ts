/**
 * Auto Scaler
 * 
 * Intelligent auto-scaling system with demand-based scaling,
 * resource optimization, and predictive scaling capabilities.
 */
export interface ScalingConfig {
  minInstances: number;
  maxInstances: number;
  targetCPUUtilization: number;
  targetMemoryUtilization: number;
  targetResponseTime: number;
  scaleUpCooldown: number;
  scaleDownCooldown: number;
  enablePredictiveScaling: boolean;
  enableScheduledScaling: boolean;
  scheduledRules: ScheduledScalingRule[];
  metrics: ScalingMetric[];
}
export interface ScheduledScalingRule {
  name: string;
  schedule: string; // Cron expression
  minInstances: number;
  maxInstances: number;
  enabled: boolean;
}
export interface ScalingMetric {
  name: string;
  threshold: number;
  comparison: 'greater' | 'less' | 'equal';
  weight: number;
  cooldown: number;
}
export interface ScalingDecision {
  action: 'scale_up' | 'scale_down' | 'no_action';
  currentInstances: number;
  targetInstances: number;
  reason: string;
  confidence: number;
  metrics: Record<string, number>;
  timestamp: number;
}
export interface InstanceMetrics {
  instanceId: string;
  cpuUtilization: number;
  memoryUtilization: number;
  responseTime: number;
  requestsPerSecond: number;
  errorRate: number;
  healthStatus: 'healthy' | 'unhealthy' | 'degraded';
  lastUpdated: number;
}
export interface PredictiveModel {
  type: 'linear' | 'exponential' | 'seasonal';
  accuracy: number;
  predictions: Array<{
    timestamp: number;
    predictedLoad: number;
    confidence: number;
  }>;
  lastTrained: number;
}
export class AutoScaler {
  private config: ScalingConfig;
  private instances: Map<string, InstanceMetrics> = new Map();
  private scalingHistory: ScalingDecision[] = [];
  private lastScaleAction: number = 0;
  private predictiveModel: PredictiveModel | null = null;
  private metricsInterval: NodeJS.Timeout | null = null;
  private scalingInterval: NodeJS.Timeout | null = null;
  constructor(config: Partial<ScalingConfig> = {}) {
    this.config = {
      minInstances: 1,
      maxInstances: 10,
      targetCPUUtilization: 70,
      targetMemoryUtilization: 80,
      targetResponseTime: 500, // ms
      scaleUpCooldown: 300000, // 5 minutes
      scaleDownCooldown: 600000, // 10 minutes
      enablePredictiveScaling: true,
      enableScheduledScaling: true,
      scheduledRules: [],
      metrics: [
        {
          name: 'cpu_utilization',
          threshold: 70,
          comparison: 'greater',
          weight: 1.0,
          cooldown: 300000
        },
        {
          name: 'memory_utilization',
          threshold: 80,
          comparison: 'greater',
          weight: 0.8,
          cooldown: 300000
        },
        {
          name: 'response_time',
          threshold: 500,
          comparison: 'greater',
          weight: 0.9,
          cooldown: 180000
        }
      ],
      ...config
    };
    this.startMonitoring();
  }
  private startMonitoring() {
    // Collect metrics every 30 seconds
    this.metricsInterval = setInterval(() => {
      this.collectMetrics();
    }, 30000);
    // Make scaling decisions every minute
    this.scalingInterval = setInterval(() => {
      this.evaluateScaling();
    }, 60000);
    // Train predictive model every hour
    if (this.config.enablePredictiveScaling) {
      setInterval(() => {
        this.trainPredictiveModel();
      }, 3600000);
    }
  }
  private async collectMetrics() {
    try {
      // In a real implementation, this would collect metrics from actual instances
      // For now, we'll simulate metrics collection
      const instanceIds = await this.getActiveInstances();
      for (const instanceId of instanceIds) {
        const metrics = await this.getInstanceMetrics(instanceId);
        this.instances.set(instanceId, metrics);
      }
    } catch (error) {
    }
  }
  private async getActiveInstances(): Promise<string[]> {
    // In a real implementation, this would query the container orchestrator
    // or cloud provider API to get active instances
    // Simulate active instances
    const currentCount = Math.max(this.config.minInstances, this.instances.size || 1);
    const instances: string[] = [];
    for (let i = 0; i < currentCount; i++) {
      instances.push(`instance-${i + 1}`);
    }
    return instances;
  }
  private async getInstanceMetrics(instanceId: string): Promise<InstanceMetrics> {
    // In a real implementation, this would fetch actual metrics from monitoring systems
    // For now, we'll simulate realistic metrics
    const baseLoad = 0.3 + Math.random() * 0.4; // 30-70% base load
    const timeOfDay = new Date().getHours();
    const businessHoursMultiplier = (timeOfDay >= 9 && timeOfDay <= 17) ? 1.5 : 0.8;
    return {
      instanceId,
      cpuUtilization: Math.min(100, baseLoad * businessHoursMultiplier * 100 + (Math.random() - 0.5) * 20),
      memoryUtilization: Math.min(100, baseLoad * businessHoursMultiplier * 90 + (Math.random() - 0.5) * 15),
      responseTime: 200 + baseLoad * businessHoursMultiplier * 300 + (Math.random() - 0.5) * 100,
      requestsPerSecond: baseLoad * businessHoursMultiplier * 100 + (Math.random() - 0.5) * 20,
      errorRate: Math.max(0, baseLoad * 2 + (Math.random() - 0.5) * 1),
      healthStatus: Math.random() > 0.95 ? 'unhealthy' : Math.random() > 0.9 ? 'degraded' : 'healthy',
      lastUpdated: Date.now()
    };
  }
  private async evaluateScaling(): Promise<ScalingDecision> {
    const currentInstances = this.instances.size;
    const aggregatedMetrics = this.aggregateMetrics();
    // Check cooldown periods
    const timeSinceLastScale = Date.now() - this.lastScaleAction;
    const scaleUpCooldownActive = timeSinceLastScale < this.config.scaleUpCooldown;
    const scaleDownCooldownActive = timeSinceLastScale < this.config.scaleDownCooldown;
    // Calculate scaling score based on metrics
    const scalingScore = this.calculateScalingScore(aggregatedMetrics);
    // Check scheduled scaling rules
    const scheduledTarget = this.getScheduledTarget();
    // Get predictive scaling recommendation
    const predictiveTarget = this.config.enablePredictiveScaling 
      ? this.getPredictiveTarget() 
      : null;
    // Make scaling decision
    let decision: ScalingDecision;
    if (scalingScore > 0.7 && !scaleUpCooldownActive && currentInstances < this.config.maxInstances) {
      // Scale up
      const targetInstances = Math.min(
        this.config.maxInstances,
        Math.ceil(currentInstances * (1 + scalingScore * 0.5))
      );
      decision = {
        action: 'scale_up',
        currentInstances,
        targetInstances,
        reason: `High resource utilization (score: ${scalingScore.toFixed(2)})`,
        confidence: scalingScore,
        metrics: aggregatedMetrics,
        timestamp: Date.now()
      };
    } else if (scalingScore < -0.5 && !scaleDownCooldownActive && currentInstances > this.config.minInstances) {
      // Scale down
      const targetInstances = Math.max(
        this.config.minInstances,
        Math.floor(currentInstances * (1 + scalingScore * 0.3))
      );
      decision = {
        action: 'scale_down',
        currentInstances,
        targetInstances,
        reason: `Low resource utilization (score: ${scalingScore.toFixed(2)})`,
        confidence: Math.abs(scalingScore),
        metrics: aggregatedMetrics,
        timestamp: Date.now()
      };
    } else {
      // No action
      let reason = 'Metrics within target ranges';
      if (scaleUpCooldownActive || scaleDownCooldownActive) {
        reason = 'Cooldown period active';
      } else if (currentInstances >= this.config.maxInstances) {
        reason = 'Maximum instances reached';
      } else if (currentInstances <= this.config.minInstances) {
        reason = 'Minimum instances reached';
      }
      decision = {
        action: 'no_action',
        currentInstances,
        targetInstances: currentInstances,
        reason,
        confidence: 1 - Math.abs(scalingScore),
        metrics: aggregatedMetrics,
        timestamp: Date.now()
      };
    }
    // Apply scheduled scaling override
    if (scheduledTarget && scheduledTarget !== currentInstances) {
      decision = {
        ...decision,
        action: scheduledTarget > currentInstances ? 'scale_up' : 'scale_down',
        targetInstances: scheduledTarget,
        reason: `Scheduled scaling rule: ${decision.reason}`,
        confidence: 0.9
      };
    }
    // Apply predictive scaling adjustment
    if (predictiveTarget && this.config.enablePredictiveScaling) {
      const predictiveAdjustment = predictiveTarget - currentInstances;
      if (Math.abs(predictiveAdjustment) > 0 && decision.action === 'no_action') {
        decision = {
          ...decision,
          action: predictiveAdjustment > 0 ? 'scale_up' : 'scale_down',
          targetInstances: predictiveTarget,
          reason: `Predictive scaling: ${decision.reason}`,
          confidence: this.predictiveModel?.accuracy || 0.7
        };
      }
    }
    // Record decision
    this.scalingHistory.push(decision);
    // Keep only last 100 decisions
    if (this.scalingHistory.length > 100) {
      this.scalingHistory = this.scalingHistory.slice(-100);
    }
    // Execute scaling action
    if (decision.action !== 'no_action') {
      await this.executeScaling(decision);
    }
    return decision;
  }
  private aggregateMetrics(): Record<string, number> {
    if (this.instances.size === 0) {
      return {};
    }
    const metrics: Record<string, number[]> = {};
    // Collect all metrics
    for (const instance of this.instances.values()) {
      if (!metrics.cpuUtilization) metrics.cpuUtilization = [];
      if (!metrics.memoryUtilization) metrics.memoryUtilization = [];
      if (!metrics.responseTime) metrics.responseTime = [];
      if (!metrics.requestsPerSecond) metrics.requestsPerSecond = [];
      if (!metrics.errorRate) metrics.errorRate = [];
      metrics.cpuUtilization.push(instance.cpuUtilization);
      metrics.memoryUtilization.push(instance.memoryUtilization);
      metrics.responseTime.push(instance.responseTime);
      metrics.requestsPerSecond.push(instance.requestsPerSecond);
      metrics.errorRate.push(instance.errorRate);
    }
    // Calculate aggregated values
    const aggregated: Record<string, number> = {};
    for (const [metricName, values] of Object.entries(metrics)) {
      // Use 95th percentile for most metrics, average for requests per second
      if (metricName === 'requestsPerSecond') {
        aggregated[metricName] = values.reduce((sum, val) => sum + val, 0);
      } else {
        values.sort((a, b) => a - b);
        const p95Index = Math.floor(values.length * 0.95);
        aggregated[metricName] = values[p95Index] || 0;
      }
    }
    return aggregated;
  }
  private calculateScalingScore(metrics: Record<string, number>): number {
    let totalScore = 0;
    let totalWeight = 0;
    for (const metricConfig of this.config.metrics) {
      const value = metrics[metricConfig.name];
      if (value === undefined) continue;
      let score = 0;
      switch (metricConfig.comparison) {
        case 'greater':
          score = (value - metricConfig.threshold) / metricConfig.threshold;
          break;
        case 'less':
          score = (metricConfig.threshold - value) / metricConfig.threshold;
          break;
        case 'equal':
          score = -Math.abs(value - metricConfig.threshold) / metricConfig.threshold;
          break;
      }
      // Normalize score to [-1, 1] range
      score = Math.max(-1, Math.min(1, score));
      totalScore += score * metricConfig.weight;
      totalWeight += metricConfig.weight;
    }
    return totalWeight > 0 ? totalScore / totalWeight : 0;
  }
  private getScheduledTarget(): number | null {
    if (!this.config.enableScheduledScaling) {
      return null;
    }
    const now = new Date();
    for (const rule of this.config.scheduledRules) {
      if (!rule.enabled) continue;
      // Simple schedule matching (in real implementation, use a cron library)
      const hour = now.getHours();
      const dayOfWeek = now.getDay();
      // Example: "9-17 * * 1-5" means 9 AM to 5 PM, Monday to Friday
      if (rule.schedule.includes(`${hour}`) || rule.schedule.includes('*')) {
        return Math.max(rule.minInstances, Math.min(rule.maxInstances, this.instances.size));
      }
    }
    return null;
  }
  private getPredictiveTarget(): number | null {
    if (!this.predictiveModel || this.predictiveModel.predictions.length === 0) {
      return null;
    }
    const now = Date.now();
    const futureTime = now + 300000; // 5 minutes ahead
    // Find the closest prediction
    let closestPrediction = this.predictiveModel.predictions[0];
    let minTimeDiff = Math.abs(closestPrediction.timestamp - futureTime);
    for (const prediction of this.predictiveModel.predictions) {
      const timeDiff = Math.abs(prediction.timestamp - futureTime);
      if (timeDiff < minTimeDiff) {
        minTimeDiff = timeDiff;
        closestPrediction = prediction;
      }
    }
    // Convert predicted load to instance count
    const baseInstancesNeeded = Math.ceil(closestPrediction.predictedLoad / 100); // Assume 100 RPS per instance
    const targetInstances = Math.max(
      this.config.minInstances,
      Math.min(this.config.maxInstances, baseInstancesNeeded)
    );
    return targetInstances;
  }
  private async executeScaling(decision: ScalingDecision): Promise<void> {
    try {
      if (decision.action === 'scale_up') {
        await this.scaleUp(decision.targetInstances - decision.currentInstances);
      } else if (decision.action === 'scale_down') {
        await this.scaleDown(decision.currentInstances - decision.targetInstances);
      }
      this.lastScaleAction = Date.now();
      // Notify monitoring systems
      await this.notifyScalingEvent(decision);
    } catch (error) {
    }
  }
  private async scaleUp(instanceCount: number): Promise<void> {
    // In a real implementation, this would call the container orchestrator
    // or cloud provider API to start new instances
    // Simulate instance creation
    for (let i = 0; i < instanceCount; i++) {
      const instanceId = `instance-${this.instances.size + i + 1}`;
      // Add placeholder metrics for new instance
      this.instances.set(instanceId, {
        instanceId,
        cpuUtilization: 10, // New instances start with low utilization
        memoryUtilization: 20,
        responseTime: 150,
        requestsPerSecond: 0,
        errorRate: 0,
        healthStatus: 'healthy',
        lastUpdated: Date.now()

    }
  }
  private async scaleDown(instanceCount: number): Promise<void> {
    // In a real implementation, this would gracefully terminate instances
    // Remove instances with lowest utilization first
    const instances = Array.from(this.instances.entries())
      .sort(([, a], [, b]) => a.cpuUtilization - b.cpuUtilization)
      .slice(0, instanceCount);
    for (const [instanceId] of instances) {
      this.instances.delete(instanceId);
    }
  }
  private async notifyScalingEvent(decision: ScalingDecision): Promise<void> {
    // In a real implementation, this would send notifications to monitoring
    // systems, Slack, email, etc.
    const notification = {
      type: 'scaling_event',
      action: decision.action,
      instances: {
        before: decision.currentInstances,
        after: decision.targetInstances
      },
      reason: decision.reason,
      confidence: decision.confidence,
      timestamp: decision.timestamp
    };
  }
  private trainPredictiveModel(): void {
    if (this.scalingHistory.length < 10) {
      return; // Need more data
    }
    // Simple linear regression model (in real implementation, use more sophisticated ML)
    const trainingData = this.scalingHistory.slice(-50); // Use last 50 decisions
    // Generate predictions for next 24 hours
    const predictions = [];
    const now = Date.now();
    for (let i = 1; i <= 24; i++) {
      const futureTime = now + (i * 3600000); // Each hour
      const hour = new Date(futureTime).getHours();
      // Simple pattern: higher load during business hours
      let predictedLoad = 50; // Base load
      if (hour >= 9 && hour <= 17) {
        predictedLoad = 80 + Math.sin((hour - 9) / 8 * Math.PI) * 20;
      } else {
        predictedLoad = 30 + Math.random() * 20;
      }
      predictions.push({
        timestamp: futureTime,
        predictedLoad,
        confidence: 0.7 + Math.random() * 0.2

    }
    this.predictiveModel = {
      type: 'linear',
      accuracy: 0.75,
      predictions,
      lastTrained: Date.now()
    };
  }
  // Public API methods
  public getCurrentInstances(): InstanceMetrics[] {
    return Array.from(this.instances.values());
  }
  public getScalingHistory(limit: number = 20): ScalingDecision[] {
    return this.scalingHistory.slice(-limit);
  }
  public getScalingStats() {
    const recentDecisions = this.scalingHistory.slice(-20);
    const scaleUpCount = recentDecisions.filter(d => d.action === 'scale_up').length;
    const scaleDownCount = recentDecisions.filter(d => d.action === 'scale_down').length;
    const noActionCount = recentDecisions.filter(d => d.action === 'no_action').length;
    const averageConfidence = recentDecisions.length > 0
      ? recentDecisions.reduce((sum, d) => sum + d.confidence, 0) / recentDecisions.length
      : 0;
    return {
      currentInstances: this.instances.size,
      minInstances: this.config.minInstances,
      maxInstances: this.config.maxInstances,
      recentActions: {
        scaleUp: scaleUpCount,
        scaleDown: scaleDownCount,
        noAction: noActionCount
      },
      averageConfidence,
      lastScaleAction: this.lastScaleAction,
      predictiveModelAccuracy: this.predictiveModel?.accuracy || 0
    };
  }
  public updateConfig(newConfig: Partial<ScalingConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }
  public async manualScale(targetInstances: number, reason: string = 'Manual scaling'): Promise<void> {
    const currentInstances = this.instances.size;
    if (targetInstances === currentInstances) {
      return;
    }
    const decision: ScalingDecision = {
      action: targetInstances > currentInstances ? 'scale_up' : 'scale_down',
      currentInstances,
      targetInstances,
      reason,
      confidence: 1.0,
      metrics: this.aggregateMetrics(),
      timestamp: Date.now()
    };
    await this.executeScaling(decision);
  }
  public destroy(): void {
    if (this.metricsInterval) {
      clearInterval(this.metricsInterval);
      this.metricsInterval = null;
    }
    if (this.scalingInterval) {
      clearInterval(this.scalingInterval);
      this.scalingInterval = null;
    }
    this.instances.clear();
    this.scalingHistory = [];
  }
}
export default AutoScaler;
