/**
 * Async operation utilities for model selection services
 */

/**
 * Sleep for a specified number of milliseconds
 */
export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Execute an async operation with a timeout
 */
export async function withTimeout<T>(
  promise: Promise<T>,
  timeoutMs: number,
  timeoutMessage: string = 'Operation timed out'
): Promise<T> {
  const timeoutPromise = new Promise<never>((_, reject) => {
    setTimeout(() => reject(new Error(timeoutMessage)), timeoutMs);
  });

  return Promise.race([promise, timeoutPromise]);
}

/**
 * Retry an async operation with exponential backoff
 */
export async function retry<T>(
  operation: () => Promise<T>,
  maxAttempts: number = 3,
  baseDelayMs: number = 1000,
  maxDelayMs: number = 10000,
  backoffMultiplier: number = 2
): Promise<T> {
  let lastError: any;
  let delayMs = baseDelayMs;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error;
      
      if (attempt === maxAttempts) {
        break;
      }

      await sleep(Math.min(delayMs, maxDelayMs));
      delayMs *= backoffMultiplier;
    }
  }

  throw lastError;
}

/**
 * Execute operations in parallel with a concurrency limit
 */
export async function parallelLimit<T, R>(
  items: T[],
  operation: (item: T, index: number) => Promise<R>,
  limit: number = 5
): Promise<R[]> {
  const results: R[] = new Array(items.length);
  const executing: Promise<void>[] = [];
  let index = 0;

  const executeNext = async (): Promise<void> => {
    const currentIndex = index++;
    if (currentIndex >= items.length) {
      return;
    }

    try {
      results[currentIndex] = await operation(items[currentIndex], currentIndex);
    } catch (error) {
      // Store error as result - caller can handle it
      results[currentIndex] = error as any;
    }

    return executeNext();
  };

  // Start initial batch
  for (let i = 0; i < Math.min(limit, items.length); i++) {
    executing.push(executeNext());
  }

  await Promise.all(executing);
  return results;
}

/**
 * Execute operations in batches
 */
export async function executeBatches<T, R>(
  items: T[],
  operation: (batch: T[]) => Promise<R[]>,
  batchSize: number = 10
): Promise<R[]> {
  const results: R[] = [];
  
  for (let i = 0; i < items.length; i += batchSize) {
    const batch = items.slice(i, i + batchSize);
    const batchResults = await operation(batch);
    results.push(...batchResults);
  }
  
  return results;
}

/**
 * Create a debounced async function
 */
export function debounceAsync<T extends (...args: any[]) => Promise<any>>(
  func: T,
  waitMs: number
): (...args: Parameters<T>) => Promise<ReturnType<T>> {
  let timeoutId: NodeJS.Timeout | null = null;
  let resolvePromise: ((value: ReturnType<T>) => void) | null = null;
  let rejectPromise: ((reason: any) => void) | null = null;

  return (...args: Parameters<T>): Promise<ReturnType<T>> => {
    return new Promise((resolve, reject) => {
      // Cancel previous timeout
      if (timeoutId) {
        clearTimeout(timeoutId);
      }

      // Store the resolve/reject for the latest call
      resolvePromise = resolve;
      rejectPromise = reject;

      timeoutId = setTimeout(async () => {
        try {
          const result = await func(...args);
          resolvePromise?.(result);
        } catch (error) {
          rejectPromise?.(error);
        }
        
        timeoutId = null;
        resolvePromise = null;
        rejectPromise = null;
      }, waitMs);
    });
  };
}

/**
 * Create a throttled async function
 */
export function throttleAsync<T extends (...args: any[]) => Promise<any>>(
  func: T,
  limitMs: number
): (...args: Parameters<T>) => Promise<ReturnType<T> | null> {
  let lastCall = 0;
  let isExecuting = false;

  return async (...args: Parameters<T>): Promise<ReturnType<T> | null> => {
    const now = Date.now();
    
    if (isExecuting || now - lastCall < limitMs) {
      return null; // Skip this call
    }

    lastCall = now;
    isExecuting = true;

    try {
      const result = await func(...args);
      return result;
    } finally {
      isExecuting = false;
    }
  };
}

/**
 * Create a queue for sequential execution of async operations
 */
export class AsyncQueue {
  private queue: Array<() => Promise<any>> = [];
  private isProcessing = false;

  /**
   * Add an operation to the queue
   */
  async add<T>(operation: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      this.queue.push(async () => {
        try {
          const result = await operation();
          resolve(result);
        } catch (error) {
          reject(error);
        }
      });

      this.process();
    });
  }

  /**
   * Process the queue
   */
  private async process(): Promise<void> {
    if (this.isProcessing || this.queue.length === 0) {
      return;
    }

    this.isProcessing = true;

    while (this.queue.length > 0) {
      const operation = this.queue.shift();
      if (operation) {
        await operation();
      }
    }

    this.isProcessing = false;
  }

  /**
   * Get queue size
   */
  get size(): number {
    return this.queue.length;
  }

  /**
   * Check if queue is processing
   */
  get processing(): boolean {
    return this.isProcessing;
  }

  /**
   * Clear the queue
   */
  clear(): void {
    this.queue = [];
  }
}

/**
 * Create a semaphore for limiting concurrent operations
 */
export class Semaphore {
  private permits: number;
  private waiting: Array<() => void> = [];

  constructor(permits: number) {
    this.permits = permits;
  }

  /**
   * Acquire a permit
   */
  async acquire(): Promise<void> {
    if (this.permits > 0) {
      this.permits--;
      return;
    }

    return new Promise(resolve => {
      this.waiting.push(resolve);
    });
  }

  /**
   * Release a permit
   */
  release(): void {
    if (this.waiting.length > 0) {
      const resolve = this.waiting.shift();
      resolve?.();
    } else {
      this.permits++;
    }
  }

  /**
   * Execute an operation with the semaphore
   */
  async execute<T>(operation: () => Promise<T>): Promise<T> {
    await this.acquire();
    try {
      return await operation();
    } finally {
      this.release();
    }
  }

  /**
   * Get available permits
   */
  get available(): number {
    return this.permits;
  }

  /**
   * Get waiting count
   */
  get waitingCount(): number {
    return this.waiting.length;
  }
}

/**
 * Create a circuit breaker for async operations
 */
export class CircuitBreaker<T extends (...args: any[]) => Promise<any>> {
  private failures = 0;
  private lastFailureTime = 0;
  private state: 'closed' | 'open' | 'half-open' = 'closed';

  constructor(
    private operation: T,
    private failureThreshold: number = 5,
    private resetTimeoutMs: number = 60000,
    private successThreshold: number = 2
  ) {}

  /**
   * Execute the operation through the circuit breaker
   */
  async execute(...args: Parameters<T>): Promise<ReturnType<T>> {
    if (this.state === 'open') {
      if (Date.now() - this.lastFailureTime > this.resetTimeoutMs) {
        this.state = 'half-open';
        this.failures = 0;
      } else {
        throw new Error('Circuit breaker is open');
      }
    }

    try {
      const result = await this.operation(...args);
      
      if (this.state === 'half-open') {
        this.failures = 0;
        this.state = 'closed';
      }
      
      return result;
    } catch (error) {
      this.failures++;
      this.lastFailureTime = Date.now();
      
      if (this.failures >= this.failureThreshold) {
        this.state = 'open';
      }
      
      throw error;
    }
  }

  /**
   * Get circuit breaker state
   */
  get currentState(): 'closed' | 'open' | 'half-open' {
    return this.state;
  }

  /**
   * Get failure count
   */
  get failureCount(): number {
    return this.failures;
  }

  /**
   * Reset the circuit breaker
   */
  reset(): void {
    this.failures = 0;
    this.lastFailureTime = 0;
    this.state = 'closed';
  }
}

/**
 * Create a promise that resolves after all provided promises settle
 */
export async function allSettled<T>(
  promises: Promise<T>[]
): Promise<Array<{ status: 'fulfilled'; value: T } | { status: 'rejected'; reason: any }>> {
  return Promise.allSettled(promises);
}

/**
 * Create a promise that resolves with the first successful result
 */
export async function firstSuccessful<T>(promises: Promise<T>[]): Promise<T> {
  const errors: any[] = [];
  
  return new Promise((resolve, reject) => {
    let completed = 0;
    
    promises.forEach(promise => {
      promise
        .then(resolve)
        .catch(error => {
          errors.push(error);
          completed++;
          
          if (completed === promises.length) {
            reject(new Error(`All promises failed: ${errors.map(e => e.message).join(', ')}`));
          }
        });
    });
  });
}

/**
 * Create a cancellable promise
 */
export function cancellable<T>(
  promise: Promise<T>
): { promise: Promise<T>; cancel: () => void } {
  let cancelled = false;
  
  const cancellablePromise = new Promise<T>((resolve, reject) => {
    promise
      .then(value => {
        if (!cancelled) {
          resolve(value);
        }
      })
      .catch(error => {
        if (!cancelled) {
          reject(error);
        }
      });
  });
  
  return {
    promise: cancellablePromise,
    cancel: () => {
      cancelled = true;
    }
  };
}