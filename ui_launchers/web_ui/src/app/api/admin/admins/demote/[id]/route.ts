/**
 * Admin Demotion API Route
 * POST /api/admin/admins/demote/[id] - Demote admin to user
 * 
 * Requirements: 3.3
 */

import { NextRequest, NextResponse } from 'next/server';
import { requireSuperAdmin } from '@/lib/middleware/admin-auth';
import { getAdminDatabaseUtils } from '@/lib/database/admin-utils';
import type { AdminApiResponse } from '@/types/admin';

/**
 * POST /api/admin/admins/demote/[id] - Demote admin to user (super admin only)
 */
export const POST = requireSuperAdmin(async (request: NextRequest, context) => {
  try {
    const userId = request.nextUrl.pathname.split('/').slice(-2)[0]; // Get ID from demote/[id]/route
    
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

    // Check if user is actually an admin
    if (currentUser.role !== 'admin' && currentUser.role !== 'super_admin') {
      return NextResponse.json({
        success: false,
        error: {
          code: 'NOT_ADMIN',
          message: 'User is not an admin',
          details: { user_id: userId, current_role: currentUser.role }
        }
      } as AdminApiResponse<never>, { status: 400 });
    }

    // Cannot demote self
    if (userId === context.user.user_id) {
      return NextResponse.json({
        success: false,
        error: {
          code: 'CANNOT_DEMOTE_SELF',
          message: 'Cannot demote your own account',
          details: { user_id: userId }
        }
      } as AdminApiResponse<never>, { status: 400 });
    }

    // Cannot demote the last super admin
    if (currentUser.role === 'super_admin') {
      const isLastSuperAdmin = await adminUtils.isLastSuperAdmin(userId);
      if (isLastSuperAdmin) {
        return NextResponse.json({
          success: false,
          error: {
            code: 'CANNOT_DEMOTE_LAST_SUPER_ADMIN',
            message: 'Cannot demote the last super admin',
            details: { user_id: userId, current_role: currentUser.role }
          }
        } as AdminApiResponse<never>, { status: 400 });
      }
    }

    // Demote user to regular user
    await adminUtils.updateUserRole(userId, 'user', context.user.user_id);

    // Get updated user for response
    const updatedUser = await adminUtils.getUserWithRole(userId);
    if (!updatedUser) {
      throw new Error('Failed to retrieve demoted user');
    }

    // Log the demotion
    await adminUtils.createAuditLog({
      user_id: context.user.user_id,
      action: 'admin.demote',
      resource_type: 'user',
      resource_id: userId,
      details: {
        email: currentUser.email,
        full_name: currentUser.full_name,
        previous_role: currentUser.role,
        new_role: 'user',
        demoted_by: context.user.email
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

    const response: AdminApiResponse<{ demoted_user: typeof responseUser }> = {
      success: true,
      data: { demoted_user: responseUser },
      meta: {
        message: 'Admin demoted to user successfully',
        previous_role: currentUser.role,
        new_role: 'user',
        demoted_by: context.user.email,
        notes: [
          'User no longer has admin privileges',
          'User will lose access to admin interfaces on next login',
          'Consider notifying user of role change'
        ]
      }
    };

    return NextResponse.json(response);

  } catch (error) {
    console.error('Admin demotion error:', error);
    
    return NextResponse.json({
      success: false,
      error: {
        code: 'ADMIN_DEMOTION_FAILED',
        message: 'Failed to demote admin to user',
        details: { error: error instanceof Error ? error.message : 'Unknown error' }
      }
    } as AdminApiResponse<never>, { status: 500 });
  }
});