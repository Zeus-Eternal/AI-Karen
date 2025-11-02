/**
 * Bulk User Operations API Route
 * POST /api/admin/users/bulk - Perform bulk operations on users
 * 
 * Requirements: 4.5
 */

import { NextRequest, NextResponse } from 'next/server';
import { requireAdmin } from '@/lib/middleware/admin-auth';
import { getAdminDatabaseUtils } from '@/lib/database/admin-utils';
import type { AdminApiResponse, BulkUserOperation } from '@/types/admin';

/**
 * POST /api/admin/users/bulk - Perform bulk operations on users
 */
export const POST = requireAdmin(async (request: NextRequest, context) => {
  try {
    const body: BulkUserOperation = await request.json();
    
    // Validate request
    if (!body.operation || !body.user_ids || !Array.isArray(body.user_ids)) {
      return NextResponse.json({
        success: false,
        error: {
          code: 'VALIDATION_ERROR',
          message: 'Operation and user_ids array are required',
          details: { provided_operation: body.operation, user_ids_count: body.user_ids?.length }
        }
      } as AdminApiResponse<never>, { status: 400 });
    }

    if (body.user_ids.length === 0) {
      return NextResponse.json({
        success: false,
        error: {
          code: 'VALIDATION_ERROR',
          message: 'At least one user ID is required',
          details: { user_ids_count: 0 }
        }
      } as AdminApiResponse<never>, { status: 400 });
    }

    // Limit bulk operations to reasonable size
    if (body.user_ids.length > 100) {
      return NextResponse.json({
        success: false,
        error: {
          code: 'BULK_LIMIT_EXCEEDED',
          message: 'Bulk operations limited to 100 users at a time',
          details: { requested_count: body.user_ids.length, max_allowed: 100 }
        }
      } as AdminApiResponse<never>, { status: 400 });
    }

    const adminUtils = getAdminDatabaseUtils();
    
    // Validate all users exist and check permissions
    const users = await Promise.all(
      body.user_ids.map(id => adminUtils.getUserWithRole(id))
    );
    
    const notFoundUsers = body.user_ids.filter((id, index) => !users[index]);
    if (notFoundUsers.length > 0) {
      return NextResponse.json({
        success: false,
        error: {
          code: 'USERS_NOT_FOUND',
          message: 'Some users were not found',
          details: { not_found_user_ids: notFoundUsers }
        }
      } as AdminApiResponse<never>, { status: 404 });
    }

    // Check for super admin users if current user is not super admin
    const superAdminUsers = users.filter(user => user?.role === 'super_admin');
    if (superAdminUsers.length > 0 && !context.isSuperAdmin()) {
      return NextResponse.json({
        success: false,
        error: {
          code: 'INSUFFICIENT_PERMISSIONS',
          message: 'Cannot perform bulk operations on super admin users',
          details: { 
            super_admin_user_ids: superAdminUsers.map(u => u?.user_id),
            required_role: 'super_admin' 
          }
        }
      } as AdminApiResponse<never>, { status: 403 });
    }

    // Prevent operations on self
    if (body.user_ids.includes(context.user.user_id)) {
      return NextResponse.json({
        success: false,
        error: {
          code: 'CANNOT_MODIFY_SELF',
          message: 'Cannot perform bulk operations on your own account',
          details: { self_user_id: context.user.user_id }
        }
      } as AdminApiResponse<never>, { status: 400 });
    }

    let result: any = {};
    let auditAction = '';
    let auditDetails: any = {};

    switch (body.operation) {
      case 'activate':
        await adminUtils.bulkUpdateUserStatus(body.user_ids, true, context.user.user_id);
        result = { activated_count: body.user_ids.length };
        auditAction = 'user.bulk_activate';
        auditDetails = { user_ids: body.user_ids, count: body.user_ids.length };
        break;

      case 'deactivate':
        await adminUtils.bulkUpdateUserStatus(body.user_ids, false, context.user.user_id);
        result = { deactivated_count: body.user_ids.length };
        auditAction = 'user.bulk_deactivate';
        auditDetails = { user_ids: body.user_ids, count: body.user_ids.length };
        break;

      case 'delete':
        // Soft delete by deactivating
        await adminUtils.bulkUpdateUserStatus(body.user_ids, false, context.user.user_id);
        result = { deleted_count: body.user_ids.length };
        auditAction = 'user.bulk_delete';
        auditDetails = { 
          user_ids: body.user_ids, 
          count: body.user_ids.length,
          deletion_type: 'soft_delete'
        };
        break;

      case 'role_change':
        if (!body.parameters?.new_role) {
          return NextResponse.json({
            success: false,
            error: {
              code: 'VALIDATION_ERROR',
              message: 'new_role parameter is required for role_change operation',
              details: { operation: body.operation, parameters: body.parameters }
            }
          } as AdminApiResponse<never>, { status: 400 });
        }

        const newRole = body.parameters.new_role as 'admin' | 'user';
        
        // Validate role
        if (!['admin', 'user'].includes(newRole)) {
          return NextResponse.json({
            success: false,
            error: {
              code: 'INVALID_ROLE',
              message: 'Invalid role for bulk operation',
              details: { provided_role: newRole, allowed_roles: ['admin', 'user'] }
            }
          } as AdminApiResponse<never>, { status: 400 });
        }

        // Check permissions for admin role assignment
        if (newRole === 'admin' && !context.isSuperAdmin()) {
          return NextResponse.json({
            success: false,
            error: {
              code: 'INSUFFICIENT_PERMISSIONS',
              message: 'Super admin role required for bulk admin role assignment',
              details: { requested_role: newRole, user_role: context.user.role }
            }
          } as AdminApiResponse<never>, { status: 403 });
        }

        // Update roles individually for proper audit logging
        for (const userId of body.user_ids) {
          await adminUtils.updateUserRole(userId, newRole, context.user.user_id);
        }

        result = { role_changed_count: body.user_ids.length, new_role: newRole };
        auditAction = 'user.bulk_role_change';
        auditDetails = { 
          user_ids: body.user_ids, 
          count: body.user_ids.length,
          new_role: newRole
        };
        break;

      case 'export':
        // Generate export data
        const exportUsers = users.filter(Boolean).map(user => ({
          user_id: user!.user_id,
          email: user!.email,
          full_name: user!.full_name,
          role: user!.role,
          is_verified: user!.is_verified,
          is_active: user!.is_active,
          created_at: user!.created_at,
          last_login_at: user!.last_login_at,
          two_factor_enabled: user!.two_factor_enabled
        }));

        result = { 
          export_data: exportUsers,
          export_count: exportUsers.length,
          export_format: 'json'
        };
        auditAction = 'user.bulk_export';
        auditDetails = { 
          user_ids: body.user_ids, 
          count: body.user_ids.length,
          export_format: 'json'
        };
        break;

      default:
        return NextResponse.json({
          success: false,
          error: {
            code: 'INVALID_OPERATION',
            message: 'Invalid bulk operation',
            details: { 
              provided_operation: body.operation,
              allowed_operations: ['activate', 'deactivate', 'delete', 'role_change', 'export']
            }
          }
        } as AdminApiResponse<never>, { status: 400 });
    }

    // Log the bulk operation
    await adminUtils.createAuditLog({
      user_id: context.user.user_id,
      action: auditAction,
      resource_type: 'user',
      details: auditDetails,
      ip_address: request.headers.get('x-forwarded-for')?.split(',')[0] || 'unknown',
      user_agent: request.headers.get('user-agent') || undefined
    });

    const response: AdminApiResponse<typeof result> = {
      success: true,
      data: result,
      meta: {
        operation: body.operation,
        processed_count: body.user_ids.length,
        message: `Bulk ${body.operation} operation completed successfully`
      }
    };

    return NextResponse.json(response);

  } catch (error) {
    console.error('Bulk user operation error:', error);
    
    return NextResponse.json({
      success: false,
      error: {
        code: 'BULK_OPERATION_FAILED',
        message: 'Failed to perform bulk user operation',
        details: { error: error instanceof Error ? error.message : 'Unknown error' }
      }
    } as AdminApiResponse<never>, { status: 500 });
  }
});