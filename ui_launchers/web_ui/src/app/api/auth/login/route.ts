import { NextRequest, NextResponse } from 'next/server';

import { getBackendCandidates, withBackendPath } from '@/app/api/_utils/backend';

const BACKEND_BASES = getBackendCandidates();
const AUTH_TIMEOUT_MS = Number(process.env.NEXT_PUBLIC_AUTH_PROXY_TIMEOUT_MS || process.env.KAREN_AUTH_PROXY_TIMEOUT_MS || 30000);

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Forward the request to the backend with timeout + transient retry
    // Try multiple backend base URLs to survive Docker/host differences
    const bases = BACKEND_BASES;
    let url = '';
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
        url = withBackendPath('/api/auth/login', base);
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
          // Fallback to simple-auth mount if API path not found
          if (!response.ok && (response.status === 404 || response.status === 405)) {
            const controller2 = new AbortController();
            const timeout2 = setTimeout(() => controller2.abort(), AUTH_TIMEOUT_MS);
            response = await fetch(withBackendPath('/auth/login', base), {
              method: 'POST',
              headers,
              body: JSON.stringify(body),
              signal: controller2.signal,
              // @ts-ignore Node/undici hints
              keepalive: true,
              cache: 'no-store',
            });
            clearTimeout(timeout2);
          }

          if (response.ok) break;

          // On server errors, try dev-login as final fallback in dev
          if (!response.ok && response.status >= 500) {
            const enableDevLogin = process.env.NODE_ENV !== 'production';
            if (enableDevLogin) {
              const controller3 = new AbortController();
              const timeout3 = setTimeout(() => controller3.abort(), AUTH_TIMEOUT_MS);
              try {
                const devResp = await fetch(withBackendPath('/api/auth/dev-login', base), {
                  method: 'POST',
                  headers,
                  body: JSON.stringify({}),
                  signal: controller3.signal,
                  keepalive: true as any,
                  cache: 'no-store',
                });
                clearTimeout(timeout3);
                if (devResp.ok) {
                  response = devResp;
                  break;
                }
              } catch {}
            }
          }

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
          // Try next base URL
          continue;
        }
      }
      if (response?.ok) break;
    }
    if (!response) {
      console.error('Login proxy fatal error:', lastErr);
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
      // Forward cookie(s) from backend to client
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
    console.error('Login proxy error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
