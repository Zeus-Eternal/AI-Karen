// app/api/health/route.ts
import { NextResponse } from 'next/server';
import { logger } from '@/lib/logger';

/**
 * Production-grade health snapshot for the Kari web UI.
 * Reports environment, uptime, and configuration readiness.
 */
export async function GET() {
  const environment = process.env.NODE_ENV ?? 'unknown';
  const timestamp = new Date().toISOString();
  const uptimeSeconds = Math.round(process.uptime());

  const backendConfigured = Boolean(
    process.env.KAREN_BACKEND_URL || process.env.NEXT_PUBLIC_KAREN_BACKEND_URL
  );
  const authenticationConfigured = process.env.SIMPLE_AUTH_ENABLED !== 'false';

  const status = backendConfigured ? 'ok' : 'degraded';
  const statusCode = backendConfigured ? 200 : 503;

  const responseBody = {
    status,
    environment,
    timestamp,
    uptimeSeconds,
    checks: {
      backend: { configured: backendConfigured },
      authentication: { simpleAuthEnabled: authenticationConfigured },
    },
  } as const;

  // Structured logging
  logger.info('Served production health snapshot', {
    environment,
    backendConfigured,
    authenticationConfigured,
    uptimeSeconds,
    status,
  });

  return NextResponse.json(responseBody, {
    status: statusCode,
    headers: {
      'Cache-Control': 'no-store, max-age=0',
      'Content-Type': 'application/json',
    },
  });
}
