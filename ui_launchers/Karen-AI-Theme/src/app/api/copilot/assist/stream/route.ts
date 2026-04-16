import { NextRequest, NextResponse } from 'next/server';
import { getBackendBaseUrl, sanitizeHeaders } from '../../../_lib/backend-proxy';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function POST(request: NextRequest) {
  const backendBaseUrl = getBackendBaseUrl();
  const upstreamUrl = `${backendBaseUrl}/api/copilot/assist/stream`;

  try {
    const rawBody = await request.text();
    const headers = sanitizeHeaders(request.headers, backendBaseUrl);

    const upstream = await fetch(upstreamUrl, {
      method: 'POST',
      headers,
      body: rawBody,
      cache: 'no-store',
      redirect: 'manual',
      signal: request.signal,
      // @ts-expect-error Node/undici extension supported in Next runtime.
      duplex: 'half',
    });

    if (!upstream.ok) {
      const errorBody = await upstream.text().catch(() => 'Upstream error');
      console.error(
        `[StreamProxy] Upstream returned ${upstream.status}: ${errorBody.slice(0, 200)}`,
      );
      return new NextResponse(errorBody, {
        status: upstream.status,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    if (!upstream.body) {
      return new NextResponse('No response body from upstream', { status: 502 });
    }

    const responseHeaders = new Headers();
    responseHeaders.set('Content-Type', 'text/event-stream');
    responseHeaders.set('Cache-Control', 'no-cache');
    responseHeaders.set('Connection', 'keep-alive');
    responseHeaders.set('X-Accel-Buffering', 'no');

    const correlationId = upstream.headers.get('x-correlation-id');
    if (correlationId) {
      responseHeaders.set('X-Correlation-Id', correlationId);
    }

    return new NextResponse(upstream.body, {
      status: upstream.status,
      headers: responseHeaders,
    });
  } catch (error) {
    console.error('[StreamProxy] Failed to proxy stream request:', error);
    const detail =
      error instanceof Error && error.name === 'AbortError'
        ? 'Stream request was cancelled'
        : error instanceof Error
          ? error.message
          : 'Unknown proxy error';

    return NextResponse.json(
      { detail: 'Failed to proxy stream to backend', error: detail },
      { status: 502 },
    );
  }
}
