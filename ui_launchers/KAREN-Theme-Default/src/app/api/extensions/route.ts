import { NextRequest, NextResponse } from 'next/server';
import { getBackendCandidates, withBackendPath } from '@/app/api/_utils/backend';
import { getSampleExtensionsResponse } from '@/lib/extensions/sample-data';

const REQUEST_TIMEOUT_MS = Number(
  process.env.NEXT_PUBLIC_EXTENSIONS_TIMEOUT_MS ||
    process.env.KAREN_EXTENSIONS_TIMEOUT_MS ||
    5_000
);

export const dynamic = 'force-dynamic';
export const revalidate = 0;

function buildForwardHeaders(request: NextRequest): Headers {
  const headers = new Headers({
    Accept: 'application/json',
  });

  const auth = request.headers.get('authorization');
  if (auth) headers.set('Authorization', auth);

  const cookie = request.headers.get('cookie');
  if (cookie) headers.set('Cookie', cookie);

  const forwardable = new Map([
    ['x-session-id', 'X-Session-ID'],
    ['x-user-id', 'X-User-ID'],
    ['x-tenant-id', 'X-Tenant-ID'],
    ['x-request-id', 'X-Request-ID'],
    ['x-correlation-id', 'X-Correlation-ID'],
    ['x-api-key', 'X-API-Key'],
  ]);

  for (const [source, target] of forwardable.entries()) {
    const value = request.headers.get(source);
    if (value) headers.set(target, value);
  }

  return headers;
}

async function parseBackendResponse(response: Response): Promise<unknown> {
  const contentType = response.headers.get('content-type') || '';
  if (contentType.toLowerCase().includes('application/json')) {
    try {
      return await response.json();
    } catch {
      return { message: 'Invalid JSON payload from backend.' };
    }
  }

  try {
    const text = await response.text();
    return text ? { message: text } : {};
  } catch {
    return {};
  }
}

function buildSuccessResponse(status: number, data: unknown, upstream: Response) {
  const res = NextResponse.json(data, {
    status,
    headers: {
      'Cache-Control': 'no-store',
      'X-Proxy-Upstream-Status': String(upstream.status),
    },
  });

  upstream.headers.forEach((value, key) => {
    const lower = key.toLowerCase();
    if (lower === 'set-cookie' || lower === 'transfer-encoding') return;
    if (lower === 'content-length') return;
    if (lower === 'connection') return;
    res.headers.set(key, value);
  });

  return res;
}

export async function GET(request: NextRequest) {
  const headers = buildForwardHeaders(request);
  const candidates = getBackendCandidates();
  let lastError: unknown = null;

  for (const base of candidates) {
    const url = withBackendPath('/api/extensions/', base);
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

    try {
      const response = await fetch(url, {
        method: 'GET',
        headers,
        signal: controller.signal,
        cache: 'no-store',
      });

      clearTimeout(timeout);

      if (!response.ok) {
        // Propagate auth failures immediately
        if (response.status === 401 || response.status === 403) {
          const data = await parseBackendResponse(response);
          return buildSuccessResponse(response.status, data, response);
        }

        lastError = new Error(`HTTP ${response.status}`);

        // For 4xx errors other than auth, propagate first response
        if (response.status >= 400 && response.status < 500) {
          const data = await parseBackendResponse(response);
          return buildSuccessResponse(response.status, data, response);
        }

        // Retry for >=500 with next candidate
        continue;
      }

      const data = await parseBackendResponse(response);
      return buildSuccessResponse(response.status, data, response);
    } catch (error) {
      clearTimeout(timeout);
      lastError = error;
      continue;
    }
  }

  if (process.env.NODE_ENV !== 'production') {
    console.warn(
      '[api/extensions] Falling back to sample extensions',
      lastError instanceof Error ? lastError.message : lastError
    );
  }

  const fallback = getSampleExtensionsResponse();
  return NextResponse.json(fallback, {
    status: 200,
    headers: {
      'Cache-Control': 'no-store',
      'X-Fallback': 'sample-extensions',
    },
  });
}
