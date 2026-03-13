/**
 * Backend Performance Optimization Types
 * TypeScript definitions for backend performance optimization
 */

// Backend metrics
export interface BackendMetrics {
  responseTime: number; // Average response time in ms
  throughput: number; // Requests per second
  errorRate: number; // Error rate percentage
  cpuUsage: number; // CPU usage percentage
  memoryUsage: number; // Memory usage in MB
  diskUsage: number; // Disk usage in MB
  networkLatency: number; // Network latency in ms
  cacheHitRate: number; // Cache hit rate percentage
  activeConnections: number; // Active database connections
  queueLength: number; // Queue length
}

// Backend cache status
export interface CacheStatus {
  size: number; // Cache size in MB
  entries: number; // Number of cache entries
  hitRate: number; // Hit rate percentage
  missRate: number; // Miss rate percentage
  evictionRate: number; // Eviction rate percentage
  ttl: number; // Average TTL in seconds
  strategy: string; // Caching strategy being used
}

// Backend optimization status
export interface OptimizationStatus {
  enabledOptimizations: string[]; // List of enabled optimizations
  appliedOptimizations: string[]; // List of applied optimizations
  pendingOptimizations: string[]; // List of pending optimizations
  failedOptimizations: string[]; // List of failed optimizations
  lastOptimization: Date | null; // Last optimization time
  nextOptimization: Date | null; // Next optimization time
}

// Backend performance report
export interface PerformanceReport {
  id: string;
  timestamp: Date;
  metrics: BackendMetrics;
  cacheStats: CacheStatus;
  optimizations: OptimizationStatus;
  recommendations: string[];
  score: number; // 0-100
}

// Database optimization
export interface DatabaseOptimization {
  queryOptimization: boolean;
  indexOptimization: boolean;
  connectionPooling: boolean;
  connectionTimeout: number; // ms
  batchSize: number;
  retryStrategy: 'exponential' | 'linear' | 'none';
  maxRetries: number;
}

// API response optimization
export interface APIResponseOptimization {
  compressionEnabled: boolean;
  compressionLevel: 'none' | 'gzip' | 'brotli' | 'zstd';
  cachingEnabled: boolean;
  cachingStrategy: 'memory' | 'disk' | 'redis' | 'hybrid';
  cacheTimeout: number; // seconds
  rateLimiting: boolean;
  rateLimitWindow: number; // seconds
  rateLimitMax: number; // requests per window
}

// Server-side rendering optimization
export interface ServerRenderingOptimization {
  ssrEnabled: boolean;
  ssrStrategy: 'static' | 'dynamic' | 'hybrid';
  componentCaching: boolean;
  streamRendering: boolean;
  progressiveRendering: boolean;
  renderTimeout: number; // ms
  maxConcurrentRenders: number;
}

// Network optimization
export interface NetworkOptimization {
  cdnEnabled: boolean;
  cdnProvider: string;
  compressionEnabled: boolean;
  compressionLevel: 'none' | 'gzip' | 'brotli' | 'zstd';
  keepAliveEnabled: boolean;
  keepAliveTimeout: number; // seconds
  connectionReuse: boolean;
  maxConnections: number;
  requestTimeout: number; // ms
}

// Complete backend optimization configuration
export interface BackendOptimizationConfig {
  database: DatabaseOptimization;
  api: APIResponseOptimization;
  serverRendering: ServerRenderingOptimization;
  network: NetworkOptimization;
  monitoring: {
    enabled: boolean;
    interval: number; // ms
    metricsRetention: number; // hours
    alertingEnabled: boolean;
    alertThresholds: {
      responseTime: number; // ms
      errorRate: number; // percentage
      cpuUsage: number; // percentage
      memoryUsage: number; // MB
      throughput: number; // requests per second
    };
  };
  caching: {
    enabled: boolean;
    strategy: 'memory' | 'disk' | 'redis' | 'hybrid';
    maxSize: number; // MB
    ttl: number; // seconds
    evictionPolicy: 'lru' | 'lfu' | 'ttl' | 'random';
    compressionEnabled: boolean;
    compressionLevel: 'none' | 'gzip' | 'brotli' | 'zstd';
  };
}

// Optimization action types
export type OptimizationAction = 
  | 'enable-query-optimization'
  | 'enable-index-optimization'
  | 'enable-connection-pooling'
  | 'enable-response-compression'
  | 'enable-response-caching'
  | 'enable-request-caching'
  | 'enable-keep-alive'
  | 'enable-connection-reuse'
  | 'enable-rate-limiting'
  | 'enable-ssr'
  | 'enable-component-caching'
  | 'enable-stream-rendering'
  | 'enable-progressive-rendering'
  | 'enable-cdn'
  | 'enable-network-compression';

// Optimization result
export interface OptimizationResult {
  action: OptimizationAction;
  success: boolean;
  message: string;
  previousValue: unknown;
  newValue: unknown;
  timestamp: Date;
}

// Performance alert
export interface PerformanceAlert {
  id: string;
  type: 'performance' | 'availability' | 'capacity' | 'error-rate' | 'resource-usage' | 'metric-poor';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  metric?: string;
  threshold?: number;
  actualValue?: number;
  timestamp: Date;
  resolved: boolean;
  action?: OptimizationAction;
}
