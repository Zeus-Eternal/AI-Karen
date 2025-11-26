import { NextRequest, NextResponse } from 'next/server';
import { withBackendPath } from '@/app/api/_utils/backend';
import { safeGetSearchParams, safeGetHeaders } from '@/app/api/_utils/static-export-helpers';

// Explicitly set dynamic to auto for static export compatibility
export const dynamic = 'auto';

const TIMEOUT_MS = 15_000;

export async function GET(request: NextRequest) {
  // Build upstream URL with original query params
  const searchParams = safeGetSearchParams(request);
  const upstream = new URL(withBackendPath('/api/files'));
  searchParams.forEach((v, k) => upstream.searchParams.append(k, v));

  // Minimal allow-listed headers
  const headers = new Headers({
    Accept: 'application/json, text/plain;q=0.8, */*;q=0.5',
    'Content-Type': 'application/json',
  });
  const requestHeaders = safeGetHeaders(request);
  const authorization = requestHeaders.get('authorization');
  if (authorization) headers.set('Authorization', authorization);
  const cookie = requestHeaders.get('cookie');
  if (cookie) headers.set('Cookie', cookie);

  let upstreamResp: Response;

  try {
    upstreamResp = await fetch(upstream.toString(), {
      method: 'GET',
      headers,
      signal: AbortSignal.timeout(TIMEOUT_MS),
      cache: 'no-store', // control caching at our edge response instead
    });
  } catch (err) {
    return NextResponse.json(
      {
        error: 'File service unavailable',
        message: 'Unable to fetch files (upstream unreachable)',
        details: err instanceof Error ? err.message : 'Unknown error',
      },
      { status: 503 }
    );
  }

  // Try to parse JSON; fall back to text
  const ct = upstreamResp.headers.get('content-type')?.toLowerCase() ?? '';
  let payload: unknown = null;

  try {
    if (ct.includes('application/json')) {
      payload = await upstreamResp.json();
    } else {
      const text = await upstreamResp.text();
      // Wrap non-JSON in a stable contract
      payload = { data: text, contentType: ct || 'text/plain' };
    }
  } catch {
    // Body parse failure: keep payload minimal but informative
    payload = { data: null, note: 'Unable to parse upstream body' };
  }

  const okCacheHeaders = {
    // private cache OK (contains user files listing); CDN should not cache
    'Cache-Control': 'private, max-age=300',
    Pragma: 'no-cache',
    'X-Proxy-Upstream-Status': String(upstreamResp.status),
  };

  const errCacheHeaders = {
    'Cache-Control': 'no-store',
    'X-Proxy-Upstream-Status': String(upstreamResp.status),
  };

  if (upstreamResp.ok) {
    return NextResponse.json(payload, {
      status: upstreamResp.status,
      headers: okCacheHeaders,
    });
  }

  // Bubble up non-2xx with context
  return NextResponse.json(
    {
      error: 'Upstream error',
      upstream_status: upstreamResp.status,
      data: payload,
    },
    {
      status: upstreamResp.status,
      headers: errCacheHeaders,
    }
  );
}
