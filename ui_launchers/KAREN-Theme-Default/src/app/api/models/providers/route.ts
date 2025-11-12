import { NextRequest, NextResponse } from 'next/server';
import { withBackendPath, getBackendCandidates } from '@/app/api/_utils/backend';
import { logger } from '@/lib/logger';

const REQUEST_TIMEOUT_MS = Number(process.env.KAREN_API_PROXY_TIMEOUT_MS || 15000);
const RETRYABLE_STATUS = new Set([500, 502, 503, 504]);

type BackendResult = {
  response: Response;
  url: string;
};

function buildForwardHeaders(
  request: NextRequest,
  overrides: Record<string, string> = {},
): Record<string, string> {
  const headers: Record<string, string> = {
    Accept: 'application/json',
    ...overrides,
  };

  const authorization = request.headers.get('authorization');
  const cookie = request.headers.get('cookie');
  const requestId = request.headers.get('x-request-id');

  if (authorization) headers.Authorization = authorization;
  if (cookie) headers.Cookie = cookie;
  if (requestId) headers['X-Request-ID'] = requestId;

  return headers;
}

async function parseBody(response: Response): Promise<unknown> {
  const raw = await response.text();
  if (!raw) return {};
  try {
    return JSON.parse(raw);
  } catch {
    // Return as a simple message if not JSON but request succeeded.
    return response.ok ? { message: raw } : { error: raw };
  }
}

async function tryFetch(
  url: string,
  init: RequestInit,
  timeoutMs = REQUEST_TIMEOUT_MS,
): Promise<Response> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const resp = await fetch(url, {
      ...init,
      signal: controller.signal,
      // @ts-expect-error (Node/undici hint)
      keepalive: true,
      cache: 'no-store',
    });
    return resp;
  } finally {
    clearTimeout(timeout);
  }
}

async function forwardToBackends(
  path: string,
  request: NextRequest,
  init: RequestInit,
  fallbackPath?: string,
): Promise<BackendResult> {
  const candidates = getBackendCandidates(['http://host.docker.internal:8000']);
  const attempts: Array<{ url: string; status?: number; error?: string }> = [];
  let lastResponse: BackendResult | null = null;

  for (const base of candidates) {
    // First, authenticated/private endpoint
    const primaryUrl = withBackendPath(path, base);
    try {
      const res = await tryFetch(primaryUrl, init);
      if (RETRYABLE_STATUS.has(res.status)) {
        attempts.push({ url: primaryUrl, status: res.status });
        lastResponse = { response: res, url: primaryUrl };
      } else if (!res.ok && fallbackPath && [401, 403, 404].includes(res.status)) {
        // Fallback to a public discovery/providers endpoint if access denied/not found
        const publicUrl = withBackendPath(fallbackPath, base);
        try {
          const pubRes = await tryFetch(publicUrl, init);
          if (pubRes.ok || !RETRYABLE_STATUS.has(pubRes.status)) {
            return { response: pubRes, url: publicUrl };
          }
          attempts.push({ url: publicUrl, status: pubRes.status });
          lastResponse = { response: pubRes, url: publicUrl };
        } catch (e: Event) {
          attempts.push({ url: publicUrl, error: e?.message || String(e) });
        }
      } else {
        return { response: res, url: primaryUrl };
      }
    } catch (e: Event) {
      attempts.push({ url: primaryUrl, error: e?.message || String(e) });
    }
  }

  if (lastResponse) {
    logger.warn('All model providers candidates returned server errors', { attempts });
    return lastResponse;
  }

  throw new Error(
    attempts.length
      ? `All backends failed: ${attempts.map(a => `${a.url}${a.status ? ` (HTTP ${a.status})` : a.error ? ` (${a.error})` : ''}`).join('; ')}`
      : 'No backend candidates available',
  );
}

export async function GET(request: NextRequest) {
  try {
    // Preserve any incoming query params (e.g., provider filters)
    const qs = request.nextUrl.searchParams.toString();
    const path = `/api/models/providers${qs ? `?${qs}` : ''}`;
    const publicFallback = `/api/public/models/providers${qs ? `?${qs}` : ''}`;

    const { response, url } = await forwardToBackends(
      path,
      request,
      {
        method: 'GET',
        headers: buildForwardHeaders(request),
      },
      publicFallback,
    );

    const payload = await parseBody(response);

    logger.info('Model providers proxy result', {
      url,
      status: response.status,
    });

    return NextResponse.json(
      typeof payload === 'string' ? { message: payload } : payload ?? {},
      {
        status: response.status,
        headers: {
          'Cache-Control': response.ok ? 'public, max-age=300' : 'no-store',
          Vary: 'Authorization, Cookie, Accept',
        },
      },
    );
  } catch (error: Error) {
    const message = error?.message || 'Unknown error';
    return NextResponse.json(
      {
        error: 'Models service unavailable',
        message: 'Unable to fetch model providers',
        details: message,
      },
      { status: 503 },
    );
  }
}
