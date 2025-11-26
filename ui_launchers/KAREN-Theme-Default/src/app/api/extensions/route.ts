import { NextRequest, NextResponse } from 'next/server';
import { withBackendPath } from '@/app/api/_utils/backend';
import { getSampleExtensionsRecord } from '@/lib/extensions/sample-data';

const DEFAULT_TIMEOUT_MS = 5_000;

// Note: Removed 'force-dynamic' to allow static export
export const revalidate = 0;

type NormalizedExtensionsResponse = {
  extensions: Record<string, unknown>;
  total: number;
  user_context?: unknown;
  filters?: unknown;
  message?: unknown;
};

function buildSampleResponse(): NormalizedExtensionsResponse {
  const extensions = getSampleExtensionsRecord();
  return {
    extensions,
    total: Object.keys(extensions).length,
    message: 'Sample extension data returned by fallback handler',
  };
}

function cloneForwardHeaders(request: NextRequest): Headers {
  const headers = new Headers({
    Accept: 'application/json',
    'Content-Type': 'application/json',
  });

  const authHeader = request.headers.get('authorization');
  if (authHeader) headers.set('Authorization', authHeader);

  const cookieHeader = request.headers.get('cookie');
  if (cookieHeader) headers.set('Cookie', cookieHeader);

  const forwardableHeaders: Record<string, string> = {
    'x-session-id': 'X-Session-ID',
    'x-conversation-id': 'X-Conversation-ID',
    'x-user-id': 'X-User-ID',
    'x-request-id': 'X-Request-ID',
    'x-correlation-id': 'X-Correlation-ID',
  };

  for (const [sourceKey, targetKey] of Object.entries(forwardableHeaders)) {
    const value = request.headers.get(sourceKey);
    if (value) headers.set(targetKey, value);
  }

  return headers;
}

function toExtensionRecord(source: unknown): Record<string, unknown> | null {
  if (!source) return null;

  if (Array.isArray(source)) {
    const record: Record<string, unknown> = {};
    for (const entry of source) {
      if (entry && typeof entry === 'object') {
        const obj = entry as Record<string, unknown>;
        const key =
          typeof obj.name === 'string'
            ? obj.name
            : typeof obj.id === 'string'
            ? obj.id
            : undefined;
        if (key) {
          record[key] = obj;
        }
      }
    }
    return Object.keys(record).length > 0 ? record : null;
  }

  if (typeof source === 'object') {
    return source as Record<string, unknown>;
  }

  return null;
}

function normalizeBackendPayload(data: unknown): NormalizedExtensionsResponse | null {
  if (!data || typeof data !== 'object') {
    return null;
  }

  const payload = data as Record<string, unknown>;
  const recordSource = payload.extensions ?? data;
  const extensions = toExtensionRecord(recordSource);

  if (!extensions) {
    return null;
  }

  const totalValue = payload.total;
  const total =
    typeof totalValue === 'number'
      ? totalValue
      : typeof totalValue === 'string' && !Number.isNaN(Number(totalValue))
      ? Number(totalValue)
      : Object.keys(extensions).length;

  const normalized: NormalizedExtensionsResponse = {
    extensions,
    total,
  };

  if ('user_context' in payload) {
    normalized.user_context = payload.user_context;
  }
  if ('filters' in payload) {
    normalized.filters = payload.filters;
  }
  if ('message' in payload) {
    normalized.message = payload.message;
  }

  return normalized;
}

async function parseJsonResponse(response: Response): Promise<unknown> {
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    return null;
  }

  try {
    return await response.json();
  } catch {
    return null;
  }
}

function buildFallbackResponse() {
  return NextResponse.json(buildSampleResponse(), {
    status: 200,
    headers: {
      'Cache-Control': 'no-store',
      'X-Extensions-Fallback': 'sample-data',
    },
  });
}

export async function GET(request: NextRequest) {
  if (process.env.NEXT_PHASE === 'phase-production-build') {
    return buildFallbackResponse();
  }

  const timeoutMs = Number(
    process.env.NEXT_PUBLIC_EXTENSIONS_TIMEOUT_MS ||
      process.env.KAREN_EXTENSIONS_TIMEOUT_MS ||
      DEFAULT_TIMEOUT_MS,
  );

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const search = request.nextUrl.search || '';
    const backendUrl = withBackendPath(`/extensions${search}`);
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: cloneForwardHeaders(request),
      signal: controller.signal,
      cache: 'no-store',
    });

    if (response.status === 401 || response.status === 403) {
      // During the grace period after login, return sample data instead of 401
      // to prevent auth interceptor from triggering logout
      console.warn('[GET /api/extensions] Backend returned auth error, using fallback', {
        status: response.status,
      });
      return buildFallbackResponse();
    }

    if (!response.ok) {
      const body = await parseJsonResponse(response);
      if (body) {
        console.warn('[GET /api/extensions] Backend returned error payload', {
          status: response.status,
          statusText: response.statusText,
        });
      } else {
        console.warn('[GET /api/extensions] Backend request failed', {
          status: response.status,
          statusText: response.statusText,
        });
      }
      return buildFallbackResponse();
    }

    const data = await parseJsonResponse(response);
    const normalized = normalizeBackendPayload(data);

    if (!normalized) {
      console.warn('[GET /api/extensions] Backend payload could not be normalized');
      return buildFallbackResponse();
    }

    return NextResponse.json(normalized, {
      status: 200,
      headers: {
        'Cache-Control': 'no-store',
      },
    });
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      console.warn('[GET /api/extensions] Backend request timed out');
    } else {
      console.error('[GET /api/extensions] Unexpected error', error);
    }
    return buildFallbackResponse();
  } finally {
    clearTimeout(timeoutId);
  }
}
