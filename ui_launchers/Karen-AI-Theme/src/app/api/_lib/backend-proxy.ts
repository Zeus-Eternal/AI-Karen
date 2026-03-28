import { NextRequest, NextResponse } from 'next/server';

const DEFAULT_BACKEND_URL = process.env.KAREN_BACKEND_URL || 'http://api:8000';
const DEFAULT_TIMEOUT_MS = Number.parseInt(process.env.NEXT_PUBLIC_API_PROXY_TIMEOUT_MS || '60000', 10);
const LONG_TIMEOUT_MS = Number.parseInt(process.env.NEXT_PUBLIC_API_PROXY_LONG_TIMEOUT_MS || '180000', 10);
const RETRYABLE_PROXY_ERROR_CODES = new Set([
  'ECONNREFUSED',
  'ECONNRESET',
  'EPIPE',
  'UND_ERR_CONNECT_TIMEOUT',
  'UND_ERR_SOCKET',
]);

function getBackendBaseUrl(): string {
  return DEFAULT_BACKEND_URL.replace(/\/$/, '');
}

function sanitizeHeaders(headers: Headers, backendBaseUrl: string): Headers {
  const nextHeaders = new Headers(headers);
  const backendHost = new URL(backendBaseUrl).host;

  nextHeaders.delete('host');
  nextHeaders.set('x-forwarded-host', headers.get('host') || backendHost);
  nextHeaders.set('x-forwarded-proto', 'http');
  return nextHeaders;
}

async function buildInit(
  request: NextRequest,
  backendBaseUrl: string,
  timeoutMs: number,
  bodyOverride?: string,
): Promise<RequestInit> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  const body =
    request.method === 'GET' || request.method === 'HEAD'
      ? undefined
      : bodyOverride ?? await request.text();

  return {
    method: request.method,
    headers: sanitizeHeaders(request.headers, backendBaseUrl),
    body,
    cache: 'no-store',
    redirect: 'manual',
    signal: controller.signal,
    // @ts-expect-error Node/undici extension supported in Next runtime.
    duplex: body ? 'half' : undefined,
    next: { revalidate: 0 },
    // @ts-expect-error attach for cleanup in proxyToBackend.
    __timeout: timeout,
  };
}

function getTimeoutHandle(init: RequestInit): ReturnType<typeof setTimeout> | undefined {
  return (init as RequestInit & { __timeout?: ReturnType<typeof setTimeout> }).__timeout;
}

function clearInitTimeout(init: RequestInit): void {
  const timeout = getTimeoutHandle(init);
  if (timeout) {
    clearTimeout(timeout);
  }
}

function isRetryableProxyError(error: unknown): boolean {
  if (!(error instanceof Error)) {
    return false;
  }

  const errorWithCode = error as Error & { code?: string; cause?: { code?: string } };
  const code = errorWithCode.code || errorWithCode.cause?.code;
  return Boolean(code && RETRYABLE_PROXY_ERROR_CODES.has(code));
}

async function sleep(ms: number): Promise<void> {
  await new Promise((resolve) => setTimeout(resolve, ms));
}

export async function proxyToBackend(
  request: NextRequest,
  upstreamPath: string,
  options?: { longTimeout?: boolean; retryAttempts?: number; retryDelayMs?: number; rawBody?: string },
): Promise<NextResponse> {
  const backendBaseUrl = getBackendBaseUrl();
  const timeoutMs = options?.longTimeout ? LONG_TIMEOUT_MS : DEFAULT_TIMEOUT_MS;
  const retryAttempts = Math.max(1, options?.retryAttempts ?? 2);
  const retryDelayMs = Math.max(0, options?.retryDelayMs ?? 250);
  const upstreamUrl = `${backendBaseUrl}${upstreamPath}${request.nextUrl.search}`;
  let init = await buildInit(request, backendBaseUrl, timeoutMs, options?.rawBody);

  try {
    let upstream: Response | undefined;
    let lastError: unknown;

    for (let attempt = 1; attempt <= retryAttempts; attempt += 1) {
      try {
        upstream = await fetch(upstreamUrl, init);
        lastError = undefined;
        break;
      } catch (error) {
        clearInitTimeout(init);
        lastError = error;

        const canRetry = isRetryableProxyError(error) && attempt < retryAttempts;
        if (!canRetry) {
          throw error;
        }

        await sleep(retryDelayMs * attempt);
        init = await buildInit(request, backendBaseUrl, timeoutMs, options?.rawBody);
      }
    }

    if (!upstream) {
      throw lastError instanceof Error ? lastError : new Error('Unknown proxy error');
    }

    const body = await upstream.text();
    const headers = new Headers(upstream.headers);
    clearInitTimeout(init);

    headers.delete('content-encoding');
    headers.delete('content-length');
    headers.delete('transfer-encoding');
    headers.delete('connection');
    headers.set('cache-control', 'no-store');

    return new NextResponse(body, {
      status: upstream.status,
      headers,
    });
  } catch (error) {
    clearInitTimeout(init);

    const detail =
      error instanceof Error && error.name === 'AbortError'
        ? `Upstream request timed out after ${timeoutMs}ms`
        : error instanceof Error
          ? error.message
          : 'Unknown proxy error';

    return NextResponse.json(
      {
        detail: `Failed to proxy ${upstreamPath} to backend`,
        error: detail,
      },
      { status: 502 },
    );
  }
}
