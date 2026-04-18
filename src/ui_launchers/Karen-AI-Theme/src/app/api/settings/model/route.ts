import { NextRequest } from 'next/server';

import { proxyToBackend } from '../../_lib/backend-proxy';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  return proxyToBackend(request, '/api/settings/model', {
    retryAttempts: 3,
    retryDelayMs: 250,
    retryOnStatusCodes: [500, 502, 503, 504],
  });
}

export async function PUT(request: NextRequest) {
  return proxyToBackend(request, '/api/settings/model', {
    retryAttempts: 3,
    retryDelayMs: 250,
    retryOnStatusCodes: [500, 502, 503, 504],
  });
}
