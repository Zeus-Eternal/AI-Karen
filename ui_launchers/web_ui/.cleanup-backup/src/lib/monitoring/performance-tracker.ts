/**
 * Performance Tracker
 * 
 * Comprehensive performance monitoring system for tracking application
 * performance metrics, resource usage, and optimization opportunities.
 */

export interface PerformanceMetrics {
  memory: {
    rss: number;
    heapTotal: number;
    heapUsed: number;
    external: number;
    arrayBuffers: number;
    heapUsagePercent: number;
  };
  cpu: {
    usage: number;
    user: number;
    system: number;
  };
  eventLoop: {
    delay: number;
    utilization: number;
  };
  gc: {
    collections: number;
    duration: number;
    reclaimedBytes: number;
  };
  network: {
    bytesReceived: number;
    bytesSent: number;
    connectionsActive: number;
    requestsPerSecond: number;
  };
  rendering: {
    frameRate: number;
    paintTime: number;
    layoutTime: number;
    scriptTime: number;
  };
  bundleSize: {
    javascript: number;
    css: number;
    images: number;
    total: number;
  };
}

export interface PerformanceAlert {
  type: 'memory' | 'cpu' | 'eventLoop' | 'gc' | 'network' | 'rendering';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  value: number;
  threshold: number;
  timestamp: number;
}

export class PerformanceTracker {
  private metrics: PerformanceMetrics;
  private alerts: PerformanceAlert[] = [];
  private performanceObserver: PerformanceObserver | null = null;
  private gcObserver: any = null;
  private intervalId: NodeJS.Timeout | null = null;
  
  // Performance thresholds
  private thresholds = {
    memory: {
      heapUsagePercent: { medium: 70, high: 85, critical: 95 },
      rss: { medium: 500 * 1024 * 1024, high: 1024 * 1024 * 1024, critical: 2 * 1024 * 1024 * 1024 }
    },
    cpu: {
      usage: { medium: 70, high: 85, critical: 95 }
    },
    eventLoop: {
      delay: { medium: 10, high: 50, critical: 100 },
      utilization: { medium: 0.7, high: 0.85, critical: 0.95 }
    },
    gc: {
      duration: { medium: 10, high: 50, critical: 100 },
      frequency: { medium: 10, high: 20, critical: 50 }
    },
    network: {
      requestsPerSecond: { medium: 100, high: 500, critical: 1000 }
    },
    rendering: {
      frameRate: { medium: 30, high: 20, critical: 10 },
      paintTime: { medium: 16, high: 33, critical: 50 }
    }
  };

  constructor() {
    this.metrics = this.initializeMetrics();
    this.startTracking();
  }

  private initializeMetrics(): PerformanceMetrics {
    return {
      memory: {
        rss: 0,
        heapTotal: 0,
        heapUsed: 0,
        external: 0,
        arrayBuffers: 0,
        heapUsagePercent: 0
      },
      cpu: {
        usage: 0,
        user: 0,
        system: 0
      },
      eventLoop: {
        delay: 0,
        utilization: 0
      },
      gc: {
        collections: 0,
        duration: 0,
        reclaimedBytes: 0
      },
      network: {
        bytesReceived: 0,
        bytesSent: 0,
        connectionsActive: 0,
        requestsPerSecond: 0
      },
      rendering: {
        frameRate: 0,
        paintTime: 0,
        layoutTime: 0,
        scriptTime: 0
      },
      bundleSize: {
        javascript: 0,
        css: 0,
        images: 0,
        total: 0
      }
    };
  }

  private startTracking() {
    // Start periodic metrics collection
    this.intervalId = setInterval(() => {
      this.collectMetrics();
    }, 5000); // Collect every 5 seconds

    // Set up performance observer for browser-specific metrics
    if (typeof window !== 'undefined' && 'PerformanceObserver' in window) {
      this.setupPerformanceObserver();
    }

    // Set up GC observer for Node.js
    if (typeof process !== 'undefined' && process.versions && process.versions.node) {
      this.setupGCObserver();
    }
  }

  private setupPerformanceObserver() {
    try {
      this.performanceObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        
        entries.forEach((entry) => {
          switch (entry.entryType) {
            case 'paint':
              if (entry.name === 'first-contentful-paint') {
                this.metrics.rendering.paintTime = entry.startTime;
              }
              break;
            
            case 'layout-shift':
              // Track cumulative layout shift
              break;
            
            case 'largest-contentful-paint':
              this.metrics.rendering.paintTime = entry.startTime;
              break;
            
            case 'navigation':
              const navEntry = entry as PerformanceNavigationTiming;
              this.metrics.network.bytesReceived += navEntry.transferSize || 0;
              break;
            
            case 'resource':
              const resourceEntry = entry as PerformanceResourceTiming;
              this.updateBundleSize(resourceEntry);
              break;
          }
        });
      });

      // Observe different types of performance entries
      this.performanceObserver.observe({ 
        entryTypes: ['paint', 'navigation', 'resource', 'largest-contentful-paint'] 
      });
    } catch (error) {
      console.warn('Failed to setup performance observer:', error);
    }
  }

  private setupGCObserver() {
    try {
      // In Node.js, we can use perf_hooks to monitor GC
      const { PerformanceObserver } = require('perf_hooks');
      
      this.gcObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        
        entries.forEach((entry) => {
          if (entry.entryType === 'gc') {
            this.metrics.gc.collections++;
            this.metrics.gc.duration += entry.duration;
            
            // Check for GC performance alerts
            this.checkGCPerformance(entry.duration);
          }
        });
      });

      this.gcObserver.observe({ entryTypes: ['gc'] });
    } catch (error) {
      console.warn('Failed to setup GC observer:', error);
    }
  }

  private updateBundleSize(entry: PerformanceResourceTiming) {
    const url = entry.name;
    const size = entry.transferSize || 0;

    if (url.endsWith('.js')) {
      this.metrics.bundleSize.javascript += size;
    } else if (url.endsWith('.css')) {
      this.metrics.bundleSize.css += size;
    } else if (url.match(/\.(png|jpg|jpeg|gif|svg|webp)$/)) {
      this.metrics.bundleSize.images += size;
    }

    this.metrics.bundleSize.total += size;
  }

  private collectMetrics() {
    this.collectMemoryMetrics();
    this.collectCPUMetrics();
    this.collectEventLoopMetrics();
    this.collectNetworkMetrics();
    this.collectRenderingMetrics();
    
    // Check for performance alerts
    this.checkPerformanceAlerts();
  }

  private collectMemoryMetrics() {
    if (typeof process !== 'undefined' && process.memoryUsage) {
      const memUsage = process.memoryUsage();
      
      this.metrics.memory = {
        rss: memUsage.rss,
        heapTotal: memUsage.heapTotal,
        heapUsed: memUsage.heapUsed,
        external: memUsage.external,
        arrayBuffers: memUsage.arrayBuffers,
        heapUsagePercent: (memUsage.heapUsed / memUsage.heapTotal) * 100
      };
    } else if (typeof window !== 'undefined' && 'performance' in window && 'memory' in (window.performance as any)) {
      const memInfo = (window.performance as any).memory;
      
      this.metrics.memory = {
        rss: memInfo.totalJSHeapSize,
        heapTotal: memInfo.totalJSHeapSize,
        heapUsed: memInfo.usedJSHeapSize,
        external: 0,
        arrayBuffers: 0,
        heapUsagePercent: (memInfo.usedJSHeapSize / memInfo.totalJSHeapSize) * 100
      };
    }
  }

  private collectCPUMetrics() {
    if (typeof process !== 'undefined' && process.cpuUsage) {
      const cpuUsage = process.cpuUsage();
      
      this.metrics.cpu = {
        usage: 0, // Would need additional calculation for percentage
        user: cpuUsage.user / 1000, // Convert to milliseconds
        system: cpuUsage.system / 1000
      };
    }
  }

  private collectEventLoopMetrics() {
    if (typeof process !== 'undefined') {
      // Measure event loop delay
      const start = process.hrtime.bigint();
      setImmediate(() => {
        const delay = Number(process.hrtime.bigint() - start) / 1000000; // Convert to milliseconds
        this.metrics.eventLoop.delay = delay;
        
        // Calculate event loop utilization (simplified)
        this.metrics.eventLoop.utilization = Math.min(delay / 16, 1); // Assuming 60fps target
      });
    }
  }

  private collectNetworkMetrics() {
    // Network metrics would typically come from external monitoring
    // For now, we'll track basic connection info
    if (typeof navigator !== 'undefined' && 'connection' in navigator) {
      const connection = (navigator as any).connection;
      
      if (connection) {
        // Update network metrics based on connection info
        this.metrics.network.connectionsActive = 1; // Simplified
      }
    }
  }

  private collectRenderingMetrics() {
    if (typeof window !== 'undefined') {
      // Measure frame rate
      let frameCount = 0;
      let lastTime = performance.now();
      
      const measureFrameRate = () => {
        frameCount++;
        const currentTime = performance.now();
        
        if (currentTime - lastTime >= 1000) {
          this.metrics.rendering.frameRate = frameCount;
          frameCount = 0;
          lastTime = currentTime;
        }
        
        requestAnimationFrame(measureFrameRate);
      };
      
      requestAnimationFrame(measureFrameRate);
    }
  }

  private checkPerformanceAlerts() {
    // Check memory alerts
    this.checkMemoryAlerts();
    
    // Check CPU alerts
    this.checkCPUAlerts();
    
    // Check event loop alerts
    this.checkEventLoopAlerts();
    
    // Check rendering alerts
    this.checkRenderingAlerts();
    
    // Clean up old alerts (keep last 100)
    if (this.alerts.length > 100) {
      this.alerts = this.alerts.slice(-100);
    }
  }

  private checkMemoryAlerts() {
    const { heapUsagePercent, rss } = this.metrics.memory;
    const thresholds = this.thresholds.memory;
    
    // Check heap usage percentage
    if (heapUsagePercent >= thresholds.heapUsagePercent.critical) {
      this.addAlert('memory', 'critical', `Critical heap usage: ${heapUsagePercent.toFixed(1)}%`, heapUsagePercent, thresholds.heapUsagePercent.critical);
    } else if (heapUsagePercent >= thresholds.heapUsagePercent.high) {
      this.addAlert('memory', 'high', `High heap usage: ${heapUsagePercent.toFixed(1)}%`, heapUsagePercent, thresholds.heapUsagePercent.high);
    } else if (heapUsagePercent >= thresholds.heapUsagePercent.medium) {
      this.addAlert('memory', 'medium', `Elevated heap usage: ${heapUsagePercent.toFixed(1)}%`, heapUsagePercent, thresholds.heapUsagePercent.medium);
    }
    
    // Check RSS usage
    if (rss >= thresholds.rss.critical) {
      this.addAlert('memory', 'critical', `Critical RSS usage: ${(rss / 1024 / 1024).toFixed(1)}MB`, rss, thresholds.rss.critical);
    } else if (rss >= thresholds.rss.high) {
      this.addAlert('memory', 'high', `High RSS usage: ${(rss / 1024 / 1024).toFixed(1)}MB`, rss, thresholds.rss.high);
    }
  }

  private checkCPUAlerts() {
    const { usage } = this.metrics.cpu;
    const thresholds = this.thresholds.cpu;
    
    if (usage >= thresholds.usage.critical) {
      this.addAlert('cpu', 'critical', `Critical CPU usage: ${usage.toFixed(1)}%`, usage, thresholds.usage.critical);
    } else if (usage >= thresholds.usage.high) {
      this.addAlert('cpu', 'high', `High CPU usage: ${usage.toFixed(1)}%`, usage, thresholds.usage.high);
    } else if (usage >= thresholds.usage.medium) {
      this.addAlert('cpu', 'medium', `Elevated CPU usage: ${usage.toFixed(1)}%`, usage, thresholds.usage.medium);
    }
  }

  private checkEventLoopAlerts() {
    const { delay, utilization } = this.metrics.eventLoop;
    const thresholds = this.thresholds.eventLoop;
    
    // Check event loop delay
    if (delay >= thresholds.delay.critical) {
      this.addAlert('eventLoop', 'critical', `Critical event loop delay: ${delay.toFixed(1)}ms`, delay, thresholds.delay.critical);
    } else if (delay >= thresholds.delay.high) {
      this.addAlert('eventLoop', 'high', `High event loop delay: ${delay.toFixed(1)}ms`, delay, thresholds.delay.high);
    } else if (delay >= thresholds.delay.medium) {
      this.addAlert('eventLoop', 'medium', `Elevated event loop delay: ${delay.toFixed(1)}ms`, delay, thresholds.delay.medium);
    }
    
    // Check event loop utilization
    if (utilization >= thresholds.utilization.critical) {
      this.addAlert('eventLoop', 'critical', `Critical event loop utilization: ${(utilization * 100).toFixed(1)}%`, utilization, thresholds.utilization.critical);
    }
  }

  private checkRenderingAlerts() {
    const { frameRate, paintTime } = this.metrics.rendering;
    const thresholds = this.thresholds.rendering;
    
    // Check frame rate (lower is worse)
    if (frameRate <= thresholds.frameRate.critical && frameRate > 0) {
      this.addAlert('rendering', 'critical', `Critical frame rate: ${frameRate}fps`, frameRate, thresholds.frameRate.critical);
    } else if (frameRate <= thresholds.frameRate.high && frameRate > 0) {
      this.addAlert('rendering', 'high', `Low frame rate: ${frameRate}fps`, frameRate, thresholds.frameRate.high);
    }
    
    // Check paint time
    if (paintTime >= thresholds.paintTime.critical) {
      this.addAlert('rendering', 'critical', `Critical paint time: ${paintTime.toFixed(1)}ms`, paintTime, thresholds.paintTime.critical);
    } else if (paintTime >= thresholds.paintTime.high) {
      this.addAlert('rendering', 'high', `High paint time: ${paintTime.toFixed(1)}ms`, paintTime, thresholds.paintTime.high);
    }
  }

  private checkGCPerformance(duration: number) {
    const thresholds = this.thresholds.gc;
    
    if (duration >= thresholds.duration.critical) {
      this.addAlert('gc', 'critical', `Critical GC duration: ${duration.toFixed(1)}ms`, duration, thresholds.duration.critical);
    } else if (duration >= thresholds.duration.high) {
      this.addAlert('gc', 'high', `High GC duration: ${duration.toFixed(1)}ms`, duration, thresholds.duration.high);
    } else if (duration >= thresholds.duration.medium) {
      this.addAlert('gc', 'medium', `Elevated GC duration: ${duration.toFixed(1)}ms`, duration, thresholds.duration.medium);
    }
  }

  private addAlert(type: PerformanceAlert['type'], severity: PerformanceAlert['severity'], message: string, value: number, threshold: number) {
    const alert: PerformanceAlert = {
      type,
      severity,
      message,
      value,
      threshold,
      timestamp: Date.now()
    };
    
    this.alerts.push(alert);
    
    // Log critical alerts
    if (severity === 'critical') {
      console.error('Performance Alert:', alert);
    } else if (severity === 'high') {
      console.warn('Performance Alert:', alert);
    }
  }

  // Public methods
  public async getPerformanceMetrics(): Promise<PerformanceMetrics> {
    return { ...this.metrics };
  }

  public getPerformanceAlerts(): PerformanceAlert[] {
    return [...this.alerts];
  }

  public getRecentAlerts(minutes: number = 5): PerformanceAlert[] {
    const cutoff = Date.now() - (minutes * 60 * 1000);
    return this.alerts.filter(alert => alert.timestamp >= cutoff);
  }

  public getCriticalAlerts(): PerformanceAlert[] {
    return this.alerts.filter(alert => alert.severity === 'critical');
  }

  public clearAlerts() {
    this.alerts = [];
  }

  public updateThresholds(newThresholds: Partial<typeof this.thresholds>) {
    this.thresholds = { ...this.thresholds, ...newThresholds };
  }

  public getPerformanceSummary() {
    const recentAlerts = this.getRecentAlerts(5);
    const criticalAlerts = this.getCriticalAlerts();
    
    return {
      memory: {
        heapUsagePercent: this.metrics.memory.heapUsagePercent,
        rssUsageMB: this.metrics.memory.rss / 1024 / 1024
      },
      cpu: {
        usage: this.metrics.cpu.usage
      },
      eventLoop: {
        delay: this.metrics.eventLoop.delay,
        utilization: this.metrics.eventLoop.utilization
      },
      rendering: {
        frameRate: this.metrics.rendering.frameRate,
        paintTime: this.metrics.rendering.paintTime
      },
      alerts: {
        total: this.alerts.length,
        recent: recentAlerts.length,
        critical: criticalAlerts.length
      },
      bundleSize: {
        totalMB: this.metrics.bundleSize.total / 1024 / 1024,
        javascriptMB: this.metrics.bundleSize.javascript / 1024 / 1024,
        cssMB: this.metrics.bundleSize.css / 1024 / 1024,
        imagesMB: this.metrics.bundleSize.images / 1024 / 1024
      }
    };
  }

  public destroy() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
    
    if (this.performanceObserver) {
      this.performanceObserver.disconnect();
      this.performanceObserver = null;
    }
    
    if (this.gcObserver) {
      this.gcObserver.disconnect();
      this.gcObserver = null;
    }
  }
}

export default PerformanceTracker;