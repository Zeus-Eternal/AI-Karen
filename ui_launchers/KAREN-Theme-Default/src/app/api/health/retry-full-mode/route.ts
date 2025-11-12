// app/api/health/degraded-mode/recover/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { withBackendPath } from '@/app/api/_utils/backend';

const HEALTH_TIMEOUT_MS = 10_000;

function buildForwardHeaders(req: NextRequest): Headers {
  const h = new Headers({
    Accept: 'application/json',
    'Content-Type': 'application/json',
  });

  // Forward common auth/trace headers
  const auth = req.headers.get('authorization');
  if (auth) h.set('Authorization', auth);

  const cookie = req.headers.get('cookie');
  if (cookie) h.set('Cookie', cookie);

  const xReqId = req.headers.get('x-request-id');
  if (xReqId) h.set('X-Request-ID', xReqId);

  const corr = req.headers.get('x-correlation-id');
  if (corr) h.set('X-Correlation-ID', corr);

  return h;
}

export async function POST(request: NextRequest) {
  const upstreamUrl = withBackendPath('/api/health/degraded-mode/recover');

  // Parse JSON body if present (silently ignore malformed JSON)
  let body: unknown = undefined;
  try {
    const ct = request.headers.get('content-type') || '';
    if (ct.includes('application/json')) {
      body = await request.json();
    }
  } catch {
    // ignore malformed body
  }

  try {
    const response = await fetch(upstreamUrl, {
      method: 'POST',
      headers: buildForwardHeaders(request),
      body: body !== undefined ? JSON.stringify(body) : undefined,
      // Rely on Node/undici AbortSignal.timeout for precise cutoff
      signal: AbortSignal.timeout(HEALTH_TIMEOUT_MS),
      // We don’t want any caching semantics here
      cache: 'no-store',
    });

    // Best-effort content handling
    const ct = response.headers.get('content-type') || '';
    let data: unknown;

    if (ct.toLowerCase().includes('application/json')) {
      try {
        data = await response.json();
      } catch {
        data = { status: 'unknown', message: 'Invalid JSON from upstream' };
      }
    } else {
      try {
        const text = await response.text();
        data = {
          status: text?.trim() || 'ok',
          message: 'Retry full mode initiated',
        };
      } catch {
        data = { status: 'unknown' };
      }
    }

    // Mirror upstream status; respond with JSON contract
    return NextResponse.json(data, {
      status: response.status,
      headers: {
        'Cache-Control': 'no-store',
        'X-Proxy-Upstream-Status': String(response.status),
      },
    });
  } catch (_err) {
    // Timeout / network failure
    return NextResponse.json(
      {
        status: 'error',
        error: 'Backend unreachable for retry-full-mode',
        message: 'Could not connect to backend to retry full mode',
        timestamp: new Date().toISOString(),
      },
      { status: 503 }
    );
  }
}

// Provide an informative GET; advertise allowed method
export async function GET(_request: NextRequest) {
  return NextResponse.json(
    {
      status: 'info',
      message: 'Retry full mode endpoint. Use POST to trigger recovery.',
      timestamp: new Date().toISOString(),
    },
    {
      status: 405,
      headers: { Allow: 'POST', 'Cache-Control': 'no-store' },
    }
  );
}
