// app/api/chat/runtime/stream/route.ts
import { NextRequest } from 'next/server';
import { withBackendPath } from '@/app/api/_utils/backend';

const VERBOSE = process.env.NODE_ENV !== 'production';
const TIMEOUT_NORMAL_MS = 120_000; // streaming can be long
const TIMEOUT_DEGRADED_MS = 10_000;

const FALLBACK_RESPONSES = [
  "I'm currently running in degraded mode due to backend connectivity issues. I can provide basic assistance, but my full AI capabilities are temporarily limited.",
  "The system is experiencing some connectivity issues. I'm operating with reduced functionality but can still help with basic questions.",
  "I'm currently in fallback mode. While I can't access my full AI capabilities right now, I'm still here to help with what I can.",
  "The backend services are temporarily unavailable. I'm running in a limited capacity but can still provide some assistance.",
  "I'm operating in degraded mode due to system issues. My responses may be limited, but I'll do my best to help you."
];

// ---------- Helpers ----------
function chooseFallbackFromMessage(userMessage: string): string {
  const msg = (userMessage || '').toLowerCase();
  if (/(^|\s)(hi|hello|hey)\b/.test(msg)) {
    return "Hello! I'm currently running in degraded mode, but I'm still here to help. What can I assist you with?";
  }
  if (msg.includes('help') || msg.includes('what can you do')) {
    return "I'm currently in degraded mode with limited capabilities. I can provide basic information and assistance, but my full AI features are temporarily unavailable due to backend connectivity issues.";
  }
  if (msg.includes('error') || msg.includes('problem') || msg.includes('issue')) {
    return "I can see you're experiencing an issue. I'm currently running in degraded mode, so my troubleshooting capabilities are limited. Please try again later when full services are restored.";
  }
  if (msg.includes('status') || msg.includes('health')) {
    return "The system is currently in degraded mode due to backend connectivity issues. Core services are running but AI capabilities are limited. Please check back later for full functionality.";
  }
  return FALLBACK_RESPONSES[Math.floor(Math.random() * FALLBACK_RESPONSES.length)];
}

function createStreamingFallbackResponse(message: string): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  const text = chooseFallbackFromMessage(message);
  const tokens = text.split(/\s+/);

  return new ReadableStream<Uint8Array>({
    start(controller) {
      let i = 0;
      const pump = () => {
        if (i < tokens.length) {
          const chunk = (i === 0 ? tokens[i] : ' ' + tokens[i]);
          controller.enqueue(encoder.encode(`data: ${JSON.stringify({ content: chunk })}\n\n`));
          i += 1;
          setTimeout(pump, 50);
        } else {
          controller.enqueue(encoder.encode('data: [DONE]\n\n'));
          controller.close();
        }
      };
      // Initial event headers (optional)
      controller.enqueue(encoder.encode(`event: open\ndata: ${JSON.stringify({ mode: 'fallback' })}\n\n`));
      pump();
    }
  });
}

function buildForwardHeaders(req: NextRequest): Headers {
  const h = new Headers({
    'Content-Type': 'application/json',
    'Accept': 'text/event-stream, application/json;q=0.8, text/plain;q=0.7, */*;q=0.5',
    'Connection': 'keep-alive'
  });
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

async function checkDegradedMode(): Promise<boolean> {
  try {
    const url = withBackendPath('/api/health/degraded-mode'); // absolute server-side URL
    const resp = await fetch(url, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      signal: AbortSignal.timeout(3_000),
      cache: 'no-store'
    });
    if (!resp.ok) return false;
    const ct = (resp.headers.get('content-type') || '').toLowerCase();
    if (!ct.includes('application/json')) return false;
    const data: any = await resp.json();
    return Boolean(data?.is_active || data?.degraded_mode);
  } catch {
    return false;
  }
}

// ---------- Routes ----------
export async function POST(request: NextRequest) {
  let body: any;
  try {
    body = await request.json();
  } catch {
    const msg = "I'm experiencing technical difficulties and am running in emergency fallback mode. Please try again later.";
    return new Response(createStreamingFallbackResponse(msg), {
      status: 200,
      headers: {
        'Content-Type': 'text/event-stream; charset=utf-8',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Request-ID, X-Correlation-ID',
      }
    });
  }

  const isDegraded = await checkDegradedMode();
  const backendUrl = withBackendPath('/api/chat/runtime/stream');
  const headers = buildForwardHeaders(request);

  if (VERBOSE) {
    const preview = JSON.stringify(body);
    console.log('🔌 Stream proxy → backend', {
      backendUrl,
      isDegraded,
      timeout: isDegraded ? TIMEOUT_DEGRADED_MS : TIMEOUT_NORMAL_MS,
      bodyPreview: preview.length > 600 ? preview.slice(0, 600) + '…' : preview
    });
  }

  try {
    const upstream = await fetch(backendUrl, {
      method: 'POST',
      headers,
      body: JSON.stringify(body ?? {}),
      signal: AbortSignal.timeout(isDegraded ? TIMEOUT_DEGRADED_MS : TIMEOUT_NORMAL_MS),
      cache: 'no-store',
      // keepalive is unreliable on long-lived SSE; omit intentionally
    });

    const ct = upstream.headers.get('content-type') || '';
    const isSSE = ct.includes('text/event-stream');
    const isText = ct.includes('text/plain');

    if (isSSE || isText) {
      // Passthrough streaming body
      return new Response(upstream.body, {
        status: upstream.status,
        headers: {
          'Content-Type': isSSE ? 'text/event-stream; charset=utf-8' : 'text/plain; charset=utf-8',
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Connection': 'keep-alive',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Request-ID, X-Correlation-ID',
          'X-Proxy-Upstream-Status': String(upstream.status),
        }
      });
    }

    // Non-stream JSON fallback (some backends can reply JSON on errors)
    let data: any = {};
    try {
      data = await upstream.json();
    } catch {
      try {
        const text = await upstream.text();
        data = { message: text || '' };
      } catch {
        data = { message: 'Unknown upstream response' };
      }
    }

    return new Response(JSON.stringify(data), {
      status: upstream.status,
      headers: {
        'Content-Type': 'application/json; charset=utf-8',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
        'X-Proxy-Upstream-Status': String(upstream.status),
      }
    });
  } catch (err: any) {
    // Backend unreachable / timeout → graceful SSE fallback
    const lastUserMsg =
      (Array.isArray(body?.messages) && body.messages.length
        ? body.messages[body.messages.length - 1]?.content
        : body?.message) || '';
    if (VERBOSE) {
      console.warn('⚠️ Stream proxy fallback', {
        reason: err?.name === 'AbortError' ? 'timeout' : (err?.message || 'upstream_unreachable'),
        isDegraded
      });
    }
    return new Response(createStreamingFallbackResponse(String(lastUserMsg)), {
      status: 200,
      headers: {
        'Content-Type': 'text/event-stream; charset=utf-8',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Request-ID, X-Correlation-ID',
        'X-Fallback': 'true',
        'X-Fallback-Reason': err?.name === 'AbortError'
          ? `timeout_${isDegraded ? TIMEOUT_DEGRADED_MS : TIMEOUT_NORMAL_MS}ms`
          : 'upstream_unreachable',
      }
    });
  }
}

// CORS preflight
export async function OPTIONS() {
  return new Response(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Request-ID, X-Correlation-ID',
      'Access-Control-Max-Age': '86400'
    }
  });
}
