import { NextRequest, NextResponse } from 'next/server';
import { getBackendCandidates, withBackendPath } from '@/app/api/_utils/backend';

const REQUEST_TIMEOUT_MS = Number(
  process.env.NEXT_PUBLIC_CONVERSATION_TIMEOUT_MS ||
    process.env.KAREN_CONVERSATION_TIMEOUT_MS ||
    process.env.NEXT_PUBLIC_CHAT_RUNTIME_TIMEOUT_MS ||
    60_000
);

// Note: Removed 'force-dynamic' to allow static export
export const revalidate = 0;

type ConversationMessage = {
  role?: string;
  content?: string;
  [key: string]: unknown;
};

type ConversationPayload = {
  prompt?: string;
  message?: string;
  conversation_history?: ConversationMessage[];
  [key: string]: unknown;
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

function extractPrompt(payload: ConversationPayload | null): string {
  if (!payload || typeof payload !== 'object') return '';
  if (typeof payload.prompt === 'string') return payload.prompt;
  if (typeof payload.message === 'string') return payload.message;

  const history = payload.conversation_history;
  if (Array.isArray(history)) {
    for (let i = history.length - 1; i >= 0; i -= 1) {
      const entry = history[i];
      if (entry && typeof entry === 'object' && entry.role === 'user' && typeof entry.content === 'string') {
        return entry.content;
      }
    }
  }

  return '';
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

function buildFallbackResponse(prompt: string) {
  const trimmedPrompt = prompt.trim();
  const message = trimmedPrompt
    ? `I'm sorry, but I can't reach the AI services right now. Let's try again once the system recovers. (Last message: "${trimmedPrompt.slice(0, 120)}${trimmedPrompt.length > 120 ? '…' : ''}")`
    : "I'm sorry, but I can't reach the AI services right now. Let's try again once the system recovers.";

  return {
    response: message,
    requires_plugin: false,
    suggested_actions: [],
    ai_data: {
      degraded_mode: true,
      reason: 'upstream_unreachable',
      timestamp: new Date().toISOString(),
    },
    proactive_suggestion: null,
  };
}

export async function POST(request: NextRequest) {
  const headers = buildForwardHeaders(request);
  const rawBody = await request.text();
  const bodyText = rawBody.trim().length > 0 ? rawBody : '{}';

  let parsedBody: ConversationPayload | null = null;
  try {
    parsedBody = JSON.parse(bodyText) as ConversationPayload;
  } catch {
    parsedBody = null;
  }

  const candidates = getBackendCandidates();
  let lastError: unknown = null;

  for (const base of candidates) {
    const url = withBackendPath('/api/ai/conversation-processing', base);
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
      '[api/ai/conversation-processing] Falling back to degraded response',
      lastError instanceof Error ? lastError.message : lastError
    );
  }

  const fallback = buildFallbackResponse(extractPrompt(parsedBody));
  return NextResponse.json(fallback, {
    status: 200,
    headers: {
      'Cache-Control': 'no-store',
      'X-Fallback': 'conversation-processing',
      'X-Fallback-Reason':
        lastError instanceof Error && lastError.name === 'AbortError'
          ? `timeout_${REQUEST_TIMEOUT_MS}ms`
          : 'upstream_unreachable',
    },
  });
}
