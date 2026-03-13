/**
 * Streamlined Logout API
 *
 * Clears session and auth tokens securely.
 */

import { NextRequest, NextResponse } from 'next/server';

const getBackendUrl = (): string => {
  const isProduction = process.env.NODE_ENV === 'production';
  return isProduction
    ? process.env.NEXT_PUBLIC_KAREN_BACKEND_URL ||
      process.env.KAREN_BACKEND_URL ||
      'https://api.yourdomain.com' // Production fallback
    : process.env.KAREN_BACKEND_URL ||
      process.env.NEXT_PUBLIC_KAREN_BACKEND_URL ||
      'http://localhost:8000';
};

const BACKEND_URL = getBackendUrl();

export async function POST(request: NextRequest) {
  try {
    // Call backend logout
    await fetch(`${BACKEND_URL}/api/auth/logout`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Cookie': request.headers.get('cookie') || '',
      },
      signal: AbortSignal.timeout(5000),
    });

    // Clear all auth cookies
    const result = NextResponse.json(
      { success: true, message: 'Logged out successfully' },
      { status: 200 }
    );

    // Clear auth cookies
    const isProduction = process.env.NODE_ENV === 'production';
    const cookieOptions = {
      httpOnly: true,
      secure: isProduction,
      sameSite: 'lax' as const,
      maxAge: 0,
      path: '/',
      domain: isProduction ? '.yourdomain.com' : undefined,
    };

    result.cookies.set('auth_token', '', cookieOptions);
    result.cookies.set('refresh_token', '', cookieOptions);
    result.cookies.set('kari_session', '', cookieOptions);
    result.cookies.set('session_token', '', cookieOptions);

    return result;
  } catch (error) {
    console.error('[LOGOUT] Error:', error);

    // Still clear cookies even if backend fails
    const result = NextResponse.json(
      { success: true, message: 'Logged out (local)' },
      { status: 200 }
    );

    const cookieOptions = { maxAge: 0, path: '/' };
    result.cookies.set('auth_token', '', cookieOptions);
    result.cookies.set('refresh_token', '', cookieOptions);
    result.cookies.set('kari_session', '', cookieOptions);
    result.cookies.set('session_token', '', cookieOptions);

    return result;
  }
}
