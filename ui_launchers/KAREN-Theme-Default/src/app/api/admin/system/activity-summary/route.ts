/**
 * Activity Summary API Route
 * GET /api/admin/system/activity-summary - Get activity summary for dashboard
 *
 * Requirements: 4.6, 7.3
 */

import { NextRequest, NextResponse } from 'next/server';
import { requireAdmin } from '@/lib/middleware/admin-auth';
import { getAdminDatabaseUtils } from '@/lib/database/admin-utils';
import type { AdminApiResponse, ActivitySummary } from '@/types/admin';

type Period = 'today' | 'week' | 'month';

function noStore(init?: ResponseInit): ResponseInit {
  return {
    ...(init || {}),
    headers: {
      ...(init?.headers || {}),
      'Cache-Control': 'no-cache, no-store, must-revalidate',
      'Pragma': 'no-cache',
      'Expires': '0',
      'Content-Type': 'application/json; charset=utf-8',
    },
  };
}

function getPeriodAndRange(periodParam?: string): { period: Period; startDate: Date; endDate: Date } {
  const now = new Date();
  const normalized = (periodParam || 'week').toLowerCase() as Period;
  let startDate: Date;

  switch (normalized) {
    case 'today': {
      startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      break;
    }
    case 'month': {
      startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
      break;
    }
    case 'week':
    default: {
      startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      break;
    }
  }

  return { period: ['today', 'week', 'month'].includes(normalized) ? normalized : 'week', startDate, endDate: now };
}

export const GET = requireAdmin(async (request: NextRequest, _context) => {
  try {
    const { searchParams } = new URL(request.url);
    const { period, startDate, endDate } = getPeriodAndRange(searchParams.get('period') || undefined);

    // Optional limit override for analysis—clamped for safety
    const rawLimit = parseInt(searchParams.get('limit') || '1000', 10);
    const limit = Number.isFinite(rawLimit) ? Math.max(100, Math.min(rawLimit, 2000)) : 1000;

    const adminUtils = getAdminDatabaseUtils();

    // Pull audit logs for analysis window
    const auditLogsResult = await adminUtils.getAuditLogs(
      { start_date: startDate, end_date: endDate },
      { page: 1, limit, sort_by: 'timestamp', sort_order: 'desc' }
    );

    const auditLogs = Array.isArray(auditLogsResult?.data) ? auditLogsResult.data : [];

    // --- Metrics -------------------------------------------------------------

    // 1) User registrations
    const userRegistrations = auditLogs.filter((log: unknown) => log?.action === 'user.create').length;

    // 2) Admin actions (broad: admin.*, user.*, system.*)
    const adminActions = auditLogs.filter((log: unknown) => {
      const a = String(log?.action || '');
      return a.startsWith('admin.') || a.startsWith('user.') || a.startsWith('system.');
    }).length;

    // 3) Logins
    const successfulLogins = auditLogs.filter(
      (log: unknown) => log?.action === 'user.login' && Boolean(log?.details?.success) === true
    ).length;

    const failedLogins = auditLogs.filter((log: unknown) => {
      const a = String(log?.action || '');
      return a === 'user.login_failed' || (a === 'user.login' && Boolean(log?.details?.success) === false);
    }).length;

    // 4) Security-ish events (approx)
    const securityEvents = auditLogs.filter((log: unknown) => {
      const a = String(log?.action || '').toLowerCase();
      return a.includes('security') || a.includes('failed') || a.includes('locked');
    }).length;

    // 5) Top actions
    const actionCounts: Record<string, number> = {};
    for (const log of auditLogs) {
      const a = String(log?.action || 'unknown');
      actionCounts[a] = (actionCounts[a] || 0) + 1;
    }
    const topActions = Object.entries(actionCounts)
      .sort(([, A], [, B]) => (B as number) - (A as number))
      .slice(0, 10)
      .map(([action, count]) => ({ action, count: Number(count) }));

    // 6) Top users by activity
    const userCounts: Record<
      string,
      { email: string; count: number }
    > = {};
    for (const log of auditLogs) {
      const userId = String(log?.user_id || '');
      const email = String(log?.user?.email || '') || 'unknown';
      if (!userId) continue;
      if (!userCounts[userId]) userCounts[userId] = { email, count: 0 };
      userCounts[userId].count++;
    }
    const topUsers = Object.entries(userCounts)
      .sort(([, A], [, B]) => (B.count as number) - (A.count as number))
      .slice(0, 10)
      .map(([user_id, data]) => ({ user_id, email: data.email, action_count: data.count }));

    const activitySummary: ActivitySummary = {
      period,
      user_registrations: userRegistrations,
      admin_actions: adminActions,
      security_events: securityEvents,
      failed_logins: failedLogins,
      successful_logins: successfulLogins,
      top_actions: topActions,
      top_users: topUsers,
    };

    const response: AdminApiResponse<ActivitySummary> = {
      success: true,
      data: activitySummary,
      meta: {
        period,
        start_date: startDate.toISOString(),
        end_date: endDate.toISOString(),
        total_audit_logs: auditLogs.length,
        limit_applied: limit,
        note:
          auditLogs.length === limit
            ? 'Results truncated to analysis limit; widen window or increase limit (max 2000) for finer granularity.'
            : undefined,
      },
    };

    return NextResponse.json(response, noStore());
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: {
          code: 'ACTIVITY_SUMMARY_FAILED',
          message: 'Failed to retrieve activity summary',
          details: { error: error instanceof Error ? error.message : 'Unknown error' },
        },
      } as AdminApiResponse<never>,
      noStore({ status: 500 })
    );
  }
});
