// app/api/health/degraded-mode/recover/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { withBackendPath } from '@/app/api/_utils/backend';

const HEALTH_TIMEOUT_MS = 10_000;

/** Build upstream headers (auth/cookies/correlation), minimal & explicit */
function buildForwardHeaders(req: NextRequest): Headers {
  const h = new Headers({
    Accept: 'application/json',
    'Content-Type': 'application/json',
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
  const upstreamUrl = withBackendPath('/api/health/degraded-mode/recover');

  // Parse JSON body if present; ignore malformed JSON gracefully
  let body: unknown = undefined;
  try {
    const ct = (request.headers.get('content-type') || '').toLowerCase();
    if (ct.includes('application/json')) {
      body = await request.json();
    }
  } catch {
    // ignore bad JSON
  }

  try {
    const response = await fetch(upstreamUrl, {
      method: 'POST',
      headers: buildForwardHeaders(request),
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: AbortSignal.timeout(HEALTH_TIMEOUT_MS),
      cache: 'no-store',
    });

    const ct = (response.headers.get('content-type') || '').toLowerCase();
    let data: any;

    if (ct.includes('application/json')) {
      try {
        data = await response.json();
      } catch {
        data = { status: 'unknown', message: 'Invalid JSON from upstream' };
      }
    } else {
      try {
        const text = (await response.text()).trim();
        data = { status: text || 'ok', message: 'Recovery initiated' };
      } catch {
        data = { status: 'unknown' };
      }
    }

    return NextResponse.json(data, {
      status: response.status,
      headers: {
        'Cache-Control': 'no-store',
        'X-Proxy-Upstream-Status': String(response.status),
      },
    });
  } catch {
    return NextResponse.json(
      {
        status: 'error',
        error: 'Backend unreachable for recovery',
        message: 'Could not connect to backend to initiate recovery',
        timestamp: new Date().toISOString(),
      },
      { status: 503 }
    );
  }
}

// Informative GET; advertise allowed method
export async function GET(_request: NextRequest) {
  return NextResponse.json(
    {
      status: 'info',
      message: 'Degraded mode recovery endpoint. Use POST to initiate recovery.',
      timestamp: new Date().toISOString(),
    },
    {
      status: 405,
      headers: { Allow: 'POST', 'Cache-Control': 'no-store' },
    }
  );
}
