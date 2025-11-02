import { NextRequest, NextResponse } from 'next/server';
import { withBackendPath } from '@/app/api/_utils/backend';
export async function POST(request: NextRequest) {
  try {
    // Parse the registration data from the request body
    const body = await request.json();
    // Forward the registration request to the backend
    const backendUrl = withBackendPath('/api/auth/register');
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(15000), // 15 second timeout for registration
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
        error: 'Registration service unavailable',
        message: 'Unable to process registration request',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 503 }
    );
  }
}
