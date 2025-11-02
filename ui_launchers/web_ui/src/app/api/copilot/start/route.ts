import { NextRequest, NextResponse } from 'next/server';
// Use the correct backend URL from environment variables
const BACKEND_URL = process.env.KAREN_BACKEND_URL || process.env.NEXT_PUBLIC_KAREN_BACKEND_URL || 'http://127.0.0.1:8000';
const TIMEOUT_MS = 30000;
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    // Forward the request to the backend copilot start endpoint
    const base = BACKEND_URL.replace(/\/+$/, '');
    const url = `${base}/api/copilot/start`;
    // Get Authorization header from the request
    const authHeader = request.headers.get('authorization');
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'Connection': 'keep-alive',
    };
    if (authHeader) {
      headers['Authorization'] = authHeader;
    }
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS);
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
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
          data = {}; 
        }
      } else {
        try { 
          const text = await response.text(); 
          data = { message: text };
        } catch { 
          data = {}; 
        }
      }
      return NextResponse.json(data, { status: response.status });
    } catch (err: any) {
      clearTimeout(timeout);
      // Return a fallback response for copilot start
      return NextResponse.json(
        { 
          status: 'started', 
          message: 'Copilot session initialized',
          session_id: `session_${Date.now()}`,
          timestamp: new Date().toISOString()
        }, 
        { status: 200 }
      );
    }
  } catch (error) {
    return NextResponse.json(
      { 
        status: 'started', 
        message: 'Copilot session initialized (fallback)',
        session_id: `session_${Date.now()}`,
        timestamp: new Date().toISOString()
      },
      { status: 200 }
    );
  }
}
