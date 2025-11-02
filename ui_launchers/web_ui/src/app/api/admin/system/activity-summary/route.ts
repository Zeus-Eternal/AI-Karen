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
/**
 * GET /api/admin/system/activity-summary - Get activity summary
 */
export const GET = requireAdmin(async (request: NextRequest, context) => {
  try {
    const { searchParams } = new URL(request.url);
    const period = searchParams.get('period') || 'week';
    const adminUtils = getAdminDatabaseUtils();
    // Calculate date range based on period
    const now = new Date();
    let startDate: Date;
    switch (period) {
      case 'today':
        startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        break;
      case 'week':
        startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        break;
      case 'month':
        startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        break;
      default:
        startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    }
    // Get audit logs for the period
    const auditLogsResult = await adminUtils.getAuditLogs({
      start_date: startDate,
      end_date: now
    }, {
      page: 1,
      limit: 1000, // Get more logs for analysis
      sort_by: 'timestamp',
      sort_order: 'desc'

    const auditLogs = auditLogsResult.data;
    // Count user registrations (user.create actions)
    const userRegistrations = auditLogs.filter(log => 
      log.action === 'user.create'
    ).length;
    // Count admin actions (any action by admin/super_admin users)
    const adminActions = auditLogs.filter(log => 
      log.action.startsWith('admin.') || 
      log.action.startsWith('user.') ||
      log.action.startsWith('system.')
    ).length;
    // Count successful logins
    const successfulLogins = auditLogs.filter(log => 
      log.action === 'user.login' && 
      log.details?.success === true
    ).length;
    // Count failed logins
    const failedLogins = auditLogs.filter(log => 
      log.action === 'user.login_failed' || 
      (log.action === 'user.login' && log.details?.success === false)
    ).length;
    // Count security events (approximate from audit logs)
    const securityEvents = auditLogs.filter(log => 
      log.action.includes('security') ||
      log.action.includes('failed') ||
      log.action.includes('locked')
    ).length;
    // Get top actions
    const actionCounts: Record<string, number> = {};
    auditLogs.forEach(log => {
      actionCounts[log.action] = (actionCounts[log.action] || 0) + 1;

    const topActions = Object.entries(actionCounts)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 10)
      .map(([action, count]) => ({ action, count }));
    // Get top users by activity
    const userCounts: Record<string, { email: string; count: number }> = {};
    auditLogs.forEach(log => {
      if (log.user?.email) {
        if (!userCounts[log.user_id]) {
          userCounts[log.user_id] = { email: log.user.email, count: 0 };
        }
        userCounts[log.user_id].count++;
      }

    const topUsers = Object.entries(userCounts)
      .sort(([, a], [, b]) => b.count - a.count)
      .slice(0, 10)
      .map(([user_id, data]) => ({
        user_id,
        email: data.email,
        action_count: data.count
      }));
    const activitySummary: ActivitySummary = {
      period: period as 'today' | 'week' | 'month',
      user_registrations: userRegistrations,
      admin_actions: adminActions,
      security_events: securityEvents,
      failed_logins: failedLogins,
      successful_logins: successfulLogins,
      top_actions: topActions,
      top_users: topUsers
    };
    const response: AdminApiResponse<ActivitySummary> = {
      success: true,
      data: activitySummary,
      meta: {
        period,
        start_date: startDate.toISOString(),
        end_date: now.toISOString(),
        total_audit_logs: auditLogs.length
      }
    };
    return NextResponse.json(response);
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: {
        code: 'ACTIVITY_SUMMARY_FAILED',
        message: 'Failed to retrieve activity summary',
        details: { error: error instanceof Error ? error.message : 'Unknown error' }
      }
    } as AdminApiResponse<never>, { status: 500 });
  }
