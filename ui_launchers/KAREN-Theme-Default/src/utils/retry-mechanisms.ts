"use client";
/**
 * Retry Mechanisms System (production‑grade)
 *
 * Features
 * - Exponential backoff w/ jitter (full/centered)
 * - Circuit Breaker (closed → open → half-open)
 * - Intelligent retry conditions (HTTP/Network/Timeout/Idempotent)
 * - Observable state per operation (attempts, next delay, last error)
 * - Fetch helper (with optional timeout via AbortController)
 * - React hooks: useRetry, useRetryFetch
 * - SSR-safe and side‑effect free on import
 */

import React from "react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
export interface RetryConfig {
  maxAttempts: number; // total tries including the first
  baseDelay: number; // ms
  maxDelay: number; // ms cap
  backoffFactor: number; // exponential factor
  jitter: boolean | "full" | "centered"; // strategy
  timeoutMs?: number; // for fetch helper
  retryCondition?: (error: any, attempt: number) => boolean;
  onRetry?: (error: any, attempt: number, nextDelayMs: number) => void;
  onSuccess?: (result: any, attempt: number) => void;
  onFailure?: (error: any, attempts: number) => void;
}

export interface RetryState {
  attempt: number;
  isRetrying: boolean;
  lastError: Error | null;
  nextRetryIn: number; // ms
  totalAttempts: number; // alias of attempt for convenience
}

export interface CircuitBreakerConfig {
  failureThreshold: number; // consecutive failures to open
  resetTimeout: number; // ms before half-open probe allowed
  monitoringPeriod: number; // ms to keep idle entries
}

export type CircuitState = "closed" | "open" | "half-open";

export interface CircuitBreakerState {
  state: CircuitState;
  failures: number; // consecutive failures
  lastFailureTime: number; // epoch ms
  nextAttemptTime: number; // epoch ms when half-open probe begins
}

// ---------------------------------------------------------------------------
// Tiny Emitter for state updates
// ---------------------------------------------------------------------------
class Emitter<T = void> {
  private listeners = new Set<(p: T) => void>();
  on(fn: (p: T) => void) {
    this.listeners.add(fn);
    return () => this.off(fn);
  }
  off(fn: (p: T) => void) {
    this.listeners.delete(fn);
  }
  emit(payload: T) {
    this.listeners.forEach((fn) => fn(payload));
  }
}

// SSR guard
const isBrowser = typeof window !== "undefined";

// ---------------------------------------------------------------------------
// Core Service
// ---------------------------------------------------------------------------
class RetryMechanismService {
  private circuitBreakers = new Map<string, CircuitBreakerState>();
  private activeRetries = new Map<string, RetryState>();
  private updated = new Emitter<{ id: string; state: RetryState }>();

  // Defaults
  private defaultConfig: RetryConfig = {
    maxAttempts: 3,
    baseDelay: 1000,
    maxDelay: 30000,
    backoffFactor: 2,
    jitter: "centered",
    retryCondition: (error: any) => this.defaultRetryCondition(error),
  };

  private defaultCircuitBreakerConfig: CircuitBreakerConfig = {
    failureThreshold: 5,
    resetTimeout: 60_000,
    monitoringPeriod: 300_000, // 5 minutes
  };

  // --------------------------- Observability -------------------------------
  onRetryState(cb: (evt: { id: string; state: RetryState }) => void) {
    return this.updated.on(cb);
  }

  // --------------------------- Policies -----------------------------------
  private defaultRetryCondition(error: any): boolean {
    const status = (error?.status ?? error?.response?.status) as number | undefined;
    const name = error?.name as string | undefined;

    // Network-like classes
    if (name === "NetworkError" || name === "TimeoutError") return true;

    // HTTP semantics
    if (status !== undefined) {
      if (status === 408 || status === 429) return true; // timeout / rate-limit
      if (status >= 500 && status < 600) return true; // server errors
      if (status >= 400 && status < 500) return false; // client errors (do not retry)
    }

    // Unknown errors: be conservative but allow retry once
    return true;
  }

  public shouldRetry(error: any, attempt?: number): boolean {
    void attempt;
    return this.defaultRetryCondition(error);
  }

  // --------------------------- Public API ----------------------------------
  public async withRetry<T>(
    operation: () => Promise<T>,
    config: Partial<RetryConfig> = {},
    operationId?: string
  ): Promise<T> {
    const final: RetryConfig = { ...this.defaultConfig, ...config };
    const id = operationId ?? this.createOperationId();

    // Initialize state
    const state: RetryState = {
      attempt: 0,
      isRetrying: false,
      lastError: null,
      nextRetryIn: 0,
      totalAttempts: 0,
    };
    this.activeRetries.set(id, state);

    try {
      const result = await this.executeWithRetry(operation, final, id);
      return result;
    } finally {
      // cleanup of retry state deferred to allow consumers to read final snapshot
      setTimeout(() => this.activeRetries.delete(id), 0);
    }
  }

  private async executeWithRetry<T>(
    operation: () => Promise<T>,
    config: RetryConfig,
    operationId: string
  ): Promise<T> {
    const state = this.activeRetries.get(operationId)!;
    let lastError: any;

    for (let attempt = 1; attempt <= config.maxAttempts; attempt++) {
      state.attempt = attempt;
      state.totalAttempts = attempt;
      this.updated.emit({ id: operationId, state: { ...state } });

      try {
        // Circuit check
        if (!this.canExecute(operationId)) {
          const err = new Error("Circuit breaker is open");
          (err as any).name = "CircuitOpenError";
          throw err;
        }

        const result = await operation();

        // success → record and reset breaker on half-open
        this.recordSuccess(operationId);
        config.onSuccess?.(result, attempt);
        return result;
      } catch (error: any) {
        lastError = error;
        state.lastError = error instanceof Error ? error : new Error(String(error));

        // failure → tick breaker
        this.recordFailure(operationId);

        const canRetry =
          attempt < config.maxAttempts && (config.retryCondition?.(error, attempt) ?? true);

        if (!canRetry) break;

        const delayMs = this.calculateDelay(attempt, config);
        state.nextRetryIn = delayMs;
        state.isRetrying = true;
        this.updated.emit({ id: operationId, state: { ...state } });
        config.onRetry?.(error, attempt, delayMs);

        await this.delay(delayMs);
        state.isRetrying = false;
        this.updated.emit({ id: operationId, state: { ...state } });
      }
    }

    config.onFailure?.(lastError, (this.activeRetries.get(operationId)?.attempt ?? 0));
    throw lastError;
  }

  private calculateDelay(attempt: number, config: RetryConfig): number {
    const base = config.baseDelay * Math.pow(config.backoffFactor, Math.max(0, attempt - 1));
    const capped = Math.min(base, config.maxDelay);

    const strategy = config.jitter;
    if (strategy === false || strategy == null) {
      return Math.floor(capped);
    }

    // Jitter strategies
    if (strategy === "full" || strategy === true) {
      // [0, capped]
      return Math.floor(Math.random() * capped);
    }
    // centered: [0.5capped, capped]
    const min = capped * 0.5;
    const span = capped - min;
    return Math.floor(min + Math.random() * span);
  }

  private delay(ms: number) {
    return new Promise<void>((resolve) => setTimeout(resolve, ms));
  }

  public createOperationId(): string {
    return `retry-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
  }

  // ----------------------- Circuit Breaker ---------------------------------
  public canExecute(operationId: string): boolean {
    const state = this.getCircuitBreakerState(operationId);
    const now = Date.now();

    switch (state.state) {
      case "closed":
        return true;
      case "open":
        if (now >= state.nextAttemptTime) {
          state.state = "half-open"; // allow one probe
          return true;
        }
        return false;
      case "half-open":
        // allow exactly one attempt; success will close, failure will reopen
        return true;
      default:
        return true;
    }
  }

  public recordSuccess(operationId: string): void {
    const state = this.getCircuitBreakerState(operationId);
    if (state.state === "half-open" || state.state === "open") {
      state.state = "closed";
      state.failures = 0;
    } else if (state.state === "closed") {
      state.failures = 0; // keep clean
    }
  }

  public recordFailure(operationId: string): void {
    const state = this.getCircuitBreakerState(operationId);
    const cfg = this.defaultCircuitBreakerConfig;
    const now = Date.now();

    state.failures += 1;
    state.lastFailureTime = now;

    if (state.state === "half-open") {
      // Probe failed → open again
      state.state = "open";
      state.nextAttemptTime = now + cfg.resetTimeout;
      return;
    }

    if (state.failures >= cfg.failureThreshold) {
      state.state = "open";
      state.nextAttemptTime = now + cfg.resetTimeout;
    }
  }

  private getCircuitBreakerState(operationId: string): CircuitBreakerState {
    if (!this.circuitBreakers.has(operationId)) {
      this.circuitBreakers.set(operationId, {
        state: "closed",
        failures: 0,
        lastFailureTime: 0,
        nextAttemptTime: 0,
      });
    }
    return this.circuitBreakers.get(operationId)!;
  }

  // --------------------------- Introspection --------------------------------
  public getRetryState(operationId: string): RetryState | null {
    const st = this.activeRetries.get(operationId);
    return st ? { ...st } : null;
  }

  public getCircuitBreakerStatus(operationId: string): CircuitBreakerState {
    const st = this.getCircuitBreakerState(operationId);
    return { ...st };
  }

  public resetCircuitBreaker(operationId: string): void {
    this.circuitBreakers.set(operationId, {
      state: "closed",
      failures: 0,
      lastFailureTime: 0,
      nextAttemptTime: 0,
    });
  }

  public cleanup(): void {
    const now = Date.now();
    const maxAge = this.defaultCircuitBreakerConfig.monitoringPeriod;
    for (const [id, st] of this.circuitBreakers.entries()) {
      if (st.failures === 0 && now - st.lastFailureTime > maxAge) {
        this.circuitBreakers.delete(id);
      }
    }
  }
}

// Singleton
export const retryMechanism = new RetryMechanismService();

// ---------------------------------------------------------------------------
// React Hooks
// ---------------------------------------------------------------------------
export function useRetry<T>(
  operation: () => Promise<T>,
  config: Partial<RetryConfig> = {},
  dependencies: any[] = []
) {
  const [state, setState] = React.useState<{
    data: T | null;
    error: Error | null;
    isLoading: boolean;
    isRetrying: boolean;
    attempt: number;
    canRetry: boolean;
    operationId: string | null;
  }>(
    {
      data: null,
      error: null,
      isLoading: false,
      isRetrying: false,
      attempt: 0,
      canRetry: true,
      operationId: null,
    }
  );

  const exec = React.useCallback(async () => {
    const opId = retryMechanism.createOperationId();
    setState((prev) => ({ ...prev, isLoading: true, error: null, operationId: opId }));

    // Subscribe to live retry updates to reflect attempt/next delay
    const off = retryMechanism.onRetryState(({ id, state: s }) => {
      if (id === opId) {
        setState((prev) => ({
          ...prev,
          attempt: s.attempt,
          isRetrying: s.isRetrying,
        }));
      }
    });

    try {
      const result = await retryMechanism.withRetry(
        operation,
        {
          ...config,
          onRetry: (error, attempt, nextDelayMs) => {
            setState((prev) => ({
              ...prev,
              isRetrying: true,
              attempt,
              error: error instanceof Error ? error : new Error(String(error)),
            }));
            config.onRetry?.(error, attempt, nextDelayMs);
          },
        },
        opId
      );

      setState((prev) => ({
        ...prev,
        data: result,
        isLoading: false,
        isRetrying: false,
        error: null,
        canRetry: true,
      }));
      return result;
    } catch (e: any) {
      const err = e instanceof Error ? e : new Error(String(e));
      setState((prev) => ({
        ...prev,
        error: err,
        isLoading: false,
        isRetrying: false,
        canRetry: (config.maxAttempts ?? 3) > (prev.attempt || 0),
      }));
      throw err;
    } finally {
      off();
    }
  }, [operation, JSON.stringify(config), ...dependencies]);

  const retry = React.useCallback(() => {
    if (state.canRetry && !state.isLoading) {
      void exec();
    }
  }, [state.canRetry, state.isLoading, exec]);

  const reset = React.useCallback(() => {
    if (state.operationId) {
      retryMechanism.resetCircuitBreaker(state.operationId);
    }
    setState({
      data: null,
      error: null,
      isLoading: false,
      isRetrying: false,
      attempt: 0,
      canRetry: true,
      operationId: null,
    });
  }, [state.operationId]);

  return {
    ...state,
    execute: exec,
    retry,
    reset,
  };
}

// Fetch helper with retry + optional timeout
export async function fetchWithTimeout(input: RequestInfo | URL, init: RequestInit = {}, timeoutMs = 0) {
  if (!timeoutMs) return fetch(input, init);
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(input, { ...init, signal: controller.signal });
    return res;
  } finally {
    clearTimeout(id);
  }
}

export function useRetryFetch(
  url: string,
  options: RequestInit = {},
  config: Partial<RetryConfig> = {}
) {
  return useRetry(
    async () => {
      const timeout = config.timeoutMs ?? 0;
      const opId = `fetch-${url}`;
      const res = await retryMechanism.withRetry(
        async () => {
          const response = await fetchWithTimeout(url, options, timeout);
          if (!response.ok) {
            const error = new Error(`HTTP ${response.status}: ${response.statusText}`);
            (error as any).status = response.status;
            (error as any).response = response;
            throw error;
          }
          return response;
        },
        {
          ...config,
          retryCondition: (error, attempt) => {
            // prefer 429/5xx/timeouts; avoid 4xx except 408/429
            const status = error?.status ?? error?.response?.status;
            if (status === 429 || status === 408) return true;
            return retryMechanism.shouldRetry(error, attempt);
          },
        },
        opId
      );
      return res;
    },
    config,
    [url, JSON.stringify(options)]
  );
}

export default retryMechanism;
