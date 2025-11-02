/**
 * Security Dashboard API Endpoint
 * 
 * Provides comprehensive security metrics, statistics, and monitoring data
 * for the admin security dashboard.
 * 
 * Requirements: 5.4, 5.5, 5.6
 */
import { NextRequest, NextResponse } from 'next/server';
import { enhancedAuthMiddleware } from '@/lib/security/enhanced-auth-middleware';
import { securityManager } from '@/lib/security/security-manager';
import { sessionTimeoutManager } from '@/lib/security/session-timeout-manager';
import { ipSecurityManager } from '@/lib/security/ip-security-manager';
import { mfaManager } from '@/lib/security/mfa-manager';
import { getAdminDatabaseUtils } from '@/lib/database/admin-utils';
import type { AdminApiResponse } from '@/types/admin';
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
      severity: string;
      timestamp: string;
      details: any;
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
    severity: 'low' | 'medium' | 'high' | 'critical';
    user_id?: string;
    user_email?: string;
    ip_address?: string;
    timestamp: string;
    resolved: boolean;
    details: any;
  }>;
  recent_activities: Array<{
    timestamp: string;
    action: string;
    user_id: string;
    user_email: string;
    ip_address?: string;
    details: any;
  }>;
}
export async function GET(request: NextRequest): Promise<NextResponse> {
  return enhancedAuthMiddleware.withEnhancedAuth(
    request,
    async (req, context) => {
      try {
        // Only super admins can access security dashboard
        if (context.user.role !== 'super_admin') {
          return NextResponse.json({
            success: false,
            error: {
              code: 'INSUFFICIENT_PERMISSIONS',
              message: 'Super admin role required to access security dashboard'
            }
          } as AdminApiResponse<never>, { status: 403 });
        }
        const adminUtils = getAdminDatabaseUtils();
        const now = new Date();
        const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const hourAgo = new Date(now.getTime() - 60 * 60 * 1000);
        // Gather security statistics
        const dashboardData: SecurityDashboardData = {
          overview: await getSecurityOverview(adminUtils, todayStart, hourAgo),
          session_statistics: getSessionStatistics(),
          ip_security: getIpSecurityData(),
          mfa_statistics: await getMfaStatistics(adminUtils),
          security_events: getRecentSecurityEvents(),
          recent_activities: await getRecentSecurityActivities(adminUtils, todayStart)
        };
        return NextResponse.json({
          success: true,
          data: dashboardData,
          meta: {
            generated_at: now.toISOString(),
            generated_by: context.user.user_id,
            data_freshness: 'real-time'
          }
        } as AdminApiResponse<SecurityDashboardData>);
      } catch (error) {
        return NextResponse.json({
          success: false,
          error: {
            code: 'DASHBOARD_ERROR',
            message: 'Failed to generate security dashboard data',
            details: { error: error instanceof Error ? error.message : 'Unknown error' }
          }
        } as AdminApiResponse<never>, { status: 500 });
      }
    },
    { requiredRole: 'super_admin' }
  );
}
/**
 * Get security overview statistics
 */
async function getSecurityOverview(adminUtils: any, todayStart: Date, hourAgo: Date) {
  const sessionStats = sessionTimeoutManager.getSessionStatistics();
  const ipStats = ipSecurityManager.getIpStatistics();
  const blockedIps = ipSecurityManager.getBlockedIps();
  // Get security events from today
  const securityEvents = securityManager.getSecurityEvents('system');
  const todayEvents = securityEvents.filter(event => event.created_at >= todayStart);
  // Get failed login attempts from last hour (this would come from audit logs in production)
  const recentAuditLogs = await adminUtils.getAuditLogs({
    action: 'ip.failed_attempt',
    start_date: hourAgo
  }).catch(() => ({ data: [] }));
  // Get MFA enabled users count
  const allUsers = await adminUtils.getUsers({}).catch(() => ({ data: [] }));
  const mfaEnabledCount = allUsers.data.filter((user: any) => user.two_factor_enabled).length;
  // Get locked accounts count
  const lockedAccounts = allUsers.data.filter((user: any) => 
    user.locked_until && new Date(user.locked_until) > new Date()
  ).length;
  return {
    total_active_sessions: sessionStats.totalActiveSessions,
    failed_login_attempts_last_hour: recentAuditLogs.data.length,
    blocked_ips: blockedIps.length,
    security_events_today: todayEvents.length,
    mfa_enabled_users: mfaEnabledCount,
    locked_accounts: lockedAccounts
  };
}
/**
 * Get session statistics
 */
function getSessionStatistics() {
  const stats = sessionTimeoutManager.getSessionStatistics();
  const concurrentSessions = sessionTimeoutManager.getConcurrentSessionsByUser(25).map(summary => ({
    user_id: summary.user_id,
    email: summary.email,
    session_count: summary.session_count,
    role: summary.role,
    last_activity: summary.last_activity,
    sessions: summary.active_sessions
  }));
  return {
    total_sessions: stats.totalActiveSessions,
    sessions_by_role: stats.sessionsByRole,
    average_session_duration: stats.averageSessionDuration,
    expiring_soon: stats.expiringSoon,
    concurrent_sessions_by_user: concurrentSessions
  };
}
/**
 * Get IP security data
 */
function getIpSecurityData() {
  const stats = ipSecurityManager.getIpStatistics();
  const blockedIps = ipSecurityManager.getBlockedIps();
  const whitelistEntries = ipSecurityManager.getWhitelistEntries();
  // Get suspicious activities (from security events)
  const securityEvents = securityManager.getSecurityEvents('system');
  const suspiciousActivities = securityEvents
    .filter(event => event.event_type === 'suspicious_activity')
    .slice(0, 10)
    .map(event => ({
      ip: event.ip_address || 'unknown',
      user_id: event.user_id,
      event_type: event.event_type,
      severity: event.severity,
      timestamp: event.created_at.toISOString(),
      details: event.details
    }));
  return {
    unique_ips_today: stats.totalUniqueIps,
    whitelisted_ips: whitelistEntries.length,
    blocked_ips: blockedIps.map(blocked => ({
      ip: blocked.ip,
      reason: blocked.reason,
      blocked_until: blocked.blockedUntil.toISOString()
    })),
    top_accessed_ips: stats.topAccessedIps.map(ip => ({
      ip: ip.ip,
      access_count: ip.accessCount || 0,
      users: ip.users || 0,
      last_access: new Date().toISOString() // Mock data
    })),
    suspicious_activities: suspiciousActivities
  };
}
/**
 * Get MFA statistics
 */
async function getMfaStatistics(adminUtils: any) {
  const allUsers = await adminUtils.getUsers({}).catch(() => ({ data: [] }));
  const totalUsers = allUsers.data.length;
  const mfaEnabledUsers = allUsers.data.filter((user: any) => user.two_factor_enabled);
  const mfaEnabledCount = mfaEnabledUsers.length;
  // Count users who should have MFA (admins and super admins)
  const adminUsers = allUsers.data.filter((user: any) => 
    user.role === 'admin' || user.role === 'super_admin'
  );
  const mfaRequiredCount = adminUsers.length;
  const complianceRate = mfaRequiredCount > 0 
    ? (adminUsers.filter((user: any) => user.two_factor_enabled).length / mfaRequiredCount) * 100
    : 100;
  // Recent MFA setups (mock data - would come from audit logs)
  const recentSetups = mfaEnabledUsers.slice(0, 5).map((user: any) => ({
    user_id: user.user_id,
    email: user.email,
    enabled_at: user.updated_at || new Date().toISOString()
  }));
  return {
    total_users: totalUsers,
    mfa_enabled: mfaEnabledCount,
    mfa_required: mfaRequiredCount,
    mfa_compliance_rate: Math.round(complianceRate),
    recent_mfa_setups: recentSetups
  };
}
/**
 * Get recent security events
 */
function getRecentSecurityEvents() {
  const events = securityManager.getSecurityEvents('system');
  return events
    .slice(0, 20)
    .map(event => ({
      id: event.id,
      event_type: event.event_type,
      severity: event.severity,
      user_id: event.user_id,
      user_email: undefined, // Would be populated from user lookup
      ip_address: event.ip_address,
      timestamp: event.created_at.toISOString(),
      resolved: event.resolved,
      details: event.details
    }));
}
/**
 * Get recent security activities from audit logs
 */
async function getRecentSecurityActivities(adminUtils: any, todayStart: Date) {
  const securityActions = [
    'session.created',
    'session.terminated',
    'session.extended',
    'mfa.enabled',
    'mfa.disabled',
    'account.locked',
    'account.unlocked',
    'ip.blocked',
    'ip.unblocked'
  ];
  const activities = [];
  for (const action of securityActions) {
    try {
      const logs = await adminUtils.getAuditLogs({
        action,
        start_date: todayStart,
        limit: 5

      activities.push(...logs.data.map((log: any) => ({
        timestamp: log.timestamp,
        action: log.action,
        user_id: log.user_id,
        user_email: log.user?.email || 'unknown',
        ip_address: log.ip_address,
        details: log.details
      })));
    } catch (error) {
      // Continue if specific action logs are not available
      continue;
    }
  }
  // Sort by timestamp and return most recent
  return activities
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    .slice(0, 20);
}
/**
 * Security event resolution endpoint
 */
export async function PATCH(request: NextRequest): Promise<NextResponse> {
  return enhancedAuthMiddleware.withEnhancedAuth(
    request,
    async (req, context) => {
      try {
        if (context.user.role !== 'super_admin') {
          return NextResponse.json({
            success: false,
            error: {
              code: 'INSUFFICIENT_PERMISSIONS',
              message: 'Super admin role required'
            }
          } as AdminApiResponse<never>, { status: 403 });
        }
        const body = await req.json();
        const { event_id, resolution_notes } = body;
        if (!event_id) {
          return NextResponse.json({
            success: false,
            error: {
              code: 'MISSING_EVENT_ID',
              message: 'Event ID is required'
            }
          } as AdminApiResponse<never>, { status: 400 });
        }
        await securityManager.resolveSecurityEvent(event_id, context.user.user_id);
        return NextResponse.json({
          success: true,
          data: {
            event_id,
            resolved_by: context.user.user_id,
            resolved_at: new Date().toISOString(),
            resolution_notes
          }
        } as AdminApiResponse<any>);
      } catch (error) {
        return NextResponse.json({
          success: false,
          error: {
            code: 'RESOLUTION_ERROR',
            message: 'Failed to resolve security event'
          }
        } as AdminApiResponse<never>, { status: 500 });
      }
    },
    { requiredRole: 'super_admin' }
  );
}
