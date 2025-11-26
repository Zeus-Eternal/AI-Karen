// app/api/models/all/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { withBackendPath } from '@/app/api/_utils/backend';
import { safeGetSearchParams, safeGetHeaders } from '@/app/api/_utils/static-export-helpers';

// Explicitly set dynamic to auto for static export compatibility
export const dynamic = 'auto';

/**
 * GET /api/models/all
 * - Forwards query params to backend
 * - Forwards Authorization & Cookie safely
 * - 20s timeout
 * - Robust JSON-or-text response handling
 * - Caches successful upstream responses for 10 minutes
 */
export async function GET(request: NextRequest) {
  // Build upstream URL with original query params
  const upstreamUrl = new URL(withBackendPath('/api/models/all'));
  const searchParams = safeGetSearchParams(request);
  searchParams.forEach((v, k) => upstreamUrl.searchParams.append(k, v));

  // Minimal, explicit header forwarding
  const headers = new Headers({ Accept: 'application/json' });
  const requestHeaders = safeGetHeaders(request);
  const authorization = requestHeaders.get('authorization');
  const cookie = requestHeaders.get('cookie');
  if (authorization) headers.set('Authorization', authorization);
  if (cookie) headers.set('Cookie', cookie);

  let upstreamResponse: Response;

  try {
    upstreamResponse = await fetch(upstreamUrl.toString(), {
      method: 'GET',
      headers,
      // Node 18+ supports AbortSignal.timeout
      signal: AbortSignal.timeout(20_000),
      // We control caching on our response, not the fetch cache
      cache: 'no-store',
    });
  } catch (err) {
    const message =
      err instanceof Error ? err.message : 'Unknown upstream fetch error';
    return NextResponse.json(
      {
        error: 'Models service unavailable',
        message: 'Unable to reach upstream models service',
        details: message,
      },
      { status: 503 }
    );
  }

  // Try to parse JSON; fall back to text if needed
  const isJson =
    upstreamResponse.headers
      .get('content-type')
      ?.toLowerCase()
      .includes('application/json') ?? false;

  let payload: unknown = null;
  try {
    payload = isJson ? await upstreamResponse.json() : await upstreamResponse.text();
  } catch {
    // If body parse fails, keep payload as null for transparent pass-through
    payload = null;
  }

  // Cache successful responses for 10 minutes (public models list is cacheable)
  const cacheHeaders: Record<string, string> = {
    'Cache-Control': 'public, max-age=600',
    Pragma: 'cache',
  };

  if (upstreamResponse.ok) {
    // If upstream didn't return JSON but was OK, still wrap as JSON for our API contract
    const data =
      payload ?? { message: 'No content from upstream', data: null };
    return NextResponse.json(data, {
      status: upstreamResponse.status,
      headers: cacheHeaders,
    });
  }

  // Non-2xx: surface upstream status and payload (text or json) transparently
  return NextResponse.json(
    {
      error: 'Upstream error',
      upstream_status: upstreamResponse.status,
      data: payload,
    },
    { status: upstreamResponse.status }
  );
}
