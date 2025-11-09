// Performance monitoring components and utilities
export { PerformanceDashboard } from './performance-dashboard';
export type { PerformanceDashboardProps } from './performance-dashboard';

export {
  PerformanceProvider,
  usePerformanceContext,
  withPerformanceMeasurement,
  useComponentPerformance,
  useInteractionPerformance,
} from './performance-provider';
export type { PerformanceProviderProps, PerformanceContextValue } from './performance-provider';

// Re-export performance utilities
export {
  PerformanceMonitor,
  PERFORMANCE_THRESHOLDS,
  performanceMonitor,
  usePerformanceMonitor,
  checkPerformanceBudget,
} from '@/utils/performance-monitor';

// Re-export types
export type {
  CustomMetric,
  MetricSummary,
  NavigationTimingSummary,
  PerformanceSummary,
  ResourceTimingSummary,
  WebVitalsMetric,
} from '@/utils/performance-monitor';
