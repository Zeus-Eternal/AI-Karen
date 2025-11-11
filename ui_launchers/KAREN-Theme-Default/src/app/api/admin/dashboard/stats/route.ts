import { NextRequest, NextResponse } from 'next/server';
import { adminAuthMiddleware } from '@/lib/middleware/admin-auth';
import { getAdminUtils } from '@/lib/database/admin-utils';
/**
 * GET /api/admin/dashboard/stats
 * 
 * Get dashboard statistics for super admin overview
 */
export async function GET(request: NextRequest) {
  try {
    // Check admin authentication and permissions
    const authResult = await adminAuthMiddleware(request, 'super_admin');
    if (authResult instanceof NextResponse) {
      return authResult;
    }
    const adminUtils = getAdminUtils();
    // Get user statistics
    const totalUsers = await adminUtils.getUserCount();
    const totalAdmins = await adminUtils.getAdminCount();
    const activeUsers = await adminUtils.getActiveUserCount();
    // Get security alerts count
    const securityAlerts = await adminUtils.getSecurityAlertsCount();
    // Determine system health based on various factors
    let systemHealth: 'healthy' | 'warning' | 'critical' = 'healthy';
    if (securityAlerts > 10) {
      systemHealth = 'critical';
    } else if (securityAlerts > 5) {
      systemHealth = 'warning';
    }
    const stats = {
      totalUsers,
      totalAdmins,
      activeUsers,
      securityAlerts,
      systemHealth
    };
    return NextResponse.json(stats);
  } catch {
    return NextResponse.json(
      { error: 'Failed to load dashboard statistics' },
      { status: 500 }
    );
  }
}
