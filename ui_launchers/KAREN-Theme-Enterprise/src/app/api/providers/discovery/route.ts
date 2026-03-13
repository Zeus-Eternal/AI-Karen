import { NextRequest, NextResponse } from 'next/server';
// IMPORTANT: Never use NEXT_PUBLIC_* here (those may point back to the Next server and cause loops)
import { getBackendCandidates, withBackendPath } from '@/app/api/_utils/backend';

const BACKEND_CANDIDATES = getBackendCandidates(['http://host.docker.internal:8000']);

// Prefer server-side env; fall back to KAREN var; default 20s
const TIMEOUT_MS = Number(
  process.env.KAREN_API_PROXY_LONG_TIMEOUT_MS ||
  process.env.NEXT_PUBLIC_API_PROXY_LONG_TIMEOUT_MS || // still honored if set, but not used for URLs
  20000
);

// If the private discovery is 401/403/404, we try the public discovery as a fallback
const RETRYABLE_PRIVATE_STATUSES = new Set([401, 403, 404]);
const JSON_CT = 'application/json';

function buildForwardHeaders(req: NextRequest): Record<string, string> {
  const headers: Record<string, string> = {
    Accept: JSON_CT,
    Connection: 'keep-alive',
    'X-Forwarded-Proto': 'https',
  };

  const auth = req.headers.get('authorization');
  const cookie = req.headers.get('cookie');
  const reqId = req.headers.get('x-request-id');
  const ua = req.headers.get('user-agent');

  if (auth) headers.Authorization = auth;
  if (cookie) headers.Cookie = cookie;
  if (reqId) headers['X-Request-ID'] = reqId;
  if (ua) headers['User-Agent'] = ua;

  return headers;
}

async function fetchWithTimeout(url: string, init: RequestInit, timeoutMs: number): Promise<Response> {
  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...init, signal: controller.signal, cache: 'no-store' as const });
  } finally {
    clearTimeout(t);
  }
}

async function tryDiscover(
  base: string,
  search: string,
  req: NextRequest,
): Promise<{ response: Response | null; urlTried: string; fallbackUsed: boolean }> {
  const headers = buildForwardHeaders(req);

  // 1) Private discovery
  const privateUrl = withBackendPath(`/api/providers/discovery${search ? `?${search}` : ''}`, base);
  try {
    const privateResp = await fetchWithTimeout(
      privateUrl,
      { method: 'GET', headers, keepalive: true },
      TIMEOUT_MS,
    );
    if (privateResp.ok || !RETRYABLE_PRIVATE_STATUSES.has(privateResp.status)) {
      return { response: privateResp, urlTried: privateUrl, fallbackUsed: false };
    }

    // 2) Fallback to public discovery for certain statuses
    const publicUrl = withBackendPath(`/api/public/providers/discovery${search ? `?${search}` : ''}`, base);
    try {
      const publicResp = await fetchWithTimeout(
        publicUrl,
        { method: 'GET', headers: { Accept: JSON_CT, Connection: 'keep-alive' }, keepalive: true },
        TIMEOUT_MS,
      );

      return { response: publicResp, urlTried: publicUrl, fallbackUsed: true };
    } catch {
      // Public attempt failed—return private response as last known
      return { response: privateResp, urlTried: privateUrl, fallbackUsed: false };
    }
  } catch {
    // Private request itself failed (timeout/network). No fallback URL to return.
    return { response: null, urlTried: privateUrl, fallbackUsed: false };
  }
}

function noCacheHeaders(extra?: Record<string, string>) {
  return {
    'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
    Pragma: 'no-cache',
    Expires: '0',
    ...(extra || {}),
  };
}

export async function GET(request: NextRequest) {
  try {
    const url = new URL(request.url);
    const searchParams = url.searchParams.toString();

    let chosenResponse: Response | null = null;
    let chosenUrl = '';
    let usedFallback = false;
    let lastError: string | null = null;

    for (const base of BACKEND_CANDIDATES) {
      const { response, urlTried, fallbackUsed } = await tryDiscover(base, searchParams, request);

      if (response) {
        chosenResponse = response;
        chosenUrl = urlTried;
        usedFallback = fallbackUsed;
        // If OK, we’re done; else we’ll still return that status but we don’t try other bases
        break;
      } else {
        lastError = `Timeout or network error for ${urlTried}`;
        // Continue to next base
      }
    }

    if (!chosenResponse) {
      return NextResponse.json(
        { error: 'Discovery request failed', detail: lastError ?? 'No backend candidates reachable' },
        { status: 502, headers: noCacheHeaders({ 'Content-Type': JSON_CT }) },
      );
    }

    const contentType = chosenResponse.headers.get('content-type') || '';
    // Try to parse JSON if advertised; otherwise treat as text and wrap
    if (contentType.includes(JSON_CT)) {
      let payload: unknown = {};
      try {
        payload = await chosenResponse.json();
      } catch {
        payload = {};
      }
      return NextResponse.json(payload, {
        status: chosenResponse.status,
        headers: noCacheHeaders({
          'X-Backend-URL': chosenUrl,
          'X-Discovery-Fallback': String(usedFallback),
        }),
      });
    } else {
      let bodyText = '';
      try {
        bodyText = await chosenResponse.text();
      } catch {
        bodyText = '';
      }

      const data = chosenResponse.ok ? { message: bodyText } : { error: bodyText || 'Upstream error' };
      return NextResponse.json(data, {
        status: chosenResponse.status,
        headers: noCacheHeaders({
          'X-Backend-URL': chosenUrl,
          'X-Discovery-Fallback': String(usedFallback),
        }),
      });
    }
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    return NextResponse.json(
      { error: 'Internal server error', detail: message },
      { status: 500, headers: noCacheHeaders({ 'Content-Type': JSON_CT }) },
    );
  }
}
