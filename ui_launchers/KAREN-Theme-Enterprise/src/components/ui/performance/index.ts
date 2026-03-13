// Performance monitoring components and utilities
export { PerformanceDashboard } from './performance-dashboard';
export type { PerformanceDashboardProps } from './performance-dashboard';

export { PerformanceProvider } from './performance-provider';
export type { PerformanceProviderProps } from './performance-provider';
export {
  usePerformanceContext,
  withPerformanceMeasurement,
  useComponentPerformance,
  useInteractionPerformance,
} from './performance-context';
export type { PerformanceContextValue, PerformanceMetric } from './performance-context';

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
