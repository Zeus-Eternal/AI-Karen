import { NextRequest } from 'next/server';
import { proxyToBackend } from '../../_lib/backend-proxy';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

async function handle(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> },
) {
  const { path } = await params;
  const fullPath = path.join('/');

  return proxyToBackend(request, `/api/conversations/${fullPath}`, {
    longTimeout: true,
    retryAttempts: 4,
    retryDelayMs: 300,
  });
}

export const GET = handle;
export const POST = handle;
export const PUT = handle;
export const DELETE = handle;
export const PATCH = handle;
export const HEAD = handle;
export const OPTIONS = handle;
