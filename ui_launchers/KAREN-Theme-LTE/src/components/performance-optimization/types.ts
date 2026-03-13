/**
 * Performance Optimization Types
 * TypeScript definitions for the performance optimization system
 */

// Lazy loading types
export interface LazyComponentConfig {
  componentId: string;
  importPath: string;
  preload?: boolean;
  fallback?: React.ComponentType;
  errorBoundary?: React.ComponentType;
  priority?: 'high' | 'normal' | 'low';
  dependencies?: string[];
}

export interface LazyLoadState {
  isLoading: boolean;
  isLoaded: boolean;
  hasError: boolean;
  error?: Error;
  loadTime?: number;
}

// Route-based code splitting types
export interface RouteConfig {
  path: string;
  componentPath: string;
  preload?: boolean;
  priority?: 'high' | 'normal' | 'low';
  chunkName?: string;
}

// Resource lazy loading types
export interface ResourceConfig {
  id: string;
  url: string;
  type: 'image' | 'script' | 'style' | 'font' | 'data';
  preload?: boolean;
  priority?: 'high' | 'normal' | 'low';
  cacheStrategy?: 'memory' | 'disk' | 'service-worker';
  compression?: boolean;
}

// Performance monitoring types
export interface PerformanceMetric {
  name: string;
  value: number;
  unit: string;
  timestamp: Date;
  rating: 'good' | 'needs-improvement' | 'poor';
  threshold?: {
    good: number;
    poor: number;
  };
  metadata?: Record<string, unknown>;
}

export interface PerformanceBudget {
  totalSize: number; // KB
  jsSize: number; // KB
  cssSize: number; // KB
  imageSize: number; // KB
  fontSize: number; // KB
  renderTime: number; // ms
  loadTime: number; // ms
}

export interface PerformanceAlert {
  id: string;
  type: 'budget-exceeded' | 'metric-poor' | 'bottleneck-detected' | 'memory-leak' | 'regression-detected' | 'threshold-approaching';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  metric?: string;
  threshold?: number;
  actualValue?: number;
  timestamp: Date;
  resolved?: boolean;
}

// Caching strategy types
export interface CacheConfig {
  strategy: 'memory' | 'disk' | 'service-worker' | 'hybrid';
  maxSize: number; // MB
  ttl: number; // seconds
  compressionEnabled: boolean;
  encryptionEnabled: boolean;
}

export interface CacheEntry<T = unknown> {
  key: string;
  value: T;
  timestamp: Date;
  expiresAt: Date;
  size: number;
  accessCount: number;
  lastAccessed: Date;
  metadata?: Record<string, unknown>;
}

// Preloading and prefetching types
export interface PreloadConfig {
  resources: ResourceConfig[];
  strategy: 'critical' | 'important' | 'background';
  trigger: 'immediate' | 'idle' | 'viewport' | 'interaction';
  priority?: 'high' | 'normal' | 'low';
}

export interface PrefetchConfig {
  routes: RouteConfig[];
  components: LazyComponentConfig[];
  data: string[]; // API endpoints
  strategy: 'conservative' | 'moderate' | 'aggressive';
  bandwidthAware: boolean;
}

// Device-specific optimization types
export interface DeviceProfile {
  type: 'mobile' | 'tablet' | 'desktop';
  os: string;
  browser: string;
  connectionType: 'slow-2g' | '2g' | '3g' | '4g' | '5g' | 'wifi' | 'ethernet';
  memory: number; // GB
  cpuCores: number;
  screenResolution: {
    width: number;
    height: number;
  };
  pixelRatio: number;
  capabilities: {
    webp: boolean;
    avif: boolean;
    wasm: boolean;
    webgl: boolean;
    webgl2: boolean;
    serviceWorker: boolean;
    pushNotifications: boolean;
    bluetooth: boolean;
    geolocation: boolean;
    camera: boolean;
    microphone: boolean;
    touchEvents: boolean;
    pointerEvents: boolean;
    deviceMemory: boolean;
    connectionApi: boolean;
    batteryApi: boolean;
    performanceTimeline: boolean;
    userActivation: boolean;
  };
}

// Performance profiling types
export interface ProfileResult {
  id: string;
  name: string;
  startTime: number;
  endTime: number;
  duration: number;
  samples: ProfileSample[];
  bottlenecks: Bottleneck[];
  recommendations: string[];
  timestamp: Date;
}

export interface ProfileSample {
  timestamp: number;
  cpu: number;
  memory: number;
  network: number;
  frameTime?: number;
  longTasks?: LongTask[];
}

export interface LongTask {
  startTime: number;
  duration: number;
  type: string;
  attribution?: string;
}

export interface Bottleneck {
  type: 'cpu' | 'memory' | 'network' | 'rendering' | 'javascript';
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  location?: string;
  impact: string;
  recommendation: string;
  score?: number;
}

// Performance optimization state
export interface PerformanceOptimizationState {
  // Lazy loading
  lazyComponents: Record<string, LazyLoadState>;
  
  // Resource management
  loadedResources: Record<string, ResourceConfig>;
  preloadQueue: ResourceConfig[];
  
  // Performance metrics
  metrics: PerformanceMetric[];
  budgets: Record<string, PerformanceBudget>;
  alerts: PerformanceAlert[];
  
  // Caching
  cache: Record<string, CacheEntry>;
  cacheConfig: CacheConfig;
  
  // Device profiling
  deviceProfile: DeviceProfile | null;
  
  // Settings
  settings: {
    enableLazyLoading: boolean;
    enablePreloading: boolean;
    enablePrefetching: boolean;
    enableMonitoring: boolean;
    enableCaching: boolean;
    enableProfiling: boolean;
    enableDeviceOptimization: boolean;
    enableBudgetAlerts: boolean;
    monitoringInterval: number;
    cacheSize: number;
    preloadStrategy: 'critical' | 'important' | 'background';
  };
}

// Performance optimization actions
export interface PerformanceOptimizationActions {
  // Lazy loading actions
  loadComponent: (componentId: string) => Promise<void>;
  preloadComponent: (componentId: string) => Promise<void>;
  unloadComponent: (componentId: string) => void;
  
  // Resource management actions
  loadResource: (resourceId: string) => Promise<void>;
  preloadResources: (resourceIds: string[]) => Promise<void>;
  unloadResource: (resourceId: string) => void;
  
  // Performance monitoring actions
  startMonitoring: () => void;
  stopMonitoring: () => void;
  measureMetric: (metric: PerformanceMetric) => void;
  generateReport: () => PerformanceReport;
  
  // Caching actions
  setCacheConfig: (config: Partial<CacheConfig>) => void;
  addToCache: <T>(key: string, value: T, ttl?: number) => void;
  getFromCache: <T>(key: string) => T | null;
  removeFromCache: (key: string) => void;
  clearCache: () => void;
  
  // Device optimization actions
  detectDeviceProfile: () => Promise<DeviceProfile>;
  applyDeviceOptimizations: (profile: DeviceProfile) => void;
  
  // Settings actions
  updateSettings: (settings: Partial<PerformanceOptimizationState['settings']>) => void;
}

// Performance report types
export interface PerformanceReport {
  id: string;
  timestamp: Date;
  metrics: PerformanceMetric[];
  budgets: Record<string, PerformanceBudget>;
  alerts: PerformanceAlert[];
  cacheStats: {
    size: number;
    entries: number;
    hitRate: number;
    missRate: number;
  };
  deviceProfile: DeviceProfile;
  recommendations: string[];
  score: number; // 0-100
}

// Event types
export interface PerformanceEvent {
  type: 'component-loaded' | 'resource-loaded' | 'metric-measured' | 'alert-triggered' | 'cache-hit' | 'cache-miss';
  payload: unknown;
  timestamp: Date;
}

// Hook types
export interface UseLazyComponentResult<T = Record<string, unknown>> {
  Component: React.ComponentType<T> | null;
  isLoading: boolean;
  hasError: boolean;
  error: Error | null;
  preload: () => Promise<void>;
  retry: () => Promise<void>;
}

export interface UsePerformanceMetricsResult {
  metrics: PerformanceMetric[];
  isMonitoring: boolean;
  score: number;
  alerts: PerformanceAlert[];
  startMonitoring: () => void;
  stopMonitoring: () => void;
  generateReport: () => PerformanceReport;
}

export interface UseCacheResult<T = unknown> {
  data: T | null;
  isLoading: boolean;
  hasError: boolean;
  error: Error | null;
  set: (value: T, ttl?: number) => void;
  get: () => T | null;
  remove: () => void;
  clear: () => void;
}

export interface UseDeviceOptimizationResult {
  profile: DeviceProfile | null;
  isOptimized: boolean;
  optimizations: string[];
  detectProfile: () => Promise<DeviceProfile>;
  applyOptimizations: () => void;
}
