import { NextResponse } from 'next/server';

import { logger } from '@/lib/logger';

/**
 * Production-ready health signal for the Kari web UI.
 */
export async function GET() {
  const environment = process.env.NODE_ENV ?? 'unknown';
  const timestamp = new Date().toISOString();
  const uptimeSeconds = Math.round(process.uptime());

  const backendConfigured = Boolean(
    process.env.KAREN_BACKEND_URL || process.env.NEXT_PUBLIC_KAREN_BACKEND_URL,
  );
  const authenticationConfigured = process.env.SIMPLE_AUTH_ENABLED !== 'false';

  const responseBody = {
    status: backendConfigured ? 'ok' : 'degraded',
    environment,
    timestamp,
    uptimeSeconds,
    checks: {
      backend: {
        configured: backendConfigured,
      },
      authentication: {
        simpleAuthEnabled: authenticationConfigured,
      },
    },
  } as const;

  logger.info('Served production health snapshot', {
    environment,
    backendConfigured,
    authenticationConfigured,

  return NextResponse.json(responseBody, {
    status: backendConfigured ? 200 : 503,
    headers: {
      'Cache-Control': 'no-store, max-age=0',
      'Content-Type': 'application/json',
    },

}
