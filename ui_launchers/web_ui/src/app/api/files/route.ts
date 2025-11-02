import { NextRequest, NextResponse } from 'next/server';
import { withBackendPath } from '@/app/api/_utils/backend';
export async function GET(request: NextRequest) {
  try {
    // Get authorization header from the request
    const authorization = request.headers.get('authorization');
    const cookie = request.headers.get('cookie');
    // Get query parameters for pagination, filtering, etc.
    const { searchParams } = new URL(request.url);
    // Forward the request to the backend files endpoint
    const backendUrl = `${withBackendPath('/api/files')}?${searchParams.toString()}`;
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
      method: 'GET',
      headers,
      signal: AbortSignal.timeout(15000), // 15 second timeout
    });
    const data = await response.json();
    // Return the backend response with appropriate status
    return NextResponse.json(data, { 
      status: response.status,
      headers: {
        'Cache-Control': 'private, max-age=300', // Cache for 5 minutes
        'Pragma': 'no-cache',
      }
    });
  } catch (error) {
    // Return structured error response
    return NextResponse.json(
      { 
        error: 'File service unavailable',
        message: 'Unable to fetch files',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 503 }
    );
  }
}
