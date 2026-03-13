import { NextRequest, NextResponse } from 'next/server';
import { getBackendCandidates, withBackendPath } from '@/app/api/_utils/backend';

const REQUEST_TIMEOUT_MS = Number(
  process.env.NEXT_PUBLIC_MEMORY_TIMEOUT_MS ||
  process.env.KAREN_MEMORY_TIMEOUT_MS ||
  30_000
);

export const revalidate = 0;

type MemoryCommitRequest = {
  user_id: string;
  org_id?: string;
  text: string;
  tags?: string[];
  importance?: number;
  decay?: string;
};

type MemoryCommitResponse = {
  id: string;
  success: boolean;
  message: string;
  correlation_id: string;
};

function buildForwardHeaders(request: NextRequest): Headers {
  const headers = new Headers({
    Accept: 'application/json',
    'Content-Type': request.headers.get('content-type') || 'application/json',
  });

  const forwardable = new Map([
    ['authorization', 'Authorization'],
    ['cookie', 'Cookie'],
    ['x-session-id', 'X-Session-ID'],
    ['x-conversation-id', 'X-Conversation-ID'],
    ['x-user-id', 'X-User-ID'],
    ['x-request-id', 'X-Request-ID'],
    ['x-correlation-id', 'X-Correlation-ID'],
    ['x-api-key', 'X-API-Key'],
    ['x-client-version', 'X-Client-Version'],
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

function buildUpstreamResponse(status: number, data: unknown, upstream: Response) {
  const res = NextResponse.json(data, {
    status,
    headers: {
      'Cache-Control': 'no-store',
      'X-Proxy-Upstream-Status': String(upstream.status),
    },
  });

  upstream.headers.forEach((value, key) => {
    const lower = key.toLowerCase();
    if (lower === 'set-cookie' || lower === 'transfer-encoding' || lower === 'content-length') return;
    if (lower === 'connection') return;
    res.headers.set(key, value);
  });

  return res;
}

function buildFallbackResponse(text: string) {
  return {
    id: `fallback_${Date.now()}`,
    success: true,
    message: 'Memory stored in fallback mode',
    correlation_id: `fallback_${Date.now()}`,
  };
}

export async function POST(request: NextRequest) {
  const headers = buildForwardHeaders(request);
  const rawBody = await request.text();
  const bodyText = rawBody.trim().length > 0 ? rawBody : '{}';

  let parsedBody: MemoryCommitRequest | null = null;
  try {
    parsedBody = JSON.parse(bodyText) as MemoryCommitRequest;
  } catch {
    parsedBody = null;
  }


  const candidates = getBackendCandidates();
  let lastError: unknown = null;

  for (const base of candidates) {
    const url = withBackendPath('/api/memory/commit', base);
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: bodyText,
        signal: controller.signal,
        cache: 'no-store',
      });

      clearTimeout(timeout);

      if (!response.ok) {
        // Propagate client errors immediately
        if (response.status >= 400 && response.status < 500) {
          const data = await parseBackendResponse(response);
          return buildUpstreamResponse(response.status, data, response);
        }

        lastError = new Error(`HTTP ${response.status}`);
        continue;
      }

      const data = await parseBackendResponse(response);
      return buildUpstreamResponse(response.status, data, response);
    } catch (error) {
      clearTimeout(timeout);
      lastError = error;
      continue;
    }
  }

  if (process.env.NODE_ENV !== 'production') {
    console.warn(
      '[api/memory/commit] Falling back to success response',
      lastError instanceof Error ? lastError.message : lastError
    );
  }

  const fallback = buildFallbackResponse(parsedBody?.text || '');
  return NextResponse.json(fallback, {
    status: 200,
    headers: {
      'Cache-Control': 'no-store',
      'X-Fallback': 'memory-commit',
      'X-Fallback-Reason':
        lastError instanceof Error && lastError.name === 'AbortError'
          ? `timeout_${REQUEST_TIMEOUT_MS}ms`
          : 'upstream_unreachable',
    },
  });
}

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Session-ID, X-User-ID, X-Correlation-ID',
    },
  });
}