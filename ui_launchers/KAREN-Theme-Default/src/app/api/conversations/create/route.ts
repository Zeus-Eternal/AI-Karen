// app/api/conversations/create/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { withBackendPath } from '@/app/api/_utils/backend';

const TIMEOUT_MS = 15_000;

function buildForwardHeaders(req: NextRequest): Headers {
  const h = new Headers({ 'Content-Type': 'application/json', Accept: 'application/json' });
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
  // Parse JSON body safely
  let body: unknown;
  try {
    body = await request.json();
  } catch (e) {
    return NextResponse.json(
      { error: 'Invalid request body', message: e instanceof Error ? e.message : 'Malformed JSON' },
      { status: 400, headers: { 'Cache-Control': 'no-store' } }
    );
  }

  const backendUrl = withBackendPath('/api/conversations/create');

  let upstreamResp: Response;
  try {
    upstreamResp = await fetch(backendUrl, {
      method: 'POST',
      headers: buildForwardHeaders(request),
      body: JSON.stringify(body ?? {}),
      signal: AbortSignal.timeout(TIMEOUT_MS),
      cache: 'no-store',
    });
  } catch (err) {
    return NextResponse.json(
      {
        error: 'Conversation service unavailable',
        message: 'Unable to create conversation (upstream unreachable)',
        details: err instanceof Error ? err.message : 'Unknown error',
      },
      { status: 503, headers: { 'Cache-Control': 'no-store' } }
    );
  }

  // Resilient parse of upstream body
  const ct = upstreamResp.headers.get('content-type')?.toLowerCase() ?? '';
  let payload: unknown;
  try {
    if (ct.includes('application/json')) {
      payload = await upstreamResp.json();
    } else {
      const text = await upstreamResp.text();
      payload = { message: text || '', contentType: ct || 'text/plain' };
    }
  } catch {
    payload = { message: 'Unable to parse upstream body' };
  }

  // Mirror upstream status; never cache writes
  return NextResponse.json(payload, {
    status: upstreamResp.status,
    headers: {
      'Cache-Control': 'no-cache, no-store, must-revalidate',
      Pragma: 'no-cache',
      Expires: '0',
      'X-Proxy-Upstream-Status': String(upstreamResp.status),
    },
  });
}
