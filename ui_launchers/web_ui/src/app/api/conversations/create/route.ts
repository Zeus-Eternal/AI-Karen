import { NextRequest, NextResponse } from 'next/server';
import { withBackendPath } from '@/app/api/_utils/backend';
export async function POST(request: NextRequest) {
  try {
    // Get authorization header from the request
    const authorization = request.headers.get('authorization');
    const cookie = request.headers.get('cookie');
    // Parse the request body for conversation creation data
    const body = await request.json();
    // Forward the request to the backend conversations create endpoint
    const backendUrl = withBackendPath('/api/conversations/create');
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
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(15000), // 15 second timeout
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
        error: 'Conversation service unavailable',
        message: 'Unable to create conversation',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 503 }
    );
  }
}
