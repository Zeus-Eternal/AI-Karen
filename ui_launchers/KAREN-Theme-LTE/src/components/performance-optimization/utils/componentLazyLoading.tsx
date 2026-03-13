/**
 * Component Lazy Loading Utilities
 * Advanced utilities for lazy loading React components with various strategies
 */

import React, { Suspense, lazy, type ComponentType, type ReactNode, useEffect, useState } from 'react';
import { LazyComponentConfig, LazyLoadState, UseLazyComponentResult } from '../types';
import { usePerformanceOptimizationStore } from '../store/performanceOptimizationStore';

type LazyComponentProps = Record<string, unknown>;
type LazyModule = { default?: ComponentType<LazyComponentProps> } & Record<string, unknown>;
type NavigatorWithConnection = Navigator & {
  connection?: {
    effectiveType?: string;
  };
};

// Default fallback component with skeleton loading
const DefaultFallback: React.FC<{ variant?: 'skeleton' | 'spinner' | 'dots' }> = ({ variant = 'spinner' }) => {
  switch (variant) {
    case 'skeleton':
      return (
        <div className="animate-pulse">
          <div className="h-4 bg-gray-300 rounded w-3/4 mb-2"></div>
          <div className="h-4 bg-gray-300 rounded w-1/2 mb-2"></div>
          <div className="h-4 bg-gray-300 rounded w-5/6"></div>
        </div>
      );
    case 'dots':
      return (
        <div className="flex justify-center items-center p-4">
          <div className="flex space-x-2">
            <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"></div>
            <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
            <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
          </div>
        </div>
      );
    default:
      return (
        <div className="flex items-center justify-center p-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      );
  }
};

// Enhanced error boundary component
const DefaultErrorBoundary: ComponentType<{ 
  error: Error; 
  retry: () => void;
  componentName?: string;
}> = ({ error, retry, componentName = 'Component' }) => (
  <div className="flex flex-col items-center justify-center p-8 text-center border border-red-200 rounded-lg bg-red-50">
    <div className="text-red-500 font-semibold mb-2">Failed to load {componentName}</div>
    <div className="text-sm text-gray-600 mb-4 max-w-md">{error.message}</div>
    <details className="text-xs text-gray-500 mb-4 cursor-pointer">
      <summary className="font-medium">Technical details</summary>
      <pre className="mt-2 p-2 bg-gray-100 rounded text-left overflow-auto max-h-32">
        {error.stack}
      </pre>
    </details>
    <button 
      onClick={retry}
      className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
    >
      Retry
    </button>
  </div>
);

// Advanced error boundary wrapper
interface AdvancedLazyErrorBoundaryProps {
  children: ReactNode;
  fallback: ComponentType<{ error: Error; retry: () => void; componentName?: string }>;
  componentName?: string;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

class AdvancedLazyErrorBoundary extends React.Component<
  AdvancedLazyErrorBoundaryProps, 
  { hasError: boolean; error: Error | null; errorInfo: React.ErrorInfo | null }
> {
  constructor(props: AdvancedLazyErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error, errorInfo: null };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.setState({ errorInfo });
    
    // Log error to performance monitoring
    const store = usePerformanceOptimizationStore.getState();
    store.measureMetric({
      name: `component-error-${this.props.componentName || 'unknown'}`,
      value: 1,
      unit: 'count',
      timestamp: new Date(),
      rating: 'poor',
      threshold: { good: 0, poor: 1 },
      metadata: { error: error.message, stack: error.stack },
    });

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  render(): ReactNode {
    if (this.state.hasError && this.state.error) {
      const FallbackComponent = this.props.fallback;
      return (
        <FallbackComponent 
          error={this.state.error} 
          retry={() => this.setState({ hasError: false, error: null, errorInfo: null })}
          componentName={this.props.componentName}
        />
      );
    }

    return this.props.children;
  }
}

// Enhanced lazy component registry with metadata
interface ComponentMetadata {
  config: LazyComponentConfig;
  loadCount: number;
  lastLoaded: Date | null;
  averageLoadTime: number;
  errorCount: number;
}

const lazyComponentRegistry = new Map<string, ComponentType<LazyComponentProps>>();
const componentMetadata = new Map<string, ComponentMetadata>();
const lazyComponentPromises = new Map<string, Promise<unknown>>();

// Register a lazy component with enhanced features
export function registerLazyComponent(config: LazyComponentConfig): void {
  const {
    componentId,
    importPath,
    fallback = DefaultFallback,
    errorBoundary = DefaultErrorBoundary,
    priority = 'normal',
    dependencies = [],
  } = config;

  // Initialize metadata
  componentMetadata.set(componentId, {
    config,
    loadCount: 0,
    lastLoaded: null,
    averageLoadTime: 0,
    errorCount: 0,
  });

  // Create lazy component with enhanced loading and error handling
  const LazyComponent = lazy(() => {
    const startTime = performance.now();
    const metadata = componentMetadata.get(componentId)!;

    // Load dependencies first if any
    const dependencyPromises = dependencies.map(dep => {
      if (!lazyComponentPromises.has(dep)) {
        lazyComponentPromises.set(dep, import(dep));
      }
      return lazyComponentPromises.get(dep)!;
    });

    // Load main component after dependencies
    return Promise.all(dependencyPromises)
      .then(() => import(importPath))
      .then((module: LazyModule) => {
        const loadTime = performance.now() - startTime;
        
        // Update metadata
        metadata.loadCount++;
        metadata.lastLoaded = new Date();
        metadata.averageLoadTime = (metadata.averageLoadTime * (metadata.loadCount - 1) + loadTime) / metadata.loadCount;
        
        // Update store with load time
        const store = usePerformanceOptimizationStore.getState();
        store.measureMetric({
          name: `component-load-${componentId}`,
          value: loadTime,
          unit: 'ms',
          timestamp: new Date(),
          rating: loadTime < 100 ? 'good' : loadTime < 300 ? 'needs-improvement' : 'poor',
          threshold: { good: 100, poor: 300 },
          metadata: {
            loadCount: metadata.loadCount,
            averageLoadTime: metadata.averageLoadTime,
            priority,
          },
        });

        return module.default || module;
      })
      .catch(error => {
        // Update error count
        metadata.errorCount++;
        
        // Log error to performance monitoring
        const store = usePerformanceOptimizationStore.getState();
        store.measureMetric({
          name: `component-load-error-${componentId}`,
          value: 1,
          unit: 'count',
          timestamp: new Date(),
          rating: 'poor',
          threshold: { good: 0, poor: 1 },
          metadata: { error: error.message, errorCount: metadata.errorCount },
        });

        throw error;
      });
  });

  // Wrap with error boundary and suspense
  const WrappedComponent: ComponentType<LazyComponentProps> = (props: LazyComponentProps) => (
    <AdvancedLazyErrorBoundary
      fallback={errorBoundary}
      componentName={componentId}
      onError={(error, errorInfo) => {
        console.error(`Error in lazy component ${componentId}:`, error, errorInfo);
      }}
    >
      <Suspense fallback={React.createElement(fallback)}>
        <LazyComponent {...props} />
      </Suspense>
    </AdvancedLazyErrorBoundary>
  );

  // Register component
  lazyComponentRegistry.set(componentId, WrappedComponent);

  // Preload if specified
  if (config.preload) {
    preloadComponent(componentId);
  }
}

// Get a lazy component
export function getLazyComponent(componentId: string): ComponentType<LazyComponentProps> | null {
  return lazyComponentRegistry.get(componentId) || null;
}

// Get component metadata
export function getComponentMetadata(componentId: string): ComponentMetadata | null {
  return componentMetadata.get(componentId) || null;
}

// Preload a component with enhanced error handling
export async function preloadComponent(componentId: string): Promise<void> {
  const component = lazyComponentRegistry.get(componentId);
  if (!component) {
    throw new Error(`Component ${componentId} not found in registry`);
  }

  try {
    // This is a simplified preload - in a real implementation,
    // you'd need to trigger the actual import
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // Update metadata
    const metadata = componentMetadata.get(componentId);
    if (metadata) {
      metadata.lastLoaded = new Date();
    }
  } catch (error) {
    console.warn(`Failed to preload component ${componentId}:`, error);
    throw error;
  }
}

// Enhanced hook for using lazy components
export function useLazyComponent<T extends object = LazyComponentProps>(
  componentId: string,
  options?: {
    config?: Partial<LazyComponentConfig>;
    autoLoad?: boolean;
    retryDelay?: number;
    maxRetries?: number;
  }
): UseLazyComponentResult<T> {
  const [state, setState] = React.useState<LazyLoadState>({
    isLoading: false,
    isLoaded: false,
    hasError: false,
    error: undefined,
  });

  const [retryCount, setRetryCount] = useState(0);
  const Component = getLazyComponent(componentId);
  const { autoLoad = true, retryDelay = 1000, maxRetries = 3 } = options || {};

  const load = React.useCallback(async () => {
    if (state.isLoaded || state.isLoading) return;

    setState(prev => ({ ...prev, isLoading: true, hasError: false, error: undefined }));

    try {
      await preloadComponent(componentId);
      setState(prev => ({ ...prev, isLoading: false, isLoaded: true, loadTime: performance.now() }));
      setRetryCount(0); // Reset retry count on success
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        hasError: true,
        error: error as Error,
      }));
    }
  }, [componentId, state.isLoaded, state.isLoading]);

  const preload = React.useCallback(async () => {
    try {
      await preloadComponent(componentId);
    } catch (error) {
      console.warn(`Failed to preload component ${componentId}:`, error);
    }
  }, [componentId]);

  const retry = React.useCallback(async () => {
    if (retryCount >= maxRetries) {
      setState(prev => ({
        ...prev,
        hasError: true,
        error: new Error(`Maximum retry attempts (${maxRetries}) exceeded`),
      }));
      return;
    }

    setState({
      isLoading: false,
      isLoaded: false,
      hasError: false,
      error: undefined,
    });
    
    setRetryCount(prev => prev + 1);
    
    // Add delay before retry
    setTimeout(() => {
      load();
    }, retryDelay * retryCount);
  }, [load, retryCount, maxRetries, retryDelay]);

  // Auto-load if component is available but not loaded
  useEffect(() => {
    if (autoLoad && Component && !state.isLoaded && !state.isLoading) {
      load();
    }
  }, [Component, state.isLoaded, state.isLoading, load, autoLoad]);

  return {
    Component,
    isLoading: state.isLoading,
    hasError: state.hasError,
    error: state.error || null,
    preload,
    retry,
  };
}

// Higher-order component with enhanced lazy loading
export function withLazyLoading<P extends object>(
  componentId: string,
  options?: {
    config?: Partial<LazyComponentConfig>;
    fallbackVariant?: 'skeleton' | 'spinner' | 'dots';
    autoLoad?: boolean;
  }
) {
  return function LazyWrapper(props: P) {
    const { Component, isLoading, hasError, error, retry } = useLazyComponent<P>(componentId, {
      autoLoad: options?.autoLoad,
    });

    if (isLoading) {
      const FallbackComponent = options?.config?.fallback || DefaultFallback;
      return <FallbackComponent variant={options?.fallbackVariant} />;
    }

    if (hasError || !Component) {
      const ErrorComponent = options?.config?.errorBoundary || DefaultErrorBoundary;
      return (
        <ErrorComponent 
          error={error || new Error('Component not found')} 
          retry={retry}
          componentName={componentId}
        />
      );
    }

    return <Component {...props} />;
  };
}

// Intersection Observer for viewport-based lazy loading with enhanced options
export function useViewportLazyLoad(
  componentId: string,
  options?: IntersectionObserverInit & { 
    preloadDistance?: number;
    rootMargin?: string;
    threshold?: number | number[];
    fallbackVariant?: 'skeleton' | 'spinner' | 'dots';
  }
) {
  const [shouldLoad, setShouldLoad] = React.useState(false);
  const elementRef = React.useRef<HTMLElement>(null);
  const { preloadDistance = 200, fallbackVariant = 'spinner', ...observerOptions } = options || {};

  React.useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting || entry.intersectionRatio > 0) {
            setShouldLoad(true);
            observer.disconnect();
          }
        });
      },
      {
        rootMargin: `${preloadDistance}px`,
        ...observerOptions,
      }
    );

    observer.observe(element);

    return () => observer.disconnect();
  }, [preloadDistance, observerOptions]);

  const { Component, isLoading, hasError, error, retry } = useLazyComponent(componentId);

  return {
    elementRef,
    Component: shouldLoad ? Component : null,
    isLoading: shouldLoad && isLoading,
    hasError: shouldLoad && hasError,
    error: shouldLoad ? error : null,
    retry,
    Placeholder: () => <DefaultFallback variant={fallbackVariant} />,
  };
}

// Advanced preloading manager with priority queue and network awareness
class AdvancedPreloadManager {
  private queue: Array<{
    componentId: string;
    priority: 'high' | 'normal' | 'low';
    timestamp: number;
    retryCount: number;
  }> = [];
  private isProcessing = false;
  private networkAware = true;
  private maxConcurrent = 3;
  private currentLoading = 0;
  private isClient = false;

  constructor() {
    // Check if we're on client side
    this.isClient = typeof window !== 'undefined';
  }

  addToQueue(componentId: string, priority: 'high' | 'normal' | 'low' = 'normal') {
    this.queue.push({
      componentId,
      priority,
      timestamp: this.isClient ? Date.now() : 0,
      retryCount: 0,
    });
    
    this.sortQueue();
    
    if (!this.isProcessing && this.currentLoading < this.maxConcurrent) {
      this.processQueue();
    }
  }

  private sortQueue() {
    const priorityOrder = { high: 0, normal: 1, low: 2 };
    this.queue.sort((a, b) => {
      // First by priority
      const priorityDiff = priorityOrder[a.priority] - priorityOrder[b.priority];
      if (priorityDiff !== 0) return priorityDiff;
      
      // Then by timestamp (older first)
      return a.timestamp - b.timestamp;
    });
  }

  private async processQueue() {
    this.isProcessing = true;

    while (this.queue.length > 0 && this.currentLoading < this.maxConcurrent) {
      const item = this.queue.shift()!;
      this.currentLoading++;
      
      // Process in parallel with concurrency control
      this.processItem(item).finally(() => {
        this.currentLoading--;
        
        // Continue processing if there are more items
        if (this.queue.length > 0 && !this.isProcessing) {
          this.processQueue();
        }
      });
    }

    this.isProcessing = false;
  }

  private async processItem(item: {
    componentId: string;
    priority: 'high' | 'normal' | 'low';
    timestamp: number;
    retryCount: number;
  }) {
    try {
      // Check network conditions if network-aware
      if (this.networkAware) {
        const connection = (navigator as NavigatorWithConnection).connection;
        if (connection) {
          // Adjust behavior based on network conditions
          if (connection.effectiveType === 'slow-2g' && item.priority !== 'high') {
            // Skip non-critical components on slow networks
            return;
          }
        }
      }

      await preloadComponent(item.componentId);
    } catch (error) {
      console.warn(`Failed to preload ${item.componentId}:`, error);
      
      // Retry logic
      if (item.retryCount < 2) {
        item.retryCount++;
        item.timestamp = this.isClient ? Date.now() : 0; // Update timestamp for retry
        this.queue.push(item);
        this.sortQueue();
      }
    }
  }

  setNetworkAware(aware: boolean) {
    this.networkAware = aware;
  }

  setMaxConcurrent(max: number) {
    this.maxConcurrent = Math.max(1, max);
  }

  clearQueue() {
    this.queue = [];
  }

  getQueueStatus() {
    return {
      queueLength: this.queue.length,
      isProcessing: this.isProcessing,
      currentLoading: this.currentLoading,
      maxConcurrent: this.maxConcurrent,
    };
  }
}

export const advancedPreloadManager = new AdvancedPreloadManager();

// Batch preloading with enhanced options
export async function preloadComponents(
  componentIds: string[],
  options?: {
    priority?: 'high' | 'normal' | 'low';
    concurrent?: number;
    networkAware?: boolean;
    timeout?: number;
  }
): Promise<void> {
  const {
    priority = 'normal',
    concurrent = 3,
    networkAware = true,
    timeout = 10000,
  } = options || {};

  // Configure manager
  advancedPreloadManager.setNetworkAware(networkAware);
  advancedPreloadManager.setMaxConcurrent(concurrent);

  // Add all components to queue
  componentIds.forEach(id => 
    advancedPreloadManager.addToQueue(id, priority)
  );
  
  // Wait for all components to be preloaded with timeout
  return new Promise((resolve, reject) => {
    const startTime = typeof window !== 'undefined' ? Date.now() : 0;
    const isClient = typeof window !== 'undefined';
    const timeoutId = setTimeout(() => {
      reject(new Error(`Preload timeout after ${timeout}ms`));
    }, timeout);

    const checkInterval = setInterval(() => {
      const status = advancedPreloadManager.getQueueStatus();
      
      if (status.queueLength === 0 && !status.isProcessing && status.currentLoading === 0) {
        clearTimeout(timeoutId);
        clearInterval(checkInterval);
        resolve();
      }
      
      // Check if we've exceeded the timeout
      if (isClient && Date.now() - startTime > timeout) {
        clearTimeout(timeoutId);
        clearInterval(checkInterval);
        reject(new Error(`Preload timeout after ${timeout}ms`));
      }
    }, 100);
  });
}

// Enhanced performance monitoring for lazy loading
export function useLazyLoadingMetrics() {
  const metrics = usePerformanceOptimizationStore(state => state.metrics);
  
  const getComponentMetrics = React.useCallback((componentId: string) => {
    return metrics.filter(metric => 
      metric.name === `component-load-${componentId}` || 
      metric.name === `component-load-error-${componentId}`
    );
  }, [metrics]);

  const getAverageLoadTime = React.useCallback((componentId: string) => {
    const componentMetrics = getComponentMetrics(componentId)
      .filter(metric => !metric.name.includes('error'));
    
    if (componentMetrics.length === 0) return 0;
    
    const total = componentMetrics.reduce((sum, metric) => sum + metric.value, 0);
    return total / componentMetrics.length;
  }, [getComponentMetrics]);

  const getLoadSuccessRate = React.useCallback((componentId: string) => {
    const componentMetrics = getComponentMetrics(componentId);
    if (componentMetrics.length === 0) return 0;
    
    const successful = componentMetrics.filter(metric => 
      !metric.name.includes('error') && metric.rating !== 'poor'
    ).length;
    
    return (successful / componentMetrics.length) * 100;
  }, [getComponentMetrics]);

  const getComponentStats = React.useCallback((componentId: string) => {
    const metadata = getComponentMetadata(componentId);
    const componentMetrics = getComponentMetrics(componentId);
    
    return {
      metadata,
      metrics: componentMetrics,
      averageLoadTime: getAverageLoadTime(componentId),
      successRate: getLoadSuccessRate(componentId),
      totalLoads: componentMetrics.filter(m => !m.name.includes('error')).length,
      totalErrors: componentMetrics.filter(m => m.name.includes('error')).length,
    };
  }, [getComponentMetrics, getAverageLoadTime, getLoadSuccessRate]);

  const getTopSlowComponents = React.useCallback((limit: number = 5) => {
    const componentIds = Array.from(componentMetadata.keys());
    const stats = componentIds.map(id => ({
      componentId: id,
      averageLoadTime: getAverageLoadTime(id),
      loadCount: getComponentMetadata(id)?.loadCount || 0,
    }));
    
    return stats
      .filter(stat => stat.averageLoadTime > 0)
      .sort((a, b) => b.averageLoadTime - a.averageLoadTime)
      .slice(0, limit);
  }, [getAverageLoadTime]);

  return {
    getComponentMetrics,
    getAverageLoadTime,
    getLoadSuccessRate,
    getComponentStats,
    getTopSlowComponents,
    getAllMetadata: () => Array.from(componentMetadata.entries()),
  };
}
