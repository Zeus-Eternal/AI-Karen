/**
 * Performance Components Index
 * Exports all performance monitoring and analytics components
 */

export { PerformanceAnalyticsDashboard } from './PerformanceAnalyticsDashboard';
export { PerformanceAlertSystem } from './PerformanceAlertSystem';
export { PerformanceOptimizationDashboard } from './PerformanceOptimizationDashboard';
export { ResourceMonitoringDashboard } from './ResourceMonitoringDashboard';

// Re-export performance services for convenience
export { performanceMonitor } from '@/services/performance-monitor';
export { performanceOptimizer } from '@/services/performance-optimizer';
export { resourceMonitor } from '@/services/resource-monitor';
export { performanceProfiler } from '@/services/performance-profiler';

// Re-export types
export type {
  PerformanceMetric,
  PerformanceAlert,
  WebVitalsMetrics,
  ResourceUsage,
  PerformanceThresholds,
} from '@/services/performance-monitor';

export type {
  OptimizationConfig,
  OptimizationMetrics,
  OptimizationRecommendation,
} from '@/services/performance-optimizer';

export type {
  ResourceMetrics,
  ResourceAlert,
  ScalingRecommendation,
  CapacityPlan,
} from '@/services/resource-monitor';

export type {
  PerformanceProfile,
  Bottleneck,
  OptimizationSuggestion,
  PerformanceComparison,
  RegressionTest,
} from '@/services/performance-profiler';