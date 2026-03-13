/**
 * Unified Performance Optimizer
 * 
 * Consolidates all performance optimization functionality into a single,
 * production-ready architecture that eliminates code duplication and provides
 * consistent APIs for performance optimization tasks.
 * 
 * Features:
 * - Single source of truth for performance optimization
 * - Modular architecture with clear separation of concerns
 * - Backward compatibility with existing APIs
 * - Comprehensive metrics and monitoring
 * - TypeScript best practices with full type safety
 */

import React, { useCallback, useEffect, useRef, useMemo, useState } from 'react';

// ===== Core Types =====

export interface OptimizerConfig {
  // Monitoring configuration
  monitoring: {
    enabled: boolean;
    sampleRate: number;
    maxSamples: number;
    enableDetailedLogging: boolean;
    enableProfiling: boolean;
  };
  
  // Caching configuration
  caching: {
    enabled: boolean;
    defaultTtl: number;
    maxSize: number;
    enableCompression: boolean;
  };
  
  // Memory management
  memory: {
    enableLeakDetection: boolean;
    enableGCMonitoring: boolean;
    leakThreshold: number;
    cleanupInterval: number;
  };
  
  // Bundle optimization
  bundle: {
    enableCodeSplitting: boolean;
    enableLazyLoading: boolean;
    chunkSizeLimit: number;
    enablePreloading: boolean;
  };
  
  // Animation optimization
  animation: {
    enableReducedMotion: boolean;
    enableRAFOptimization: boolean;
    frameRateTarget: number;
  };
}

export interface PerformanceMetrics {
  // Timing metrics
  timing: {
    fcp?: number;    // First Contentful Paint
    lcp?: number;    // Largest Contentful Paint
    ttfb?: number;   // Time to First Byte
    inp?: number;     // Interaction to Next Paint
    cls?: number;     // Cumulative Layout Shift
  };
  
  // Memory metrics
  memory: {
    used: number;
    total: number;
    limit: number;
    usagePercentage: number;
  };
  
  // Network metrics
  network: {
    downlink: number;
    effectiveType: string;
    rtt: number;
    saveData: boolean;
  };
  
  // Custom metrics
  custom: Record<string, {
    value: number;
    unit: string;
    timestamp: number;
    metadata?: Record<string, unknown>;
  }>;
}

export interface OptimizationRecommendation {
  id: string;
  type: 'performance' | 'memory' | 'network' | 'bundle' | 'animation';
  priority: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  impact: string;
  implementation: string;
  estimatedGain: number; // percentage improvement
  confidence: number; // 0-100
}

export interface PerformanceThresholds {
  timing: {
    fcp: { good: number; poor: number };
    lcp: { good: number; poor: number };
    ttfb: { good: number; poor: number };
    inp: { good: number; poor: number };
    cls: { good: number; poor: number };
  };
  memory: {
    usage: { warning: number; critical: number };
    leaks: { threshold: number };
  };
  network: {
    slowConnection: number; // Mbps threshold
    highLatency: number;  // ms threshold
  };
}

// ===== Default Configuration =====

const DEFAULT_CONFIG: OptimizerConfig = {
  monitoring: {
    enabled: process.env.NODE_ENV === 'development',
    sampleRate: 1.0,
    maxSamples: 100,
    enableDetailedLogging: false,
    enableProfiling: false,
  },
  caching: {
    enabled: true,
    defaultTtl: 300000, // 5 minutes
    maxSize: 1000,
    enableCompression: true,
  },
  memory: {
    enableLeakDetection: true,
    enableGCMonitoring: true,
    leakThreshold: 0.8, // 80% usage threshold
    cleanupInterval: 60000, // 1 minute
  },
  bundle: {
    enableCodeSplitting: true,
    enableLazyLoading: true,
    chunkSizeLimit: 244 * 1024, // 244KB
    enablePreloading: true,
  },
  animation: {
    enableReducedMotion: true,
    enableRAFOptimization: true,
    frameRateTarget: 60,
  },
};

const DEFAULT_THRESHOLDS: PerformanceThresholds = {
  timing: {
    fcp: { good: 1800, poor: 3000 },
    lcp: { good: 2500, poor: 4000 },
    ttfb: { good: 800, poor: 1800 },
    inp: { good: 200, poor: 500 },
    cls: { good: 0.1, poor: 0.25 },
  },
  memory: {
    usage: { warning: 70, critical: 90 },
    leaks: { threshold: 50 * 1024 * 1024 }, // 50MB
  },
  network: {
    slowConnection: 1.5, // Mbps
    highLatency: 1000, // ms
  },
};

// ===== Core Optimizer Class =====

export class UnifiedOptimizer {
  private config: OptimizerConfig;
  private thresholds: PerformanceThresholds;
  private metrics: PerformanceMetrics;
  private recommendations: OptimizationRecommendation[] = [];
  
  // Observers and timers
  private observers: PerformanceObserver[] = [];
  private timers: NodeJS.Timeout[] = [];
  private cleanupCallbacks: (() => void)[] = [];
  
  // Caching
  private cache: Map<string, { data: unknown; timestamp: number; ttl: number }> = new Map();
  
  // Memory tracking
  private memorySnapshots: number[] = [];
  private lastGCTime = 0;
  
  // Performance tracking
  private measurements: Map<string, number[]> = new Map();
  private activeProfiles: Map<string, number> = new Map();
  
  constructor(config: Partial<OptimizerConfig> = {}) {
    this.config = this.mergeConfig(DEFAULT_CONFIG, config);
    this.thresholds = DEFAULT_THRESHOLDS;
    this.metrics = this.initializeMetrics();
    
    if (typeof window !== 'undefined') {
      this.initialize();
    }
  }
  
  // ===== Initialization =====
  
  private initialize(): void {
    if (this.config.monitoring.enabled) {
      this.setupPerformanceObservers();
      this.setupMemoryMonitoring();
      this.setupNetworkMonitoring();
      this.startPeriodicCleanup();
    }
    
    this.logInfo('Unified Performance Optimizer initialized', {
      config: this.config,
      thresholds: this.thresholds,
    });
  }
  
  private setupPerformanceObservers(): void {
    if (!('PerformanceObserver' in window)) return;
    
    try {
      // Core Web Vitals
      this.observeWebVitals();
      
      // Resource timing
      this.observeResourceTiming();
      
      // Long tasks
      this.observeLongTasks();
      
      // Navigation timing
      this.observeNavigationTiming();
    } catch (error) {
      this.logError('Failed to setup performance observers', { error });
    }
  }
  
  private observeWebVitals(): void {
    // LCP
    this.createObserver('largest-contentful-paint', (list) => {
      const entries = list.getEntries();
      const last = entries[entries.length - 1] as PerformanceEntry;
      this.metrics.timing.lcp = last.startTime;
      this.checkThreshold('lcp', last.startTime);
    });
    
    // FCP
    this.createObserver('paint', (list) => {
      const entries = list.getEntries();
      const fcp = entries.find(e => e.name === 'first-contentful-paint');
      if (fcp) {
        this.metrics.timing.fcp = fcp.startTime;
        this.checkThreshold('fcp', fcp.startTime);
      }
    });
    
    // CLS
    let clsValue = 0;
    this.createObserver('layout-shift', (list) => {
      const entries = list.getEntries();
      entries.forEach(entry => {
        const shift = entry as LayoutShift;
        if (!shift.hadRecentInput) {
          clsValue += shift.value || 0;
        }
      });
      this.metrics.timing.cls = clsValue;
      this.checkThreshold('cls', clsValue);
    });
    
    // INP/FID
    let inpValue = 0;
    this.createObserver('event', (list) => {
      const entries = list.getEntries();
      entries.forEach(entry => {
        const event = entry as PerformanceEventTiming;
        if (event.duration > 0 && !this.isContinuousInteraction(entry.name)) {
          inpValue = Math.max(inpValue, event.duration);
        }
      });
      this.metrics.timing.inp = inpValue;
      this.checkThreshold('inp', inpValue);
    });
  }
  
  private observeResourceTiming(): void {
    this.createObserver('resource', (list) => {
      const entries = list.getEntries();
      entries.forEach(entry => {
        const resource = entry as PerformanceResourceTiming;
        
        // Track slow resources
        if (resource.duration > 2000) {
          this.addRecommendation({
            id: `slow-resource-${Date.now()}`,
            type: 'network',
            priority: 'medium',
            title: 'Slow Resource Detected',
            description: `Resource ${resource.name} took ${resource.duration}ms to load`,
            impact: 'Degraded user experience',
            implementation: 'Optimize resource size, enable compression, use CDN',
            estimatedGain: 25,
            confidence: 80,
          });
        }
        
        // Track large resources
        if ((resource.transferSize || 0) > 1024 * 1024) { // 1MB
          this.addRecommendation({
            id: `large-resource-${Date.now()}`,
            type: 'bundle',
            priority: 'high',
            title: 'Large Resource Detected',
            description: `Resource ${resource.name} is ${((resource.transferSize || 0) / 1024 / 1024).toFixed(1)}MB`,
            impact: 'Slow initial load',
            implementation: 'Compress, optimize, or split large resources',
            estimatedGain: 40,
            confidence: 90,
          });
        }
      });
    });
  }
  
  private observeLongTasks(): void {
    this.createObserver('longtask', (list) => {
      const entries = list.getEntries();
      entries.forEach(entry => {
        if (entry.duration > 50) {
          this.addRecommendation({
            id: `long-task-${Date.now()}`,
            type: 'performance',
            priority: 'high',
            title: 'Long Task Detected',
            description: `Main thread blocked for ${entry.duration}ms`,
            impact: 'UI jank and poor responsiveness',
            implementation: 'Break up long tasks, use Web Workers, optimize algorithms',
            estimatedGain: 60,
            confidence: 85,
          });
        }
      });
    });
  }
  
  private observeNavigationTiming(): void {
    this.createObserver('navigation', (list) => {
      const entries = list.getEntries();
      entries.forEach(entry => {
        const nav = entry as PerformanceNavigationTiming;
        
        // TTFB
        const ttfb = nav.responseStart - nav.requestStart;
        this.metrics.timing.ttfb = ttfb;
        this.checkThreshold('ttfb', ttfb);
        
        // Page load time
        const loadTime = nav.loadEventEnd - nav.fetchStart;
        this.recordMetric('page-load', loadTime);
      });
    });
  }
  
  private setupMemoryMonitoring(): void {
    if (!('memory' in performance)) return;
    
    const checkMemory = () => {
      const memory = (performance as any).memory;
      const used = memory.usedJSHeapSize;
      const total = memory.totalJSHeapSize;
      const limit = memory.jsHeapSizeLimit;
      
      this.metrics.memory = {
        used,
        total,
        limit,
        usagePercentage: (used / total) * 100,
      };
      
      // Check for memory leaks
      if (this.config.memory.enableLeakDetection) {
        this.memorySnapshots.push(used);
        if (this.memorySnapshots.length > 10) {
          this.memorySnapshots.shift();
        }
        
        this.detectMemoryLeaks();
      }
      
      // Check memory thresholds
      const usagePercent = this.metrics.memory.usagePercentage;
      if (usagePercent > this.thresholds.memory.usage.critical) {
        this.addRecommendation({
          id: `high-memory-${Date.now()}`,
          type: 'memory',
          priority: 'critical',
          title: 'High Memory Usage',
          description: `Memory usage at ${usagePercent.toFixed(1)}%`,
          impact: 'Potential crashes and poor performance',
          implementation: 'Release unused objects, clear caches, optimize data structures',
          estimatedGain: 70,
          confidence: 95,
        });
      }
    };
    
    // Check memory every 5 seconds
    const interval = setInterval(checkMemory, 5000);
    this.timers.push(interval);
    
    // Initial check
    checkMemory();
  }
  
  private setupNetworkMonitoring(): void {
    if (!('connection' in navigator)) return;
    
    const connection = (navigator as any).connection;
    
    const updateNetworkInfo = () => {
      this.metrics.network = {
        downlink: connection.downlink || 0,
        effectiveType: connection.effectiveType || 'unknown',
        rtt: connection.rtt || 0,
        saveData: connection.saveData || false,
      };
      
      // Check for slow connection
      if (connection.downlink < this.thresholds.network.slowConnection) {
        this.addRecommendation({
          id: `slow-connection-${Date.now()}`,
          type: 'network',
          priority: 'medium',
          title: 'Slow Network Connection',
          description: `Connection speed: ${connection.downlink}Mbps`,
          impact: 'Slow resource loading',
          implementation: 'Optimize resource sizes, enable compression, use adaptive loading',
          estimatedGain: 30,
          confidence: 75,
        });
      }
    };
    
    connection.addEventListener('change', updateNetworkInfo);
    this.cleanupCallbacks.push(() => {
      connection.removeEventListener('change', updateNetworkInfo);
    });
    
    updateNetworkInfo();
  }
  
  // ===== Memory Management =====
  
  private detectMemoryLeaks(): void {
    if (this.memorySnapshots.length < 6) return;
    
    let increasingCount = 0;
    for (let i = 1; i < this.memorySnapshots.length; i++) {
      if (this.memorySnapshots[i] > this.memorySnapshots[i - 1]) {
        increasingCount++;
      }
    }
    
    // If 80% of snapshots show increasing memory, flag as potential leak
    if (increasingCount >= Math.floor(this.memorySnapshots.length * 0.8)) {
      this.addRecommendation({
        id: `memory-leak-${Date.now()}`,
        type: 'memory',
        priority: 'critical',
        title: 'Potential Memory Leak Detected',
        description: 'Memory usage consistently increasing over time',
        impact: 'Progressive performance degradation and potential crashes',
        implementation: 'Check for unclosed event listeners, circular references, and growing caches',
        estimatedGain: 80,
        confidence: 70,
      });
    }
  }
  
  // ===== Caching =====
  
  setCache<T>(key: string, data: T, ttl?: number): void {
    if (!this.config.caching.enabled) return;
    
    const cacheTtl = ttl || this.config.caching.defaultTtl;
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl: cacheTtl,
    });
    
    // Cleanup old entries
    if (this.cache.size > this.config.caching.maxSize) {
      this.cleanupCache();
    }
  }
  
  getCache<T>(key: string): T | null {
    if (!this.config.caching.enabled) return null;
    
    const entry = this.cache.get(key);
    if (!entry) return null;
    
    if (Date.now() - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return null;
    }
    
    return entry.data as T;
  }
  
  clearCache(key?: string): void {
    if (key) {
      this.cache.delete(key);
    } else {
      this.cache.clear();
    }
  }
  
  private cleanupCache(): void {
    const now = Date.now();
    const entries = Array.from(this.cache.entries());
    
    // Sort by timestamp (oldest first)
    entries.sort((a, b) => a[1].timestamp - b[1].timestamp);
    
    // Remove expired entries
    entries.forEach(([key, entry]) => {
      if (now - entry.timestamp > entry.ttl) {
        this.cache.delete(key);
      }
    });
    
    // If still too large, remove oldest entries
    while (this.cache.size > this.config.caching.maxSize) {
      const oldestKey = entries.shift()?.[0];
      if (oldestKey) {
        this.cache.delete(oldestKey);
      }
    }
  }
  
  // ===== Performance Measurement =====
  
  startMeasure(name: string): string {
    const id = `${name}-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
    this.activeProfiles.set(id, performance.now());
    
    if (this.config.monitoring.enableDetailedLogging) {
      this.logDebug(`Started measurement: ${name}`, { id });
    }
    
    return id;
  }
  
  endMeasure(id: string): number | null {
    const startTime = this.activeProfiles.get(id);
    if (!startTime) return null;
    
    const endTime = performance.now();
    const duration = endTime - startTime;
    
    this.activeProfiles.delete(id);
    this.recordMetric(id.split('-')[0], duration);
    
    if (this.config.monitoring.enableDetailedLogging) {
      this.logDebug(`Ended measurement: ${id}`, { duration });
    }
    
    return duration;
  }
  
  measureFunction<T>(name: string, fn: () => T): T {
    const id = this.startMeasure(name);
    try {
      return fn();
    } finally {
      this.endMeasure(id);
    }
  }
  
  async measureAsyncFunction<T>(name: string, fn: () => Promise<T>): Promise<T> {
    const id = this.startMeasure(name);
    try {
      return await fn();
    } finally {
      this.endMeasure(id);
    }
  }
  
  private recordMetric(name: string, value: number): void {
    if (!this.measurements.has(name)) {
      this.measurements.set(name, []);
    }
    
    const measurements = this.measurements.get(name)!;
    measurements.push(value);
    
    // Keep only recent measurements
    if (measurements.length > this.config.monitoring.maxSamples) {
      measurements.shift();
    }
  }
  
  // ===== React Hooks =====
  
  useDebounce<T extends (...args: any[]) => any>(
    callback: T,
    delay: number,
    deps: React.DependencyList = []
  ): T {
    const timeoutRef = useRef<NodeJS.Timeout>();
    const callbackRef = useRef(callback);
    
    useEffect(() => {
      callbackRef.current = callback;
    }, [callback]);
    
    return useCallback((...args: Parameters<T>) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      
      timeoutRef.current = setTimeout(() => {
        callbackRef.current(...args);
      }, delay);
    }, deps) as T;
  }
  
  useThrottle<T extends (...args: any[]) => any>(
    callback: T,
    delay: number,
    deps: React.DependencyList = []
  ): T {
    const lastCallRef = useRef<number>(0);
    const callbackRef = useRef(callback);
    
    useEffect(() => {
      callbackRef.current = callback;
    }, [callback]);
    
    return useCallback((...args: Parameters<T>) => {
      const now = Date.now();
      if (now - lastCallRef.current >= delay) {
        lastCallRef.current = now;
        callbackRef.current(...args);
      }
    }, deps) as T;
  }
  
  useDeepMemo<T>(value: T, deps: React.DependencyList): T {
    const ref = useRef<{ deps: React.DependencyList; value: T }>({
      deps: [],
      value: value as T,
    });
    
    const startTime = performance.now();
    
    if (!deps || !ref.current.deps || !this.areDepsEqual(deps, ref.current.deps)) {
      ref.current.deps = [...(deps || [])];
      ref.current.value = value;
      this.recordMetric('deep-memo-calculation', performance.now() - startTime);
    } else {
      this.recordMetric('deep-memo-cache-hit', performance.now() - startTime);
    }
    
    return ref.current.value;
  }
  
  useVirtualScroll<T>({
    items,
    itemHeight,
    containerHeight,
    overscan = 5,
  }: {
    items: T[];
    itemHeight: number;
    containerHeight: number;
    overscan?: number;
  }) {
    const [scrollTop, setScrollTop] = useState(0);
    
    const visibleItems = useMemo(() => {
      const startTime = performance.now();
      
      const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
      const endIndex = Math.min(
        items.length - 1,
        Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
      );
      
      const result = items.slice(startIndex, endIndex + 1).map((item, index) => ({
        item,
        index: startIndex + index,
      }));
      
      this.recordMetric('virtual-scroll-calculation', performance.now() - startTime);
      return result;
    }, [items, itemHeight, containerHeight, scrollTop, overscan]);
    
    const totalHeight = items.length * itemHeight;
    
    return {
      visibleItems,
      totalHeight,
      onScroll: useCallback((e: React.UIEvent<HTMLDivElement>) => {
        const startTime = performance.now();
        setScrollTop(e.currentTarget.scrollTop);
        this.recordMetric('virtual-scroll', performance.now() - startTime);
      }, []),
    };
  }
  
  // ===== Public API =====
  
  getMetrics(): PerformanceMetrics {
    return { ...this.metrics };
  }
  
  getRecommendations(): OptimizationRecommendation[] {
    return [...this.recommendations].sort((a, b) => {
      const priorityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
      return priorityOrder[b.priority] - priorityOrder[a.priority];
    });
  }
  
  clearRecommendations(): void {
    this.recommendations = [];
  }
  
  updateConfig(config: Partial<OptimizerConfig>): void {
    this.config = this.mergeConfig(this.config, config);
    this.logInfo('Configuration updated', { config: this.config });
  }
  
  getConfig(): OptimizerConfig {
    return { ...this.config };
  }
  
  generateReport(): {
    timestamp: number;
    metrics: PerformanceMetrics;
    recommendations: OptimizationRecommendation[];
    summary: {
      totalIssues: number;
      criticalIssues: number;
      performanceScore: number;
    };
  } {
    const recommendations = this.getRecommendations();
    const criticalIssues = recommendations.filter(r => r.priority === 'critical').length;
    
    // Calculate performance score (0-100)
    const performanceScore = this.calculatePerformanceScore();
    
    return {
      timestamp: Date.now(),
      metrics: this.getMetrics(),
      recommendations,
      summary: {
        totalIssues: recommendations.length,
        criticalIssues,
        performanceScore,
      },
    };
  }
  
  // ===== Cleanup =====
  
  destroy(): void {
    // Disconnect observers
    this.observers.forEach(observer => {
      try {
        observer.disconnect();
      } catch (error) {
        this.logError('Error disconnecting observer', { error });
      }
    });
    this.observers = [];
    
    // Clear timers
    this.timers.forEach(timer => clearInterval(timer));
    this.timers = [];
    
    // Run cleanup callbacks
    this.cleanupCallbacks.forEach(callback => callback());
    this.cleanupCallbacks = [];
    
    // Clear data
    this.cache.clear();
    this.measurements.clear();
    this.activeProfiles.clear();
    this.memorySnapshots = [];
    
    this.logInfo('Unified Performance Optimizer destroyed');
  }
  
  // ===== Private Helpers =====
  
  private mergeConfig(base: OptimizerConfig, override: Partial<OptimizerConfig>): OptimizerConfig {
    return {
      monitoring: { ...base.monitoring, ...override.monitoring },
      caching: { ...base.caching, ...override.caching },
      memory: { ...base.memory, ...override.memory },
      bundle: { ...base.bundle, ...override.bundle },
      animation: { ...base.animation, ...override.animation },
    };
  }
  
  private initializeMetrics(): PerformanceMetrics {
    return {
      timing: {},
      memory: { used: 0, total: 0, limit: 0, usagePercentage: 0 },
      network: { downlink: 0, effectiveType: 'unknown', rtt: 0, saveData: false },
      custom: {},
    };
  }
  
  private createObserver(type: string, callback: PerformanceObserverCallback): void {
    try {
      const observer = new PerformanceObserver(callback);
      observer.observe({ type, buffered: true });
      this.observers.push(observer);
    } catch (error) {
      this.logError(`Failed to create ${type} observer`, { error });
    }
  }
  
  private checkThreshold(metric: keyof PerformanceThresholds['timing'], value: number): void {
    const threshold = this.thresholds.timing[metric];
    if (!threshold) return;
    
    if (value > threshold.poor) {
      this.addRecommendation({
        id: `${metric}-poor-${Date.now()}`,
        type: 'performance',
        priority: 'high',
        title: `Poor ${metric.toUpperCase()} Performance`,
        description: `${metric.toUpperCase()} is ${value}ms (threshold: ${threshold.poor}ms)`,
        impact: 'Poor user experience',
        implementation: `Optimize ${metric} through various techniques`,
        estimatedGain: 50,
        confidence: 90,
      });
    } else if (value > threshold.good) {
      this.addRecommendation({
        id: `${metric}-needs-improvement-${Date.now()}`,
        type: 'performance',
        priority: 'medium',
        title: `${metric.toUpperCase()} Needs Improvement`,
        description: `${metric.toUpperCase()} is ${value}ms (threshold: ${threshold.good}ms)`,
        impact: 'Suboptimal user experience',
        implementation: `Optimize ${metric} for better performance`,
        estimatedGain: 30,
        confidence: 75,
      });
    }
  }
  
  private addRecommendation(recommendation: OptimizationRecommendation): void {
    // Avoid duplicate recommendations
    const exists = this.recommendations.some(r => 
      r.type === recommendation.type && 
      r.title === recommendation.title &&
      Date.now() - parseInt(r.id.split('-').pop() || '0') < 60000 // Within last minute
    );
    
    if (!exists) {
      this.recommendations.push(recommendation);
      
      if (this.config.monitoring.enableDetailedLogging) {
        this.logInfo('Recommendation added', { recommendation });
      }
    }
  }
  
  private calculatePerformanceScore(): number {
    let score = 100;
    
    // Deduct points for timing issues
    Object.entries(this.metrics.timing).forEach(([metric, value]) => {
      if (!value) return;
      
      const threshold = this.thresholds.timing[metric as keyof PerformanceThresholds['timing']];
      if (!threshold) return;
      
      if (value > threshold.poor) {
        score -= 20;
      } else if (value > threshold.good) {
        score -= 10;
      }
    });
    
    // Deduct points for memory issues
    if (this.metrics.memory.usagePercentage > this.thresholds.memory.usage.critical) {
      score -= 25;
    } else if (this.metrics.memory.usagePercentage > this.thresholds.memory.usage.warning) {
      score -= 15;
    }
    
    // Deduct points for network issues
    if (this.metrics.network.downlink < this.thresholds.network.slowConnection) {
      score -= 15;
    }
    
    return Math.max(0, Math.min(100, score));
  }
  
  private isContinuousInteraction(name: string): boolean {
    const continuous = ['scroll', 'mousemove', 'pointermove'];
    return continuous.some(type => name.toLowerCase().includes(type));
  }
  
  private areDepsEqual(a: React.DependencyList, b: React.DependencyList): boolean {
    if (a === b) return true;
    if (a.length !== b.length) return false;
    
    for (let i = 0; i < a.length; i++) {
      if (a[i] !== b[i]) return false;
    }
    
    return true;
  }
  
  private startPeriodicCleanup(): void {
    const interval = setInterval(() => {
      this.cleanupCache();
      this.cleanupOldMeasurements();
      this.cleanupOldRecommendations();
    }, this.config.memory.cleanupInterval);
    
    this.timers.push(interval);
  }
  
  private cleanupOldMeasurements(): void {
    this.measurements.forEach((measurements, name) => {
      if (measurements.length > this.config.monitoring.maxSamples) {
        this.measurements.set(name, measurements.slice(-this.config.monitoring.maxSamples));
      }
    });
  }
  
  private cleanupOldRecommendations(): void {
    const oneHourAgo = Date.now() - 3600000;
    this.recommendations = this.recommendations.filter(r => 
      parseInt(r.id.split('-').pop() || '0') > oneHourAgo
    );
  }
  
  private logInfo(message: string, details?: Record<string, unknown>): void {
    if (this.config.monitoring.enableDetailedLogging) {
      console.info(`[UnifiedOptimizer] ${message}`, details);
    }
  }
  
  private logError(message: string, details?: Record<string, unknown>): void {
    console.error(`[UnifiedOptimizer] ${message}`, details);
  }
  
  private logDebug(message: string, details?: Record<string, unknown>): void {
    if (this.config.monitoring.enableDetailedLogging) {
      console.debug(`[UnifiedOptimizer] ${message}`, details);
    }
  }
}

// ===== Singleton Instance =====

let instance: UnifiedOptimizer | null = null;

export function getOptimizer(config?: Partial<OptimizerConfig>): UnifiedOptimizer {
  if (!instance) {
    instance = new UnifiedOptimizer(config);
  } else if (config) {
    instance.updateConfig(config);
  }
  return instance;
}

export function initializeOptimizer(config?: Partial<OptimizerConfig>): UnifiedOptimizer {
  instance = new UnifiedOptimizer(config);
  return instance;
}

export function destroyOptimizer(): void {
  if (instance) {
    instance.destroy();
    instance = null;
  }
}

// ===== Backward Compatibility Exports =====

// Re-export as default for compatibility
export default UnifiedOptimizer;

// Legacy exports
export const PerformanceOptimizer = UnifiedOptimizer;
export const getPerformanceOptimizer = getOptimizer;
export const initializePerformanceOptimizer = initializeOptimizer;
export const shutdownPerformanceOptimizer = destroyOptimizer;