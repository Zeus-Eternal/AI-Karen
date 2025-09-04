import { NextRequest, NextResponse } from 'next/server';

// Development-only authentication bypass
export async function POST(request: NextRequest) {
  // Only allow in development
  if (process.env.NODE_ENV !== 'development') {
    return NextResponse.json({ error: 'Not available in production' }, { status: 403 });
  }

  try {
    // Create a simple development session
    const devSession = {
      access_token: 'dev-token-' + Date.now(),
      refresh_token: 'dev-refresh-' + Date.now(),
      token_type: 'bearer',
      expires_in: 3600,
      user: {
        id: 'dev-user',
        username: 'developer',
        email: 'dev@localhost',
        role: 'admin'
      }
    };

    const response = NextResponse.json(devSession);
    
    // Set development cookies
    response.cookies.set('auth_token', devSession.access_token, {
      httpOnly: true,
      secure: false, // Allow HTTP in development
      sameSite: 'lax',
      maxAge: 3600,
      path: '/'
    });

    response.cookies.set('refresh_token', devSession.refresh_token, {
      httpOnly: true,
      secure: false,
      sameSite: 'lax',
      maxAge: 7 * 24 * 3600, // 7 days
      path: '/'
    });

    return response;
    
  } catch (error) {
    console.error('Dev auth bypass error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}