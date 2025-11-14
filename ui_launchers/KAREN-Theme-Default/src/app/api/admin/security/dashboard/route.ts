/**
 * Security Dashboard API Endpoint (Prod-Grade)
 *
 * Provides comprehensive security metrics, statistics, and monitoring data
 * for the admin security dashboard.
 *
 * Requirements: 5.4, 5.5, 5.6
 *
 * Notes:
 * - Enforces super_admin via enhancedAuthMiddleware
 * - Robust error handling and safe fallbacks
 * - Zod validation for PATCH payload
 * - Query params: ?limit=, ?offset=, ?period=today|week|month
 * - Meta: generated_at, generated_by, paging
 */

import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';

import { enhancedAuthMiddleware } from '@/lib/security/enhanced-auth-middleware';
import { securityManager } from '@/lib/security/security-manager';
import { sessionTimeoutManager, type ConcurrentSessionSummary } from '@/lib/security/session-timeout-manager';
import { ipSecurityManager } from '@/lib/security/ip-security-manager';
import { getAdminDatabaseUtils, type BlockedIpEntry, type IpWhitelistEntry } from '@/lib/database/admin-utils';
import type { AdminApiResponse, AuditLog, SecurityEvent, User } from '@/types/admin';

const MAX_LIMIT = 100;
const DEFAULT_LIMIT = 25;

type Severity = 'low' | 'medium' | 'high' | 'critical';
type AdminUtils = ReturnType<typeof getAdminDatabaseUtils>;

interface SecurityDashboardData {
  overview: {
    total_active_sessions: number;
    failed_login_attempts_last_hour: number;
    blocked_ips: number;
    security_events_today: number;
    mfa_enabled_users: number;
    locked_accounts: number;
  };
  session_statistics: {
    total_sessions: number;
    sessions_by_role: Record<string, number>;
    average_session_duration: number;
    expiring_soon: number;
    concurrent_sessions_by_user: Array<{
      user_id: string;
      email: string;
      session_count: number;
      role: string;
      last_activity: string;
      sessions: Array<{
        session_token: string;
        ip_address?: string;
        user_agent?: string;
        created_at: string;
        last_accessed: string;
        expires_at: string;
      }>;
    }>;
  };
  ip_security: {
    unique_ips_today: number;
    whitelisted_ips: number;
    blocked_ips: Array<{
      ip: string;
      reason: string;
      blocked_until: string;
      failed_attempts?: number;
    }>;
    top_accessed_ips: Array<{
      ip: string;
      access_count: number;
      users: number;
      last_access: string;
    }>;
    suspicious_activities: Array<{
      ip: string;
      user_id?: string;
      event_type: string;
      severity: Severity;
      timestamp: string;
      details: unknown;
    }>;
  };
  mfa_statistics: {
    total_users: number;
    mfa_enabled: number;
    mfa_required: number;
    mfa_compliance_rate: number;
    recent_mfa_setups: Array<{
      user_id: string;
      email: string;
      enabled_at: string;
    }>;
  };
  security_events: Array<{
    id: string;
    event_type: string;
    severity: Severity;
    user_id?: string;
    user_email?: string;
    ip_address?: string;
    timestamp: string;
    resolved: boolean;
    details: unknown;
  }>;
  recent_activities: Array<{
    timestamp: string;
    action: string;
    user_id: string;
    user_email: string;
    ip_address?: string;
    details: unknown;
  }>;
}

/* ----------------------------- GET DASHBOARD ----------------------------- */

export async function GET(request: NextRequest): Promise<NextResponse> {
  return enhancedAuthMiddleware.withEnhancedAuth(
    request,
    async (req, context) => {
      try {
        // Super admin only
        if (context.user.role !== 'super_admin') {
          return NextResponse.json(
            {
              success: false,
              error: {
                code: 'INSUFFICIENT_PERMISSIONS',
                message: 'Super admin role required to access security dashboard',
              },
            } as AdminApiResponse<never>,
            { status: 403 },
          );
        }

        const { searchParams } = new URL(req.url);
        const period = (searchParams.get('period') || 'week').toLowerCase();
        const limit = clampInt(searchParams.get('limit'), DEFAULT_LIMIT, 1, MAX_LIMIT);
        const offset = clampInt(searchParams.get('offset'), 0, 0, 10_000);

        const adminUtils = getAdminDatabaseUtils();
        const { now, todayStart, hourAgo } = deriveTimeRange(period);

        const dashboardData: SecurityDashboardData = {
          overview: await getSecurityOverview(adminUtils, todayStart, hourAgo),
          session_statistics: getSessionStatistics(),
          ip_security: await getIpSecurityData(),
          mfa_statistics: await getMfaStatistics(adminUtils),
          security_events: await getRecentSecurityEvents(adminUtils, limit, offset),
          recent_activities: await getRecentSecurityActivities(adminUtils, todayStart, limit, offset),
        };

        return NextResponse.json(
          {
            success: true,
            data: dashboardData,
            meta: {
              generated_at: now.toISOString(),
              generated_by: context.user.user_id,
              data_freshness: 'real-time',
              paging: { limit, offset },
            },
          } as AdminApiResponse<SecurityDashboardData>,
          {
            headers: {
              'Cache-Control': 'no-store',
              'X-Kari-Security-Metrics': '1',
            },
          },
        );
      } catch (error) {
        return NextResponse.json(
          {
            success: false,
            error: {
              code: 'DASHBOARD_ERROR',
              message: 'Failed to generate security dashboard data',
              details: { error: error instanceof Error ? error.message : 'Unknown error' },
            },
          } as AdminApiResponse<never>,
          { status: 500 },
        );
      }
    },
    { requiredRole: 'super_admin' },
  );
}

/* ---------------------------- SUPPORTING GETTERS ---------------------------- */

async function getSecurityOverview(adminUtils: AdminUtils, todayStart: Date, hourAgo: Date) {
  const sessionStats = safe(() => sessionTimeoutManager.getSessionStatistics(), {
    totalActiveSessions: 0,
    sessionsByRole: {},
    averageSessionDuration: 0,
    expiringSoon: 0,
  });

  let blockedIps: BlockedIpEntry[] = [];
  try {
    blockedIps = await ipSecurityManager.getBlockedIps();
  } catch {
    blockedIps = [];
  }
  const securityEvents = safe<SecurityEvent[]>(() => securityManager.getSecurityEvents('system'), []);
  const todayEvents = securityEvents.filter((e) => toDate(e.created_at) >= todayStart);

  // Failed attempts in the last hour (audit logs)
  const recentAuditLogs = await adminUtils
    .getAuditLogs(
      { action: 'ip.failed_attempt', start_date: hourAgo },
      { page: 1, limit: DEFAULT_LIMIT },
    )
    .catch(() => ({ data: [] as AuditLog[] }));
  // Users & MFA (fallback to 1k users)
  const userResponse = await adminUtils
    .getUsersWithRoleFilter({}, { page: 1, limit: 1000 })
    .catch(() => ({ data: [] as User[] }));
  const allUsers = userResponse.data || [];
  const mfaEnabledCount = allUsers.filter((u) => !!u.two_factor_enabled).length;
  const lockedAccounts = allUsers.filter(
    (u) => u.locked_until && toDate(u.locked_until) > new Date(),
  ).length;

  return {
    total_active_sessions: sessionStats.totalActiveSessions,
    failed_login_attempts_last_hour: recentAuditLogs.data.length,
    blocked_ips: blockedIps.length,
    security_events_today: todayEvents.length,
    mfa_enabled_users: mfaEnabledCount,
    locked_accounts: lockedAccounts,
  };
}

function getSessionStatistics() {
  const stats = safe(() => sessionTimeoutManager.getSessionStatistics(), {
    totalActiveSessions: 0,
    sessionsByRole: {},
    averageSessionDuration: 0,
    expiringSoon: 0,
  });

  const concurrentSessions = safe<ConcurrentSessionSummary[]>(
    () => sessionTimeoutManager.getConcurrentSessionsByUser(25),
    [],
  );

  const formattedConcurrentSessions = concurrentSessions.map((summary) => ({
    user_id: summary.user_id,
    email: summary.email,
    session_count: summary.session_count,
    role: summary.role,
    last_activity: toDate(summary.last_activity).toISOString(),
    sessions: (summary.active_sessions || []).map((s) => ({
      session_token: s.session_token,
      ip_address: s.ip_address,
      user_agent: s.user_agent,
      created_at: toDate(s.created_at).toISOString(),
      last_accessed: toDate(s.last_accessed).toISOString(),
      expires_at: toDate(s.expires_at).toISOString(),
    })),
  }));

  return {
    total_sessions: stats.totalActiveSessions,
    sessions_by_role: stats.sessionsByRole,
    average_session_duration: stats.averageSessionDuration,
    expiring_soon: stats.expiringSoon,
    concurrent_sessions_by_user: formattedConcurrentSessions,
  };
}

async function getIpSecurityData() {
  const stats = await ipSecurityManager
    .getIpStatistics()
    .catch(() => ({ totalUniqueIps: 0, topAccessedIps: [] }));
  const blockedIps = await ipSecurityManager.getBlockedIps().catch(() => [] as BlockedIpEntry[]);
  const whitelistEntries = await ipSecurityManager
    .getWhitelistEntries()
    .catch(() => [] as IpWhitelistEntry[]);
  const securityEvents = safe<SecurityEvent[]>(() => securityManager.getSecurityEvents('system'), []);

  const suspiciousActivities = securityEvents
    .filter((event) => event.event_type === 'suspicious_activity')
    .slice(0, 10)
    .map((event) => ({
      ip: event.ip_address || 'unknown',
      user_id: event.user_id,
      event_type: event.event_type,
      severity: event.severity as Severity,
      timestamp: toDate(event.created_at).toISOString(),
      details: event.details,
    }));

  return {
    unique_ips_today: stats.totalUniqueIps,
    whitelisted_ips: whitelistEntries.filter((entry) => entry.is_active !== false).length,
    blocked_ips: blockedIps.map((entry) => ({
      ip: entry.ipAddress,
      reason: entry.reason || 'policy_violation',
      blocked_until: entry.expiresAt ? toDate(entry.expiresAt).toISOString() : '',
      failed_attempts: entry.failedAttempts,
    })),
    top_accessed_ips: (stats.topAccessedIps || []).map((summary) => ({
      ip: summary.ip,
      access_count: summary.accessCount,
      users: summary.uniqueUsers,
      last_access: summary.lastAccess?.toISOString() || new Date().toISOString(),
    })),
    suspicious_activities: suspiciousActivities,
  };
}

async function getMfaStatistics(adminUtils: AdminUtils) {
  // Optionally ask mfaManager for authoritative counts if available
  const userResponse = await adminUtils
    .getUsersWithRoleFilter({}, { page: 1, limit: 1000 })
    .catch(() => ({ data: [] as User[] }));
  const allUsers = userResponse.data || [];
  const totalUsers = allUsers.length;
  const mfaEnabledUsers = allUsers.filter((u) => !!u.two_factor_enabled);
  const mfaEnabledCount = mfaEnabledUsers.length;

  const adminUsers = allUsers.filter(
    (u) => u.role === 'admin' || u.role === 'super_admin',
  );
  const mfaRequiredCount = adminUsers.length;
  const complianceRate =
    mfaRequiredCount > 0
      ? Math.round(
          (adminUsers.filter((u) => !!u.two_factor_enabled).length / mfaRequiredCount) * 100,
        )
      : 100;

  const recentSetups = mfaEnabledUsers.slice(0, 5).map((u) => ({
    user_id: u.user_id,
    email: u.email,
    enabled_at: (u.updated_at && toDate(u.updated_at).toISOString()) || new Date().toISOString(),
  }));

  return {
    total_users: totalUsers,
    mfa_enabled: mfaEnabledCount,
    mfa_required: mfaRequiredCount,
    mfa_compliance_rate: complianceRate,
    recent_mfa_setups: recentSetups,
  };
}

async function getRecentSecurityEvents(adminUtils: AdminUtils, limit = DEFAULT_LIMIT, offset = 0) {
  const events = safe<SecurityEvent[]>(() => securityManager.getSecurityEvents('system'), []);
  const page = events
    .sort((a, b) => toDate(b.created_at).getTime() - toDate(a.created_at).getTime())
    .slice(offset, offset + limit);

  // Optionally hydrate user emails
  const userIds = Array.from(
    new Set(page.map((e) => e.user_id).filter((x): x is string => Boolean(x))),
  );

  const usersById: Record<string, User> = {};
  if (userIds.length) {
    try {
      const users = await adminUtils.getUsersByIds(userIds);
      for (const u of users) {
        usersById[u.user_id] = u;
      }
    } catch {
      // swallow — email stays undefined
    }
  }

  return page.map((event) => ({
    id: event.id,
    event_type: event.event_type,
    severity: (event.severity || 'low') as Severity,
    user_id: event.user_id,
    user_email: event.user_id ? usersById[event.user_id]?.email : undefined,
    ip_address: event.ip_address,
    timestamp: toDate(event.created_at).toISOString(),
    resolved: !!event.resolved,
    details: event.details,
  }));
}

async function getRecentSecurityActivities(
  adminUtils: AdminUtils,
  startFrom: Date,
  limit = DEFAULT_LIMIT,
  offset = 0,
) {
  const securityActions = [
    'session.created',
    'session.terminated',
    'session.extended',
    'mfa.enabled',
    'mfa.disabled',
    'account.locked',
    'account.unlocked',
    'ip.blocked',
    'ip.unblocked',
  ];

  type ActivityLog = {
    timestamp: string;
    action: string;
    user_id: string;
    user_email: string;
    ip_address?: string;
    details: unknown;
  };

  const activities: ActivityLog[] = [];

  for (const action of securityActions) {
    try {
      const logs = await adminUtils.getAuditLogs(
        {
          action,
          start_date: startFrom,
        },
        { page: 1, limit }, // pull enough; we’ll sort/dedupe below
      );
      for (const log of logs.data || []) {
        activities.push({
          timestamp: toDate(log.timestamp).toISOString(),
          action: log.action,
          user_id: log.user_id,
          user_email: log.user?.email || 'unknown',
          ip_address: log.ip_address,
          details: log.details,
        });
      }
    } catch {
      // continue on per-action failure
      continue;
    }
  }

  // Sort, dedupe by (timestamp+user_id+action), paginate
  const key = (a: ActivityLog) => `${a.timestamp}|${a.user_id}|${a.action}`;
  const deduped = Array.from(new Map(activities.map((a) => [key(a), a])).values()).sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
  );

  return deduped.slice(offset, offset + limit);
}

/* --------------------------- PATCH: Resolve Event --------------------------- */

const ResolveEventSchema = z.object({
  event_id: z.string().min(1, 'event_id is required'),
  resolution_notes: z.string().max(10_000).optional(),
});

export async function PATCH(request: NextRequest): Promise<NextResponse> {
  return enhancedAuthMiddleware.withEnhancedAuth(
    request,
    async (req, context) => {
      try {
        if (context.user.role !== 'super_admin') {
          return NextResponse.json(
            {
              success: false,
              error: {
                code: 'INSUFFICIENT_PERMISSIONS',
                message: 'Super admin role required',
              },
            } as AdminApiResponse<never>,
            { status: 403 },
          );
        }

        const json = await req.json().catch(() => ({}));
        const parsed = ResolveEventSchema.safeParse(json);
        if (!parsed.success) {
          return NextResponse.json(
            {
              success: false,
              error: {
                code: 'INVALID_PAYLOAD',
                message: 'Invalid request payload',
                details: parsed.error.flatten(),
              },
            } as AdminApiResponse<never>,
            { status: 400 },
          );
        }

        const { event_id, resolution_notes } = parsed.data;
        await securityManager.resolveSecurityEvent(event_id, context.user.user_id, {
          resolution_notes,
        });

        const response: AdminApiResponse<{
          event_id: string;
          resolved_by: string;
          resolved_at: string;
          resolution_notes?: string;
        }> = {
          success: true,
          data: {
            event_id,
            resolved_by: context.user.user_id,
            resolved_at: new Date().toISOString(),
            resolution_notes,
          },
        };

        return NextResponse.json(response);
      } catch (error) {
        return NextResponse.json(
          {
            success: false,
            error: {
              code: 'RESOLUTION_ERROR',
              message: 'Failed to resolve security event',
              details: { error: error instanceof Error ? error.message : 'Unknown error' },
            },
          } as AdminApiResponse<never>,
          { status: 500 },
        );
      }
    },
    { requiredRole: 'super_admin' },
  );
}

/* --------------------------------- Utils ---------------------------------- */

function clampInt(
  raw: string | null,
  fallback: number,
  min = Number.MIN_SAFE_INTEGER,
  max = Number.MAX_SAFE_INTEGER,
) {
  if (!raw) return fallback;
  const n = Number.parseInt(raw, 10);
  if (Number.isNaN(n)) return fallback;
  return Math.min(Math.max(n, min), max);
}

function deriveTimeRange(period: string) {
  const now = new Date();
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const hourAgo = new Date(now.getTime() - 60 * 60 * 1000);

  if (period === 'today') return { now, todayStart, hourAgo };
  if (period === 'month') {
    const start = new Date(now.getFullYear(), now.getMonth(), 1);
    return { now, todayStart: start, hourAgo };
  }
  // default week
  const weekStart = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
  return { now, todayStart: weekStart, hourAgo };
}

function toDate(d: unknown): Date {
  if (!d) return new Date(0);
  if (d instanceof Date) return d;
  const t = new Date(d as string | number | Date);
  return Number.isNaN(t.getTime()) ? new Date(0) : t;
}

// Safe call wrapper with fallback
function safe<T>(fn: () => T, fallback: T): T {
  try {
    return fn();
  } catch {
    return fallback;
  }
}
