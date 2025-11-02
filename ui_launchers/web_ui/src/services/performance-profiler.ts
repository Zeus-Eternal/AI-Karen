/**
 * Performance Profiler and Bottleneck Analyzer
 * Provides detailed execution analysis, bottleneck detection, and optimization recommendations
 */
export interface PerformanceProfile {
  id: string;
  name: string;
  startTime: number;
  endTime: number;
  duration: number;
  type: 'function' | 'component' | 'api' | 'render' | 'user-interaction';
  metadata: Record<string, any>;
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
  frequency: number; // How often it occurs
  duration: number; // Average duration in ms
  suggestions: string[];
  priority: 'low' | 'medium' | 'high' | 'critical';
  detectedAt: number;
}
export interface PerformanceComparison {
  id: string;
  name: string;
  baseline: PerformanceMetrics;
  current: PerformanceMetrics;
  improvement: number; // percentage change
  regression: boolean;
  significance: number; // statistical significance 0-1
}
interface PerformanceMetrics {
  duration: number;
  memoryUsage: number;
  cpuUsage: number;
  renderTime: number;
  networkTime: number;
  samples: number;
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
export class PerformanceProfiler {
  private profiles: PerformanceProfile[] = [];
  private bottlenecks: Bottleneck[] = [];
  private comparisons: PerformanceComparison[] = [];
  private suggestions: OptimizationSuggestion[] = [];
  private regressionTests: RegressionTest[] = [];
  private observers: PerformanceObserver[] = [];
  private activeProfiles: Map<string, PerformanceProfile> = new Map();
  private isEnabled = true;
  constructor() {
    this.initializeProfiler();
  }
  /**
   * Initialize the performance profiler
   */
  private initializeProfiler(): void {
    this.setupPerformanceObservers();
    this.setupUserTimingCapture();
    this.setupLongTaskDetection();
    this.setupRenderProfiler();
    this.startBottleneckDetection();
  }
  /**
   * Set up performance observers
   */
  private setupPerformanceObservers(): void {
    if (!('PerformanceObserver' in window)) return;
    // Observe navigation timing
    try {
      const navigationObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          this.analyzeNavigationTiming(entry as PerformanceNavigationTiming);
        }

      navigationObserver.observe({ entryTypes: ['navigation'] });
      this.observers.push(navigationObserver);
    } catch (error) {
    }
    // Observe resource timing
    try {
      const resourceObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          this.analyzeResourceTiming(entry as PerformanceResourceTiming);
        }

      resourceObserver.observe({ entryTypes: ['resource'] });
      this.observers.push(resourceObserver);
    } catch (error) {
    }
    // Observe paint timing
    try {
      const paintObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          this.analyzePaintTiming(entry);
        }

      paintObserver.observe({ entryTypes: ['paint'] });
      this.observers.push(paintObserver);
    } catch (error) {
    }
  }
  /**
   * Set up user timing capture
   */
  private setupUserTimingCapture(): void {
    if (!('PerformanceObserver' in window)) return;
    try {
      const userTimingObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          this.captureUserTiming(entry);
        }

      userTimingObserver.observe({ entryTypes: ['measure', 'mark'] });
      this.observers.push(userTimingObserver);
    } catch (error) {
    }
  }
  /**
   * Set up long task detection
   */
  private setupLongTaskDetection(): void {
    if (!('PerformanceObserver' in window)) return;
    try {
      const longTaskObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          this.detectLongTaskBottleneck(entry);
        }

      longTaskObserver.observe({ entryTypes: ['longtask'] });
      this.observers.push(longTaskObserver);
    } catch (error) {
    }
  }
  /**
   * Set up render profiler
   */
  private setupRenderProfiler(): void {
    // Monitor React component renders if React DevTools is available
    if (typeof window !== 'undefined' && (window as any).__REACT_DEVTOOLS_GLOBAL_HOOK__) {
      this.setupReactProfiler();
    }
    // Monitor DOM mutations
    this.setupMutationObserver();
  }
  /**
   * Start a performance profile
   */
  startProfile(name: string, type: PerformanceProfile['type'] = 'function', metadata: Record<string, any> = {}): string {
    if (!this.isEnabled) return '';
    const id = `${name}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const profile: PerformanceProfile = {
      id,
      name,
      startTime: performance.now(),
      endTime: 0,
      duration: 0,
      type,
      metadata,
      children: [],
      bottleneck: false,
      severity: 'low',
    };
    this.activeProfiles.set(id, profile);
    performance.mark(`${name}-start`);
    return id;
  }
  /**
   * End a performance profile
   */
  endProfile(id: string): PerformanceProfile | null {
    if (!this.isEnabled || !id) return null;
    const profile = this.activeProfiles.get(id);
    if (!profile) return null;
    profile.endTime = performance.now();
    profile.duration = profile.endTime - profile.startTime;
    performance.mark(`${profile.name}-end`);
    performance.measure(profile.name, `${profile.name}-start`, `${profile.name}-end`);
    // Analyze for bottlenecks
    this.analyzeProfileForBottlenecks(profile);
    this.profiles.push(profile);
    this.activeProfiles.delete(id);
    // Keep only last 1000 profiles
    if (this.profiles.length > 1000) {
      this.profiles = this.profiles.slice(-500);
    }
    return profile;
  }
  /**
   * Profile a function execution
   */
  profileFunction<T>(name: string, fn: () => T, metadata?: Record<string, any>): T {
    const id = this.startProfile(name, 'function', metadata);
    try {
      const result = fn();
      return result;
    } finally {
      this.endProfile(id);
    }
  }
  /**
   * Profile an async function execution
   */
  async profileAsync<T>(name: string, fn: () => Promise<T>, metadata?: Record<string, any>): Promise<T> {
    const id = this.startProfile(name, 'function', metadata);
    try {
      const result = await fn();
      return result;
    } finally {
      this.endProfile(id);
    }
  }
  /**
   * Analyze navigation timing for bottlenecks
   */
  private analyzeNavigationTiming(entry: PerformanceNavigationTiming): void {
    const profile: PerformanceProfile = {
      id: `navigation-${Date.now()}`,
      name: 'Page Navigation',
      startTime: entry.navigationStart,
      endTime: entry.loadEventEnd,
      duration: entry.loadEventEnd - entry.navigationStart,
      type: 'api',
      metadata: {
        domContentLoaded: entry.domContentLoadedEventEnd - entry.navigationStart,
        firstByte: entry.responseStart - entry.navigationStart,
        domComplete: entry.domComplete - entry.navigationStart,
        loadComplete: entry.loadEventEnd - entry.navigationStart,
      },
      children: [],
      bottleneck: false,
      severity: 'low',
    };
    // Check for navigation bottlenecks
    if (entry.responseStart - entry.navigationStart > 1000) {
      this.createBottleneck({
        type: 'network',
        location: 'Navigation',
        description: `Slow server response time: ${(entry.responseStart - entry.navigationStart).toFixed(0)}ms`,
        impact: Math.min(100, (entry.responseStart - entry.navigationStart) / 50),
        duration: entry.responseStart - entry.navigationStart,
        suggestions: [
          'Optimize server response time',
          'Implement server-side caching',
          'Use a CDN for static assets',
          'Optimize database queries',
        ],

    }
    if (entry.domContentLoadedEventEnd - entry.domContentLoadedEventStart > 500) {
      this.createBottleneck({
        type: 'javascript',
        location: 'DOM Content Loaded',
        description: `Slow DOM content loading: ${(entry.domContentLoadedEventEnd - entry.domContentLoadedEventStart).toFixed(0)}ms`,
        impact: Math.min(100, (entry.domContentLoadedEventEnd - entry.domContentLoadedEventStart) / 25),
        duration: entry.domContentLoadedEventEnd - entry.domContentLoadedEventStart,
        suggestions: [
          'Reduce JavaScript execution during DOMContentLoaded',
          'Defer non-critical JavaScript',
          'Optimize DOM manipulation',
        ],

    }
    this.analyzeProfileForBottlenecks(profile);
    this.profiles.push(profile);
  }
  /**
   * Analyze resource timing for bottlenecks
   */
  private analyzeResourceTiming(entry: PerformanceResourceTiming): void {
    const profile: PerformanceProfile = {
      id: `resource-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      name: `Resource: ${entry.name.split('/').pop() || entry.name}`,
      startTime: entry.startTime,
      endTime: entry.responseEnd,
      duration: entry.duration,
      type: 'api',
      metadata: {
        url: entry.name,
        size: entry.transferSize,
        cached: entry.transferSize === 0 && entry.decodedBodySize > 0,
        dns: entry.domainLookupEnd - entry.domainLookupStart,
        connect: entry.connectEnd - entry.connectStart,
        request: entry.responseStart - entry.requestStart,
        response: entry.responseEnd - entry.responseStart,
      },
      children: [],
      bottleneck: false,
      severity: 'low',
    };
    // Check for resource bottlenecks
    if (entry.duration > 2000) {
      this.createBottleneck({
        type: 'network',
        location: entry.name,
        description: `Slow resource loading: ${entry.duration.toFixed(0)}ms`,
        impact: Math.min(100, entry.duration / 100),
        duration: entry.duration,
        suggestions: [
          'Optimize resource size',
          'Enable compression',
          'Use a CDN',
          'Implement caching headers',
        ],

    }
    if (entry.transferSize > 1024 * 1024) { // 1MB
      this.createBottleneck({
        type: 'network',
        location: entry.name,
        description: `Large resource size: ${(entry.transferSize / 1024 / 1024).toFixed(1)}MB`,
        impact: Math.min(100, entry.transferSize / (1024 * 1024) * 20),
        duration: entry.duration,
        suggestions: [
          'Compress images and assets',
          'Use modern image formats (WebP, AVIF)',
          'Implement lazy loading',
          'Split large bundles',
        ],

    }
    this.analyzeProfileForBottlenecks(profile);
    this.profiles.push(profile);
  }
  /**
   * Analyze paint timing
   */
  private analyzePaintTiming(entry: PerformanceEntry): void {
    const profile: PerformanceProfile = {
      id: `paint-${entry.name}-${Date.now()}`,
      name: `Paint: ${entry.name}`,
      startTime: entry.startTime,
      endTime: entry.startTime + entry.duration,
      duration: entry.duration,
      type: 'render',
      metadata: {
        paintType: entry.name,
      },
      children: [],
      bottleneck: false,
      severity: 'low',
    };
    // Check for paint bottlenecks
    if (entry.name === 'first-contentful-paint' && entry.startTime > 1800) {
      this.createBottleneck({
        type: 'render',
        location: 'First Contentful Paint',
        description: `Slow first contentful paint: ${entry.startTime.toFixed(0)}ms`,
        impact: Math.min(100, entry.startTime / 90),
        duration: entry.startTime,
        suggestions: [
          'Optimize critical rendering path',
          'Reduce render-blocking resources',
          'Inline critical CSS',
          'Optimize web fonts loading',
        ],

    }
    this.profiles.push(profile);
  }
  /**
   * Capture user timing marks and measures
   */
  private captureUserTiming(entry: PerformanceEntry): void {
    if (entry.entryType === 'measure') {
      const profile: PerformanceProfile = {
        id: `user-timing-${entry.name}-${Date.now()}`,
        name: entry.name,
        startTime: entry.startTime,
        endTime: entry.startTime + entry.duration,
        duration: entry.duration,
        type: 'function',
        metadata: {
          userTiming: true,
        },
        children: [],
        bottleneck: false,
        severity: 'low',
      };
      this.analyzeProfileForBottlenecks(profile);
      this.profiles.push(profile);
    }
  }
  /**
   * Detect long task bottlenecks
   */
  private detectLongTaskBottleneck(entry: PerformanceEntry): void {
    this.createBottleneck({
      type: 'javascript',
      location: 'Long Task',
      description: `Long running task: ${entry.duration.toFixed(0)}ms`,
      impact: Math.min(100, entry.duration / 10),
      duration: entry.duration,
      suggestions: [
        'Break up long-running tasks',
        'Use requestIdleCallback for non-critical work',
        'Implement time slicing',
        'Move heavy computation to Web Workers',
      ],

  }
  /**
   * Set up React profiler
   */
  private setupReactProfiler(): void {
    const hook = (window as any).__REACT_DEVTOOLS_GLOBAL_HOOK__;
    if (!hook) return;
    // Monitor React component renders
    hook.onCommitFiberRoot = (id: any, root: any, priorityLevel: any) => {
      // This would integrate with React DevTools profiler data
      // Implementation would depend on React DevTools API
    };
  }
  /**
   * Set up mutation observer for DOM changes
   */
  private setupMutationObserver(): void {
    if (!('MutationObserver' in window)) return;
    const observer = new MutationObserver((mutations) => {
      const mutationCount = mutations.length;
      if (mutationCount > 100) {
        this.createBottleneck({
          type: 'render',
          location: 'DOM Mutations',
          description: `Excessive DOM mutations: ${mutationCount} changes`,
          impact: Math.min(100, mutationCount / 10),
          duration: 0,
          suggestions: [
            'Batch DOM updates',
            'Use DocumentFragment for multiple insertions',
            'Minimize DOM manipulation in loops',
            'Consider virtual DOM or efficient rendering libraries',
          ],

      }

    observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,

  }
  /**
   * Start bottleneck detection
   */
  private startBottleneckDetection(): void {
    // Periodic analysis of performance patterns
    setInterval(() => {
      this.analyzePerformancePatterns();
      this.generateOptimizationSuggestions();
      this.updateRegressionTests();
    }, 30000); // Every 30 seconds
  }
  /**
   * Analyze profile for bottlenecks
   */
  private analyzeProfileForBottlenecks(profile: PerformanceProfile): void {
    // Determine if this profile represents a bottleneck
    let isBottleneck = false;
    let severity: PerformanceProfile['severity'] = 'low';
    if (profile.duration > 1000) {
      isBottleneck = true;
      severity = profile.duration > 5000 ? 'critical' : profile.duration > 2000 ? 'high' : 'medium';
    }
    // Check for memory usage if available
    if (profile.metadata.memoryUsage && profile.metadata.memoryUsage > 50 * 1024 * 1024) {
      isBottleneck = true;
      severity = 'high';
    }
    profile.bottleneck = isBottleneck;
    profile.severity = severity;
    if (isBottleneck) {
      this.createBottleneck({
        type: profile.type === 'render' ? 'render' : profile.type === 'api' ? 'network' : 'javascript',
        location: profile.name,
        description: `Slow ${profile.type}: ${profile.duration.toFixed(0)}ms`,
        impact: Math.min(100, profile.duration / 50),
        duration: profile.duration,
        suggestions: this.getSuggestionsForProfileType(profile.type, profile.duration),

    }
  }
  /**
   * Get optimization suggestions for profile type
   */
  private getSuggestionsForProfileType(type: PerformanceProfile['type'], duration: number): string[] {
    const suggestions: Record<PerformanceProfile['type'], string[]> = {
      'function': [
        'Optimize algorithm complexity',
        'Use memoization for expensive calculations',
        'Consider lazy evaluation',
        'Profile and optimize hot code paths',
      ],
      'component': [
        'Use React.memo for expensive components',
        'Optimize render logic',
        'Reduce prop drilling',
        'Use useMemo and useCallback appropriately',
      ],
      'api': [
        'Implement request caching',
        'Use request deduplication',
        'Optimize API response size',
        'Consider GraphQL for efficient data fetching',
      ],
      'render': [
        'Minimize DOM manipulations',
        'Use CSS transforms for animations',
        'Implement virtual scrolling for large lists',
        'Optimize CSS selectors',
      ],
      'user-interaction': [
        'Debounce user input handlers',
        'Use passive event listeners',
        'Optimize event delegation',
        'Reduce layout thrashing',
      ],
    };
    return suggestions[type] || [];
  }
  /**
   * Create a bottleneck entry
   */
  private createBottleneck(bottleneck: Omit<Bottleneck, 'id' | 'frequency' | 'priority' | 'detectedAt'>): void {
    const id = `bottleneck-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    // Check if similar bottleneck already exists
    const existing = this.bottlenecks.find(b => 
      b.type === bottleneck.type && 
      b.location === bottleneck.location &&
      Date.now() - b.detectedAt < 60000 // Within last minute
    );
    if (existing) {
      existing.frequency++;
      existing.duration = (existing.duration + bottleneck.duration) / 2; // Average duration
      return;
    }
    const priority = bottleneck.impact > 80 ? 'critical' : 
                    bottleneck.impact > 60 ? 'high' : 
                    bottleneck.impact > 30 ? 'medium' : 'low';
    this.bottlenecks.push({
      id,
      frequency: 1,
      priority,
      detectedAt: Date.now(),
      ...bottleneck,

    // Keep only last 100 bottlenecks
    if (this.bottlenecks.length > 100) {
      this.bottlenecks = this.bottlenecks.slice(-50);
    }
  }
  /**
   * Analyze performance patterns
   */
  private analyzePerformancePatterns(): void {
    if (this.profiles.length < 10) return;
    const recentProfiles = this.profiles.slice(-50);
    // Analyze for patterns
    const patterns = this.identifyPerformancePatterns(recentProfiles);
    patterns.forEach(pattern => {
      this.suggestions.push({
        id: `pattern-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        type: 'architecture',
        title: pattern.title,
        description: pattern.description,
        impact: pattern.impact,
        effort: pattern.effort,
        implementation: pattern.implementation,
        estimatedGain: pattern.estimatedGain,
        confidence: pattern.confidence,


  }
  /**
   * Identify performance patterns
   */
  private identifyPerformancePatterns(profiles: PerformanceProfile[]): OptimizationSuggestion[] {
    const patterns: OptimizationSuggestion[] = [];
    // Pattern: Frequent slow API calls
    const apiProfiles = profiles.filter(p => p.type === 'api' && p.duration > 1000);
    if (apiProfiles.length > 5) {
      patterns.push({
        id: 'frequent-slow-api',
        type: 'architecture',
        title: 'Frequent Slow API Calls',
        description: `Detected ${apiProfiles.length} slow API calls in recent activity`,
        impact: 'high',
        effort: 'medium',
        implementation: 'Implement API response caching and request optimization',
        estimatedGain: 40,
        confidence: 85,

    }
    // Pattern: Excessive rendering
    const renderProfiles = profiles.filter(p => p.type === 'render');
    if (renderProfiles.length > 20) {
      patterns.push({
        id: 'excessive-rendering',
        type: 'code',
        title: 'Excessive Rendering',
        description: `Detected ${renderProfiles.length} render operations in short time`,
        impact: 'medium',
        effort: 'low',
        implementation: 'Optimize component re-renders with memoization',
        codeExample: `
// Use React.memo to prevent unnecessary re-renders
const MyComponent = React.memo(({ data }) => {
  return <div>{data.value}</div>;

// Use useMemo for expensive calculations
const expensiveValue = useMemo(() => {
  return heavyCalculation(data);
}, [data]);
        `,
        estimatedGain: 25,
        confidence: 75,

    }
    return patterns;
  }
  /**
   * Generate optimization suggestions
   */
  private generateOptimizationSuggestions(): void {
    // Clear old suggestions
    this.suggestions = this.suggestions.filter(s => Date.now() - parseInt(s.id.split('-')[1]) < 300000); // Keep for 5 minutes
    // Generate suggestions based on bottlenecks
    const recentBottlenecks = this.bottlenecks.filter(b => Date.now() - b.detectedAt < 300000);
    recentBottlenecks.forEach(bottleneck => {
      if (bottleneck.frequency > 3) { // Recurring bottleneck
        this.suggestions.push({
          id: `suggestion-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          type: 'code',
          title: `Optimize ${bottleneck.location}`,
          description: `Recurring bottleneck detected: ${bottleneck.description}`,
          impact: bottleneck.priority === 'critical' ? 'critical' : bottleneck.priority === 'high' ? 'high' : 'medium',
          effort: 'medium',
          implementation: bottleneck.suggestions.join('. '),
          estimatedGain: Math.min(50, bottleneck.impact),
          confidence: Math.min(90, bottleneck.frequency * 20),

      }

  }
  /**
   * Compare performance between two time periods
   */
  comparePerformance(baselineStart: number, baselineEnd: number, currentStart: number, currentEnd: number): PerformanceComparison[] {
    const baselineProfiles = this.profiles.filter(p => p.startTime >= baselineStart && p.startTime <= baselineEnd);
    const currentProfiles = this.profiles.filter(p => p.startTime >= currentStart && p.startTime <= currentEnd);
    const comparisons: PerformanceComparison[] = [];
    // Group profiles by name for comparison
    const baselineGroups = this.groupProfilesByName(baselineProfiles);
    const currentGroups = this.groupProfilesByName(currentProfiles);
    Object.keys(baselineGroups).forEach(name => {
      if (currentGroups[name]) {
        const baseline = this.calculateMetrics(baselineGroups[name]);
        const current = this.calculateMetrics(currentGroups[name]);
        const improvement = ((baseline.duration - current.duration) / baseline.duration) * 100;
        const significance = this.calculateStatisticalSignificance(baselineGroups[name], currentGroups[name]);
        comparisons.push({
          id: `comparison-${name}-${Date.now()}`,
          name,
          baseline,
          current,
          improvement,
          regression: improvement < -5, // 5% degradation threshold
          significance,

      }

    this.comparisons = comparisons;
    return comparisons;
  }
  /**
   * Group profiles by name
   */
  private groupProfilesByName(profiles: PerformanceProfile[]): Record<string, PerformanceProfile[]> {
    return profiles.reduce((groups, profile) => {
      if (!groups[profile.name]) {
        groups[profile.name] = [];
      }
      groups[profile.name].push(profile);
      return groups;
    }, {} as Record<string, PerformanceProfile[]>);
  }
  /**
   * Calculate performance metrics for a group of profiles
   */
  private calculateMetrics(profiles: PerformanceProfile[]): PerformanceMetrics {
    const durations = profiles.map(p => p.duration);
    const memoryUsages = profiles.map(p => p.metadata.memoryUsage || 0);
    return {
      duration: durations.reduce((sum, d) => sum + d, 0) / durations.length,
      memoryUsage: memoryUsages.reduce((sum, m) => sum + m, 0) / memoryUsages.length,
      cpuUsage: 0, // Would need CPU profiling data
      renderTime: 0, // Would need render timing data
      networkTime: 0, // Would need network timing data
      samples: profiles.length,
    };
  }
  /**
   * Calculate statistical significance of performance difference
   */
  private calculateStatisticalSignificance(baseline: PerformanceProfile[], current: PerformanceProfile[]): number {
    // Simplified t-test calculation
    const baselineDurations = baseline.map(p => p.duration);
    const currentDurations = current.map(p => p.duration);
    if (baselineDurations.length < 2 || currentDurations.length < 2) return 0;
    const baselineMean = baselineDurations.reduce((sum, d) => sum + d, 0) / baselineDurations.length;
    const currentMean = currentDurations.reduce((sum, d) => sum + d, 0) / currentDurations.length;
    const baselineVariance = baselineDurations.reduce((sum, d) => sum + Math.pow(d - baselineMean, 2), 0) / (baselineDurations.length - 1);
    const currentVariance = currentDurations.reduce((sum, d) => sum + Math.pow(d - currentMean, 2), 0) / (currentDurations.length - 1);
    const pooledStdDev = Math.sqrt(((baselineDurations.length - 1) * baselineVariance + (currentDurations.length - 1) * currentVariance) / (baselineDurations.length + currentDurations.length - 2));
    const standardError = pooledStdDev * Math.sqrt(1 / baselineDurations.length + 1 / currentDurations.length);
    if (standardError === 0) return 0;
    const tStat = Math.abs(baselineMean - currentMean) / standardError;
    // Convert t-statistic to approximate p-value (simplified)
    return Math.min(1, Math.max(0, 1 - (tStat / 10)));
  }
  /**
   * Update regression tests
   */
  private updateRegressionTests(): void {
    // Update existing regression tests with new data
    this.regressionTests.forEach(test => {
      const recentProfiles = this.profiles.filter(p => 
        p.name === test.name && 
        Date.now() - p.startTime < 300000 // Last 5 minutes
      );
      if (recentProfiles.length > 0) {
        const avgDuration = recentProfiles.reduce((sum, p) => sum + p.duration, 0) / recentProfiles.length;
        test.currentValue = avgDuration;
        test.history.push({ timestamp: Date.now(), value: avgDuration });
        // Keep only last 100 history points
        if (test.history.length > 100) {
          test.history = test.history.slice(-50);
        }
        // Update status
        const degradation = ((avgDuration - test.baseline) / test.baseline) * 100;
        if (degradation > test.threshold) {
          test.status = 'fail';
        } else if (degradation > test.threshold * 0.7) {
          test.status = 'warning';
        } else {
          test.status = 'pass';
        }
        // Update trend
        if (test.history.length >= 5) {
          const recent = test.history.slice(-5);
          const trend = recent[recent.length - 1].value - recent[0].value;
          if (trend > test.baseline * 0.05) {
            test.trend = 'degrading';
          } else if (trend < -test.baseline * 0.05) {
            test.trend = 'improving';
          } else {
            test.trend = 'stable';
          }
        }
      }

  }
  /**
   * Add a regression test
   */
  addRegressionTest(name: string, baseline: number, threshold: number = 20): void {
    const test: RegressionTest = {
      id: `regression-${name}-${Date.now()}`,
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
  /**
   * Get performance profiles
   */
  getProfiles(limit?: number): PerformanceProfile[] {
    return limit ? this.profiles.slice(-limit) : [...this.profiles];
  }
  /**
   * Get detected bottlenecks
   */
  getBottlenecks(): Bottleneck[] {
    return [...this.bottlenecks].sort((a, b) => {
      const priorityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
      return priorityOrder[b.priority] - priorityOrder[a.priority];

  }
  /**
   * Get optimization suggestions
   */
  getOptimizationSuggestions(): OptimizationSuggestion[] {
    return [...this.suggestions].sort((a, b) => {
      const impactOrder = { critical: 4, high: 3, medium: 2, low: 1 };
      return impactOrder[b.impact] - impactOrder[a.impact];

  }
  /**
   * Get performance comparisons
   */
  getPerformanceComparisons(): PerformanceComparison[] {
    return [...this.comparisons];
  }
  /**
   * Get regression tests
   */
  getRegressionTests(): RegressionTest[] {
    return [...this.regressionTests];
  }
  /**
   * Enable or disable profiler
   */
  setEnabled(enabled: boolean): void {
    this.isEnabled = enabled;
  }
  /**
   * Clear all profiling data
   */
  clear(): void {
    this.profiles = [];
    this.bottlenecks = [];
    this.comparisons = [];
    this.suggestions = [];
    this.activeProfiles.clear();
  }
  /**
   * Destroy the profiler
   */
  destroy(): void {
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];
    this.clear();
  }
}
// Singleton instance
export const performanceProfiler = new PerformanceProfiler();
