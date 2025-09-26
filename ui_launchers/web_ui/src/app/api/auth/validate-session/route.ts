import { NextRequest, NextResponse } from 'next/server';

// Use the correct backend URL from environment variables
const BACKEND_URL = process.env.KAREN_BACKEND_URL || process.env.NEXT_PUBLIC_KAREN_BACKEND_URL || 'http://127.0.0.1:8000';
const AUTH_TIMEOUT_MS = Number(process.env.NEXT_PUBLIC_AUTH_PROXY_TIMEOUT_MS || process.env.KAREN_AUTH_PROXY_TIMEOUT_MS || 30000);

export async function GET(request: NextRequest) {
  try {
    // Forward the request to the backend with timeout + transient retry
    const base = BACKEND_URL.replace(/\/+$/, '');
    let url = `${base}/api/auth/me`;
    
    // Get Authorization header from the request
    const authHeader = request.headers.get('authorization');
    const headers: Record<string, string> = {
      'Accept': 'application/json',
      'Connection': 'keep-alive',
    };
    
    if (authHeader) {
      headers['Authorization'] = authHeader;
    }

    const maxAttempts = 2;
    let response: Response | null = null;
    let lastErr: any = null;
    
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), AUTH_TIMEOUT_MS);
      
      try {
        response = await fetch(url, {
          method: 'GET',
          headers,
          signal: controller.signal,
          // @ts-ignore Node/undici hints
          keepalive: true,
          cache: 'no-store',
        });
        clearTimeout(timeout);
        lastErr = null;
        break;
      } catch (err: any) {
        clearTimeout(timeout);
        lastErr = err;
        const msg = String(err?.message || err);
        const isAbort = err?.name === 'AbortError';
        const isSocket = msg.includes('UND_ERR_SOCKET') || msg.includes('other side closed');
        if (attempt < maxAttempts && (isAbort || isSocket)) {
          // small backoff then retry
          await new Promise(res => setTimeout(res, 300));
          continue;
        }
        break;
      }
    }
    
    if (!response) {
      console.error('Validate session proxy fatal error:', lastErr);
      return NextResponse.json({ valid: false, error: 'Validation request failed' }, { status: 502 });
    }

    const contentType = response.headers.get('content-type') || '';
    let data: any = {};
    if (contentType.includes('application/json')) {
      try { data = await response.json(); } catch { data = {}; }
    } else {
      try { data = await response.text(); } catch { data = ''; }
      if (typeof data === 'string' && response.ok) {
        data = { message: data };
      }
    }

    if (!response.ok) {
      return NextResponse.json(
        typeof data === 'string' ? { valid: false, error: data } : { valid: false, ...data },
        { status: response.status }
      );
    }
    
    // Transform the /me response to match validate-session format
    if (data && data.authenticated) {
      return NextResponse.json({
        valid: true,
        user: {
          user_id: data.user_id,
          email: data.email,
          full_name: data.full_name,
          roles: data.roles,
          tenant_id: data.tenant_id || 'default'
        }
      });
    } else {
      return NextResponse.json({ valid: false });
    }
    
  } catch (error) {
    console.error('Validate session proxy error:', error);
    return NextResponse.json(
      { valid: false, error: 'Internal server error' },
      { status: 500 }
    );
  }
}
