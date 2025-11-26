/**
 * Streamlined Login API
 *
 * Clean, secure authentication without over-complication.
 * Proxies to backend with proper error handling and security.
 */

import { NextRequest, NextResponse } from 'next/server';

// Explicitly set dynamic to auto for static export compatibility
export const dynamic = 'auto';

const TIMEOUT_MS = 15000; // 15 seconds
const MAX_RETRIES = 2;
const SESSION_COOKIE_NAME = 'kari_session';

type HeadersWithGetAll = Headers & { getAll?: (name: string) => string[] };

function normalizeEndpoint(value: string): string {
  return value.replace(/\/+$/, '');
}

function getBackendEndpoints(): string[] {
  const primary =
    process.env.KAREN_BACKEND_URL ||
    process.env.NEXT_PUBLIC_KAREN_BACKEND_URL ||
    'http://localhost:8000';
  const fallbackRaw = process.env.KAREN_FALLBACK_BACKEND_URLS || '';
  const fallbacks = fallbackRaw
    .split(',')
    .map((url) => url.trim())
    .filter(Boolean);

  const candidates = [primary, ...fallbacks].map(normalizeEndpoint);
  return Array.from(new Set(candidates));
}

interface LoginRequest {
  email: string;
  password: string;
  totp_code?: string;
  remember_me?: boolean;
}

interface LoginResponse {
  access_token: string;
  refresh_token?: string;
  permissions?: string[];
  user: {
    user_id: string;
    email: string;
    full_name?: string;
    role: string;
    roles?: string[];
    permissions?: string[];
  };
  expires_in?: number;
}

export async function POST(request: NextRequest) {
  const startTime = Date.now();

  // Parse request body
  let body: LoginRequest;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      { error: 'Invalid request body' },
      { status: 400 }
    );
  }

  // Validate required fields
  if (!body.email || !body.password) {
    return NextResponse.json(
      { error: 'Email and password are required' },
      { status: 400 }
    );
  }

  const endpoints = getBackendEndpoints();
  let lastFailure: { endpoint: string; error: unknown; attempt: number } | null = null;

  for (const endpoint of endpoints) {
    for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS);

      try {
        const response = await fetch(`${endpoint}/api/auth/login`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
          body: JSON.stringify(body),
          signal: controller.signal,
        });

        clearTimeout(timeout);

        const data = await response.json();
        const responseTime = Date.now() - startTime;

        if (!response.ok) {
          console.error('[LOGIN] Auth failed:', {
            status: response.status,
            endpoint,
            attempt: attempt + 1,
            error: data.error || data.detail,
            responseTime,
          });

          return NextResponse.json(
            {
              error: data.error || data.detail || 'Login failed',
              responseTime,
            },
            { status: response.status }
          );
        }

        console.log('[LOGIN] Success:', {
          email: body.email,
          endpoint,
          responseTime,
          hasToken: !!data.access_token,
        });

        const result = NextResponse.json(data as LoginResponse, { status: 200 });
        appendBackendCookies(response, result);

        if (data.access_token) {
          const maxAge = body.remember_me ? 30 * 24 * 60 * 60 : 24 * 60 * 60;
          const cookieOptions = {
            httpOnly: true,
            secure: process.env.NODE_ENV === 'production',
            sameSite: 'lax' as const,
            maxAge,
            path: '/',
          };
          result.cookies.set('auth_token', data.access_token, cookieOptions);
          result.cookies.set(SESSION_COOKIE_NAME, data.access_token, cookieOptions);
          result.cookies.set('session_token', data.access_token, cookieOptions);
        }

        if (data.refresh_token) {
          result.cookies.set('refresh_token', data.refresh_token, {
            httpOnly: true,
            secure: process.env.NODE_ENV === 'production',
            sameSite: 'lax',
            maxAge: 30 * 24 * 60 * 60,
            path: '/',
          });
        }

        return result;
      } catch (error) {
        lastFailure = {
          endpoint,
          error,
          attempt: attempt + 1,
        };

        console.warn('[LOGIN] Endpoint request failed:', {
          endpoint,
          attempt: attempt + 1,
          error: (error as Error).message,
        });

        if (attempt < MAX_RETRIES - 1) {
          await new Promise((resolve) => setTimeout(resolve, 1000 * (attempt + 1)));
          continue;
        }
      } finally {
        clearTimeout(timeout);
      }
    }
  }

  const responseTime = Date.now() - startTime;
  const lastFailureEntry = lastFailure;
  console.error('[LOGIN] All backend endpoints failed:', {
    lastEndpoint: lastFailureEntry?.endpoint,
    attempt: lastFailureEntry?.attempt,
    error:
      lastFailureEntry && lastFailureEntry.error instanceof Error
        ? lastFailureEntry.error.message
        : lastFailureEntry?.error,
    responseTime,
  });

  const lastError = lastFailureEntry ? lastFailureEntry.error : undefined;
  const timedOut = lastError instanceof Error && lastError.name === 'AbortError';
  return NextResponse.json(
    {
      error: timedOut ? 'Login request timed out' : 'Unable to connect to authentication server',
      responseTime,
    },
    { status: 503 }
  );
}

function appendBackendCookies(backendResponse: Response, nextResponse: NextResponse) {
  const headersWithGetAll = backendResponse.headers as HeadersWithGetAll;
  const getAll = headersWithGetAll.getAll?.bind(backendResponse.headers);
  const cookies: string[] = getAll ? getAll('set-cookie') ?? [] : [];
  if (cookies.length === 0) {
    const single = backendResponse.headers.get('set-cookie');
    if (single) {
      cookies.push(single);
    }
  }

  for (const cookie of cookies) {
    if (!cookie) continue;
    try {
      nextResponse.headers.append('Set-Cookie', cookie);
    } catch {
      // ignore invalid cookie strings
    }
  }
}
