/**
 * Performance Tracker (Prod-Ready, Node + Browser)
 *
 * Features:
 *  - Memory, CPU%, Event Loop (delay & utilization), GC (Node), Network (hooks), Rendering/Bundle (Browser)
 *  - Safe in SSR/Node/browser with guards
 *  - Sliding RPS calc + hooks for requests and bytes
 *  - Alerting with severity thresholds + optional onAlert callback
 *  - Clean destroy() and zero-leak rAF loop
 *  - Prometheus-ready summaries via getPerformanceSummary()
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
    usage: number;  // percentage 0..100
    user: number;   // ms
    system: number; // ms
  };
  eventLoop: {
    delay: number;        // ms (p50-ish recent tick)
    utilization: number;  // 0..1
  };
  gc: {
    collections: number;
    duration: number;       // total ms
    reclaimedBytes: number; // best-effort (Node reports vary; we keep 0 if not available)
  };
  network: {
    bytesReceived: number;
    bytesSent: number;
    connectionsActive: number;
    requestsPerSecond: number;
  };
  rendering: {
    frameRate: number;
    paintTime: number;   // LCP/FCP if available
    layoutTime: number;  // placeholder (timing APIs differ; kept for schema continuity)
    scriptTime: number;  // placeholder
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

export type AlertCallback = (alert: PerformanceAlert) => void;

const isNode = typeof process !== 'undefined' && !!(process as unknown as { versions?: { node?: string } }).versions?.node;
const isBrowser = typeof window !== 'undefined' && typeof document !== 'undefined';

/** Safe dynamic imports/refs guarded for Node environments */
let perfHooks: typeof import('perf_hooks') | null = null;
let osMod: typeof import('os') | null = null;
if (isNode) {
  try {
    perfHooks = eval('require')('perf_hooks');
    osMod = eval('require')('os');
  } catch {
    // ignore
  }
}

export class PerformanceTracker {
  private metrics: PerformanceMetrics;
  private alerts: PerformanceAlert[] = [];
  private onAlert?: AlertCallback;

  // Observers
  private browserPerfObserver: PerformanceObserver | null = null;
  private nodeGCObserver: PerformanceObserver | null = null;

  // Event loop tools (Node)
  private elu: { idle: number; active: number; utilization: number } | null = null; // eventLoopUtilization handle
  private eld: { mean: number; reset: () => void; enable: () => void; disable: () => void } | null = null; // monitorEventLoopDelay histogram

  // Intervals / loops
  private intervalId: ReturnType<typeof setInterval> | null = null;
  private rafActive = false;
  private rAFId = 0;

  // CPU calc baseline (Node)
  private lastCpuUsage: { user: number; system: number } | null = null; // microseconds
  private lastHrTimeNs: bigint | null = null;

  // Network sliding window counters
  private requestsInWindow = 0;
  private lastNetworkWindowTs = Date.now();
  private networkWindowMs = 1000;

  // Bundle resource de-dup
  private seenResources = new Set<string>();

  // Performance thresholds (tuned defaults)
  private thresholds = {
    memory: {
      heapUsagePercent: { medium: 70, high: 85, critical: 95 },
      rss: {
        medium: 500 * 1024 * 1024,
        high: 1024 * 1024 * 1024,
        critical: 2 * 1024 * 1024 * 1024,
      },
    },
    cpu: {
      usage: { medium: 70, high: 85, critical: 95 },
    },
    eventLoop: {
      delay: { medium: 10, high: 50, critical: 100 },       // ms p50-ish
      utilization: { medium: 0.7, high: 0.85, critical: 0.95 },
    },
    gc: {
      duration: { medium: 10, high: 50, critical: 100 },    // single GC event duration ms
      frequency: { medium: 10, high: 20, critical: 50 },    // events per 5 min (used in summary)
    },
    network: {
      requestsPerSecond: { medium: 100, high: 500, critical: 1000 },
    },
    rendering: {
      frameRate: { medium: 30, high: 20, critical: 10 }, // lower is worse
      paintTime: { medium: 2000, high: 4000, critical: 6000 }, // ms (LCP/FCP budgets)
    },
  };

  constructor(opts?: { onAlert?: AlertCallback; thresholds?: Partial<PerformanceTracker['thresholds']>; intervalMs?: number }) {
    if (opts?.thresholds) {
      this.thresholds = { ...this.thresholds, ...opts.thresholds };
    }
    if (opts?.onAlert) {
      this.onAlert = opts.onAlert;
    }

    this.metrics = this.initializeMetrics();

    // Initialize Node monitors
    if (isNode && perfHooks) {
      try {
        const { monitorEventLoopDelay } = perfHooks;
        if (typeof monitorEventLoopDelay === 'function') {
          this.eld = monitorEventLoopDelay({ resolution: 10 }) as { mean: number; reset: () => void; enable: () => void; disable: () => void };
          this.eld?.enable();
        }
        // eventLoopUtilization is available in newer Node versions
        if ('eventLoopUtilization' in perfHooks && typeof perfHooks.eventLoopUtilization === 'function') {
          this.elu = perfHooks.eventLoopUtilization();
        }
        this.setupNodeGCObserver();
      } catch {
        // ignore
      }
    }

    // Initialize browser observers
    if (isBrowser && 'PerformanceObserver' in window) {
      this.setupBrowserPerformanceObserver();
      this.startFrameRateLoop();
    }

    // Start periodic collection
    const intervalMs = opts?.intervalMs && opts.intervalMs >= 1000 ? opts.intervalMs : 5000;
    this.intervalId = setInterval(() => this.collectMetrics(), intervalMs);
  }

  // ---------- Initialization ----------
  private initializeMetrics(): PerformanceMetrics {
    return {
      memory: {
        rss: 0,
        heapTotal: 0,
        heapUsed: 0,
        external: 0,
        arrayBuffers: 0,
        heapUsagePercent: 0,
      },
      cpu: {
        usage: 0,
        user: 0,
        system: 0,
      },
      eventLoop: {
        delay: 0,
        utilization: 0,
      },
      gc: {
        collections: 0,
        duration: 0,
        reclaimedBytes: 0,
      },
      network: {
        bytesReceived: 0,
        bytesSent: 0,
        connectionsActive: 0,
        requestsPerSecond: 0,
      },
      rendering: {
        frameRate: 0,
        paintTime: 0,
        layoutTime: 0,
        scriptTime: 0,
      },
      bundleSize: {
        javascript: 0,
        css: 0,
        images: 0,
        total: 0,
      },
    };
  }

  // ---------- Browser performance observer ----------
  private setupBrowserPerformanceObserver() {
    try {
      this.browserPerfObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          switch (entry.entryType) {
            case 'paint': {
              if ((entry as PerformancePaintTiming).name === 'first-contentful-paint') {
                this.metrics.rendering.paintTime = entry.startTime;
              }
              break;
            }
            case 'largest-contentful-paint': {
              const lcpEntry = entry as PerformanceEntry & { startTime?: number };
              const lcpTime = typeof lcpEntry.startTime === 'number' ? lcpEntry.startTime : 0;
              this.metrics.rendering.paintTime = lcpTime;
              break;
            }
            case 'navigation': {
              const nav = entry as PerformanceNavigationTiming;
              this.metrics.network.bytesReceived += nav.transferSize || 0;
              break;
            }
            case 'resource': {
              const res = entry as PerformanceResourceTiming;
              this.updateBundleSize(res);
              break;
            }
            default:
              break;
          }
        }
      });

      this.browserPerfObserver.observe({
        entryTypes: ['paint', 'navigation', 'resource', 'largest-contentful-paint'],
      });
    } catch {
      // ignore
    }
  }

  private startFrameRateLoop() {
    if (!isBrowser || this.rafActive) return;
    this.rafActive = true;

    let frameCount = 0;
    let lastTime = performance.now();

    const tick = () => {
      if (!this.rafActive) return;
      frameCount++;
      const now = performance.now();
      if (now - lastTime >= 1000) {
        this.metrics.rendering.frameRate = frameCount;
        frameCount = 0;
        lastTime = now;
      }
      this.rAFId = window.requestAnimationFrame(tick);
    };

    this.rAFId = window.requestAnimationFrame(tick);
  }

  private stopFrameRateLoop() {
    if (!this.rafActive) return;
    this.rafActive = false;
    if (this.rAFId) {
      try {
        window.cancelAnimationFrame(this.rAFId);
      } catch {
        // ignore
      }
    }
  }

  private updateBundleSize(entry: PerformanceResourceTiming) {
    const url = entry.name;
    if (this.seenResources.has(url)) return; // avoid double counting
    this.seenResources.add(url);

    const size = entry.transferSize || 0;
    if (url.endsWith('.js')) {
      this.metrics.bundleSize.javascript += size;
    } else if (url.endsWith('.css')) {
      this.metrics.bundleSize.css += size;
    } else if (/\.(png|jpg|jpeg|gif|svg|webp|avif)$/i.test(url)) {
      this.metrics.bundleSize.images += size;
    }
    this.metrics.bundleSize.total += size;
  }

  // ---------- Node GC Observer ----------
  private setupNodeGCObserver() {
    if (!isNode || !perfHooks) return;
    try {
      const { PerformanceObserver } = perfHooks;
      this.nodeGCObserver = new PerformanceObserver((list) => {
        for (const e of list.getEntries()) {
          if (e.entryType === 'gc') {
            this.metrics.gc.collections++;
            this.metrics.gc.duration += e.duration || 0;
            // reclaimedBytes are not reliably reported; keep at 0 unless available
            const gcEntry = e as PerformanceEntry & { detail?: { reclaimed?: number } };
            if (typeof gcEntry.detail?.reclaimed === 'number') {
              this.metrics.gc.reclaimedBytes += gcEntry.detail.reclaimed;
            }
            this.checkGCPerformance(e.duration || 0);
          }
        }
      }) as PerformanceObserver;
      if (this.nodeGCObserver) {
        this.nodeGCObserver.observe({ entryTypes: ['gc'] });
      }
    } catch {
      // ignore
    }
  }

  // ---------- Periodic collection ----------
  private collectMetrics() {
    this.collectMemoryMetrics();
    this.collectCPUMetrics();
    this.collectEventLoopMetrics();
    this.collectNetworkMetrics(); // computes RPS window
    // Rendering metrics are live-updated via observers/rAF

    this.checkPerformanceAlerts();
  }

  private collectMemoryMetrics() {
    if (isNode && typeof process.memoryUsage === 'function') {
      const m = process.memoryUsage();
      const heapUsagePercent = m.heapTotal > 0 ? (m.heapUsed / m.heapTotal) * 100 : 0;
      this.metrics.memory = {
        rss: m.rss,
        heapTotal: m.heapTotal,
        heapUsed: m.heapUsed,
        external: (m as NodeJS.MemoryUsage & { external?: number }).external ?? 0,
        arrayBuffers: (m as NodeJS.MemoryUsage & { arrayBuffers?: number }).arrayBuffers ?? 0,
        heapUsagePercent,
      };
    } else if (isBrowser && (performance as Performance & { memory?: { totalJSHeapSize?: number; usedJSHeapSize?: number } }).memory) {
      const mem = (performance as Performance & { memory: { totalJSHeapSize?: number; usedJSHeapSize?: number } }).memory;
      const total = mem.totalJSHeapSize || 0;
      const used = mem.usedJSHeapSize || 0;
      this.metrics.memory = {
        rss: total,
        heapTotal: total,
        heapUsed: used,
        external: 0,
        arrayBuffers: 0,
        heapUsagePercent: total > 0 ? (used / total) * 100 : 0,
      };
    }
  }

  private collectCPUMetrics() {
    if (isNode && typeof process.cpuUsage === 'function') {
      const usage = process.cpuUsage(); // microseconds since process start OR since last call (platform dependent)
      const nowNs = process.hrtime.bigint();

      if (this.lastCpuUsage && this.lastHrTimeNs) {
        const userDeltaUs = Math.max(0, usage.user - this.lastCpuUsage.user);
        const sysDeltaUs = Math.max(0, usage.system - this.lastCpuUsage.system);
        const cpuDeltaUs = userDeltaUs + sysDeltaUs;

        const elapsedNs = Number(nowNs - this.lastHrTimeNs);
        const elapsedUs = elapsedNs / 1000;

        const cores = Math.max(1, (osMod?.cpus?.() || []).length || 1);
        // CPU% = (process CPU time / (elapsed wall time * cores)) * 100
        const percent = elapsedUs > 0 ? Math.min(100, (cpuDeltaUs / (elapsedUs * cores)) * 100) : 0;

        this.metrics.cpu = {
          usage: percent,
          user: userDeltaUs / 1000,   // ms
          system: sysDeltaUs / 1000,  // ms
        };
      }

      this.lastCpuUsage = { user: usage.user, system: usage.system };
      this.lastHrTimeNs = nowNs;
    } else {
      // Browser: we could derive CPU heuristics via Performance APIs, but keep 0 for now.
      // (Headless-first; real CPU% best captured server-side.)
    }
  }

  private collectEventLoopMetrics() {
    // Utilization
    if (isNode && perfHooks && 'eventLoopUtilization' in perfHooks && this.elu) {
      try {
        const eventLoopUtilization = perfHooks.eventLoopUtilization as (elu?: { idle: number; active: number; utilization: number }) => { idle: number; active: number; utilization: number };
        const current = eventLoopUtilization(this.elu);
        this.metrics.eventLoop.utilization = Math.max(0, Math.min(1, current.utilization ?? 0));
      } catch {
        // ignore
      }
    } else {
      // Browser: simple heuristic—keep last calc or 0
      this.metrics.eventLoop.utilization = Math.min(1, this.metrics.eventLoop.delay / 16);
    }

    // Delay
    if (isNode && this.eld) {
      try {
        // monitorEventLoopDelay returns nanoseconds histogram
        const meanNs = Number(this.eld.mean);
        // Mean is influenced by idle time; p50 or max are also available. We use mean as a stable indicator.
        this.metrics.eventLoop.delay = meanNs / 1e6; // ms
        // Reset histogram window to keep it "recent"
        this.eld.reset();
      } catch {
        // ignore
      }
    } else if (isBrowser) {
      // Lightweight one-shot delay sample: schedule a macrotask and measure drift vs expected 0
      const start = performance.now();
      setTimeout(() => {
        const delay = performance.now() - start; // ms
        this.metrics.eventLoop.delay = delay;
      }, 0);
    }
  }

  private collectNetworkMetrics() {
    // RPS window computation (based on increments coming from tickRequest())
    const now = Date.now();
    const dt = now - this.lastNetworkWindowTs;
    if (dt >= this.networkWindowMs) {
      const rps = this.requestsInWindow / (dt / 1000);
      this.metrics.network.requestsPerSecond = rps;
      this.requestsInWindow = 0;
      this.lastNetworkWindowTs = now;
    }
    // connectionsActive and bytes are updated via hooks
  }

  // ---------- Alerting ----------
  private checkPerformanceAlerts() {
    this.checkMemoryAlerts();
    this.checkCPUAlerts();
    this.checkEventLoopAlerts();
    this.checkRenderingAlerts();

    // Trim alert buffer
    if (this.alerts.length > 100) {
      this.alerts = this.alerts.slice(-100);
    }
  }

  private addAlert(
    type: PerformanceAlert['type'],
    severity: PerformanceAlert['severity'],
    message: string,
    value: number,
    threshold: number,
  ) {
    const alert: PerformanceAlert = {
      type,
      severity,
      message,
      value,
      threshold,
      timestamp: Date.now(),
    };
    this.alerts.push(alert);

    if (this.onAlert) {
      try {
        this.onAlert(alert);
      } catch {
        // ignore callback errors
      }
    }
    // Optional: route by severity
    if (severity === 'critical') {
      // console.error(message);
    } else if (severity === 'high') {
      // console.warn(message);
    }
  }

  private checkMemoryAlerts() {
    const { heapUsagePercent, rss } = this.metrics.memory;
    const t = this.thresholds.memory;

    if (heapUsagePercent >= t.heapUsagePercent.critical) {
      this.addAlert('memory', 'critical', `Critical heap usage: ${heapUsagePercent.toFixed(1)}%`, heapUsagePercent, t.heapUsagePercent.critical);
    } else if (heapUsagePercent >= t.heapUsagePercent.high) {
      this.addAlert('memory', 'high', `High heap usage: ${heapUsagePercent.toFixed(1)}%`, heapUsagePercent, t.heapUsagePercent.high);
    } else if (heapUsagePercent >= t.heapUsagePercent.medium) {
      this.addAlert('memory', 'medium', `Elevated heap usage: ${heapUsagePercent.toFixed(1)}%`, heapUsagePercent, t.heapUsagePercent.medium);
    }

    if (rss >= t.rss.critical) {
      this.addAlert('memory', 'critical', `Critical RSS: ${(rss / 1024 / 1024).toFixed(1)} MB`, rss, t.rss.critical);
    } else if (rss >= t.rss.high) {
      this.addAlert('memory', 'high', `High RSS: ${(rss / 1024 / 1024).toFixed(1)} MB`, rss, t.rss.high);
    } else if (rss >= t.rss.medium) {
      this.addAlert('memory', 'medium', `Elevated RSS: ${(rss / 1024 / 1024).toFixed(1)} MB`, rss, t.rss.medium);
    }
  }

  private checkCPUAlerts() {
    const { usage } = this.metrics.cpu;
    const t = this.thresholds.cpu;
    if (usage >= t.usage.critical) {
      this.addAlert('cpu', 'critical', `Critical CPU: ${usage.toFixed(1)}%`, usage, t.usage.critical);
    } else if (usage >= t.usage.high) {
      this.addAlert('cpu', 'high', `High CPU: ${usage.toFixed(1)}%`, usage, t.usage.high);
    } else if (usage >= t.usage.medium) {
      this.addAlert('cpu', 'medium', `Elevated CPU: ${usage.toFixed(1)}%`, usage, t.usage.medium);
    }
  }

  private checkEventLoopAlerts() {
    const { delay, utilization } = this.metrics.eventLoop;
    const t = this.thresholds.eventLoop;

    if (delay >= t.delay.critical) {
      this.addAlert('eventLoop', 'critical', `Critical event loop delay: ${delay.toFixed(1)} ms`, delay, t.delay.critical);
    } else if (delay >= t.delay.high) {
      this.addAlert('eventLoop', 'high', `High event loop delay: ${delay.toFixed(1)} ms`, delay, t.delay.high);
    } else if (delay >= t.delay.medium) {
      this.addAlert('eventLoop', 'medium', `Elevated event loop delay: ${delay.toFixed(1)} ms`, delay, t.delay.medium);
    }

    if (utilization >= t.utilization.critical) {
      this.addAlert('eventLoop', 'critical', `Critical event loop utilization: ${(utilization * 100).toFixed(1)}%`, utilization, t.utilization.critical);
    } else if (utilization >= t.utilization.high) {
      this.addAlert('eventLoop', 'high', `High event loop utilization: ${(utilization * 100).toFixed(1)}%`, utilization, t.utilization.high);
    } else if (utilization >= t.utilization.medium) {
      this.addAlert('eventLoop', 'medium', `Elevated event loop utilization: ${(utilization * 100).toFixed(1)}%`, utilization, t.utilization.medium);
    }
  }

  private checkRenderingAlerts() {
    const { frameRate, paintTime } = this.metrics.rendering;
    const t = this.thresholds.rendering;

    // Frame rate (lower is worse)
    if (frameRate > 0) {
      if (frameRate <= t.frameRate.critical) {
        this.addAlert('rendering', 'critical', `Critical frame rate: ${frameRate} fps`, frameRate, t.frameRate.critical);
      } else if (frameRate <= t.frameRate.high) {
        this.addAlert('rendering', 'high', `Low frame rate: ${frameRate} fps`, frameRate, t.frameRate.high);
      } else if (frameRate <= t.frameRate.medium) {
        this.addAlert('rendering', 'medium', `Below target frame rate: ${frameRate} fps`, frameRate, t.frameRate.medium);
      }
    }

    // Paint time (LCP/FCP)
    if (paintTime >= t.paintTime.critical) {
      this.addAlert('rendering', 'critical', `Critical paint time: ${paintTime.toFixed(0)} ms`, paintTime, t.paintTime.critical);
    } else if (paintTime >= t.paintTime.high) {
      this.addAlert('rendering', 'high', `High paint time: ${paintTime.toFixed(0)} ms`, paintTime, t.paintTime.high);
    } else if (paintTime >= t.paintTime.medium) {
      this.addAlert('rendering', 'medium', `Elevated paint time: ${paintTime.toFixed(0)} ms`, paintTime, t.paintTime.medium);
    }
  }

  private checkGCPerformance(duration: number) {
    const t = this.thresholds.gc;
    if (duration >= t.duration.critical) {
      this.addAlert('gc', 'critical', `Critical GC duration: ${duration.toFixed(1)} ms`, duration, t.duration.critical);
    } else if (duration >= t.duration.high) {
      this.addAlert('gc', 'high', `High GC duration: ${duration.toFixed(1)} ms`, duration, t.duration.high);
    } else if (duration >= t.duration.medium) {
      this.addAlert('gc', 'medium', `Elevated GC duration: ${duration.toFixed(1)} ms`, duration, t.duration.medium);
    }
  }

  // ---------- Public hooks ----------
  /** Call this per request to track RPS. */
  public tickRequest(count = 1) {
    if (count > 0) this.requestsInWindow += count;
  }

  /** Update active connections (useful for websockets/pooling). */
  public setActiveConnections(n: number) {
    this.metrics.network.connectionsActive = Math.max(0, Math.floor(n));
  }

  /** Add to bytes accounting for received/sent. */
  public recordNetwork(bytesIn = 0, bytesOut = 0) {
    if (bytesIn > 0) this.metrics.network.bytesReceived += bytesIn;
    if (bytesOut > 0) this.metrics.network.bytesSent += bytesOut;
  }

  /** Accessors */
  public async getPerformanceMetrics(): Promise<PerformanceMetrics> {
    return { ...this.metrics };
  }

  public getPerformanceAlerts(): PerformanceAlert[] {
    return [...this.alerts];
  }

  public getRecentAlerts(minutes = 5): PerformanceAlert[] {
    const cutoff = Date.now() - minutes * 60 * 1000;
    return this.alerts.filter((a) => a.timestamp >= cutoff);
  }

  public getCriticalAlerts(): PerformanceAlert[] {
    return this.alerts.filter((a) => a.severity === 'critical');
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
        rssUsageMB: this.metrics.memory.rss / 1024 / 1024,
      },
      cpu: {
        usage: this.metrics.cpu.usage,
      },
      eventLoop: {
        delay: this.metrics.eventLoop.delay,
        utilization: this.metrics.eventLoop.utilization,
      },
      rendering: {
        frameRate: this.metrics.rendering.frameRate,
        paintTime: this.metrics.rendering.paintTime,
      },
      alerts: {
        total: this.alerts.length,
        recent: recentAlerts.length,
        critical: criticalAlerts.length,
      },
      bundleSize: {
        totalMB: this.metrics.bundleSize.total / (1024 * 1024),
        javascriptMB: this.metrics.bundleSize.javascript / (1024 * 1024),
        cssMB: this.metrics.bundleSize.css / (1024 * 1024),
        imagesMB: this.metrics.bundleSize.images / (1024 * 1024),
      },
      network: {
        rps: this.metrics.network.requestsPerSecond,
        bytesInMB: this.metrics.network.bytesReceived / (1024 * 1024),
        bytesOutMB: this.metrics.network.bytesSent / (1024 * 1024),
        connectionsActive: this.metrics.network.connectionsActive,
      },
    };
  }

  /** Clean up all observers and timers. */
  public destroy() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
    if (this.browserPerfObserver) {
      try {
        this.browserPerfObserver.disconnect();
      } catch (err) {
        console.warn('[PERF_TRACKER] Failed to disconnect browser performance observer:', err);
      }
      this.browserPerfObserver = null;
    }
    if (this.nodeGCObserver) {
      try {
        this.nodeGCObserver.disconnect();
      } catch (err) {
        console.warn('[PERF_TRACKER] Failed to disconnect Node GC observer:', err);
      }
      this.nodeGCObserver = null;
    }
    if (this.eld) {
      try {
        this.eld.disable?.();
      } catch (err) {
        console.warn('[PERF_TRACKER] Failed to disable event loop delay monitor:', err);
      }
      this.eld = null;
    }
    this.stopFrameRateLoop();
  }
}

export default PerformanceTracker;
