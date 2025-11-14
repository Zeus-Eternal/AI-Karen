import { NextRequest, NextResponse } from 'next/server';
import { adminAuthMiddleware } from '@/lib/middleware/admin-auth';
import { getAdminUtils } from '@/lib/database/admin-utils';
import { getAuditLogger } from '@/lib/audit/audit-logger';
import type { BlockedIpEntry, SecurityAlert } from '@/lib/database/admin-utils';
import type { AuditLogger } from '@/lib/audit/audit-logger';
import type { AdminDatabaseUtils } from '@/lib/database/admin-utils';
import type { User, UserStatistics, AuditLog } from '@/types/admin';

/**
 * Security Report API
 * GET /api/admin/security/report?format=json|csv&days=NUMBER
 *
 * - Auth: super_admin required
 * - Formats: json (default), csv
 * - Validations: days ∈ [1, 365]
 * - Observability: audit log emitted on success and error
 * - Headers: no-store, CSV attachment when requested
 */

type ReportFormat = 'json' | 'csv';

interface ReportSummary {
  reportPeriod: {
    startDate: string;
    endDate: string;
    days: number;
  };
  securityOverview: {
    totalAlerts: number;
    criticalAlerts: number;
    highAlerts: number;
    resolvedAlerts: number;
    blockedIPs: number;
    failedLogins: number;
  };
  userActivity: {
    totalUsers: number;
    activeUsers: number;
    newUsers: number;
    adminUsers: number;
  };
  systemHealth: {
    overallStatus: string;
    uptime: string | number;
    lastIncident: string | null;
  };
}

interface ReportData {
  generatedAt: string;
  summary: ReportSummary;
  details: {
    securityAlerts: SecurityAlert[];
    alertsByType: Record<string, number>;
    topBlockedIPs: BlockedIpEntry[];
    recentAdminActions: AuditLog[];
    failedLoginTrends: Array<{ date: string; count: number; uniqueIPs: number }>;
  };
  recommendations: Array<{
    priority: 'low' | 'medium' | 'high' | 'critical';
    category: string;
    title: string;
    description: string;
    action: string;
  }>;
}

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const startedAt = Date.now();
  const ip =
    request.headers.get('x-forwarded-for') ||
    request.headers.get('x-real-ip') ||
    'unknown';

  try {
    // 1) RBAC / Auth
    const authResult = await adminAuthMiddleware(request, 'super_admin');
    if (authResult instanceof NextResponse) return authResult;

    const { user: currentUser } = authResult || {};
    if (!currentUser?.user_id) {
      return NextResponse.json({ error: 'User not found' }, { status: 401 });
    }

    // 2) Input parsing / validation
    const { searchParams } = new URL(request.url);
    const formatParam = (searchParams.get('format') || 'json').toLowerCase();
    const format: ReportFormat = formatParam === 'csv' ? 'csv' : 'json';

    const daysRaw = searchParams.get('days') || '30';
    const daysParsed = Number.parseInt(daysRaw, 10);
    const days =
      Number.isFinite(daysParsed) && daysParsed >= 1 && daysParsed <= 365
        ? daysParsed
        : 30;

    const adminUtils = getAdminUtils();
    const auditLogger = getAuditLogger();

    // 3) Build report payload
    const reportData = await generateSecurityReport(adminUtils, days);

    // 4) Audit log (success)
    await safeAudit(auditLogger, {
      userId: currentUser.user_id,
      event: 'security.report.generate',
      entityType: 'security_report',
      details: {
        format,
        daysCovered: days,
        reportSizeBytes: byteLengthOf(reportData),
        durationMs: Date.now() - startedAt,
      },
      ip,
      request,
    });

    // 5) Respond
    const securityHeaders = {
      'Cache-Control': 'no-store',
      'X-Content-Type-Options': 'nosniff',
      'Content-Security-Policy': "default-src 'none'",
      'X-Frame-Options': 'DENY',
    } as const;

    if (format === 'json') {
      return NextResponse.json(reportData, { headers: securityHeaders });
    }

    // CSV
    const csv = generateCSVReport(reportData);
    const filename = `security-report-${new Date()
      .toISOString()
      .split('T')[0]}.csv`;

    return new NextResponse(csv, {
      headers: {
        ...securityHeaders,
        'Content-Type': 'text/csv; charset=utf-8',
        'Content-Disposition': `attachment; filename="${filename}"`,
      },
    });
  } catch (error: unknown) {
    // Audit log (error)
    try {
      const auditLogger = getAuditLogger();
      const errorMessage =
        error instanceof Error ? error.message : String(error ?? 'Unknown error');
      await safeAudit(auditLogger, {
        userId: 'unknown',
        event: 'security.report.error',
        entityType: 'security_report',
        details: {
          error: errorMessage,
        },
        ip: 'unknown',
        request,
      });
    } catch {
      // swallow audit failure silently
    }

    return NextResponse.json(
      { error: 'Failed to generate security report' },
      { status: 500 }
    );
  }
}

/** Helpers */

function byteLengthOf(obj: unknown): number {
  try {
    return Buffer.byteLength(JSON.stringify(obj), 'utf8');
  } catch {
    return 0;
  }
}

async function safeAudit(
  auditLogger: AuditLogger,
  args: {
    userId: string;
    event: string;
    entityType: string;
    details: Record<string, unknown>;
    ip: string;
    request: NextRequest;
  }
) {
  try {
    await auditLogger.log(args.userId, args.event, args.entityType, {
      details: args.details,
      request: args.request,
      ip_address: args.ip,
    });
  } catch {
    // ignore audit write failure
  }
}

/**
 * Generate comprehensive security report data
 */
async function generateSecurityReport(adminUtils: AdminDatabaseUtils, days: number): Promise<ReportData> {
  const endDate = new Date();
  const startDate = new Date();
  startDate.setDate(startDate.getDate() - days);

  const [
    securityAlertsResult,
    blockedIPsResult,
    auditLogsResult,
  ] = await Promise.all([
    adminUtils.getSecurityAlerts({ limit: 1000, offset: 0 }),
    adminUtils.getBlockedIPs({ limit: 1000, offset: 0 }),
    adminUtils.getAuditLogs(
      { start_date: startDate, end_date: endDate },
      { page: 1, limit: 1000, sort_by: 'timestamp', sort_order: 'desc' }
    ),
  ]);

  const securityAlerts = securityAlertsResult.data;
  const blockedIPs = blockedIPsResult.data;
  const auditLogs: AuditLog[] = Array.isArray(auditLogsResult?.data)
    ? (auditLogsResult.data as AuditLog[])
    : [];

  const failedLoginEntries = auditLogs
    .filter((log) => {
      const action = String(log.action || '').toLowerCase();
      if (action === 'user.login_failed') return true;
      if (action === 'user.login' && log.details?.success === false) return true;
      return false;
    })
    .map((log) => ({
      timestamp: log.timestamp instanceof Date ? log.timestamp.toISOString() : String(log.timestamp),
      ipAddress: log.ip_address ?? undefined,
    }));

  const failedLogins = failedLoginEntries.length;

  const recentAdminActions = auditLogs
    .filter((log) => {
      const action = String(log.action || '').toLowerCase();
      return action.startsWith('admin.') || action.startsWith('user.') || action.startsWith('system.');
    })
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    .slice(0, 50);

  const userStats = await collectUserStatistics(adminUtils);

  const summary: ReportSummary = {
    reportPeriod: {
      startDate: startDate.toISOString(),
      endDate: endDate.toISOString(),
      days,
    },
    securityOverview: {
      totalAlerts: securityAlerts.length,
      criticalAlerts: securityAlerts.filter((a) => a.severity === 'critical').length,
      highAlerts: securityAlerts.filter((a) => a.severity === 'high').length,
      resolvedAlerts: securityAlerts.filter((a) => a.resolved).length,
      blockedIPs: blockedIPs.length,
      failedLogins,
    },
    userActivity: {
      totalUsers: userStats.total_users,
      activeUsers: userStats.active_users,
      newUsers: userStats.users_created_today,
      adminUsers: userStats.admin_users,
    },
    systemHealth: {
      overallStatus: 'nominal',
      uptime: 'unknown',
      lastIncident: deriveLastSecurityIncident(auditLogs),
    },
  };

  const alertsByType: Record<string, number> = securityAlerts.reduce((acc, alert) => {
    const key = String(alert.type ?? 'unknown');
    acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const topBlockedIPs = [...blockedIPs]
    .sort((a, b) => (b.failedAttempts ?? 0) - (a.failedAttempts ?? 0))
    .slice(0, 10);

  return {
    generatedAt: new Date().toISOString(),
    summary,
    details: {
      securityAlerts: securityAlerts.slice(0, 100),
      alertsByType,
      topBlockedIPs,
      recentAdminActions,
      failedLoginTrends: generateFailedLoginTrends(failedLoginEntries, days),
    },
    recommendations: generateSecurityRecommendations(summary, alertsByType, blockedIPs),
  };
}

async function collectUserStatistics(adminUtils: AdminDatabaseUtils): Promise<UserStatistics> {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const weekAgo = new Date(today);
  weekAgo.setDate(today.getDate() - 7);
  const monthAgo = new Date(today);
  monthAgo.setDate(today.getDate() - 30);

  const [
    totalUsersResult,
    activeUsersResult,
    verifiedUsersResult,
    adminUsersResult,
    superAdminUsersResult,
    usersCreatedTodayResult,
    usersCreatedThisWeekResult,
    usersCreatedThisMonthResult,
    lastLoginTodayResult,
    usersFor2FA,
  ] = await Promise.all([
    adminUtils.getUsersWithRoleFilter({}),
    adminUtils.getUsersWithRoleFilter({ is_active: true }),
    adminUtils.getUsersWithRoleFilter({ is_verified: true }),
    adminUtils.getUsersWithRoleFilter({ role: 'admin' }),
    adminUtils.getUsersWithRoleFilter({ role: 'super_admin' }),
    adminUtils.getUsersWithRoleFilter({ created_after: today }),
    adminUtils.getUsersWithRoleFilter({ created_after: weekAgo }),
    adminUtils.getUsersWithRoleFilter({ created_after: monthAgo }),
    adminUtils.getUsersWithRoleFilter({ last_login_after: today }),
    adminUtils.getUsersWithRoleFilter({}),
  ]);

  const twoFactorEnabled = Array.isArray(usersFor2FA.data)
    ? (usersFor2FA.data as User[]).filter((u) => u.two_factor_enabled).length
    : 0;

  return {
    total_users: totalUsersResult.pagination.total,
    active_users: activeUsersResult.pagination.total,
    verified_users: verifiedUsersResult.pagination.total,
    admin_users: adminUsersResult.pagination.total,
    super_admin_users: superAdminUsersResult.pagination.total,
    users_created_today: usersCreatedTodayResult.pagination.total,
    users_created_this_week: usersCreatedThisWeekResult.pagination.total,
    users_created_this_month: usersCreatedThisMonthResult.pagination.total,
    last_login_today: lastLoginTodayResult.pagination.total,
    two_factor_enabled: twoFactorEnabled,
  };
}

function deriveLastSecurityIncident(auditLogs: AuditLog[]): string | null {
  const incident = auditLogs.find((log) => {
    const action = String(log.action || '').toLowerCase();
    return (
      action.includes('security') ||
      action.includes('alert') ||
      action.includes('threat') ||
      action.includes('incident') ||
      action.includes('breach')
    );
  });
  if (!incident) {
    return null;
  }
  if (incident.timestamp instanceof Date) {
    return incident.timestamp.toISOString();
  }
  return incident.timestamp ? String(incident.timestamp) : null;
}

/**
 * Generate failed login trends per day
 */
function generateFailedLoginTrends(
  failedLogins: Array<{ timestamp: string; ipAddress?: string }>,
  days: number
) {
  const trends: Array<{ date: string; count: number; uniqueIPs: number }> = [];
  const now = new Date();

  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);

    const dayStart = new Date(date);
    dayStart.setHours(0, 0, 0, 0);

    const dayEnd = new Date(date);
    dayEnd.setHours(23, 59, 59, 999);

    const dayFailedLogins = failedLogins.filter((login) => {
      const loginDate = new Date(login.timestamp);
      return loginDate >= dayStart && loginDate <= dayEnd;
    });

    const uniqueIPs = new Set(
      dayFailedLogins.map((login) => String(login.ipAddress ?? 'unknown'))
    ).size;

    trends.push({
      date: dayStart.toISOString().split('T')[0],
      count: dayFailedLogins.length,
      uniqueIPs,
    });
  }

  return trends;
}

/**
 * Heuristic security recommendations
 */
function generateSecurityRecommendations(
  summary: ReportSummary,
  alertsByType: Record<string, number>,
  blockedIPs: BlockedIpEntry[]
) {
  const recs: ReportData['recommendations'] = [];

  if (summary.securityOverview.failedLogins > 100) {
    recs.push({
      priority: 'high',
      category: 'authentication',
      title: 'High Failed Login Activity',
      description:
        'Elevated failed logins detected. Consider rate limiting, lockout policies, or CAPTCHA on suspicious patterns.',
      action: 'Harden authentication controls',
    });
  }

  if (blockedIPs.length > 50) {
    recs.push({
      priority: 'medium',
      category: 'network',
      title: 'High Number of Blocked IPs',
      description:
        'Large volume of blocked IPs suggests scanning/credential stuffing. Investigate ASN/geo clustering.',
      action: 'Analyze blocked IP distribution and add network rules',
    });
  }

  if (
    summary.securityOverview.criticalAlerts >
    summary.securityOverview.resolvedAlerts
  ) {
    recs.push({
      priority: 'critical',
      category: 'monitoring',
      title: 'Unresolved Critical Alerts',
      description:
        'There are more critical alerts than resolved items—triage and remediation required.',
      action: 'Escalate on-call and resolve critical alerts',
    });
  }

  if ((alertsByType['admin_action'] ?? 0) > 200) {
    recs.push({
      priority: 'low',
      category: 'audit',
      title: 'High Admin Activity',
      description:
        'Unusually frequent admin actions can mask malicious changes.',
      action: 'Review admin change logs and correlate with off-hours',
    });
  }

  return recs;
}

/**
 * CSV generator (escape-safe)
 */
function generateCSVReport(report: ReportData): string {
  const lines: string[] = [];
  const esc = (v: unknown) => {
    const s = String(v ?? '');
    if (s.includes('"') || s.includes(',') || s.includes('\n')) {
      return `"${s.replace(/"/g, '""')}"`;
    }
    return s;
    };

  // Header
  lines.push(`Security Report Generated,${esc(report.generatedAt)}`);
  lines.push(
    `Report Period,${esc(report.summary.reportPeriod.startDate)} to ${esc(
      report.summary.reportPeriod.endDate
    )}`
  );
  lines.push(`Days,${esc(report.summary.reportPeriod.days)}`);
  lines.push('');

  // Summary
  lines.push('SECURITY OVERVIEW');
  lines.push('Metric,Value');
  lines.push(`Total Alerts,${esc(report.summary.securityOverview.totalAlerts)}`);
  lines.push(`Critical Alerts,${esc(report.summary.securityOverview.criticalAlerts)}`);
  lines.push(`High Alerts,${esc(report.summary.securityOverview.highAlerts)}`);
  lines.push(`Resolved Alerts,${esc(report.summary.securityOverview.resolvedAlerts)}`);
  lines.push(`Blocked IPs,${esc(report.summary.securityOverview.blockedIPs)}`);
  lines.push(`Failed Logins,${esc(report.summary.securityOverview.failedLogins)}`);
  lines.push('');

  // Alerts by type
  lines.push('ALERTS BY TYPE');
  lines.push('Type,Count');
  for (const [type, count] of Object.entries(report.details.alertsByType)) {
    lines.push(`${esc(type)},${esc(count)}`);
  }
  lines.push('');

  // Top blocked IPs
  lines.push('TOP BLOCKED IPs');
  lines.push('IP Address,Failed Attempts,Blocked At,Reason');
  for (const ip of report.details.topBlockedIPs) {
    lines.push(
      [
        esc(ip.ipAddress),
        esc(ip.failedAttempts),
        esc(ip.blockedAt),
        esc(ip.reason),
      ].join(',')
    );
  }
  lines.push('');

  // Recommendations
  lines.push('RECOMMENDATIONS');
  lines.push('Priority,Category,Title,Description,Action');
  for (const r of report.recommendations) {
    lines.push(
      [esc(r.priority), esc(r.category), esc(r.title), esc(r.description), esc(r.action)].join(',')
    );
  }

  // Trends (compact)
  lines.push('');
  lines.push('FAILED LOGIN TRENDS');
  lines.push('Date,Count,Unique IPs');
  for (const t of report.details.failedLoginTrends) {
    lines.push([esc(t.date), esc(t.count), esc(t.uniqueIPs)].join(','));
  }

  return lines.join('\n');
}
