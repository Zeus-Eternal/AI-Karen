// app/api/analytics/usage/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { getBackendCandidates, withBackendPath } from '@/app/api/_utils/backend';

const BACKEND_BASES = (() => {
  try {
    const c = getBackendCandidates();
    return Array.isArray(c) && c.length > 0 ? c : [process.env.KAREN_BACKEND_URL || 'http://ai-karen-api:8000'];
  } catch {
    return [process.env.KAREN_BACKEND_URL || 'http://ai-karen-api:8000'];
  }
})();

const ANALYTICS_TIMEOUT_MS = Number(
  process.env.NEXT_PUBLIC_ANALYTICS_PROXY_TIMEOUT_MS ??
  process.env.KAREN_ANALYTICS_PROXY_TIMEOUT_MS ??
  process.env.NEXT_PUBLIC_API_PROXY_TIMEOUT_MS ??
  process.env.KAREN_API_PROXY_TIMEOUT_MS ??
  15_000
);

const MAX_ATTEMPTS_PER_BASE = 2;
const RETRY_BACKOFF_MS = 300;

function noStore(init?: ResponseInit): ResponseInit {
  return {
    ...(init || {}),
    headers: {
      ...(init?.headers || {}),
      'Cache-Control': 'no-cache, no-store, must-revalidate',
      'Pragma': 'no-cache',
      'Expires': '0',
      'Content-Type': 'application/json; charset=utf-8',
    },
  };
}

export async function GET(request: NextRequest) {
  try {
    // Forward auth + cookies so usage is scoped to the current principal/session
    const authHeader = request.headers.get('authorization');
    const cookieHeader = request.headers.get('cookie');

    const fwdHeaders: Record<string, string> = {
      Accept: 'application/json',
      Connection: 'keep-alive',
    };
    if (authHeader) fwdHeaders.Authorization = authHeader;
    if (cookieHeader) fwdHeaders.Cookie = cookieHeader;

    let upstreamResponse: Response | null = null;
    let upstreamBaseUsed: string | null = null;
    let lastErr: unknown = null;

    // Multi-base, per-base bounded retries (timeout/UND socket)
    for (const base of BACKEND_BASES) {
      for (let attempt = 1; attempt <= MAX_ATTEMPTS_PER_BASE; attempt++) {
        const url = withBackendPath('/api/analytics/usage', base);
        const controller = new AbortController();
        const t = setTimeout(() => controller.abort(), ANALYTICS_TIMEOUT_MS);

        try {
          const resp = await fetch(url, {
            method: 'GET',
            headers: fwdHeaders,
            signal: controller.signal,
            // keepalive is supported in Node/undici and Edge runtimes
            keepalive: true,
            cache: 'no-store',
          });

          clearTimeout(t);
          upstreamResponse = resp;
          upstreamBaseUsed = base;
          lastErr = null;
          break; // success for this base
        } catch (err) {
          clearTimeout(t);
          lastErr = err;

          const msg = err instanceof Error ? err.message : String(err ?? 'Unknown error');
          const errName =
            typeof err === 'object' && err !== null && 'name' in err
              ? String((err as { name?: unknown }).name ?? '')
              : '';
          const isAbort = errName === 'AbortError';
          const isSocket =
            msg.includes('UND_ERR_SOCKET') ||
            msg.includes('other side closed') ||
            msg.toLowerCase().includes('socket');

          // Retry only on timeout/socket and only if attempts remain
          if (attempt < MAX_ATTEMPTS_PER_BASE && (isAbort || isSocket)) {
            await new Promise((res) => setTimeout(res, RETRY_BACKOFF_MS));
            continue;
          }
          // Break attempts loop; try next base
          break;
        }
      }
      if (upstreamResponse) break; // don’t try other bases once we have a response
    }

    if (!upstreamResponse) {
      const lastErrorDetail =
        lastErr instanceof Error
          ? lastErr.message
          : typeof lastErr === 'string'
            ? lastErr
            : 'unavailable';
      // Nothing succeeded; surface a clean 502 with no-store
      return NextResponse.json(
        { error: 'Analytics request failed', detail: lastErrorDetail },
        noStore({ status: 502 })
      );
    }

    // Parse upstream payload
    const contentType = upstreamResponse.headers.get('content-type') ?? '';
    let data: unknown;

    if (contentType.includes('application/json')) {
      try {
        data = await upstreamResponse.json();
      } catch {
        data = {};
      }
    } else {
      let textPayload = '';
      try {
        textPayload = await upstreamResponse.text();
      } catch {
        textPayload = '';
      }
      data = upstreamResponse.ok ? { message: textPayload } : { error: textPayload || 'Upstream error' };
    }

    // Mirror upstream status on errors; enrich on success
    if (!upstreamResponse.ok) {
      const payload: Record<string, unknown> =
        typeof data === 'string'
          ? { error: data }
          : typeof data === 'object' && data !== null
            ? (data as Record<string, unknown>)
            : { error: 'Invalid upstream payload' };
      return NextResponse.json(
        {
          proxy: 'analytics-gateway',
          upstream_status: upstreamResponse.status,
          base: upstreamBaseUsed,
          ...payload,
        },
        noStore({ status: upstreamResponse.status })
      );
    }

    const res = NextResponse.json(
      {
        proxy: 'analytics-gateway',
        base: upstreamBaseUsed,
        data,
      },
      noStore({ status: 200 })
    );

    // Forward Set-Cookie (array or single) if upstream set any session context
    try {
      const cookies: string[] = [];
      upstreamResponse.headers.forEach((value, key) => {
        if (key.toLowerCase() === 'set-cookie' && value) {
          cookies.push(value);
        }
      });
      const single = upstreamResponse.headers.get('set-cookie');
      if (single && !cookies.includes(single)) cookies.push(single);
      for (const raw of cookies) {
        res.headers.append('Set-Cookie', raw);
      }
    } catch {
      const single = upstreamResponse.headers.get('set-cookie');
      if (single) res.headers.set('Set-Cookie', single);
    }

    // Trace headers (optional, safe to expose)
    res.headers.set('X-Upstream-Base', String(upstreamBaseUsed || 'unknown'));
    res.headers.set('X-Proxy-Cache', 'no-store');

    return res;
  } catch (error: unknown) {
    return NextResponse.json(
      {
        error: 'Internal server error',
        detail:
          error instanceof Error
            ? error.message
            : typeof error === 'string'
              ? error
              : 'unknown',
      },
      noStore({ status: 500 })
    );
  }
}
