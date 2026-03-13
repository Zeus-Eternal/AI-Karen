/**
 * Performance Optimization Store
 * Simplified Zustand store for performance optimization state
 */

import { create } from 'zustand';
import { 
  PerformanceOptimizationState,
  PerformanceOptimizationActions,
  PerformanceMetric,
  PerformanceAlert,
  PerformanceBudget,
  CacheConfig,
  CacheEntry,
  DeviceProfile,
  PerformanceReport,
} from '../types';

declare global {
  interface Window {
    __performanceOptimizationInterval?: ReturnType<typeof setInterval>;
  }
}

type NetworkConnectionInfo = {
  effectiveType?: DeviceProfile['connectionType'];
};

type NavigatorWithPerformanceExtensions = Navigator & {
  connection?: NetworkConnectionInfo;
  mozConnection?: NetworkConnectionInfo;
  webkitConnection?: NetworkConnectionInfo;
  deviceMemory?: number;
};

type PerformanceWithMemory = Performance & {
  memory?: {
    usedJSHeapSize: number;
  };
};

function hasMeasurePerformance(store: unknown): store is { measurePerformance: () => void } {
  if (typeof store !== 'object' || store === null) {
    return false;
  }

  return typeof (store as { measurePerformance?: unknown }).measurePerformance === 'function';
}

// Default performance budgets
const DEFAULT_BUDGETS: Record<string, PerformanceBudget> = {
  mobile: {
    totalSize: 250, // 250KB
    jsSize: 100, // 100KB
    cssSize: 50, // 50KB
    imageSize: 75, // 75KB
    fontSize: 25, // 25KB
    renderTime: 1000, // 1s
    loadTime: 3000, // 3s
  },
  desktop: {
    totalSize: 500, // 500KB
    jsSize: 200, // 200KB
    cssSize: 100, // 100KB
    imageSize: 150, // 150KB
    fontSize: 50, // 50KB
    renderTime: 500, // 500ms
    loadTime: 2000, // 2s
  },
};

// Default cache configuration
const DEFAULT_CACHE_CONFIG: CacheConfig = {
  strategy: 'hybrid',
  maxSize: 50, // 50MB
  ttl: 3600, // 1 hour
  compressionEnabled: true,
  encryptionEnabled: false,
};

// Default settings
const DEFAULT_SETTINGS = {
  enableLazyLoading: true,
  enablePreloading: true,
  enablePrefetching: true,
  enableMonitoring: true,
  enableCaching: true,
  enableProfiling: false,
  enableDeviceOptimization: true,
  enableBudgetAlerts: true,
  monitoringInterval: 5000, // 5 seconds
  cacheSize: 50, // 50MB
  preloadStrategy: 'critical' as const,
};

export const usePerformanceOptimizationStore = create<PerformanceOptimizationState & PerformanceOptimizationActions>((set, get) => ({
  // Initial state
  lazyComponents: {},
  loadedResources: {},
  preloadQueue: [],
  metrics: [],
  budgets: DEFAULT_BUDGETS,
  alerts: [],
  cache: {},
  cacheConfig: DEFAULT_CACHE_CONFIG,
  deviceProfile: null,
  settings: DEFAULT_SETTINGS,
  
  // Lazy loading actions
  loadComponent: async (componentId: string) => {
    const startTime = performance.now();
    
    set((state) => ({
      lazyComponents: {
        ...state.lazyComponents,
        [componentId]: {
          ...state.lazyComponents[componentId],
          isLoading: true,
          hasError: false,
          error: undefined,
          isLoaded: false,
          loadTime: undefined,
        },
      },
    }));
    
    try {
      // Simulate component loading
      await new Promise(resolve => setTimeout(resolve, 100));
      
      const loadTime = performance.now() - startTime;
      
      set((state) => ({
        lazyComponents: {
          ...state.lazyComponents,
          [componentId]: {
            ...state.lazyComponents[componentId],
            isLoading: false,
            isLoaded: true,
            hasError: false,
            error: undefined,
            loadTime,
          },
        },
      }));
      
      // Record performance metric
      const currentState = get();
      currentState.measureMetric({
        name: `component-load-${componentId}`,
        value: loadTime,
        unit: 'ms',
        timestamp: new Date(),
        rating: loadTime < 100 ? 'good' : loadTime < 300 ? 'needs-improvement' : 'poor',
        threshold: { good: 100, poor: 300 },
      });
    } catch (error) {
      set((state) => ({
        lazyComponents: {
          ...state.lazyComponents,
          [componentId]: {
            ...state.lazyComponents[componentId],
            isLoading: false,
            isLoaded: false,
            hasError: true,
            error: error as Error,
            loadTime: undefined,
          },
        },
      }));
    }
  },
  
  preloadComponent: async (componentId: string) => {
    // Similar to loadComponent but with lower priority
    void componentId;
    await new Promise(resolve => setTimeout(resolve, 50));
  },
  
  unloadComponent: (componentId: string) => {
    set((state) => {
      const newLazyComponents = { ...state.lazyComponents };
      delete newLazyComponents[componentId];
      return { lazyComponents: newLazyComponents };
    });
  },
  
  // Resource management actions
  loadResource: async (resourceId: string) => {
    const startTime = performance.now();
    
    set((state) => {
      const updatedResources = { ...state.loadedResources };
      updatedResources[resourceId] = {
        id: resourceId,
        url: `/resources/${resourceId}`,
        type: 'data' as const,
      };
      return { loadedResources: updatedResources };
    });
    
    try {
      await new Promise(resolve => setTimeout(resolve, 50));
      const loadTime = performance.now() - startTime;
      
      set((state) => {
        const updatedResources = { ...state.loadedResources };
        if (updatedResources[resourceId]) {
          updatedResources[resourceId] = {
            ...updatedResources[resourceId],
          };
        }
        return { loadedResources: updatedResources };
      });
      
      const currentState = get();
      currentState.measureMetric({
        name: `resource-load-${resourceId}`,
        value: loadTime,
        unit: 'ms',
        timestamp: new Date(),
        rating: loadTime < 50 ? 'good' : loadTime < 150 ? 'needs-improvement' : 'poor',
        threshold: { good: 50, poor: 150 },
      });
    } catch (error) {
      console.error(`Failed to load resource ${resourceId}:`, error);
    }
  },
  
  preloadResources: async (resourceIds: string[]) => {
    const currentState = get();
    const promises = resourceIds.map(id => currentState.loadResource(id));
    await Promise.all(promises);
  },
  
  unloadResource: (resourceId: string) => {
    set((state) => {
      const newLoadedResources = { ...state.loadedResources };
      delete newLoadedResources[resourceId];
      return { loadedResources: newLoadedResources };
    });
  },
  
  // Performance monitoring actions
  startMonitoring: () => {
    const currentState = get();
    const { settings } = currentState;
    
    if (!settings.enableMonitoring) return;
    
    const monitorInterval = setInterval(() => {
      const currentStore = get();
      if (hasMeasurePerformance(currentStore)) {
        currentStore.measurePerformance();
      }
    }, settings.monitoringInterval);
    
    window.__performanceOptimizationInterval = monitorInterval;
    
    const currentStore = get();
    if (hasMeasurePerformance(currentStore)) {
      currentStore.measurePerformance();
    }
  },
  
  stopMonitoring: () => {
    const interval = window.__performanceOptimizationInterval;
    if (interval) {
      clearInterval(interval);
      delete window.__performanceOptimizationInterval;
    }
  },
  
  measureMetric: (metric: PerformanceMetric) => {
    set((state) => ({
      metrics: [...state.metrics, metric],
    }));
  },
  
  measurePerformance: () => {
    try {
      if ('performance' in window) {
        const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
        
        if (navigation) {
          // Load time metric
          const loadTime = navigation.loadEventEnd - navigation.requestStart;
          const currentState = get();
          currentState.measureMetric({
            name: 'page-load-time',
            value: loadTime,
            unit: 'ms',
            timestamp: new Date(),
            rating: loadTime < 2000 ? 'good' : loadTime < 4000 ? 'needs-improvement' : 'poor',
            threshold: { good: 2000, poor: 4000 },
          });

          // Render time metric
          const renderTime = navigation.domContentLoadedEventEnd - navigation.responseStart;
          currentState.measureMetric({
            name: 'render-time',
            value: renderTime,
            unit: 'ms',
            timestamp: new Date(),
            rating: renderTime < 500 ? 'good' : renderTime < 1000 ? 'needs-improvement' : 'poor',
            threshold: { good: 500, poor: 1000 },
          });
        }

        // Memory usage
        if ('memory' in performance) {
          const memory = (performance as PerformanceWithMemory).memory;
          if (!memory) {
            return;
          }
          const memoryUsage = Math.round(memory.usedJSHeapSize / 1048576); // Convert to MB
          
          const currentState = get();
          currentState.measureMetric({
            name: 'memory-usage',
            value: memoryUsage,
            unit: 'MB',
            timestamp: new Date(),
            rating: memoryUsage < 50 ? 'good' : memoryUsage < 100 ? 'needs-improvement' : 'poor',
            threshold: { good: 50, poor: 100 },
          });
        }
      }
    } catch (error) {
      console.error('Failed to measure performance:', error);
    }
  },
  
  generateReport: (): PerformanceReport => {
    const currentState = get();
    const score = calculatePerformanceScore(currentState.metrics);
    
    return {
      id: `report-${Date.now()}`,
      timestamp: new Date(),
      metrics: currentState.metrics,
      budgets: currentState.budgets,
      alerts: currentState.alerts,
      cacheStats: calculateCacheStats(currentState.cache),
      deviceProfile: currentState.deviceProfile!,
      recommendations: generateRecommendations(currentState.metrics, currentState.alerts),
      score,
    };
  },
  
  // Caching actions
  setCacheConfig: (config: Partial<CacheConfig>) => {
    set((state) => ({
      cacheConfig: { ...state.cacheConfig, ...config },
    }));
  },
  
  addToCache: <T,>(key: string, value: T, ttl?: number) => {
    const currentState = get();
    const { cacheConfig } = currentState;
    const now = new Date();
    const expiresAt = new Date(now.getTime() + (ttl || cacheConfig.ttl) * 1000);
    
    const entry: CacheEntry<T> = {
      key,
      value,
      timestamp: now,
      expiresAt,
      size: JSON.stringify(value).length,
      accessCount: 0,
      lastAccessed: now,
    };
    
    set((state) => ({
      cache: {
        ...state.cache,
        [key]: entry,
      },
    }));
  },
  
  getFromCache: <T,>(key: string): T | null => {
    const currentState = get();
    const entry = currentState.cache[key] as CacheEntry<T>;
    
    if (!entry) return null;
    
    const now = new Date();
    if (now > entry.expiresAt) {
      // Entry expired, remove it
      set((state) => {
        const newCache = { ...state.cache };
        delete newCache[key];
        return { cache: newCache };
      });
      return null;
    }
    
    // Update access statistics
    set((state) => ({
      cache: {
        ...state.cache,
        [key]: {
          ...entry,
          accessCount: entry.accessCount + 1,
          lastAccessed: now,
        },
      },
    }));
    
    return entry.value;
  },
  
  removeFromCache: (key: string) => {
    set((state) => {
      const newCache = { ...state.cache };
      delete newCache[key];
      return { cache: newCache };
    });
  },
  
  clearCache: () => {
    set({ cache: {} });
  },
  
  // Device optimization actions
  detectDeviceProfile: async (): Promise<DeviceProfile> => {
    const profile: DeviceProfile = {
      type: detectDeviceType(),
      os: detectOS(),
      browser: detectBrowser(),
      connectionType: detectConnectionType(),
      memory: detectMemory(),
      cpuCores: navigator.hardwareConcurrency || 4,
      screenResolution: {
        width: window.screen.width,
        height: window.screen.height,
      },
      pixelRatio: window.devicePixelRatio || 1,
      capabilities: {
        webp: supportsWebP(),
        avif: supportsAVIF(),
        wasm: supportsWASM(),
        webgl: supportsWebGL(),
        webgl2: supportsWebGL2(),
        serviceWorker: 'serviceWorker' in navigator,
        pushNotifications: 'PushManager' in window,
        bluetooth: 'bluetooth' in navigator,
        geolocation: 'geolocation' in navigator,
        camera: 'mediaDevices' in navigator,
        microphone: 'mediaDevices' in navigator,
        touchEvents: 'ontouchstart' in window,
        pointerEvents: 'onpointerdown' in window,
        deviceMemory: 'deviceMemory' in navigator,
        connectionApi: 'connection' in navigator,
        batteryApi: 'getBattery' in navigator,
        performanceTimeline: 'PerformanceObserver' in window,
        userActivation: 'userActivation' in navigator,
      },
    };
    
    set({ deviceProfile: profile });
    return profile;
  },
  
  applyDeviceOptimizations: (profile: DeviceProfile) => {
    const optimizations: string[] = [];
    
    // Apply optimizations based on device profile
    if (profile.type === 'mobile') {
      optimizations.push('Enabled mobile-specific optimizations');
    }
    
    if (profile.connectionType === 'slow-2g' || profile.connectionType === '2g') {
      optimizations.push('Enabled data-saving mode');
    }
    
    if (profile.memory < 4) {
      optimizations.push('Enabled memory-saving mode');
    }
    
    set({ deviceProfile: profile });
    return optimizations;
  },
  
  // Settings actions
  updateSettings: (settings: Partial<PerformanceOptimizationState['settings']>) => {
    set((state) => ({
      settings: { ...state.settings, ...settings },
    }));
  },
  
}));

// Helper functions
function calculatePerformanceScore(metrics: PerformanceMetric[]): number {
  if (metrics.length === 0) return 0;
  
  let totalScore = 0;
  let metricCount = 0;
  
  metrics.forEach((metric) => {
    let score = 0;
    switch (metric.rating) {
      case 'good':
        score = 100;
        break;
      case 'needs-improvement':
        score = 50;
        break;
      case 'poor':
        score = 0;
        break;
    }
    
    totalScore += score;
    metricCount++;
  });
  
  return Math.round(totalScore / metricCount);
}

function calculateCacheStats(cache: Record<string, CacheEntry>) {
  const entries = Object.values(cache);
  const totalSize = entries.reduce((sum, entry) => sum + entry.size, 0);
  const totalAccesses = entries.reduce((sum, entry) => sum + entry.accessCount, 0);
  const hitRate = totalAccesses > 0 ? (totalAccesses / entries.length) : 0;
  const missRate = hitRate > 0 ? (1 - hitRate) : 0;
  
  return {
    size: Math.round(totalSize / 1024), // KB
    entries: entries.length,
    hitRate: Math.round(hitRate * 100),
    missRate: Math.round(missRate * 100),
  };
}

function generateRecommendations(metrics: PerformanceMetric[], alerts: PerformanceAlert[]): string[] {
  const recommendations: string[] = [];
  
  // Analyze metrics for recommendations
  const loadTimeMetrics = metrics.filter(m => m.name === 'page-load-time');
  if (loadTimeMetrics.length > 0) {
    const avgLoadTime = loadTimeMetrics.reduce((sum, m) => sum + m.value, 0) / loadTimeMetrics.length;
    if (avgLoadTime > 3000) {
      recommendations.push('Consider implementing code splitting and lazy loading to reduce page load time');
    }
  }
  
  const memoryMetrics = metrics.filter(m => m.name === 'memory-usage');
  if (memoryMetrics.length > 0) {
    const avgMemory = memoryMetrics.reduce((sum, m) => sum + m.value, 0) / memoryMetrics.length;
    if (avgMemory > 100) {
      recommendations.push('Optimize memory usage by implementing proper cleanup and reducing cache size');
    }
  }
  
  // Analyze alerts for recommendations
  alerts.forEach((alert) => {
    if (alert.type === 'budget-exceeded') {
      recommendations.push(`Budget exceeded for ${alert.metric}: ${alert.message}`);
    }
  });
  
  return recommendations;
}

// Device detection utilities
function detectDeviceType(): 'mobile' | 'tablet' | 'desktop' {
  const width = window.innerWidth;
  if (width < 768) return 'mobile';
  if (width < 1024) return 'tablet';
  return 'desktop';
}

function detectOS(): string {
  const userAgent = navigator.userAgent;
  if (userAgent.includes('Windows')) return 'Windows';
  if (userAgent.includes('Mac')) return 'macOS';
  if (userAgent.includes('Linux')) return 'Linux';
  if (userAgent.includes('Android')) return 'Android';
  if (userAgent.includes('iOS')) return 'iOS';
  return 'Unknown';
}

function detectBrowser(): string {
  const userAgent = navigator.userAgent;
  if (userAgent.includes('Chrome')) return 'Chrome';
  if (userAgent.includes('Firefox')) return 'Firefox';
  if (userAgent.includes('Safari')) return 'Safari';
  if (userAgent.includes('Edge')) return 'Edge';
  return 'Unknown';
}

function detectConnectionType(): DeviceProfile['connectionType'] {
  const nav = navigator as NavigatorWithPerformanceExtensions;
  const connection = nav.connection || nav.mozConnection || nav.webkitConnection;
  if (connection) {
    return connection.effectiveType || 'wifi';
  }
  return 'wifi';
}

function detectMemory(): number {
  const memory = (navigator as NavigatorWithPerformanceExtensions).deviceMemory;
  return memory || 4; // Default to 4GB if not available
}

function supportsWebP(): boolean {
  const canvas = document.createElement('canvas');
  canvas.width = 1;
  canvas.height = 1;
  return canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0;
}

function supportsAVIF(): boolean {
  const canvas = document.createElement('canvas');
  canvas.width = 1;
  canvas.height = 1;
  return canvas.toDataURL('image/avif').indexOf('data:image/avif') === 0;
}

function supportsWASM(): boolean {
  return typeof WebAssembly === 'object' && typeof WebAssembly.instantiate === 'function';
}

function supportsWebGL(): boolean {
  const canvas = document.createElement('canvas');
  return !!(canvas.getContext('webgl') || canvas.getContext('experimental-webgl'));
}

function supportsWebGL2(): boolean {
  const canvas = document.createElement('canvas');
  return !!canvas.getContext('webgl2');
}
