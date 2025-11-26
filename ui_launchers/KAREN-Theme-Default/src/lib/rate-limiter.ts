/**
 * Rate Limiter Utility (production-grade)
 *
 * - Sliding-window requests cap (maxRequests / windowMs)
 * - Optional concurrency cap
 * - Exponential backoff with jitter for 429/5xx
 * - Honors Retry-After header (seconds or HTTP-date)
 * - FIFO queue with optional high-priority enqueue
 * - Per-request timeout + AbortSignal support
 * - Pause/Resume, stats, and safe shutdown
 * - Helper: wrapFetch() for API calls
 */

export type Millis = number;

interface RetryAfterError extends Error {
  __retryAfterMs?: number | null;
}

export interface RateLimitConfig {
  /** Max requests allowed within the window */
  maxRequests: number;
  /** Window length in milliseconds */
  windowMs: Millis;

  /** Default backoff if 429 and no Retry-After present */
  retryAfterMs?: Millis;

  /** Optional max concurrent in-flight requests */
  maxConcurrent?: number;

  /** Minimum spacing between requests (ms). Defaults to 0 */
  minIntervalMs?: Millis;

  /** Exponential backoff base (ms) */
  backoffBaseMs?: Millis;

  /** Exponential backoff ceiling (ms) */
  backoffMaxMs?: Millis;

  /** Add ±jitter% to backoff (0..1). Example: 0.2 = ±20% */
  jitter?: number;

  /** Respect server Retry-After header if present */
  respectRetryAfterHeader?: boolean;

  /** Max queued requests; older are dropped if exceeded (0 = unlimited) */
  maxQueueSize?: number;
}

export interface ExecuteOptions {
  /** High priority goes to the front of the queue */
  priority?: 'high' | 'normal';
  /** Optional AbortSignal to cancel before execution */
  signal?: AbortSignal;
  /** Per-request timeout (ms) */
  timeoutMs?: Millis;
  /** Name for diagnostics */
  label?: string;
}

export interface QueuedRequest<T = unknown> {
  resolve: (value: T) => void;
  reject: (error: Error) => void;
  request: () => Promise<T>;
  createdAt: number;
  attempt: number;
  options: ExecuteOptions;
}

export class RateLimiter {
  private readonly config: Required<
    Omit<
      RateLimitConfig,
      'retryAfterMs' | 'maxConcurrent' | 'minIntervalMs' | 'backoffBaseMs' | 'backoffMaxMs' | 'jitter' | 'respectRetryAfterHeader' | 'maxQueueSize'
    >
  > & {
    retryAfterMs: number;
    maxConcurrent: number;
    minIntervalMs: number;
    backoffBaseMs: number;
    backoffMaxMs: number;
    jitter: number;
    respectRetryAfterHeader: boolean;
    maxQueueSize: number;
  };

  /** timestamps of recent successful dispatches */
  private readonly stamps: number[] = [];
  /** in-flight count */
  private inFlight = 0;
  /** queue */
  private queue: Array<QueuedRequest> = [];
  /** processing loop flag */
  private processing = false;
  /** paused flag */
  private paused = false;
  /** last dispatch timestamp for minInterval */
  private lastDispatchAt = 0;

  constructor(cfg: RateLimitConfig) {
    this.config = {
      maxRequests: cfg.maxRequests,
      windowMs: cfg.windowMs,
      retryAfterMs: cfg.retryAfterMs ?? 5000,
      maxConcurrent: cfg.maxConcurrent ?? Infinity,
      minIntervalMs: cfg.minIntervalMs ?? 0,
      backoffBaseMs: cfg.backoffBaseMs ?? 1000,
      backoffMaxMs: cfg.backoffMaxMs ?? 30000,
      jitter: cfg.jitter ?? 0.2,
      respectRetryAfterHeader: cfg.respectRetryAfterHeader ?? true,
      maxQueueSize: cfg.maxQueueSize ?? 5000,
    };
  }

  /** Enqueue and execute respecting rate/concurrency limits */
  public execute<T>(request: () => Promise<T>, options: ExecuteOptions = {}): Promise<T> {
    return new Promise<T>((resolve, reject) => {
      const item: QueuedRequest<T> = {
        resolve,
        reject,
        request,
        createdAt: Date.now(),
        attempt: 0,
        options: {
          priority: options.priority ?? 'normal',
          signal: options.signal,
          timeoutMs: options.timeoutMs,
          label: options.label ?? 'request',
        },
      };

      if (this.config.maxQueueSize > 0 && this.queue.length >= this.config.maxQueueSize) {
        // Drop oldest to maintain cap
        this.queue.shift();
      }

      if (item.options.priority === 'high') {
        this.queue.unshift(item);
      } else {
        this.queue.push(item);
      }

      // If already aborted, reject immediately
      if (item.options.signal?.aborted) {
        reject(this.abortError(item.options.label));
        return;
      }

      this.kick();
    });
  }

  /** Helper for fetch with retry/backoff on 429/5xx + Retry-After handling */
  public wrapFetch(
    input: RequestInfo | URL,
    init: RequestInit = {},
    options?: ExecuteOptions
  ): Promise<Response> {
    const label =
      options?.label ??
      (typeof input === 'string' ? `fetch:${input}` : `fetch:${(input as URL).toString?.() ?? 'req'}`);
    return this.execute(async () => {
      const controller = new AbortController();
      const timeout = options?.timeoutMs;
      const signals: AbortSignal[] = [];
      if (init.signal) signals.push(init.signal as AbortSignal);
      if (options?.signal) signals.push(options.signal);
      const composite = this.mergeSignals(signals, controller);

      let timer: ReturnType<typeof setTimeout> | undefined;
      if (timeout && timeout > 0) {
        timer = setTimeout(() => controller.abort(), timeout);
      }

      try {
        const res = await fetch(input, { ...init, signal: composite });
        if (this.isRetriableStatus(res.status)) {
          const retryAfter = this.parseRetryAfter(res.headers.get('Retry-After'));
          const err = new Error(`HTTP ${res.status}`) as RetryAfterError;
          err.__retryAfterMs = retryAfter ?? null;
          throw err;
        }
        return res;
      } finally {
        if (timer) clearTimeout(timer);
      }
    }, { ...options, label });
  }

  /** Pause processing (queued items remain) */
  public pause(): void {
    this.paused = true;
  }

  /** Resume processing */
  public resume(): void {
    if (!this.paused) return;
    this.paused = false;
    this.kick();
  }

  /** Clear queue (does not cancel in-flight) */
  public clearQueue(reason = 'RateLimiter: queue cleared'): void {
    while (this.queue.length) {
      const q = this.queue.shift()!;
      q.reject(new Error(reason));
    }
  }

  /** Stats for dashboards/diagnostics */
  public getStats() {
    this.sweep();
    return {
      queued: this.queue.length,
      inFlight: this.inFlight,
      windowCount: this.stamps.length,
      windowMs: this.config.windowMs,
      maxRequests: this.config.maxRequests,
      paused: this.paused,
    };
  }

  // ---------------- internal engine ----------------

  private kick() {
    if (this.processing) return;
    this.processing = true;
    void this.loop();
  }

  private async loop(): Promise<void> {
    try {
      let shouldContinue = true;
      while (shouldContinue) {
        if (this.paused) {
          shouldContinue = false;
          break;
        }
        this.sweep();

        if (this.queue.length === 0) {
          shouldContinue = false;
          break;
        }

        // respect concurrency
        if (this.inFlight >= this.config.maxConcurrent) {
          await this.delay(10);
          continue;
        }

        // respect rate window
        if (this.stamps.length >= this.config.maxRequests) {
          const wait = this.untilWindowSlot();
          await this.delay(wait);
          continue;
        }

        // respect min interval
        const sinceLast = Date.now() - this.lastDispatchAt;
        if (sinceLast < this.config.minIntervalMs) {
          await this.delay(this.config.minIntervalMs - sinceLast);
          continue;
        }

        const q = this.queue.shift()!;
        if (q.options.signal?.aborted) {
          q.reject(this.abortError(q.options.label));
          continue;
        }

        // Dispatch
        this.inFlight++;
        this.stamps.push(Date.now());
        this.lastDispatchAt = Date.now();

        // Fire and handle result/errors
        void this.runQueued(q).finally(() => {
          this.inFlight--;
        });
      }
    } finally {
      this.processing = false;
      // If items arrived while processing, loop again
      if (!this.paused && this.queue.length > 0) this.kick();
    }
  }

  private async runQueued<T>(q: QueuedRequest<T>): Promise<void> {
    try {
      const out = await q.request();
      q.resolve(out);
    } catch (err: unknown) {
      // Handle retriable errors (429 or explicit flag)
        const retriable = this.isRetriableError(err as Error);
        if (retriable) {
          q.attempt += 1;
          const errorObj = err as { __retryAfterMs?: number | null } | null;
          const retryDelay = this.nextBackoffMs(q.attempt, errorObj?.__retryAfterMs);
          await this.delay(retryDelay);

        // Put back at front with the same options
        this.queue.unshift(q);
        return;
      }
      q.reject(err as Error);
    }
  }

  private nextBackoffMs(attempt: number, serverRetryAfterMs?: number | null): number {
    if (this.config.respectRetryAfterHeader && serverRetryAfterMs && serverRetryAfterMs > 0) {
      return serverRetryAfterMs;
    }
    const base = Math.min(
      this.config.backoffBaseMs * Math.pow(2, Math.max(0, attempt - 1)),
      this.config.backoffMaxMs
    );
    return this.addJitter(base, this.config.jitter);
  }

  private addJitter(value: number, jitter: number): number {
    if (!jitter) return value;
    const delta = value * jitter;
    const offset = (Math.random() * 2 - 1) * delta; // ±jitter
    return Math.max(0, Math.round(value + offset));
  }

  private untilWindowSlot(): number {
    // time until the oldest stamp exits window
    const now = Date.now();
    const oldest = this.stamps[0];
    return Math.max(1, this.config.windowMs - (now - oldest));
    }

  private sweep(): void {
    const now = Date.now();
    // remove stamps outside window
    while (this.stamps.length && now - this.stamps[0] >= this.config.windowMs) {
      this.stamps.shift();
    }
  }

  private delay(ms: number): Promise<void> {
    return new Promise((r) => setTimeout(r, ms));
  }

  private isRetriableStatus(status: number): boolean {
    // throttle / server busy / transient server errors
    return status === 429 || (status >= 500 && status < 600);
  }

  private isRetriableError(err: Error): boolean {
    const msg = (err?.message ?? '').toString();
    if (msg.includes('429')) return true;
    if (msg.startsWith('HTTP 5')) return true;
    // Browser/network aborts are not retriable here
    return false;
  }

  /** Parses Retry-After header: seconds or HTTP-date. Returns ms or null. */
  private parseRetryAfter(header: string | null): number | null {
    if (!header) return null;
    const trimmed = header.trim();
    // seconds form
    if (/^\d+$/.test(trimmed)) {
      const s = parseInt(trimmed, 10);
      return isFinite(s) ? s * 1000 : null;
    }
    // HTTP-date
    const date = Date.parse(trimmed);
    if (!isNaN(date)) {
      const delta = date - Date.now();
      return delta > 0 ? delta : 0;
    }
    return null;
  }

  private abortError(label?: string): Error {
    return new Error(`${label ?? 'request'} aborted`);
  }

  /** Merge AbortSignals: abort if any constituent aborts */
  private mergeSignals(signals: AbortSignal[], controller: AbortController): AbortSignal {
    const onAbort = () => controller.abort();
    for (const s of signals) {
      if (!s) continue;
      if (s.aborted) {
        controller.abort();
        break;
      }
      s.addEventListener('abort', onAbort, { once: true });
    }
    return controller.signal;
  }
}

/* ------------------------------------------------------------------ */
/* Ready-to-use instances (tune as needed)                            */
/* ------------------------------------------------------------------ */

export const errorAnalysisRateLimiter = new RateLimiter({
  maxRequests: 25,             // Under 30/min
  windowMs: 60_000,
  retryAfterMs: 5_000,
  maxConcurrent: 5,
  minIntervalMs: 0,
  backoffBaseMs: 1000,
  backoffMaxMs: 20_000,
  jitter: 0.2,
  respectRetryAfterHeader: true,
  maxQueueSize: 2000,
});

export const apiRateLimiter = new RateLimiter({
  maxRequests: 50,             // General API budget
  windowMs: 60_000,
  retryAfterMs: 2_000,
  maxConcurrent: 10,
  minIntervalMs: 0,
  backoffBaseMs: 800,
  backoffMaxMs: 15_000,
  jitter: 0.25,
  respectRetryAfterHeader: true,
  maxQueueSize: 5000,
});

/* ------------------------------------------------------------------ */
/* Example usage                                                       */
/* ------------------------------------------------------------------ */
// 1) Wrap an arbitrary async function
// await apiRateLimiter.execute(() => myApiCall());

// 2) With high priority and timeout
// await apiRateLimiter.execute(() => myApiCall(), { priority: 'high', timeoutMs: 5000 });

// 3) Wrap fetch with automatic retry on 429/5xx (+ Retry-After)
// const res = await apiRateLimiter.wrapFetch('/api/data', { method: 'GET' }, { timeoutMs: 7000 });
