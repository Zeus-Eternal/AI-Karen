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
  timezone?: string;
}

export interface ScalingMetric {
  name: string;
  threshold: number;
  comparison: 'greater' | 'less' | 'equal';
  weight: number;
  cooldown: number;
  enabled: boolean;
}

export interface ScalingDecision {
  action: 'scale_up' | 'scale_down' | 'no_action';
  currentInstances: number;
  targetInstances: number;
  reason: string;
  confidence: number;
  metrics: Record<string, number>;
  timestamp: number;
  cooldownRemaining?: number;
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
  startupTime?: number;
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
  trainingDataSize: number;
}

export interface ScalingStats {
  currentInstances: number;
  minInstances: number;
  maxInstances: number;
  recentActions: {
    scaleUp: number;
    scaleDown: number;
    noAction: number;
  };
  averageConfidence: number;
  lastScaleAction: number;
  predictiveModelAccuracy: number;
  averageResponseTime: number;
  averageCPUUtilization: number;
  healthStatus: {
    healthy: number;
    degraded: number;
    unhealthy: number;
  };
}

export class AutoScalerError extends Error {
  constructor(
    message: string,
    public operation: string,
    public originalError?: unknown
  ) {
    super(message);
    this.name = 'AutoScalerError';
  }
}

export class AutoScaler {
  private config: ScalingConfig;
  private instances: Map<string, InstanceMetrics> = new Map();
  private scalingHistory: ScalingDecision[] = [];
  private lastScaleAction: number = 0;
  private predictiveModel: PredictiveModel | null = null;
  private metricsInterval: NodeJS.Timeout | null = null;
  private scalingInterval: NodeJS.Timeout | null = null;
  private isMonitoring: boolean = false;
  private readonly MAX_HISTORY_SIZE = 1000;
  private readonly MIN_TRAINING_DATA_SIZE = 10;

  constructor(config: Partial<ScalingConfig> = {}) {
    this.config = this.validateConfig({
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
          cooldown: 300000,
          enabled: true
        },
        {
          name: 'memory_utilization',
          threshold: 80,
          comparison: 'greater',
          weight: 0.8,
          cooldown: 300000,
          enabled: true
        },
        {
          name: 'response_time',
          threshold: 500,
          comparison: 'greater',
          weight: 0.9,
          cooldown: 180000,
          enabled: true
        },
        {
          name: 'error_rate',
          threshold: 5,
          comparison: 'greater',
          weight: 1.2,
          cooldown: 120000,
          enabled: true
        }
      ],
      ...config
    });

    this.startMonitoring();
  }

  private validateConfig(config: ScalingConfig): ScalingConfig {
    // Validate instance limits
    if (config.minInstances < 0) {
      throw new AutoScalerError('minInstances must be non-negative', 'validateConfig');
    }
    if (config.maxInstances <= 0) {
      throw new AutoScalerError('maxInstances must be positive', 'validateConfig');
    }
    if (config.minInstances > config.maxInstances) {
      throw new AutoScalerError('minInstances cannot exceed maxInstances', 'validateConfig');
    }

    // Validate utilization thresholds
    if (config.targetCPUUtilization <= 0 || config.targetCPUUtilization > 100) {
      throw new AutoScalerError('targetCPUUtilization must be between 1 and 100', 'validateConfig');
    }
    if (config.targetMemoryUtilization <= 0 || config.targetMemoryUtilization > 100) {
      throw new AutoScalerError('targetMemoryUtilization must be between 1 and 100', 'validateConfig');
    }

    // Validate cooldown periods
    if (config.scaleUpCooldown < 0 || config.scaleDownCooldown < 0) {
      throw new AutoScalerError('Cooldown periods must be non-negative', 'validateConfig');
    }

    // Validate metrics
    for (const metric of config.metrics) {
      if (metric.weight < 0) {
        throw new AutoScalerError(`Metric ${metric.name} weight must be non-negative`, 'validateConfig');
      }
      if (metric.cooldown < 0) {
        throw new AutoScalerError(`Metric ${metric.name} cooldown must be non-negative`, 'validateConfig');
      }
    }

    return config;
  }

  private startMonitoring(): void {
    if (this.isMonitoring) {
      return;
    }

    this.isMonitoring = true;

    // Collect metrics every 30 seconds
    this.metricsInterval = setInterval(() => {
      this.collectMetrics().catch(error => {
        console.error('Metrics collection error:', error);
      });
    }, 30000);

    // Make scaling decisions every minute
    this.scalingInterval = setInterval(() => {
      this.evaluateScaling().catch(error => {
        console.error('Scaling evaluation error:', error);
      });
    }, 60000);

    // Train predictive model every hour if enabled
    if (this.config.enablePredictiveScaling) {
      setInterval(() => {
        this.trainPredictiveModel().catch(error => {
          console.error('Predictive model training error:', error);
        });
      }, 3600000);
    }

    // Initial metrics collection
    this.collectMetrics().catch(error => {
      console.error('Initial metrics collection error:', error);
    });
  }

  private async collectMetrics(): Promise<void> {
    try {
      const instanceIds = await this.getActiveInstances();
      const metricsPromises = instanceIds.map(instanceId => 
        this.getInstanceMetrics(instanceId)
      );
      
      const metricsResults = await Promise.allSettled(metricsPromises);
      
      for (const result of metricsResults) {
        if (result.status === 'fulfilled') {
          this.instances.set(result.value.instanceId, result.value);
        } else {
          console.error('Failed to collect metrics for instance:', result.reason);
        }
      }

      // Remove instances that are no longer active
      const activeInstanceIds = new Set(instanceIds);
      for (const instanceId of this.instances.keys()) {
        if (!activeInstanceIds.has(instanceId)) {
          this.instances.delete(instanceId);
        }
      }
    } catch (error) {
      throw new AutoScalerError(
        'Failed to collect metrics',
        'collectMetrics',
        error
      );
    }
  }

  private async getActiveInstances(): Promise<string[]> {
    try {
      // In a real implementation, this would query the container orchestrator
      // or cloud provider API to get active instances
      // For simulation, maintain at least minInstances
      const currentCount = Math.max(
        this.config.minInstances, 
        Math.min(this.config.maxInstances, this.instances.size || this.config.minInstances)
      );
      
      const instances: string[] = [];
      for (let i = 0; i < currentCount; i++) {
        instances.push(`instance-${i + 1}`);
      }
      return instances;
    } catch (error) {
      throw new AutoScalerError(
        'Failed to get active instances',
        'getActiveInstances',
        error
      );
    }
  }

  private async getInstanceMetrics(instanceId: string): Promise<InstanceMetrics> {
    try {
      // In a real implementation, this would fetch actual metrics from monitoring systems
      // For now, simulate realistic metrics with more sophisticated patterns
      
      const baseLoad = 0.3 + Math.random() * 0.4; // 30-70% base load
      const now = new Date();
      const timeOfDay = now.getHours();
      const dayOfWeek = now.getDay();
      
      // Business hours multiplier (higher during business hours)
      const isBusinessHours = timeOfDay >= 9 && timeOfDay <= 17 && dayOfWeek >= 1 && dayOfWeek <= 5;
      const businessHoursMultiplier = isBusinessHours ? 1.5 : 0.8;
      
      // Weekend effect
      const weekendMultiplier = (dayOfWeek === 0 || dayOfWeek === 6) ? 0.7 : 1.0;
      
      // Random noise and spikes
      const noise = (Math.random() - 0.5) * 0.2;
      const spikeChance = Math.random();
      const spikeMultiplier = spikeChance > 0.95 ? 2.0 : 1.0;
      
      const loadFactor = baseLoad * businessHoursMultiplier * weekendMultiplier * spikeMultiplier + noise;

      return {
        instanceId,
        cpuUtilization: Math.min(100, Math.max(0, loadFactor * 100)),
        memoryUtilization: Math.min(100, Math.max(0, loadFactor * 90 + (Math.random() - 0.5) * 10)),
        responseTime: Math.max(50, 100 + loadFactor * 400 + (Math.random() - 0.5) * 50),
        requestsPerSecond: Math.max(0, loadFactor * 150 + (Math.random() - 0.5) * 20),
        errorRate: Math.max(0, Math.min(10, loadFactor * 3 + (Math.random() - 0.5) * 2)),
        healthStatus: this.calculateHealthStatus(loadFactor, spikeChance),
        lastUpdated: Date.now(),
        startupTime: this.instances.get(instanceId)?.startupTime || Date.now()
      };
    } catch (error) {
      throw new AutoScalerError(
        `Failed to get metrics for instance ${instanceId}`,
        'getInstanceMetrics',
        error
      );
    }
  }

  private calculateHealthStatus(loadFactor: number, spikeChance: number): 'healthy' | 'unhealthy' | 'degraded' {
    if (spikeChance > 0.98 || loadFactor > 0.9) {
      return 'unhealthy';
    } else if (spikeChance > 0.9 || loadFactor > 0.7) {
      return 'degraded';
    } else {
      return 'healthy';
    }
  }

  private async evaluateScaling(): Promise<ScalingDecision> {
    try {
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

      // Make initial scaling decision
      let decision = this.makeScalingDecision(
        currentInstances,
        scalingScore,
        scaleUpCooldownActive,
        scaleDownCooldownActive,
        aggregatedMetrics
      );

      // Apply scheduled scaling override
      if (scheduledTarget !== null && scheduledTarget !== currentInstances) {
        decision = this.applyScheduledScaling(decision, scheduledTarget, currentInstances);
      }

      // Apply predictive scaling adjustment
      if (predictiveTarget !== null && this.config.enablePredictiveScaling) {
        decision = this.applyPredictiveScaling(decision, predictiveTarget, currentInstances);
      }

      // Record decision
      this.recordDecision(decision);

      // Execute scaling action if needed
      if (decision.action !== 'no_action') {
        await this.executeScaling(decision);
      }

      return decision;
    } catch (error) {
      throw new AutoScalerError(
        'Failed to evaluate scaling',
        'evaluateScaling',
        error
      );
    }
  }

  private makeScalingDecision(
    currentInstances: number,
    scalingScore: number,
    scaleUpCooldownActive: boolean,
    scaleDownCooldownActive: boolean,
    metrics: Record<string, number>
  ): ScalingDecision {
    let action: 'scale_up' | 'scale_down' | 'no_action' = 'no_action';
    let targetInstances = currentInstances;
    let reason = 'Metrics within target ranges';
    let confidence = 1 - Math.abs(scalingScore);

    if (scalingScore > 0.7 && !scaleUpCooldownActive && currentInstances < this.config.maxInstances) {
      // Scale up
      action = 'scale_up';
      targetInstances = Math.min(
        this.config.maxInstances,
        Math.ceil(currentInstances * (1 + scalingScore * 0.5))
      );
      reason = `High resource utilization (score: ${scalingScore.toFixed(2)})`;
      confidence = scalingScore;
    } else if (scalingScore < -0.5 && !scaleDownCooldownActive && currentInstances > this.config.minInstances) {
      // Scale down
      action = 'scale_down';
      targetInstances = Math.max(
        this.config.minInstances,
        Math.floor(currentInstances * (1 + scalingScore * 0.3))
      );
      reason = `Low resource utilization (score: ${scalingScore.toFixed(2)})`;
      confidence = Math.abs(scalingScore);
    } else {
      // Handle edge cases
      if (scaleUpCooldownActive || scaleDownCooldownActive) {
        reason = 'Cooldown period active';
        const cooldownRemaining = scaleUpCooldownActive 
          ? this.config.scaleUpCooldown - (Date.now() - this.lastScaleAction)
          : this.config.scaleDownCooldown - (Date.now() - this.lastScaleAction);
        
        return {
          action,
          currentInstances,
          targetInstances,
          reason,
          confidence,
          metrics,
          timestamp: Date.now(),
          cooldownRemaining
        };
      } else if (currentInstances >= this.config.maxInstances) {
        reason = 'Maximum instances reached';
      } else if (currentInstances <= this.config.minInstances) {
        reason = 'Minimum instances reached';
      }
    }

    return {
      action,
      currentInstances,
      targetInstances,
      reason,
      confidence,
      metrics,
      timestamp: Date.now()
    };
  }

  private applyScheduledScaling(
    decision: ScalingDecision,
    scheduledTarget: number,
    currentInstances: number
  ): ScalingDecision {
    return {
      ...decision,
      action: scheduledTarget > currentInstances ? 'scale_up' : 'scale_down',
      targetInstances: scheduledTarget,
      reason: `Scheduled scaling rule: ${decision.reason}`,
      confidence: Math.max(decision.confidence, 0.9)
    };
  }

  private applyPredictiveScaling(
    decision: ScalingDecision,
    predictiveTarget: number,
    currentInstances: number
  ): ScalingDecision {
    const predictiveAdjustment = predictiveTarget - currentInstances;
    
    if (Math.abs(predictiveAdjustment) > 0 && decision.action === 'no_action') {
      return {
        ...decision,
        action: predictiveAdjustment > 0 ? 'scale_up' : 'scale_down',
        targetInstances: predictiveTarget,
        reason: `Predictive scaling: ${decision.reason}`,
        confidence: this.predictiveModel?.accuracy || 0.7
      };
    }
    
    return decision;
  }

  private recordDecision(decision: ScalingDecision): void {
    this.scalingHistory.push(decision);
    
    // Keep history within limits
    if (this.scalingHistory.length > this.MAX_HISTORY_SIZE) {
      this.scalingHistory = this.scalingHistory.slice(-this.MAX_HISTORY_SIZE);
    }
  }

  private aggregateMetrics(): Record<string, number> {
    if (this.instances.size === 0) {
      return {};
    }

    const healthyInstances = Array.from(this.instances.values())
      .filter(instance => instance.healthStatus === 'healthy');

    if (healthyInstances.length === 0) {
      return {};
    }

    const metrics: Record<string, number[]> = {
      cpuUtilization: [],
      memoryUtilization: [],
      responseTime: [],
      requestsPerSecond: [],
      errorRate: []
    };

    // Collect metrics from healthy instances only
    for (const instance of healthyInstances) {
      metrics.cpuUtilization.push(instance.cpuUtilization);
      metrics.memoryUtilization.push(instance.memoryUtilization);
      metrics.responseTime.push(instance.responseTime);
      metrics.requestsPerSecond.push(instance.requestsPerSecond);
      metrics.errorRate.push(instance.errorRate);
    }

    // Calculate aggregated values with different strategies
    const aggregated: Record<string, number> = {};
    
    // For utilization metrics, use 95th percentile to handle spikes
    aggregated.cpuUtilization = this.calculatePercentile(metrics.cpuUtilization, 95);
    aggregated.memoryUtilization = this.calculatePercentile(metrics.memoryUtilization, 95);
    
    // For response time, use 95th percentile
    aggregated.responseTime = this.calculatePercentile(metrics.responseTime, 95);
    
    // For requests, use sum across all instances
    aggregated.requestsPerSecond = metrics.requestsPerSecond.reduce((sum, val) => sum + val, 0);
    
    // For error rate, use average
    aggregated.errorRate = metrics.errorRate.length > 0 
      ? metrics.errorRate.reduce((sum, val) => sum + val, 0) / metrics.errorRate.length
      : 0;

    return aggregated;
  }

  private calculatePercentile(values: number[], percentile: number): number {
    if (values.length === 0) return 0;
    
    const sorted = [...values].sort((a, b) => a - b);
    const index = Math.ceil((percentile / 100) * sorted.length) - 1;
    return sorted[Math.max(0, Math.min(index, sorted.length - 1))];
  }

  private calculateScalingScore(metrics: Record<string, number>): number {
    let totalScore = 0;
    let totalWeight = 0;

    for (const metricConfig of this.config.metrics) {
      if (!metricConfig.enabled) continue;
      
      const value = metrics[metricConfig.name];
      if (value === undefined) continue;

      let score = 0;
      const normalizedThreshold = metricConfig.threshold;

      switch (metricConfig.comparison) {
        case 'greater':
          score = (value - normalizedThreshold) / Math.max(normalizedThreshold, 1);
          break;
        case 'less':
          score = (normalizedThreshold - value) / Math.max(normalizedThreshold, 1);
          break;
        case 'equal':
          score = -Math.abs(value - normalizedThreshold) / Math.max(normalizedThreshold, 1);
          break;
      }

      // Apply non-linear scaling for more aggressive response to high values
      if (Math.abs(score) > 0.5) {
        score = score * 1.5;
      }

      // Normalize score to [-1, 1] range
      score = Math.max(-1, Math.min(1, score));
      totalScore += score * metricConfig.weight;
      totalWeight += metricConfig.weight;
    }

    return totalWeight > 0 ? totalScore / totalWeight : 0;
  }

  private getScheduledTarget(): number | null {
    if (!this.config.enableScheduledScaling || this.config.scheduledRules.length === 0) {
      return null;
    }

    const now = new Date();
    const currentHour = now.getHours();
    const currentDay = now.getDay(); // 0 = Sunday, 6 = Saturday

    for (const rule of this.config.scheduledRules) {
      if (!rule.enabled) continue;

      // Simple schedule matching - in production, use a proper cron parser
      // This is a simplified version for demonstration
      if (this.matchesSchedule(rule.schedule, currentHour, currentDay)) {
        return Math.max(
          rule.minInstances, 
          Math.min(rule.maxInstances, this.config.maxInstances)
        );
      }
    }

    return null;
  }

  private matchesSchedule(schedule: string, currentHour: number, currentDay: number): boolean {
    // Very basic cron matching for demonstration
    // In production, use a library like 'cron-parser'
    try {
      const parts = schedule.split(' ');
      if (parts.length >= 5) {
        const [minute, hour, dayOfMonth, month, dayOfWeek] = parts;
        
        // Check hour and day of week (simplified)
        const hourMatch = hour === '*' || parseInt(hour) === currentHour;
        const dayMatch = dayOfWeek === '*' || parseInt(dayOfWeek) === currentDay;
        
        return hourMatch && dayMatch;
      }
    } catch (error) {
      console.error('Error parsing schedule:', schedule, error);
    }
    
    return false;
  }

  private getPredictiveTarget(): number | null {
    if (!this.predictiveModel || this.predictiveModel.predictions.length === 0) {
      return null;
    }

    const now = Date.now();
    const predictionWindow = 300000; // 5 minutes ahead

    // Find predictions within the relevant time window
    const relevantPredictions = this.predictiveModel.predictions.filter(
      p => p.timestamp >= now && p.timestamp <= now + predictionWindow
    );

    if (relevantPredictions.length === 0) {
      return null;
    }

    // Use weighted average of predictions based on confidence
    let totalLoad = 0;
    let totalConfidence = 0;

    for (const prediction of relevantPredictions) {
      totalLoad += prediction.predictedLoad * prediction.confidence;
      totalConfidence += prediction.confidence;
    }

    const averagePredictedLoad = totalConfidence > 0 ? totalLoad / totalConfidence : 0;

    // Convert predicted load to instance count (assuming 100 RPS per instance capacity)
    const baseInstancesNeeded = Math.ceil(averagePredictedLoad / 100);
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
      await this.notifyScalingEvent(decision);
    } catch (error) {
      throw new AutoScalerError(
        `Failed to execute scaling action: ${decision.action}`,
        'executeScaling',
        error
      );
    }
  }

  private async scaleUp(instanceCount: number): Promise<void> {
    try {
      // In a real implementation, this would call cloud provider APIs
      for (let i = 0; i < instanceCount; i++) {
        const instanceId = `instance-${Date.now()}-${i}`;
        const newInstance: InstanceMetrics = {
          instanceId,
          cpuUtilization: 5, // New instances start with low utilization
          memoryUtilization: 15,
          responseTime: 100,
          requestsPerSecond: 0,
          errorRate: 0,
          healthStatus: 'healthy',
          lastUpdated: Date.now(),
          startupTime: Date.now()
        };
        this.instances.set(instanceId, newInstance);
      }
    } catch (error) {
      throw new AutoScalerError(
        `Failed to scale up by ${instanceCount} instances`,
        'scaleUp',
        error
      );
    }
  }

  private async scaleDown(instanceCount: number): Promise<void> {
    try {
      // Remove instances with lowest utilization and newest first
      const instancesToRemove = Array.from(this.instances.entries())
        .sort(([, a], [, b]) => {
          // Prefer to remove instances with lower utilization and newer instances
          const scoreA = a.cpuUtilization * 0.6 + (a.startupTime ? Date.now() - a.startupTime : 0) * 0.4;
          const scoreB = b.cpuUtilization * 0.6 + (b.startupTime ? Date.now() - b.startupTime : 0) * 0.4;
          return scoreA - scoreB;
        })
        .slice(0, instanceCount);

      for (const [instanceId] of instancesToRemove) {
        this.instances.delete(instanceId);
      }
    } catch (error) {
      throw new AutoScalerError(
        `Failed to scale down by ${instanceCount} instances`,
        'scaleDown',
        error
      );
    }
  }

  private async notifyScalingEvent(decision: ScalingDecision): Promise<void> {
    try {
      // In real implementation, send to monitoring systems, Slack, etc.
      const event = {
        type: 'scaling_event',
        action: decision.action,
        instances: {
          before: decision.currentInstances,
          after: decision.targetInstances
        },
        reason: decision.reason,
        confidence: decision.confidence,
        timestamp: decision.timestamp,
        metrics: decision.metrics
      };
      
      // Simulate async notification
      await Promise.resolve();
    } catch (error) {
      console.error('Failed to notify scaling event:', error);
      // Don't fail scaling if notification fails
    }
  }

  private async trainPredictiveModel(): Promise<void> {
    if (this.scalingHistory.length < this.MIN_TRAINING_DATA_SIZE) {
      return; // Need more data
    }

    try {
      // Use recent history for training
      const trainingData = this.scalingHistory.slice(-100);
      
      // Generate predictions for next 24 hours in 1-hour intervals
      const predictions: PredictiveModel['predictions'] = [];
      const now = Date.now();
      
      for (let i = 1; i <= 24; i++) {
        const futureTime = now + (i * 3600000);
        const hour = new Date(futureTime).getHours();
        const dayOfWeek = new Date(futureTime).getDay();
        
        // Enhanced prediction model considering time patterns
        let predictedLoad = 50; // Base load
        
        // Business hours pattern
        if (hour >= 9 && hour <= 17 && dayOfWeek >= 1 && dayOfWeek <= 5) {
          predictedLoad = 80 + Math.sin((hour - 9) / 8 * Math.PI) * 20;
        } else if (dayOfWeek === 0 || dayOfWeek === 6) {
          // Weekend pattern
          predictedLoad = 30 + Math.random() * 20;
        } else {
          // Evening pattern
          predictedLoad = 40 + Math.random() * 15;
        }
        
        // Add some randomness and trend from historical data
        const historicalTrend = this.calculateHistoricalTrend(hour);
        predictedLoad = predictedLoad * (1 + historicalTrend);
        
        predictions.push({
          timestamp: futureTime,
          predictedLoad: Math.max(10, Math.min(100, predictedLoad)),
          confidence: 0.7 + Math.random() * 0.2
        });
      }

      this.predictiveModel = {
        type: 'seasonal',
        accuracy: 0.75 + Math.random() * 0.15, // Simulated accuracy
        predictions,
        lastTrained: Date.now(),
        trainingDataSize: trainingData.length
      };
    } catch (error) {
      throw new AutoScalerError(
        'Failed to train predictive model',
        'trainPredictiveModel',
        error
      );
    }
  }

  private calculateHistoricalTrend(hour: number): number {
    // Simple trend calculation based on historical data
    // In production, use proper time series analysis
    const recentMetrics = this.scalingHistory.slice(-24);
    if (recentMetrics.length === 0) return 0;
    
    const hourMetrics = recentMetrics.filter(metric => {
      const metricHour = new Date(metric.timestamp).getHours();
      return metricHour === hour;
    });
    
    if (hourMetrics.length === 0) return 0;
    
    const averageLoad = hourMetrics.reduce((sum, metric) => 
      sum + (metric.metrics.requestsPerSecond || 0), 0) / hourMetrics.length;
    
    return (averageLoad - 50) / 100; // Normalized trend
  }

  // Public API methods
  public getCurrentInstances(): InstanceMetrics[] {
    return Array.from(this.instances.values());
  }

  public getScalingHistory(limit: number = 20): ScalingDecision[] {
    return this.scalingHistory.slice(-Math.min(limit, this.MAX_HISTORY_SIZE));
  }

  public getScalingStats(): ScalingStats {
    const recentDecisions = this.scalingHistory.slice(-20);
    const currentInstances = this.getCurrentInstances();
    
    const scaleUpCount = recentDecisions.filter(d => d.action === 'scale_up').length;
    const scaleDownCount = recentDecisions.filter(d => d.action === 'scale_down').length;
    const noActionCount = recentDecisions.filter(d => d.action === 'no_action').length;
    
    const averageConfidence = recentDecisions.length > 0
      ? recentDecisions.reduce((sum, d) => sum + d.confidence, 0) / recentDecisions.length
      : 0;

    const healthStatus = {
      healthy: currentInstances.filter(i => i.healthStatus === 'healthy').length,
      degraded: currentInstances.filter(i => i.healthStatus === 'degraded').length,
      unhealthy: currentInstances.filter(i => i.healthStatus === 'unhealthy').length
    };

    const averageResponseTime = currentInstances.length > 0
      ? currentInstances.reduce((sum, i) => sum + i.responseTime, 0) / currentInstances.length
      : 0;

    const averageCPUUtilization = currentInstances.length > 0
      ? currentInstances.reduce((sum, i) => sum + i.cpuUtilization, 0) / currentInstances.length
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
      predictiveModelAccuracy: this.predictiveModel?.accuracy || 0,
      averageResponseTime,
      averageCPUUtilization,
      healthStatus
    };
  }

  public updateConfig(newConfig: Partial<ScalingConfig>): void {
    try {
      const mergedConfig = { ...this.config, ...newConfig };
      this.config = this.validateConfig(mergedConfig);
    } catch (error) {
      throw new AutoScalerError(
        'Failed to update config',
        'updateConfig',
        error
      );
    }
  }

  public async manualScale(targetInstances: number, reason: string = 'Manual scaling'): Promise<void> {
    if (targetInstances < this.config.minInstances || targetInstances > this.config.maxInstances) {
      throw new AutoScalerError(
        `Target instances must be between ${this.config.minInstances} and ${this.config.maxInstances}`,
        'manualScale'
      );
    }

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

  public async emergencyScaleDown(): Promise<void> {
    // Emergency scale down to minimum instances
    await this.manualScale(this.config.minInstances, 'Emergency scale down');
  }

  public isHealthy(): boolean {
    const stats = this.getScalingStats();
    const unhealthyRatio = stats.healthStatus.unhealthy / stats.currentInstances;
    return unhealthyRatio < 0.3; // Consider healthy if less than 30% instances are unhealthy
  }

  public destroy(): void {
    this.isMonitoring = false;
    
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
    this.predictiveModel = null;
  }
}

export default AutoScaler;