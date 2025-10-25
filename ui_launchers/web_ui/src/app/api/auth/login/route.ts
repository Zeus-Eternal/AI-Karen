import { NextRequest, NextResponse } from 'next/server';

import { 
  makeBackendRequest, 
  getTimeoutConfig, 
  getRetryPolicy,
  checkBackendHealth,
  getConnectionStatus 
} from '@/app/api/_utils/backend';
import { isSimpleAuthEnabled } from '@/lib/auth/env';
import { ConnectionError } from '@/lib/connection/connection-manager';

interface DatabaseConnectivityResult {
  isConnected: boolean;
  responseTime: number;
  error?: string;
  timestamp: Date;
}

interface AuthenticationAttempt {
  timestamp: Date;
  email: string;
  success: boolean;
  errorType?: 'timeout' | 'network' | 'credentials' | 'database' | 'server';
  retryCount: number;
  responseTime: number;
  userAgent?: string;
  ipAddress?: string;
}

interface ErrorResponse {
  error: string;
  errorType: string;
  retryable: boolean;
  retryAfter?: number;
  databaseConnectivity?: DatabaseConnectivityResult;
  responseTime?: number;
  timestamp: string;
}

const SIMPLE_AUTH_ENABLED = isSimpleAuthEnabled();
const timeoutConfig = getTimeoutConfig();
const retryPolicy = getRetryPolicy();

// Authentication attempt tracking (in-memory for now)
const authAttempts = new Map<string, AuthenticationAttempt[]>();

/**
 * Log authentication attempt for monitoring and security
 */
function logAuthenticationAttempt(attempt: AuthenticationAttempt): void {
  const key = `${attempt.email}:${attempt.ipAddress || 'unknown'}`;
  const attempts = authAttempts.get(key) || [];
  attempts.push(attempt);
  
  // Keep only last 10 attempts per email/IP combination
  if (attempts.length > 10) {
    attempts.splice(0, attempts.length - 10);
  }
  
  authAttempts.set(key, attempts);
  
  // Log to console for monitoring (in production, this would go to a proper logging system)
  console.log(`[AUTH] ${attempt.success ? 'SUCCESS' : 'FAILED'} login attempt:`, {
    email: attempt.email,
    errorType: attempt.errorType,
    responseTime: attempt.responseTime,
    retryCount: attempt.retryCount,
    timestamp: attempt.timestamp.toISOString(),
  });
}

/**
 * Check if IP/email combination has too many recent failed attempts
 */
function isRateLimited(email: string, ipAddress: string): boolean {
  const key = `${email}:${ipAddress}`;
  const attempts = authAttempts.get(key) || [];
  
  // Check for more than 5 failed attempts in the last 15 minutes
  const fifteenMinutesAgo = new Date(Date.now() - 15 * 60 * 1000);
  const recentFailedAttempts = attempts.filter(
    attempt => !attempt.success && attempt.timestamp > fifteenMinutesAgo
  );
  
  return recentFailedAttempts.length >= 5;
}

/**
 * Test database connectivity for authentication using enhanced backend utilities
 */
async function testDatabaseConnectivity(): Promise<DatabaseConnectivityResult> {
  const startTime = Date.now();
  
  try {
    const isHealthy = await checkBackendHealth();
    const responseTime = Date.now() - startTime;
    
    if (isHealthy) {
      return {
        isConnected: true,
        responseTime,
        timestamp: new Date(),
      };
    } else {
      const connectionStatus = getConnectionStatus();
      return {
        isConnected: false,
        responseTime,
        error: `Backend health check failed. Circuit breaker state: ${connectionStatus.circuitBreakerState}`,
        timestamp: new Date(),
      };
    }
  } catch (error: any) {
    const responseTime = Date.now() - startTime;
    return {
      isConnected: false,
      responseTime,
      error: error.message || 'Database connectivity test failed',
      timestamp: new Date(),
    };
  }
}

export async function POST(request: NextRequest) {
  const startTime = Date.now();
  const DEBUG_AUTH = Boolean(process.env.DEBUG_AUTH || process.env.NEXT_PUBLIC_DEBUG_AUTH);
  
  // Extract request metadata for logging
  const userAgent = request.headers.get('user-agent') || 'unknown';
  const ipAddress = request.headers.get('x-forwarded-for') || 
                   request.headers.get('x-real-ip') || 
                   'unknown';
  
  let email = 'unknown';
  let retryCount = 0;
  
  try {
    const body = await request.json();
    email = body.email || 'unknown';
    
    // Check rate limiting
    if (isRateLimited(email, ipAddress)) {
      const attempt: AuthenticationAttempt = {
        timestamp: new Date(),
        email,
        success: false,
        errorType: 'network',
        retryCount: 0,
        responseTime: Date.now() - startTime,
        userAgent,
        ipAddress,
      };
      logAuthenticationAttempt(attempt);
      
      return NextResponse.json({
        error: 'Too many failed login attempts. Please wait 15 minutes before trying again.',
        errorType: 'rate_limit',
        retryable: true,
        retryAfter: 900, // 15 minutes in seconds
        timestamp: new Date().toISOString(),
      } as ErrorResponse, { status: 429 });
    }
    
    // Test database connectivity before attempting authentication
    const databaseConnectivity = await testDatabaseConnectivity();
    
    // Forward the request to the backend using enhanced backend utilities
    const headers: Record<string, string> = {
      'X-Request-ID': `auth-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    };

    const connectionOptions = {
      timeout: timeoutConfig.authentication,
      retryAttempts: retryPolicy.maxAttempts,
      retryDelay: retryPolicy.baseDelay,
      exponentialBackoff: retryPolicy.jitterEnabled,
      headers,
    };

    let result;
    try {
      // Try primary authentication endpoint
      result = await makeBackendRequest('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...connectionOptions.headers,
        },
        body: JSON.stringify(body),
      }, connectionOptions);
      
    } catch (error) {
      // Fallback to simple-auth mount if API path not found and simple auth is enabled
      if (error instanceof ConnectionError && 
          (error.statusCode === 404 || error.statusCode === 405) && 
          SIMPLE_AUTH_ENABLED) {
        try {
          result = await makeBackendRequest('/auth/login', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              ...connectionOptions.headers,
            },
            body: JSON.stringify(body),
          }, connectionOptions);
        } catch (fallbackError) {
          throw error; // Throw original error if fallback also fails
        }
      } else {
        throw error;
      }
    }
    
    const totalResponseTime = Date.now() - startTime;
    retryCount = result.retryCount;
    const data = result.data;
    
    // Log successful authentication attempt
    const successAttempt: AuthenticationAttempt = {
      timestamp: new Date(),
      email,
      success: true,
      retryCount,
      responseTime: totalResponseTime,
      userAgent,
      ipAddress,
    };
    logAuthenticationAttempt(successAttempt);
    
    // Create the response with the data and database connectivity info
    const nextResponse = NextResponse.json({
      ...data,
      databaseConnectivity,
      responseTime: totalResponseTime
    });
    
    // Forward any Set-Cookie headers from the backend
    try {
      const setCookieHeaders: string[] = [];
      try {
        // Prefer iterating entries (works in Node/fetch runtimes)
        const headersAny = result.headers as any;
        if (typeof headersAny.entries === 'function') {
          for (const [k, v] of headersAny.entries()) {
            if (String(k).toLowerCase() === 'set-cookie' && v) setCookieHeaders.push(String(v));
          }
        }
        // Fallback to single header
        const single = result.headers.get('set-cookie');
        if (single && !setCookieHeaders.includes(single)) setCookieHeaders.push(single);
      } catch (e) {
        // ignore; leave setCookieHeaders empty
      }

      if (DEBUG_AUTH) console.log('Login proxy: backend Set-Cookie headers:', setCookieHeaders);
      for (const raw of setCookieHeaders) {
        if (!raw) continue;
        // Parse simple cookie string into name/value and attributes.
        const parts = raw.split(';').map(p => p.trim());
        const [nameValue, ...attrs] = parts;
        const eq = nameValue.indexOf('=');
        if (eq === -1) continue;
        const name = nameValue.substring(0, eq);
        const value = nameValue.substring(eq + 1);

        const cookieOptions: any = { path: '/' };
        for (const attr of attrs) {
          const [k, v] = attr.split('=').map(s => s.trim());
          const key = k.toLowerCase();
          if (key === 'httponly') cookieOptions.httpOnly = true;
          else if (key === 'secure') cookieOptions.secure = true;
          else if (key === 'samesite') cookieOptions.sameSite = (v || '').toLowerCase();
          else if (key === 'path') cookieOptions.path = v || '/';
          else if (key === 'max-age') cookieOptions.maxAge = Number(v);
          else if (key === 'expires') {
            const date = new Date(v);
            if (!Number.isNaN(date.getTime())) {
              cookieOptions.expires = date;
            }
          }
        }

        try {
          nextResponse.cookies.set(name, value, cookieOptions);
        } catch (e) {
          // If NextResponse.cookies.set fails for any cookie, fall back to
          // forwarding the raw header to ensure the cookie is sent.
          if (DEBUG_AUTH) console.log('Login proxy: failed to set cookie via NextResponse.cookies.set, appending raw header', name, e);
          nextResponse.headers.append('Set-Cookie', raw);
        }
      }
    } catch (e) {
      // Safe fallback: forward single header if parsing fails
      const single = result.headers.get('set-cookie');
      if (single) nextResponse.headers.set('Set-Cookie', single);
    }

    // Also set our own auth_token cookie for downstream proxying
    const token = data?.access_token;
    if (typeof token === 'string' && token.length > 0) {
      try {
        nextResponse.cookies.set('auth_token', token, {
          httpOnly: true,
          sameSite: 'lax',
          secure: false, // dev
          path: '/',
          maxAge: data?.expires_in ? Number(data.expires_in) : 24 * 60 * 60,
        });
      } catch {
        // ignore cookie errors in dev
      }
    }
    
    return nextResponse;
    
  } catch (error) {
    console.error('Login proxy error:', error);
    const totalResponseTime = Date.now() - startTime;
    
    // Test database connectivity even in error cases
    const databaseConnectivity = await testDatabaseConnectivity();
    
    // Extract error information from ConnectionError if available
    let errorType: 'timeout' | 'network' | 'credentials' | 'database' | 'server' = 'server';
    let statusCode = 500;
    let retryable = true;
    
    if (error instanceof ConnectionError) {
      retryCount = error.retryCount;
      statusCode = error.statusCode || 500;
      retryable = error.retryable;
      
      switch (error.category) {
        case 'timeout_error':
          errorType = 'timeout';
          break;
        case 'network_error':
          errorType = 'network';
          break;
        case 'http_error':
          errorType = statusCode === 401 || statusCode === 403 ? 'credentials' : 'server';
          break;
        default:
          errorType = 'server';
      }
    }
    
    // Log failed authentication attempt
    const attempt: AuthenticationAttempt = {
      timestamp: new Date(),
      email,
      success: false,
      errorType,
      retryCount,
      responseTime: totalResponseTime,
      userAgent,
      ipAddress,
    };
    logAuthenticationAttempt(attempt);
    
    const errorResponse: ErrorResponse = {
      error: getLoginErrorMessage(databaseConnectivity, statusCode, error instanceof Error ? error.message : 'Unknown error'),
      errorType,
      retryable,
      databaseConnectivity,
      responseTime: totalResponseTime,
      timestamp: new Date().toISOString(),
    };
    
    return NextResponse.json(errorResponse, { status: statusCode });
  }
}

/**
 * Get error type from exception
 */
function getErrorType(error: any): 'timeout' | 'network' | 'credentials' | 'database' | 'server' {
  if (!error) return 'server';
  
  const message = String(error.message || error).toLowerCase();
  
  if (error.name === 'AbortError' || message.includes('timeout')) {
    return 'timeout';
  }
  if (message.includes('network') || message.includes('connection') || message.includes('fetch')) {
    return 'network';
  }
  if (message.includes('database') || message.includes('db')) {
    return 'database';
  }
  
  return 'server';
}

/**
 * Get error type from HTTP status code
 */
function getErrorTypeFromStatus(status: number): 'timeout' | 'network' | 'credentials' | 'database' | 'server' {
  switch (status) {
    case 401:
    case 403:
      return 'credentials';
    case 408:
    case 504:
      return 'timeout';
    case 502:
    case 503:
      return 'network';
    case 500:
      return 'database';
    default:
      return 'server';
  }
}

/**
 * Check if error is retryable
 */
function isRetryableError(error: any): boolean {
  if (!error) return false;
  
  const message = String(error.message || error).toLowerCase();
  const isTimeout = error.name === 'AbortError' || message.includes('timeout');
  const isNetwork = message.includes('network') || message.includes('connection') || message.includes('fetch');
  const isSocket = message.includes('und_err_socket') || message.includes('other side closed');
  
  return isTimeout || isNetwork || isSocket;
}

/**
 * Check if HTTP status is retryable
 */
function isRetryableStatus(status: number): boolean {
  return status >= 500 || status === 408 || status === 429;
}

/**
 * Get user-friendly error message based on database connectivity status and HTTP status
 */
function getLoginErrorMessage(
  connectivity: DatabaseConnectivityResult, 
  httpStatus: number,
  originalError?: string
): string {
  if (!connectivity.isConnected) {
    if (connectivity.error?.includes('timeout')) {
      return 'Database authentication is taking longer than expected. Please try again.';
    } else if (connectivity.error?.includes('network') || connectivity.error?.includes('connection')) {
      return 'Unable to connect to authentication database. Please check your network connection.';
    } else {
      return 'Authentication database is temporarily unavailable. Please try again later.';
    }
  }
  
  // Database is connected but authentication failed
  switch (httpStatus) {
    case 401:
      return 'Invalid email or password. Please try again.';
    case 403:
      return 'Access denied. Please verify your credentials.';
    case 429:
      return 'Too many login attempts. Please wait a moment and try again.';
    case 500:
    case 502:
    case 503:
      return 'Authentication service temporarily unavailable. Please try again.';
    default:
      return originalError || 'Login failed. Please try again.';
  }
}
