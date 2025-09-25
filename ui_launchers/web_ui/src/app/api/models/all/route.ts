import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.KAREN_BACKEND_URL || 'http://ai-karen-api:8000';

export async function GET(request: NextRequest) {
  try {
    // Get authorization header from the request
    const authorization = request.headers.get('authorization');
    const cookie = request.headers.get('cookie');

    // Get query parameters for filtering, pagination, etc.
    const { searchParams } = new URL(request.url);

    // Forward the request to the backend models all endpoint
    const base = BACKEND_URL.replace(/\/+$/, '');
    const backendUrl = `${base}/api/models/all?${searchParams.toString()}`;

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
      signal: AbortSignal.timeout(20000), // 20 second timeout for large model lists
    });

    const data = await response.json();

    // Return the backend response with appropriate status
    return NextResponse.json(data, { 
      status: response.status,
      headers: {
        'Cache-Control': 'public, max-age=600', // Cache for 10 minutes
        'Pragma': 'cache',
      }
    });

  } catch (error) {
    console.error('Models all error:', error);
    
    // Return structured error response
    return NextResponse.json(
      { 
        error: 'Models service unavailable',
        message: 'Unable to fetch all models',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 503 }
    );
  }
}
