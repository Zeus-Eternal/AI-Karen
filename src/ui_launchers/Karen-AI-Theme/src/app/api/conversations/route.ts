import { NextRequest } from 'next/server';
import { proxyToBackend } from '../_lib/backend-proxy';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

function handle(request: NextRequest) {
  return proxyToBackend(request, '/api/conversations', {
    retryAttempts: 3,
    retryDelayMs: 200,
  });
}

export const GET = handle;
export const POST = handle;
export const PUT = handle;
export const DELETE = handle;
export const PATCH = handle;
export const HEAD = handle;
export const OPTIONS = handle;
