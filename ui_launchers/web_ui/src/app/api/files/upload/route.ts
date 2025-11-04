// app/api/files/upload/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { withBackendPath } from '@/app/api/_utils/backend';

const UPLOAD_TIMEOUT_MS = 120_000; // 2 minutes

/** Allow-list and build upstream headers (never set Content-Type for FormData). */
function buildForwardHeaders(req: NextRequest): Headers {
  const h = new Headers();
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

/** CORS helper */
function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Request-ID, X-Correlation-ID',
  };
}

export async function POST(request: NextRequest) {
  const backendUrl = withBackendPath('/api/files/upload');

  let formData: FormData;
  try {
    formData = await request.formData();
  } catch (e) {
    return NextResponse.json(
      { error: 'Invalid multipart/form-data', message: e instanceof Error ? e.message : 'Malformed form data' },
      { status: 400, headers: { ...corsHeaders(), 'Cache-Control': 'no-store' } }
    );
  }

  // Optional sanity: ensure at least one file-like field exists
  const hasFile = Array.from(formData.values()).some((v) => v instanceof File);
  if (!hasFile) {
    // Not fatal—some backends accept metadata-only forms, but guard by default.
    return NextResponse.json(
      { error: 'No files provided', message: 'At least one file is required in multipart form data' },
      { status: 400, headers: { ...corsHeaders(), 'Cache-Control': 'no-store' } }
    );
  }

  try {
    const upstreamResp = await fetch(backendUrl, {
      method: 'POST',
      headers: buildForwardHeaders(request),
      body: formData, // undici sets correct multipart boundary automatically
      signal: AbortSignal.timeout(UPLOAD_TIMEOUT_MS),
      cache: 'no-store',
      // keepalive is not honored for large bodies; avoid setting explicitly
    });

    const ct = upstreamResp.headers.get('content-type')?.toLowerCase() || '';
    let payload: unknown;

    if (ct.includes('application/json')) {
      try {
        payload = await upstreamResp.json();
      } catch {
        payload = { status: 'unknown', message: 'Invalid JSON from upstream' };
      }
    } else {
      try {
        const text = await upstreamResp.text();
        payload = { status: upstreamResp.ok ? 'success' : 'error', message: text || '' };
      } catch {
        payload = { status: 'unknown' };
      }
    }

    // Mirror upstream status; no caching
    return NextResponse.json(payload, {
      status: upstreamResp.status,
      headers: {
        ...corsHeaders(),
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        Pragma: 'no-cache',
        Expires: '0',
        'X-Proxy-Upstream-Status': String(upstreamResp.status),
      },
    });
  } catch (err: any) {
    const isAbort = err?.name === 'AbortError';
    return NextResponse.json(
      {
        error: isAbort ? 'Upload timeout' : 'File upload service unavailable',
        message: isAbort
          ? `Upload exceeded ${Math.round(UPLOAD_TIMEOUT_MS / 1000)}s limit`
          : err instanceof Error
          ? err.message
          : 'Unknown error',
      },
      { status: isAbort ? 504 : 503, headers: { ...corsHeaders(), 'Cache-Control': 'no-store' } }
    );
  }
}

/** Preflight */
export async function OPTIONS() {
  return new Response(null, { status: 204, headers: corsHeaders() });
}
