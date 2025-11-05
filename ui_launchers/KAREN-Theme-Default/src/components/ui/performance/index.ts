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
  performanceMonitor,
  usePerformanceMonitor,
  checkPerformanceBudget,
} from '@/utils/performance-monitor';

// Re-export types
export type {
  PerformanceMetrics,
  PerformanceConfig,
  PerformanceBudget,
} from '@/utils/performance-monitor';
