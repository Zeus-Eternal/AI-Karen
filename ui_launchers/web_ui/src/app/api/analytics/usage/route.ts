import { NextRequest, NextResponse } from 'next/server';
import { getBackendCandidates, withBackendPath } from '@/app/api/_utils/backend';
const BACKEND_BASES = getBackendCandidates();
const ANALYTICS_TIMEOUT_MS = Number(
  process.env.NEXT_PUBLIC_ANALYTICS_PROXY_TIMEOUT_MS ||
    process.env.KAREN_ANALYTICS_PROXY_TIMEOUT_MS ||
    process.env.NEXT_PUBLIC_API_PROXY_TIMEOUT_MS ||
    process.env.KAREN_API_PROXY_TIMEOUT_MS ||
    15000
);
export async function GET(request: NextRequest) {
  try {
    const authHeader = request.headers.get('authorization');
    const cookieHeader = request.headers.get('cookie');
    const headers: Record<string, string> = {
      Accept: 'application/json',
      Connection: 'keep-alive',
    };
    if (authHeader) {
      headers.Authorization = authHeader;
    }
    if (cookieHeader) {
      headers.Cookie = cookieHeader;
    }
    const maxAttempts = 2;
    let response: Response | null = null;
    let lastErr: unknown = null;
    for (const base of BACKEND_BASES) {
      for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        const url = withBackendPath('/api/analytics/usage', base);
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), ANALYTICS_TIMEOUT_MS);
        try {
          response = await fetch(url, {
            method: 'GET',
            headers,
            signal: controller.signal,
            // @ts-ignore keepalive supported in runtime
            keepalive: true,
            cache: 'no-store',

          clearTimeout(timeout);
          lastErr = null;
          break;
        } catch (err) {
          clearTimeout(timeout);
          lastErr = err;
          const msg = String((err as Error)?.message ?? err);
          const isAbort = (err as any)?.name === 'AbortError';
          const isSocket = msg.includes('UND_ERR_SOCKET') || msg.includes('other side closed');
          if (attempt < maxAttempts && (isAbort || isSocket)) {
            await new Promise((res) => setTimeout(res, 300));
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
      return NextResponse.json({ error: 'Analytics request failed' }, { status: 502 });
    }
    const contentType = response.headers.get('content-type') ?? '';
    let data: any = {};
    if (contentType.includes('application/json')) {
      try {
        data = await response.json();
      } catch {
        data = {};
      }
    } else {
      try {
        data = await response.text();
      } catch {
        data = '';
      }
      if (typeof data === 'string' && response.ok) {
        data = { message: data };
      }
    }
    if (!response.ok) {
      const payload = typeof data === 'string' ? { error: data } : data;
      return NextResponse.json(payload, { status: response.status });
    }
    const nextResponse = NextResponse.json(data);
    try {
      const setCookieHeaders: string[] = [];
      const headersAny = response.headers as any;
      if (typeof headersAny.entries === 'function') {
        for (const [key, value] of headersAny.entries()) {
          if (String(key).toLowerCase() === 'set-cookie' && value) {
            setCookieHeaders.push(String(value));
          }
        }
      }
      const single = response.headers.get('set-cookie');
      if (single && !setCookieHeaders.includes(single)) {
        setCookieHeaders.push(single);
      }
      for (const raw of setCookieHeaders) {
        nextResponse.headers.append('Set-Cookie', raw);
      }
    } catch {
      const single = response.headers.get('set-cookie');
      if (single) {
        nextResponse.headers.set('Set-Cookie', single);
      }
    }
    return nextResponse;
  } catch (error) {
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
