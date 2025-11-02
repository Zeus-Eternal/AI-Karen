import { NextRequest, NextResponse } from 'next/server';
import { withBackendPath } from '@/app/api/_utils/backend';
export async function POST(request: NextRequest) {
  try {
    // Get authorization header from the request
    const authorization = request.headers.get('authorization');
    const cookie = request.headers.get('cookie');
    // Forward the logout request to the backend
    const backendUrl = withBackendPath('/api/auth/logout');
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    // Forward auth headers if present
    if (authorization) {
      headers['Authorization'] = authorization;
    }
    if (cookie) {
      headers['Cookie'] = cookie;
    }
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers,
      signal: AbortSignal.timeout(10000), // 10 second timeout
    });
    const data = await response.json();
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
    // Return structured error response
    return NextResponse.json(
      { 
        error: 'Authentication service unavailable',
        message: 'Unable to process logout request',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 503 }
    );
  }
}
