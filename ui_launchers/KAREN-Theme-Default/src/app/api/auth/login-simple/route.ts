// app/api/auth/login-simple/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { makeBackendRequest, getTimeoutConfig, getRetryPolicy } from '@/app/api/_utils/backend';
import { isSimpleAuthEnabled } from '@/lib/auth/env';
import { ConnectionError } from '@/lib/connection/connection-manager';
import { logger } from '@/lib/logger';

interface ErrorResponse {
  error: string;
  errorType: 'timeout' | 'network' | 'credentials' | 'database' | 'server';
  retryable: boolean;
  retryAfter?: number;
  responseTime?: number;
  timestamp: string;
}

const timeoutConfig = getTimeoutConfig();
const retryPolicy = getRetryPolicy();

export async function POST(request: NextRequest) {
  const startTime = Date.now();

  // Feature gate
  if (!isSimpleAuthEnabled()) {
    const errorResponse: ErrorResponse = {
      error: 'Simple auth is disabled',
      errorType: 'server',
      retryable: false,
      responseTime: Date.now() - startTime,
      timestamp: new Date().toISOString(),
    };
    return NextResponse.json(errorResponse, { status: 404 });
  }

  // Parse JSON body safely
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    const errorResponse: ErrorResponse = {
      error: 'Invalid JSON body',
      errorType: 'server',
      retryable: false,
      responseTime: Date.now() - startTime,
      timestamp: new Date().toISOString(),
    };
    return NextResponse.json(errorResponse, { status: 400 });
  }

  // Optional: basic shape validation (non-fatal if you want pass-through)
  if (typeof body !== 'object' || body == null) {
    const errorResponse: ErrorResponse = {
      error: 'Request body must be a JSON object',
      errorType: 'server',
      retryable: false,
      responseTime: Date.now() - startTime,
      timestamp: new Date().toISOString(),
    };
    return NextResponse.json(errorResponse, { status: 400 });
  }

  const requestId = `simple-auth-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;

  const connectionOptions = {
    timeout: timeoutConfig.authentication,
    retryAttempts: retryPolicy.maxAttempts,
    retryDelay: retryPolicy.baseDelay,
    exponentialBackoff: retryPolicy.jitterEnabled,
    headers: {
      'X-Request-ID': requestId,
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    } as Record<string, string>,
  };

  try {
    // Call backend auth
    const result = await makeBackendRequest(
      '/api/auth/login',
      { method: 'POST', body: JSON.stringify(body) },
      connectionOptions
    );

    const totalResponseTime = Date.now() - startTime;
    const data = result.data;
    const status = result.status ?? 200;

    logger.info('Simple auth proxy success', {
      requestId,
      backendStatus: status,
      responseTime: totalResponseTime,
    });

    // Build response mirroring backend status
    const nextResponse = NextResponse.json(data, {
      status,
      headers: {
        'Cache-Control': 'no-store, max-age=0',
        'X-Proxy-Upstream-Status': String(status),
      },
    });

    // Forward Set-Cookie from backend if present (array or string)
    try {
      const setCookie =
        (result.headers as unknown)?.['set-cookie'] ?? (result.headers as unknown)?.['Set-Cookie'];
      if (setCookie) {
        if (Array.isArray(setCookie)) {
          // Append each cookie header
          setCookie.forEach((c: string) => nextResponse.headers.append('Set-Cookie', c));
        } else if (typeof setCookie === 'string') {
          nextResponse.headers.set('Set-Cookie', setCookie);
        }
      }
    } catch {
      // ignore header forwarding errors
    }

    // Also set our own auth_token cookie for downstream proxies if token provided
    const token = data?.access_token as string | undefined;
    const shouldUseSecureCookies = process.env.NODE_ENV === 'production';

    if (token && token.length > 0) {
      try {
        // Use expires_in if provided; default 24h
        const maxAge =
          typeof data?.expires_in === 'number' ? Math.max(0, Number(data.expires_in)) : 24 * 60 * 60;

        nextResponse.cookies.set('auth_token', token, {
          httpOnly: true,
          sameSite: 'lax',
          secure: shouldUseSecureCookies,
          path: '/',
          maxAge,
        });
      } catch {
        // keep local/dev flexible
      }
    }

    return nextResponse;
  } catch (error: Error) {
    // Typed failure path
    const totalResponseTime = Date.now() - startTime;
    let errorType: ErrorResponse['errorType'] = 'server';
    let statusCode = 500;
    let retryable = true;

    if (error instanceof ConnectionError) {
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

    logger.error('Login-simple proxy error', {
      requestId,
      statusCode,
      errorType,
      retryable,
      message: error?.message || String(error),
    });

    const errorResponse: ErrorResponse = {
      error: error instanceof Error ? error.message : 'Internal server error',
      errorType,
      retryable,
      responseTime: totalResponseTime,
      timestamp: new Date().toISOString(),
    };

    return NextResponse.json(errorResponse, {
      status: statusCode,
      headers: { 'Cache-Control': 'no-store, max-age=0' },
    });
  }
}
