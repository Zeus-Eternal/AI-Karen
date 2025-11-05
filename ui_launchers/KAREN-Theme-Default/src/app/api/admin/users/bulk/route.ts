// app/api/admin/users/bulk/route.ts
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

type AllowedOperation = 'activate' | 'deactivate' | 'delete' | 'role_change' | 'export';
const ALLOWED_OPS: AllowedOperation[] = ['activate', 'deactivate', 'delete', 'role_change', 'export'];
const MAX_BULK = 100;

function noStore(init?: ResponseInit): ResponseInit {
  return {
    ...(init || {}),
    headers: {
      ...(init?.headers || {}),
      'Cache-Control': 'no-cache, no-store, must-revalidate',
      'Pragma': 'no-cache',
      'Expires': '0',
      'Content-Type': 'application/json; charset=utf-8',
    },
  };
}

/**
 * POST /api/admin/users/bulk - Perform bulk operations on users
 */
export const POST = requireAdmin(async (request: NextRequest, context) => {
  try {
    const body: BulkUserOperation = await request.json();

    // Basic shape validation
    if (!body?.operation || !body?.user_ids || !Array.isArray(body.user_ids)) {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Operation and user_ids array are required',
            details: {
              provided_operation: body?.operation,
              user_ids_count: body?.user_ids ? body.user_ids.length : 0,
            },
          },
        } as AdminApiResponse<never>,
        noStore({ status: 400 })
      );
    }

    // Operation validation
    if (!ALLOWED_OPS.includes(body.operation as AllowedOperation)) {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'INVALID_OPERATION',
            message: 'Invalid bulk operation',
            details: { provided_operation: body.operation, allowed_operations: ALLOWED_OPS },
          },
        } as AdminApiResponse<never>,
        noStore({ status: 400 })
      );
    }

    // Deduplicate and guard size
    const uniqueIds = Array.from(new Set(body.user_ids.filter(Boolean)));
    if (uniqueIds.length === 0) {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'At least one user ID is required',
            details: { user_ids_count: 0 },
          },
        } as AdminApiResponse<never>,
        noStore({ status: 400 })
      );
    }
    if (uniqueIds.length > MAX_BULK) {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'BULK_LIMIT_EXCEEDED',
            message: `Bulk operations limited to ${MAX_BULK} users at a time`,
            details: { requested_count: uniqueIds.length, max_allowed: MAX_BULK },
          },
        } as AdminApiResponse<never>,
        noStore({ status: 400 })
      );
    }

    // Prevent operations on self (early)
    if (uniqueIds.includes(context.user.user_id)) {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'CANNOT_MODIFY_SELF',
            message: 'Cannot perform bulk operations on your own account',
            details: { self_user_id: context.user.user_id },
          },
        } as AdminApiResponse<never>,
        noStore({ status: 400 })
      );
    }

    const adminUtils = getAdminDatabaseUtils();

    // Hydrate users & existence check
    const users = await Promise.all(uniqueIds.map(id => adminUtils.getUserWithRole(id)));
    const notFoundUsers = uniqueIds.filter((id, idx) => !users[idx]);
    if (notFoundUsers.length > 0) {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'USERS_NOT_FOUND',
            message: 'Some users were not found',
            details: { not_found_user_ids: notFoundUsers },
          },
        } as AdminApiResponse<never>,
        noStore({ status: 404 })
      );
    }

    // Super admin protection
    const superAdminUsers = users.filter(u => u?.role === 'super_admin');
    if (superAdminUsers.length > 0 && !context.isSuperAdmin()) {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'INSUFFICIENT_PERMISSIONS',
            message: 'Cannot perform bulk operations on super admin users',
            details: {
              super_admin_user_ids: superAdminUsers.map(u => u!.user_id),
              required_role: 'super_admin',
            },
          },
        } as AdminApiResponse<never>,
        noStore({ status: 403 })
      );
    }

    // Execute operation
    let result: any = {};
    let auditAction = '';
    let auditDetails: any = {};

    switch (body.operation as AllowedOperation) {
      case 'activate': {
        await adminUtils.bulkUpdateUserStatus(uniqueIds, true, context.user.user_id);
        result = { activated_count: uniqueIds.length };
        auditAction = 'user.bulk_activate';
        auditDetails = { user_ids: uniqueIds, count: uniqueIds.length };
        break;
      }
      case 'deactivate': {
        await adminUtils.bulkUpdateUserStatus(uniqueIds, false, context.user.user_id);
        result = { deactivated_count: uniqueIds.length };
        auditAction = 'user.bulk_deactivate';
        auditDetails = { user_ids: uniqueIds, count: uniqueIds.length };
        break;
      }
      case 'delete': {
        // Soft delete policy via deactivate
        await adminUtils.bulkUpdateUserStatus(uniqueIds, false, context.user.user_id);
        result = { deleted_count: uniqueIds.length, deletion_type: 'soft_delete' };
        auditAction = 'user.bulk_delete';
        auditDetails = { user_ids: uniqueIds, count: uniqueIds.length, deletion_type: 'soft_delete' };
        break;
      }
      case 'role_change': {
        const newRole = body.parameters?.new_role as 'admin' | 'user' | undefined;
        if (!newRole || !['admin', 'user'].includes(newRole)) {
          return NextResponse.json(
            {
              success: false,
              error: {
                code: 'VALIDATION_ERROR',
                message: 'new_role parameter is required and must be "admin" or "user"',
                details: { operation: body.operation, parameters: body.parameters },
              },
            } as AdminApiResponse<never>,
            noStore({ status: 400 })
          );
        }
        // Only super-admin can elevate to admin in bulk
        if (newRole === 'admin' && !context.isSuperAdmin()) {
          return NextResponse.json(
            {
              success: false,
              error: {
                code: 'INSUFFICIENT_PERMISSIONS',
                message: 'Super admin role required for bulk admin role assignment',
                details: { requested_role: newRole, user_role: context.user.role },
              },
            } as AdminApiResponse<never>,
            noStore({ status: 403 })
          );
        }

        // Update one-by-one to ensure per-user invariants and fine-grained audit trails if needed
        for (const userId of uniqueIds) {
          await adminUtils.updateUserRole(userId, newRole, context.user.user_id);
        }
        result = { role_changed_count: uniqueIds.length, new_role: newRole };
        auditAction = 'user.bulk_role_change';
        auditDetails = { user_ids: uniqueIds, count: uniqueIds.length, new_role: newRole };
        break;
      }
      case 'export': {
        const exportUsers = users.filter(Boolean).map(user => ({
          user_id: user!.user_id,
          email: user!.email,
          full_name: user!.full_name,
          role: user!.role,
          is_verified: user!.is_verified,
          is_active: user!.is_active,
          created_at: user!.created_at,
          last_login_at: user!.last_login_at,
          two_factor_enabled: user!.two_factor_enabled,
        }));
        result = {
          export_data: exportUsers,
          export_count: exportUsers.length,
          export_format: 'json',
        };
        auditAction = 'user.bulk_export';
        auditDetails = { user_ids: uniqueIds, count: uniqueIds.length, export_format: 'json' };
        break;
      }
    }

    // Operation audit (request-scope)
    await adminUtils.createAuditLog({
      user_id: context.user.user_id,
      action: auditAction,
      resource_type: 'user',
      details: auditDetails,
      ip_address: request.headers.get('x-forwarded-for')?.split(',')[0] || 'unknown',
      user_agent: request.headers.get('user-agent') || undefined,
    });

    const response: AdminApiResponse<typeof result> = {
      success: true,
      data: result,
      meta: {
        operation: body.operation,
        processed_count: uniqueIds.length,
        message: `Bulk ${body.operation} operation completed successfully`,
      },
    };
    return NextResponse.json(response, noStore());
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: {
          code: 'BULK_OPERATION_FAILED',
          message: 'Failed to perform bulk user operation',
          details: { error: error instanceof Error ? error.message : 'Unknown error' },
        },
      } as AdminApiResponse<never>,
      noStore({ status: 500 })
    );
  }
});
