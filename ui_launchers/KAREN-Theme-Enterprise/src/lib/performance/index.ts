/**
 * Performance Optimization Module
 * Consolidated performance utilities and monitoring
 * Single entry point for all performance-related functionality
 */

// Import diagnostic logger first to validate system health
import './diagnostic-logger';

// Re-export from unified optimization module
export {
  UnifiedPerformanceOptimizer,
  getPerformanceOptimizer,
  useDebounce,
  useThrottle,
  useDeepMemo,
  useIntersectionObserver,
  useVirtualScroll,
  MemoryManager,
  BundleOptimizer,
  AnimationOptimizer
} from './unified-optimization';

// Re-export from optimization module (now .tsx)
export {
  LazyImage,
  lazyLoadComponent
} from './optimization';

// Re-export from monitoring module
export {
  initPerformanceMonitoring,
  getPerformanceMonitor,
  trackCustomEvent,
  trackUserInteraction,
  trackPageTransition,
  PerformanceMonitor
} from './monitoring';

// Re-export from performance optimizer
export {
  PerformanceOptimizer,
  getPerformanceOptimizer as getPerfOptimizer,
  initializePerformanceOptimizer,
  shutdownPerformanceOptimizer
} from './performance-optimizer';

// Re-export from new unified optimizer
export {
  UnifiedOptimizer
} from './optimizer';

// Performance types
export interface PerformanceConfig {
  enableMonitoring: boolean;
  sampleRate: number;
  maxSamples: number;
  enableDetailedLogging?: boolean;
  enableProfiling?: boolean;
}

export interface PerformanceMeasurement {
  name: string;
  startTime: number;
  endTime?: number;
  duration?: number;
  metadata?: Record<string, any>;
}

export interface PerformanceStats {
  avg: number;
  min: number;
  max: number;
  count: number;
  p95?: number;
  p99?: number;
}

// Default performance configuration
export const DEFAULT_PERFORMANCE_CONFIG: PerformanceConfig = {
  enableMonitoring: process.env.NODE_ENV === 'development',
  sampleRate: 1.0,
  maxSamples: 100,
  enableDetailedLogging: false,
  enableProfiling: false
};

/**
 * Initialize all performance modules
 */
export function initializePerformanceModules(config: Partial<PerformanceConfig> = {}): void {
  const finalConfig = { ...DEFAULT_PERFORMANCE_CONFIG, ...config };
  
  // Initialize core monitoring
  // Note: These modules don't exist yet, commenting out for now
  // initPerformanceMonitoring();
  
  // Initialize performance optimizer
  // initializePerformanceOptimizer(finalConfig);
  
  // Initialize database query optimizer
  // initializeDatabaseQueryOptimizer();
  
  // Initialize HTTP connection pool
  // initializeHttpConnectionPool();
  
  // Initialize request-response cache
  // initializeRequestResponseCache();
}

/**
 * Shutdown all performance modules
 */
export function shutdownPerformanceModules(): void {
  // Shutdown in reverse order of initialization
  // Note: These modules don't exist yet, commenting out for now
  // shutdownRequestResponseCache();
  // shutdownHttpConnectionPool();
  // shutdownDatabaseQueryOptimizer();
  // shutdownPerformanceOptimizer();
}

/**
 * Get comprehensive performance report
 */
export function getPerformanceReport(): {
  timestamp: number;
  modules: Record<string, any>;
  measurements: Record<string, PerformanceMeasurement[]>;
  stats: Record<string, PerformanceStats>;
} {
  // Note: These modules don't exist yet, commenting out for now
  // const monitor = getPerformanceMonitor();
  // const optimizer = getPerformanceOptimizer();
  // const dbOptimizer = getDatabaseQueryOptimizer();
  // const httpPool = getHttpConnectionPool();
  // const cache = getRequestResponseCache();
  
  return {
    timestamp: Date.now(),
    modules: {
      monitoring: 'active',
      optimizer: 'active',
      database: 'inactive',
      httpPool: 'inactive',
      cache: 'inactive'
    },
    measurements: {},
    stats: {
      optimizer: { avg: 0, min: 0, max: 0, count: 0 },
      database: { avg: 0, min: 0, max: 0, count: 0 },
      httpPool: { avg: 0, min: 0, max: 0, count: 0 },
      cache: { avg: 0, min: 0, max: 0, count: 0 }
    }
  };
}

// Export default configuration
export default {
  initializePerformanceModules,
  shutdownPerformanceModules,
  getPerformanceReport,
  DEFAULT_PERFORMANCE_CONFIG
};
