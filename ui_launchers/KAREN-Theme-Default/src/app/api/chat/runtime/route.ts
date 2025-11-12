// app/api/chat/runtime/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { withBackendPath } from '@/app/api/_utils/backend';

const VERBOSE = process.env.NODE_ENV !== 'production';
const TIMEOUT_NORMAL_MS = 60_000;
const TIMEOUT_DEGRADED_MS = 10_000;

type ChatMessage = { role: string; content: string };
type ChatBody = {
  model?: string;
  messages?: ChatMessage[];
  stream?: boolean;
  [k: string]: unknown;
};

// --- Fallback, degraded-mode friendly replies ---
function createFallbackResponse(userMessage: string) {
  const msg = (userMessage || '').toLowerCase();
  const base = (content: string) => ({
    content,
    role: 'assistant' as const,
    model: 'fallback-mode',
    usage: { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 },
  });

  if (/(^|\s)(hi|hello|hey)\b/.test(msg)) {
    return base("Hello! I'm in degraded mode, but still here. What can I help you with?");
  }
  if (msg.includes('help') || msg.includes('what can you do')) {
    return base(
      "I'm in degraded mode with limited capabilities. I can provide basic info and guidance while core AI services recover."
    );
  }
  if (msg.includes('error') || msg.includes('problem') || msg.includes('issue')) {
    return base(
      "Looks like you're hitting an issue. I'm currently limited by degraded mode—try again soon when full services are back."
    );
  }
  if (msg.includes('status') || msg.includes('health')) {
    return base(
      "System is in degraded mode due to backend connectivity. Core services run, AI features are limited for now."
    );
  }
  return base(
    "I'm operating in degraded mode due to backend issues. I can give basic assistance; full AI features will return soon."
  );
}

// --- Degraded mode probe (server-side absolute URL via backend path) ---
async function checkDegradedMode(): Promise<boolean> {
  try {
    const url = withBackendPath('/api/health/degraded-mode');
    const resp = await fetch(url, {
      method: 'GET',
      headers: { Accept: 'application/json' },
      signal: AbortSignal.timeout(3_000),
      cache: 'no-store',
    });
    if (!resp.ok) return false;

    const ct = (resp.headers.get('content-type') || '').toLowerCase();
    if (!ct.includes('application/json')) return false;

    const data: unknown = await resp.json();
    return Boolean(data?.is_active || data?.degraded_mode);
  } catch {
    // If probe fails, do NOT assume degraded; keep normal behavior
    return false;
  }
}

function buildForwardHeaders(req: NextRequest): Headers {
  const h = new Headers({
    'Content-Type': 'application/json',
    Accept: 'application/json',
  });
  const auth = req.headers.get('authorization');
  if (auth) h.set('Authorization', auth);
  const cookie = req.headers.get('cookie');
  if (cookie) h.set('Cookie', cookie);

  // Trace headers for observability (optional)
  const reqId = req.headers.get('x-request-id');
  if (reqId) h.set('X-Request-ID', reqId);
  const corrId = req.headers.get('x-correlation-id');
  if (corrId) h.set('X-Correlation-ID', corrId);

  return h;
}

export async function POST(request: NextRequest) {
  if (VERBOSE) {
    console.log('🔍 ChatRuntime API: Request received', {
      url: request.url,
      method: request.method,
      headers: Object.fromEntries(request.headers.entries()),
    });
  }

  // Parse body safely
  let body: ChatBody;
  try {
    body = (await request.json()) as ChatBody;
  } catch {
    // Even if the payload is bad, reply with a gentle degraded response
    const fallback = createFallbackResponse(
      "I'm experiencing technical difficulties and am running in emergency fallback mode."
    );
    if (VERBOSE) console.log('🔍 ChatRuntime API: Body parse failed; returning fallback');
    return NextResponse.json(fallback, {
      status: 200,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        Pragma: 'no-cache',
        Expires: '0',
      },
    });
  }

  if (VERBOSE) {
    const preview = JSON.stringify(body);
    console.log('🔍 ChatRuntime API: Request body parsed', {
      bodyKeys: Object.keys(body || {}),
      model: body?.model,
      messageCount: Array.isArray(body?.messages) ? body!.messages!.length : 0,
      hasStream: body?.stream !== undefined,
      bodyPreview: preview.length > 500 ? preview.slice(0, 500) + '...' : preview,
    });
  }

  const isDegraded = await checkDegradedMode();
  const backendUrl = withBackendPath('/api/chat/runtime');

  if (VERBOSE) {
    console.log('🔍 ChatRuntime API: Degraded probe', { isDegraded, backendUrl });
  }

  const headers = buildForwardHeaders(request);

  try {
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers,
      body: JSON.stringify(body ?? {}),
      signal: AbortSignal.timeout(isDegraded ? TIMEOUT_DEGRADED_MS : TIMEOUT_NORMAL_MS),
      cache: 'no-store',
    });

    if (VERBOSE) {
      console.log('🔍 ChatRuntime API: Backend response meta', {
        status: response.status,
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries()),
        ok: response.ok,
        url: response.url,
      });
    }

    const ct = (response.headers.get('content-type') || '').toLowerCase();
    let data: unknown;

    // Prefer JSON; if not, wrap text nicely
    if (ct.includes('application/json')) {
      try {
        data = await response.json();
      } catch {
        data = { message: 'Invalid JSON from upstream' };
      }
    } else {
      try {
        const text = await response.text();
        data = text ? { message: text } : {};
      } catch {
        data = {};
      }
    }

    if (VERBOSE) {
      const str = JSON.stringify(data ?? {});
      console.log('🔍 ChatRuntime API: Backend response data', {
        dataKeys: typeof data === 'object' && data ? Object.keys(data as unknown) : [],
        hasContent: (data as unknown)?.content != null,
        contentLength: ((data as unknown)?.content ?? '').length ?? 0,
        hasError: (data as unknown)?.error != null,
        dataPreview: str.length > 500 ? str.slice(0, 500) + '...' : str,
      });
    }

    return NextResponse.json(data, {
      status: response.status,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        Pragma: 'no-cache',
        Expires: '0',
        'X-Proxy-Upstream-Status': String(response.status),
      },
    });
  } catch (backendError) {
    // Backend unreachable/timeout → produce graceful fallback
    const lastUserMsg =
      (Array.isArray(body?.messages) && body!.messages!.length
        ? body!.messages![body!.messages!.length - 1]?.content
        : (body as unknown)?.message) || '';
    const fallback = createFallbackResponse(String(lastUserMsg ?? ''));
    if (VERBOSE) {
      console.log('🔍 ChatRuntime API: Backend error; returning fallback', {
        reason:
          (backendError as unknown)?.name === 'AbortError'
            ? 'timeout'
            : (backendError as Error)?.message || 'unknown',
        degraded: isDegraded,
      });
    }
    return NextResponse.json(fallback, {
      status: 200,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        Pragma: 'no-cache',
        Expires: '0',
        'X-Fallback': 'true',
        'X-Fallback-Reason':
          (backendError as unknown)?.name === 'AbortError'
            ? `timeout_${isDegraded ? TIMEOUT_DEGRADED_MS : TIMEOUT_NORMAL_MS}ms`
            : 'upstream_unreachable',
      },
    });
  }
}
