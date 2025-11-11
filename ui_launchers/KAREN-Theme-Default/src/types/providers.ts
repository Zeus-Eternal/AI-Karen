/**
 * Enhanced Provider and Model Management Types
 * Supporting intelligent recommendations, performance monitoring, and failover
 */

export interface ProviderType {
  id: string;
  name: string;
  category: 'local' | 'cloud' | 'custom';
  description: string;
  icon?: string;
  configSchema: ProviderConfigSchema;
  supportedModels: string[];
  capabilities: string[];
}

export interface ProviderConfigSchema {
  fields: ProviderConfigField[];
  validation: ValidationRule[];
  dependencies?: ProviderDependency[];
}

export interface ProviderConfigField {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'select' | 'multiselect' | 'password' | 'url' | 'file' | 'textarea';
  label: string;
  description?: string;
  required: boolean;
  default?: unknown;
  options?: { value: string; label: string }[];
  validation?: FieldValidation;
  sensitive?: boolean;
}

export interface FieldValidation {
  pattern?: string;
  min?: number;
  max?: number;
  minLength?: number;
  maxLength?: number;
  custom?: string;
}

export interface ValidationRule {
  field: string;
  rule: string;
  message: string;
  dependsOn?: string[];
}

export interface ProviderDependency {
  field: string;
  dependsOn: string;
  condition: 'equals' | 'not_equals' | 'contains' | 'not_contains';
  value: unknown;
}

export interface ProviderConfig {
  id: string;
  name: string;
  type: string;
  enabled: boolean;
  configuration: Record<string, unknown>;
  credentials: Record<string, unknown>;
  metadata: ProviderMetadata;
  createdAt: Date;
  updatedAt: Date;
}

export interface ProviderMetadata {
  version: string;
  author?: string;
  description?: string;
  tags: string[];
  supportUrl?: string;
  documentationUrl?: string;
}

export interface ProviderHealth {
  status: 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
  lastCheck: Date;
  responseTime: number;
  uptime: number;
  errorRate: number;
  issues: HealthIssue[];
  metrics: ProviderMetrics;
}

export interface HealthIssue {
  id: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  details?: string;
  timestamp: Date;
  resolved: boolean;
}

export interface ProviderMetrics {
  requestCount: number;
  successRate: number;
  averageLatency: number;
  errorCount: number;
  lastError?: string;
  throughput: number;
  concurrentRequests: number;
  rateLimitStatus?: RateLimitStatus;
}

export interface RateLimitStatus {
  limit: number;
  remaining: number;
  resetTime: Date;
  windowSize: number;
}

export interface ModelRecommendation {
  modelId: string;
  score: number;
  reasons: RecommendationReason[];
  taskSuitability: TaskSuitability;
  performanceMetrics: ModelPerformanceMetrics;
  costEstimate: CostEstimate;
}

export interface RecommendationReason {
  type: 'performance' | 'cost' | 'capability' | 'availability' | 'history' | 'popularity';
  weight: number;
  description: string;
  evidence?: unknown;
}

export interface TaskSuitability {
  taskType: string;
  suitabilityScore: number;
  strengths: string[];
  limitations: string[];
  alternatives?: string[];
}

export interface ModelPerformanceMetrics {
  latency: LatencyMetrics;
  throughput: ThroughputMetrics;
  accuracy: AccuracyMetrics;
  reliability: ReliabilityMetrics;
  resourceUsage: ResourceUsageMetrics;
}

export interface LatencyMetrics {
  p50: number;
  p95: number;
  p99: number;
  average: number;
  trend: 'improving' | 'stable' | 'degrading';
}

export interface ThroughputMetrics {
  requestsPerSecond: number;
  tokensPerSecond: number;
  maxConcurrency: number;
  queueTime: number;
}

export interface AccuracyMetrics {
  overallScore: number;
  taskSpecificScores: Record<string, number>;
  benchmarkResults: BenchmarkResult[];
  userRatings: UserRating[];
}

export interface BenchmarkResult {
  benchmark: string;
  score: number;
  percentile: number;
  date: Date;
}

export interface UserRating {
  userId: string;
  rating: number;
  comment?: string;
  taskType: string;
  date: Date;
}

export interface ReliabilityMetrics {
  uptime: number;
  errorRate: number;
  failureTypes: Record<string, number>;
  recoveryTime: number;
}

export interface ResourceUsageMetrics {
  cpuUsage: number;
  memoryUsage: number;
  gpuUsage?: number;
  networkBandwidth: number;
  storageUsage: number;
}

export interface CostEstimate {
  perRequest: number;
  perToken: number;
  monthly: number;
  currency: string;
  breakdown: CostBreakdown;
  comparison: CostComparison[];
}

export interface CostBreakdown {
  compute: number;
  storage: number;
  network: number;
  licensing: number;
  other: number;
}

export interface CostComparison {
  modelId: string;
  costDifference: number;
  percentageDifference: number;
}

export interface ModelUsageAnalytics {
  modelId: string;
  timeRange: TimeRange;
  usage: UsageMetrics;
  performance: PerformanceAnalytics;
  costs: CostAnalytics;
  trends: TrendAnalytics;
  recommendations: OptimizationRecommendation[];
}

export interface TimeRange {
  start: Date;
  end: Date;
  granularity: 'hour' | 'day' | 'week' | 'month';
}

export interface UsageMetrics {
  totalRequests: number;
  uniqueUsers: number;
  averageRequestsPerUser: number;
  peakConcurrency: number;
  usageByHour: number[];
  usageByDay: number[];
  taskDistribution: Record<string, number>;
}

export interface PerformanceAnalytics {
  averageLatency: number;
  latencyDistribution: LatencyDistribution;
  throughputTrend: DataPoint[];
  errorRateTrend: DataPoint[];
  qualityMetrics: QualityMetrics;
}

export interface LatencyDistribution {
  buckets: LatencyBucket[];
  percentiles: Record<string, number>;
}

export interface LatencyBucket {
  min: number;
  max: number;
  count: number;
  percentage: number;
}

export interface DataPoint {
  timestamp: Date;
  value: number;
}

export interface QualityMetrics {
  userSatisfaction: number;
  taskSuccessRate: number;
  outputQuality: number;
  consistencyScore: number;
}

export interface CostAnalytics {
  totalCost: number;
  costTrend: DataPoint[];
  costPerRequest: number;
  costPerUser: number;
  budgetUtilization: number;
  projectedMonthlyCost: number;
}

export interface TrendAnalytics {
  usageTrend: 'increasing' | 'stable' | 'decreasing';
  performanceTrend: 'improving' | 'stable' | 'degrading';
  costTrend: 'increasing' | 'stable' | 'decreasing';
  seasonalPatterns: SeasonalPattern[];
}

export interface SeasonalPattern {
  pattern: string;
  strength: number;
  description: string;
}

export interface OptimizationRecommendation {
  type: 'cost' | 'performance' | 'reliability' | 'usage';
  priority: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  impact: ImpactEstimate;
  implementation: ImplementationGuide;
}

export interface ImpactEstimate {
  costSavings?: number;
  performanceImprovement?: number;
  reliabilityImprovement?: number;
  confidence: number;
}

export interface ImplementationGuide {
  steps: string[];
  estimatedTime: number;
  difficulty: 'easy' | 'medium' | 'hard';
  prerequisites: string[];
}

export interface FallbackConfig {
  id: string;
  name: string;
  enabled: boolean;
  chains: FallbackChain[];
  healthChecks: HealthCheck[];
  failoverRules: FailoverRule[];
  recovery: RecoveryConfig;
  analytics: FallbackAnalytics;
}

export interface FallbackChain {
  id: string;
  name: string;
  priority: number;
  providers: FallbackProvider[];
  conditions: FallbackCondition[];
}

export interface FallbackProvider {
  providerId: string;
  modelId?: string;
  weight: number;
  maxRetries: number;
  timeout: number;
  healthThreshold: number;
}

export interface FallbackCondition {
  type: 'error' | 'latency' | 'availability' | 'cost' | 'custom';
  operator: 'gt' | 'lt' | 'eq' | 'ne' | 'contains';
  value: unknown;
  action: 'skip' | 'fallback' | 'retry' | 'alert';
}

export interface HealthCheck {
  id: string;
  providerId: string;
  type: 'ping' | 'request' | 'custom';
  interval: number;
  timeout: number;
  retries: number;
  healthyThreshold: number;
  unhealthyThreshold: number;
}

export interface FailoverRule {
  id: string;
  name: string;
  trigger: FailoverTrigger;
  action: FailoverAction;
  cooldown: number;
  maxFailovers: number;
}

export interface FailoverTrigger {
  type: 'health' | 'error_rate' | 'latency' | 'custom';
  threshold: number;
  duration: number;
  conditions: string[];
}

export interface FailoverAction {
  type: 'switch' | 'load_balance' | 'circuit_break' | 'alert';
  target?: string;
  parameters: Record<string, unknown>;
}

export interface RecoveryConfig {
  autoRecovery: boolean;
  recoveryDelay: number;
  healthCheckInterval: number;
  recoveryThreshold: number;
  maxRecoveryAttempts: number;
}

export interface FallbackAnalytics {
  totalFailovers: number;
  failoversByProvider: Record<string, number>;
  averageRecoveryTime: number;
  successRate: number;
  impactMetrics: ImpactMetrics;
  recentEvents: FallbackEvent[];
}

export interface ImpactMetrics {
  requestsAffected: number;
  downtimeAvoided: number;
  costImpact: number;
  userImpact: number;
}

export interface FallbackEvent {
  id: string;
  timestamp: Date;
  type: 'failover' | 'recovery' | 'health_check';
  providerId: string;
  reason: string;
  duration: number;
  impact: string;
  resolved: boolean;
}

export interface ModelComparison {
  models: string[];
  criteria: ComparisonCriteria[];
  results: ComparisonResult[];
  recommendation: string;
  summary: ComparisonSummary;
}

export interface ComparisonCriteria {
  name: string;
  weight: number;
  type: 'performance' | 'cost' | 'capability' | 'reliability';
  description: string;
}

export interface ComparisonResult {
  modelId: string;
  scores: Record<string, number>;
  totalScore: number;
  rank: number;
  strengths: string[];
  weaknesses: string[];
}

export interface ComparisonSummary {
  winner: string;
  winnerScore: number;
  keyDifferentiators: string[];
  tradeoffs: string[];
  recommendations: string[];
}

export interface BudgetAlert {
  id: string;
  type: 'threshold' | 'projection' | 'anomaly';
  severity: 'info' | 'warning' | 'critical';
  title: string;
  message: string;
  currentSpend: number;
  threshold: number;
  projectedSpend?: number;
  timeframe: string;
  affectedProviders: string[];
  recommendations: string[];
  timestamp: Date;
}

export interface ModelWarmupConfig {
  modelId: string;
  enabled: boolean;
  preloadOnStartup: boolean;
  keepWarm: boolean;
  warmupTriggers: WarmupTrigger[];
  cooldownDelay: number;
  resourceLimits: ResourceLimits;
}

export interface WarmupTrigger {
  type: 'schedule' | 'usage_pattern' | 'manual' | 'api_call';
  condition: string;
  parameters: Record<string, unknown>;
}

export interface ResourceLimits {
  maxMemory: number;
  maxCpu: number;
  maxGpu?: number;
  priority: number;
}

export interface ModelBenchmark {
  id: string;
  modelId: string;
  benchmarkSuite: string;
  version: string;
  results: BenchmarkMetric[];
  environment: BenchmarkEnvironment;
  timestamp: Date;
  status: 'running' | 'completed' | 'failed';
}

export interface BenchmarkMetric {
  name: string;
  value: number;
  unit: string;
  percentile?: number;
  baseline?: number;
}

export interface BenchmarkEnvironment {
  hardware: string;
  software: string;
  configuration: Record<string, unknown>;
  dataset: string;
}
