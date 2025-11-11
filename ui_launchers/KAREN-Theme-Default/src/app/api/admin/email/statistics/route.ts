// ui_launchers/web_ui/src/app/api/admin/email/statistics/route.ts
/**
 * Email Statistics API
 *
 * API endpoint for retrieving email delivery statistics, analytics,
 * and performance metrics for admin monitoring.
 */
import { NextRequest, NextResponse } from 'next/server';
import { adminAuthMiddleware } from '@/lib/middleware/admin-auth';
import { deliveryStatusManager } from '@/lib/email/delivery-tracker';
import { auditLogger } from '@/lib/audit/audit-logger';
import type { AdminApiResponse } from '@/types/admin';

export const dynamic = 'force-dynamic';

type Role = 'admin' | 'super_admin';

interface StatisticsFilters {
  start_date?: string;
  end_date?: string;
  template_id?: string;
}

function parseIsoDate(raw: string | null): Date | undefined {
  if (!raw) return undefined;
  const d = new Date(raw);
  return Number.isFinite(d.getTime()) ? d : undefined;
}

function sanitizeTemplateId(raw: string | null): string | undefined {
  if (!raw) return undefined;
  const v = raw.trim();
  // keep it permissive but safe (UUID-like, slug, or simple id). Adjust to your schema if needed.
  if (/^[A-Za-z0-9_\-:.]{1,128}$/.test(v)) return v;
  return undefined;
}

/**
 * GET /api/admin/email/statistics
 * RBAC: admin | super_admin
 * Query:
 *  - start_date?: ISO-8601 date/time
 *  - end_date?: ISO-8601 date/time
 *  - template_id?: string (UUID/slug/id)
 */
export async function GET(request: NextRequest) {
  try {
    // AuthZ: allow admin and super_admin
    const authResult = await adminAuthMiddleware(request, ['admin', 'super_admin'] as Role[]);
    // If your middleware returns a NextResponse on failure, honor it
    if (authResult instanceof NextResponse) {
      return authResult;
    }
    // Else assume an object with { success, status, error, user }
    if (!('success' in authResult) || !authResult.success) {
      const status = 'status' in authResult ? (authResult as unknown).status ?? 401 : 401;
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'UNAUTHORIZED',
            message: 'Unauthorized',
            details: { reason: ('error' in authResult && (authResult as unknown).error) || 'RBAC check failed' },
          },
        } satisfies AdminApiResponse<never>,
        { status },
      );
    }

    const { searchParams } = new URL(request.url);

    const startDate = parseIsoDate(searchParams.get('start_date'));
    const endDate = parseIsoDate(searchParams.get('end_date'));
    const templateId = sanitizeTemplateId(searchParams.get('template_id'));

    // Validate date ordering
    if (startDate && endDate && startDate > endDate) {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'INVALID_DATE_RANGE',
            message: 'Start date must be before end date',
            details: { start_date: startDate.toISOString(), end_date: endDate.toISOString() },
          },
        } satisfies AdminApiResponse<never>,
        { status: 400 },
      );
    }

    // Validate template id (if provided)
    if (searchParams.get('template_id') && !templateId) {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'INVALID_TEMPLATE_ID',
            message: 'Invalid template_id format',
          },
        } satisfies AdminApiResponse<never>,
        { status: 400 },
      );
    }

    // Fetch delivery statistics
    const statistics = await deliveryStatusManager.getDeliveryStatistics(startDate, endDate, templateId);

    // Audit (best-effort)
    try {
      await auditLogger.log(
        authResult.user?.user_id || 'unknown',
        'email_statistics_viewed',
        'email_statistics',
        {
          resourceId: templateId,
          details: {
            start_date: startDate?.toISOString(),
            end_date: endDate?.toISOString(),
            template_id: templateId,
            total_sent: statistics?.total_sent ?? 0,
          },
          request,
        },
      );
    } catch {
      // swallow audit errors; do not break telemetry view
    }

    const payload: AdminApiResponse<{
      statistics: unknown;
      filters: StatisticsFilters;
      generated_at: string;
    }> = {
      success: true,
      data: {
        statistics,
        filters: {
          start_date: startDate?.toISOString(),
          end_date: endDate?.toISOString(),
          template_id: templateId,
        },
        generated_at: new Date().toISOString(),
      },
      meta: {
        message: 'Email statistics generated',
      },
    };

    return NextResponse.json(payload, {
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
          code: 'EMAIL_STATISTICS_FAILED',
          message: 'Failed to get email statistics',
          details: { error: message },
        },
      } satisfies AdminApiResponse<never>,
      { status: 500 },
    );
  }
}
