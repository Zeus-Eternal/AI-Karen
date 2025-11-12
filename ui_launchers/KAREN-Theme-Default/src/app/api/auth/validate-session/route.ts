import { NextRequest, NextResponse } from 'next/server';
// Temporarily disable complex backend utilities that may have client-side dependencies
// import {
//   makeBackendRequest,
//   getTimeoutConfig,
//   getRetryPolicy,
//   checkBackendHealth,
//   getConnectionStatus,
// } from '@/app/api/_utils/backend';

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

// Use simple timeout and retry config
const timeoutConfig = { sessionValidation: 10000 };
const retryPolicy = { maxAttempts: 2, baseDelay: 300, jitterEnabled: false };

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
type NormalizedError = {
  name: string;
  message: string;
  status?: number;
};

function normalizeError(error: unknown): NormalizedError {
  if (typeof error === 'object' && error !== null) {
    const candidate = error as { name?: unknown; message?: unknown; status?: unknown };
    return {
      name: typeof candidate.name === 'string' ? candidate.name : '',
      message: typeof candidate.message === 'string' ? candidate.message : '',
      status: typeof candidate.status === 'number' ? candidate.status : undefined,
    };
  }

  return { name: '', message: String(error ?? ''), status: undefined };
}

function isRetryableError(error: unknown): boolean {
  const { name, message } = normalizeError(error);
  const msg = message.toLowerCase();
  const isAbort = name === 'AbortError' || msg.includes('timeout');
  const isNet = msg.includes('network') || msg.includes('connection') || msg.includes('fetch');
  const isSocket = msg.includes('und_err_socket') || msg.includes('other side closed');
  return isAbort || isNet || isSocket;
}

/** Heuristics for retryable statuses */
function isRetryableStatus(status: number): boolean {
  return status >= 500 || status === 408 || status === 429;
}

/** Test database/backend connectivity with simple health check */
async function testDatabaseConnectivity(): Promise<DatabaseConnectivityResult> {
  const start = Date.now();
  try {
    // Simple health check using direct fetch
    const backendUrl = process.env.KAREN_BACKEND_URL || process.env.NEXT_PUBLIC_KAREN_BACKEND_URL || 'http://localhost:8000';
    const response = await fetch(`${backendUrl}/health`, { 
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      signal: AbortSignal.timeout(5000)
    });
    const responseTime = Date.now() - start;

    if (response.ok) {
      return {
        isConnected: true,
        responseTime,
        timestamp: new Date(),
      };
    }

    return {
      isConnected: false,
      responseTime,
      error: `Backend health check failed with status ${response.status}`,
      timestamp: new Date(),
    };
  } catch (error: Error) {
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

    let result: {
      data: unknown;
      statusCode?: number;
      retryCount?: number;
    };

    try {
      // Simple direct backend request
      const backendUrl = process.env.KAREN_BACKEND_URL || process.env.NEXT_PUBLIC_KAREN_BACKEND_URL || 'http://localhost:8000';
      const response = await fetch(`${backendUrl}/api/auth/validate-session`, {
        method: 'GET',
        headers,
        signal: AbortSignal.timeout(timeoutConfig.sessionValidation)
      });
      
      const data = await response.json();
      result = {
        data,
        statusCode: response.status,
        retryCount: 0
      };
    } catch (error) {
      const totalResponseTime = Date.now() - startTime;
      const normalized = normalizeError(error);

      let errorType: 'timeout' | 'network' | 'credentials' | 'database' | 'server' = 'server';
      let statusCode = 502;
      let retryable = true;

      // Simple error mapping
      if (normalized.name === 'AbortError' || normalized.message.toLowerCase().includes('timeout')) {
        errorType = 'timeout';
        statusCode = 504;
      } else if (normalized.message.toLowerCase().includes('fetch') || normalized.message.toLowerCase().includes('network')) {
        errorType = 'network';
        statusCode = 502;
      } else if (normalized.status === 401 || normalized.status === 403) {
        errorType = 'credentials';
        statusCode = normalized.status;
        retryable = false;
      }

      if (retryable) {
        retryable = isRetryableStatus(statusCode) || isRetryableError(error);
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
  } catch (_error) {
    const totalResponseTime = Date.now() - startTime;
    const databaseConnectivity = await testDatabaseConnectivity();

      console.error('Session validation request failed', error);

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
