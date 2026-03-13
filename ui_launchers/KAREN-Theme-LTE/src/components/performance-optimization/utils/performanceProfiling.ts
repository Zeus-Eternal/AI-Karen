/**
 * Performance Profiling and Bottleneck Detection
 * Advanced performance profiling with intelligent bottleneck detection
 */

'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { ProfileResult, Bottleneck } from '../types';
import { usePerformanceOptimizationStore } from '../store/performanceOptimizationStore';

// Profiling configuration
interface ProfilingConfig {
  enabled: boolean;
  sampleInterval: number; // ms
  maxSamples: number;
  longTaskThreshold: number; // ms
  memoryThreshold: number; // MB
  enableFlameGraph: boolean;
  enableCPUProfiling: boolean;
  enableMemoryProfiling: boolean;
  enableNetworkProfiling: boolean;
}

// Performance sample data
interface PerformanceSample {
  timestamp: number;
  cpu: number;
  memory: number;
  network: number;
  frameTime?: number;
  longTasks?: Array<{ startTime: number; duration: number; type: string; attribution?: unknown }>;
  domNodes?: number;
  reflows?: number;
  repaints?: number;
}

interface PerformanceWithMemory extends Performance {
  memory?: {
    usedJSHeapSize: number;
  };
}

// Profiling manager class
class ProfilingManager {
  private config: ProfilingConfig;
  private isProfiling = false;
  private samples: PerformanceSample[] = [];
  private profilingInterval: NodeJS.Timeout | null = null;
  private observers: PerformanceObserver[] = [];
  private startTimestamp = 0;
  private frameCount = 0;
  private lastFrameTime = 0;

  constructor(config: Partial<ProfilingConfig> = {}) {
    this.config = {
      enabled: true,
      sampleInterval: 100, // 100ms
      maxSamples: 1000,
      longTaskThreshold: 50, // 50ms
      memoryThreshold: 100, // 100MB
      enableFlameGraph: false,
      enableCPUProfiling: true,
      enableMemoryProfiling: true,
      enableNetworkProfiling: true,
      ...config,
    };
  }

  // Start profiling
  startProfiling(): void {
    if (this.isProfiling || !this.config.enabled) return;

    this.isProfiling = true;
    this.startTimestamp = performance.now();
    this.samples = [];
    this.frameCount = 0;
    this.lastFrameTime = 0;

    // Set up performance observers
    this.setupObservers();

    // Start sampling interval
    this.profilingInterval = setInterval(() => {
      this.collectSample();
    }, this.config.sampleInterval);

    // Start frame timing
    this.startFrameTiming();
  }

  // Stop profiling
  stopProfiling(): ProfileResult | null {
    if (!this.isProfiling) return null;

    this.isProfiling = false;

    // Clear interval
    if (this.profilingInterval) {
      clearInterval(this.profilingInterval);
      this.profilingInterval = null;
    }

    // Disconnect observers
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];

    // Stop frame timing
    this.stopFrameTiming();

    // Analyze samples and generate profile
    return this.analyzeSamples();
  }

  // Set up performance observers
  private setupObservers(): void {
    // Long task observer
    if (this.config.enableCPUProfiling && 'PerformanceObserver' in window) {
      try {
        const longTaskObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry: PerformanceEntry & { duration?: number; startTime?: number; name?: string; attribution?: unknown }) => {
            if (entry.duration && entry.duration > this.config.longTaskThreshold) {
              // Record long task
              const sample = this.getCurrentSample();
              if (sample) {
                if (!sample.longTasks) sample.longTasks = [];
                sample.longTasks.push({
                  startTime: entry.startTime,
                  duration: entry.duration,
                  type: entry.name || 'unknown',
                  attribution: entry.attribution,
                });
              }
            }
          });
        });

        longTaskObserver.observe({ entryTypes: ['longtask'] });
        this.observers.push(longTaskObserver);
      } catch (e) {
        console.warn('Long task observer not supported:', e);
      }
    }

    // Memory observer
    if (this.config.enableMemoryProfiling && 'PerformanceObserver' in window) {
      try {
        const memoryObserver = new PerformanceObserver(() => {
          // Memory pressure events would be handled here
          // This is browser-dependent and may not be widely supported
        });

        // Try to observe memory pressure events
        try {
          memoryObserver.observe({ entryTypes: ['measure'] });
          this.observers.push(memoryObserver);
        } catch (e) {
          console.warn('Memory observer not supported:', e);
        }
      } catch (e) {
        console.warn('Memory observer setup failed:', e);
      }
    }

    // Network observer
    if (this.config.enableNetworkProfiling && 'PerformanceObserver' in window) {
      try {
        const networkObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry: PerformanceEntry & { duration?: number; startTime?: number; name?: string }) => {
            // Network resource timing
            const sample = this.getCurrentSample();
            if (sample) {
              // Track slow network requests
              if (entry.duration > 1000) { // > 1s
                sample.network = Math.max(sample.network, entry.duration);
              }
            }
          });
        });

        networkObserver.observe({ entryTypes: ['resource'] });
        this.observers.push(networkObserver);
      } catch (e) {
        console.warn('Network observer not supported:', e);
      }
    }
  }

  // Start frame timing
  private startFrameTiming(): void {
    if ('requestAnimationFrame' in window) {
      const measureFrame = (timestamp: number) => {
        if (this.lastFrameTime > 0) {
          const frameTime = timestamp - this.lastFrameTime;
          const sample = this.getCurrentSample();
          if (sample) {
            sample.frameTime = frameTime;
            this.frameCount++;
          }
        }
        this.lastFrameTime = timestamp;

        if (this.isProfiling) {
          requestAnimationFrame(measureFrame);
        }
      };

      requestAnimationFrame(measureFrame);
    }
  }

  // Stop frame timing
  private stopFrameTiming(): void {
    // Frame timing will stop automatically when isProfiling is false
  }

  // Collect a performance sample
  private collectSample(): void {
    const now = performance.now();
    const sample: PerformanceSample = {
      timestamp: now,
      cpu: this.measureCPU(),
      memory: this.measureMemory(),
      network: this.measureNetwork(),
      domNodes: this.measureDOMNodes(),
      reflows: this.measureReflows(),
      repaints: this.measureRepaints(),
    };

    this.samples.push(sample);

    // Limit sample count
    if (this.samples.length > this.config.maxSamples) {
      this.samples = this.samples.slice(-this.config.maxSamples);
    }
  }

  // Get current sample or create new one
  private getCurrentSample(): PerformanceSample | null {
    return this.samples.length > 0 ? this.samples[this.samples.length - 1] as PerformanceSample : null;
  }

  // Measure CPU usage
  private measureCPU(): number {
    // This is a simplified CPU measurement
    // In a real implementation, you'd use more sophisticated methods
    
    // Check for long tasks in recent sample
    const sample = this.getCurrentSample();
    if (sample && sample.longTasks && sample.longTasks.length > 0) {
      // Calculate CPU impact from long tasks
      const totalLongTaskTime = sample.longTasks.reduce((sum, task) => sum + task.duration, 0);
      const timeWindow = 100; // 100ms window
      return Math.min(100, (totalLongTaskTime / timeWindow) * 100);
    }

    // Check frame rate
    if (sample && sample.frameTime) {
      const targetFrameTime = 16.67; // 60fps
      if (sample.frameTime > targetFrameTime * 2) {
        return 80; // High CPU usage
      } else if (sample.frameTime > targetFrameTime * 1.5) {
        return 60; // Medium CPU usage
      }
    }

    return 0; // Normal CPU usage
  }

  // Measure memory usage
  private measureMemory(): number {
    if ('memory' in performance) {
      const memory = (performance as PerformanceWithMemory).memory;
      if (memory) {
        return Math.round(memory.usedJSHeapSize / 1048576); // Convert to MB
      }
    }
    return 0;
  }

  // Measure network performance
  private measureNetwork(): number {
    // This would measure network performance
    // For now, return 0
    return 0;
  }

  // Measure DOM nodes
  private measureDOMNodes(): number {
    return document.querySelectorAll('*').length;
  }

  // Measure reflows
  private measureReflows(): number {
    // This would require more sophisticated measurement
    // For now, return 0
    return 0;
  }

  // Measure repaints
  private measureRepaints(): number {
    // This would require more sophisticated measurement
    // For now, return 0
    return 0;
  }

  // Analyze samples and generate profile
  private analyzeSamples(): ProfileResult {
    if (this.samples.length === 0) {
      return {
        id: `profile-${Date.now()}`,
        name: 'Empty Profile',
        startTime: this.startTimestamp,
        endTime: performance.now(),
        duration: performance.now() - this.startTimestamp,
        samples: [],
        bottlenecks: [],
        recommendations: ['No samples collected'],
        timestamp: new Date(),
      };
    }

    // Detect bottlenecks
    const bottlenecks = this.detectBottlenecks();
    
    // Generate recommendations
    const recommendations = this.generateRecommendations(bottlenecks);

    return {
      id: `profile-${Date.now()}`,
      name: `Performance Profile ${new Date().toISOString()}`,
      startTime: this.startTimestamp,
      endTime: performance.now(),
      duration: performance.now() - this.startTimestamp,
      samples: this.samples.map(sample => ({
        timestamp: sample.timestamp,
        cpu: sample.cpu,
        memory: sample.memory,
        network: sample.network,
        frameTime: sample.frameTime,
        longTasks: (sample.longTasks || []).map(lt => ({
          ...lt,
          attribution: lt.attribution as string | undefined,
        })),
      })),
      bottlenecks,
      recommendations,
      timestamp: new Date(),
    };
  }

  // Detect bottlenecks from samples
  private detectBottlenecks(): Bottleneck[] {
    const bottlenecks: Bottleneck[] = [];

    // CPU bottlenecks
    const cpuBottleneck = this.detectCPUBottleneck();
    if (cpuBottleneck) {
      bottlenecks.push(cpuBottleneck);
    }

    // Memory bottlenecks
    const memoryBottleneck = this.detectMemoryBottleneck();
    if (memoryBottleneck) {
      bottlenecks.push(memoryBottleneck);
    }

    // Network bottlenecks
    const networkBottleneck = this.detectNetworkBottleneck();
    if (networkBottleneck) {
      bottlenecks.push(networkBottleneck);
    }

    // Rendering bottlenecks
    const renderingBottleneck = this.detectRenderingBottleneck();
    if (renderingBottleneck) {
      bottlenecks.push(renderingBottleneck);
    }

    // JavaScript bottlenecks
    const jsBottleneck = this.detectJavaScriptBottleneck();
    if (jsBottleneck) {
      bottlenecks.push(jsBottleneck);
    }

    return bottlenecks;
  }

  // Detect CPU bottlenecks
  private detectCPUBottleneck(): Bottleneck | null {
    const avgCPU = this.samples.reduce((sum, sample) => sum + sample.cpu, 0) / this.samples.length;
    
    if (avgCPU > 80) {
      return {
        type: 'cpu',
        severity: 'high',
        description: `High CPU usage detected: ${avgCPU.toFixed(1)}%`,
        impact: 'Reduced responsiveness and battery life',
        recommendation: 'Optimize JavaScript execution, reduce computational complexity',
      };
    } else if (avgCPU > 60) {
      return {
        type: 'cpu',
        severity: 'medium',
        description: `Moderate CPU usage: ${avgCPU.toFixed(1)}%`,
        impact: 'Some performance degradation',
        recommendation: 'Consider optimizing animations and computations',
      };
    }

    return null;
  }

  // Detect memory bottlenecks
  private detectMemoryBottleneck(): Bottleneck | null {
    const avgMemory = this.samples.reduce((sum, sample) => sum + sample.memory, 0) / this.samples.length;
    const maxMemory = Math.max(...this.samples.map(sample => sample.memory));
    
    if (avgMemory > this.config.memoryThreshold) {
      return {
        type: 'memory',
        severity: 'high',
        description: `High memory usage: ${avgMemory.toFixed(1)}MB (peak: ${maxMemory.toFixed(1)}MB)`,
        impact: 'Increased risk of crashes and slow performance',
        recommendation: 'Reduce memory allocations, implement object pooling',
      };
    } else if (maxMemory > this.config.memoryThreshold * 1.5) {
      return {
        type: 'memory',
        severity: 'medium',
        description: `Memory spikes detected: peak ${maxMemory.toFixed(1)}MB`,
        impact: 'Periodic performance degradation',
        recommendation: 'Monitor for memory leaks, optimize data structures',
      };
    }

    return null;
  }

  // Detect network bottlenecks
  private detectNetworkBottleneck(): Bottleneck | null {
    // Check for slow resources
    const slowResources = this.samples
      .filter(sample => sample.network > 1000) // > 1s
      .length;

    if (slowResources > this.samples.length * 0.1) { // > 10% of resources are slow
      return {
        type: 'network',
        severity: 'medium',
        description: `${slowResources} slow network requests detected`,
        impact: 'Increased page load times',
        recommendation: 'Optimize resource size, implement caching, use CDN',
      };
    }

    return null;
  }

  // Detect rendering bottlenecks
  private detectRenderingBottleneck(): Bottleneck | null {
    // Check frame rate
    const frameTimeSamples = this.samples
      .filter(sample => sample.frameTime !== undefined)
      .map(sample => sample.frameTime!) as number[];

    if (frameTimeSamples.length === 0) return null;

    const avgFrameTime = frameTimeSamples.reduce((sum, time) => sum + time, 0) / frameTimeSamples.length;
    const fps = 1000 / avgFrameTime;

    if (fps < 30) { // < 30fps
      return {
        type: 'rendering',
        severity: 'high',
        description: `Low frame rate: ${fps.toFixed(1)}fps`,
        impact: 'Poor user experience, janky animations',
        recommendation: 'Optimize rendering, reduce DOM manipulations, use CSS transforms',
      };
    } else if (fps < 45) { // < 45fps
      return {
        type: 'rendering',
        severity: 'medium',
        description: `Reduced frame rate: ${fps.toFixed(1)}fps`,
        impact: 'Slightly choppy animations',
        recommendation: 'Reduce animation complexity, optimize paint operations',
      };
    }

    return null;
  }

  // Detect JavaScript bottlenecks
  private detectJavaScriptBottleneck(): Bottleneck | null {
    // Check for long tasks
    const longTasks = this.samples
      .filter(sample => sample.longTasks)
      .flatMap(sample => sample.longTasks || []);

    if (longTasks.length === 0) return null;

    const avgLongTaskTime = longTasks.reduce((sum, task) => sum + task.duration, 0) / longTasks.length;
    const maxLongTaskTime = Math.max(...longTasks.map(task => task.duration));

    if (avgLongTaskTime > 100) { // > 100ms
      return {
        type: 'javascript',
        severity: 'high',
        description: `Long running tasks detected: avg ${avgLongTaskTime.toFixed(1)}ms`,
        impact: 'UI blocking, unresponsive interface',
        recommendation: 'Break up large tasks, use Web Workers for heavy computations',
      };
    } else if (maxLongTaskTime > 200) { // > 200ms
      return {
        type: 'javascript',
        severity: 'medium',
        description: `Very long tasks detected: max ${maxLongTaskTime.toFixed(1)}ms`,
        impact: 'Occasional UI freezing',
        recommendation: 'Implement code splitting, optimize algorithms',
      };
    }

    return null;
  }

  // Generate recommendations based on bottlenecks
  private generateRecommendations(bottlenecks: Bottleneck[]): string[] {
    const recommendations: string[] = [];

    bottlenecks.forEach(bottleneck => {
      recommendations.push(bottleneck.recommendation);
    });

    // Add general recommendations based on overall profile
    const avgMemory = this.samples.reduce((sum, sample) => sum + sample.memory, 0) / this.samples.length;
    const avgCPU = this.samples.reduce((sum, sample) => sum + sample.cpu, 0) / this.samples.length;

    if (avgMemory > 50) {
      recommendations.push('Consider implementing memory optimization techniques');
    }

    if (avgCPU > 70) {
      recommendations.push('Consider reducing computational complexity');
    }

    // Remove duplicates
    return [...new Set(recommendations)];
  }

  // Update configuration
  updateConfig(config: Partial<ProfilingConfig>): void {
    this.config = { ...this.config, ...config };
    
    // Restart profiling if it was running
    const wasProfiling = this.isProfiling;
    if (wasProfiling) {
      this.stopProfiling();
      if (this.config.enabled) {
        this.startProfiling();
      }
    }
  }

  // Get current configuration
  getConfig(): ProfilingConfig {
    return { ...this.config };
  }

  // Get profiling status
  getProfilingStatus(): {
    isProfiling: boolean;
    sampleCount: number;
    duration: number;
  } {
    return {
      isProfiling: this.isProfiling,
      sampleCount: this.samples.length,
      duration: this.isProfiling ? performance.now() - this.startTimestamp : 0,
    };
  }
}

export function usePerformanceProfiling(config?: Partial<ProfilingConfig>) {
  const [isProfiling, setIsProfiling] = useState(false);
  const [profile, setProfile] = useState<ProfileResult | null>(null);
  const [bottlenecks, setBottlenecks] = useState<Array<{
    type: 'cpu' | 'memory' | 'network' | 'rendering' | 'javascript';
    severity: 'low' | 'medium' | 'high' | 'critical';
    description: string;
    location?: string;
    impact: string;
    recommendation: string;
    score?: number;
  }>>([]);
  const [profilingStatus, setProfilingStatus] = useState<{
    isProfiling: boolean;
    samplesCollected: number;
    estimatedMemoryUsage: number;
  } | null>(null);
  const profilingManagerRef = useRef<ProfilingManager | null>(null);

  useEffect(() => {
    profilingManagerRef.current = new ProfilingManager(config);
    
    return () => {
      if (profilingManagerRef.current) {
        profilingManagerRef.current.stopProfiling();
      }
    };
  }, [config]);

  const startProfiling = useCallback(() => {
    if (profilingManagerRef.current) {
      profilingManagerRef.current.startProfiling();
      setIsProfiling(true);
      const status = profilingManagerRef.current.getProfilingStatus();
      setProfilingStatus({
        isProfiling: status.isProfiling,
        samplesCollected: status.sampleCount,
        estimatedMemoryUsage: 0, // Could be calculated from samples
      });
    }
  }, []);

  const stopProfiling = useCallback(() => {
    if (profilingManagerRef.current) {
      const result = profilingManagerRef.current.stopProfiling();
      setProfile(result);
      setIsProfiling(false);
      const status = profilingManagerRef.current.getProfilingStatus();
      setProfilingStatus({
        isProfiling: status.isProfiling,
        samplesCollected: status.sampleCount,
        estimatedMemoryUsage: 0,
      });
      
      if (result) {
        setBottlenecks(result.bottlenecks);
        
        // Store bottlenecks in performance store
        const store = usePerformanceOptimizationStore.getState();
        result.bottlenecks.forEach(bottleneck => {
          store.measureMetric({
            name: `bottleneck-${bottleneck.type}`,
            value: 100 - ((bottleneck as Bottleneck & { score?: number }).score || 0),
            unit: 'score',
            timestamp: new Date(),
            rating: bottleneck.severity === 'high' ? 'poor' :
                     bottleneck.severity === 'medium' ? 'needs-improvement' : 'good',
            threshold: { good: 80, poor: 50 },
            metadata: {
              type: bottleneck.type,
              description: bottleneck.description,
              recommendation: bottleneck.recommendation,
            },
          });
        });
      }
    }
  }, []);

  const updateConfig = useCallback((newConfig: Partial<ProfilingConfig>) => {
    if (profilingManagerRef.current) {
      profilingManagerRef.current.updateConfig(newConfig);
    }
  }, []);

  const clearProfile = useCallback(() => {
    setProfile(null);
    setBottlenecks([]);
    setProfilingStatus(null);
  }, []);

  return {
    isProfiling,
    profile,
    bottlenecks,
    profilingStatus,
    startProfiling,
    stopProfiling,
    updateConfig,
    clearProfile,
  };
}

// Hook for flame graph data
export function useFlameGraph() {
  const [flameGraphData, setFlameGraphData] = useState<{
    name: string;
    value: number;
    children?: Array<{
      name: string;
      value: number;
      children?: Array<{
        name: string;
        value: number;
      }>;
    }>;
  } | null>(null);
  const [isEnabled, setIsEnabled] = useState(false);

  const generateFlameGraph = useCallback(() => {
    // This would generate flame graph data from performance samples
    // For now, return mock data
    const mockData = {
      name: 'main',
      value: 100,
      children: [
        {
          name: 'component-a',
          value: 60,
          children: [
            { name: 'render', value: 40 },
            { name: 'update', value: 20 },
          ],
        },
        {
          name: 'component-b',
          value: 40,
          children: [
            { name: 'calculate', value: 30 },
            { name: 'draw', value: 10 },
          ],
        },
      ],
    };

    setFlameGraphData(mockData);
  }, []);

  return {
    flameGraphData,
    isEnabled,
    generateFlameGraph,
    setIsEnabled,
  };
}

// Export singleton instance
export const profilingManager = new ProfilingManager();

// Utility functions
export function startProfilingWithTimeout(timeoutMs: number = 10000): Promise<ProfileResult> {
  return new Promise((resolve, reject) => {
    profilingManager.startProfiling();
    
    const timeoutId = setTimeout(() => {
      const result = profilingManager.stopProfiling();
      if (result) {
        resolve(result);
      } else {
        reject(new Error('Profiling failed to produce results'));
      }
    }, timeoutMs);

    // Auto-stop if resolved early
    const checkInterval = setInterval(() => {
      const status = profilingManager.getProfilingStatus();
      if (!status.isProfiling) {
        clearTimeout(timeoutId);
        clearInterval(checkInterval);
        const result = profilingManager.stopProfiling();
        if (result) {
          resolve(result);
        }
      }
    }, 100);
  });
}

export function analyzePerformanceTrend(profiles: ProfileResult[]): {
  trend: 'improving' | 'stable' | 'degrading';
  insights: string[];
  recommendations: string[];
} {
  if (profiles.length < 2) {
    return {
      trend: 'stable',
      insights: ['Insufficient data for trend analysis'],
      recommendations: ['Collect more performance profiles'],
    };
  }

  // Calculate overall performance score trend
  const scores = profiles.map(profile => {
    const bottleneckScore = profile.bottlenecks.reduce((sum) => sum + 50, 0);
    return Math.max(0, 100 - bottleneckScore / Math.max(1, profile.bottlenecks.length));
  });

  // Simple trend analysis
  let trend: 'improving' | 'stable' | 'degrading' = 'stable';
  if (scores.length > 1) {
    const recent = scores.slice(-3);
    const older = scores.slice(0, -3);
    
    const recentAvg = recent.reduce((sum, score) => sum + score, 0) / recent.length;
    const olderAvg = older.reduce((sum, score) => sum + score, 0) / older.length;
    
    if (recentAvg > olderAvg + 5) {
      trend = 'degrading';
    } else if (recentAvg < olderAvg - 5) {
      trend = 'improving';
    }
  }

  // Generate insights
  const insights: string[] = [];
  
  if (trend === 'degrading') {
    insights.push('Performance is degrading over time');
  } else if (trend === 'improving') {
    insights.push('Performance is improving over time');
  } else {
    insights.push('Performance is stable over time');
  }

  // Generate recommendations
  const recommendations: string[] = [];
  
  if (trend === 'degrading') {
    recommendations.push('Investigate recent changes that may have impacted performance');
    recommendations.push('Consider rolling back problematic changes');
  } else if (trend === 'improving') {
    recommendations.push('Continue with current optimization strategies');
  } else {
    recommendations.push('Monitor for performance regressions');
  }

  return {
    trend,
    insights,
    recommendations,
  };
}

export function createPerformanceReport(profile: ProfileResult): {
  summary: string;
  details: string[];
  actionItems: string[];
} {
  const summary = `Performance Profile: ${profile.name}`;
  
  const details: string[] = [
    `Duration: ${profile.duration.toFixed(2)}ms`,
    `Samples collected: ${profile.samples.length}`,
    `Bottlenecks detected: ${profile.bottlenecks.length}`,
  ];

  const actionItems: string[] = profile.recommendations;

  return {
    summary,
    details,
    actionItems,
  };
}
