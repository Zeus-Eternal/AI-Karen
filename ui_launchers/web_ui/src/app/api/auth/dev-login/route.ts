import { NextRequest, NextResponse } from "next/server";

/**
 * Development-only login bypass
 * This route provides a simple authentication mechanism for development
 */

export async function POST(request: NextRequest) {
  // Only allow in development
  if (process.env.NODE_ENV !== 'development') {
    return NextResponse.json(
      { error: 'Development login not available in production' },
      { status: 404 }
    );
  }

  try {
    const body = await request.json();
    const { email, password } = body;

    // Simple development authentication
    if (email && password) {
      const response = NextResponse.json({
        access_token: 'dev-token-' + Date.now(),
        token_type: 'Bearer',
        expires_in: 3600,
        user_data: {
          id: 'dev-user-1',
          email: email,
          name: 'Development User',
          roles: ['user', 'admin'],
        },
        databaseConnectivity: {
          isConnected: true,
          responseTime: 10,
          timestamp: new Date(),
        },
        responseTime: 50,
      });

      // Set development auth cookie
      response.cookies.set('auth_token', 'dev-token-' + Date.now(), {
        httpOnly: true,
        sameSite: 'lax',
        secure: false,
        path: '/',
        maxAge: 3600,
      });

      return response;
    }

    return NextResponse.json(
      { error: 'Email and password required' },
      { status: 400 }
    );
  } catch (error) {
    console.error('Dev login error:', error);
    return NextResponse.json(
      { error: 'Development login failed' },
      { status: 500 }
    );
  }
}

export async function GET() {
  return NextResponse.json({
    message: 'Development login endpoint',
    available: process.env.NODE_ENV === 'development',
  });
}