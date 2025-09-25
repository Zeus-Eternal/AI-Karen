import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.KAREN_BACKEND_URL || 'http://ai-karen-api:8000';
const HEALTH_TIMEOUT_MS = 10000; // Longer timeout for retry operations

export async function POST(request: NextRequest) {
  try {
    // Forward the request to the backend degraded-mode recovery endpoint
    const base = BACKEND_URL.replace(/\/+$/, '');
    const url = `${base}/api/health/degraded-mode/recover`;
    
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
          data = { status: text || 'ok', message: 'Retry full mode initiated' };
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
          error: 'Backend unreachable for retry-full-mode',
          message: 'Could not connect to backend to retry full mode',
          timestamp: new Date().toISOString()
        }, 
        { status: 503 }
      );
    }
    
  } catch (error) {
    console.error('Retry full mode proxy error:', error);
    return NextResponse.json(
      { 
        status: 'error', 
        error: 'Retry full mode failed',
        message: 'Internal server error during retry full mode operation',
        timestamp: new Date().toISOString()
      },
      { status: 500 }
    );
  }
}

// Also support GET method in case it's needed
export async function GET(request: NextRequest) {
  return NextResponse.json(
    { 
      status: 'info',
      message: 'Retry full mode endpoint - use POST method',
      timestamp: new Date().toISOString()
    },
    { status: 405 }
  );
}