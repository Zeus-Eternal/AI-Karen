import { NextRequest, NextResponse } from 'next/server';

import { withBackendPath } from '@/app/api/_utils/backend';
const HEALTH_TIMEOUT_MS = 10000; // Longer timeout for recovery operations

export async function POST(request: NextRequest) {
  try {
    // Forward the request to the backend degraded-mode recovery endpoint
    const url = withBackendPath('/api/health/degraded-mode/recover');
    
    // Get request body if present
    let body: any = null;
    try {
      const contentType = request.headers.get('content-type') || '';
      if (contentType.includes('application/json')) {
        body = await request.json();
      }
    } catch {
      // No body or invalid JSON, continue without body
    }
    
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), HEALTH_TIMEOUT_MS);
    
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'Connection': 'keep-alive',
          // Forward auth headers if present
          ...(request.headers.get('authorization') && {
            'Authorization': request.headers.get('authorization')!
          }),
        },
        ...(body && { body: JSON.stringify(body) }),
        signal: controller.signal,
        // @ts-ignore Node/undici hints
        keepalive: true,
        cache: 'no-store',
      });
      
      clearTimeout(timeout);
      
      const contentType = response.headers.get('content-type') || '';
      let data: any = {};
      
      if (contentType.includes('application/json')) {
        try { 
          data = await response.json(); 
        } catch { 
          data = { status: 'unknown' }; 
        }
      } else {
        try { 
          const text = await response.text(); 
          data = { status: text || 'ok', message: 'Recovery initiated' };
        } catch { 
          data = { status: 'unknown' }; 
        }
      }

      return NextResponse.json(data, { status: response.status });
      
    } catch (err: any) {
      clearTimeout(timeout);
      
      // Return error response
      return NextResponse.json(
        { 
          status: 'error', 
          error: 'Backend unreachable for recovery',
          message: 'Could not connect to backend to initiate recovery',
          timestamp: new Date().toISOString()
        }, 
        { status: 503 }
      );
    }
    
  } catch (error) {
    console.error('Degraded mode recovery error:', error);
    return NextResponse.json(
      { 
        status: 'error', 
        error: 'Recovery failed',
        message: 'Internal server error during recovery operation',
        timestamp: new Date().toISOString()
      },
      { status: 500 }
    );
  }
}

// Also support GET method to check recovery status
export async function GET(request: NextRequest) {
  return NextResponse.json(
    { 
      status: 'info',
      message: 'Degraded mode recovery endpoint - use POST method to initiate recovery',
      timestamp: new Date().toISOString()
    },
    { status: 405 }
  );
}