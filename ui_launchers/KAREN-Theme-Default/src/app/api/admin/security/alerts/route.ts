// ui_launchers/web_ui/src/app/api/admin/security/alerts/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { adminAuthMiddleware } from '@/lib/middleware/admin-auth';
import { getAdminDatabaseUtils } from '@/lib/database/admin-utils';
import type { AdminApiResponse } from '@/types/admin';

export const dynamic = 'force-dynamic';

type Severity = 'low' | 'medium' | 'high' | 'critical';
interface AlertsQuery {
  limit: number;
  offset: number;
  severity?: Severity;
  resolved?: boolean;
}

interface AlertsResult<T> {
  data: T[];
  total?: number;
}

function parseBoolean(value: string | null): boolean | undefined {
  if (value === 'true') return true;
  if (value === 'false') return false;
  return undefined;
}

function parseLimit(raw: string | null, def = 50, max = 200): number {
  const n = Number(raw ?? def);
  if (!Number.isFinite(n) || n <= 0) return def;
  return Math.min(Math.floor(n), max);
}

function parseOffset(raw: string | null): number {
  const n = Number(raw ?? 0);
  if (!Number.isFinite(n) || n < 0) return 0;
  return Math.floor(n);
}

function parseSeverity(raw: string | null): Severity | undefined {
  if (!raw) return undefined;
  const s = raw.toLowerCase();
  return ['low', 'medium', 'high', 'critical'].includes(s) ? (s as Severity) : undefined;
}

/**
 * GET /api/admin/security/alerts
 * 
 * RBAC: super_admin (via adminAuthMiddleware)
 * Query params:
 *  - limit?: number (default 50, max 200)
 *  - offset?: number (default 0)
 *  - severity?: 'low'|'medium'|'high'|'critical'
 *  - resolved?: 'true'|'false'
 */
export async function GET(request: NextRequest) {
  try {
    // AuthZ: only super_admin may list security alerts
    const authResult = await adminAuthMiddleware(request, 'super_admin');
    if (authResult instanceof NextResponse) {
      return authResult; // middleware already responded (unauthorized / forbidden)
    }

    const { searchParams } = new URL(request.url);
    const limit = parseLimit(searchParams.get('limit'));
    const offset = parseOffset(searchParams.get('offset'));
    const severity = parseSeverity(searchParams.get('severity'));
    const resolved = parseBoolean(searchParams.get('resolved'));

    const adminUtils = getAdminDatabaseUtils();

    // Fetch alerts (implementation detail lives in admin-utils)
    // Expectation: returns { data: Alert[], total?: number }
    const alerts: AlertsResult<any> = await adminUtils.getSecurityAlerts({
      limit,
      offset,
      severity,
      resolved,
    } as AlertsQuery);

    const total = typeof alerts.total === 'number' ? alerts.total : alerts.data.length + offset;
    const nextOffset = offset + alerts.data.length;
    const hasMore = nextOffset < total;

    const response: AdminApiResponse<{
      items: unknown[];
      pagination: {
        total: number;
        limit: number;
        offset: number;
        next_offset: number | null;
        has_more: boolean;
      };
      filters: {
        severity?: Severity;
        resolved?: boolean;
      };
    }> = {
      success: true,
      data: {
        items: alerts.data,
        pagination: {
          total,
          limit,
          offset,
          next_offset: hasMore ? nextOffset : null,
          has_more: hasMore,
        },
        filters: { severity, resolved },
      },
      meta: {
        message: 'Security alerts loaded',
        timestamp: new Date().toISOString(),
      },
    };

    return NextResponse.json(response, {
      status: 200,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        Pragma: 'no-cache',
        Expires: '0',
      },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return NextResponse.json(
      {
        success: false,
        error: {
          code: 'SECURITY_ALERTS_FETCH_FAILED',
          message: 'Failed to load security alerts',
          details: { error: message },
        },
      },
      { status: 500 },
    );
  }
}
