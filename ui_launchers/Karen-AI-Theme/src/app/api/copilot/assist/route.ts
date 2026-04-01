import { NextRequest, NextResponse } from 'next/server';

import { proxyToBackend } from '../../_lib/backend-proxy';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

type ResponseSnapshot = {
  body: string;
  headers: Array<[string, string]>;
  status: number;
};

const inFlightAssistRequests = new Map<string, Promise<ResponseSnapshot>>();

function buildAssistDedupKey(rawBody: string): string {
  try {
    const payload = JSON.parse(rawBody) as Record<string, unknown>;
    const sessionId = String(payload.session_id || '');
    const userId = String(payload.user_id || '');
    const message = String(payload.message || '').trim();

    if (sessionId && message) {
      return `${sessionId}::${userId}::${message}`;
    }
  } catch {
    // Fall back to the raw request body if parsing fails.
  }

  return rawBody;
}

function snapshotToResponse(snapshot: ResponseSnapshot): NextResponse {
  return new NextResponse(snapshot.body, {
    status: snapshot.status,
    headers: new Headers(snapshot.headers),
  });
}

export async function POST(request: NextRequest) {
  const rawBody = await request.text();
  const dedupeKey = buildAssistDedupKey(rawBody);
  const existingRequest = inFlightAssistRequests.get(dedupeKey);

  if (existingRequest) {
    return snapshotToResponse(await existingRequest);
  }

  const upstreamRequest = proxyToBackend(request, '/api/copilot/assist', {
    longTimeout: true,
    retryAttempts: 4,
    retryDelayMs: 500,
    retryOnStatusCodes: [500, 502, 503, 504],
    rawBody,
  })
    .then(async (response) => ({
      body: await response.text(),
      headers: Array.from(response.headers.entries()),
      status: response.status,
    }))
    .finally(() => {
      inFlightAssistRequests.delete(dedupeKey);
    });

  inFlightAssistRequests.set(dedupeKey, upstreamRequest);

  return snapshotToResponse(await upstreamRequest);
}
