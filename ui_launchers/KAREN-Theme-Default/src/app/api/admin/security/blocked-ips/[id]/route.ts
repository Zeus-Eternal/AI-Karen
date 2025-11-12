import { NextRequest, NextResponse } from 'next/server';
import { adminAuthMiddleware } from '@/lib/middleware/admin-auth';
import { getAdminUtils } from '@/lib/database/admin-utils';
import { getAuditLogger } from '@/lib/audit/audit-logger';
/**
 * DELETE /api/admin/security/blocked-ips/[id]
 * 
 * Unblock an IP address
 */
export async function DELETE(
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
    const { id: blockedIpId } = await params;
    if (!blockedIpId) {
      return NextResponse.json(
        { error: 'Blocked IP ID is required' },
        { status: 400 }
      );
    }
    const adminUtils = getAdminUtils();
    const auditLogger = getAuditLogger();
    // Get the blocked IP first
    const blockedIP = await adminUtils.getBlockedIP(blockedIpId);
    if (!blockedIP) {
      return NextResponse.json(
        { error: 'Blocked IP not found' },
        { status: 404 }
      );
    }
    // Unblock the IP
    await adminUtils.unblockIP(blockedIpId);
    // Log the action
    await auditLogger.log(
      currentUser.user_id,
      'security.ip.unblock',
      'blocked_ip',
      {
        resourceId: blockedIpId,
        details: {
          ipAddress: blockedIP.ipAddress,
          originalReason: blockedIP.reason,
          failedAttempts: blockedIP.failedAttempts
        },
        request,
        ip_address: request.headers.get('x-forwarded-for') || 
                   request.headers.get('x-real-ip') || 
                   'unknown'
      }
    );
    return NextResponse.json({
      message: 'IP address unblocked successfully'
    });
  } catch (_error) {
    return NextResponse.json(
      { error: 'Failed to unblock IP address' },
      { status: 500 }
    );
  }
}
