import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.KAREN_BACKEND_URL || 'http://api:8000';

export async function POST(request: NextRequest) {
  console.log('🔍 DevLogin API: Request received', {
    url: request.url,
    method: request.method,
    headers: Object.fromEntries(request.headers.entries())
  });

  try {
    // Get request body
    const body = await request.json();

    console.log('🔍 DevLogin API: Request body parsed', {
      bodyKeys: Object.keys(body),
      hasUsername: !!body.username,
      hasPassword: !!body.password
    });

    // Forward the request to the backend dev-login endpoint
    const base = BACKEND_URL.replace(/\/+$/, '');
    const backendUrl = `${base}/api/auth/dev-login`;

    console.log('🔍 DevLogin API: Backend URL constructed', {
      backendUrl,
      baseUrl: base
    });

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    // Forward auth headers if present
    const authorization = request.headers.get('authorization');
    if (authorization) {
      headers['Authorization'] = authorization;
      console.log('🔍 DevLogin API: Authorization header found');
    }

    const cookie = request.headers.get('cookie');
    if (cookie) {
      headers['Cookie'] = cookie;
      console.log('🔍 DevLogin API: Cookie header found');
    }

    console.log('🔍 DevLogin API: Attempting backend fetch', {
      backendUrl,
      timeout: 30000,
      headers: Object.keys(headers)
    });

    const response = await fetch(backendUrl, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(30000), // 30 second timeout
    });

    console.log('🔍 DevLogin API: Backend response received', {
      status: response.status,
      statusText: response.statusText,
      headers: Object.fromEntries(response.headers.entries()),
      ok: response.ok,
      url: response.url
    });

    const data = await response.json();

    console.log('🔍 DevLogin API: Backend response data', {
      dataKeys: Object.keys(data),
      hasAccessToken: !!data.access_token,
      hasUser: !!data.user,
      hasError: !!data.error
    });

    // Return the backend response with appropriate status
    return NextResponse.json(data, {
      status: response.status,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      }
    });

  } catch (error) {
    console.error('🔍 DevLogin API: Error', error);
    
    // Return structured error response
    const errorResponse = {
      error: 'Development login service unavailable',
      message: 'Unable to process development login request',
      details: error instanceof Error ? error.message : 'Unknown error'
    };

    console.log('🔍 DevLogin API: Returning error response', errorResponse);
    return NextResponse.json(errorResponse, { status: 503 });
  }
}
