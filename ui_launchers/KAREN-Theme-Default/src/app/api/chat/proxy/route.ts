import { NextRequest, NextResponse } from 'next/server';
import { getBackendCandidates, withBackendPath } from '@/app/api/_utils/backend';

type HeadersWithRaw = Headers & { raw?: () => Record<string, string[]> };

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

function forwardResponse(origin: Response): Response {
  const headers = new Headers();

  origin.headers.forEach((value, key) => {
    const lower = key.toLowerCase();
    if (HOP_BY_HOP.has(lower)) return;
    if (lower === 'set-cookie') return;
    headers.set(key, value);
  });

  const headersWithRaw = origin.headers as HeadersWithRaw;
  const raw = headersWithRaw.raw?.();
  const setCookies = raw?.['set-cookie'] ?? [];
  if (setCookies.length > 0) {
    for (const cookie of setCookies) {
      headers.append('set-cookie', cookie);
    }
  } else {
    const single = origin.headers.get('set-cookie');
    if (single) headers.append('set-cookie', single);
  }

  const contentType = headers.get('content-type') ?? '';
  if (contentType.includes('text/event-stream')) {
    if (!headers.has('cache-control')) {
      headers.set('cache-control', 'no-cache, no-transform');
    }
    headers.set('connection', 'keep-alive');
  }

  return new Response(origin.body, {
    status: origin.status,
    statusText: origin.statusText,
    headers,
  });
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

  let lastError: Error | null = null;
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
      } catch (err) {
        if (timeout) clearTimeout(timeout);
        const normalizedError =
          err instanceof Error ? err : new Error(String(err ?? 'Unknown error'));
        lastError = normalizedError;

        const msg = normalizedError.message;
        const isAbort = normalizedError.name === 'AbortError';
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
    const fallbackMessage = 'All backends unreachable or timed out';
    const errorMessage = lastError instanceof Error ? lastError.message : fallbackMessage;

    return NextResponse.json(
      {
        error: 'Chat request failed',
        message: errorMessage || fallbackMessage,
      },
      { status: 502 }
    );
  }

  return forwardResponse(response);
}
