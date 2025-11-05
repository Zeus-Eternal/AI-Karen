import { NextRequest, NextResponse } from 'next/server';
import { adminAuthMiddleware } from '@/lib/middleware/admin-auth';
import { getAdminUtils } from '@/lib/database/admin-utils';
/**
 * GET /api/admin/security/blocked-ips
 * 
 * Get blocked IP addresses
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
    const adminUtils = getAdminUtils();
    const blockedIPs = await adminUtils.getBlockedIPs({ limit, offset });
    return NextResponse.json(blockedIPs);
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to load blocked IP addresses' },
      { status: 500 }
    );
  }
}
