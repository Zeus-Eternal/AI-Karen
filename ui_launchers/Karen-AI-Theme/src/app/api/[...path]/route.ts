import { NextRequest } from 'next/server';
import { proxyToBackend } from '../_lib/backend-proxy';

/**
 * Catch-all API Route Handler
 * 
 * In Next.js 15 with Turbopack and Docker environments, standard next.config.ts rewrites 
 * can sometimes be unreliable or shadowed by internal routing behavior.
 * 
 * This catch-all route at /api/[...path] ensures that ANY /api/* request
 * that doesn't have a more specific local handler in src/app/api/... 
 * is correctly proxied to the backend AI-Karen engine.
 */

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

async function handle(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  const fullPath = path.join('/');
  
  // Delegate the actual proxy logic to the existing backend-proxy utility.
  // The backend expects routes with the /api prefix (e.g., /api/auth/me).
  // Retry on 502 Bad Gateway errors to handle startup timing issues.
  return proxyToBackend(request, `/api/${fullPath}`, { retryOnStatusCodes: [502] });
}

export const GET = handle;
export const POST = handle;
export const PUT = handle;
export const DELETE = handle;
export const PATCH = handle;
export const HEAD = handle;
export const OPTIONS = handle;
