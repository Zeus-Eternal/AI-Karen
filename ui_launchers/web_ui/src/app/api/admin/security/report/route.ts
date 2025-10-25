import { NextRequest, NextResponse } from 'next/server';
import { adminAuthMiddleware } from '@/lib/middleware/admin-auth';
import { getAdminUtils } from '@/lib/database/admin-utils';
import { getAuditLogger } from '@/lib/audit/audit-logger';

/**
 * GET /api/admin/security/report
 * 
 * Generate and download a security report
 */
export async function GET(request: NextRequest) {
  try {
    // Check admin authentication and permissions
    const authResult = await adminAuthMiddleware(request, 'super_admin');
    if (authResult instanceof NextResponse) {
      return authResult;
    }

    const { user: currentUser } = authResult;

    if (!currentUser) {
      return NextResponse.json(
        { error: 'User not found' },
        { status: 401 }
      );
    }
    const { searchParams } = new URL(request.url);
    const format = searchParams.get('format') || 'json';
    const days = parseInt(searchParams.get('days') || '30');

    const adminUtils = getAdminUtils();
    const auditLogger = getAuditLogger();

    // Generate report data
    const reportData = await generateSecurityReport(adminUtils, days);

    // Log the report generation
    await auditLogger.log(
      currentUser.user_id,
      'security.report.generate',
      'security_report',
      {
        details: {
          format,
          daysCovered: days,
          reportSize: JSON.stringify(reportData).length
        },
        request,
        ip_address: request.headers.get('x-forwarded-for') || 
                   request.headers.get('x-real-ip') || 
                   'unknown'
      }
    );

    if (format === 'json') {
      return NextResponse.json(reportData);
    } else if (format === 'csv') {
      const csv = generateCSVReport(reportData);
      return new NextResponse(csv, {
        headers: {
          'Content-Type': 'text/csv',
          'Content-Disposition': `attachment; filename="security-report-${new Date().toISOString().split('T')[0]}.csv"`
        }
      });
    } else {
      // For PDF or other formats, you would integrate with a PDF generation library
      return NextResponse.json(
        { error: 'PDF format not yet implemented' },
        { status: 501 }
      );
    }
  } catch (error) {
    console.error('Generate security report error:', error);
    return NextResponse.json(
      { error: 'Failed to generate security report' },
      { status: 500 }
    );
  }
}

/**
 * Generate comprehensive security report data
 */
async function generateSecurityReport(adminUtils: any, days: number) {
  const endDate = new Date();
  const startDate = new Date();
  startDate.setDate(startDate.getDate() - days);

  // Get various security metrics
  const [
    securityAlerts,
    blockedIPs,
    failedLogins,
    adminActions,
    userStats,
    systemHealth
  ] = await Promise.all([
    adminUtils.getSecurityAlerts({ 
      startDate, 
      endDate, 
      limit: 1000 
    }),
    adminUtils.getBlockedIPs({ limit: 1000 }),
    adminUtils.getFailedLoginAttempts({ startDate, endDate }),
    adminUtils.getAdminActions({ startDate, endDate }),
    adminUtils.getUserStatistics({ startDate, endDate }),
    adminUtils.getSystemHealthMetrics()
  ]);

  // Calculate summary statistics
  const summary = {
    reportPeriod: {
      startDate: startDate.toISOString(),
      endDate: endDate.toISOString(),
      days
    },
    securityOverview: {
      totalAlerts: securityAlerts.length,
      criticalAlerts: securityAlerts.filter((a: any) => a.severity === 'critical').length,
      highAlerts: securityAlerts.filter((a: any) => a.severity === 'high').length,
      resolvedAlerts: securityAlerts.filter((a: any) => a.resolved).length,
      blockedIPs: blockedIPs.length,
      failedLogins: failedLogins.length
    },
    userActivity: {
      totalUsers: userStats.totalUsers,
      activeUsers: userStats.activeUsers,
      newUsers: userStats.newUsers,
      adminUsers: userStats.adminUsers
    },
    systemHealth: {
      overallStatus: systemHealth.status,
      uptime: systemHealth.uptime,
      lastIncident: systemHealth.lastIncident
    }
  };

  // Categorize alerts by type
  const alertsByType = securityAlerts.reduce((acc: any, alert: any) => {
    acc[alert.type] = (acc[alert.type] || 0) + 1;
    return acc;
  }, {});

  // Top blocked IPs
  const topBlockedIPs = blockedIPs
    .sort((a: any, b: any) => b.failedAttempts - a.failedAttempts)
    .slice(0, 10);

  // Recent admin actions
  const recentAdminActions = adminActions
    .sort((a: any, b: any) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    .slice(0, 50);

  return {
    generatedAt: new Date().toISOString(),
    summary,
    details: {
      securityAlerts: securityAlerts.slice(0, 100), // Limit for report size
      alertsByType,
      topBlockedIPs,
      recentAdminActions,
      failedLoginTrends: generateFailedLoginTrends(failedLogins, days)
    },
    recommendations: generateSecurityRecommendations(summary, alertsByType, blockedIPs)
  };
}

/**
 * Generate failed login trends
 */
function generateFailedLoginTrends(failedLogins: any[], days: number) {
  const trends = [];
  const now = new Date();
  
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    const dayStart = new Date(date.setHours(0, 0, 0, 0));
    const dayEnd = new Date(date.setHours(23, 59, 59, 999));
    
    const dayFailedLogins = failedLogins.filter(login => {
      const loginDate = new Date(login.timestamp);
      return loginDate >= dayStart && loginDate <= dayEnd;
    });
    
    trends.push({
      date: dayStart.toISOString().split('T')[0],
      count: dayFailedLogins.length,
      uniqueIPs: new Set(dayFailedLogins.map(login => login.ipAddress)).size
    });
  }
  
  return trends;
}

/**
 * Generate security recommendations based on report data
 */
function generateSecurityRecommendations(summary: any, alertsByType: any, blockedIPs: any[]) {
  const recommendations = [];
  
  // High number of failed logins
  if (summary.securityOverview.failedLogins > 100) {
    recommendations.push({
      priority: 'high',
      category: 'authentication',
      title: 'High Failed Login Activity',
      description: 'Consider implementing additional rate limiting or CAPTCHA verification.',
      action: 'Review authentication security settings'
    });
  }
  
  // Many blocked IPs
  if (blockedIPs.length > 50) {
    recommendations.push({
      priority: 'medium',
      category: 'network',
      title: 'High Number of Blocked IPs',
      description: 'Review blocked IP patterns to identify potential coordinated attacks.',
      action: 'Analyze blocked IP geographical distribution'
    });
  }
  
  // Unresolved critical alerts
  if (summary.securityOverview.criticalAlerts > summary.securityOverview.resolvedAlerts) {
    recommendations.push({
      priority: 'critical',
      category: 'monitoring',
      title: 'Unresolved Critical Alerts',
      description: 'Multiple critical security alerts require immediate attention.',
      action: 'Review and resolve all critical security alerts'
    });
  }
  
  // Frequent admin actions
  if (alertsByType['admin_action'] > 200) {
    recommendations.push({
      priority: 'low',
      category: 'audit',
      title: 'High Admin Activity',
      description: 'Consider reviewing admin action patterns for unusual activity.',
      action: 'Audit recent administrative changes'
    });
  }
  
  return recommendations;
}

/**
 * Generate CSV format report
 */
function generateCSVReport(reportData: any): string {
  const lines = [];
  
  // Header
  lines.push('Security Report Generated: ' + reportData.generatedAt);
  lines.push('Report Period: ' + reportData.summary.reportPeriod.startDate + ' to ' + reportData.summary.reportPeriod.endDate);
  lines.push('');
  
  // Summary
  lines.push('SECURITY OVERVIEW');
  lines.push('Metric,Value');
  lines.push(`Total Alerts,${reportData.summary.securityOverview.totalAlerts}`);
  lines.push(`Critical Alerts,${reportData.summary.securityOverview.criticalAlerts}`);
  lines.push(`High Alerts,${reportData.summary.securityOverview.highAlerts}`);
  lines.push(`Resolved Alerts,${reportData.summary.securityOverview.resolvedAlerts}`);
  lines.push(`Blocked IPs,${reportData.summary.securityOverview.blockedIPs}`);
  lines.push(`Failed Logins,${reportData.summary.securityOverview.failedLogins}`);
  lines.push('');
  
  // Alerts by type
  lines.push('ALERTS BY TYPE');
  lines.push('Type,Count');
  Object.entries(reportData.details.alertsByType).forEach(([type, count]) => {
    lines.push(`${type},${count}`);
  });
  lines.push('');
  
  // Top blocked IPs
  lines.push('TOP BLOCKED IPs');
  lines.push('IP Address,Failed Attempts,Blocked At,Reason');
  reportData.details.topBlockedIPs.forEach((ip: any) => {
    lines.push(`${ip.ipAddress},${ip.failedAttempts},${ip.blockedAt},${ip.reason}`);
  });
  
  return lines.join('\n');
}