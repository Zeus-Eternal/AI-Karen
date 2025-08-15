import { lazy, ComponentType } from 'react';

// Type for dynamic import functions
type ImportFunction<T = any> = () => Promise<{ default: ComponentType<T> }>;

// Utility for creating lazy components with retry logic
export const createLazyComponent = <T = any>(
  importFn: ImportFunction<T>,
  retries = 3,
  retryDelay = 1000
): React.LazyExoticComponent<ComponentType<T>> => {
  return lazy(() => {
    return new Promise<{ default: ComponentType<T> }>((resolve, reject) => {
      const attemptImport = (attemptsLeft: number) => {
        importFn()
          .then(resolve)
          .catch((error) => {
            if (attemptsLeft <= 0) {
              reject(error);
              return;
            }

            console.warn(
              `Failed to load component, retrying... (${attemptsLeft} attempts left)`,
              error
            );

            setTimeout(() => {
              attemptImport(attemptsLeft - 1);
            }, retryDelay);
          });
      };

      attemptImport(retries);
    });
  });
};

// Preload utility for components
export const preloadComponent = <T = any>(
  importFn: ImportFunction<T>
): Promise<{ default: ComponentType<T> }> => {
  return importFn();
};

// Batch preloader for multiple components
export const preloadComponents = async (
  importFunctions: ImportFunction[]
): Promise<void> => {
  try {
    await Promise.all(importFunctions.map(fn => fn()));
  } catch (error) {
    console.warn('Some components failed to preload:', error);
  }
};

// Route-based code splitting configuration
export interface RouteConfig {
  path: string;
  component: React.LazyExoticComponent<ComponentType<any>>;
  preload?: boolean;
  chunkName?: string;
}

// Create route configurations with lazy loading
export const createRouteConfig = (routes: {
  [key: string]: {
    importFn: ImportFunction;
    preload?: boolean;
    chunkName?: string;
  };
}): RouteConfig[] => {
  return Object.entries(routes).map(([path, config]) => ({
    path,
    component: createLazyComponent(config.importFn),
    preload: config.preload,
    chunkName: config.chunkName,
  }));
};

// Intersection Observer based lazy loading for components
export class LazyComponentLoader {
  private static instance: LazyComponentLoader;
  private observer: IntersectionObserver | null = null;
  private loadedComponents = new Set<string>();

  static getInstance(): LazyComponentLoader {
    if (!LazyComponentLoader.instance) {
      LazyComponentLoader.instance = new LazyComponentLoader();
    }
    return LazyComponentLoader.instance;
  }

  private constructor() {
    if (typeof window !== 'undefined' && 'IntersectionObserver' in window) {
      this.observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              const element = entry.target as HTMLElement;
              const componentId = element.dataset.componentId;
              const importFn = element.dataset.importFn;

              if (componentId && importFn && !this.loadedComponents.has(componentId)) {
                this.loadComponent(componentId, importFn);
                this.observer?.unobserve(element);
              }
            }
          });
        },
        {
          rootMargin: '50px', // Start loading 50px before component comes into view
          threshold: 0.1,
        }
      );
    }
  }

  private async loadComponent(componentId: string, importFnString: string): Promise<void> {
    try {
      // This would need to be implemented based on your specific import strategy
      // For now, we'll just mark it as loaded
      this.loadedComponents.add(componentId);
      console.log(`Lazy loaded component: ${componentId}`);
    } catch (error) {
      console.error(`Failed to lazy load component ${componentId}:`, error);
    }
  }

  observeElement(element: HTMLElement, componentId: string, importFn: string): void {
    if (this.observer && !this.loadedComponents.has(componentId)) {
      element.dataset.componentId = componentId;
      element.dataset.importFn = importFn;
      this.observer.observe(element);
    }
  }

  unobserveElement(element: HTMLElement): void {
    if (this.observer) {
      this.observer.unobserve(element);
    }
  }

  destroy(): void {
    if (this.observer) {
      this.observer.disconnect();
      this.observer = null;
    }
    this.loadedComponents.clear();
  }
}

// Hook for using lazy component loader
export const useLazyComponentLoader = () => {
  return LazyComponentLoader.getInstance();
};

// Bundle analysis utilities
export const getBundleInfo = () => {
  if (typeof window !== 'undefined' && (window as any).__webpack_require__) {
    const webpackRequire = (window as any).__webpack_require__;
    
    return {
      loadedChunks: Object.keys(webpackRequire.cache || {}),
      chunkLoadingGlobal: (window as any).webpackChunkName,
    };
  }
  
  return null;
};

// Performance monitoring for code splitting
export const trackChunkLoad = (chunkName: string, startTime: number) => {
  const endTime = performance.now();
  const loadTime = endTime - startTime;
  
  console.log(`Chunk "${chunkName}" loaded in ${loadTime.toFixed(2)}ms`);
  
  // Send to analytics if available
  if (typeof window !== 'undefined' && (window as any).gtag) {
    (window as any).gtag('event', 'chunk_load', {
      chunk_name: chunkName,
      load_time: Math.round(loadTime),
    });
  }
};

// Prefetch utility for critical chunks
export const prefetchChunk = (chunkName: string): void => {
  if (typeof document !== 'undefined') {
    const link = document.createElement('link');
    link.rel = 'prefetch';
    link.href = `/${chunkName}.js`; // Adjust path as needed
    document.head.appendChild(link);
  }
};

// Preload utility for critical chunks
export const preloadChunk = (chunkName: string): void => {
  if (typeof document !== 'undefined') {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.as = 'script';
    link.href = `/${chunkName}.js`; // Adjust path as needed
    document.head.appendChild(link);
  }
};