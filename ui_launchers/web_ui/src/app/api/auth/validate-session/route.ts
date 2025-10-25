import { NextRequest, NextResponse } from 'next/server';
import { 
  makeBackendRequest, 
  getTimeoutConfig, 
  getRetryPolicy,
  checkBackendHealth,
  getConnectionStatus 
} from '@/app/api/_utils/backend';
import { ConnectionError } from '@/lib/connection/connection-manager';

interface DatabaseConnectivityResult {
  isConnected: boolean;
  responseTime: number;
  error?: string;
  timestamp: Date;
}

interface SessionValidationAttempt {
  timestamp: Date;
  success: boolean;
  errorType?: 'timeout' | 'network' | 'credentials' | 'database' | 'server';
  retryCount: number;
  responseTime: number;
  userAgent?: string;
  ipAddress?: string;
}

interface ErrorResponse {
  valid: false;
  user: null;
  error: string;
  errorType: string;
  retryable: boolean;
  retryAfter?: number;
  databaseConnectivity?: DatabaseConnectivityResult;
  responseTime?: number;
  timestamp: string;
}

const timeoutConfig = getTimeoutConfig();
const retryPolicy = getRetryPolicy();

// Session validation attempt tracking (in-memory for now)
const sessionValidationAttempts = new Map<string, SessionValidationAttempt[]>();

/**
 * Log session validation attempt for monitoring
 */
function logSessionValidationAttempt(attempt: SessionValidationAttempt): void {
  const key = attempt.ipAddress || 'unknown';
  const attempts = sessionValidationAttempts.get(key) || [];
  attempts.push(attempt);
  
  // Keep only last 20 attempts per IP
  if (attempts.length > 20) {
    attempts.splice(0, attempts.length - 20);
  }
  
  sessionValidationAttempts.set(key, attempts);
  
  // Log to console for monitoring
  console.log(`[SESSION] ${attempt.success ? 'SUCCESS' : 'FAILED'} validation attempt:`, {
    errorType: attempt.errorType,
    responseTime: attempt.responseTime,
    retryCount: attempt.retryCount,
    timestamp: attempt.timestamp.toISOString(),
  });
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
 * Test database connectivity for authentication validation using enhanced backend utilities
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

export async function GET(request: NextRequest) {
  const startTime = Date.now();
  const DEBUG_AUTH = Boolean(process.env.DEBUG_AUTH || process.env.NEXT_PUBLIC_DEBUG_AUTH);
  
  // Extract request metadata for logging
  const userAgent = request.headers.get('user-agent') || 'unknown';
  const ipAddress = request.headers.get('x-forwarded-for') || 
                   request.headers.get('x-real-ip') || 
                   'unknown';
  
  let retryCount = 0;
  
  try {
    // Test database connectivity first with enhanced error handling
    const databaseConnectivity = await testDatabaseConnectivity();
    
    // Forward the request to the backend using enhanced backend utilities
    const headers: Record<string, string> = {
      'X-Request-ID': `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    };

    // Forward cookies from the request
    const cookieHeader = request.headers.get('cookie');
    if (cookieHeader) {
      headers['Cookie'] = cookieHeader;
    }

    const connectionOptions = {
      timeout: timeoutConfig.sessionValidation,
      retryAttempts: retryPolicy.maxAttempts,
      retryDelay: retryPolicy.baseDelay,
      exponentialBackoff: retryPolicy.jitterEnabled,
      headers,
    };

    let result;
    try {
      result = await makeBackendRequest('/api/auth/validate-session', {
        method: 'GET',
      }, connectionOptions);
    } catch (error) {
      console.error('Validate session proxy error:', error);
      const totalResponseTime = Date.now() - startTime;
      
      // Extract error information from ConnectionError if available
      let errorType: 'timeout' | 'network' | 'credentials' | 'database' | 'server' = 'server';
      let statusCode = 502;
      let retryable = true;
      
      if (error instanceof ConnectionError) {
        retryCount = error.retryCount;
        statusCode = error.statusCode || 502;
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
      
      // Log failed session validation attempt
      const attempt: SessionValidationAttempt = {
        timestamp: new Date(),
        success: false,
        errorType,
        retryCount,
        responseTime: totalResponseTime,
        userAgent,
        ipAddress,
      };
      logSessionValidationAttempt(attempt);
      
      const errorResponse: ErrorResponse = {
        valid: false,
        user: null,
        error: getDatabaseConnectionErrorMessage(databaseConnectivity, statusCode),
        errorType,
        retryable,
        databaseConnectivity,
        responseTime: totalResponseTime,
        timestamp: new Date().toISOString(),
      };
      
      return NextResponse.json(errorResponse, { status: statusCode });
    }

    const totalResponseTime = Date.now() - startTime;
    retryCount = result.retryCount;
    const data = result.data;
    
    // Log successful session validation attempt
    const successAttempt: SessionValidationAttempt = {
      timestamp: new Date(),
      success: true,
      retryCount,
      responseTime: totalResponseTime,
      userAgent,
      ipAddress,
    };
    logSessionValidationAttempt(successAttempt);
    
    // Include database connectivity information in successful response
    return NextResponse.json({
      ...data,
      databaseConnectivity,
      responseTime: totalResponseTime,
    });
    
  } catch (error) {
    console.error('Validate session proxy error:', error);
    const totalResponseTime = Date.now() - startTime;
    
    // Test database connectivity even in error cases
    const databaseConnectivity = await testDatabaseConnectivity();
    
    // Log failed session validation attempt
    const attempt: SessionValidationAttempt = {
      timestamp: new Date(),
      success: false,
      errorType: 'server',
      retryCount,
      responseTime: totalResponseTime,
      userAgent,
      ipAddress,
    };
    logSessionValidationAttempt(attempt);
    
    const errorResponse: ErrorResponse = {
      valid: false,
      user: null,
      error: getDatabaseConnectionErrorMessage(databaseConnectivity, 500),
      errorType: 'server',
      retryable: true,
      databaseConnectivity,
      responseTime: totalResponseTime,
      timestamp: new Date().toISOString(),
    };
    
    return NextResponse.json(errorResponse, { status: 500 });
  }
}

/**
 * Get user-friendly error message based on database connectivity status
 */
function getDatabaseConnectionErrorMessage(
  connectivity: DatabaseConnectivityResult, 
  httpStatus: number
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
      return 'Session has expired. Please log in again.';
    case 403:
      return 'Access denied. Please verify your permissions.';
    case 429:
      return 'Too many requests. Please wait a moment and try again.';
    case 500:
    case 502:
    case 503:
      return 'Authentication service temporarily unavailable. Please try again.';
    default:
      return 'Session validation failed. Please try logging in again.';
  }
}