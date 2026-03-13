/**
 * Performance Adaptive Routing Types
 * TypeScript definitions for the performance adaptive routing dashboard
 */

// Performance Metrics Types
export interface LatencyMetrics {
  p50: number;
  p95: number;
  p99: number;
  mean: number;
  standardDeviation: number;
  timestamp: Date;
}

export interface ThroughputMetrics {
  requestsPerSecond: number;
  tokensPerSecond: number;
  concurrentRequests: number;
  timestamp: Date;
}

export interface ErrorMetrics {
  errorRate: number;
  timeoutRate: number;
  retryRate: number;
  timestamp: Date;
}

export interface ResourceUtilization {
  cpu: number;
  memory: number;
  networkBandwidth: number;
  timestamp: Date;
}

export interface QualityMetrics {
  userSatisfaction: number;
  responseQuality: number;
  capabilityMatch: number;
  timestamp: Date;
}

export interface CostMetrics {
  costPerRequest: number;
  costPerToken: number;
  costEfficiency: number;
  timestamp: Date;
}

export interface ReliabilityMetrics {
  uptimePercentage: number;
  successRate: number;
  meanTimeToRecovery: number;
  timestamp: Date;
}

export interface PerformanceMetrics {
  id: string;
  providerId: string;
  latency: LatencyMetrics;
  throughput: ThroughputMetrics;
  errors: ErrorMetrics;
  resources: ResourceUtilization;
  quality: QualityMetrics;
  cost: CostMetrics;
  reliability: ReliabilityMetrics;
  timestamp: Date;
}

// Provider Types
export interface Provider {
  id: string;
  name: string;
  type: 'primary' | 'fallback' | 'specialized';
  status: 'active' | 'inactive' | 'degraded' | 'maintenance';
  capabilities: string[];
  region: string;
  priority: number;
  maxRequests: number;
  currentLoad: number;
  healthScore: number;
  lastHealthCheck: Date;
}

export interface ProviderPerformance {
  providerId: string;
  metrics: PerformanceMetrics[];
  averageResponseTime: number;
  successRate: number;
  costEfficiency: number;
  reliabilityScore: number;
  userSatisfaction: number;
  trend: 'improving' | 'stable' | 'declining';
  status: 'active' | 'inactive' | 'degraded' | 'maintenance';
  lastUpdated: Date;
}

// Routing Decision Types
export interface RoutingDecision {
  id: string;
  requestId: string;
  timestamp: Date;
  inputType: string;
  selectedProvider: string;
  alternativeProviders: string[];
  confidence: number;
  rationale: string;
  factors: RoutingFactor[];
  executionTime: number;
  success: boolean;
  error?: string;
}

export interface RoutingFactor {
  name: string;
  weight: number;
  value: number;
  impact: 'positive' | 'negative' | 'neutral';
}

export interface RoutingStrategy {
  id: string;
  name: string;
  description: string;
  type: 'performance-based' | 'cost-based' | 'reliability-based' | 'hybrid';
  factors: RoutingFactor[];
  thresholds: RoutingThresholds;
  fallbackBehavior: 'sequential' | 'parallel' | 'smart';
  isActive: boolean;
  priority: number;
}

export interface RoutingThresholds {
  maxLatency: number;
  minSuccessRate: number;
  maxErrorRate: number;
  maxCostPerRequest: number;
  minReliabilityScore: number;
}

// Analytics Types
export interface RoutingAnalytics {
  id: string;
  timestamp: Date;
  period: 'hour' | 'day' | 'week' | 'month';
  totalRequests: number;
  successfulRequests: number;
  failedRequests: number;
  averageResponseTime: number;
  providerUsage: Record<string, number>;
  strategyEffectiveness: Record<string, number>;
  performanceTrends: PerformanceTrend[];
  anomalies: Anomaly[];
}

export interface PerformanceTrend {
  metric: string;
  direction: 'up' | 'down' | 'stable';
  change: number;
  period: string;
  significance: 'low' | 'medium' | 'high';
}

export interface Anomaly {
  id: string;
  type: 'performance' | 'availability' | 'cost' | 'quality';
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  detectedAt: Date;
  affectedProviders: string[];
  impact: string;
  resolution?: string;
  resolvedAt?: Date;
}

// Alert Types
export interface PerformanceAlert {
  id: string;
  type: 'performance-degradation' | 'provider-failure' | 'cost-spike' | 'quality-drop' | 'anomaly-detected';
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  message: string;
  providerId?: string;
  metric?: string;
  threshold?: number;
  actualValue?: number;
  timestamp: Date;
  acknowledged: boolean;
  acknowledgedBy?: string;
  acknowledgedAt?: Date;
  resolved: boolean;
  resolvedAt?: Date;
  resolution?: string;
}

// Configuration Types
export interface AdaptiveRoutingConfig {
  enabled: boolean;
  defaultStrategy: string;
  fallbackStrategies: string[];
  monitoringInterval: number;
  alertThresholds: AlertThresholds;
  autoOptimization: boolean;
  learningEnabled: boolean;
  dataRetention: number;
}

export interface AlertThresholds {
  responseTime: number;
  errorRate: number;
  costPerRequest: number;
  reliabilityScore: number;
  userSatisfaction: number;
}

// State Management Types
export interface PerformanceAdaptiveRoutingState {
  providers: Provider[];
  providerPerformance: Record<string, ProviderPerformance>;
  currentMetrics: PerformanceMetrics[];
  routingDecisions: RoutingDecision[];
  analytics: RoutingAnalytics[];
  alerts: PerformanceAlert[];
  strategies: RoutingStrategy[];
  config: AdaptiveRoutingConfig;
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
}

export interface PerformanceAdaptiveRoutingActions {
  // Data fetching
  fetchProviders: () => Promise<void>;
  fetchMetrics: (providerId?: string, timeRange?: TimeRange) => Promise<void>;
  fetchRoutingDecisions: (timeRange?: TimeRange) => Promise<void>;
  fetchAnalytics: (period: string) => Promise<void>;
  fetchAlerts: () => Promise<void>;
  fetchStrategies: () => Promise<void>;
  fetchConfig: () => Promise<void>;

  // Real-time updates
  subscribeToUpdates: () => void;
  unsubscribeFromUpdates: () => void;

  // Alert management
  acknowledgeAlert: (alertId: string, userId: string) => Promise<void>;
  resolveAlert: (alertId: string, resolution: string) => Promise<void>;

  // Configuration
  updateConfig: (config: Partial<AdaptiveRoutingConfig>) => Promise<void>;
  updateStrategy: (strategyId: string, strategy: Partial<RoutingStrategy>) => Promise<void>;
  setActiveStrategy: (strategyId: string) => Promise<void>;

  // Manual overrides
  overrideRouting: (requestId: string, providerId: string, reason: string) => Promise<void>;
  enableProvider: (providerId: string) => Promise<void>;
  disableProvider: (providerId: string, reason: string) => Promise<void>;

  // Data export
  exportMetrics: (providerId?: string, timeRange?: TimeRange) => Promise<void>;
  exportAnalytics: (period: string) => Promise<void>;
}

// Utility Types
export interface TimeRange {
  start: Date;
  end: Date;
}

export interface ChartDataPoint {
  timestamp: Date;
  value: number;
  label?: string;
  metadata?: Record<string, unknown>;
}

export interface FilterOptions {
  providers?: string[];
  strategies?: string[];
  timeRange?: TimeRange;
  metrics?: string[];
  severity?: string[];
}

export interface SortOptions {
  field: string;
  direction: 'asc' | 'desc';
}

// Hook Types
export interface UsePerformanceMetricsResult {
  metrics: PerformanceMetrics[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  subscribe: () => void;
  unsubscribe: () => void;
}

export interface UseRoutingDecisionsResult {
  decisions: RoutingDecision[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  override: (requestId: string, providerId: string, reason: string) => Promise<void>;
}

export interface UseProviderComparisonResult {
  providers: ProviderPerformance[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  compare: (providerIds: string[]) => void;
}

export interface UseRoutingAnalyticsResult {
  analytics: RoutingAnalytics[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  export: (period: string) => Promise<void>;
}

export interface UsePerformanceAlertsResult {
  alerts: PerformanceAlert[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  acknowledge: (alertId: string, userId: string) => Promise<void>;
  resolve: (alertId: string, resolution: string) => Promise<void>;
}

export interface UseAdaptiveStrategyResult {
  strategies: RoutingStrategy[];
  activeStrategy: RoutingStrategy | null;
  config: AdaptiveRoutingConfig;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  updateConfig: (config: Partial<AdaptiveRoutingConfig>) => Promise<void>;
  updateStrategy: (strategyId: string, strategy: Partial<RoutingStrategy>) => Promise<void>;
  setActive: (strategyId: string) => Promise<void>;
}
