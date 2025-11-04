/**
 * Admin Promotion API Route
 * POST /api/admin/admins/promote/[id] - Promote user to admin
 * 
 * Requirements: 3.3
 */
import { NextRequest, NextResponse } from 'next/server';
// Force this route to be dynamic
export const dynamic = 'force-dynamic';
import { requireSuperAdmin } from '@/lib/middleware/admin-auth';
import { getAdminDatabaseUtils } from '@/lib/database/admin-utils';
import type { AdminApiResponse } from '@/types/admin';
/**
 * POST /api/admin/admins/promote/[id] - Promote user to admin (super admin only)
 */
export const POST = requireSuperAdmin(async (request: NextRequest, context) => {
  try {
    const userId = request.nextUrl.pathname.split('/').slice(-2)[0]; // Get ID from promote/[id]/route
    if (!userId) {
      return NextResponse.json({
        success: false,
        error: {
          code: 'INVALID_USER_ID',
          message: 'User ID is required',
          details: { provided_id: userId }
        }
      } as AdminApiResponse<never>, { status: 400 });
    }
    const adminUtils = getAdminDatabaseUtils();
    // Get current user data
    const currentUser = await adminUtils.getUserWithRole(userId);
    if (!currentUser) {
      return NextResponse.json({
        success: false,
        error: {
          code: 'USER_NOT_FOUND',
          message: 'User not found',
          details: { user_id: userId }
        }
      } as AdminApiResponse<never>, { status: 404 });
    }
    // Check if user is already an admin
    if (currentUser.role === 'admin' || currentUser.role === 'super_admin') {
      return NextResponse.json({
        success: false,
        error: {
          code: 'ALREADY_ADMIN',
          message: 'User is already an admin',
          details: { user_id: userId, current_role: currentUser.role }
        }
      } as AdminApiResponse<never>, { status: 400 });
    }
    // Cannot promote self (though this should be prevented by super admin requirement)
    if (userId === context.user.user_id) {
      return NextResponse.json({
        success: false,
        error: {
          code: 'CANNOT_PROMOTE_SELF',
          message: 'Cannot promote your own account',
          details: { user_id: userId }
        }
      } as AdminApiResponse<never>, { status: 400 });
    }
    // Promote user to admin
    await adminUtils.updateUserRole(userId, 'admin', context.user.user_id);
    // Get updated user for response
    const updatedUser = await adminUtils.getUserWithRole(userId);
    if (!updatedUser) {
      throw new Error('Failed to retrieve promoted user');
    }
    // Log the promotion
    await adminUtils.createAuditLog({
      user_id: context.user.user_id,
      action: 'admin.promote',
      resource_type: 'user',
      resource_id: userId,
      details: {
        email: currentUser.email,
        full_name: currentUser.full_name,
        previous_role: currentUser.role,
        new_role: 'admin',
        promoted_by: context.user.email
      },
      ip_address: request.headers.get('x-forwarded-for')?.split(',')[0] || 'unknown',
      user_agent: request.headers.get('user-agent') || undefined
    });

    // Remove sensitive information from response
    const responseUser = {
      user_id: updatedUser.user_id,
      email: updatedUser.email,
      full_name: updatedUser.full_name,
      role: updatedUser.role,
      is_verified: updatedUser.is_verified,
      is_active: updatedUser.is_active,
      created_at: updatedUser.created_at,
      updated_at: updatedUser.updated_at,
      last_login_at: updatedUser.last_login_at,
      two_factor_enabled: updatedUser.two_factor_enabled
    };
    const response: AdminApiResponse<{ promoted_user: typeof responseUser }> = {
      success: true,
      data: { promoted_user: responseUser },
      meta: {
        message: 'User promoted to admin successfully',
        previous_role: currentUser.role,
        new_role: 'admin',
        promoted_by: context.user.email,
        recommendations: [
          'User should enable two-factor authentication',
          'User should review admin permissions and responsibilities',
          'Consider notifying user of their new admin privileges'
        ]
      }
    };
    return NextResponse.json(response);
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: {
        code: 'ADMIN_PROMOTION_FAILED',
        message: 'Failed to promote user to admin',
        details: { error: error instanceof Error ? error.message : 'Unknown error' }
      }
    } as AdminApiResponse<never>, { status: 500 });
  }
});
