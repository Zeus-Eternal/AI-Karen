import { NextRequest, NextResponse } from 'next/server';

import { 
  makeBackendRequest, 
  getTimeoutConfig, 
  getRetryPolicy 
} from '@/app/api/_utils/backend';
import { isSimpleAuthEnabled } from '@/lib/auth/env';
import { ConnectionError } from '@/lib/connection/connection-manager';

interface ErrorResponse {
  error: string;
  errorType: string;
  retryable: boolean;
  retryAfter?: number;
  responseTime?: number;
  timestamp: string;
}

const timeoutConfig = getTimeoutConfig();
const retryPolicy = getRetryPolicy();

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

export async function POST(request: NextRequest) {
  const startTime = Date.now();
  
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

  try {
    const body = await request.json();
    
    // Forward the request to the backend using enhanced backend utilities
    const headers: Record<string, string> = {
      'X-Request-ID': `simple-auth-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
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
        body: JSON.stringify(body),
      }, connectionOptions);
      
    } catch (error) {
      // Try legacy bypass endpoints as fallback
      try {
        result = await makeBackendRequest('/api/auth/login-bypass', {
          method: 'POST',
          body: JSON.stringify({ email: 'dev@local', password: 'dev' }),
        }, connectionOptions);
      } catch (fallbackError) {
        throw error; // Throw original error if fallback also fails
      }
    }

    const totalResponseTime = Date.now() - startTime;
    const data = result.data;
    
    // Create the response with the data
    const nextResponse = NextResponse.json(data);
    
    // Forward any Set-Cookie headers from the backend
    const setCookieHeader = result.headers.get('set-cookie');
    if (setCookieHeader) {
      nextResponse.headers.set('Set-Cookie', setCookieHeader);
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
    console.error('Login-simple proxy error:', error);
    const totalResponseTime = Date.now() - startTime;
    
    // Extract error information from ConnectionError if available
    let errorType: 'timeout' | 'network' | 'credentials' | 'database' | 'server' = 'server';
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
    
    const errorResponse: ErrorResponse = {
      error: error instanceof Error ? error.message : 'Internal server error',
      errorType,
      retryable,
      responseTime: totalResponseTime,
      timestamp: new Date().toISOString(),
    };
    
    return NextResponse.json(errorResponse, { status: statusCode });
  }
}
