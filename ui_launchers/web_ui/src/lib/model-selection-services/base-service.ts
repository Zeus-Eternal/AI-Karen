/**
 * Base service class with common utilities and constants
 */

import { safeError, safeLog } from "@/lib/safe-console";
import { MemoryCache, CacheKeyGenerator } from "./utils/cache-utils";
import { formatMemorySize } from "./utils/resource-utils";
import { ModelSelectionError, ErrorUtils } from "./errors/model-selection-errors";

export abstract class BaseModelService {
  // Cache duration constants
  protected readonly CACHE_DURATION = 30000; // 30 seconds
  protected readonly SCAN_CACHE_DURATION = 60000; // 1 minute for directory scans
  protected readonly REGISTRY_CACHE_DURATION = 45000; // 45 seconds for registry
  protected readonly HEALTH_CACHE_DURATION = 20000; // 20 seconds for health checks
  protected readonly PERFORMANCE_CACHE_DURATION = 60000; // 1 minute for performance data

  // Timing constants
  protected readonly DEFAULT_DEBOUNCE_MS = 2000; // 2 seconds debounce for file changes
  protected readonly DEFAULT_POLLING_INTERVAL = 10000; // 10 seconds polling interval
  protected readonly DEFAULT_TIMEOUT_MS = 30000; // 30 seconds default timeout
  protected readonly HEALTH_CHECK_TIMEOUT_MS = 10000; // 10 seconds for health checks

  // Operation limits
  protected readonly MAX_CONCURRENT_OPERATIONS = 5;
  protected readonly MAX_RETRY_ATTEMPTS = 3;
  protected readonly RETRY_DELAY_MS = 1000;

  // Service state
  protected readonly serviceName: string;
  protected readonly cache: MemoryCache<any>;
  protected isInitialized = false;
  protected isShuttingDown = false;

  constructor(serviceName: string, cacheDefaultTTL?: number) {
    this.serviceName = serviceName;
    this.cache = new MemoryCache(cacheDefaultTTL || this.CACHE_DURATION);
  }

  /**
   * Format memory size in human readable format (backward compatibility)
   */
  protected formatMemorySize(bytes: number): string {
    return formatMemorySize(bytes);
  }

  /**
   * Generate model ID from filename and type
   */
  protected generateModelId(filename: string, type: string): string {
    // Remove file extension and create a clean ID
    const baseName = filename.replace(/\.(gguf|bin|safetensors)$/i, "");
    const cleanName = baseName
      .toLowerCase()
      .replace(/[^a-z0-9.-]/g, "-")
      .replace(/-+/g, "-")
      .replace(/^-|-$/g, "");

    return `${type}-${cleanName}`;
  }

  /**
   * Generate human-readable model name from filename and metadata
   */
  protected generateModelName(
    filename: string,
    metadata: Record<string, any>
  ): string {
    // Remove file extension
    let name = filename.replace(/\.(gguf|bin|safetensors)$/i, "");

    // Clean up common patterns
    name = name.replace(/[._-]/g, " ");
    name = name.replace(/\s+/g, " ");

    // Capitalize words
    name = name
      .split(" ")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(" ");

    // Add quantization info if available
    if (metadata.quantization) {
      name += ` (${metadata.quantization})`;
    }

    return name.trim();
  }

  /**
   * Generate model description from metadata
   */
  protected generateModelDescription(
    metadata: Record<string, any>,
    type: string
  ): string {
    const parts: string[] = [];

    if (metadata.parameter_count) {
      parts.push(`${metadata.parameter_count} parameter model`);
    }

    if (metadata.architecture) {
      parts.push(`based on ${metadata.architecture} architecture`);
    }

    if (metadata.quantization) {
      parts.push(`with ${metadata.quantization} quantization`);
    }

    if (metadata.context_length) {
      parts.push(`supporting ${metadata.context_length} token context`);
    }

    const description = parts.join(", ");
    return description.charAt(0).toUpperCase() + description.slice(1);
  }

  /**
   * Simple hash function for state comparison
   */
  protected simpleHash(str: string): number {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = (hash << 5) - hash + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return hash;
  }

  /**
   * Normalize issue text for grouping similar issues
   */
  protected normalizeIssueText(issue: string): string {
    // Remove specific paths, numbers, and other variable content
    return issue
      .replace(/\/[^\s]+/g, "[path]") // Replace file paths
      .replace(/\d+(\.\d+)?\s*(MB|GB|TB|KB|B)/gi, "[size]") // Replace sizes
      .replace(/\d+/g, "[number]") // Replace numbers
      .replace(/Model \w+/g, "Model [id]") // Replace model IDs
      .trim();
  }

  /**
   * Initialize the service (to be implemented by subclasses)
   */
  protected async initialize(): Promise<void> {
    if (this.isInitialized) {
      return;
    }

    this.log(`Initializing ${this.serviceName} service`);
    this.isInitialized = true;
  }

  /**
   * Shutdown the service gracefully
   */
  protected async shutdown(): Promise<void> {
    if (this.isShuttingDown) {
      return;
    }

    this.log(`Shutting down ${this.serviceName} service`);
    this.isShuttingDown = true;
    this.cache.clear();
  }

  /**
   * Check if service is ready for operations
   */
  protected isReady(): boolean {
    return this.isInitialized && !this.isShuttingDown;
  }

  /**
   * Execute operation with timeout
   */
  protected async withTimeout<T>(
    operation: Promise<T>,
    timeoutMs: number = this.DEFAULT_TIMEOUT_MS,
    operationName?: string
  ): Promise<T> {
    const timeoutPromise = new Promise<never>((_, reject) => {
      setTimeout(() => {
        reject(
          new ModelSelectionError(
            `Operation timed out after ${timeoutMs}ms`,
            "TIMEOUT_ERROR",
            this.serviceName,
            { operationName, timeoutMs }
          )
        );
      }, timeoutMs);

    return Promise.race([operation, timeoutPromise]);
  }

  /**
   * Execute operation with retry logic
   */
  protected async withRetry<T>(
    operation: () => Promise<T>,
    maxAttempts: number = this.MAX_RETRY_ATTEMPTS,
    delayMs: number = this.RETRY_DELAY_MS,
    operationName?: string
  ): Promise<T> {
    let lastError: any;

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        return await operation();
      } catch (error) {
        lastError = error;

        if (attempt === maxAttempts) {
          break;
        }

        this.log(
          `${
            operationName || "Operation"
          } failed (attempt ${attempt}/${maxAttempts}), retrying in ${delayMs}ms...`
        );
        await this.delay(delayMs);

        // Exponential backoff
        delayMs *= 2;
      }
    }

    throw ErrorUtils.wrapError(
      lastError,
      this.serviceName,
      operationName || "Retry operation",
      { maxAttempts, finalDelayMs: delayMs / 2 }
    );
  }

  /**
   * Delay execution for specified milliseconds
   */
  protected delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Generate cache key using the utility
   */
  protected generateCacheKey(
    ...parts: (string | number | boolean | undefined | null)[]
  ): string {
    return CacheKeyGenerator.generate(this.serviceName, ...parts);
  }

  /**
   * Get cached value or compute and cache it
   */
  protected async getCachedOrCompute<T>(
    key: string,
    computeFn: () => Promise<T>,
    ttl?: number
  ): Promise<T> {
    const cached = this.cache.get(key);
    if (cached !== undefined) {
      return cached;
    }

    const result = await computeFn();
    this.cache.set(key, result, ttl);
    return result;
  }

  /**
   * Invalidate cache entries by pattern
   */
  protected invalidateCachePattern(pattern: string): number {
    const keys = this.cache.keys();
    let invalidated = 0;

    keys.forEach((key) => {
      if (key.includes(pattern)) {
        this.cache.delete(key);
        invalidated++;
      }

    return invalidated;
  }

  /**
   * Get service statistics
   */
  protected getServiceStats(): {
    serviceName: string;
    isInitialized: boolean;
    isShuttingDown: boolean;
    cacheSize: number;
    cacheKeys: string[];
  } {
    return {
      serviceName: this.serviceName,
      isInitialized: this.isInitialized,
      isShuttingDown: this.isShuttingDown,
      cacheSize: this.cache.size(),
      cacheKeys: this.cache.keys(),
    };
  }

  /**
   * Handle errors consistently across services
   */
  protected handleError(
    error: any,
    context: string,
    additionalInfo?: Record<string, any>
  ): void {
    const wrappedError = ErrorUtils.wrapError(
      error,
      this.serviceName,
      context,
      ErrorUtils.createContext(additionalInfo)
    );

    ErrorUtils.logError(wrappedError, { error: this.logError.bind(this) });
  }

  /**
   * Validate service configuration
   */
  protected validateConfig<T>(config: T, requiredFields: (keyof T)[]): void {
    for (const field of requiredFields) {
      if (config[field] === undefined || config[field] === null) {
        throw new ModelSelectionError(
          `Missing required configuration field: ${String(field)}`,
          "CONFIG_VALIDATION_ERROR",
          this.serviceName,
          { field: String(field), config }
        );
      }
    }
  }

  /**
   * Create a debounced version of a function
   */
  protected debounce<T extends (...args: any[]) => any>(
    func: T,
    waitMs: number = this.DEFAULT_DEBOUNCE_MS
  ): (...args: Parameters<T>) => void {
    let timeoutId: NodeJS.Timeout | null = null;

    return (...args: Parameters<T>) => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }

      timeoutId = setTimeout(() => {
        func.apply(this, args);
        timeoutId = null;
      }, waitMs);
    };
  }

  /**
   * Create a throttled version of a function
   */
  protected throttle<T extends (...args: any[]) => any>(
    func: T,
    limitMs: number = 1000
  ): (...args: Parameters<T>) => void {
    let lastCall = 0;

    return (...args: Parameters<T>) => {
      const now = Date.now();
      if (now - lastCall >= limitMs) {
        lastCall = now;
        func.apply(this, args);
      }
    };
  }

  /**
   * Execute multiple operations concurrently with limit
   */
  protected async executeConcurrently<T, R>(
    items: T[],
    operation: (item: T) => Promise<R>,
    concurrencyLimit: number = this.MAX_CONCURRENT_OPERATIONS
  ): Promise<R[]> {
    const results: R[] = [];
    const executing: Promise<void>[] = [];

    for (const item of items) {
      const promise = operation(item).then((result) => {
        results.push(result);

      executing.push(promise);

      if (executing.length >= concurrencyLimit) {
        await Promise.race(executing);
        // Remove completed promises
        for (let i = executing.length - 1; i >= 0; i--) {
          if (
            await Promise.race([
              executing[i].then(() => true),
              Promise.resolve(false),
            ])
          ) {
            executing.splice(i, 1);
          }
        }
      }
    }

    await Promise.all(executing);
    return results;
  }

  /**
   * Create a safe async operation wrapper
   */
  protected safeAsync<T>(
    operation: () => Promise<T>,
    fallback: T,
    operationName?: string
  ): Promise<T> {
    return operation().catch((error) => {
      this.handleError(error, operationName || "Safe async operation");
      return fallback;

  }

  /**
   * Measure operation execution time
   */
  protected async measureTime<T>(
    operation: () => Promise<T>,
    operationName?: string
  ): Promise<{ result: T; duration: number }> {
    const startTime = Date.now();

    try {
      const result = await operation();
      const duration = Date.now() - startTime;

      if (operationName) {
        this.log(`${operationName} completed in ${duration}ms`);
      }

      return { result, duration };
    } catch (error) {
      const duration = Date.now() - startTime;
      this.logError(
        `${operationName || "Operation"} failed after ${duration}ms`,
        error
      );
      throw error;
    }
  }

  /**
   * Create a circuit breaker for operations
   */
  protected createCircuitBreaker<T extends (...args: any[]) => Promise<any>>(
    operation: T,
    failureThreshold: number = 5,
    resetTimeoutMs: number = 60000
  ): T {
    let failures = 0;
    let lastFailureTime = 0;
    let isOpen = false;

    return ((...args: Parameters<T>) => {
      const now = Date.now();

      // Reset if enough time has passed
      if (isOpen && now - lastFailureTime > resetTimeoutMs) {
        isOpen = false;
        failures = 0;
      }

      // Reject if circuit is open
      if (isOpen) {
        return Promise.reject(
          new ModelSelectionError(
            "Circuit breaker is open",
            "CIRCUIT_BREAKER_OPEN",
            this.serviceName,
            { failures, lastFailureTime }
          )
        );
      }

      return operation(...args).catch((error) => {
        failures++;
        lastFailureTime = now;

        if (failures >= failureThreshold) {
          isOpen = true;
          this.log(`Circuit breaker opened after ${failures} failures`);
        }

        throw error;

    }) as T;
  }

  /**
   * Batch operations to reduce overhead
   */
  protected createBatcher<T, R>(
    batchOperation: (items: T[]) => Promise<R[]>,
    batchSize: number = 10,
    maxWaitMs: number = 1000
  ): (item: T) => Promise<R> {
    const queue: Array<{
      item: T;
      resolve: (result: R) => void;
      reject: (error: any) => void;
    }> = [];

    let batchTimeout: NodeJS.Timeout | null = null;

    const processBatch = async () => {
      if (queue.length === 0) return;

      const batch = queue.splice(0, batchSize);
      const items = batch.map((entry) => entry.item);

      try {
        const results = await batchOperation(items);
        batch.forEach((entry, index) => {
          entry.resolve(results[index]);

      } catch (error) {
        batch.forEach((entry) => {
          entry.reject(error);

      }
    };

    return (item: T): Promise<R> => {
      return new Promise((resolve, reject) => {
        queue.push({ item, resolve, reject });

        // Process immediately if batch is full
        if (queue.length >= batchSize) {
          if (batchTimeout) {
            clearTimeout(batchTimeout);
            batchTimeout = null;
          }
          processBatch();
        } else if (!batchTimeout) {
          // Set timeout for partial batch
          batchTimeout = setTimeout(() => {
            batchTimeout = null;
            processBatch();
          }, maxWaitMs);
        }

    };
  }

  /**
   * Create a memoized version of an async function
   */
  protected memoizeAsync<T extends (...args: any[]) => Promise<any>>(
    func: T,
    keyGenerator?: (...args: Parameters<T>) => string,
    ttl?: number
  ): T {
    const cache = new MemoryCache<any>(ttl || this.CACHE_DURATION);

    return ((...args: Parameters<T>) => {
      const key = keyGenerator
        ? keyGenerator(...args)
        : this.generateCacheKey(...args);

      const cached = cache.get(key);
      if (cached !== undefined) {
        return Promise.resolve(cached);
      }

      const promise = func(...args);
      promise
        .then((result) => {
          cache.set(key, result);
        })
        .catch(() => {
          // Don't cache errors

      return promise;
    }) as T;
  }

  /**
   * Validate and sanitize input data
   */
  protected validateInput<T>(
    input: any,
    validator: (input: any) => input is T,
    errorMessage: string = "Invalid input"
  ): T {
    if (!validator(input)) {
      throw new ModelSelectionError(
        errorMessage,
        "INPUT_VALIDATION_ERROR",
        this.serviceName,
        { input }
      );
    }
    return input;
  }

  /**
   * Create a rate limiter for operations
   */
  protected createRateLimiter(
    maxOperations: number,
    windowMs: number = 60000
  ): () => Promise<void> {
    const operations: number[] = [];

    return async (): Promise<void> => {
      const now = Date.now();

      // Remove operations outside the window
      while (operations.length > 0 && operations[0] <= now - windowMs) {
        operations.shift();
      }

      // Check if we're at the limit
      if (operations.length >= maxOperations) {
        const oldestOperation = operations[0];
        const waitTime = windowMs - (now - oldestOperation);

        if (waitTime > 0) {
          await this.delay(waitTime);
          return this.createRateLimiter(maxOperations, windowMs)();
        }
      }

      operations.push(now);
    };
  }

  /**
   * Safe logging wrapper with service context
   */
  protected log(message: string, ...args: any[]): void {
    safeLog(`[${this.serviceName}] ${message}`, ...args);
  }

  /**
   * Safe error logging wrapper with service context
   */
  protected logError(message: string, error?: any): void {
    safeError(`[${this.serviceName}] ${message}`, error);
  }
}
