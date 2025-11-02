/**
 * Individual User Management API Routes
 * GET /api/admin/users/[id] - Get user details
 * PUT /api/admin/users/[id] - Update user
 * DELETE /api/admin/users/[id] - Delete user
 * 
 * Requirements: 4.2, 4.5
 */
import { NextRequest, NextResponse } from 'next/server';
import { requireAdmin } from '@/lib/middleware/admin-auth';
import { getAdminDatabaseUtils } from '@/lib/database/admin-utils';
import { getDatabaseClient } from '@/lib/database/client';
import { validateEmail } from '@/lib/auth/setup-validation';
import type { AdminApiResponse, UpdateUserRequest, User } from '@/types/admin';
/**
 * GET /api/admin/users/[id] - Get user details
 */
export const GET = requireAdmin(async (request: NextRequest, context) => {
  try {
    const userId = request.nextUrl.pathname.split('/').pop();
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
    const user = await adminUtils.getUserWithRole(userId);
    if (!user) {
      return NextResponse.json({
        success: false,
        error: {
          code: 'USER_NOT_FOUND',
          message: 'User not found',
          details: { user_id: userId }
        }
      } as AdminApiResponse<never>, { status: 404 });
    }
    // Non-super admins cannot view super admin users
    if (user.role === 'super_admin' && !context.isSuperAdmin()) {
      return NextResponse.json({
        success: false,
        error: {
          code: 'INSUFFICIENT_PERMISSIONS',
          message: 'Cannot access super admin user data',
          details: { required_role: 'super_admin' }
        }
      } as AdminApiResponse<never>, { status: 403 });
    }
    // Remove sensitive information from response
    const responseUser = {
      user_id: user.user_id,
      email: user.email,
      full_name: user.full_name,
      role: user.role,
      is_verified: user.is_verified,
      is_active: user.is_active,
      created_at: user.created_at,
      updated_at: user.updated_at,
      last_login_at: user.last_login_at,
      two_factor_enabled: user.two_factor_enabled,
      failed_login_attempts: user.failed_login_attempts,
      locked_until: user.locked_until,
      preferences: user.preferences
    };
    const response: AdminApiResponse<{ user: typeof responseUser }> = {
      success: true,
      data: { user: responseUser }
    };
    return NextResponse.json(response);
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: {
        code: 'GET_USER_FAILED',
        message: 'Failed to retrieve user',
        details: { error: error instanceof Error ? error.message : 'Unknown error' }
      }
    } as AdminApiResponse<never>, { status: 500 });
  }
});
/**
 * PUT /api/admin/users/[id] - Update user
 */
export const PUT = requireAdmin(async (request: NextRequest, context) => {
  try {
    const userId = request.nextUrl.pathname.split('/').pop();
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
    const body: UpdateUserRequest = await request.json();
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
    // Permission checks
    if (currentUser.role === 'super_admin' && !context.isSuperAdmin()) {
      return NextResponse.json({
        success: false,
        error: {
          code: 'INSUFFICIENT_PERMISSIONS',
          message: 'Cannot modify super admin users',
          details: { required_role: 'super_admin' }
        }
      } as AdminApiResponse<never>, { status: 403 });
    }
    // Prevent self-modification of critical fields
    if (userId === context.user.user_id) {
      if (body.role || body.is_active === false) {
        return NextResponse.json({
          success: false,
          error: {
            code: 'CANNOT_MODIFY_SELF',
            message: 'Cannot modify your own role or active status',
            details: { attempted_changes: Object.keys(body) }
          }
        } as AdminApiResponse<never>, { status: 400 });
      }
    }
    // Role change validation
    if (body.role) {
      // Only super admins can assign super_admin role
      if (body.role === 'super_admin' && !context.isSuperAdmin()) {
        return NextResponse.json({
          success: false,
          error: {
            code: 'INSUFFICIENT_PERMISSIONS',
            message: 'Super admin role required to assign super admin role',
            details: { requested_role: body.role, user_role: context.user.role }
          }
        } as AdminApiResponse<never>, { status: 403 });
      }
      // Non-super admins cannot create admin users
      if (body.role === 'admin' && !context.isSuperAdmin()) {
        return NextResponse.json({
          success: false,
          error: {
            code: 'INSUFFICIENT_PERMISSIONS',
            message: 'Super admin role required to promote users to admin',
            details: { requested_role: body.role, user_role: context.user.role }
          }
        } as AdminApiResponse<never>, { status: 403 });
      }
      // Cannot demote the last super admin
      if (currentUser.role === 'super_admin' && body.role !== 'super_admin') {
        const isLastSuperAdmin = await adminUtils.isLastSuperAdmin(userId);
        if (isLastSuperAdmin) {
          return NextResponse.json({
            success: false,
            error: {
              code: 'CANNOT_DELETE_LAST_SUPER_ADMIN',
              message: 'Cannot demote the last super admin',
              details: { current_role: currentUser.role, requested_role: body.role }
            }
          } as AdminApiResponse<never>, { status: 400 });
        }
      }
    }
    // Build update query dynamically
    const updateFields: string[] = [];
    const updateValues: any[] = [];
    let paramIndex = 1;
    if (body.full_name !== undefined) {
      updateFields.push(`full_name = $${paramIndex++}`);
      updateValues.push(body.full_name);
    }
    if (body.is_active !== undefined) {
      updateFields.push(`is_active = $${paramIndex++}`);
      updateValues.push(body.is_active);
    }
    if (body.is_verified !== undefined) {
      updateFields.push(`is_verified = $${paramIndex++}`);
      updateValues.push(body.is_verified);
    }
    if (body.preferences !== undefined) {
      updateFields.push(`preferences = $${paramIndex++}`);
      updateValues.push(JSON.stringify(body.preferences));
    }
    if (body.two_factor_enabled !== undefined) {
      updateFields.push(`two_factor_enabled = $${paramIndex++}`);
      updateValues.push(body.two_factor_enabled);
    }
    // Always update the updated_at timestamp
    updateFields.push(`updated_at = NOW()`);
    if (updateFields.length > 1) { // More than just updated_at
      updateValues.push(userId); // For WHERE clause
      const query = `
        UPDATE auth_users 
        SET ${updateFields.join(', ')}
        WHERE user_id = $${paramIndex}
      `;
      // Use direct database query for complex updates
      const db = getDatabaseClient();
      await db.query(query, updateValues);
    }
    // Handle role change separately for audit logging
    if (body.role && body.role !== currentUser.role) {
      await adminUtils.updateUserRole(userId, body.role, context.user.user_id);
    }
    // Log the update
    await adminUtils.createAuditLog({
      user_id: context.user.user_id,
      action: 'user.update',
      resource_type: 'user',
      resource_id: userId,
      details: {
        email: currentUser.email,
        changes: body,
        previous_values: {
          full_name: currentUser.full_name,
          role: currentUser.role,
          is_active: currentUser.is_active,
          is_verified: currentUser.is_verified,
          two_factor_enabled: currentUser.two_factor_enabled
        }
      },
      ip_address: request.headers.get('x-forwarded-for')?.split(',')[0] || 'unknown',
      user_agent: request.headers.get('user-agent') || undefined
    });
    // Get updated user for response
    const updatedUser = await adminUtils.getUserWithRole(userId);
    if (!updatedUser) {
      throw new Error('Failed to retrieve updated user');
    }
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
      two_factor_enabled: updatedUser.two_factor_enabled,
      preferences: updatedUser.preferences
    };
    const response: AdminApiResponse<{ user: typeof responseUser }> = {
      success: true,
      data: { user: responseUser },
      meta: {
        message: 'User updated successfully',
        changes_applied: Object.keys(body)
      }
    };
    return NextResponse.json(response);
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: {
        code: 'USER_UPDATE_FAILED',
        message: 'Failed to update user',
        details: { error: error instanceof Error ? error.message : 'Unknown error' }
      }
    } as AdminApiResponse<never>, { status: 500 });
  }
});
/**
 * DELETE /api/admin/users/[id] - Delete user
 */
export const DELETE = requireAdmin(async (request: NextRequest, context) => {
  try {
    const userId = request.nextUrl.pathname.split('/').pop();
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
    // Permission checks
    if (currentUser.role === 'super_admin' && !context.isSuperAdmin()) {
      return NextResponse.json({
        success: false,
        error: {
          code: 'INSUFFICIENT_PERMISSIONS',
          message: 'Cannot delete super admin users',
          details: { required_role: 'super_admin' }
        }
      } as AdminApiResponse<never>, { status: 403 });
    }
    // Prevent self-deletion
    if (userId === context.user.user_id) {
      return NextResponse.json({
        success: false,
        error: {
          code: 'CANNOT_DELETE_SELF',
          message: 'Cannot delete your own account',
          details: { user_id: userId }
        }
      } as AdminApiResponse<never>, { status: 400 });
    }
    // Cannot delete the last super admin
    if (currentUser.role === 'super_admin') {
      const isLastSuperAdmin = await adminUtils.isLastSuperAdmin(userId);
      if (isLastSuperAdmin) {
        return NextResponse.json({
          success: false,
          error: {
            code: 'CANNOT_DELETE_LAST_SUPER_ADMIN',
            message: 'Cannot delete the last super admin',
            details: { user_id: userId, role: currentUser.role }
          }
        } as AdminApiResponse<never>, { status: 400 });
      }
    }
    // Soft delete by setting is_active to false
    const query = `
      UPDATE auth_users 
      SET is_active = false, updated_at = NOW()
      WHERE user_id = $1
    `;
    const db = getDatabaseClient();
    await db.query(query, [userId]);
    // Log the deletion
    await adminUtils.createAuditLog({
      user_id: context.user.user_id,
      action: 'user.delete',
      resource_type: 'user',
      resource_id: userId,
      details: {
        email: currentUser.email,
        role: currentUser.role,
        full_name: currentUser.full_name,
        deletion_type: 'soft_delete'
      },
      ip_address: request.headers.get('x-forwarded-for')?.split(',')[0] || 'unknown',
      user_agent: request.headers.get('user-agent') || undefined
    });
    const response: AdminApiResponse<{ deleted_user_id: string }> = {
      success: true,
      data: { deleted_user_id: userId },
      meta: {
        message: 'User deleted successfully',
        deletion_type: 'soft_delete',
        note: 'User account has been deactivated but data is retained for audit purposes'
      }
    };
    return NextResponse.json(response);
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: {
        code: 'USER_DELETION_FAILED',
        message: 'Failed to delete user',
        details: { error: error instanceof Error ? error.message : 'Unknown error' }
      }
    } as AdminApiResponse<never>, { status: 500 });
  }
});
