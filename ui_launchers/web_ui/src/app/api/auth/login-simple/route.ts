import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.KAREN_BACKEND_URL || process.env.API_BASE_URL || 'http://127.0.0.1:8000';
const AUTH_TIMEOUT_MS = Number(process.env.NEXT_PUBLIC_AUTH_PROXY_TIMEOUT_MS || process.env.KAREN_AUTH_PROXY_TIMEOUT_MS || 30000);

export async function POST(request: NextRequest) {
  // Gate dev login behind explicit flag
  const devEnabled = (process.env.NEXT_PUBLIC_ENABLE_DEV_LOGIN || '').toLowerCase() === 'true';
  if (!devEnabled) {
    return NextResponse.json({ error: 'Dev login is disabled' }, { status: 410 });
  }
  try {
    const body = await request.json();

    // Backend exposes this as /api/login-simple (no /auth prefix)
    const url = `${BACKEND_URL.replace(/\/+$/, '')}/api/login-simple`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'Connection': 'keep-alive',
    };

    const maxAttempts = 2;
    let response: Response | null = null;
    let lastErr: any = null;
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), AUTH_TIMEOUT_MS);
      try {
        response = await fetch(url, {
          method: 'POST',
          headers,
          body: JSON.stringify(body),
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
          await new Promise(res => setTimeout(res, 300));
          continue;
        }
        break;
      }
    }

    if (!response) {
      console.error('Login-simple proxy fatal error:', lastErr);
      return NextResponse.json({ error: 'Login request failed' }, { status: 502 });
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
        typeof data === 'string' ? { error: data } : data,
        { status: response.status }
      );
    }

    const nextResponse = NextResponse.json(data);
    const setCookieHeader = response.headers.get('set-cookie');
    if (setCookieHeader) {
      nextResponse.headers.set('Set-Cookie', setCookieHeader);
    }
    return nextResponse;
  } catch (error) {
    console.error('Login-simple proxy error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
