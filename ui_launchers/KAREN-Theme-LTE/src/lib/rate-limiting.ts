/**
 * Rate Limiting Middleware
 * Provides configurable rate limiting for API endpoints
 */

// Rate limit storage (in production, this would be Redis or database)
const rateLimitStore = new Map<string, {
  count: number;
  resetTime: number;
  windowMs: number;
}>();

// Rate limit configuration
interface RateLimitConfig {
  windowMs: number;
  maxRequests: number;
  skipSuccessfulRequests?: boolean;
  skipFailedRequests?: boolean;
  keyGenerator?: (req: { ip?: string; userId?: string; headers?: { get: (name: string) => string | null } }) => string | undefined;
}

// Default rate limits
const DEFAULT_LIMITS: Record<string, RateLimitConfig> = {
  'global': {
    windowMs: 60 * 1000, // 1 minute
    maxRequests: 100,
    keyGenerator: (req) => req.ip || 'global',
  },
  'per-user': {
    windowMs: 60 * 1000, // 1 minute
    maxRequests: 60,
    keyGenerator: (req) => req.userId || req.ip,
  },
  'per-ip': {
    windowMs: 60 * 1000, // 1 minute
    maxRequests: 1000,
    keyGenerator: (req) => req.ip,
  },
  'auth': {
    windowMs: 60 * 60 * 1000, // 1 hour
    maxRequests: 10,
    keyGenerator: (req) => req.headers?.get('authorization') || 'anonymous',
  },
};

// Rate limit result interface
export interface RateLimitResult {
  allowed: boolean;
  limit?: RateLimitConfig;
  remaining?: number;
  resetTime?: Date;
  retryAfter?: number;
}

// Main rate limiting middleware functions
async function checkRateLimit(
  identifier: string,
  config: RateLimitConfig = DEFAULT_LIMITS['global']!
): Promise<RateLimitResult> {
  const now = Date.now();
  const key = identifier;
  
  // Get current rate limit data
  let rateData = rateLimitStore.get(key);
  
  // Initialize if not exists
  if (!rateData) {
    rateData = {
      count: 0,
      resetTime: now,
      windowMs: config.windowMs,
    };
    rateLimitStore.set(key, rateData);
  }
  
  // Reset window if expired
  if (now - rateData.resetTime > config.windowMs) {
    rateData = {
      count: 0,
      resetTime: now,
      windowMs: config.windowMs,
    };
    rateLimitStore.set(key, rateData);
  }
  
  // Check if under limit
  const allowed = rateData.count < config.maxRequests;
  
  // Update count
  if (allowed) {
    rateData.count++;
  }
  
  rateLimitStore.set(key, rateData);
  
  return {
    allowed,
    limit: config,
    remaining: Math.max(0, config.maxRequests - rateData.count),
    resetTime: new Date(rateData.resetTime + config.windowMs),
    retryAfter: allowed ? undefined : config.windowMs - (now - rateData.resetTime),
  };
}

function getRateLimitStatus(key: string): RateLimitResult | null {
  const rateData = rateLimitStore.get(key);
  if (!rateData) return null;
  
  const now = Date.now();
  const isExpired = now - rateData.resetTime > rateData.windowMs;
  
  return {
    allowed: !isExpired && rateData.count < DEFAULT_LIMITS['global']!.maxRequests,
    limit: DEFAULT_LIMITS['global']!,
    remaining: Math.max(0, DEFAULT_LIMITS['global']!.maxRequests - rateData.count),
    resetTime: new Date(rateData.resetTime + rateData.windowMs),
  };
}

function resetRateLimit(key?: string): void {
  if (key) {
    rateLimitStore.delete(key);
  } else {
    rateLimitStore.clear();
  }
}

function cleanupRateLimits(): void {
  const now = Date.now();
  for (const [key, data] of Array.from(rateLimitStore.entries())) {
    if (now - data.resetTime > data.windowMs * 2) {
      rateLimitStore.delete(key);
    }
  }
}

export const rateLimitMiddleware = {
  check: checkRateLimit,
  
  createMiddleware(config: RateLimitConfig = DEFAULT_LIMITS['global']!) {
    return async (req: { ip?: string; userId?: string; headers?: { get: (name: string) => string | null } }, res: { setHeader: (name: string, value: string) => void; status: (code: number) => { json: (data: unknown) => void }; json: (data: unknown) => void }, next: () => void) => {
      const key = config.keyGenerator ? config.keyGenerator(req) || 'default' : 'default';
      const result = await checkRateLimit(key, config);
      
      if (!result.allowed) {
        res.setHeader('X-RateLimit-Limit', config.maxRequests.toString());
        res.setHeader('X-RateLimit-Remaining', result.remaining?.toString() || '0');
        res.setHeader('X-RateLimit-Reset', result.resetTime?.toUTCString() || '');
        res.setHeader('Retry-After', result.retryAfter?.toString() || '0');
        
        return res.status(429).json({
          error: 'Rate limit exceeded',
          limit: config.maxRequests,
          remaining: result.remaining,
          resetTime: result.resetTime,
        });
      }
      
      // Add rate limit headers for successful requests
      res.setHeader('X-RateLimit-Limit', config.maxRequests.toString());
      res.setHeader('X-RateLimit-Remaining', result.remaining?.toString() || '0');
      res.setHeader('X-RateLimit-Reset', result.resetTime?.toUTCString() || '');
      
      return next();
    };
  },
  
  getStatus: getRateLimitStatus,
  
  reset: resetRateLimit,
  
  cleanup: cleanupRateLimits,
};

// Auto-cleanup every 5 minutes
setInterval(rateLimitMiddleware.cleanup, 5 * 60 * 1000);
