import { useState, useEffect, useCallback, useRef } from 'react';
import { preloadComponent } from '../utils/codeSplitting';

// Type for lazy loading state
interface LazyLoadingState {
  isLoading: boolean;
  isLoaded: boolean;
  error: Error | null;
}

// Type for import function
type ImportFunction<T = any> = () => Promise<{ default: React.ComponentType<T> }>;

// Hook for managing lazy component loading
export const useLazyComponent = <T = any>(
  importFn: ImportFunction<T>,
  preload = false
) => {
  const [state, setState] = useState<LazyLoadingState>({
    isLoading: false,
    isLoaded: false,
    error: null,
  });

  const componentRef = useRef<React.ComponentType<T> | null>(null);
  const importFnRef = useRef(importFn);

  // Update import function ref
  importFnRef.current = importFn;

  // Load component function
  const loadComponent = useCallback(async () => {
    if (componentRef.current) {
      return componentRef.current;
    }

    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const module = await importFnRef.current();
      componentRef.current = module.default;
      
      setState({
        isLoading: false,
        isLoaded: true,
        error: null,
      });

      return module.default;
    } catch (error) {
      setState({
        isLoading: false,
        isLoaded: false,
        error: error as Error,
      });
      throw error;
    }
  }, []);

  // Preload on mount if requested
  useEffect(() => {
    if (preload) {
      loadComponent().catch(() => {
        // Preload errors are non-critical
      });
    }
  }, [preload, loadComponent]);

  return {
    ...state,
    component: componentRef.current,
    loadComponent,
  };
};

// Hook for batch lazy loading
export const useBatchLazyLoading = (
  importFunctions: ImportFunction[],
  preloadAll = false
) => {
  const [loadingStates, setLoadingStates] = useState<LazyLoadingState[]>(
    importFunctions.map(() => ({
      isLoading: false,
      isLoaded: false,
      error: null,
    }))
  );

  const componentsRef = useRef<(React.ComponentType<any> | null)[]>(
    new Array(importFunctions.length).fill(null)
  );

  // Load specific component by index
  const loadComponent = useCallback(async (index: number) => {
    if (index < 0 || index >= importFunctions.length) {
      throw new Error('Invalid component index');
    }

    if (componentsRef.current[index]) {
      return componentsRef.current[index];
    }

    setLoadingStates(prev => 
      prev.map((state, i) => 
        i === index 
          ? { ...state, isLoading: true, error: null }
          : state
      )
    );

    try {
      const module = await importFunctions[index]();
      componentsRef.current[index] = module.default;
      
      setLoadingStates(prev => 
        prev.map((state, i) => 
          i === index 
            ? { isLoading: false, isLoaded: true, error: null }
            : state
        )
      );

      return module.default;
    } catch (error) {
      setLoadingStates(prev => 
        prev.map((state, i) => 
          i === index 
            ? { isLoading: false, isLoaded: false, error: error as Error }
            : state
        )
      );
      throw error;
    }
  }, [importFunctions]);

  // Load all components
  const loadAllComponents = useCallback(async () => {
    const promises = importFunctions.map((_, index) => 
      loadComponent(index).catch(() => null)
    );
    
    return Promise.all(promises);
  }, [importFunctions, loadComponent]);

  // Preload all on mount if requested
  useEffect(() => {
    if (preloadAll) {
      loadAllComponents().catch(() => {
        // Preload errors are non-critical
      });
    }
  }, [preloadAll, loadAllComponents]);

  return {
    loadingStates,
    components: componentsRef.current,
    loadComponent,
    loadAllComponents,
  };
};

// Hook for intersection observer based lazy loading
export const useIntersectionLazyLoading = <T = any>(
  importFn: ImportFunction<T>,
  options: IntersectionObserverInit = {}
) => {
  const [isVisible, setIsVisible] = useState(false);
  const elementRef = useRef<HTMLElement | null>(null);
  const observerRef = useRef<IntersectionObserver | null>(null);

  const { component, loadComponent, isLoading, isLoaded, error } = useLazyComponent(
    importFn,
    false
  );

  // Set up intersection observer
  useEffect(() => {
    if (!elementRef.current || typeof window === 'undefined') {
      return;
    }

    observerRef.current = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !isVisible) {
          setIsVisible(true);
          loadComponent().catch(() => {});
        }
      },
      {
        rootMargin: '50px',
        threshold: 0.1,
        ...options,
      }
    );

    observerRef.current.observe(elementRef.current);

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [isVisible, loadComponent, options]);

  // Ref callback to set element
  const setRef = useCallback((element: HTMLElement | null) => {
    elementRef.current = element;
  }, []);

  return {
    ref: setRef,
    isVisible,
    component,
    isLoading,
    isLoaded,
    error,
    loadComponent,
  };
};

// Hook for route-based preloading
export const useRoutePreloading = (
  routeImports: Record<string, ImportFunction>,
  currentPath: string
) => {
  const [preloadedRoutes, setPreloadedRoutes] = useState<Set<string>>(new Set());

  // Preload route based on current path
  const preloadRoute = useCallback(async (path: string) => {
    if (preloadedRoutes.has(path) || !routeImports[path]) {
      return;
    }

    try {
      await preloadComponent(routeImports[path]);
      setPreloadedRoutes(prev => new Set(prev).add(path));
    } catch (error) {
      console.warn(`Failed to preload route ${path}:`, error);
    }
  }, [routeImports, preloadedRoutes]);

  // Preload likely next routes based on current path
  useEffect(() => {
    const preloadStrategies: Record<string, string[]> = {
      '/': ['/settings', '/help'],
      '/chat': ['/settings', '/analytics'],
      '/settings': ['/chat', '/profile'],
      '/analytics': ['/chat', '/settings'],
      '/help': ['/chat'],
      '/profile': ['/settings', '/chat'],
    };

    const routesToPreload = preloadStrategies[currentPath] || [];
    
    // Preload with a small delay to not block current route
    const timeoutId = setTimeout(() => {
      routesToPreload.forEach(route => {
        preloadRoute(route).catch(() => {});
      });
    }, 100);

    return () => clearTimeout(timeoutId);
  }, [currentPath, preloadRoute]);

  return {
    preloadedRoutes: Array.from(preloadedRoutes),
    preloadRoute,
  };
};

// Hook for managing loading priorities
export const useLoadingPriority = () => {
  const [highPriorityQueue, setHighPriorityQueue] = useState<(() => Promise<any>)[]>([]);
  const [lowPriorityQueue, setLowPriorityQueue] = useState<(() => Promise<any>)[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);

  // Add to high priority queue
  const addHighPriority = useCallback((loadFn: () => Promise<any>) => {
    setHighPriorityQueue(prev => [...prev, loadFn]);
  }, []);

  // Add to low priority queue
  const addLowPriority = useCallback((loadFn: () => Promise<any>) => {
    setLowPriorityQueue(prev => [...prev, loadFn]);
  }, []);

  // Process queues
  const processQueues = useCallback(async () => {
    if (isProcessing) return;

    setIsProcessing(true);

    try {
      // Process high priority first
      while (highPriorityQueue.length > 0) {
        const loadFn = highPriorityQueue.shift();
        if (loadFn) {
          await loadFn().catch(() => {});
        }
        setHighPriorityQueue(prev => prev.slice(1));
      }

      // Then process low priority with idle callback
      while (lowPriorityQueue.length > 0) {
        if (typeof requestIdleCallback !== 'undefined') {
          await new Promise(resolve => {
            requestIdleCallback(() => {
              const loadFn = lowPriorityQueue.shift();
              if (loadFn) {
                loadFn().catch(() => {}).finally(resolve);
              } else {
                resolve(undefined);
              }
            });
          });
        } else {
          // Fallback for browsers without requestIdleCallback
          const loadFn = lowPriorityQueue.shift();
          if (loadFn) {
            await loadFn().catch(() => {});
          }
        }
        setLowPriorityQueue(prev => prev.slice(1));
      }
    } finally {
      setIsProcessing(false);
    }
  }, [highPriorityQueue, lowPriorityQueue, isProcessing]);

  // Auto-process queues when items are added
  useEffect(() => {
    if ((highPriorityQueue.length > 0 || lowPriorityQueue.length > 0) && !isProcessing) {
      processQueues();
    }
  }, [highPriorityQueue.length, lowPriorityQueue.length, isProcessing, processQueues]);

  return {
    addHighPriority,
    addLowPriority,
    isProcessing,
    queueSizes: {
      high: highPriorityQueue.length,
      low: lowPriorityQueue.length,
    },
  };
};