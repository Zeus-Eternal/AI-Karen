import { NextRequest, NextResponse } from 'next/server';

import { getBackendCandidates, withBackendPath } from '@/app/api/_utils/backend';

const BACKEND_BASES = getBackendCandidates();
const AUTH_TIMEOUT_MS = Number(process.env.NEXT_PUBLIC_AUTH_PROXY_TIMEOUT_MS || process.env.KAREN_AUTH_PROXY_TIMEOUT_MS || 30000);

export async function GET(request: NextRequest) {
  try {
    const DEBUG_AUTH = Boolean(process.env.DEBUG_AUTH || process.env.NEXT_PUBLIC_DEBUG_AUTH);
    // Forward the request to the backend with timeout + transient retry
    const authHeader = request.headers.get('authorization');
    const cookieHeader = request.headers.get('cookie');

    if (DEBUG_AUTH) {
      console.log('Validate proxy incoming Authorization:', authHeader);
      console.log('Validate proxy incoming Cookie:', cookieHeader);
    }

    const headers: Record<string, string> = {
      Accept: 'application/json',
      Connection: 'keep-alive',
    };

    if (authHeader) {
      headers['Authorization'] = authHeader;
    }
    if (cookieHeader) {
      headers['Cookie'] = cookieHeader;
    }

    const bases = BACKEND_BASES;
    const maxAttempts = 2;
    let response: Response | null = null;
    let lastErr: any = null;

    for (const base of bases) {
      for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        const url = withBackendPath('/api/auth/me', base);
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
      if (response) {
        break;
      }
    }

    if (!response) {
      console.error('Validate session proxy fatal error:', lastErr);
      return NextResponse.json({ valid: false, error: 'Validation request failed' }, { status: 502 });
    }

  // Collect Set-Cookie headers if present. Prefer runtime getAll if available.
    const setCookieHeaders: string[] = [];
    try {
      const headersAny = response.headers as any;
      if (typeof headersAny.entries === 'function') {
        for (const [k, v] of headersAny.entries()) {
          if (String(k).toLowerCase() === 'set-cookie' && v) setCookieHeaders.push(String(v));
        }
      }
      const single = response.headers.get('set-cookie');
      if (single && !setCookieHeaders.includes(single)) setCookieHeaders.push(single);
    } catch (e) {
      // ignore
    }
  if (DEBUG_AUTH) console.log('Validate proxy: backend Set-Cookie headers:', setCookieHeaders);
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
      const errorPayload = typeof data === 'string' ? { valid: false, error: data } : { valid: false, ...data };
      const nextResponse = NextResponse.json(errorPayload, { status: response.status });
      // Forward raw Set-Cookie headers so browser stores cookies
      for (const raw of setCookieHeaders) {
        if (!raw) continue;
        try {
          if (DEBUG_AUTH) console.log('Validate proxy forwarding Set-Cookie raw:', raw);
          nextResponse.headers.append('Set-Cookie', raw);
        } catch (e) {
          if (DEBUG_AUTH) console.log('Validate proxy failed to append Set-Cookie header', e);
        }
      }
      return nextResponse;
    }

    // Transform the /me response to match validate-session format
    if (data && data.authenticated) {
      const nextResponse = NextResponse.json({
        valid: true,
        user: {
          user_id: data.user_id,
          email: data.email,
          full_name: data.full_name,
          roles: data.roles,
          tenant_id: data.tenant_id || 'default'
        }
      });
      for (const raw of setCookieHeaders) {
        if (!raw) continue;
        try {
          if (DEBUG_AUTH) console.log('Validate proxy forwarding Set-Cookie raw:', raw);
          nextResponse.headers.append('Set-Cookie', raw);
        } catch (e) {
          if (DEBUG_AUTH) console.log('Validate proxy failed to append Set-Cookie header', e);
        }
      }
      return nextResponse;
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
