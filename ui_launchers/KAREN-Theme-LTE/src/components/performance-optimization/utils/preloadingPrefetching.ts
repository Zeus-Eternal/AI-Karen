/**
 * Preloading and Prefetching Utilities
 * Advanced preloading and prefetching system with intelligent strategies
 */

'use client';
'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { usePerformanceOptimizationStore } from '../store/performanceOptimizationStore';

type NavigatorWithConnection = Navigator & {
  connection?: {
    effectiveType?: 'slow-2g' | '2g' | '3g' | '4g';
    downlink?: number;
    rtt?: number;
    saveData?: boolean;
    addEventListener?: (event: string, listener: () => void) => void;
  };
};

// Preload resource types
type PreloadResourceType = 'script' | 'style' | 'image' | 'font' | 'video' | 'audio';

// Preload priority levels
type PreloadPriority = 'high' | 'low' | 'auto';

// Network conditions
interface NetworkConditions {
  effectiveType: 'slow-2g' | '2g' | '3g' | '4g';
  downlink: number;
  rtt: number;
  saveData: boolean;
}

// Preload manager class
class PreloadManager {
  private queue: Array<{
    id: string;
    url: string;
    type: PreloadResourceType;
    priority: PreloadPriority;
    callback?: () => void;
    timeout?: number;
  }> = [];
  private isProcessing = false;
  private maxConcurrent = 3;
  private currentLoading = 0;
  private preloadedResources = new Set<string>();
  private networkConditions: NetworkConditions | null = null;

  constructor() {
    this.detectNetworkConditions();
    this.setupNetworkListeners();
  }

  // Add resource to preload queue
  addToQueue(
    id: string,
    url: string,
    type: PreloadResourceType,
    priority: PreloadPriority = 'auto',
    callback?: () => void,
    timeout?: number
  ): void {
    // Skip if already preloaded
    if (this.preloadedResources.has(url)) {
      if (callback) callback();
      return;
    }

    this.queue.push({
      id,
      url,
      type,
      priority,
      callback,
      timeout,
    });

    // Sort queue by priority
    this.sortQueue();

    // Start processing if not already
    if (!this.isProcessing && this.currentLoading < this.maxConcurrent) {
      this.processQueue();
    }
  }

  // Process the preload queue
  private async processQueue(): Promise<void> {
    if (this.isProcessing || this.queue.length === 0) return;

    this.isProcessing = true;

    while (this.queue.length > 0 && this.currentLoading < this.maxConcurrent) {
      const item = this.queue.shift()!;
      this.currentLoading++;

      // Process item with network-aware logic
      this.preloadResource(item)
        .finally(() => {
          this.currentLoading--;
          
          // Continue processing if there are more items
          if (this.queue.length > 0) {
            this.processQueue();
          } else {
            this.isProcessing = false;
          }
        });
    }
  }

  // Preload a single resource
  private async preloadResource(item: {
    id: string;
    url: string;
    type: PreloadResourceType;
    priority: PreloadPriority;
    callback?: () => void;
    timeout?: number;
  }): Promise<void> {
    const startTime = performance.now();

    try {
      // Check if we should preload based on network conditions
      if (!this.shouldPreload(item.type, item.priority)) {
        console.log(`Skipping preload of ${item.url} due to network conditions`);
        return;
      }

      // Create preload element based on type
      const element = this.createPreloadElement(item);
      if (!element) return;

      // Set up timeout if specified
      let timeoutId: NodeJS.Timeout | null = null;
      if (item.timeout) {
        timeoutId = setTimeout(() => {
          console.warn(`Preload timeout for ${item.url}`);
          this.removeElement(element);
        }, item.timeout);
      }

      // Set up load and error handlers
      return new Promise<void>((resolve, reject) => {
        element.onload = () => {
          const loadTime = performance.now() - startTime;
          
          // Mark as preloaded
          this.preloadedResources.add(item.url);
          
          // Record performance metric
          const store = usePerformanceOptimizationStore.getState();
          store.measureMetric({
            name: 'preload-success',
            value: loadTime,
            unit: 'ms',
            timestamp: new Date(),
            rating: loadTime < 500 ? 'good' : loadTime < 1500 ? 'needs-improvement' : 'poor',
            threshold: { good: 500, poor: 1500 },
            metadata: {
              url: item.url,
              type: item.type,
              priority: item.priority,
            },
          });

          // Clear timeout
          if (timeoutId) clearTimeout(timeoutId);
          
          // Remove element
          this.removeElement(element);
          
          // Call callback if provided
          if (item.callback) item.callback();
          
          resolve();
        };

        element.onerror = () => {
          const loadTime = performance.now() - startTime;
          
          // Record performance metric
          const store = usePerformanceOptimizationStore.getState();
          store.measureMetric({
            name: 'preload-error',
            value: loadTime,
            unit: 'ms',
            timestamp: new Date(),
            rating: 'poor',
            threshold: { good: 0, poor: 0 },
            metadata: {
              url: item.url,
              type: item.type,
              priority: item.priority,
            },
          });

          // Clear timeout
          if (timeoutId) clearTimeout(timeoutId);
          
          // Remove element
          this.removeElement(element);
          
          reject(new Error(`Failed to preload ${item.url}`));
        };

        // Add to document
        document.head.appendChild(element);
      });
    } catch (error) {
      console.error(`Error preloading ${item.url}:`, error);
    }
  }

  // Create preload element based on type
  private createPreloadElement(item: {
    url: string;
    type: PreloadResourceType;
    priority: PreloadPriority;
  }): HTMLElement | null {
    try {
      switch (item.type) {
        case 'script':
          const script = document.createElement('link');
          script.rel = 'preload';
          script.href = item.url;
          script.as = 'script';
          script.setAttribute('importance', item.priority);
          return script;

        case 'style':
          const style = document.createElement('link');
          style.rel = 'preload';
          style.href = item.url;
          style.as = 'style';
          style.setAttribute('importance', item.priority);
          return style;

        case 'image':
          const image = document.createElement('link');
          image.rel = 'preload';
          image.href = item.url;
          image.as = 'image';
          image.setAttribute('importance', item.priority);
          return image;

        case 'font':
          const font = document.createElement('link');
          font.rel = 'preload';
          font.href = item.url;
          font.as = 'font';
          font.setAttribute('importance', item.priority);
          font.crossOrigin = 'anonymous';
          return font;

        case 'video':
          const video = document.createElement('link');
          video.rel = 'preload';
          video.href = item.url;
          video.as = 'video';
          video.setAttribute('importance', item.priority);
          return video;

        case 'audio':
          const audio = document.createElement('link');
          audio.rel = 'preload';
          audio.href = item.url;
          audio.as = 'audio';
          audio.setAttribute('importance', item.priority);
          return audio;

        default:
          console.warn(`Unknown preload type: ${item.type}`);
          return null;
      }
    } catch (error) {
      console.error(`Error creating preload element for ${item.url}:`, error);
      return null;
    }
  }

  // Remove element from DOM
  private removeElement(element: HTMLElement): void {
    if (element.parentNode) {
      element.parentNode.removeChild(element);
    }
  }

  // Sort queue by priority
  private sortQueue(): void {
    const priorityOrder = { high: 0, auto: 1, low: 2 };
    this.queue.sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority]);
  }

  // Detect network conditions
  private detectNetworkConditions(): void {
    if ('connection' in navigator) {
      const connection = (navigator as NavigatorWithConnection).connection;
      if (connection) {
        this.networkConditions = {
          effectiveType: connection.effectiveType || '4g',
          downlink: connection.downlink || 10,
          rtt: connection.rtt || 100,
          saveData: connection.saveData || false,
        };
      }
    }
  }

  // Set up network condition listeners
  private setupNetworkListeners(): void {
    if ('connection' in navigator) {
      const connection = (navigator as Record<string, unknown>).connection as NetworkConditions & { addEventListener?: (event: string, handler: () => void) => void } | null;
      if (connection && connection.addEventListener) {
        connection.addEventListener('change', () => {
          this.detectNetworkConditions();
        });
      }
    }
  }

  // Determine if we should preload based on network conditions
  private shouldPreload(type: PreloadResourceType, priority: PreloadPriority): boolean {
    if (!this.networkConditions) return true;

    // Don't preload on slow networks for non-critical resources
    if (this.networkConditions.effectiveType === 'slow-2g' && priority !== 'high') {
      return false;
    }

    if (this.networkConditions.effectiveType === '2g' && priority === 'low') {
      return false;
    }

    // Don't preload if data saver is on for non-critical resources
    if (this.networkConditions.saveData && priority !== 'high') {
      return false;
    }

    return true;
  }

  // Get network conditions
  getNetworkConditions(): NetworkConditions | null {
    return this.networkConditions;
  }

  // Set max concurrent preloads
  setMaxConcurrent(max: number): void {
    this.maxConcurrent = Math.max(1, max);
  }

  // Clear queue
  clearQueue(): void {
    this.queue = [];
  }

  // Get queue status
  getQueueStatus() {
    return {
      queueLength: this.queue.length,
      isProcessing: this.isProcessing,
      currentLoading: this.currentLoading,
      maxConcurrent: this.maxConcurrent,
      preloadedCount: this.preloadedResources.size,
    };
  }
}

// Prefetch manager for link prefetching
class PrefetchManager {
  private prefetchedUrls = new Set<string>();
  private networkConditions: NetworkConditions | null = null;

  constructor() {
    this.detectNetworkConditions();
  }

  // Prefetch a URL
  prefetch(url: string, priority: PreloadPriority = 'auto'): void {
    // Skip if already prefetched
    if (this.prefetchedUrls.has(url)) {
      return;
    }

    // Check if we should prefetch based on network conditions
    if (!this.shouldPrefetch(priority)) {
      return;
    }

    try {
      const link = document.createElement('link');
      link.rel = 'prefetch';
      link.href = url;
      
      // Set importance if supported
      if ('importance' in link) {
        (link as HTMLLinkElement & { importance?: string }).importance = priority;
      }

      document.head.appendChild(link);
      this.prefetchedUrls.add(url);

      // Record performance metric
      const store = usePerformanceOptimizationStore.getState();
      store.measureMetric({
        name: 'prefetch-initiated',
        value: 1,
        unit: 'count',
        timestamp: new Date(),
        rating: 'good',
        threshold: { good: 0, poor: 0 },
        metadata: {
          url,
          priority,
        },
      });
    } catch (error) {
      console.error(`Error prefetching ${url}:`, error);
    }
  }

  // Prefetch multiple URLs
  prefetchUrls(urls: string[], priority: PreloadPriority = 'auto'): void {
    urls.forEach(url => this.prefetch(url, priority));
  }

  // Detect network conditions
  private detectNetworkConditions(): void {
    if ('connection' in navigator) {
      const connection = (navigator as NavigatorWithConnection).connection;
      if (connection) {
        this.networkConditions = {
          effectiveType: connection.effectiveType || '4g',
          downlink: connection.downlink || 10,
          rtt: connection.rtt || 100,
          saveData: connection.saveData || false,
        };
      }
    }
  }

  // Determine if we should prefetch based on network conditions
  private shouldPrefetch(priority: PreloadPriority): boolean {
    if (!this.networkConditions) return true;

    // Don't prefetch on slow networks for non-critical resources
    if (this.networkConditions.effectiveType === 'slow-2g' && priority !== 'high') {
      return false;
    }

    // Don't prefetch if data saver is on for non-critical resources
    if (this.networkConditions.saveData && priority !== 'high') {
      return false;
    }

    return true;
  }

  // Clear prefetched URLs
  clearPrefetched(): void {
    this.prefetchedUrls.clear();
  }

  // Get prefetched URLs
  getPrefetchedUrls(): string[] {
    return Array.from(this.prefetchedUrls);
  }
}

// Intelligent preloading based on user behavior
class IntelligentPreloader {
  private preloadManager: PreloadManager;
  private prefetchManager: PrefetchManager;
  private userBehavior: Map<string, number> = new Map();
  private lastActivity = Date.now();
  private idleThreshold = 2000; // 2 seconds of inactivity

  constructor() {
    this.preloadManager = new PreloadManager();
    this.prefetchManager = new PrefetchManager();
    this.setupActivityListeners();
  }

  // Track user interaction
  trackInteraction(element: string, weight: number = 1): void {
    const currentWeight = this.userBehavior.get(element) || 0;
    this.userBehavior.set(element, currentWeight + weight);
    this.lastActivity = Date.now();
  }

  // Predict and preload likely next resources
  async predictAndPreload(): Promise<void> {
    // Only preload when user is idle
    if (Date.now() - this.lastActivity < this.idleThreshold) {
      return;
    }

    // Get top predicted elements
    const predictions = Array.from(this.userBehavior.entries())
      .sort(([, a], [, b]) => b - a)
      .slice(0, 5);

    // Preload based on predictions
    for (const [element, weight] of predictions) {
      // Get associated resources for this element
      const resources = this.getResourcesForElement(element);
      
      for (const resource of resources) {
        const priority = weight > 10 ? 'high' : weight > 5 ? 'auto' : 'low';
        
        if (resource.type === 'preload') {
          this.preloadManager.addToQueue(
            resource.id,
            resource.url,
            resource.resourceType,
            priority
          );
        } else if (resource.type === 'prefetch') {
          this.prefetchManager.prefetch(resource.url, priority);
        }
      }
    }
  }

  // Get resources associated with an element
  private getResourcesForElement(element: string): Array<{
    id: string;
    url: string;
    type: 'preload' | 'prefetch';
    resourceType: PreloadResourceType;
  }> {
    void element;
    // This would be implemented based on the application's structure
    // For now, return empty array
    return [];
  }
  // Set up activity listeners
  private setupActivityListeners(): void {
    const events = ['click', 'scroll', 'keydown', 'mousemove', 'touchstart'];
    
    const updateActivity = () => {
      this.lastActivity = Date.now();
    };

    events.forEach(event => {
      document.addEventListener(event, updateActivity, { passive: true });
    });
    
    // Check for idle time periodically
    setInterval(() => {
      this.predictAndPreload();
    }, 5000);
  }

  // Get user behavior data
  getUserBehavior(): Map<string, number> {
    return new Map(this.userBehavior);
  }

  // Clear user behavior data
  clearUserBehavior(): void {
    this.userBehavior.clear();
  }
}

// Hook for preloading resources
export function usePreload() {
  const [queueStatus, setQueueStatus] = useState<{
    queueLength: number;
    isProcessing: boolean;
    currentLoading: number;
    maxConcurrent: number;
  } | null>(null);
  const [networkConditions, setNetworkConditions] = useState<NetworkConditions | null>(null);
  const preloadManagerRef = useRef<PreloadManager | null>(null);

  useEffect(() => {
    preloadManagerRef.current = new PreloadManager();
    
    // Update status periodically
    const interval = setInterval(() => {
      if (preloadManagerRef.current) {
        setQueueStatus(preloadManagerRef.current.getQueueStatus());
        setNetworkConditions(preloadManagerRef.current.getNetworkConditions());
      }
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const preload = useCallback((
    id: string,
    url: string,
    type: PreloadResourceType,
    priority: PreloadPriority = 'auto',
    callback?: () => void,
    timeout?: number
  ) => {
    if (preloadManagerRef.current) {
      preloadManagerRef.current.addToQueue(id, url, type, priority, callback, timeout);
    }
  }, []);

  const preloadCritical = useCallback((
    id: string,
    url: string,
    type: PreloadResourceType,
    callback?: () => void
  ) => {
    preload(id, url, type, 'high', callback);
  }, [preload]);

  const setMaxConcurrent = useCallback((max: number) => {
    if (preloadManagerRef.current) {
      preloadManagerRef.current.setMaxConcurrent(max);
    }
  }, []);

  const clearQueue = useCallback(() => {
    if (preloadManagerRef.current) {
      preloadManagerRef.current.clearQueue();
    }
  }, []);

  return {
    queueStatus,
    networkConditions,
    preload,
    preloadCritical,
    setMaxConcurrent,
    clearQueue,
  };
}

// Hook for prefetching resources
export function usePrefetch() {
  const [prefetchedUrls, setPrefetchedUrls] = useState<string[]>([]);
  const [networkConditions, setNetworkConditions] = useState<NetworkConditions | null>(null);
  const prefetchManagerRef = useRef<PrefetchManager | null>(null);

  useEffect(() => {
    prefetchManagerRef.current = new PrefetchManager();
    
    // Update status periodically
    const interval = setInterval(() => {
      if (prefetchManagerRef.current) {
        setPrefetchedUrls(prefetchManagerRef.current.getPrefetchedUrls());
        setNetworkConditions(prefetchManagerRef.current['networkConditions'] || null);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const prefetch = useCallback((url: string, priority: PreloadPriority = 'auto') => {
    if (prefetchManagerRef.current) {
      prefetchManagerRef.current.prefetch(url, priority);
    }
  }, []);

  const prefetchUrls = useCallback((urls: string[], priority: PreloadPriority = 'auto') => {
    if (prefetchManagerRef.current) {
      prefetchManagerRef.current.prefetchUrls(urls, priority);
    }
  }, []);

  const clearPrefetched = useCallback(() => {
    if (prefetchManagerRef.current) {
      prefetchManagerRef.current.clearPrefetched();
    }
  }, []);

  return {
    prefetchedUrls,
    networkConditions,
    prefetch,
    prefetchUrls,
    clearPrefetched,
  };
}

// Hook for intelligent preloading
export function useIntelligentPreloader() {
  const [userBehavior, setUserBehavior] = useState<Map<string, number>>(new Map());
  const intelligentPreloaderRef = useRef<IntelligentPreloader | null>(null);

  useEffect(() => {
    intelligentPreloaderRef.current = new IntelligentPreloader();
    
    // Update status periodically
    const interval = setInterval(() => {
      if (intelligentPreloaderRef.current) {
        setUserBehavior(intelligentPreloaderRef.current.getUserBehavior());
      }
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const trackInteraction = useCallback((element: string, weight: number = 1) => {
    if (intelligentPreloaderRef.current) {
      intelligentPreloaderRef.current.trackInteraction(element, weight);
    }
  }, []);

  const predictAndPreload = useCallback(async () => {
    if (intelligentPreloaderRef.current) {
      await intelligentPreloaderRef.current.predictAndPreload();
    }
  }, []);

  const clearUserBehavior = useCallback(() => {
    if (intelligentPreloaderRef.current) {
      intelligentPreloaderRef.current.clearUserBehavior();
    }
  }, []);

  return {
    userBehavior,
    trackInteraction,
    predictAndPreload,
    clearUserBehavior,
  };
}

// Export singleton instances
export const preloadManager = new PreloadManager();
export const prefetchManager = new PrefetchManager();
export const intelligentPreloader = new IntelligentPreloader();

// Utility functions
export function preloadCriticalResources(resources: Array<{
  id: string;
  url: string;
  type: PreloadResourceType;
}>): Promise<void[]> {
  const promises = resources.map(resource =>
    new Promise<void>((resolve) => {
      preloadManager.addToQueue(
        resource.id,
        resource.url,
        resource.type,
        'high',
        resolve,
        5000 // 5 second timeout
      );
    })
  );

  return Promise.allSettled(promises).then(results =>
    results.map(result => {
      if (result.status === 'fulfilled') {
        return result.value;
      } else {
        throw result.reason;
      }
    })
  );
}

export function prefetchLikelyPages(pages: string[]): void {
  pages.forEach(page => prefetchManager.prefetch(page, 'low'));
}

export function setupViewportPreloading(
  elements: Array<{
    selector: string;
    resources: Array<{
      id: string;
      url: string;
      type: PreloadResourceType;
    }>;
  }>
): void {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const element = entry.target as HTMLElement;
          const config = elements.find(e => e.selector === element.getAttribute('data-preload-selector'));
          
          if (config) {
            config.resources.forEach(resource => {
              preloadManager.addToQueue(resource.id, resource.url, resource.type, 'auto');
            });
            
            observer.unobserve(element);
          }
        }
      });
    },
    { rootMargin: '200px' }
  );

  // Observe elements
  elements.forEach(config => {
    const elements = document.querySelectorAll(config.selector);
    elements.forEach(element => {
      element.setAttribute('data-preload-selector', config.selector);
      observer.observe(element);
    });
  });
}
