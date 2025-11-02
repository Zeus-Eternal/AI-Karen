// Performance monitoring components and utilities
export { default as PerformanceDashboard } from './performance-dashboard';
export { 
  default as PerformanceProvider, 
  usePerformanceContext,
  withPerformanceMeasurement,
  useComponentPerformance,
  useInteractionPerformance
} from './performance-provider';

// Re-export performance utilities
export {
  PerformanceMonitor,
  performanceMonitor,
  usePerformanceMonitor,
  checkPerformanceBudget,
  PERFORMANCE_THRESHOLDS
} from '@/utils/performance-monitor';

// Re-export types
export type {
  WebVitalsMetric,
  CustomMetric,
  PerformanceSummary,
  MetricSummary,
  ResourceTimingSummary,
  NavigationTimingSummary
} from '@/utils/performance-monitor';