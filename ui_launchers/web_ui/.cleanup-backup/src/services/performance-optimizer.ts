/**
 * Performance Optimization Engine
 * Implements automatic performance optimizations including bundle splitting,
 * image optimization, caching strategies, and memory management
 */

export interface OptimizationConfig {
  bundleSplitting: {
    enabled: boolean;
    chunkSizeLimit: number;
    routeBasedSplitting: boolean;
    componentBasedSplitting: boolean;
  };
  imageOptimization: {
    enabled: boolean;
    webpConversion: boolean;
    responsiveSizing: boolean;
    lazyLoading: boolean;
    qualityThreshold: number;
  };
  caching: {
    enabled: boolean;
    serviceWorker: boolean;
    browserCache: boolean;
    preloadStrategies: string[];
    cacheInvalidation: 'aggressive' | 'conservative' | 'smart';
  };
  memoryManagement: {
    enabled: boolean;
    gcMonitoring: boolean;
    leakDetection: boolean;
    componentCleanup: boolean;
    eventListenerCleanup: boolean;
  };
}

export interface OptimizationMetrics {
  bundleSize: {
    before: number;
    after: number;
    reduction: number;
  };
  imageOptimization: {
    imagesOptimized: number;
    sizeReduction: number;
    webpConversions: number;
  };
  cachePerformance: {
    hitRate: number;
    missRate: number;
    averageLoadTime: number;
  };
  memoryUsage: {
    heapUsed: number;
    heapTotal: number;
    leaksDetected: number;
    gcFrequency: number;
  };
}

export interface OptimizationRecommendation {
  id: string;
  type: 'bundle' | 'image' | 'cache' | 'memory' | 'code';
  priority: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  impact: string;
  implementation: string;
  estimatedGain: number; // percentage improvement
}

export class PerformanceOptimizer {
  private config: OptimizationConfig;
  private metrics: OptimizationMetrics;
  private recommendations: OptimizationRecommendation[] = [];
  private observers: PerformanceObserver[] = [];
  private memoryLeakDetector: MemoryLeakDetector;

  constructor(config?: Partial<OptimizationConfig>) {
    this.config = {
      bundleSplitting: {
        enabled: true,
        chunkSizeLimit: 244 * 1024, // 244KB
        routeBasedSplitting: true,
        componentBasedSplitting: true,
      },
      imageOptimization: {
        enabled: true,
        webpConversion: true,
        responsiveSizing: true,
        lazyLoading: true,
        qualityThreshold: 85,
      },
      caching: {
        enabled: true,
        serviceWorker: true,
        browserCache: true,
        preloadStrategies: ['critical-resources', 'next-page'],
        cacheInvalidation: 'smart',
      },
      memoryManagement: {
        enabled: true,
        gcMonitoring: true,
        leakDetection: true,
        componentCleanup: true,
        eventListenerCleanup: true,
      },
      ...config,
    };

    this.metrics = {
      bundleSize: { before: 0, after: 0, reduction: 0 },
      imageOptimization: { imagesOptimized: 0, sizeReduction: 0, webpConversions: 0 },
      cachePerformance: { hitRate: 0, missRate: 0, averageLoadTime: 0 },
      memoryUsage: { heapUsed: 0, heapTotal: 0, leaksDetected: 0, gcFrequency: 0 },
    };

    this.memoryLeakDetector = new MemoryLeakDetector();
    this.initialize();
  }

  /**
   * Initialize the performance optimizer
   */
  private initialize(): void {
    if (this.config.bundleSplitting.enabled) {
      this.initializeBundleOptimization();
    }

    if (this.config.imageOptimization.enabled) {
      this.initializeImageOptimization();
    }

    if (this.config.caching.enabled) {
      this.initializeCacheOptimization();
    }

    if (this.config.memoryManagement.enabled) {
      this.initializeMemoryManagement();
    }

    this.startPerformanceMonitoring();
    this.generateInitialRecommendations();
  }

  /**
   * Initialize bundle optimization
   */
  private initializeBundleOptimization(): void {
    // Implement dynamic imports for route-based splitting
    if (this.config.bundleSplitting.routeBasedSplitting) {
      this.implementRouteSplitting();
    }

    // Implement component-based splitting
    if (this.config.bundleSplitting.componentBasedSplitting) {
      this.implementComponentSplitting();
    }

    // Monitor bundle sizes
    this.monitorBundleSizes();
  }

  /**
   * Initialize image optimization
   */
  private initializeImageOptimization(): void {
    // Set up intersection observer for lazy loading
    if (this.config.imageOptimization.lazyLoading) {
      this.setupLazyLoading();
    }

    // Monitor image loading performance
    this.monitorImagePerformance();

    // Set up WebP conversion detection
    if (this.config.imageOptimization.webpConversion) {
      this.setupWebPDetection();
    }
  }

  /**
   * Initialize cache optimization
   */
  private initializeCacheOptimization(): void {
    // Set up service worker caching
    if (this.config.caching.serviceWorker) {
      this.setupServiceWorkerCaching();
    }

    // Implement preloading strategies
    this.implementPreloadingStrategies();

    // Monitor cache performance
    this.monitorCachePerformance();
  }

  /**
   * Initialize memory management
   */
  private initializeMemoryManagement(): void {
    // Start memory leak detection
    if (this.config.memoryManagement.leakDetection) {
      this.memoryLeakDetector.start();
    }

    // Monitor garbage collection
    if (this.config.memoryManagement.gcMonitoring) {
      this.monitorGarbageCollection();
    }

    // Set up component cleanup monitoring
    if (this.config.memoryManagement.componentCleanup) {
      this.monitorComponentCleanup();
    }
  }

  /**
   * Implement route-based code splitting
   */
  private implementRouteSplitting(): void {
    // This would typically be handled at build time, but we can provide runtime optimizations
    const routes = this.getApplicationRoutes();
    
    routes.forEach(route => {
      // Preload next likely routes based on user behavior
      this.preloadRoute(route);
    });
  }

  /**
   * Implement component-based code splitting
   */
  private implementComponentSplitting(): void {
    // Monitor component usage and suggest splitting for large components
    const largeComponents = this.identifyLargeComponents();
    
    largeComponents.forEach(component => {
      this.recommendations.push({
        id: `component-split-${component.name}`,
        type: 'bundle',
        priority: 'medium',
        title: `Split large component: ${component.name}`,
        description: `Component ${component.name} is ${component.size}KB and could benefit from code splitting`,
        impact: 'Reduces initial bundle size and improves loading performance',
        implementation: 'Use React.lazy() and Suspense to split this component',
        estimatedGain: Math.min(30, (component.size / 1024) * 5),
      });
    });
  }

  /**
   * Set up lazy loading for images
   */
  private setupLazyLoading(): void {
    if ('IntersectionObserver' in window) {
      const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const img = entry.target as HTMLImageElement;
            if (img.dataset.src) {
              img.src = img.dataset.src;
              img.removeAttribute('data-src');
              imageObserver.unobserve(img);
              this.metrics.imageOptimization.imagesOptimized++;
            }
          }
        });
      }, {
        rootMargin: '50px 0px',
        threshold: 0.01,
      });

      // Observe all images with data-src attribute
      document.querySelectorAll('img[data-src]').forEach(img => {
        imageObserver.observe(img);
      });
    }
  }

  /**
   * Set up WebP detection and conversion
   */
  private setupWebPDetection(): void {
    const supportsWebP = this.checkWebPSupport();
    
    if (supportsWebP) {
      // Replace image sources with WebP versions when available
      document.querySelectorAll('img').forEach(img => {
        const webpSrc = img.src.replace(/\.(jpg|jpeg|png)$/i, '.webp');
        
        // Check if WebP version exists
        this.checkImageExists(webpSrc).then(exists => {
          if (exists) {
            img.src = webpSrc;
            this.metrics.imageOptimization.webpConversions++;
          }
        });
      });
    }
  }

  /**
   * Set up service worker caching
   */
  private setupServiceWorkerCaching(): void {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js')
        .then(registration => {
          console.log('Service Worker registered:', registration);
          this.monitorServiceWorkerCache(registration);
        })
        .catch(error => {
          console.error('Service Worker registration failed:', error);
        });
    }
  }

  /**
   * Implement preloading strategies
   */
  private implementPreloadingStrategies(): void {
    this.config.caching.preloadStrategies.forEach(strategy => {
      switch (strategy) {
        case 'critical-resources':
          this.preloadCriticalResources();
          break;
        case 'next-page':
          this.preloadNextPage();
          break;
        case 'user-behavior':
          this.preloadBasedOnBehavior();
          break;
      }
    });
  }

  /**
   * Monitor garbage collection
   */
  private monitorGarbageCollection(): void {
    if ('PerformanceObserver' in window) {
      try {
        const gcObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.name === 'gc') {
              this.metrics.memoryUsage.gcFrequency++;
              this.analyzeGCPattern(entry);
            }
          }
        });

        gcObserver.observe({ entryTypes: ['measure'] });
        this.observers.push(gcObserver);
      } catch (error) {
        console.warn('GC monitoring not supported:', error);
      }
    }

    // Fallback: monitor memory usage periodically
    setInterval(() => {
      if ('memory' in performance) {
        const memory = (performance as any).memory;
        this.metrics.memoryUsage.heapUsed = memory.usedJSHeapSize;
        this.metrics.memoryUsage.heapTotal = memory.totalJSHeapSize;
        
        this.detectMemoryLeaks();
      }
    }, 10000);
  }

  /**
   * Start performance monitoring
   */
  private startPerformanceMonitoring(): void {
    // Monitor resource loading
    if ('PerformanceObserver' in window) {
      const resourceObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          this.analyzeResourcePerformance(entry as PerformanceResourceTiming);
        }
      });

      try {
        resourceObserver.observe({ entryTypes: ['resource'] });
        this.observers.push(resourceObserver);
      } catch (error) {
        console.warn('Resource monitoring not supported:', error);
      }
    }
  }

  /**
   * Generate optimization recommendations
   */
  generateRecommendations(): OptimizationRecommendation[] {
    this.recommendations = [];

    // Analyze current performance and generate recommendations
    this.analyzeBundleSize();
    this.analyzeImageOptimization();
    this.analyzeCachePerformance();
    this.analyzeMemoryUsage();

    return this.recommendations.sort((a, b) => {
      const priorityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
      return priorityOrder[b.priority] - priorityOrder[a.priority];
    });
  }

  /**
   * Apply automatic optimizations
   */
  async applyOptimizations(): Promise<void> {
    const recommendations = this.generateRecommendations();
    
    for (const recommendation of recommendations) {
      if (recommendation.priority === 'critical' || recommendation.priority === 'high') {
        await this.applyOptimization(recommendation);
      }
    }
  }

  /**
   * Get optimization metrics
   */
  getMetrics(): OptimizationMetrics {
    return { ...this.metrics };
  }

  /**
   * Update configuration
   */
  updateConfig(config: Partial<OptimizationConfig>): void {
    this.config = { ...this.config, ...config };
    this.initialize(); // Re-initialize with new config
  }

  // Private helper methods

  private getApplicationRoutes(): Array<{ name: string; path: string; size: number }> {
    // This would typically be provided by the routing system
    return [
      { name: 'dashboard', path: '/dashboard', size: 150 },
      { name: 'analytics', path: '/analytics', size: 200 },
      { name: 'settings', path: '/settings', size: 100 },
    ];
  }

  private identifyLargeComponents(): Array<{ name: string; size: number }> {
    // This would analyze the bundle to identify large components
    return [
      { name: 'DataVisualization', size: 300 },
      { name: 'ComplexForm', size: 250 },
    ];
  }

  private preloadRoute(route: { name: string; path: string }): void {
    // Implement route preloading logic
    const link = document.createElement('link');
    link.rel = 'prefetch';
    link.href = route.path;
    document.head.appendChild(link);
  }

  private checkWebPSupport(): boolean {
    const canvas = document.createElement('canvas');
    canvas.width = 1;
    canvas.height = 1;
    return canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0;
  }

  private async checkImageExists(url: string): Promise<boolean> {
    try {
      const response = await fetch(url, { method: 'HEAD' });
      return response.ok;
    } catch {
      return false;
    }
  }

  private monitorBundleSizes(): void {
    // Monitor and track bundle size changes
    if ('PerformanceObserver' in window) {
      const navigationObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          const navEntry = entry as PerformanceNavigationTiming;
          this.metrics.bundleSize.after = navEntry.transferSize || 0;
        }
      });

      try {
        navigationObserver.observe({ entryTypes: ['navigation'] });
        this.observers.push(navigationObserver);
      } catch (error) {
        console.warn('Navigation monitoring not supported:', error);
      }
    }
  }

  private monitorImagePerformance(): void {
    document.addEventListener('load', (event) => {
      const target = event.target as HTMLImageElement;
      if (target.tagName === 'IMG') {
        // Track image loading performance
        this.metrics.imageOptimization.imagesOptimized++;
      }
    }, true);
  }

  private monitorCachePerformance(): void {
    // Monitor cache hit/miss rates
    if ('PerformanceObserver' in window) {
      const resourceObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          const resource = entry as PerformanceResourceTiming;
          if (resource.transferSize === 0 && resource.decodedBodySize > 0) {
            // Likely a cache hit
            this.metrics.cachePerformance.hitRate++;
          } else {
            this.metrics.cachePerformance.missRate++;
          }
        }
      });

      try {
        resourceObserver.observe({ entryTypes: ['resource'] });
        this.observers.push(resourceObserver);
      } catch (error) {
        console.warn('Cache monitoring not supported:', error);
      }
    }
  }

  private monitorServiceWorkerCache(registration: ServiceWorkerRegistration): void {
    // Monitor service worker cache performance
    registration.addEventListener('updatefound', () => {
      console.log('Service Worker update found');
    });
  }

  private monitorComponentCleanup(): void {
    // Monitor React component cleanup
    // This would integrate with React DevTools or custom hooks
  }

  private preloadCriticalResources(): void {
    const criticalResources = ['/api/user', '/api/config'];
    
    criticalResources.forEach(resource => {
      const link = document.createElement('link');
      link.rel = 'prefetch';
      link.href = resource;
      document.head.appendChild(link);
    });
  }

  private preloadNextPage(): void {
    // Predict and preload the next likely page based on current route
    const currentPath = window.location.pathname;
    const nextPage = this.predictNextPage(currentPath);
    
    if (nextPage) {
      this.preloadRoute({ name: nextPage, path: nextPage });
    }
  }

  private preloadBasedOnBehavior(): void {
    // Analyze user behavior and preload resources
    // This would use analytics data to predict user actions
  }

  private predictNextPage(currentPath: string): string | null {
    const predictions: Record<string, string> = {
      '/dashboard': '/analytics',
      '/analytics': '/reports',
      '/settings': '/profile',
    };
    
    return predictions[currentPath] || null;
  }

  private detectMemoryLeaks(): void {
    const memory = (performance as any).memory;
    if (memory) {
      const usagePercent = (memory.usedJSHeapSize / memory.totalJSHeapSize) * 100;
      
      if (usagePercent > 90) {
        this.metrics.memoryUsage.leaksDetected++;
        this.recommendations.push({
          id: 'memory-leak-detected',
          type: 'memory',
          priority: 'critical',
          title: 'Memory leak detected',
          description: `Memory usage is at ${usagePercent.toFixed(1)}%`,
          impact: 'High memory usage can cause performance degradation and crashes',
          implementation: 'Review component cleanup and event listener removal',
          estimatedGain: 25,
        });
      }
    }
  }

  private analyzeResourcePerformance(entry: PerformanceResourceTiming): void {
    // Analyze resource loading performance and generate recommendations
    if (entry.duration > 1000) {
      this.recommendations.push({
        id: `slow-resource-${entry.name}`,
        type: 'cache',
        priority: 'medium',
        title: `Slow loading resource: ${entry.name}`,
        description: `Resource took ${entry.duration.toFixed(0)}ms to load`,
        impact: 'Slow resources delay page rendering and user interaction',
        implementation: 'Consider caching, compression, or CDN optimization',
        estimatedGain: 15,
      });
    }
  }

  private analyzeGCPattern(entry: PerformanceEntry): void {
    // Analyze garbage collection patterns
    if (entry.duration > 50) {
      this.recommendations.push({
        id: 'gc-pressure',
        type: 'memory',
        priority: 'medium',
        title: 'High garbage collection pressure',
        description: `GC took ${entry.duration.toFixed(0)}ms`,
        impact: 'Frequent or long GC pauses can cause UI freezing',
        implementation: 'Optimize object creation and memory usage patterns',
        estimatedGain: 20,
      });
    }
  }

  private generateInitialRecommendations(): void {
    // Generate initial set of recommendations based on configuration
    if (!this.config.imageOptimization.webpConversion) {
      this.recommendations.push({
        id: 'enable-webp',
        type: 'image',
        priority: 'medium',
        title: 'Enable WebP image conversion',
        description: 'WebP images can reduce file sizes by 25-35%',
        impact: 'Faster image loading and reduced bandwidth usage',
        implementation: 'Enable WebP conversion in image optimization settings',
        estimatedGain: 30,
      });
    }

    if (!this.config.caching.serviceWorker) {
      this.recommendations.push({
        id: 'enable-service-worker',
        type: 'cache',
        priority: 'high',
        title: 'Enable Service Worker caching',
        description: 'Service Workers can significantly improve repeat visit performance',
        impact: 'Faster loading for returning users and offline capability',
        implementation: 'Enable Service Worker in caching settings',
        estimatedGain: 40,
      });
    }
  }

  private analyzeBundleSize(): void {
    // Analyze bundle size and suggest optimizations
    if (this.metrics.bundleSize.after > 500 * 1024) { // 500KB
      this.recommendations.push({
        id: 'large-bundle',
        type: 'bundle',
        priority: 'high',
        title: 'Large bundle size detected',
        description: `Bundle size is ${(this.metrics.bundleSize.after / 1024).toFixed(0)}KB`,
        impact: 'Large bundles increase initial loading time',
        implementation: 'Enable code splitting and tree shaking',
        estimatedGain: 35,
      });
    }
  }

  private analyzeImageOptimization(): void {
    // Analyze image optimization opportunities
    const images = document.querySelectorAll('img');
    let unoptimizedImages = 0;

    images.forEach(img => {
      if (!img.loading || img.loading !== 'lazy') {
        unoptimizedImages++;
      }
    });

    if (unoptimizedImages > 0) {
      this.recommendations.push({
        id: 'lazy-loading-images',
        type: 'image',
        priority: 'medium',
        title: `${unoptimizedImages} images without lazy loading`,
        description: 'Images without lazy loading can slow initial page load',
        impact: 'Faster initial page load and reduced bandwidth usage',
        implementation: 'Add loading="lazy" attribute to images',
        estimatedGain: 20,
      });
    }
  }

  private analyzeCachePerformance(): void {
    // Analyze cache performance
    const totalRequests = this.metrics.cachePerformance.hitRate + this.metrics.cachePerformance.missRate;
    if (totalRequests > 0) {
      const hitRate = (this.metrics.cachePerformance.hitRate / totalRequests) * 100;
      
      if (hitRate < 70) {
        this.recommendations.push({
          id: 'low-cache-hit-rate',
          type: 'cache',
          priority: 'medium',
          title: `Low cache hit rate: ${hitRate.toFixed(1)}%`,
          description: 'Low cache hit rate indicates caching strategy needs improvement',
          impact: 'Better caching reduces server load and improves performance',
          implementation: 'Review and optimize caching headers and strategies',
          estimatedGain: 25,
        });
      }
    }
  }

  private analyzeMemoryUsage(): void {
    // Analyze memory usage patterns
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      const usagePercent = (memory.usedJSHeapSize / memory.totalJSHeapSize) * 100;
      
      if (usagePercent > 80) {
        this.recommendations.push({
          id: 'high-memory-usage',
          type: 'memory',
          priority: 'high',
          title: `High memory usage: ${usagePercent.toFixed(1)}%`,
          description: 'High memory usage can impact performance',
          impact: 'Optimizing memory usage improves overall performance',
          implementation: 'Review component lifecycle and memory management',
          estimatedGain: 30,
        });
      }
    }
  }

  private async applyOptimization(recommendation: OptimizationRecommendation): Promise<void> {
    // Apply automatic optimizations based on recommendation type
    switch (recommendation.type) {
      case 'image':
        await this.applyImageOptimization(recommendation);
        break;
      case 'cache':
        await this.applyCacheOptimization(recommendation);
        break;
      case 'memory':
        await this.applyMemoryOptimization(recommendation);
        break;
      case 'bundle':
        await this.applyBundleOptimization(recommendation);
        break;
    }
  }

  private async applyImageOptimization(recommendation: OptimizationRecommendation): Promise<void> {
    if (recommendation.id === 'lazy-loading-images') {
      document.querySelectorAll('img:not([loading])').forEach(img => {
        img.setAttribute('loading', 'lazy');
      });
    }
  }

  private async applyCacheOptimization(recommendation: OptimizationRecommendation): Promise<void> {
    if (recommendation.id === 'enable-service-worker') {
      this.setupServiceWorkerCaching();
    }
  }

  private async applyMemoryOptimization(recommendation: OptimizationRecommendation): Promise<void> {
    if (recommendation.id === 'memory-leak-detected') {
      // Trigger garbage collection if possible
      if ('gc' in window) {
        (window as any).gc();
      }
    }
  }

  private async applyBundleOptimization(recommendation: OptimizationRecommendation): Promise<void> {
    // Bundle optimizations are typically handled at build time
    console.log('Bundle optimization recommendation:', recommendation.title);
  }

  /**
   * Cleanup observers and resources
   */
  destroy(): void {
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];
    this.memoryLeakDetector.stop();
  }
}

/**
 * Memory Leak Detector
 * Detects potential memory leaks in the application
 */
class MemoryLeakDetector {
  private monitoring = false;
  private memorySnapshots: number[] = [];
  private interval?: NodeJS.Timeout;

  start(): void {
    if (this.monitoring) return;
    
    this.monitoring = true;
    this.interval = setInterval(() => {
      this.takeMemorySnapshot();
    }, 30000); // Every 30 seconds
  }

  stop(): void {
    this.monitoring = false;
    if (this.interval) {
      clearInterval(this.interval);
      this.interval = undefined;
    }
  }

  private takeMemorySnapshot(): void {
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      this.memorySnapshots.push(memory.usedJSHeapSize);
      
      // Keep only last 10 snapshots
      if (this.memorySnapshots.length > 10) {
        this.memorySnapshots.shift();
      }
      
      this.analyzeMemoryTrend();
    }
  }

  private analyzeMemoryTrend(): void {
    if (this.memorySnapshots.length < 5) return;
    
    // Check for consistent memory growth
    let growthCount = 0;
    for (let i = 1; i < this.memorySnapshots.length; i++) {
      if (this.memorySnapshots[i] > this.memorySnapshots[i - 1]) {
        growthCount++;
      }
    }
    
    // If memory is consistently growing, it might be a leak
    if (growthCount >= this.memorySnapshots.length * 0.8) {
      console.warn('Potential memory leak detected: consistent memory growth');
    }
  }
}

// Singleton instance
export const performanceOptimizer = new PerformanceOptimizer();