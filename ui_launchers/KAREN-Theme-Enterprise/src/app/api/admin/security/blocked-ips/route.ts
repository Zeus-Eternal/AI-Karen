import { NextRequest, NextResponse } from 'next/server';
import { adminAuthMiddleware } from '@/lib/middleware/admin-auth';

// This route needs to be static for export compatibility
import { getAdminUtils } from '@/lib/database/admin-utils';
import { safeGetSearchParams } from '@/app/api/_utils/static-export-helpers';

// Explicitly set dynamic to auto for static export compatibility
export const dynamic = 'auto';
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
    const searchParams = safeGetSearchParams(request);
    const limit = parseInt(searchParams.get('limit') || '50');
    const offset = parseInt(searchParams.get('offset') || '0');
    const adminUtils = getAdminUtils();
    const blockedIPs = await adminUtils.getBlockedIPs({ limit, offset });
    return NextResponse.json(blockedIPs);
  } catch {
    return NextResponse.json(
      { error: 'Failed to load blocked IP addresses' },
      { status: 500 }
    );
  }
}
