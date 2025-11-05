import { NextRequest, NextResponse } from 'next/server';
import {
  makeBackendRequest,
  getTimeoutConfig,
  getRetryPolicy,
  checkBackendHealth,
  getConnectionStatus,
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

// In-memory ring buffer of attempts by IP
const sessionValidationAttempts = new Map<string, SessionValidationAttempt[]>();

/** Log session validation attempt for monitoring */
function logSessionValidationAttempt(attempt: SessionValidationAttempt): void {
  const key = attempt.ipAddress || 'unknown';
  const attempts = sessionValidationAttempts.get(key) || [];
  attempts.push(attempt);
  if (attempts.length > 20) attempts.splice(0, attempts.length - 20);
  sessionValidationAttempts.set(key, attempts);

  // lightweight console trace (replace with your logger if desired)
  console.log(
    `[SESSION] ${attempt.success ? 'SUCCESS' : 'FAILED'} validation attempt`,
    {
      errorType: attempt.errorType,
      responseTime: attempt.responseTime,
      retryCount: attempt.retryCount,
      userAgent: attempt.userAgent,
      ipAddress: attempt.ipAddress,
      timestamp: attempt.timestamp.toISOString(),
    }
  );
}

/** Heuristics for retryable errors */
function isRetryableError(error: any): boolean {
  if (!error) return false;
  const msg = String(error.message || error).toLowerCase();
  const isAbort = error.name === 'AbortError' || msg.includes('timeout');
  const isNet = msg.includes('network') || msg.includes('connection') || msg.includes('fetch');
  const isSocket = msg.includes('und_err_socket') || msg.includes('other side closed');
  return isAbort || isNet || isSocket;
}

/** Heuristics for retryable statuses */
function isRetryableStatus(status: number): boolean {
  return status >= 500 || status === 408 || status === 429;
}

/** Test database/backend connectivity with circuit-breaker awareness */
async function testDatabaseConnectivity(): Promise<DatabaseConnectivityResult> {
  const start = Date.now();
  try {
    const healthy = await checkBackendHealth();
    const responseTime = Date.now() - start;

    if (healthy) {
      return {
        isConnected: true,
        responseTime,
        timestamp: new Date(),
      };
    }

    const connectionStatus = await getConnectionStatus();
    return {
      isConnected: false,
      responseTime,
      error: `Backend health check failed. Circuit breaker state: ${connectionStatus.circuitBreakerState}`,
      timestamp: new Date(),
    };
  } catch (error: any) {
    return {
      isConnected: false,
      responseTime: Date.now() - start,
      error: error?.message || 'Database connectivity test failed',
      timestamp: new Date(),
    };
  }
}

/** User-friendly message builder */
function getDatabaseConnectionErrorMessage(
  connectivity: DatabaseConnectivityResult,
  httpStatus: number
): string {
  if (!connectivity.isConnected) {
    const err = (connectivity.error || '').toLowerCase();
    if (err.includes('timeout')) {
      return 'Database authentication is taking longer than expected. Please try again.';
    }
    if (err.includes('network') || err.includes('connection')) {
      return 'Unable to connect to authentication database. Please check your network connection.';
    }
    return 'Authentication database is temporarily unavailable. Please try again later.';
  }

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

export const dynamic = 'force-dynamic';
export const revalidate = 0;

export async function GET(request: NextRequest) {
  const startTime = Date.now();
  const DEBUG_AUTH = Boolean(process.env.DEBUG_AUTH || process.env.NEXT_PUBLIC_DEBUG_AUTH);

  const userAgent = request.headers.get('user-agent') || 'unknown';
  const ipAddress =
    request.headers.get('x-forwarded-for') ||
    request.headers.get('x-real-ip') ||
    'unknown';

  let retryCount = 0;

  try {
    const databaseConnectivity = await testDatabaseConnectivity();

    // Headers for backend call
    const headers: Record<string, string> = {
      'X-Request-ID': `session-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`,
    };
    const cookieHeader = request.headers.get('cookie');
    if (cookieHeader) headers['Cookie'] = cookieHeader;

    const connectionOptions = {
      timeout: timeoutConfig.sessionValidation,
      retryAttempts: retryPolicy.maxAttempts,
      retryDelay: retryPolicy.baseDelay,
      exponentialBackoff: retryPolicy.jitterEnabled,
      headers,
      // extra retry guards for transient failures
      shouldRetry: (status?: number, error?: any) =>
        (typeof status === 'number' && isRetryableStatus(status)) || isRetryableError(error),
    };

    let result: {
      data: any;
      statusCode?: number;
      retryCount?: number;
    };

    try {
      result = await makeBackendRequest(
        '/api/auth/validate-session',
        { method: 'GET' },
        connectionOptions
      );
    } catch (error) {
      const totalResponseTime = Date.now() - startTime;

      let errorType: 'timeout' | 'network' | 'credentials' | 'database' | 'server' = 'server';
      let statusCode = 502;
      let retryable = true;

      if (error instanceof ConnectionError) {
        retryCount = error.retryCount || 0;
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

      logSessionValidationAttempt({
        timestamp: new Date(),
        success: false,
        errorType,
        retryCount,
        responseTime: totalResponseTime,
        userAgent,
        ipAddress,
      });

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
    retryCount = result.retryCount || 0;

    logSessionValidationAttempt({
      timestamp: new Date(),
      success: true,
      retryCount,
      responseTime: totalResponseTime,
      userAgent,
      ipAddress,
    });

    // Shape successful payload; attach connectivity + perf
    const payload = {
      ...(result.data || {}),
      databaseConnectivity,
      responseTime: totalResponseTime,
      attempts:
        DEBUG_AUTH && ipAddress
          ? sessionValidationAttempts.get(ipAddress) ?? []
          : undefined,
    };

    return NextResponse.json(payload, { status: 200 });
  } catch (error) {
    const totalResponseTime = Date.now() - startTime;
    const databaseConnectivity = await testDatabaseConnectivity();

    logSessionValidationAttempt({
      timestamp: new Date(),
      success: false,
      errorType: 'server',
      retryCount,
      responseTime: totalResponseTime,
      userAgent,
      ipAddress,
    });

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
