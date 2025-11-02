import { NextRequest, NextResponse } from 'next/server';
import { adminAuthMiddleware } from '@/lib/middleware/admin-auth';
import { getAdminUtils } from '@/lib/database/admin-utils';
import { getAuditLogger } from '@/lib/audit/audit-logger';
/**
 * POST /api/admin/security/alerts/[id]/resolve
 * 
 * Resolve a security alert
 */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
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
    const { id: alertId } = await params;
    if (!alertId) {
      return NextResponse.json(
        { error: 'Alert ID is required' },
        { status: 400 }
      );
    }
    const adminUtils = getAdminUtils();
    const auditLogger = getAuditLogger();
    // Get the alert first
    const alert = await adminUtils.getSecurityAlert(alertId);
    if (!alert) {
      return NextResponse.json(
        { error: 'Security alert not found' },
        { status: 404 }
      );
    }
    if (alert.resolved) {
      return NextResponse.json(
        { error: 'Alert is already resolved' },
        { status: 400 }
      );
    }
    // Resolve the alert
    await adminUtils.resolveSecurityAlert(alertId, currentUser.user_id);
    // Log the action
    await auditLogger.log(
      currentUser.user_id,
      'security.alert.resolve',
      'security_alert',
      {
        resourceId: alertId,
        details: {
          alertType: alert.type,
          alertSeverity: alert.severity,
          originalMessage: alert.message
        },
        request,
        ip_address: request.headers.get('x-forwarded-for') || 
                   request.headers.get('x-real-ip') || 
                   'unknown'
      }
    );
    return NextResponse.json({
      message: 'Security alert resolved successfully'

  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to resolve security alert' },
      { status: 500 }
    );
  }
}
