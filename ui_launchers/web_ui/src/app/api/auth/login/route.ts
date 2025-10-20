import { NextRequest, NextResponse } from 'next/server';

import { getBackendCandidates, withBackendPath } from '@/app/api/_utils/backend';
import { isDevLoginEnabled, isSimpleAuthEnabled } from '@/lib/auth/env';

const BACKEND_BASES = getBackendCandidates();
const AUTH_TIMEOUT_MS = Number(process.env.NEXT_PUBLIC_AUTH_PROXY_TIMEOUT_MS || process.env.KAREN_AUTH_PROXY_TIMEOUT_MS || 30000);
const SIMPLE_AUTH_ENABLED = isSimpleAuthEnabled();
const DEV_LOGIN_ENABLED = isDevLoginEnabled();

export async function POST(request: NextRequest) {
  try {
  const DEBUG_AUTH = Boolean(process.env.DEBUG_AUTH || process.env.NEXT_PUBLIC_DEBUG_AUTH);
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
            if (SIMPLE_AUTH_ENABLED) {
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
            } else {
              console.warn('Login proxy: Simple auth fallback disabled. Skipping /auth/login retry.');
            }
          }

          if (response.ok) break;

          // On server errors, try dev-login as final fallback in dev
          if (!response.ok && response.status >= 500 && DEV_LOGIN_ENABLED) {
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
          } else if (!response.ok && response.status >= 500 && !DEV_LOGIN_ENABLED) {
            console.warn('Login proxy: Dev login fallback disabled.');
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
    
    // Forward any Set-Cookie headers from the backend. Node/undici may expose
    // multiple Set-Cookie headers; prefer reading them all if available.
  try {
      const setCookieHeaders: string[] = [];
      try {
        // Prefer iterating entries (works in Node/fetch runtimes)
        const headersAny = response.headers as any;
        if (typeof headersAny.entries === 'function') {
          for (const [k, v] of headersAny.entries()) {
            if (String(k).toLowerCase() === 'set-cookie' && v) setCookieHeaders.push(String(v));
          }
        }
        // Fallback to single header
        const single = response.headers.get('set-cookie');
        if (single && !setCookieHeaders.includes(single)) setCookieHeaders.push(single);
      } catch (e) {
        // ignore; leave setCookieHeaders empty
      }

  if (DEBUG_AUTH) console.log('Login proxy: backend Set-Cookie headers:', setCookieHeaders);
  for (const raw of setCookieHeaders) {
        if (!raw) continue;
        // Parse simple cookie string into name/value and attributes.
        const parts = raw.split(';').map(p => p.trim());
        const [nameValue, ...attrs] = parts;
        const eq = nameValue.indexOf('=');
        if (eq === -1) continue;
        const name = nameValue.substring(0, eq);
        const value = nameValue.substring(eq + 1);

        const cookieOptions: any = { path: '/' };
        for (const attr of attrs) {
          const [k, v] = attr.split('=').map(s => s.trim());
          const key = k.toLowerCase();
          if (key === 'httponly') cookieOptions.httpOnly = true;
          else if (key === 'secure') cookieOptions.secure = true;
          else if (key === 'samesite') cookieOptions.sameSite = (v || '').toLowerCase();
          else if (key === 'path') cookieOptions.path = v || '/';
          else if (key === 'max-age') cookieOptions.maxAge = Number(v);
          else if (key === 'expires') {
            const date = new Date(v);
            if (!Number.isNaN(date.getTime())) {
              cookieOptions.expires = date;
            }
          }
        }

        try {
          nextResponse.cookies.set(name, value, cookieOptions);
        } catch (e) {
          // If NextResponse.cookies.set fails for any cookie, fall back to
          // forwarding the raw header to ensure the cookie is sent.
          if (DEBUG_AUTH) console.log('Login proxy: failed to set cookie via NextResponse.cookies.set, appending raw header', name, e);
          nextResponse.headers.append('Set-Cookie', raw);
        }
      }
    } catch (e) {
      // Safe fallback: forward single header if parsing fails
      const single = response.headers.get('set-cookie');
      if (single) nextResponse.headers.set('Set-Cookie', single);
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
