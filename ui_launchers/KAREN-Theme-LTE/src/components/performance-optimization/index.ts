/**
 * Performance Optimization Module
 * Main entry point for the performance optimization system
 */

// Main component
export { default as PerformanceOptimization } from './PerformanceOptimization';

// Types
export type {
  PerformanceOptimizationState,
  PerformanceOptimizationActions,
  LazyComponentConfig,
  LazyLoadState,
  RouteConfig,
  ResourceConfig,
  PerformanceMetric,
  PerformanceBudget,
  PerformanceAlert,
  CacheConfig,
  CacheEntry,
  PreloadConfig,
  PrefetchConfig,
  DeviceProfile,
  ProfileResult,
  Bottleneck,
  PerformanceReport,
  UseLazyComponentResult,
  UsePerformanceMetricsResult,
  UseCacheResult,
  UseDeviceOptimizationResult,
} from './types';

// Store
export { usePerformanceOptimizationStore } from './store/performanceOptimizationStore';

// Utilities
export {
  useLazyComponent,
} from './utils/componentLazyLoading';

export {
  loadResource,
  preloadResources,
} from './utils/resourceLazyLoading';

export {
  useCache,
} from './utils/cachingStrategies';

export {
  usePreload,
  usePrefetch,
} from './utils/preloadingPrefetching';

export {
  usePerformanceMonitoring,
} from './utils/performanceMonitoring';

export {
  usePerformanceBudgeting,
} from './utils/performanceBudgeting';

export {
  usePerformanceProfiling,
} from './utils/performanceProfiling';

export {
  useDeviceOptimization,
} from './utils/deviceOptimizations';

// Backend optimization
export {
  BackendPerformanceOptimization as BackendOptimizationManager,
} from './backend';

// Tests
export { runIntegrationTests } from './tests/integration.test';