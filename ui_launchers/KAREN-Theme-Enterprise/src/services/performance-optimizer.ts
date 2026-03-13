/**
 * Performance Optimization Engine
 * Production-grade, SSR-safe runtime optimizer for web apps.
 * - Bundle heuristics (split suggestions + prefetch of likely routes)
 * - Image optimization (lazy loading, optional WebP swap when available)
 * - Caching strategies (SW registration, cache hit/miss telemetry, smart preloads)
 * - Memory management (GC/heap monitoring, leak trend detection)
 *
 * Notes:
 * - Build-time bundle splitting is still recommended (this only adds runtime hints/suggestions).
 * - All DOM/Window access is guarded for SSR safety.
 */

export type Priority = 'low' | 'medium' | 'high' | 'critical';

export interface OptimizationConfig {
  bundleSplitting: {
    enabled: boolean;
    chunkSizeLimit: number; // bytes
    routeBasedSplitting: boolean;
    componentBasedSplitting: boolean;
  };
  imageOptimization: {
    enabled: boolean;
    webpConversion: boolean;
    responsiveSizing: boolean; // advisory only at runtime
    lazyLoading: boolean;
    qualityThreshold: number; // advisory
  };
  caching: {
    enabled: boolean;
    serviceWorker: boolean;
    browserCache: boolean;
    preloadStrategies: Array<'critical-resources' | 'next-page' | 'user-behavior'>;
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
    hitRate: number;      // counter of hits
    missRate: number;     // counter of misses
    averageLoadTime: number; // ms, rolling avg
  };
  memoryUsage: {
    heapUsed: number;     // bytes
    heapTotal: number;    // bytes
    leaksDetected: number;
    gcFrequency: number;  // observed GC marks
  };
}

export interface OptimizationRecommendation {
  id: string;
  type: 'bundle' | 'image' | 'cache' | 'memory' | 'code';
  priority: Priority;
  title: string;
  description: string;
  impact: string;
  implementation: string;
  estimatedGain: number; // percentage improvement
}

export type Listener<T> = (payload: T) => void;

const isBrowser =
  typeof window !== 'undefined' &&
  typeof document !== 'undefined';

const hasPO =
  typeof PerformanceObserver !== 'undefined';

type SafeWindow = {
  requestIdleCallback?: (callback: IdleRequestCallback) => number;
  requestAnimationFrame?: (callback: FrameRequestCallback) => number;
  setTimeout: typeof setTimeout;
};

type FrameRequestCallback = (time: number) => void;

const safeWindow: SafeWindow =
  (typeof window !== 'undefined' ? window : globalThis as SafeWindow);

type PerformanceWithMemory = Performance & {
  memory?: {
    usedJSHeapSize?: number;
    totalJSHeapSize?: number;
  };
};

type GCWindow = Window & {
  gc?: () => void;
};

function safeRAF(cb: () => void) {
  if (!isBrowser) return;
  if ('requestIdleCallback' in safeWindow && typeof safeWindow.requestIdleCallback === 'function') {
    safeWindow.requestIdleCallback(() => cb());
    return;
  }
  if ('requestAnimationFrame' in safeWindow && typeof safeWindow.requestAnimationFrame === 'function') {
    safeWindow.requestAnimationFrame(() => cb());
    return;
  }
  safeWindow.setTimeout(cb, 0);
}

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}

class MemoryLeakDetector {
  private monitoring = false;
  private memorySnapshots: number[] = [];
  private interval?: number;
  private readonly periodMs = 30_000;
  private onLeakListeners: Set<Listener<number>> = new Set();

  start(): void {
    if (this.monitoring || !isBrowser) return;
    this.monitoring = true;
    this.interval = window.setInterval(() => this.takeMemorySnapshot(), this.periodMs);
  }

  stop(): void {
    this.monitoring = false;
    if (this.interval) {
      clearInterval(this.interval);
      this.interval = undefined;
    }
    this.onLeakListeners.clear();
  }

  onLeak(cb: Listener<number>): () => void {
    this.onLeakListeners.add(cb);
    return () => this.onLeakListeners.delete(cb);
  }

  private takeMemorySnapshot(): void {
    const perf = isBrowser ? (performance as PerformanceWithMemory) : undefined;
    if (!perf?.memory) return;
    const used = perf.memory.usedJSHeapSize ?? 0;
    this.memorySnapshots.push(used);
    if (this.memorySnapshots.length > 10) this.memorySnapshots.shift();
    this.analyzeMemoryTrend();
  }

  private analyzeMemoryTrend(): void {
    if (this.memorySnapshots.length < 6) return;
    let growthCount = 0;
    for (let i = 1; i < this.memorySnapshots.length; i++) {
      if (this.memorySnapshots[i] > this.memorySnapshots[i - 1]) growthCount++;
    }
    // Consistent growth (≥80%) across snapshots flags a likely leak
    if (growthCount >= Math.floor(this.memorySnapshots.length * 0.8)) {
      const latest = this.memorySnapshots[this.memorySnapshots.length - 1];
      this.onLeakListeners.forEach((cb) => {
        try {
          cb(latest);
        } catch (error) {
          void error;
        }
      });
    }
  }
}

export class PerformanceOptimizer {
  private config: OptimizationConfig;
  private metrics: OptimizationMetrics;
  private recommendations: OptimizationRecommendation[] = [];
  private observers: PerformanceObserver[] = [];
  private timers: number[] = [];
  private memoryLeakDetector: MemoryLeakDetector;
  private suggestionListeners: Set<Listener<OptimizationRecommendation>> = new Set();

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
    // Defer heavy setup to idle/RAF so we don't block hydration
    safeRAF(() => this.initialize());
  }

  // ---------------- Public API ----------------

  getMetrics(): OptimizationMetrics {
    return { ...this.metrics };
  }

  getConfig(): OptimizationConfig {
    return {
      bundleSplitting: { ...this.config.bundleSplitting },
      imageOptimization: { ...this.config.imageOptimization },
      caching: {
        ...this.config.caching,
        preloadStrategies: [...this.config.caching.preloadStrategies],
      },
      memoryManagement: { ...this.config.memoryManagement },
    };
  }

  generateRecommendations(): OptimizationRecommendation[] {
    // Always re-evaluate from current signals
    this.recommendations = [];
    this.analyzeBundleSize();
    this.analyzeImageOptimization();
    this.analyzeCachePerformance();
    this.analyzeMemoryUsage();
    return this.sortedRecommendations();
  }

  async applyOptimizations(): Promise<void> {
    const recs = this.generateRecommendations();
    for (const r of recs) {
      if (r.priority === 'critical' || r.priority === 'high') {
        await this.applyOptimization(r);
      }
    }
  }

  updateConfig(config: Partial<OptimizationConfig>): void {
    this.config = { ...this.config, ...config };
    // Re-initialize idempotently
    this.destroy();
    safeRAF(() => this.initialize());
  }

  onRecommendation(cb: Listener<OptimizationRecommendation>): () => void {
    this.suggestionListeners.add(cb);
    return () => this.suggestionListeners.delete(cb);
  }

  destroy(): void {
    // Disconnect observers
    this.observers.forEach((o) => {
      try {
        o.disconnect();
      } catch (error) {
        void error;
      }
    });
    this.observers = [];
    // Clear timers
    this.timers.forEach(t => clearInterval(t));
    this.timers = [];
    // Stop memory detector
    this.memoryLeakDetector.stop();
    this.suggestionListeners.clear();
  }

  // ---------------- Initialization ----------------

  private initialize(): void {
    if (!isBrowser) return;

    if (this.config.bundleSplitting.enabled) this.initializeBundleOptimization();
    if (this.config.imageOptimization.enabled) this.initializeImageOptimization();
    if (this.config.caching.enabled) this.initializeCacheOptimization();
    if (this.config.memoryManagement.enabled) this.initializeMemoryManagement();

    this.startPerformanceMonitoring();
    this.generateInitialRecommendations();
  }

  // ---------------- Bundle Optimization ----------------

  private initializeBundleOptimization(): void {
    if (this.config.bundleSplitting.routeBasedSplitting) {
      this.implementRouteSplitting();
    }
    if (this.config.bundleSplitting.componentBasedSplitting) {
      this.implementComponentSplitting();
    }
    this.monitorBundleSizes();
  }

  private implementRouteSplitting(): void {
    // Heuristic: prefetch next likely routes to smooth navigation (runtime assist).
    const routes = this.getApplicationRoutes();
    routes.forEach((route) => {
      // prefetch hint for idle time (does not block)
      this.prefetchRoute(route.path);
    });
  }

  private implementComponentSplitting(): void {
    const largeComponents = this.identifyLargeComponents();
    largeComponents.forEach((component) => {
      this.pushRecommendation({
        id: `component-split-${component.name}`,
        type: 'bundle',
        priority: component.size * 1024 > this.config.bundleSplitting.chunkSizeLimit ? 'high' : 'medium',
        title: `Split large component: ${component.name}`,
        description: `Component ${component.name} is ~${component.size}KB. Split to reduce initial JS.`,
        impact: 'Lower TTI and faster route hydration',
        implementation: 'Use React.lazy() + Suspense or dynamic(() => import(...)) with Next.js.',
        estimatedGain: clamp((component.size / 1024) * 5, 10, 40),
      });
    });
  }

  private monitorBundleSizes(): void {
    if (!hasPO) return;
    try {
      const navObs = new PerformanceObserver((list) => {
        for (const entry of list.getEntries() as PerformanceNavigationTiming[]) {
          // Use transferSize as a rough proxy for HTML + initial resources fetched with nav (not perfect).
          const size = entry.transferSize || 0;
          if (this.metrics.bundleSize.before === 0) {
            this.metrics.bundleSize.before = size;
          } else {
            this.metrics.bundleSize.after = size;
            this.metrics.bundleSize.reduction = Math.max(0, this.metrics.bundleSize.before - this.metrics.bundleSize.after);
          }
        }
      });
      navObs.observe({ type: 'navigation', buffered: true });
      this.observers.push(navObs);
    } catch (error) {
      void error;
    }
  }

  // ---------------- Image Optimization ----------------

  private initializeImageOptimization(): void {
    if (this.config.imageOptimization.lazyLoading) this.setupLazyLoading();
    this.monitorImagePerformance();
    if (this.config.imageOptimization.webpConversion) this.setupWebPDetection();
  }

  private setupLazyLoading(): void {
    if (!isBrowser) return;
    if ('loading' in HTMLImageElement.prototype) {
      // Native lazy loading—ensure untagged images become lazy by default
      document.querySelectorAll('img:not([loading])').forEach((img) => {
        img.setAttribute('loading', 'lazy');
      });
    } else if ('IntersectionObserver' in window) {
      // IO-based lazy loading for browsers without native support
      const imageObserver = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (!entry.isIntersecting) return;
            const img = entry.target as HTMLImageElement;
            const dataSrc = img.getAttribute('data-src');
            if (dataSrc) {
              img.src = dataSrc;
              img.removeAttribute('data-src');
              this.metrics.imageOptimization.imagesOptimized++;
            }
            imageObserver.unobserve(img);
          });
        },
        { rootMargin: '100px 0px', threshold: 0.01 }
      );
      document.querySelectorAll('img[data-src]').forEach((img) => imageObserver.observe(img));
    }
  }

  private setupWebPDetection(): void {
    const supports = this.checkWebPSupport();
    if (!supports) return;
    // Opportunistically swap .jpg/.png to .webp when HEAD 200
    document.querySelectorAll('img').forEach((img) => {
      const url = img.currentSrc || img.src;
      if (!url) return;
      const webpSrc = url.replace(/\.(jpe?g|png)$/i, '.webp');
      if (webpSrc === url) return;
      this.checkImageExists(webpSrc).then((exists) => {
        if (exists) {
          img.src = webpSrc;
          this.metrics.imageOptimization.webpConversions++;
        }
      });
    });
  }

  private monitorImagePerformance(): void {
    if (!isBrowser) return;
    // Count images that complete load (crude but useful for visibility)
    const handler = (ev: Event) => {
      const target = ev.target as HTMLElement | null;
      if (target && target.tagName === 'IMG') {
        this.metrics.imageOptimization.imagesOptimized++;
      }
    };
    document.addEventListener('load', handler, true);
    // Disconnect on destroy
    const stop = () => document.removeEventListener('load', handler, true);
    this.timers.push(window.setTimeout(stop, 0)); // stored to remove later via destroy()
  }

  // ---------------- Caching ----------------

  private initializeCacheOptimization(): void {
    if (this.config.caching.serviceWorker) {
      this.setupServiceWorkerCaching();
    }
    this.implementPreloadingStrategies();
    this.monitorCachePerformance();
  }

  private setupServiceWorkerCaching(): void {
    if (!('serviceWorker' in navigator)) return;
    navigator.serviceWorker
      .register('/sw.js')
      .then((reg) => {
        // Optionally listen for updates to advise on cache invalidation strategy
        reg.addEventListener('updatefound', () => {
          // noop: hook for UI toast if desired
          void 0;
        });
      })
      .catch(() => {
        // SW registration failed; keep silent in production
        void 0;
      });
  }

  private implementPreloadingStrategies(): void {
    this.config.caching.preloadStrategies.forEach((strategy) => {
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

  private monitorCachePerformance(): void {
    if (!hasPO) return;
    try {
      const resObs = new PerformanceObserver((list) => {
        const resources = list.getEntries() as PerformanceResourceTiming[];
        resources.forEach((r) => {
          // Approx cache hit: transferSize == 0 but decodedBodySize > 0 (not perfect, but indicative)
          const isHit = (r.transferSize === 0 && (r.decodedBodySize || 0) > 0);
          if (isHit) this.metrics.cachePerformance.hitRate++;
          else this.metrics.cachePerformance.missRate++;

          // Rolling average for load time
          const prev = this.metrics.cachePerformance.averageLoadTime || 0;
          this.metrics.cachePerformance.averageLoadTime = prev === 0 ? r.duration : (prev * 0.9 + r.duration * 0.1);
        });
      });
      resObs.observe({ type: 'resource', buffered: true });
      this.observers.push(resObs);
    } catch (error) {
      void error;
    }
  }

  // ---------------- Memory Management ----------------

  private initializeMemoryManagement(): void {
    if (this.config.memoryManagement.leakDetection) {
      this.memoryLeakDetector.start();
      this.memoryLeakDetector.onLeak((_latestUsed) => {
        this.metrics.memoryUsage.leaksDetected++;
        this.pushRecommendation({
          id: `memory-leak-${Date.now()}`,
          type: 'memory',
          priority: 'critical',
          title: 'Potential Memory Leak Detected',
          description: 'Heap usage has risen consistently across snapshots.',
          impact: 'May lead to UI jank or crashes over time.',
          implementation: 'Audit component lifecycles, event listeners, subscriptions, and caches. Verify unmount cleanup.',
          estimatedGain: 25,
        });
      });
    }

    if (this.config.memoryManagement.gcMonitoring && hasPO) {
      try {
        const obs = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.entryType === 'measure' && entry.name === 'gc') {
              this.metrics.memoryUsage.gcFrequency++;
              if (entry.duration > 50) {
                this.pushRecommendation({
                  id: `gc-pressure-${Date.now()}`,
                  type: 'memory',
                  priority: 'medium',
                  title: 'High Garbage Collection Pressure',
                  description: `GC pause observed: ${entry.duration.toFixed(0)}ms`,
                  impact: 'Frequent long GC pauses cause input delay and frame drops.',
                  implementation: 'Reduce allocation rate; reuse objects; avoid large arrays/maps retained across renders.',
                  estimatedGain: 20,
                });
              }
            }
          }
        });
        // Only possible if you manually mark GC; browsers don’t emit GC measures by default
        obs.observe({ entryTypes: ['measure'] });
        this.observers.push(obs);
      } catch (error) {
        void error;
      }
    }

    // Periodic heap polling (Chrome-only)
    const t = window.setInterval(() => {
      const perf = performance as PerformanceWithMemory;
      if (perf.memory) {
        this.metrics.memoryUsage.heapUsed = perf.memory.usedJSHeapSize || 0;
        this.metrics.memoryUsage.heapTotal = perf.memory.totalJSHeapSize || 0;
      }
    }, 10_000);
    this.timers.push(t);
  }

  // ---------------- Perf Monitoring ----------------

  private startPerformanceMonitoring(): void {
    if (!hasPO) return;
    try {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.entryType === 'resource') {
            this.analyzeResourcePerformance(entry as PerformanceResourceTiming);
          }
        }
      });
      observer.observe({ entryTypes: ['resource'] });
      this.observers.push(observer);
    } catch (error) {
      void error;
    }
  }

  // ---------------- Analysis → Recommendations ----------------

  private generateInitialRecommendations(): void {
    if (!this.config.imageOptimization.webpConversion) {
      this.pushRecommendation({
        id: 'enable-webp',
        type: 'image',
        priority: 'medium',
        title: 'Enable WebP image conversion',
        description: 'WebP typically reduces image size by 25–35% vs JPEG/PNG.',
        impact: 'Less bandwidth and faster LCP.',
        implementation: 'Provide .webp variants and <picture> with type="image/webp".',
        estimatedGain: 30,
      });
    }
    if (!this.config.caching.serviceWorker) {
      this.pushRecommendation({
        id: 'enable-service-worker',
        type: 'cache',
        priority: 'high',
        title: 'Enable Service Worker caching',
        description: 'Greatly improves repeat-visit performance and enables offline.',
        impact: 'Faster nav + lower server load.',
        implementation: 'Register SW and pre-cache critical shell + versioned assets.',
        estimatedGain: 40,
      });
    }
  }

  private analyzeBundleSize(): void {
    const total = this.metrics.bundleSize.after || this.metrics.bundleSize.before;
    if (total && total > 500 * 1024) {
      this.pushRecommendation({
        id: 'large-bundle',
        type: 'bundle',
        priority: 'high',
        title: 'Large initial transfer size detected',
        description: `Initial transfer ~${(total / 1024).toFixed(0)}KB.`,
        impact: 'Slow hydration and longer TTI.',
        implementation: 'Aggressive splitting, tree-shaking, dynamic imports, and vendor chunk isolation.',
        estimatedGain: 35,
      });
    }
  }

  private analyzeImageOptimization(): void {
    if (!isBrowser) return;
    const images = Array.from(document.querySelectorAll('img'));
    if (!images.length) return;

    const nonLazy = images.filter((img) => img.getAttribute('loading') !== 'lazy');
    if (nonLazy.length > 0) {
      this.pushRecommendation({
        id: 'lazy-loading-images',
        type: 'image',
        priority: 'medium',
        title: `${nonLazy.length} image(s) without lazy loading`,
        description: 'Non-critical images should lazy load to reduce initial work.',
        impact: 'Improves initial render and bandwidth usage.',
        implementation: 'Add loading="lazy" or IO-based lazy loader for unsupported browsers.',
        estimatedGain: 20,
      });
    }
  }

  private analyzeCachePerformance(): void {
    const hits = this.metrics.cachePerformance.hitRate;
    const misses = this.metrics.cachePerformance.missRate;
    const total = hits + misses;
    if (total === 0) return;
    const hitPct = (hits / total) * 100;
    if (hitPct < 70) {
      this.pushRecommendation({
        id: 'low-cache-hit-rate',
        type: 'cache',
        priority: 'medium',
        title: `Low cache hit rate: ${hitPct.toFixed(1)}%`,
        description: 'Caching strategy likely underutilized.',
        impact: 'Higher server load and slower page loads.',
        implementation: 'Strengthen Cache-Control/ETag; pre-cache critical assets in SW; leverage immutable content hashing.',
        estimatedGain: 25,
      });
    }
  }

  private analyzeMemoryUsage(): void {
    const perf = performance as PerformanceWithMemory;
    if (!perf.memory) return;
    const used = perf.memory.usedJSHeapSize ?? 0;
    const total = perf.memory.totalJSHeapSize ?? 0;
    if (total > 0) {
      const pct = (used / total) * 100;
      if (pct > 80) {
        this.pushRecommendation({
          id: 'high-memory-usage',
          type: 'memory',
          priority: 'high',
          title: `High memory usage: ${pct.toFixed(1)}%`,
          description: 'Sustained high heap pressure degrades responsiveness.',
          impact: 'UI hitches, longer GC pauses.',
          implementation: 'Tighten caches, release large arrays/maps, verify unmount cleanup, minimize retained closures.',
          estimatedGain: 30,
        });
      }
    }
  }

  private analyzeResourcePerformance(entry: PerformanceResourceTiming): void {
    if (entry.duration > 1000) {
      this.pushRecommendation({
        id: `slow-resource-${entry.name}-${Date.now()}`,
        type: 'cache',
        priority: 'medium',
        title: `Slow resource: ${this.shortName(entry.name)}`,
        description: `Load time ${entry.duration.toFixed(0)}ms.`,
        impact: 'Delays render and interactivity.',
        implementation: 'Compress, CDN, cache headers (immutable), and defer non-critical fetches.',
        estimatedGain: 15,
      });
    }
  }

  // ---------------- Apply Optimizations ----------------

  private async applyOptimization(r: OptimizationRecommendation): Promise<void> {
    switch (r.type) {
      case 'image':
        if (r.id === 'lazy-loading-images') {
          if (!isBrowser) return;
          document.querySelectorAll('img:not([loading])').forEach((img) => {
            img.setAttribute('loading', 'lazy');
          });
        }
        break;
      case 'cache':
        if (r.id === 'enable-service-worker') {
          this.setupServiceWorkerCaching();
        }
        break;
      case 'memory':
        if (r.id.startsWith('memory-leak')) {
          // Manual GC can be available in some dev environments behind flags
          const win = window as GCWindow;
          if (isBrowser && typeof win.gc === 'function') {
            try {
              win.gc();
            } catch (error) {
              void error;
            }
          }
        }
        break;
      case 'bundle':
        // Build-time action—only advisory here.
        break;
      case 'code':
        // Advisory only
        break;
    }
  }

  // ---------------- Helpers ----------------

  private prefetchRoute(path: string): void {
    if (!isBrowser) return;
    const link = document.createElement('link');
    link.rel = 'prefetch';
    link.href = path;
    link.as = 'document';
    document.head.appendChild(link);
  }

  private preloadCriticalResources(): void {
    if (!isBrowser) return;
    // These should be tailored to your app; example API endpoints and above-the-fold assets
    const critical: string[] = ['/api/user', '/api/config'];
    critical.forEach((href) => {
      const link = document.createElement('link');
      link.rel = 'preload';
      link.href = href;
      // as is best-effort; if unknown, omit to avoid warnings
      document.head.appendChild(link);
    });
  }

  private preloadNextPage(): void {
    if (!isBrowser) return;
    const next = this.predictNextPage(window.location.pathname);
    if (next) this.prefetchRoute(next);
  }

  private preloadBasedOnBehavior(): void {
    // Hook for your analytics model → map to prefetch targets
    // Left advisory to avoid guessing at runtime
    return;
  }

  private predictNextPage(current: string): string | null {
    const table: Record<string, string> = {
      '/dashboard': '/analytics',
      '/analytics': '/reports',
      '/settings': '/profile',
    };
    return table[current] || null;
  }

  private checkWebPSupport(): boolean {
    if (!isBrowser) return false;
    try {
      const canvas = document.createElement('canvas');
      canvas.width = 1; canvas.height = 1;
      return canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0;
    } catch {
      return false;
    }
  }

  private async checkImageExists(url: string): Promise<boolean> {
    try {
      const res = await fetch(url, { method: 'HEAD' });
      return res.ok;
    } catch {
      return false;
    }
  }

  private getApplicationRoutes(): Array<{ name: string; path: string; size: number /* KB */ }> {
    // Ideally sourced from your router manifest at build-time
    return [
      { name: 'dashboard', path: '/dashboard', size: 150 },
      { name: 'analytics', path: '/analytics', size: 200 },
      { name: 'settings', path: '/settings', size: 100 },
    ];
  }

  private identifyLargeComponents(): Array<{ name: string; size: number /* KB */ }> {
    // Ideally from bundle analyzer JSON; here we return advisory samples
    return [
      { name: 'DataVisualization', size: 300 },
      { name: 'ComplexForm', size: 250 },
    ];
  }

  private pushRecommendation(rec: OptimizationRecommendation): void {
    this.recommendations.push(rec);
    // notify listeners for live UI
    this.suggestionListeners.forEach((cb) => {
      try {
        cb(rec);
      } catch (error) {
        void error;
      }
    });
  }

  private sortedRecommendations(): OptimizationRecommendation[] {
    const order: Record<Priority, number> = { critical: 4, high: 3, medium: 2, low: 1 };
    return [...this.recommendations].sort((a, b) => {
      const pdiff = order[b.priority] - order[a.priority];
      if (pdiff !== 0) return pdiff;
      return b.estimatedGain - a.estimatedGain;
    });
  }

  private shortName(url: string): string {
    try {
      const u = new URL(url, window.location.href);
      return (u.pathname.split('/').pop() || u.pathname) + (u.search ? '…' : '');
    } catch {
      return url.slice(-40);
    }
  }
}

// Singleton instance
export const performanceOptimizer = new PerformanceOptimizer();
export default performanceOptimizer;
