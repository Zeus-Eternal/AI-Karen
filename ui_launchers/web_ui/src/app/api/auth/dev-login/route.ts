import { NextRequest, NextResponse } from 'next/server';

import { makeBackendRequest } from '@/app/api/_utils/backend';

export async function POST(request: NextRequest) {
  // Only allow dev login in development environment
  if (process.env.NODE_ENV === 'production') {
    return NextResponse.json(
      { error: 'Dev login is not available in production' },
      { status: 403 }
    );
  }

  try {
    const body = await request.json();
    
    // Forward the request to the backend dev login endpoint
    const result = await makeBackendRequest('/api/auth/dev-login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const data = result.data;
    
    // Create the response
    const nextResponse = NextResponse.json(data);
    
    // Set auth token cookie
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
    console.error('Dev login proxy error:', error);
    return NextResponse.json(
      { error: 'Dev login failed' },
      { status: 500 }
    );
  }
}