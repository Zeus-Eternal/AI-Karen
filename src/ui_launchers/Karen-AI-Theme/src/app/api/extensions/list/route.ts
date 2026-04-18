import { NextRequest, NextResponse } from 'next/server';
import { proxyToBackend } from '../../_lib/backend-proxy';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const proxied = await proxyToBackend(request, '/api/extensions/list', {
    longTimeout: true,
    retryAttempts: 4,
    retryDelayMs: 300,
    retryOnStatusCodes: [502, 503, 504],
  });

  if (!proxied.ok) {
    // Catalog failures must not block login/bootstrap flows.
    return NextResponse.json([], { status: 200 });
  }

  return proxied;
}
