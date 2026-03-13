/**
 * Lazy Loading Utilities
 * Utilities for lazy loading components and resources
 */

import React, { Suspense, lazy, ComponentType, ReactNode } from 'react';
import { LazyComponentConfig, LazyLoadState, UseLazyComponentResult } from '../types';
import { usePerformanceOptimizationStore } from '../store/performanceOptimizationStore';

// Default fallback component
const DefaultFallback: React.FC = () => (
  <div className="flex items-center justify-center p-8">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
  </div>
);

// Default error boundary component
const DefaultErrorBoundary: ComponentType<{ error: Error; retry: () => void }> = ({ error, retry }) => (
  <div className="flex flex-col items-center justify-center p-8 text-center">
    <div className="text-red-500 mb-4">Failed to load component</div>
    <div className="text-sm text-gray-600 mb-4">{error.message}</div>
    <button 
      onClick={retry}
      className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
    >
      Retry
    </button>
  </div>
);

// Error boundary wrapper
interface LazyErrorBoundaryProps {
  children: ReactNode;
  fallback: ComponentType<{ error: Error; retry: () => void }>;
}

class LazyErrorBoundary extends React.Component<LazyErrorBoundaryProps, { hasError: boolean; error: Error | null }> {
  constructor(props: LazyErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Lazy component error:', error, errorInfo);
  }

  render(): ReactNode {
    if (this.state.hasError && this.state.error) {
      const FallbackComponent = this.props.fallback;
      return React.createElement(
        FallbackComponent,
        {
          error: this.state.error,
          retry: () => this.setState({ hasError: false, error: null })
        }
      );
    }

    return this.props.children;
  }
}

// Lazy component registry
const lazyComponentRegistry = new Map<string, ComponentType<Record<string, unknown>>>();
const lazyComponentPromises = new Map<string, Promise<unknown>>();

// Register a lazy component
export function registerLazyComponent(config: LazyComponentConfig): void {
  const {
    componentId,
    importPath,
    fallback = DefaultFallback,
    errorBoundary = DefaultErrorBoundary,
    dependencies = [],
  } = config;

  // Create lazy component with custom loading and error handling
  const LazyComponent = lazy(() => {
    // Record start time for performance measurement
    const startTime = performance.now();

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
      .then(module => {
        const loadTime = performance.now() - startTime;
        
        // Update store with load time
        const store = usePerformanceOptimizationStore.getState();
        store.measureMetric({
          name: `component-load-${componentId}`,
          value: loadTime,
          unit: 'ms',
          timestamp: new Date(),
          rating: loadTime < 100 ? 'good' : loadTime < 300 ? 'needs-improvement' : 'poor',
          threshold: { good: 100, poor: 300 },
        });

        return module.default || module;
      });
  });

  // Wrap with error boundary and suspense
  const WrappedComponent: ComponentType<Record<string, unknown>> = (props: Record<string, unknown>) => (
    <LazyErrorBoundary fallback={errorBoundary}>
      <Suspense fallback={React.createElement(fallback)}>
        <LazyComponent {...props} />
      </Suspense>
    </LazyErrorBoundary>
  );

  // Register component
  lazyComponentRegistry.set(componentId, WrappedComponent);

  // Preload if specified
  if (config.preload) {
    preloadComponent(componentId);
  }
}

// Get a lazy component
export function getLazyComponent(componentId: string): ComponentType<Record<string, unknown>> | null {
  return lazyComponentRegistry.get(componentId) || null;
}

// Preload a component
export async function preloadComponent(componentId: string): Promise<void> {
  const component = lazyComponentRegistry.get(componentId);
  if (!component) {
    throw new Error(`Component ${componentId} not found in registry`);
  }

  // Trigger lazy import by attempting to render component
  // This will cause the component to be loaded and cached
  try {
    // This is a simplified preload - in a real implementation,
    // you'd need to trigger the actual import
    await new Promise(resolve => setTimeout(resolve, 100));
  } catch (error) {
    console.warn(`Failed to preload component ${componentId}:`, error);
  }
}

// Hook for using lazy components
export function useLazyComponent<T = unknown>(
  componentId: string
): UseLazyComponentResult<T> {
  const [state, setState] = React.useState<LazyLoadState>({
    isLoading: false,
    isLoaded: false,
    hasError: false,
    error: undefined,
  });

  const Component = getLazyComponent(componentId);

  const load = React.useCallback(async () => {
    if (state.isLoaded || state.isLoading) return;

    setState(prev => ({ ...prev, isLoading: true, hasError: false, error: undefined }));

    try {
      await preloadComponent(componentId);
      setState(prev => ({ ...prev, isLoading: false, isLoaded: true }));
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
    setState({
      isLoading: false,
      isLoaded: false,
      hasError: false,
      error: undefined,
    });
    await load();
  }, [load]);

  // Auto-load if component is available but not loaded
  React.useEffect(() => {
    if (Component && !state.isLoaded && !state.isLoading) {
      load();
    }
  }, [Component, state.isLoaded, state.isLoading, load]);

  return {
    Component: Component as ComponentType<T> | null,
    isLoading: state.isLoading,
    hasError: state.hasError,
    error: state.error || null,
    preload,
    retry,
  };
}

// Higher-order component for lazy loading
export function withLazyLoading<P extends object>(
  componentId: string,
  config?: Partial<LazyComponentConfig>
) {
  return function LazyWrapper(props: P) {
    const { Component, isLoading, hasError, error, retry } = useLazyComponent<P>(componentId);

    if (isLoading) {
      const FallbackComponent = config?.fallback || DefaultFallback;
      return React.createElement(FallbackComponent);
    }

    if (hasError || !Component) {
      const ErrorComponent = config?.errorBoundary || DefaultErrorBoundary;
      return React.createElement(
        ErrorComponent,
        {
          error: error || new Error('Component not found'),
          retry: retry
        }
      );
    }

    return React.createElement(Component, props);
  };
}

// Intersection Observer for viewport-based lazy loading
export function useViewportLazyLoad(
  componentId: string,
  options?: IntersectionObserverInit & { preloadDistance?: number }
) {
  const [shouldLoad, setShouldLoad] = React.useState(false);
  const elementRef = React.useRef<HTMLElement>(null);
  const { preloadDistance = 200, ...observerOptions } = options || {};

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
  };
}

// Priority-based preloading manager
class PreloadManager {
  private queue: Array<{ componentId: string; priority: 'high' | 'normal' | 'low' }> = [];
  private isProcessing = false;

  addToQueue(componentId: string, priority: 'high' | 'normal' | 'low' = 'normal') {
    this.queue.push({ componentId, priority });
    this.queue.sort((a, b) => {
      const priorityOrder = { high: 0, normal: 1, low: 2 };
      return priorityOrder[a.priority] - priorityOrder[b.priority];
    });

    if (!this.isProcessing) {
      this.processQueue();
    }
  }

  // Public getters for checking status
  getQueueLength(): number {
    return this.queue.length;
  }

  getIsProcessing(): boolean {
    return this.isProcessing;
  }

  private async processQueue() {
    this.isProcessing = true;

    while (this.queue.length > 0) {
      const { componentId } = this.queue.shift()!;
      
      try {
        await preloadComponent(componentId);
      } catch (error) {
        console.warn(`Failed to preload ${componentId}:`, error);
      }

      // Add small delay between preloads to avoid blocking main thread
      await new Promise(resolve => setTimeout(resolve, 50));
    }

    this.isProcessing = false;
  }
}

export const preloadManager = new PreloadManager();

// Utility function to create lazy component configs
export function createLazyComponentConfig(
  componentId: string,
  importPath: string,
  options?: Partial<LazyComponentConfig>
): LazyComponentConfig {
  return {
    componentId,
    importPath,
    priority: 'normal',
    preload: false,
    ...options,
  };
}

// Batch preloading for multiple components
export async function preloadComponents(
  componentIds: string[],
  priority: 'high' | 'normal' | 'low' = 'normal'
): Promise<void> {
  componentIds.forEach(id => 
    preloadManager.addToQueue(id, priority)
  );
  
  // Wait for all components to be preloaded
  return new Promise((resolve) => {
    const checkInterval = setInterval(() => {
      if (preloadManager.getQueueLength() === 0 && !preloadManager.getIsProcessing()) {
        clearInterval(checkInterval);
        resolve();
      }
    }, 100);
  });
}

// Performance monitoring for lazy loading
export function useLazyLoadingMetrics() {
  const metrics = usePerformanceOptimizationStore(state => state.metrics);
  
  const getComponentMetrics = React.useCallback((componentId: string) => {
    return metrics.filter(metric => metric.name === `component-load-${componentId}`);
  }, [metrics]);

  const getAverageLoadTime = React.useCallback((componentId: string) => {
    const componentMetrics = getComponentMetrics(componentId);
    if (componentMetrics.length === 0) return 0;
    
    const total = componentMetrics.reduce((sum, metric) => sum + metric.value, 0);
    return total / componentMetrics.length;
  }, [getComponentMetrics]);

  const getLoadSuccessRate = React.useCallback((componentId: string) => {
    const componentMetrics = getComponentMetrics(componentId);
    if (componentMetrics.length === 0) return 0;
    
    const successful = componentMetrics.filter(metric => metric.rating !== 'poor').length;
    return (successful / componentMetrics.length) * 100;
  }, [getComponentMetrics]);

  return {
    getComponentMetrics,
    getAverageLoadTime,
    getLoadSuccessRate,
  };
}
