/**
 * Metrics Collector
 * 
 * Comprehensive metrics collection system for application monitoring,
 * performance tracking, and business intelligence.
 */

export interface ApplicationMetrics {
  httpRequests: Record<string, {
    methods: Record<string, number>;
    statusCodes: Record<string, number>;
    totalRequests: number;
  }>;
  requestDurations: Record<string, {
    buckets: Record<number, number>;
    sum: number;
    count: number;
    total: number;
  }>;
  activeSessions: number;
  websocketConnections: number;
  featureUsage: Record<string, number>;
  pluginExecutions: Record<string, {
    success: number;
    failure: number;
    totalTime: number;
  }>;
  modelRequests: Record<string, number>;
  modelResponseTimes: Record<string, {
    buckets: Record<number, number>;
    sum: number;
    count: number;
    total: number;
  }>;
}

export interface SystemMetrics {
  healthChecks: Record<string, 'healthy' | 'unhealthy' | 'degraded'>;
  database: {
    activeConnections: number;
    idleConnections: number;
    failedConnections: number;
    queryDurations: Record<string, {
      buckets: Record<number, number>;
      sum: number;
      count: number;
      total: number;
    }>;
  };
  redis: {
    connections: number;
    failedConnections: number;
    memoryUsage: number;
    keyCount: number;
  };
  filesystem: {
    diskUsage: number;
    inodeUsage: number;
    readOperations: number;
    writeOperations: number;
  };
}

export interface BusinessMetrics {
  userSessions: number;
  conversions: number;
  bounces: number;
  rateLimitExceeded: number;
  failedLogins: Record<string, number>;
  evilModeActivations: number;
  subscriptions: {
    active: number;
    cancelled: number;
    upgraded: number;
    downgraded: number;
  };
  revenue: {
    total: number;
    recurring: number;
    oneTime: number;
  };
}

export class MetricsCollector {
  private applicationMetrics: ApplicationMetrics;
  private systemMetrics: SystemMetrics;
  private businessMetrics: BusinessMetrics;
  private metricsCollectionTimes: number[] = [];

  constructor() {
    this.applicationMetrics = this.initializeApplicationMetrics();
    this.systemMetrics = this.initializeSystemMetrics();
    this.businessMetrics = this.initializeBusinessMetrics();
    
    // Start periodic metrics collection
    this.startPeriodicCollection();
  }

  private initializeApplicationMetrics(): ApplicationMetrics {
    return {
      httpRequests: {},
      requestDurations: {},
      activeSessions: 0,
      websocketConnections: 0,
      featureUsage: {},
      pluginExecutions: {},
      modelRequests: {},
      modelResponseTimes: {}
    };
  }

  private initializeSystemMetrics(): SystemMetrics {
    return {
      healthChecks: {},
      database: {
        activeConnections: 0,
        idleConnections: 0,
        failedConnections: 0,
        queryDurations: {}
      },
      redis: {
        connections: 0,
        failedConnections: 0,
        memoryUsage: 0,
        keyCount: 0
      },
      filesystem: {
        diskUsage: 0,
        inodeUsage: 0,
        readOperations: 0,
        writeOperations: 0
      }
    };
  }

  private initializeBusinessMetrics(): BusinessMetrics {
    return {
      userSessions: 0,
      conversions: 0,
      bounces: 0,
      rateLimitExceeded: 0,
      failedLogins: {},
      evilModeActivations: 0,
      subscriptions: {
        active: 0,
        cancelled: 0,
        upgraded: 0,
        downgraded: 0
      },
      revenue: {
        total: 0,
        recurring: 0,
        oneTime: 0
      }
    };
  }

  private startPeriodicCollection() {
    // Collect system metrics every 30 seconds
    setInterval(() => {
      this.collectSystemMetrics();
    }, 30000);

    // Collect business metrics every 60 seconds
    setInterval(() => {
      this.collectBusinessMetrics();
    }, 60000);
  }

  // HTTP Request Tracking
  public recordHttpRequest(path: string, method: string, statusCode: number, duration: number) {
    // Initialize path if not exists
    if (!this.applicationMetrics.httpRequests[path]) {
      this.applicationMetrics.httpRequests[path] = {
        methods: {},
        statusCodes: {},
        totalRequests: 0
      };
    }

    const pathMetrics = this.applicationMetrics.httpRequests[path];
    
    // Track method
    pathMetrics.methods[method] = (pathMetrics.methods[method] || 0) + 1;
    
    // Track status code
    pathMetrics.statusCodes[statusCode.toString()] = (pathMetrics.statusCodes[statusCode.toString()] || 0) + 1;
    
    // Track total requests
    pathMetrics.totalRequests++;

    // Track request duration
    this.recordRequestDuration(path, duration);
  }

  private recordRequestDuration(path: string, duration: number) {
    if (!this.applicationMetrics.requestDurations[path]) {
      this.applicationMetrics.requestDurations[path] = {
        buckets: {},
        sum: 0,
        count: 0,
        total: 0
      };
    }

    const durationMetrics = this.applicationMetrics.requestDurations[path];
    
    // Update histogram buckets
    const buckets = [0.1, 0.25, 0.5, 1, 2.5, 5, 10];
    buckets.forEach(bucket => {
      if (duration <= bucket) {
        durationMetrics.buckets[bucket] = (durationMetrics.buckets[bucket] || 0) + 1;
      }
    });

    durationMetrics.sum += duration;
    durationMetrics.count++;
    durationMetrics.total++;
  }

  // Session Tracking
  public recordActiveSession() {
    this.applicationMetrics.activeSessions++;
  }

  public recordSessionEnd() {
    this.applicationMetrics.activeSessions = Math.max(0, this.applicationMetrics.activeSessions - 1);
  }

  // WebSocket Tracking
  public recordWebSocketConnection() {
    this.applicationMetrics.websocketConnections++;
  }

  public recordWebSocketDisconnection() {
    this.applicationMetrics.websocketConnections = Math.max(0, this.applicationMetrics.websocketConnections - 1);
  }

  // Feature Usage Tracking
  public recordFeatureUsage(feature: string) {
    this.applicationMetrics.featureUsage[feature] = (this.applicationMetrics.featureUsage[feature] || 0) + 1;
  }

  // Plugin Execution Tracking
  public recordPluginExecution(plugin: string, success: boolean, executionTime: number) {
    if (!this.applicationMetrics.pluginExecutions[plugin]) {
      this.applicationMetrics.pluginExecutions[plugin] = {
        success: 0,
        failure: 0,
        totalTime: 0
      };
    }

    const pluginMetrics = this.applicationMetrics.pluginExecutions[plugin];
    
    if (success) {
      pluginMetrics.success++;
    } else {
      pluginMetrics.failure++;
    }
    
    pluginMetrics.totalTime += executionTime;
  }

  // Model Request Tracking
  public recordModelRequest(model: string, responseTime: number) {
    this.applicationMetrics.modelRequests[model] = (this.applicationMetrics.modelRequests[model] || 0) + 1;
    this.recordModelResponseTime(model, responseTime);
  }

  private recordModelResponseTime(model: string, responseTime: number) {
    if (!this.applicationMetrics.modelResponseTimes[model]) {
      this.applicationMetrics.modelResponseTimes[model] = {
        buckets: {},
        sum: 0,
        count: 0,
        total: 0
      };
    }

    const responseTimeMetrics = this.applicationMetrics.modelResponseTimes[model];
    
    // Update histogram buckets
    const buckets = [0.1, 0.5, 1, 2, 5, 10, 30, 60];
    buckets.forEach(bucket => {
      if (responseTime <= bucket) {
        responseTimeMetrics.buckets[bucket] = (responseTimeMetrics.buckets[bucket] || 0) + 1;
      }
    });

    responseTimeMetrics.sum += responseTime;
    responseTimeMetrics.count++;
    responseTimeMetrics.total++;
  }

  // Health Check Tracking
  public recordHealthCheck(checkName: string, status: 'healthy' | 'unhealthy' | 'degraded') {
    this.systemMetrics.healthChecks[checkName] = status;
  }

  // Database Metrics
  public recordDatabaseConnection(active: number, idle: number) {
    this.systemMetrics.database.activeConnections = active;
    this.systemMetrics.database.idleConnections = idle;
  }

  public recordDatabaseConnectionFailure() {
    this.systemMetrics.database.failedConnections++;
  }

  public recordDatabaseQuery(query: string, duration: number) {
    if (!this.systemMetrics.database.queryDurations[query]) {
      this.systemMetrics.database.queryDurations[query] = {
        buckets: {},
        sum: 0,
        count: 0,
        total: 0
      };
    }

    const queryMetrics = this.systemMetrics.database.queryDurations[query];
    
    // Update histogram buckets
    const buckets = [0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10];
    buckets.forEach(bucket => {
      if (duration <= bucket) {
        queryMetrics.buckets[bucket] = (queryMetrics.buckets[bucket] || 0) + 1;
      }
    });

    queryMetrics.sum += duration;
    queryMetrics.count++;
    queryMetrics.total++;
  }

  // Redis Metrics
  public recordRedisConnection(connections: number) {
    this.systemMetrics.redis.connections = connections;
  }

  public recordRedisConnectionFailure() {
    this.systemMetrics.redis.failedConnections++;
  }

  public recordRedisMetrics(memoryUsage: number, keyCount: number) {
    this.systemMetrics.redis.memoryUsage = memoryUsage;
    this.systemMetrics.redis.keyCount = keyCount;
  }

  // Business Metrics
  public recordUserSession() {
    this.businessMetrics.userSessions++;
  }

  public recordConversion() {
    this.businessMetrics.conversions++;
  }

  public recordBounce() {
    this.businessMetrics.bounces++;
  }

  public recordRateLimitExceeded() {
    this.businessMetrics.rateLimitExceeded++;
  }

  public recordFailedLogin(sourceIp: string) {
    this.businessMetrics.failedLogins[sourceIp] = (this.businessMetrics.failedLogins[sourceIp] || 0) + 1;
  }

  public recordEvilModeActivation() {
    this.businessMetrics.evilModeActivations++;
  }

  // Metrics Collection Time Tracking
  public recordMetricsCollectionTime(time: number) {
    this.metricsCollectionTimes.push(time);
    
    // Keep only last 100 collection times
    if (this.metricsCollectionTimes.length > 100) {
      this.metricsCollectionTimes.shift();
    }
  }

  // System Metrics Collection
  private async collectSystemMetrics() {
    try {
      // Collect filesystem metrics
      await this.collectFilesystemMetrics();
      
      // Collect memory metrics would go here
      // await this.collectMemoryMetrics();
      
    } catch (error) {
      console.error('Failed to collect system metrics:', error);
    }
  }

  private async collectFilesystemMetrics() {
    try {
      // In a real implementation, you would collect actual filesystem metrics
      // For now, we'll simulate some metrics
      this.systemMetrics.filesystem.diskUsage = Math.random() * 100;
      this.systemMetrics.filesystem.inodeUsage = Math.random() * 100;
      this.systemMetrics.filesystem.readOperations = Math.floor(Math.random() * 1000);
      this.systemMetrics.filesystem.writeOperations = Math.floor(Math.random() * 500);
    } catch (error) {
      console.error('Failed to collect filesystem metrics:', error);
    }
  }

  // Business Metrics Collection
  private async collectBusinessMetrics() {
    try {
      // In a real implementation, you would collect actual business metrics
      // from your database or analytics service
      
      // Simulate some business metrics
      this.businessMetrics.subscriptions.active = Math.floor(Math.random() * 1000);
      this.businessMetrics.revenue.total = Math.random() * 100000;
      
    } catch (error) {
      console.error('Failed to collect business metrics:', error);
    }
  }

  // Getter methods for metrics
  public async getApplicationMetrics(): Promise<ApplicationMetrics> {
    return { ...this.applicationMetrics };
  }

  public async getSystemMetrics(): Promise<SystemMetrics> {
    return { ...this.systemMetrics };
  }

  public async getBusinessMetrics(): Promise<BusinessMetrics> {
    return { ...this.businessMetrics };
  }

  // Reset metrics (useful for testing)
  public resetMetrics() {
    this.applicationMetrics = this.initializeApplicationMetrics();
    this.systemMetrics = this.initializeSystemMetrics();
    this.businessMetrics = this.initializeBusinessMetrics();
    this.metricsCollectionTimes = [];
  }

  // Get metrics summary
  public getMetricsSummary() {
    const totalRequests = Object.values(this.applicationMetrics.httpRequests)
      .reduce((sum, path) => sum + path.totalRequests, 0);
    
    const totalPluginExecutions = Object.values(this.applicationMetrics.pluginExecutions)
      .reduce((sum, plugin) => sum + plugin.success + plugin.failure, 0);
    
    const totalModelRequests = Object.values(this.applicationMetrics.modelRequests)
      .reduce((sum, count) => sum + count, 0);

    const averageCollectionTime = this.metricsCollectionTimes.length > 0
      ? this.metricsCollectionTimes.reduce((sum, time) => sum + time, 0) / this.metricsCollectionTimes.length
      : 0;

    return {
      totalHttpRequests: totalRequests,
      activeSessions: this.applicationMetrics.activeSessions,
      websocketConnections: this.applicationMetrics.websocketConnections,
      totalPluginExecutions,
      totalModelRequests,
      totalUserSessions: this.businessMetrics.userSessions,
      totalConversions: this.businessMetrics.conversions,
      averageCollectionTime,
      lastCollectionTime: this.metricsCollectionTimes[this.metricsCollectionTimes.length - 1] || 0
    };
  }
}

export default MetricsCollector;