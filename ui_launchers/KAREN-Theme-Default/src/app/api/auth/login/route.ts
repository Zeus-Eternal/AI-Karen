/**
 * Streamlined Login API
 *
 * Clean, secure authentication without over-complication.
 * Proxies to backend with proper error handling and security.
 */

import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.KAREN_BACKEND_URL || 'http://localhost:8000';
const TIMEOUT_MS = 15000; // 15 seconds
const MAX_RETRIES = 2;

interface LoginRequest {
  email: string;
  password: string;
  totp_code?: string;
  remember_me?: boolean;
}

interface LoginResponse {
  access_token: string;
  refresh_token?: string;
  user: {
    user_id: string;
    email: string;
    full_name?: string;
    role: string;
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

  // Attempt login with backend
  let lastError: Error | null = null;
  for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS);

      const response = await fetch(`${BACKEND_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify(body),
        signal: controller.signal,
      });

      clearTimeout(timeout);

      // Parse response
      const data = await response.json();
      const responseTime = Date.now() - startTime;

      // Handle auth errors
      if (!response.ok) {
        console.error('[LOGIN] Auth failed:', {
          status: response.status,
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

      // Success! Set cookies and return
      console.log('[LOGIN] Success:', {
        email: body.email,
        responseTime,
        hasToken: !!data.access_token,
      });

      const result = NextResponse.json(data as LoginResponse, { status: 200 });

      // Set auth cookie if token provided
      if (data.access_token) {
        const maxAge = body.remember_me ? 30 * 24 * 60 * 60 : 24 * 60 * 60; // 30 days or 1 day
        result.cookies.set('auth_token', data.access_token, {
          httpOnly: true,
          secure: process.env.NODE_ENV === 'production',
          sameSite: 'lax',
          maxAge,
          path: '/',
        });
      }

      // Set refresh token cookie if provided
      if (data.refresh_token) {
        result.cookies.set('refresh_token', data.refresh_token, {
          httpOnly: true,
          secure: process.env.NODE_ENV === 'production',
          sameSite: 'lax',
          maxAge: 30 * 24 * 60 * 60, // 30 days
          path: '/',
        });
      }

      return result;
    } catch (error) {
      lastError = error as Error;

      // Retry on network errors
      if (attempt < MAX_RETRIES - 1) {
        await new Promise(resolve => setTimeout(resolve, 1000 * (attempt + 1)));
        continue;
      }
    }
  }

  // All retries failed
  const responseTime = Date.now() - startTime;
  console.error('[LOGIN] All retries failed:', {
    error: lastError?.message,
    responseTime,
  });

  return NextResponse.json(
    {
      error: lastError?.name === 'AbortError'
        ? 'Login request timed out'
        : 'Unable to connect to authentication server',
      responseTime,
    },
    { status: 503 }
  );
}
