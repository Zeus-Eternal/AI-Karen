// app/api/copilot/start/route.ts
import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL =
  process.env.KAREN_BACKEND_URL ||
  process.env.NEXT_PUBLIC_KAREN_BACKEND_URL ||
  'http://127.0.0.1:8000';

const TIMEOUT_MS = 30_000;

function buildUpstreamUrl(path: string) {
  const base = BACKEND_URL.replace(/\/+$/, '');
  return `${base}${path.startsWith('/') ? path : `/${path}`}`;
}

function buildHeaders(req: NextRequest): Headers {
  const h = new Headers({
    Accept: 'application/json',
    'Content-Type': 'application/json',
    Connection: 'keep-alive',
  });
  const auth = req.headers.get('authorization');
  if (auth) h.set('Authorization', auth);

  const cookie = req.headers.get('cookie');
  if (cookie) h.set('Cookie', cookie);

  const reqId = req.headers.get('x-request-id');
  if (reqId) h.set('X-Request-ID', reqId);

  const corrId = req.headers.get('x-correlation-id');
  if (corrId) h.set('X-Correlation-ID', corrId);

  return h;
}

export async function POST(request: NextRequest) {
  // Parse body (fail → 400)
  let body: unknown;
  try {
    body = await request.json();
  } catch (e) {
    return NextResponse.json(
      {
        error: 'Invalid JSON body',
        message: e instanceof Error ? e.message : 'Malformed request payload',
      },
      { status: 400 }
    );
  }

  const url = buildUpstreamUrl('/api/copilot/start');

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: buildHeaders(request),
      body: JSON.stringify(body ?? {}),
      signal: AbortSignal.timeout(TIMEOUT_MS),
      cache: 'no-store',
      // keepalive not reliable for large bodies; omit on purpose
    });

    const ct = (response.headers.get('content-type') || '').toLowerCase();
    let data: unknown = {};

    if (ct.includes('application/json')) {
      try {
        data = await response.json();
      } catch {
        data = { message: 'Invalid JSON from upstream' };
      }
    } else {
      try {
        const text = await response.text();
        data = text ? { message: text } : {};
      } catch {
        data = {};
      }
    }

    return NextResponse.json(data, {
      status: response.status,
      headers: {
        'Cache-Control': 'no-store',
        'X-Proxy-Upstream-Status': String(response.status),
      },
    });
  } catch (err: unknown) {
    const errName =
      err && typeof err === "object" && "name" in err && typeof err.name === "string"
        ? err.name
        : undefined;
    // Graceful “ghost-start” fallback (explicitly marked)
    const fallback = {
      status: 'started',
      message: 'Copilot session initialized (fallback)',
      session_id: `session_${Date.now()}`,
      timestamp: new Date().toISOString(),
    };

    // You can switch to 202 or 503 depending on product semantics.
    // Keeping 200 to match prior behavior, but flagging via headers.
    return NextResponse.json(fallback, {
      status: 200,
      headers: {
        'Cache-Control': 'no-store',
        'X-Fallback': 'true',
        'X-Fallback-Reason':
          errName === 'AbortError'
            ? `timeout_${Math.round(TIMEOUT_MS / 1000)}s`
            : 'upstream_unreachable',
      },
    });
  }
}
