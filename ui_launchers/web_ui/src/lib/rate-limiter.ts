/**
 * Rate Limiter Utility
 * 
 * Handles API rate limiting with exponential backoff and request queuing
 */
interface RateLimitConfig {
  maxRequests: number;
  windowMs: number;
  retryAfterMs?: number;
}
interface QueuedRequest {
  resolve: (value: any) => void;
  reject: (error: any) => void;
  request: () => Promise<any>;
  timestamp: number;
}
class RateLimiter {
  private requests: number[] = [];
  private queue: QueuedRequest[] = [];
  private processing = false;
  constructor(private config: RateLimitConfig) {}
  async execute<T>(request: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      this.queue.push({
        resolve,
        reject,
        request,
        timestamp: Date.now(),

      this.processQueue();

  }
  private async processQueue() {
    if (this.processing || this.queue.length === 0) {
      return;
    }
    this.processing = true;
    while (this.queue.length > 0) {
      const now = Date.now();
      // Clean old requests from tracking
      this.requests = this.requests.filter(
        timestamp => now - timestamp < this.config.windowMs
      );
      // Check if we can make a request
      if (this.requests.length >= this.config.maxRequests) {
        const oldestRequest = Math.min(...this.requests);
        const waitTime = this.config.windowMs - (now - oldestRequest);
        await new Promise(resolve => setTimeout(resolve, waitTime));
        continue;
      }
      // Process next request
      const queuedRequest = this.queue.shift()!;
      this.requests.push(now);
      try {
        const result = await queuedRequest.request();
        queuedRequest.resolve(result);
      } catch (error) {
        // Handle 429 errors with exponential backoff
        if (error instanceof Error && error.message.includes('429')) {
          const retryAfter = this.config.retryAfterMs || 5000;
          await new Promise(resolve => setTimeout(resolve, retryAfter));
          // Put the request back in the queue
          this.queue.unshift(queuedRequest);
          continue;
        }
        queuedRequest.reject(error);
      }
      // Small delay between requests to be respectful
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    this.processing = false;
  }
}
// Create a global rate limiter for error analysis requests
export const errorAnalysisRateLimiter = new RateLimiter({
  maxRequests: 25, // Stay under the 30/minute limit
  windowMs: 60 * 1000, // 1 minute
  retryAfterMs: 5000, // 5 seconds

// Create a general API rate limiter
export const apiRateLimiter = new RateLimiter({
  maxRequests: 50,
  windowMs: 60 * 1000,
  retryAfterMs: 2000,
