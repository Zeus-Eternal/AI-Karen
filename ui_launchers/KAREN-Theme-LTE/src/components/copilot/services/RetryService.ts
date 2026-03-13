/**
 * Retry configuration options
 */
export interface RetryOptions<TResult = unknown> {
  /** Maximum number of retry attempts */
  maxRetries?: number;
  
  /** Base delay between retries in milliseconds */
  baseDelay?: number;
  
  /** Maximum delay between retries in milliseconds */
  maxDelay?: number;
  
  /** Whether to use exponential backoff */
  exponentialBackoff?: boolean;
  
  /** Jitter factor to add to delay (0-1) */
  jitterFactor?: number;
  
  /** HTTP status codes to retry on */
  retryOnStatusCodes?: number[];
  
  /** Error types to retry on */
  retryOnErrorTypes?: string[];
  
  /** Whether to retry on network errors */
  retryOnNetworkErrors?: boolean;
  
  /** Callback function to execute before each retry */
  onRetry?: (error: unknown, attempt: number, delay: number) => void;
  
  /** Callback function to execute when all retries fail */
  onRetryFailed?: (error: unknown) => void;
  
  /** Fallback function to execute if all retries fail */
  fallback?: () => Promise<TResult> | TResult;
}

/**
 * Retry result information
 */
export interface RetryResult<TResult = unknown> {
  /** Whether the operation succeeded */
  success: boolean;
  
  /** Result if operation succeeded */
  result?: TResult;
  
  /** Error if operation failed */
  error?: unknown;
  
  /** Number of retry attempts */
  attempts: number;
  
  /** Total time spent retrying in milliseconds */
  totalTime: number;
}

/**
 * Service for handling retry logic with exponential backoff
 */
class RetryService {
  private static instance: RetryService;
  
  private constructor() {
    // Initialize with default configuration
  }
  
  public static getInstance(): RetryService {
    if (!RetryService.instance) {
      RetryService.instance = new RetryService();
    }
    return RetryService.instance;
  }
  
  /**
   * Execute a function with retry logic
   */
  public async executeWithRetry<T>(
    fn: () => Promise<T>,
    options: RetryOptions<T> = {}
  ): Promise<RetryResult<T>> {
    const startTime = Date.now();
    const {
      maxRetries = 3,
      baseDelay = 1000,
      maxDelay = 30000,
      exponentialBackoff = true,
      jitterFactor = 0.1,
      retryOnStatusCodes = [408, 429, 500, 502, 503, 504],
      retryOnErrorTypes = ['network_error', 'timeout_error'],
      retryOnNetworkErrors = true,
      onRetry,
      onRetryFailed,
      fallback
    } = options;
    
    let lastError: unknown = null;
    
    for (let attempt = 1; attempt <= maxRetries + 1; attempt++) {
      try {
        const result = await fn();
        
        // If we got here, the operation succeeded
        return {
          success: true,
          result,
          attempts: attempt,
          totalTime: Date.now() - startTime
        };
      } catch (error) {
        lastError = error;
        
        // Check if we should retry
        const shouldRetry = this.shouldRetry(
          error,
          attempt,
          maxRetries,
          retryOnStatusCodes,
          retryOnErrorTypes,
          retryOnNetworkErrors
        );
        
        if (!shouldRetry || attempt > maxRetries) {
          break;
        }
        
        // Calculate delay with exponential backoff and jitter
        const delay = this.calculateDelay(
          attempt,
          baseDelay,
          maxDelay,
          exponentialBackoff,
          jitterFactor
        );
        
        // Call onRetry callback if provided
        if (onRetry) {
          try {
            onRetry(error, attempt, delay);
          } catch (callbackError) {
            console.error('Error in retry callback:', callbackError);
          }
        }
        
        // Wait before retrying
        await this.sleep(delay);
      }
    }
    
    // All retries failed
    if (onRetryFailed) {
      try {
        onRetryFailed(lastError);
      } catch (callbackError) {
        console.error('Error in retry failed callback:', callbackError);
      }
    }
    
    // Try fallback if provided
    if (fallback) {
      try {
        const fallbackResult = await fallback();
        return {
          success: true,
          result: fallbackResult,
          attempts: maxRetries + 1,
          totalTime: Date.now() - startTime
        };
      } catch (fallbackError) {
        lastError = fallbackError;
      }
    }
    
    return {
      success: false,
      error: lastError,
      attempts: maxRetries + 1,
      totalTime: Date.now() - startTime
    };
  }
  
  /**
   * Execute an HTTP request with retry logic
   */
  public async fetchWithRetry(
    url: string,
    options: RequestInit = {},
    retryOptions: RetryOptions<Response> = {}
  ): Promise<RetryResult<Response>> {
    return this.executeWithRetry(async () => {
      const response = await fetch(url, options);
      
      // Check if response is OK
      if (!response.ok) {
        // Create error with status code
        const error = new Error(`HTTP error! status: ${response.status}`) as Error & {
          status?: number;
          response?: Response;
        };
        error.status = response.status;
        error.response = response;
        throw error;
      }
      
      return response;
    }, retryOptions);
  }
  
  /**
   * Execute multiple functions with retry logic in parallel
   */
  public async executeAllWithRetry<T>(
    fns: Array<() => Promise<T>>,
    options: RetryOptions<T> = {}
  ): Promise<RetryResult<T>[]> {
    const promises = fns.map(fn => this.executeWithRetry(fn, options));
    return Promise.all(promises);
  }
  
  /**
   * Execute multiple functions with retry logic in sequence
   */
  public async executeSequenceWithRetry<T>(
    fns: Array<() => Promise<T>>,
    options: RetryOptions<T> = {}
  ): Promise<RetryResult<T>[]> {
    const results: RetryResult<T>[] = [];
    
    for (const fn of fns) {
      const result = await this.executeWithRetry(fn, options);
      results.push(result);
      
      // If one fails and we don't want to continue, break
      if (!result.success) {
        break;
      }
    }
    
    return results;
  }
  
  /**
   * Determine if we should retry based on error
   */
  private shouldRetry(
    error: unknown,
    attempt: number,
    maxRetries: number,
    retryOnStatusCodes: number[],
    retryOnErrorTypes: string[],
    retryOnNetworkErrors: boolean
  ): boolean {
    // Don't retry if we've reached max attempts
    if (attempt > maxRetries) {
      return false;
    }
    
    // Retry on network errors
    if (retryOnNetworkErrors && this.isNetworkError(error)) {
      return true;
    }
    
    // Retry on specific HTTP status codes
    const errorWithStatus = this.asObject(error);
    const status = errorWithStatus?.status;
    if (typeof status === 'number' && retryOnStatusCodes.includes(status)) {
      return true;
    }
    
    // Retry on specific error types
    const code = errorWithStatus?.code;
    if (typeof code === 'string' && retryOnErrorTypes.includes(code)) {
      return true;
    }
    
    // Retry on specific error messages
    const messageValue = errorWithStatus?.message;
    if (typeof messageValue === 'string') {
      const message = messageValue.toLowerCase();
      if (
        message.includes('network') ||
        message.includes('timeout') ||
        message.includes('econnreset') ||
        message.includes('econnrefused') ||
        message.includes('etimedout')
      ) {
        return true;
      }
    }
    
    return false;
  }
  
  /**
   * Check if error is a network error
   */
  private isNetworkError(error: unknown): boolean {
    const errorObj = this.asObject(error);

    // Check for common network error codes
    const code = errorObj?.code;
    if (typeof code === 'string') {
      const networkErrorCodes = [
        'ECONNRESET',
        'ECONNREFUSED',
        'ETIMEDOUT',
        'ENOTFOUND',
        'ENETUNREACH',
        'EHOSTUNREACH'
      ];
      return networkErrorCodes.includes(code);
    }
    
    // Check for Fetch API network errors
    if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
      return true;
    }
    
    // Check for Axios network errors
    const isAxiosError = errorObj?.isAxiosError;
    const response = errorObj?.response;
    if (typeof isAxiosError === 'boolean' && isAxiosError && response == null) {
      return true;
    }
    
    return false;
  }
  
  /**
   * Calculate delay with exponential backoff and jitter
   */
  private calculateDelay(
    attempt: number,
    baseDelay: number,
    maxDelay: number,
    exponentialBackoff: boolean,
    jitterFactor: number
  ): number {
    let delay = baseDelay;
    
    // Apply exponential backoff
    if (exponentialBackoff) {
      delay = baseDelay * Math.pow(2, attempt - 1);
    }
    
    // Cap at maximum delay
    delay = Math.min(delay, maxDelay);
    
    // Apply jitter
    if (jitterFactor > 0) {
      const jitter = delay * jitterFactor * (Math.random() * 2 - 1);
      delay = Math.max(0, delay + jitter);
    }
    
    return Math.floor(delay);
  }
  
  /**
   * Sleep for a specified amount of time
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
  
  /**
   * Create a retry-enabled version of a function
   */
  public withRetry<T>(
    fn: () => Promise<T>,
    options: RetryOptions<T> = {}
  ): () => Promise<RetryResult<T>> {
    return () => this.executeWithRetry(fn, options);
  }
  
  /**
   * Create a retry-enabled version of an HTTP fetch function
   */
  public withFetchRetry(
    url: string,
    options: RequestInit = {},
    retryOptions: RetryOptions<Response> = {}
  ): () => Promise<RetryResult<Response>> {
    return () => this.fetchWithRetry(url, options, retryOptions);
  }

  private asObject(value: unknown): Record<string, unknown> | null {
    return typeof value === 'object' && value !== null
      ? (value as Record<string, unknown>)
      : null;
  }
}

export default RetryService;
