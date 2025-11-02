import { NextRequest, NextResponse } from 'next/server';
import { adminAuthMiddleware } from '@/lib/middleware/admin-auth';
import { getAdminUtils } from '@/lib/database/admin-utils';
/**
 * GET /api/admin/security/alerts
 * 
 * Get security alerts
 */
export async function GET(request: NextRequest) {
  try {
    // Check admin authentication and permissions
    const authResult = await adminAuthMiddleware(request, 'super_admin');
    if (authResult instanceof NextResponse) {
      return authResult;
    }
    const { searchParams } = new URL(request.url);
    const limit = parseInt(searchParams.get('limit') || '50');
    const offset = parseInt(searchParams.get('offset') || '0');
    const severity = searchParams.get('severity');
    const resolved = searchParams.get('resolved');
    const adminUtils = getAdminUtils();
    const alerts = await adminUtils.getSecurityAlerts({
      limit,
      offset,
      severity: severity as any,
      resolved: resolved === 'true' ? true : resolved === 'false' ? false : undefined

    return NextResponse.json(alerts);
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to load security alerts' },
      { status: 500 }
    );
  }
}
