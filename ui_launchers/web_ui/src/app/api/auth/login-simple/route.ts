import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.KAREN_BACKEND_URL || 'http://ai-karen-api:8000';
const CANDIDATE_BACKENDS = [
  BACKEND_URL,
  'http://ai-karen-api:8000',
  'http://api:8000',
  'http://localhost:8000',
  'http://127.0.0.1:8000',
].filter(Boolean) as string[];
const AUTH_TIMEOUT_MS = Number(process.env.NEXT_PUBLIC_AUTH_PROXY_TIMEOUT_MS || process.env.KAREN_AUTH_PROXY_TIMEOUT_MS || 30000);

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Forward the request to the backend dev-login endpoint for simple auth
    const bases = Array.from(new Set(CANDIDATE_BACKENDS.map(u => u!.replace(/\/+$/, ''))));
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'Connection': 'keep-alive',
    };

    const maxAttempts = 2;
    let response: Response | null = null;
    let lastErr: any = null;
    
    for (const base of bases) {
      for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), AUTH_TIMEOUT_MS);
        try {
          response = await fetch(`${base}/api/auth/dev-login`, {
            method: 'POST',
            headers,
            body: JSON.stringify({}),
            signal: controller.signal,
            // @ts-ignore Node/undici hints
            keepalive: true,
            cache: 'no-store',
          });
          clearTimeout(timeout);
          lastErr = null;
          if (response.ok) break;

          // Try legacy bypass endpoints as fallback
          const controller2 = new AbortController();
          const timeout2 = setTimeout(() => controller2.abort(), AUTH_TIMEOUT_MS);
          const alt = await fetch(`${base}/api/auth/login-bypass`, {
            method: 'POST',
            headers,
            body: JSON.stringify({ email: 'dev@local', password: 'dev' }),
            signal: controller2.signal,
            // @ts-ignore Node/undici hints
            keepalive: true,
            cache: 'no-store',
          });
          clearTimeout(timeout2);
          if (alt.ok) { response = alt; break; }

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
          continue;
        }
      }
      if (response?.ok) break;
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
    
    // Create the response with the data
    const nextResponse = NextResponse.json(data);
    
    // Forward any Set-Cookie headers from the backend
    const setCookieHeader = response.headers.get('set-cookie');
    if (setCookieHeader) {
      nextResponse.headers.set('Set-Cookie', setCookieHeader);
    }

    // Also set our own auth_token cookie for downstream proxying
    const token = data?.access_token;
    if (typeof token === 'string' && token.length > 0) {
      try {
        nextResponse.cookies.set('auth_token', token, {
          httpOnly: true,
          sameSite: 'lax',
          secure: false, // dev
          path: '/',
          maxAge: data?.expires_in ? Number(data.expires_in) : 24 * 60 * 60,
        });
      } catch {
        // ignore cookie errors in dev
      }
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
