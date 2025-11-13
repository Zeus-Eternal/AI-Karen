/**
 * Streamlined Session Validation API
 *
 * Validates user session with backend.
 */

import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.KAREN_BACKEND_URL || 'http://localhost:8000';
const TIMEOUT_MS = 10000; //10 seconds

export const dynamic = 'force-dynamic';
export const revalidate = 0;

export async function GET(request: NextRequest) {
  try {
    // Forward cookies to backend
    const cookieHeader = request.headers.get('cookie');

    const response = await fetch(`${BACKEND_URL}/api/auth/validate-session`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...(cookieHeader && { 'Cookie': cookieHeader }),
      },
      signal: AbortSignal.timeout(TIMEOUT_MS),
      cache: 'no-store',
    });

    const data = await response.json();

    // Return validation result
    return NextResponse.json(data, {
      status: response.status,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
      },
    });
  } catch (error) {
    const isTimeout =
      error instanceof Error &&
      (error.name === 'AbortError' || error.message.includes('timeout'));

    console.error('[SESSION] Validation failed:', {
      error: error instanceof Error ? error.message : String(error),
      isTimeout,
    });

    return NextResponse.json(
      {
        valid: false,
        user: null,
        error: isTimeout
          ? 'Session validation timed out'
          : 'Unable to validate session',
      },
      { status: 503 }
    );
  }
}
