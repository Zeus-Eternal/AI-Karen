import { NextRequest, NextResponse } from 'next/server';
import { getBackendCandidates, withBackendPath } from '@/app/api/_utils/backend';

/** ---------- Config ---------- */
const BACKEND_BASES = getBackendCandidates();
const CHAT_TIMEOUT_MS = Number(
  process.env.NEXT_PUBLIC_CHAT_PROXY_TIMEOUT_MS ||
    process.env.KAREN_CHAT_PROXY_TIMEOUT_MS ||
    process.env.NEXT_PUBLIC_AUTH_PROXY_TIMEOUT_MS ||
    45_000
);

/** ---------- Header helpers ---------- */
function cloneForwardHeaders(request: NextRequest): Record<string, string> {
  const headers: Record<string, string> = {
    Accept: request.headers.get('accept') ?? 'application/json',
    Connection: 'keep-alive',
  };

  const contentType = request.headers.get('content-type');
  if (contentType) headers['Content-Type'] = contentType;

  const authHeader = request.headers.get('authorization');
  if (authHeader) headers['Authorization'] = authHeader;

  const cookieHeader = request.headers.get('cookie');
  if (cookieHeader) headers['Cookie'] = cookieHeader;

  // Forward commonly used custom headers for chat context
  const forwardableMap: Record<string, string> = {
    'x-session-id': 'X-Session-ID',
    'x-conversation-id': 'X-Conversation-ID',
    'x-user-id': 'X-User-ID',
    'x-karen-auth-fallback': 'X-Karen-Auth-Fallback',
    'x-request-id': 'X-Request-ID',
    'x-trace-id': 'X-Trace-ID',
  };
  for (const [lowerKey, headerName] of Object.entries(forwardableMap)) {
    const value = request.headers.get(lowerKey);
    if (value) headers[headerName] = value;
  }

  return headers;
}

const HOP_BY_HOP = new Set([
  'transfer-encoding',
  'content-length',
  'connection',
  'keep-alive',
  'proxy-authenticate',
  'proxy-authorization',
  'te',
  'trailer',
  'upgrade',
]);

function buildNextResponse(origin: Response): NextResponse {
  const nextResponse = new NextResponse(origin.body, {
    status: origin.status,
    statusText: origin.statusText,
  });

  // Clone headers, skipping hop-by-hop
  origin.headers.forEach((value, key) => {
    const lower = key.toLowerCase();
    if (HOP_BY_HOP.has(lower)) return;
    // Avoid duplicating Set-Cookie here; we’ll handle multi-value explicitly below
    if (lower === 'set-cookie') return;
    nextResponse.headers.set(key, value);
  });

  // Preserve multiple Set-Cookie headers
  const getAll = (origin.headers as any).getAll?.bind(origin.headers);
  const setCookieHeaders: string[] = getAll ? getAll('set-cookie') ?? [] : [];
  if (setCookieHeaders.length === 0) {
    const single = origin.headers.get('set-cookie');
    if (single) setCookieHeaders.push(single);
  }
  for (const cookie of setCookieHeaders) {
    try {
      nextResponse.headers.append('Set-Cookie', cookie);
    } catch {
      // ignore malformed cookies
    }
  }

  return nextResponse;
}

/** ---------- Next.js Route flags ---------- */
export const dynamic = 'force-dynamic';
export const revalidate = 0;

/** ---------- Route ---------- */
export async function POST(request: NextRequest) {
  const targetPath = request.nextUrl.searchParams.get('path') || '/api/chat/runtime';
  const retryEnabled = request.nextUrl.searchParams.get('retry') !== 'false';

  // Read the body once; for streaming uploads, Next already buffers the request in edge/node runtimes.
  const bodyText = await request.text();
  const headers = cloneForwardHeaders(request);

  const acceptHeader = request.headers.get('accept') || '';
  const isStreaming =
    targetPath.includes('/stream') ||
    acceptHeader.includes('text/event-stream') ||
    headers['Accept']?.includes('text/event-stream');

  let lastError: any = null;
  let response: Response | null = null;

  const bases = BACKEND_BASES;
  const maxAttempts = retryEnabled ? 2 : 1;

  for (const base of bases) {
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      const url = withBackendPath(targetPath, base);

      const controller = new AbortController();
      const timeout =
        isStreaming
          ? null // don’t hard-timeout SSE; backend will keep the stream open
          : setTimeout(() => controller.abort(), CHAT_TIMEOUT_MS);

      try {
        response = await fetch(url, {
          method: 'POST',
          headers,
          body: bodyText,
          signal: controller.signal,
          // @ts-ignore Node/undici hint
          keepalive: true,
          cache: 'no-store',
        });

        if (timeout) clearTimeout(timeout);
        lastError = null;

        // If backend is clearly down/errored (>=500), try next attempt/base (unless this is final)
        if (!response.ok && response.status >= 500 && attempt < maxAttempts) {
          // tiny backoff
          await new Promise((res) => setTimeout(res, 250));
          continue;
        }

        // Success (or client error we should propagate)
        break;
      } catch (err: any) {
        if (timeout) clearTimeout(timeout);
        lastError = err;

        const msg = String(err?.message || err);
        const isAbort = err?.name === 'AbortError';
        const isSocket = msg.includes('UND_ERR_SOCKET') || msg.includes('other side closed');

        if (attempt < maxAttempts && (isAbort || isSocket)) {
          await new Promise((res) => setTimeout(res, 300));
          continue;
        }
      }
    }
    if (response) break;
  }

  if (!response) {
    return NextResponse.json(
      {
        error: 'Chat request failed',
        message: lastError?.message || 'All backends unreachable or timed out',
      },
      { status: 502 }
    );
  }

  return buildNextResponse(response);
}
