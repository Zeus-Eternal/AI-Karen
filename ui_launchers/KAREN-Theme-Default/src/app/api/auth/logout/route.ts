/**
 * Streamlined Logout API
 *
 * Clears session and auth tokens securely.
 */

import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.KAREN_BACKEND_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    // Call backend logout
    const response = await fetch(`${BACKEND_URL}/api/auth/logout`, {
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
    result.cookies.set('auth_token', '', {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 0,
      path: '/',
    });

    result.cookies.set('refresh_token', '', {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 0,
      path: '/',
    });

    result.cookies.set('session_token', '', {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 0,
      path: '/',
    });

    return result;
  } catch (error) {
    console.error('[LOGOUT] Error:', error);

    // Still clear cookies even if backend fails
    const result = NextResponse.json(
      { success: true, message: 'Logged out (local)' },
      { status: 200 }
    );

    result.cookies.set('auth_token', '', { maxAge: 0, path: '/' });
    result.cookies.set('refresh_token', '', { maxAge: 0, path: '/' });
    result.cookies.set('session_token', '', { maxAge: 0, path: '/' });

    return result;
  }
}
