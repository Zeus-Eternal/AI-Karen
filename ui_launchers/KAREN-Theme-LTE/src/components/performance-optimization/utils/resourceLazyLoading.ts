/**
 * Resource Lazy Loading Utilities
 * Utilities for lazy loading images, scripts, styles, fonts, and other resources
 */

import React from 'react';
import { ResourceConfig } from '../types';
import { usePerformanceOptimizationStore } from '../store/performanceOptimizationStore';

type DocumentFontsWithAdd = FontFaceSet & {
  add(font: FontFace): void;
};

// Resource registry
const resourceRegistry = new Map<string, ResourceConfig>();
const loadedResources = new Map<string, unknown>();
const loadingPromises = new Map<string, Promise<unknown>>();

// Default resource configurations
const DEFAULT_RESOURCE_CONFIGS: Partial<ResourceConfig> = {
  priority: 'normal',
  preload: false,
  cacheStrategy: 'memory',
  compression: true,
};

// Register a resource
export function registerResource(config: ResourceConfig): void {
  const resourceConfig = { ...DEFAULT_RESOURCE_CONFIGS, ...config };
  resourceRegistry.set(config.id, resourceConfig);
}

// Register multiple resources
export function registerResources(configs: ResourceConfig[]): void {
  configs.forEach(config => registerResource(config));
}

// Get resource configuration
export function getResourceConfig(id: string): ResourceConfig | undefined {
  return resourceRegistry.get(id);
}

// Get all resources
export function getAllResources(): ResourceConfig[] {
  return Array.from(resourceRegistry.values());
}

// Get resources by type
export function getResourcesByType(type: ResourceConfig['type']): ResourceConfig[] {
  return Array.from(resourceRegistry.values()).filter(resource => resource.type === type);
}

// Load a resource
export async function loadResource(id: string): Promise<unknown> {
  // Check if already loaded
  if (loadedResources.has(id)) {
    return loadedResources.get(id);
  }

  // Check if currently loading
  if (loadingPromises.has(id)) {
    return loadingPromises.get(id);
  }

  const config = getResourceConfig(id);
  if (!config) {
    throw new Error(`Resource ${id} not found in registry`);
  }

  const startTime = performance.now();

  // Create loading promise
  const loadingPromise = loadResourceByType(config)
    .then(resource => {
      const loadTime = performance.now() - startTime;
      
      // Record performance metric
      const store = usePerformanceOptimizationStore.getState();
      store.measureMetric({
        name: `resource-load-${id}`,
        value: loadTime,
        unit: 'ms',
        timestamp: new Date(),
        rating: loadTime < 100 ? 'good' : loadTime < 300 ? 'needs-improvement' : 'poor',
        threshold: { good: 100, poor: 300 },
      });

      // Cache the resource
      loadedResources.set(id, resource);
      loadingPromises.delete(id);

      return resource;
    })
    .catch(error => {
      loadingPromises.delete(id);
      throw error;
    });

  loadingPromises.set(id, loadingPromise);
  return loadingPromise;
}

// Load resource by type
async function loadResourceByType(config: ResourceConfig): Promise<unknown> {
  switch (config.type) {
    case 'image':
      return loadImageResource(config);
    case 'script':
      return loadScriptResource(config);
    case 'style':
      return loadStyleResource(config);
    case 'font':
      return loadFontResource(config);
    case 'data':
      return loadDataResource(config);
    default:
      throw new Error(`Unsupported resource type: ${config.type}`);
  }
}

// Load image resource
async function loadImageResource(config: ResourceConfig): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error(`Failed to load image: ${config.url}`));
    
    // Apply loading strategies
    if (config.compression && supportsWebP()) {
      // Try WebP version first
      const webpUrl = config.url.replace(/\.(jpg|jpeg|png)$/i, '.webp');
      img.src = webpUrl;
    } else {
      img.src = config.url;
    }

    // Set loading strategy
    img.loading = config.priority === 'high' ? 'eager' : 'lazy';
    img.decoding = 'async';
  });
}

// Load script resource
async function loadScriptResource(config: ResourceConfig): Promise<void> {
  return new Promise((resolve, reject) => {
    // Check if script already exists
    const existingScript = document.querySelector(`script[src="${config.url}"]`);
    if (existingScript) {
      resolve();
      return;
    }

    const script = (document as Document).createElement('script');
    script.src = config.url;
    script.async = true;
    script.defer = true;
    
    // Note: priority is not a standard property, but we can use other techniques
    if (config.priority === 'high') {
      script.setAttribute('importance', 'high');
    }

    script.onload = () => resolve();
    script.onerror = () => reject(new Error(`Failed to load script: ${config.url}`));

    (document as Document).head.appendChild(script);
  });
}

// Load style resource
async function loadStyleResource(config: ResourceConfig): Promise<void> {
  return new Promise((resolve, reject) => {
    // Check if style already exists
    const existingLink = document.querySelector(`link[href="${config.url}"]`);
    if (existingLink) {
      resolve();
      return;
    }

    const link = (document as Document).createElement('link');
    link.rel = 'stylesheet';
    link.href = config.url;
    
    if (config.priority === 'high') {
      link.media = 'all';
    }

    link.onload = () => resolve();
    link.onerror = () => reject(new Error(`Failed to load style: ${config.url}`));

    (document as Document).head.appendChild(link);
  });
}

// Load font resource
async function loadFontResource(config: ResourceConfig): Promise<void> {
  return new Promise((resolve, reject) => {
    if ('fonts' in document) {
      // Use modern Font Face API
      const fontFace = new FontFace(
        config.id,
        `url(${config.url})`,
        {
          weight: 'normal',
          style: 'normal',
        }
      );

      fontFace.load()
        .then(() => {
          (document.fonts as DocumentFontsWithAdd).add(fontFace);
          resolve();
        })
        .catch(reject);
    } else {
      // Fallback to CSS method
      const styleElement = (document as Document).createElement('style');
      styleElement.textContent = `
        @font-face {
          font-family: '${config.id}';
          src: url('${config.url}');
        }
      `;
      
      (document as Document).head.appendChild(styleElement);
      resolve();
    }
  });
}

// Load data resource
async function loadDataResource(config: ResourceConfig): Promise<unknown> {
  const response = await fetch(config.url, {
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to load data: ${config.url} (${response.status})`);
  }

  return response.json();
}

// Preload a resource
export async function preloadResource(id: string): Promise<void> {
  try {
    await loadResource(id);
  } catch (error) {
    console.warn(`Failed to preload resource ${id}:`, error);
  }
}

// Preload multiple resources
export async function preloadResources(ids: string[]): Promise<void> {
  const promises = ids.map(id => preloadResource(id));
  await Promise.allSettled(promises);
}

// Preload resources by priority
export async function preloadResourcesByPriority(
  priority: 'high' | 'normal' | 'low'
): Promise<void> {
  const resources = Array.from(resourceRegistry.values())
    .filter(resource => resource.priority === priority)
    .map(resource => resource.id);

  await preloadResources(resources);
}

// Intersection Observer for viewport-based resource loading
export function useViewportResourceLoading(
  resourceIds: string[],
  options?: IntersectionObserverInit & { preloadDistance?: number }
) {
  void resourceIds;
  const [loadedResources, setLoadedResources] = React.useState<Set<string>>(new Set());
  const elementRefs = React.useRef<Map<string, HTMLElement>>(new Map());
  const { preloadDistance = 200, ...observerOptions } = options || {};

  React.useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const resourceId = entry.target.getAttribute('data-resource-id');
          if (!resourceId) return;

          if (entry.isIntersecting || entry.intersectionRatio > 0) {
            // Resource is near viewport, load it
            loadResource(resourceId)
              .then(() => {
                setLoadedResources(prev => new Set([...prev, resourceId]));
              })
              .catch(error => {
                console.warn(`Failed to load resource ${resourceId}:`, error);
              });
          }
        });
      },
      {
        rootMargin: `${preloadDistance}px`,
        ...observerOptions,
      }
    );

    // Observe all resource elements
    elementRefs.current.forEach((element) => {
      observer.observe(element);
    });

    return () => observer.disconnect();
  }, [preloadDistance, observerOptions]);

  // Function to get ref for a specific resource
  const getResourceRef = React.useCallback((resourceId: string) => {
    return (element: HTMLElement | null) => {
      if (element) {
        elementRefs.current.set(resourceId, element);
        element.setAttribute('data-resource-id', resourceId);
      } else {
        elementRefs.current.delete(resourceId);
      }
    };
  }, []);

  return {
    getResourceRef,
    loadedResources,
    isLoaded: (resourceId: string) => loadedResources.has(resourceId),
  };
}

// Progressive image loading
export function useProgressiveImage(
  src: string,
  placeholder?: string,
  options?: { quality?: number; format?: 'webp' | 'avif' | 'auto' }
) {
  const [imageSrc, setImageSrc] = React.useState(placeholder || '');
  const [isLoading, setIsLoading] = React.useState(true);
  const [hasError, setHasError] = React.useState(false);

  React.useEffect(() => {
    setIsLoading(true);
    setHasError(false);

    const img = new Image();
    
    img.onload = () => {
      setImageSrc(src);
      setIsLoading(false);
    };
    
    img.onerror = () => {
      setHasError(true);
      setIsLoading(false);
    };

    // Determine optimal format
    let optimizedSrc = src;
    const { quality = 80, format = 'auto' } = options || {};

    if (format === 'auto') {
      if (supportsAVIF()) {
        optimizedSrc = src.replace(/\.(jpg|jpeg|png)$/i, '.avif');
      } else if (supportsWebP()) {
        optimizedSrc = src.replace(/\.(jpg|jpeg|png)$/i, '.webp');
      }
    } else if (format === 'webp') {
      optimizedSrc = src.replace(/\.(jpg|jpeg|png)$/i, '.webp');
    } else if (format === 'avif') {
      optimizedSrc = src.replace(/\.(jpg|jpeg|png)$/i, '.avif');
    }

    // Add quality parameter if supported
    if (quality !== 100) {
      optimizedSrc += `?quality=${quality}`;
    }

    img.src = optimizedSrc;
  }, [src, options]);

  return {
    src: imageSrc,
    isLoading,
    hasError,
  };
}

// Resource cache management
class ResourceCache {
  private cache = new Map<string, { resource: unknown; timestamp: number; ttl: number }>();
  private defaultTTL = 10 * 60 * 1000; // 10 minutes

  set(id: string, resource: unknown, ttl?: number): void {
    this.cache.set(id, {
      resource,
      timestamp: Date.now(),
      ttl: ttl || this.defaultTTL,
    });
  }

  get(id: string): unknown | null {
    const entry = this.cache.get(id);
    if (!entry) return null;

    const now = Date.now();
    if (now - entry.timestamp > entry.ttl) {
      this.cache.delete(id);
      return null;
    }

    return entry.resource;
  }

  has(id: string): boolean {
    const entry = this.cache.get(id);
    if (!entry) return false;

    const now = Date.now();
    if (now - entry.timestamp > entry.ttl) {
      this.cache.delete(id);
      return false;
    }

    return true;
  }

  clear(): void {
    this.cache.clear();
  }

  delete(id: string): boolean {
    return this.cache.delete(id);
  }

  size(): number {
    return this.cache.size;
  }

  cleanup(): void {
    const now = Date.now();
    for (const [id, entry] of this.cache.entries()) {
      if (now - entry.timestamp > entry.ttl) {
        this.cache.delete(id);
      }
    }
  }
}

export const resourceCache = new ResourceCache();

// Enhanced resource loading with caching
export async function loadResourceWithCache(id: string): Promise<unknown> {
  // Check cache first
  if (resourceCache.has(id)) {
    const cachedResource = resourceCache.get(id);
    if (cachedResource) {
      return cachedResource;
    }
  }

  // Load from network
  const resource = await loadResource(id);

  // Cache resource
  const config = getResourceConfig(id);
  if (config?.cacheStrategy !== 'memory') {
    resourceCache.set(id, resource);
  }

  return resource;
}

// Resource performance monitoring
export function useResourcePerformanceMetrics() {
  const metrics = usePerformanceOptimizationStore(state => state.metrics);

  const getResourceMetrics = React.useCallback((id: string) => {
    return metrics.filter(metric => metric.name === `resource-load-${id}`);
  }, [metrics]);

  const getAverageLoadTime = React.useCallback((id: string) => {
    const resourceMetrics = getResourceMetrics(id);
    if (resourceMetrics.length === 0) return 0;
    
    const total = resourceMetrics.reduce((sum, metric) => sum + metric.value, 0);
    return total / resourceMetrics.length;
  }, [getResourceMetrics]);

  const getLoadSuccessRate = React.useCallback((id: string) => {
    const resourceMetrics = getResourceMetrics(id);
    if (resourceMetrics.length === 0) return 0;
    
    const successful = resourceMetrics.filter(metric => metric.rating !== 'poor').length;
    return (successful / resourceMetrics.length) * 100;
  }, [getResourceMetrics]);

  return {
    getResourceMetrics,
    getAverageLoadTime,
    getLoadSuccessRate,
  };
}

// Utility functions
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

// Connection monitoring hook
export function useConnectionMonitoring() {
  const [connectionType, setConnectionType] = React.useState<string>('4g');
  const [isOnline, setIsOnline] = React.useState<boolean>(navigator.onLine);

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
        setConnectionType((connection.effectiveType as string) || '4g');
      }
      
      setIsOnline(navigator.onLine);
    };

    // Initial update
    updateConnectionInfo();

    // Listen for changes
    window.addEventListener('online', updateConnectionInfo);
    window.addEventListener('offline', updateConnectionInfo);
    
    if ((navigator as NavigatorWithConnection).connection) {
      (navigator as NavigatorWithConnection).connection?.addEventListener?.('change', updateConnectionInfo);
    }

    return () => {
      window.removeEventListener('online', updateConnectionInfo);
      window.removeEventListener('offline', updateConnectionInfo);
      if ((navigator as NavigatorWithConnection).connection) {
        (navigator as NavigatorWithConnection).connection?.removeEventListener?.('change', updateConnectionInfo);
      }
    };
  }, []);

  const getResourceQuality = React.useCallback((baseQuality: number = 80) => {
    switch (connectionType) {
      case '2g':
        return Math.min(baseQuality, 50);
      case '3g':
        return Math.min(baseQuality, 70);
      case '4g':
      default:
        return baseQuality;
    }
  }, [connectionType]);

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

  return {
    connectionType,
    isOnline,
    getResourceQuality,
    shouldPreload,
  };
}

// Batch resource loading with progress tracking
export function useBatchResourceLoading() {
  const [loadingProgress, setLoadingProgress] = React.useState<Record<string, number>>({});
  const [loadingStates, setLoadingStates] = React.useState<Record<string, boolean>>({});

  const loadResourcesWithProgress = React.useCallback(async (ids: string[]) => {
    const totalResources = ids.length;
    let loadedCount = 0;

    setLoadingStates(prev => 
      ids.reduce((acc, id) => ({ ...acc, [id]: true }), prev)
    );
    setLoadingProgress(prev => 
      ids.reduce((acc, id) => ({ ...acc, [id]: 0 }), prev)
    );

    const results = await Promise.allSettled(
      ids.map(async (id) => {
        try {
          const resource = await loadResource(id);
          loadedCount++;
          
          setLoadingProgress(prev => ({
            ...prev,
            [id]: 100,
            overall: Math.round((loadedCount / totalResources) * 100),
          }));
          
          return { id, resource, success: true };
        } catch (error) {
          setLoadingStates(prev => ({ ...prev, [id]: false }));
          return { id, error, success: false };
        }
      })
    );

    // Clean up loading states
    setTimeout(() => {
      setLoadingStates(prev => 
        ids.reduce((acc, id) => ({ ...acc, [id]: false }), prev)
      );
      setLoadingProgress({});
    }, 500);

    return results;
  }, []);

  return {
    loadingProgress,
    loadingStates,
    loadResourcesWithProgress,
    isLoading: (id: string) => loadingStates[id] || false,
    getProgress: (id: string) => loadingProgress[id] || 0,
  };
}
