/**
 * Performance Profiler and Bottleneck Analyzer
 * Production-grade, SSR-safe, with web vitals + long task + resource/nav observers
 */

export interface PerformanceProfile {
  id: string;
  name: string;
  startTime: number;
  endTime: number;
  duration: number;
  type: 'function' | 'component' | 'api' | 'render' | 'user-interaction';
  metadata: Record<string, unknown>;
  children: PerformanceProfile[];
  bottleneck: boolean;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

export interface Bottleneck {
  id: string;
  type: 'cpu' | 'memory' | 'network' | 'render' | 'javascript';
  location: string;
  description: string;
  impact: number; // 0-100 scale
  frequency: number; // How often it occurs (recently de-duplicated)
  duration: number; // Avg duration in ms
  suggestions: string[];
  priority: 'low' | 'medium' | 'high' | 'critical';
  detectedAt: number;
}

export interface PerformanceMetrics {
  duration: number;
  memoryUsage: number;
  cpuUsage: number;
  renderTime: number;
  networkTime: number;
  samples: number;
}

export interface PerformanceComparison {
  id: string;
  name: string;
  baseline: PerformanceMetrics;
  current: PerformanceMetrics;
  improvement: number; // percentage change
  regression: boolean;
  significance: number; // 0-1
}

export interface OptimizationSuggestion {
  id: string;
  type: 'code' | 'architecture' | 'configuration' | 'infrastructure';
  title: string;
  description: string;
  impact: 'low' | 'medium' | 'high' | 'critical';
  effort: 'low' | 'medium' | 'high';
  implementation: string;
  codeExample?: string;
  estimatedGain: number; // percentage improvement
  confidence: number; // 0-100
}

export interface RegressionTest {
  id: string;
  name: string;
  baseline: number;
  threshold: number; // percentage degradation threshold
  currentValue: number;
  status: 'pass' | 'warning' | 'fail';
  trend: 'improving' | 'stable' | 'degrading';
  history: Array<{ timestamp: number; value: number }>;
}

export type Listener<T> = (payload: T) => void;

const isBrowser =
  typeof window !== 'undefined' &&
  typeof performance !== 'undefined' &&
  typeof document !== 'undefined';

type ReactDevToolsHook = {
  __REACT_DEVTOOLS_GLOBAL_HOOK__?: {
    onCommitFiberRoot?: (...args: unknown[]) => void;
  };
};

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}

function priorityFromImpact(impact: number): Bottleneck['priority'] {
  if (impact >= 80) return 'critical';
  if (impact >= 60) return 'high';
  if (impact >= 30) return 'medium';
  return 'low';
}

function nowMs(): number {
  return isBrowser ? performance.now() : Date.now();
}

export class PerformanceProfiler {
  // Data
  private profiles: PerformanceProfile[] = [];
  private bottlenecks: Bottleneck[] = [];
  private comparisons: PerformanceComparison[] = [];
  private suggestions: OptimizationSuggestion[] = [];
  private regressionTests: RegressionTest[] = [];

  // Observers & timers
  private observers: PerformanceObserver[] = [];
  private mutationObserver: MutationObserver | null = null;
  private analysisTimer: number | null = null;

  // Active profile map
  private activeProfiles: Map<string, PerformanceProfile> = new Map();

  // Config
  private isEnabled = true;
  private readonly maxProfiles = 1000;
  private readonly maxBottlenecks = 100;
  private readonly analysisIntervalMs = 30_000;
  private readonly dedupeWindowMs = 60_000;
  private readonly keepRecent = 50;

  // Subscriptions
  private bottleneckListeners: Set<Listener<Bottleneck>> = new Set();
  private suggestionListeners: Set<Listener<OptimizationSuggestion>> = new Set();

  constructor() {
    if (isBrowser) {
      this.initializeProfiler();
    }
  }

  // ---------- Lifecycle ----------

  private initializeProfiler(): void {
    this.setupPerformanceObservers();
    this.setupUserTimingCapture();
    this.setupLongTaskDetection();
    this.setupWebVitals();
    this.setupRenderProfiler();
    this.startPeriodicAnalysis();
  }

  public setEnabled(enabled: boolean): void {
    this.isEnabled = enabled;
  }

  public destroy(): void {
    this.clear();
    this.observers.forEach(o => o.disconnect());
    this.observers = [];
    if (this.mutationObserver) {
      this.mutationObserver.disconnect();
      this.mutationObserver = null;
    }
    if (this.analysisTimer != null) {
      window.clearInterval(this.analysisTimer);
      this.analysisTimer = null;
    }
    this.bottleneckListeners.clear();
    this.suggestionListeners.clear();
  }

  public clear(): void {
    this.profiles = [];
    this.bottlenecks = [];
    this.comparisons = [];
    this.suggestions = [];
    this.activeProfiles.clear();
  }

  // ---------- Observers ----------

  private setupPerformanceObservers(): void {
    if (!isBrowser || typeof PerformanceObserver === 'undefined') return;

    // Navigation
    try {
      const navigationObserver = new PerformanceObserver(list => {
        for (const e of list.getEntries()) {
          this.analyzeNavigationTiming(e as PerformanceNavigationTiming);
        }
      });
      navigationObserver.observe({ type: 'navigation', buffered: true });
      this.observers.push(navigationObserver);
    } catch (error) {
      void error;
    }

    // Resource
    try {
      const resourceObserver = new PerformanceObserver(list => {
        for (const e of list.getEntries()) {
          this.analyzeResourceTiming(e as PerformanceResourceTiming);
        }
      });
      resourceObserver.observe({ type: 'resource', buffered: true });
      this.observers.push(resourceObserver);
    } catch (error) {
      void error;
    }

    // Paint (FCP lives here for some browsers)
    try {
      const paintObserver = new PerformanceObserver(list => {
        for (const e of list.getEntries()) {
          this.analyzePaintTiming(e);
        }
      });
      paintObserver.observe({ type: 'paint', buffered: true });
      this.observers.push(paintObserver);
    } catch (error) {
      void error;
    }
  }

  private setupUserTimingCapture(): void {
    if (!isBrowser || typeof PerformanceObserver === 'undefined') return;
    try {
      const userTimingObserver = new PerformanceObserver(list => {
        for (const e of list.getEntries()) {
          this.captureUserTiming(e);
        }
      });
      userTimingObserver.observe({ entryTypes: ['measure', 'mark'] });
      this.observers.push(userTimingObserver);
    } catch (error) {
      void error;
    }
  }

  private setupLongTaskDetection(): void {
    if (!isBrowser || typeof PerformanceObserver === 'undefined') return;
    try {
      const longTaskObserver = new PerformanceObserver(list => {
        for (const e of list.getEntries()) {
          // Long Tasks API entries have .duration and .name === 'self'
          const duration = (e as PerformanceEntry).duration ?? 0;
          if (duration > 50) {
            this.detectLongTaskBottleneck(e);
          }
        }
      });
      longTaskObserver.observe({ entryTypes: ['longtask'], buffered: true });
      this.observers.push(longTaskObserver);
    } catch (error) {
      void error;
    }
  }

  private setupWebVitals(): void {
    if (!isBrowser || typeof PerformanceObserver === 'undefined') return;

    // LCP
    try {
      const lcpObserver = new PerformanceObserver(list => {
        for (const e of list.getEntries()) {
          const entry = e as LargestContentfulPaint;
          const profile: PerformanceProfile = {
            id: `lcp-${Date.now()}`,
            name: 'Largest Contentful Paint',
            startTime: entry.startTime,
            endTime: entry.startTime,
            duration: 0,
            type: 'render',
            metadata: { size: entry.size, element: entry.element?.tagName },
            children: [],
            bottleneck: false,
            severity: 'low',
          };
          if (entry.startTime > 2500) {
            this.createBottleneck({
              type: 'render',
              location: 'LCP',
              description: `Slow LCP: ${entry.startTime.toFixed(0)}ms`,
              impact: clamp(entry.startTime / 40, 0, 100),
              duration: entry.startTime,
              suggestions: [
                'Optimize hero image or first large element',
                'Defer non-critical JS/CSS',
                'Serve images in AVIF/WebP',
                'Preload critical resources',
              ],
            });
            profile.bottleneck = true;
            profile.severity = entry.startTime > 4000 ? 'critical' : 'high';
          }
          this.profiles.push(profile);
          this.trimProfiles();
        }
      });
      lcpObserver.observe({ entryTypes: ['largest-contentful-paint'], buffered: true });
      this.observers.push(lcpObserver);
    } catch (error) {
      void error;
    }

    // CLS
    try {
      let cumulativeLayoutShift = 0;
      const clsObserver = new PerformanceObserver(list => {
        for (const e of list.getEntries()) {
          const entry = e as LayoutShift;
          if (!entry.hadRecentInput) {
            cumulativeLayoutShift += entry.value || 0;
          }
        }
        if (cumulativeLayoutShift > 0.25) {
          this.createBottleneck({
            type: 'render',
            location: 'CLS',
            description: `High layout shift (CLS=${cumulativeLayoutShift.toFixed(2)})`,
            impact: clamp(cumulativeLayoutShift * 300, 0, 100),
            duration: 0,
            suggestions: [
              'Always include width/height on images/iframes',
              'Avoid inserting content above existing content',
              'Reserve space for dynamic content',
              'Use font-display: optional/swap',
            ],
          });
        }
      });
      clsObserver.observe({ entryTypes: ['layout-shift'], buffered: true });
      this.observers.push(clsObserver);
    } catch (error) {
      void error;
    }
  }

  private setupRenderProfiler(): void {
    if (!isBrowser) return;

    // (Optional) React DevTools integration hook placeholder
    const hook = (window as Window & ReactDevToolsHook).__REACT_DEVTOOLS_GLOBAL_HOOK__;
    if (hook && typeof hook.onCommitFiberRoot === 'function') {
      // You can wire a bridge here if you want component-level timings
      // Leaving as a no-op placeholder to avoid runtime coupling
      void 0;
    }

    // DOM mutation storms
    if (typeof MutationObserver !== 'undefined') {
      this.mutationObserver = new MutationObserver(mutations => {
        const count = mutations.length;
        if (count > 100) {
          this.createBottleneck({
            type: 'render',
            location: 'DOM Mutations',
            description: `Excessive DOM mutations: ${count} changes`,
            impact: clamp(count / 10, 0, 100),
            duration: 0,
            suggestions: [
              'Batch DOM updates',
              'Use DocumentFragment or batched setState',
              'Virtualize long lists',
              'Avoid layout thrashing (read/write separation)',
            ],
          });
        }
      });
      this.mutationObserver.observe(document.documentElement || document.body, {
        childList: true,
        subtree: true,
        attributes: true,
      });
    }
  }

  private startPeriodicAnalysis(): void {
    if (!isBrowser) return;
    if (this.analysisTimer != null) window.clearInterval(this.analysisTimer);
    this.analysisTimer = window.setInterval(() => {
      this.analyzePerformancePatterns();
      this.generateOptimizationSuggestions();
      this.updateRegressionTests();
    }, this.analysisIntervalMs);
  }

  // ---------- Profiling API ----------

  startProfile(
    name: string,
    type: PerformanceProfile['type'] = 'function',
    metadata: Record<string, unknown> = {}
  ): string {
    if (!this.isEnabled || !isBrowser) return '';
    const id = `${name}-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
    const profile: PerformanceProfile = {
      id,
      name,
      startTime: nowMs(),
      endTime: 0,
      duration: 0,
      type,
      metadata,
      children: [],
      bottleneck: false,
      severity: 'low',
    };
    this.activeProfiles.set(id, profile);
    try {
      performance.mark?.(`${name}-start`);
    } catch (error) {
      void error;
    }
    return id;
  }

  endProfile(id: string): PerformanceProfile | null {
    if (!this.isEnabled || !isBrowser || !id) return null;
    const profile = this.activeProfiles.get(id);
    if (!profile) return null;
    profile.endTime = nowMs();
    profile.duration = profile.endTime - profile.startTime;
    try {
      performance.mark?.(`${profile.name}-end`);
      performance.measure?.(profile.name, `${profile.name}-start`, `${profile.name}-end`);
    } catch (error) {
      void error;
    }
    this.analyzeProfileForBottlenecks(profile);
    this.profiles.push(profile);
    this.trimProfiles();
    this.activeProfiles.delete(id);
    return profile;
  }

  profileFunction<T>(name: string, fn: () => T, metadata?: Record<string, unknown>): T {
    const id = this.startProfile(name, 'function', metadata);
    try {
      return fn();
    } finally {
      this.endProfile(id);
    }
  }

  async profileAsync<T>(name: string, fn: () => Promise<T>, metadata?: Record<string, unknown>): Promise<T> {
    const id = this.startProfile(name, 'function', metadata);
    try {
      const result = await fn();
      return result;
    } finally {
      this.endProfile(id);
    }
  }

  // ---------- Entry analyzers ----------

  private analyzeNavigationTiming(entry: PerformanceNavigationTiming): void {
    const profile: PerformanceProfile = {
      id: `nav-${Date.now()}`,
      name: 'Page Navigation',
      startTime: entry.startTime ?? 0,
      endTime: entry.loadEventEnd ?? (entry.startTime ?? 0),
      duration: (entry.loadEventEnd ?? 0) - (entry.startTime ?? 0),
      type: 'api',
      metadata: {
        domContentLoaded: (entry.domContentLoadedEventEnd ?? 0) - (entry.startTime ?? 0),
        firstByte: (entry.responseStart ?? 0) - (entry.startTime ?? 0),
        domComplete: (entry.domComplete ?? 0) - (entry.startTime ?? 0),
        loadComplete: (entry.loadEventEnd ?? 0) - (entry.startTime ?? 0),
      },
      children: [],
      bottleneck: false,
      severity: 'low',
    };

    // TTFB slow
    const ttfb = (entry.responseStart ?? 0) - (entry.startTime ?? 0);
    if (ttfb > 1000) {
      this.createBottleneck({
        type: 'network',
        location: 'Navigation',
        description: `Slow TTFB: ${ttfb.toFixed(0)}ms`,
        impact: clamp(ttfb / 50, 0, 100),
        duration: ttfb,
        suggestions: [
          'Enable server-side caching and compression',
          'Optimize DB queries and N+1 issues',
          'Use CDN / edge caching for HTML (where safe)',
          'Warm up cold-started services',
        ],
      });
    }

    // DOMContentLoaded handler heavy
    const dclCost = (entry.domContentLoadedEventEnd ?? 0) - (entry.domContentLoadedEventStart ?? 0);
    if (dclCost > 500) {
      this.createBottleneck({
        type: 'javascript',
        location: 'DOMContentLoaded',
        description: `Heavy DCL handlers: ${dclCost.toFixed(0)}ms`,
        impact: clamp(dclCost / 25, 0, 100),
        duration: dclCost,
        suggestions: [
          'Defer non-critical JS',
          'Split bundles and lazy-load',
          'Avoid synchronous layout thrash during DCL',
        ],
      });
    }

    this.analyzeProfileForBottlenecks(profile);
    this.profiles.push(profile);
    this.trimProfiles();
  }

  private analyzeResourceTiming(entry: PerformanceResourceTiming): void {
    const profile: PerformanceProfile = {
      id: `res-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
      name: `Resource: ${entry.name.split('/').pop() || entry.name}`,
      startTime: entry.startTime,
      endTime: entry.responseEnd,
      duration: entry.duration,
      type: 'api',
      metadata: {
        url: entry.name,
        size: entry.transferSize,
        cached: entry.transferSize === 0 && entry.decodedBodySize > 0,
        dns: (entry.domainLookupEnd ?? 0) - (entry.domainLookupStart ?? 0),
        connect: (entry.connectEnd ?? 0) - (entry.connectStart ?? 0),
        request: (entry.responseStart ?? 0) - (entry.requestStart ?? 0),
        response: (entry.responseEnd ?? 0) - (entry.responseStart ?? 0),
      },
      children: [],
      bottleneck: false,
      severity: 'low',
    };

    if (entry.duration > 2000) {
      this.createBottleneck({
        type: 'network',
        location: entry.name,
        description: `Slow resource loading: ${entry.duration.toFixed(0)}ms`,
        impact: clamp(entry.duration / 100, 0, 100),
        duration: entry.duration,
        suggestions: ['Enable HTTP/2 or HTTP/3', 'Compress assets', 'Use CDN', 'Cache aggressively'],
      });
    }

    if ((entry.transferSize ?? 0) > 1_048_576) {
      this.createBottleneck({
        type: 'network',
        location: entry.name,
        description: `Large resource: ${((entry.transferSize ?? 0) / 1024 / 1024).toFixed(1)}MB`,
        impact: clamp(((entry.transferSize ?? 0) / (1024 * 1024)) * 20, 0, 100),
        duration: entry.duration,
        suggestions: [
          'Modern formats (AVIF/WebP)',
          'Image compression & responsive sizes',
          'Code splitting & dynamic imports',
          'Tree-shake unused code',
        ],
      });
    }

    this.analyzeProfileForBottlenecks(profile);
    this.profiles.push(profile);
    this.trimProfiles();
  }

  private analyzePaintTiming(entry: PerformanceEntry): void {
    const profile: PerformanceProfile = {
      id: `paint-${entry.name}-${Date.now()}`,
      name: `Paint: ${entry.name}`,
      startTime: entry.startTime,
      endTime: entry.startTime + entry.duration,
      duration: entry.duration,
      type: 'render',
      metadata: { paintType: entry.name },
      children: [],
      bottleneck: false,
      severity: 'low',
    };

    if (entry.name === 'first-contentful-paint' && entry.startTime > 1800) {
      this.createBottleneck({
        type: 'render',
        location: 'FCP',
        description: `Slow FCP: ${entry.startTime.toFixed(0)}ms`,
        impact: clamp(entry.startTime / 90, 0, 100),
        duration: entry.startTime,
        suggestions: [
          'Reduce render-blocking CSS/JS',
          'Inline critical CSS',
          'Preload key resources',
          'Lazy-load non-critical assets',
        ],
      });
      profile.bottleneck = true;
      profile.severity = entry.startTime > 3000 ? 'high' : 'medium';
    }

    this.profiles.push(profile);
    this.trimProfiles();
  }

  private captureUserTiming(entry: PerformanceEntry): void {
    if (entry.entryType !== 'measure') return;
    const profile: PerformanceProfile = {
      id: `user-timing-${entry.name}-${Date.now()}`,
      name: entry.name,
      startTime: entry.startTime,
      endTime: entry.startTime + entry.duration,
      duration: entry.duration,
      type: 'function',
      metadata: { userTiming: true },
      children: [],
      bottleneck: false,
      severity: 'low',
    };
    this.analyzeProfileForBottlenecks(profile);
    this.profiles.push(profile);
    this.trimProfiles();
  }

  private detectLongTaskBottleneck(entry: PerformanceEntry): void {
    const duration = entry.duration ?? 0;
    if (duration <= 50) return;
    this.createBottleneck({
      type: 'javascript',
      location: 'Long Task',
      description: `Long running task: ${duration.toFixed(0)}ms`,
      impact: clamp(duration / 10, 0, 100),
      duration,
      suggestions: [
        'Split heavy work (time-slicing)',
        'Move to Web Worker',
        'Use requestIdleCallback for non-critical work',
        'Memoize expensive calculations',
      ],
    });
  }

  // ---------- Bottlenecks & suggestions ----------

  private analyzeProfileForBottlenecks(profile: PerformanceProfile): void {
    let isB = false;
    let severity: PerformanceProfile['severity'] = 'low';

    if (profile.duration > 1000) {
      isB = true;
      severity = profile.duration > 5000 ? 'critical' : profile.duration > 2000 ? 'high' : 'medium';
    }

    const profileMemoryUsage =
      typeof profile.metadata.memoryUsage === 'number' ? profile.metadata.memoryUsage : 0;
    if (profileMemoryUsage > 50 * 1024 * 1024) {
      isB = true;
      severity = 'high';
    }

    profile.bottleneck = isB;
    profile.severity = severity;

    if (isB) {
      const typeMap: Record<PerformanceProfile['type'], Bottleneck['type']> = {
        render: 'render',
        api: 'network',
        function: 'javascript',
        component: 'render',
        'user-interaction': 'javascript',
      };
      this.createBottleneck({
        type: typeMap[profile.type],
        location: profile.name,
        description: `Slow ${profile.type}: ${profile.duration.toFixed(0)}ms`,
        impact: clamp(profile.duration / 50, 0, 100),
        duration: profile.duration,
        suggestions: this.getSuggestionsForProfileType(profile.type),
      });
    }
  }

  private getSuggestionsForProfileType(type: PerformanceProfile['type']): string[] {
    const map: Record<PerformanceProfile['type'], string[]> = {
      function: [
        'Optimize algorithmic complexity',
        'Memoize expensive computations',
        'Lazy-evaluate where possible',
        'Profile hot paths and inline tight loops',
      ],
      component: [
        'Use React.memo for pure components',
        'Stabilize props with useMemo/useCallback',
        'Split heavy components and lazy-load',
        'Avoid prop drilling; use context selectively',
      ],
      api: [
        'Cache idempotent responses',
        'Deduplicate inflight requests',
        'Minify/reshape response payloads',
        'Batch & compress requests',
      ],
      render: [
        'Batch DOM updates',
        'Use transform/opacity for animations',
        'Virtualize long lists',
        'Reduce sync layout reads in loops',
      ],
      'user-interaction': [
        'Debounce/throttle handlers',
        'Use passive listeners when possible',
        'Defer heavy work off the input thread',
        'Avoid forced reflow during input',
      ],
    };
    return map[type] || [];
    }

  private createBottleneck(b: Omit<Bottleneck, 'id' | 'frequency' | 'priority' | 'detectedAt'>): void {
    const now = Date.now();
    const existing = this.bottlenecks.find(
      x =>
        x.type === b.type &&
        x.location === b.location &&
        now - x.detectedAt < this.dedupeWindowMs
    );
    if (existing) {
      existing.frequency++;
      existing.duration = (existing.duration + b.duration) / 2;
      return;
    }

    const item: Bottleneck = {
      id: `b-${now}-${Math.random().toString(36).slice(2, 9)}`,
      frequency: 1,
      priority: priorityFromImpact(b.impact),
      detectedAt: now,
      ...b,
    };

    this.bottlenecks.push(item);
    this.trimBottlenecks();
    // notify listeners
    this.bottleneckListeners.forEach((cb) => {
      try {
        cb(item);
      } catch (error) {
        void error;
      }
    });
  }

  private analyzePerformancePatterns(): void {
    if (this.profiles.length < 10) return;
    const recent = this.profiles.slice(-Math.min(50, this.profiles.length));
    const apiSlow = recent.filter(p => p.type === 'api' && p.duration > 1000);
    if (apiSlow.length > 5) {
      this.pushSuggestion({
        id: 'frequent-slow-api',
        type: 'architecture',
        title: 'Frequent Slow API Calls',
        description: `Detected ${apiSlow.length} slow API calls recently.`,
        impact: 'high',
        effort: 'medium',
        implementation:
          'Introduce client-side caching + request deduplication; consider GraphQL or selective fields; compress & paginate large payloads.',
        estimatedGain: 40,
        confidence: 85,
      });
    }

    const renders = recent.filter(p => p.type === 'render');
    if (renders.length > 20) {
      this.pushSuggestion({
        id: 'excessive-rendering',
        type: 'code',
        title: 'Excessive Rendering Detected',
        description: `Observed ${renders.length} render operations in a short window.`,
        impact: 'medium',
        effort: 'low',
        implementation:
          'Memoize components with React.memo; stabilize expensive prop values with useMemo/useCallback; split large views; virtualize long lists.',
        codeExample: `// React.memo to prevent unnecessary re-renders
const MyComp = React.memo(({data}) => <div>{data.value}</div>);

// Expensive calc memoization
const expensive = useMemo(() => heavyCalc(data), [data]);`,
        estimatedGain: 25,
        confidence: 75,
      });
    }
  }

  private generateOptimizationSuggestions(): void {
    // keep suggestions from last 5 min
    const cutoff = Date.now() - 5 * 60 * 1000;
    this.suggestions = this.suggestions.filter(s => {
      const idTime = Number(s.id.split('-')[1]) || 0;
      return idTime > cutoff;
    });

    // recurring bottlenecks => focused suggestion
    const recent = this.bottlenecks.filter(b => Date.now() - b.detectedAt < 5 * 60 * 1000);
    recent.forEach(b => {
      if (b.frequency > 3) {
        this.pushSuggestion({
          id: `suggestion-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
          type: 'code',
          title: `Optimize ${b.location}`,
          description: `Recurring bottleneck: ${b.description}`,
          impact: b.priority === 'critical' ? 'critical' : b.priority === 'high' ? 'high' : 'medium',
          effort: 'medium',
          implementation: b.suggestions.join('. '),
          estimatedGain: Math.min(50, b.impact),
          confidence: clamp(b.frequency * 20, 0, 90),
        });
      }
    });
  }

  private pushSuggestion(s: OptimizationSuggestion): void {
    this.suggestions.push(s);
    this.suggestionListeners.forEach((cb) => {
      try {
        cb(s);
      } catch (error) {
        void error;
      }
    });
  }

  // ---------- Comparisons & regression ----------

  comparePerformance(baselineStart: number, baselineEnd: number, currentStart: number, currentEnd: number): PerformanceComparison[] {
    const baseline = this.profiles.filter(p => p.startTime >= baselineStart && p.startTime <= baselineEnd);
    const current = this.profiles.filter(p => p.startTime >= currentStart && p.startTime <= currentEnd);

    const groupsBase = this.groupByName(baseline);
    const groupsCurr = this.groupByName(current);

    const results: PerformanceComparison[] = [];
    Object.keys(groupsBase).forEach(name => {
      if (!groupsCurr[name]) return;
      const baseM = this.metricsFor(groupsBase[name]);
      const currM = this.metricsFor(groupsCurr[name]);
      const improvement = ((baseM.duration - currM.duration) / baseM.duration) * 100;
      const significance = this.significance(groupsBase[name], groupsCurr[name]);
      results.push({
        id: `cmp-${name}-${Date.now()}`,
        name,
        baseline: baseM,
        current: currM,
        improvement,
        regression: improvement < -5,
        significance,
      });
    });

    this.comparisons = results;
    return results;
  }

  addRegressionTest(name: string, baseline: number, threshold = 20): void {
    const test: RegressionTest = {
      id: `reg-${name}-${Date.now()}`,
      name,
      baseline,
      threshold,
      currentValue: baseline,
      status: 'pass',
      trend: 'stable',
      history: [{ timestamp: Date.now(), value: baseline }],
    };
    this.regressionTests.push(test);
  }

  private updateRegressionTests(): void {
    const windowMs = 5 * 60 * 1000;
    const nowAbs = Date.now();
    this.regressionTests.forEach(test => {
      const recent = this.profiles.filter(
        p => p.name === test.name && nowAbs - (performance.timeOrigin + p.startTime) < windowMs
      );
      if (recent.length === 0) return;
      const avg = recent.reduce((s, p) => s + p.duration, 0) / recent.length;
      test.currentValue = avg;
      test.history.push({ timestamp: nowAbs, value: avg });
      if (test.history.length > 100) test.history = test.history.slice(-50);

      const deg = ((avg - test.baseline) / test.baseline) * 100;
      test.status = deg > test.threshold ? 'fail' : deg > test.threshold * 0.7 ? 'warning' : 'pass';

      if (test.history.length >= 5) {
        const last = test.history.slice(-5);
        const trendVal = last[last.length - 1].value - last[0].value;
        if (trendVal > test.baseline * 0.05) test.trend = 'degrading';
        else if (trendVal < -test.baseline * 0.05) test.trend = 'improving';
        else test.trend = 'stable';
      }
    });
  }

  // ---------- Getters ----------

  getProfiles(limit?: number): PerformanceProfile[] {
    return limit ? this.profiles.slice(-limit) : [...this.profiles];
  }

  getBottlenecks(): Bottleneck[] {
    return [...this.bottlenecks].sort((a, b) => {
      const order = { critical: 4, high: 3, medium: 2, low: 1 };
      return order[b.priority] - order[a.priority];
    });
  }

  getOptimizationSuggestions(): OptimizationSuggestion[] {
    return [...this.suggestions].sort((a, b) => {
      const order = { critical: 4, high: 3, medium: 2, low: 1 };
      return order[b.impact] - order[a.impact];
    });
  }

  getPerformanceComparisons(): PerformanceComparison[] {
    return [...this.comparisons];
  }

  getRegressionTests(): RegressionTest[] {
    return [...this.regressionTests];
  }

  // ---------- Subscriptions (for UI) ----------

  onBottleneck(cb: Listener<Bottleneck>): () => void {
    this.bottleneckListeners.add(cb);
    return () => this.bottleneckListeners.delete(cb);
  }

  onSuggestion(cb: Listener<OptimizationSuggestion>): () => void {
    this.suggestionListeners.add(cb);
    return () => this.suggestionListeners.delete(cb);
  }

  // ---------- Internals ----------

  private groupByName(profiles: PerformanceProfile[]): Record<string, PerformanceProfile[]> {
    return profiles.reduce((acc, p) => {
      (acc[p.name] = acc[p.name] || []).push(p);
      return acc;
    }, {} as Record<string, PerformanceProfile[]>);
  }

  private metricsFor(profiles: PerformanceProfile[]): PerformanceMetrics {
    const durations = profiles.map(p => p.duration);
    const mem = profiles.map((p) => {
      return typeof p.metadata.memoryUsage === 'number' ? p.metadata.memoryUsage : 0;
    });
    const avg = (arr: number[]) => (arr.length ? arr.reduce((s, n) => s + n, 0) / arr.length : 0);
    return {
      duration: avg(durations),
      memoryUsage: avg(mem),
      cpuUsage: 0,
      renderTime: 0,
      networkTime: 0,
      samples: profiles.length,
    };
  }

  private significance(base: PerformanceProfile[], curr: PerformanceProfile[]): number {
    const b = base.map(p => p.duration);
    const c = curr.map(p => p.duration);
    if (b.length < 2 || c.length < 2) return 0;
    const mean = (a: number[]) => a.reduce((s, n) => s + n, 0) / a.length;
    const variance = (a: number[], m: number) => a.reduce((s, n) => s + Math.pow(n - m, 2), 0) / (a.length - 1);

    const mb = mean(b), mc = mean(c);
    const vb = variance(b, mb), vc = variance(c, mc);
    const pooled = Math.sqrt(((b.length - 1) * vb + (c.length - 1) * vc) / (b.length + c.length - 2));
    const se = pooled * Math.sqrt(1 / b.length + 1 / c.length);
    if (se === 0) return 0;
    const t = Math.abs(mb - mc) / se;
    return clamp(1 - t / 10, 0, 1);
  }

  private trimProfiles() {
    if (this.profiles.length > this.maxProfiles) {
      this.profiles = this.profiles.slice(-this.keepRecent);
    }
  }

  private trimBottlenecks() {
    if (this.bottlenecks.length > this.maxBottlenecks) {
      this.bottlenecks = this.bottlenecks.slice(-this.keepRecent);
    }
  }
}

// Singleton instance
export const performanceProfiler = new PerformanceProfiler();
