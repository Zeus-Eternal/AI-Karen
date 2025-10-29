import { NextRequest, NextResponse } from 'next/server';

/**
 * Development Status Endpoint
 * Provides debugging information for development environment
 */

export async function GET(request: NextRequest) {
  // Only available in development
  if (process.env.NODE_ENV !== 'development') {
    return NextResponse.json(
      { error: 'Development status not available in production' },
      { status: 404 }
    );
  }

  try {
    const status = {
      environment: {
        NODE_ENV: process.env.NODE_ENV,
        NEXT_PUBLIC_NODE_ENV: process.env.NEXT_PUBLIC_NODE_ENV,
        development_mode: process.env.NODE_ENV === 'development',
      },
      backend: {
        KAREN_BACKEND_URL: process.env.KAREN_BACKEND_URL,
        NEXT_PUBLIC_KAREN_BACKEND_URL: process.env.NEXT_PUBLIC_KAREN_BACKEND_URL,
        KAREN_BACKEND_PORT: process.env.KAREN_BACKEND_PORT,
        BACKEND_PORT: process.env.BACKEND_PORT,
        API_BASE_URL: process.env.API_BASE_URL,
        NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
      },
      auth: {
        DEBUG_AUTH: process.env.DEBUG_AUTH,
        NEXT_PUBLIC_DEBUG_AUTH: process.env.NEXT_PUBLIC_DEBUG_AUTH,
        SIMPLE_AUTH_ENABLED: process.env.SIMPLE_AUTH_ENABLED,
        NEXT_PUBLIC_SIMPLE_AUTH_ENABLED: process.env.NEXT_PUBLIC_SIMPLE_AUTH_ENABLED,
      },
      debug: {
        NEXT_PUBLIC_DEBUG: process.env.NEXT_PUBLIC_DEBUG,
        NEXT_PUBLIC_DISABLE_MINIFICATION: process.env.NEXT_PUBLIC_DISABLE_MINIFICATION,
        NEXT_TELEMETRY_DISABLED: process.env.NEXT_TELEMETRY_DISABLED,
      },
      server: {
        port: process.env.PORT || '8010',
        host: process.env.HOST || 'localhost',
        timestamp: new Date().toISOString(),
      },
      react: {
        version: '18.3.1', // From package.json
        strict_mode: false, // From next.config.js
        minified: process.env.NODE_ENV === 'production',
      },
    };

    return NextResponse.json(status, { 
      status: 200,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
      },
    });
  } catch (error) {
    console.error('Dev status error:', error);
    return NextResponse.json(
      { error: 'Failed to get development status' },
      { status: 500 }
    );
  }
}