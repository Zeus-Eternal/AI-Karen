// app/api/chat/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { withBackendPath } from '@/app/api/_utils/backend';
import { safeGetSearchParams, safeGetHeaders } from '@/app/api/_utils/static-export-helpers';

// Explicitly set dynamic to auto for static export compatibility
export const dynamic = 'auto';

const TIMEOUT_MS = 60_000;

type ChatMessage = { role: string; content: string };
type ChatBody = {
  model?: string;
  messages?: ChatMessage[];
  stream?: boolean;
  [k: string]: unknown;
};

export async function POST(request: NextRequest) {
  // Parse body safely
  let body: ChatBody;
  try {
    body = (await request.json()) as ChatBody;
  } catch {
    return NextResponse.json(
      {
        error: 'Invalid request body',
        message: 'Unable to parse JSON request body',
      },
      { status: 400 }
    );
  }

  // Build upstream URL with caller query params
  const searchParams = safeGetSearchParams(request);
  const upstream = new URL(withBackendPath('/api/chat'));
  searchParams.forEach((v, k) => upstream.searchParams.append(k, v));

  // Allow-listed headers to forward
  const headers = new Headers({
    'Content-Type': 'application/json',
    Accept: 'application/json, text/plain;q=0.8, */*;q=0.5',
  });
  const requestHeaders = safeGetHeaders(request);
  const authorization = requestHeaders.get('authorization');
  if (authorization) headers.set('Authorization', authorization);
  const cookie = requestHeaders.get('cookie');
  if (cookie) headers.set('Cookie', cookie);

  // Forward trace headers for observability
  const reqId = requestHeaders.get('x-request-id');
  if (reqId) headers.set('X-Request-ID', reqId);
  const corrId = requestHeaders.get('x-correlation-id');
  if (corrId) headers.set('X-Correlation-ID', corrId);
  const sessionId = requestHeaders.get('x-session-id');
  if (sessionId) headers.set('X-Session-ID', sessionId);
  const conversationId = requestHeaders.get('x-conversation-id');
  if (conversationId) headers.set('X-Conversation-ID', conversationId);

  // Check if streaming is requested
  const isStreaming = body.stream === true || 
                     requestHeaders.get('accept')?.includes('text/event-stream') ||
                     searchParams.get('stream') === 'true';

  let upstreamResp: Response;
  try {
    upstreamResp = await fetch(upstream.toString(), {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(TIMEOUT_MS),
      cache: 'no-store',
    });
  } catch (err) {
    return NextResponse.json(
      {
        error: 'Chat service unavailable',
        message: 'Unable to connect to chat service (upstream unreachable)',
        details: err instanceof Error ? err.message : 'Unknown error',
      },
      { status: 503 }
    );
  }

  // Handle streaming responses
  if (isStreaming || upstreamResp.headers.get('content-type')?.includes('text/event-stream')) {
    // For streaming, we need to proxy the response directly
    const responseHeaders = new Headers();
    
    // Copy headers from upstream response, excluding hop-by-hop headers
    const hopByHopHeaders = new Set([
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
    
    upstreamResp.headers.forEach((value, key) => {
      const lowerKey = key.toLowerCase();
      if (!hopByHopHeaders.has(lowerKey)) {
        responseHeaders.set(key, value);
      }
    });
    
    // Set cache control for streaming
    if (!responseHeaders.has('cache-control')) {
      responseHeaders.set('cache-control', 'no-cache, no-transform');
    }
    responseHeaders.set('connection', 'keep-alive');
    
    // Return the streaming response
    return new Response(upstreamResp.body, {
      status: upstreamResp.status,
      statusText: upstreamResp.statusText,
      headers: responseHeaders,
    });
  }

  // Handle non-streaming JSON responses
  const ct = upstreamResp.headers.get('content-type')?.toLowerCase() ?? '';
  let payload: unknown;
  try {
    if (ct.includes('application/json')) {
      payload = await upstreamResp.json();
    } else {
      const text = await upstreamResp.text();
      payload = { data: text, contentType: ct || 'text/plain' };
    }
  } catch {
    payload = { data: null, note: 'Unable to parse upstream body' };
  }

  const okHeaders = {
    'Cache-Control': 'private, max-age=60', // per-user browser cache; no CDN
    Pragma: 'no-cache',
    'X-Proxy-Upstream-Status': String(upstreamResp.status),
  };
  const errHeaders = {
    'Cache-Control': 'no-store',
    'X-Proxy-Upstream-Status': String(upstreamResp.status),
  };

  if (upstreamResp.ok) {
    return NextResponse.json(payload, {
      status: upstreamResp.status,
      headers: okHeaders,
    });
  }

  return NextResponse.json(
    {
      error: 'Upstream error',
      upstream_status: upstreamResp.status,
      data: payload,
    },
    { status: upstreamResp.status, headers: errHeaders }
  );
}

export async function GET(request: NextRequest) {
  // Build upstream URL with caller query params
  const searchParams = safeGetSearchParams(request);
  const upstream = new URL(withBackendPath('/api/chat'));
  searchParams.forEach((v, k) => upstream.searchParams.append(k, v));

  // Allow-listed headers to forward
  const headers = new Headers({
    Accept: 'application/json, text/plain;q=0.8, */*;q=0.5',
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
      cache: 'no-store',
    });
  } catch (err) {
    return NextResponse.json(
      {
        error: 'Chat service unavailable',
        message: 'Unable to fetch chat information (upstream unreachable)',
        details: err instanceof Error ? err.message : 'Unknown error',
      },
      { status: 503 }
    );
  }

  const ct = upstreamResp.headers.get('content-type')?.toLowerCase() ?? '';
  let payload: unknown;
  try {
    if (ct.includes('application/json')) {
      payload = await upstreamResp.json();
    } else {
      const text = await upstreamResp.text();
      payload = { data: text, contentType: ct || 'text/plain' };
    }
  } catch {
    payload = { data: null, note: 'Unable to parse upstream body' };
  }

  const okHeaders = {
    'Cache-Control': 'private, max-age=60', // per-user browser cache; no CDN
    Pragma: 'no-cache',
    'X-Proxy-Upstream-Status': String(upstreamResp.status),
  };
  const errHeaders = {
    'Cache-Control': 'no-store',
    'X-Proxy-Upstream-Status': String(upstreamResp.status),
  };

  if (upstreamResp.ok) {
    return NextResponse.json(payload, {
      status: upstreamResp.status,
      headers: okHeaders,
    });
  }

  return NextResponse.json(
    {
      error: 'Upstream error',
      upstream_status: upstreamResp.status,
      data: payload,
    },
    { status: upstreamResp.status, headers: errHeaders }
  );
}