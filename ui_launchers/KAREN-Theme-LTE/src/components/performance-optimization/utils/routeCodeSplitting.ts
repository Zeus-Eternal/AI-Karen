/**
 * Route-based Code Splitting Utilities
 * Utilities for implementing route-based code splitting and dynamic imports
 */

import React from 'react';
import { RouteConfig } from '../types';
import { usePerformanceOptimizationStore } from '../store/performanceOptimizationStore';

// Route registry
const routeRegistry = new Map<string, RouteConfig>();
const routePromises = new Map<string, Promise<unknown>>();

// Default route configurations
const DEFAULT_ROUTE_CONFIGS: RouteConfig[] = [
  {
    path: '/chat',
    componentPath: '@/components/chat/ChatInterface',
    priority: 'high',
    preload: true,
  },
  {
    path: '/task-management',
    componentPath: '@/components/task-management/TaskManagement',
    priority: 'normal',
    preload: false,
  },
  {
    path: '/memory',
    componentPath: '@/components/memory/MemoryManagement',
    priority: 'normal',
    preload: false,
  },
  {
    path: '/agent-selection',
    componentPath: '@/components/agent-selection/AgentSelection',
    priority: 'low',
    preload: false,
  },
];

// Register routes
export function registerRoutes(routes: RouteConfig[]): void {
  routes.forEach(route => {
    routeRegistry.set(route.path, route);
  });
}

// Register a single route
export function registerRoute(route: RouteConfig): void {
  routeRegistry.set(route.path, route);
}

// Get route configuration
export function getRouteConfig(path: string): RouteConfig | undefined {
  return routeRegistry.get(path);
}

// Get all routes
export function getAllRoutes(): RouteConfig[] {
  return Array.from(routeRegistry.values());
}

// Get routes by priority
export function getRoutesByPriority(priority: 'high' | 'normal' | 'low'): RouteConfig[] {
  return Array.from(routeRegistry.values()).filter(route => route.priority === priority);
}

// Dynamic import for route components
export async function importRouteComponent(routePath: string): Promise<unknown> {
  if (routePromises.has(routePath)) {
    return routePromises.get(routePath);
  }

  const importPromise = import(routePath)
    .then(module => {
      const loadTime = performance.now();
      
      // Record performance metric
      const store = usePerformanceOptimizationStore.getState();
      store.measureMetric({
        name: `route-load-${routePath}`,
        value: loadTime,
        unit: 'ms',
        timestamp: new Date(),
        rating: loadTime < 200 ? 'good' : loadTime < 500 ? 'needs-improvement' : 'poor',
        threshold: { good: 200, poor: 500 },
      });

      return module.default || module;
    })
    .catch(error => {
      console.error(`Failed to load route component ${routePath}:`, error);
      throw error;
    });

  routePromises.set(routePath, importPromise);
  return importPromise;
}

// Preload route components
export async function preloadRoute(path: string): Promise<void> {
  const routeConfig = getRouteConfig(path);
  if (!routeConfig) {
    throw new Error(`Route ${path} not found in registry`);
  }

  try {
    await importRouteComponent(routeConfig.componentPath);
  } catch (error) {
    console.warn(`Failed to preload route ${path}:`, error);
  }
}

// Preload multiple routes by priority
export async function preloadRoutesByPriority(
  priority: 'high' | 'normal' | 'low'
): Promise<void> {
  const routes = getRoutesByPriority(priority);
  const preloadPromises = routes.map(route => preloadRoute(route.path));
  
  await Promise.allSettled(preloadPromises);
}

// Preload all routes
export async function preloadAllRoutes(): Promise<void> {
  // Preload high priority first
  await preloadRoutesByPriority('high');
  
  // Then normal priority
  await preloadRoutesByPriority('normal');
  
  // Finally low priority
  await preloadRoutesByPriority('low');
}

// Intersection Observer for viewport-based route preloading
export function useViewportRoutePreloading(
  routePaths: string[],
  options?: IntersectionObserverInit & { preloadDistance?: number }
) {
  void routePaths;
  const [preloadedRoutes, setPreloadedRoutes] = React.useState<Set<string>>(new Set());
  const elementRefs = React.useRef<Map<string, HTMLElement>>(new Map());
  const { preloadDistance = 200, ...observerOptions } = options || {};

  React.useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const routePath = entry.target.getAttribute('data-route-path');
          if (!routePath) return;

          if (entry.isIntersecting || entry.intersectionRatio > 0) {
            // Route is near viewport, preload it
            preloadRoute(routePath)
              .then(() => {
                setPreloadedRoutes(prev => new Set([...prev, routePath]));
              })
              .catch(error => {
                console.warn(`Failed to preload route ${routePath}:`, error);
              });
          }
        });
      },
      {
        rootMargin: `${preloadDistance}px`,
        ...observerOptions,
      }
    );

    // Observe all route elements
    elementRefs.current.forEach((element) => {
      observer.observe(element);
    });

    return () => observer.disconnect();
  }, [preloadDistance, observerOptions]);

  // Function to get ref for a specific route
  const getRouteRef = React.useCallback((routePath: string) => {
    return (element: HTMLElement | null) => {
      if (element) {
        elementRefs.current.set(routePath, element);
        element.setAttribute('data-route-path', routePath);
      } else {
        elementRefs.current.delete(routePath);
      }
    };
  }, []);

  return {
    getRouteRef,
    preloadedRoutes,
    isPreloaded: (routePath: string) => preloadedRoutes.has(routePath),
  };
}

// Network-aware route preloading
export function useNetworkAwarePreloading() {
  const [connectionType, setConnectionType] = React.useState<string>('4g');
  const [isOnline, setIsOnline] = React.useState(true);

  React.useEffect(() => {
    type NavigatorWithConnection = Navigator & {
      connection?: {
        effectiveType?: string;
        addEventListener?: (event: string, handler: () => void) => void;
        removeEventListener?: (event: string, handler: () => void) => void;
      };
      mozConnection?: {
        effectiveType?: string;
        addEventListener?: (event: string, handler: () => void) => void;
        removeEventListener?: (event: string, handler: () => void) => void;
      };
      webkitConnection?: {
        effectiveType?: string;
        addEventListener?: (event: string, handler: () => void) => void;
        removeEventListener?: (event: string, handler: () => void) => void;
      };
    };

    const updateConnectionInfo = () => {
      const nav = navigator as NavigatorWithConnection;
      const connection = nav.connection || nav.mozConnection || nav.webkitConnection;
      
      if (connection) {
        setConnectionType(connection.effectiveType || '4g');
      }
      
      setIsOnline(navigator.onLine);
    };

    // Initial update
    updateConnectionInfo();

    // Listen for changes
    window.addEventListener('online', updateConnectionInfo);
    window.addEventListener('offline', updateConnectionInfo);
    
    const nav = navigator as NavigatorWithConnection;
    if (nav.connection) {
      nav.connection.addEventListener?.('change', updateConnectionInfo);
    }

    return () => {
      window.removeEventListener('online', updateConnectionInfo);
      window.removeEventListener('offline', updateConnectionInfo);
      
      if (nav.connection) {
        nav.connection.removeEventListener?.('change', updateConnectionInfo);
      }
    };
  }, []);

  const shouldPreload = React.useCallback((priority: 'high' | 'normal' | 'low') => {
    if (!isOnline) return false;
    
    switch (connectionType) {
      case 'slow-2g':
      case '2g':
        return priority === 'high';
      case '3g':
        return priority === 'high' || priority === 'normal';
      case '4g':
      default:
        return true;
    }
  }, [connectionType, isOnline]);

  const getPreloadStrategy = React.useCallback(() => {
    if (!isOnline) return 'none';
    
    switch (connectionType) {
      case 'slow-2g':
      case '2g':
        return 'conservative';
      case '3g':
        return 'moderate';
      case '4g':
      default:
        return 'aggressive';
    }
  }, [connectionType, isOnline]);

  return {
    connectionType,
    isOnline,
    shouldPreload,
    getPreloadStrategy,
  };
}

// Route-based chunk loading with progress tracking
export function useRouteChunkLoading() {
  const [loadingProgress, setLoadingProgress] = React.useState<Record<string, number>>({});
  const [loadingStates, setLoadingStates] = React.useState<Record<string, boolean>>({});

  const loadRouteWithProgress = React.useCallback(async (path: string) => {
    const routeConfig = getRouteConfig(path);
    if (!routeConfig) {
      throw new Error(`Route ${path} not found`);
    }

    setLoadingStates(prev => ({ ...prev, [path]: true }));
    setLoadingProgress(prev => ({ ...prev, [path]: 0 }));

    try {
      // Simulate progress tracking
      const progressInterval = setInterval(() => {
        setLoadingProgress(prev => {
          const current = prev[path] || 0;
          const next = Math.min(current + 10, 90);
          return { ...prev, [path]: next };
        });
      }, 50);

      const component = await importRouteComponent(routeConfig.componentPath);
      
      clearInterval(progressInterval);
      setLoadingProgress(prev => ({ ...prev, [path]: 100 }));
      
      setTimeout(() => {
        setLoadingStates(prev => ({ ...prev, [path]: false }));
        setLoadingProgress(prev => ({ ...prev, [path]: 0 }));
      }, 500);

      return component;
    } catch (error) {
      setLoadingStates(prev => ({ ...prev, [path]: false }));
      setLoadingProgress(prev => ({ ...prev, [path]: 0 }));
      throw error;
    }
  }, []);

  return {
    loadingProgress,
    loadingStates,
    loadRouteWithProgress,
    isLoading: (path: string) => loadingStates[path] || false,
    getProgress: (path: string) => loadingProgress[path] || 0,
  };
}

// Route cache management
class RouteCache {
  private cache = new Map<string, { component: unknown; timestamp: number; ttl: number }>();
  private defaultTTL = 5 * 60 * 1000; // 5 minutes

  set(path: string, component: unknown, ttl?: number): void {
    this.cache.set(path, {
      component,
      timestamp: Date.now(),
      ttl: ttl || this.defaultTTL,
    });
  }

  get(path: string): unknown | null {
    const entry = this.cache.get(path);
    if (!entry) return null;

    const now = Date.now();
    if (now - entry.timestamp > entry.ttl) {
      this.cache.delete(path);
      return null;
    }

    return entry.component;
  }

  has(path: string): boolean {
    const entry = this.cache.get(path);
    if (!entry) return false;

    const now = Date.now();
    if (now - entry.timestamp > entry.ttl) {
      this.cache.delete(path);
      return false;
    }

    return true;
  }

  clear(): void {
    this.cache.clear();
  }

  delete(path: string): boolean {
    return this.cache.delete(path);
  }

  size(): number {
    return this.cache.size;
  }

  cleanup(): void {
    const now = Date.now();
    for (const [path, entry] of this.cache.entries()) {
      if (now - entry.timestamp > entry.ttl) {
        this.cache.delete(path);
      }
    }
  }
}

export const routeCache = new RouteCache();

// Enhanced route loading with caching
export async function loadRouteWithCache(path: string): Promise<unknown> {
  // Check cache first
  if (routeCache.has(path)) {
    const cachedComponent = routeCache.get(path);
    if (cachedComponent) {
      return cachedComponent;
    }
  }

  // Load from network
  const component = await importRouteComponent(
    getRouteConfig(path)?.componentPath || path
  );

  // Cache the component
  routeCache.set(path, component);

  return component;
}

// Initialize default routes
export function initializeDefaultRoutes(): void {
  registerRoutes(DEFAULT_ROUTE_CONFIGS);
}

// Route performance monitoring
export function useRoutePerformanceMetrics() {
  const metrics = usePerformanceOptimizationStore(state => state.metrics);

  const getRouteMetrics = React.useCallback((path: string) => {
    return metrics.filter(metric => metric.name === `route-load-${path}`);
  }, [metrics]);

  const getAverageLoadTime = React.useCallback((path: string) => {
    const routeMetrics = getRouteMetrics(path);
    if (routeMetrics.length === 0) return 0;
    
    const total = routeMetrics.reduce((sum, metric) => sum + metric.value, 0);
    return total / routeMetrics.length;
  }, [getRouteMetrics]);

  const getLoadSuccessRate = React.useCallback((path: string) => {
    const routeMetrics = getRouteMetrics(path);
    if (routeMetrics.length === 0) return 0;
    
    const successful = routeMetrics.filter(metric => metric.rating !== 'poor').length;
    return (successful / routeMetrics.length) * 100;
  }, [getRouteMetrics]);

  return {
    getRouteMetrics,
    getAverageLoadTime,
    getLoadSuccessRate,
  };
}

// Predictive route preloading based on user behavior
export function usePredictivePreloading() {
  const [routeHistory, setRouteHistory] = React.useState<string[]>([]);
  const [predictionModel, setPredictionModel] = React.useState<Map<string, number>>(new Map());

  // Track route visits
  const trackRouteVisit = React.useCallback((path: string) => {
    setRouteHistory(prev => {
      const newHistory = [...prev, path].slice(-50); // Keep last 50 routes
      return newHistory;
    });
  }, []);

  // Update prediction model based on history
  React.useEffect(() => {
    const model = new Map<string, number>();
    
    // Simple frequency analysis
    routeHistory.forEach(route => {
      const count = model.get(route) || 0;
      model.set(route, count + 1);
    });

    // Normalize scores
    const maxCount = Math.max(...model.values());
    model.forEach((count, route) => {
      model.set(route, count / maxCount);
    });

    setPredictionModel(model);
  }, [routeHistory]);

  // Get predicted next routes
  const getPredictedRoutes = React.useCallback((currentRoute: string, limit: number = 3) => {
    const predictions = Array.from(predictionModel.entries())
      .filter(([route]) => route !== currentRoute)
      .sort(([, a], [, b]) => b - a)
      .slice(0, limit)
      .map(([route]) => route);

    return predictions;
  }, [predictionModel]);

  // Preload predicted routes
  const preloadPredictedRoutes = React.useCallback(async (currentRoute: string) => {
    const predicted = getPredictedRoutes(currentRoute);
    const preloadPromises = predicted.map(route => preloadRoute(route));
    
    await Promise.allSettled(preloadPromises);
  }, [getPredictedRoutes]);

  return {
    trackRouteVisit,
    getPredictedRoutes,
    preloadPredictedRoutes,
    routeHistory,
    predictionModel,
  };
}
