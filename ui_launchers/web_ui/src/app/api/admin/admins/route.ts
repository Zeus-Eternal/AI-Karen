/**
 * Admin Management API Routes
 * GET /api/admin/admins - List admin users
 * POST /api/admin/admins - Create new admin (super admin only)
 * 
 * Requirements: 3.3, 3.4
 */
import { NextRequest, NextResponse } from 'next/server';
import { requireSuperAdmin } from '@/lib/middleware/admin-auth';
import { getAdminDatabaseUtils } from '@/lib/database/admin-utils';
import { validateEmail, hashPassword } from '@/lib/auth/setup-validation';
import type { AdminApiResponse, CreateUserRequest, User } from '@/types/admin';
/**
 * GET /api/admin/admins - List admin users (super admin only)
 */
export const GET = requireSuperAdmin(async (request: NextRequest, context) => {
  try {
    const adminUtils = getAdminDatabaseUtils();
    // Get all admin and super admin users
    const adminUsers = await adminUtils.getUsersByRole('admin');
    const superAdminUsers = await adminUtils.getUsersByRole('super_admin');
    const allAdmins = [...adminUsers, ...superAdminUsers];
    // Remove sensitive information from response
    const sanitizedAdmins = allAdmins.map((user: User) => ({
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
      locked_until: user.locked_until
    }));
    // Sort by role (super_admin first) then by creation date
    sanitizedAdmins.sort((a, b) => {
      if (a.role === 'super_admin' && b.role !== 'super_admin') return -1;
      if (b.role === 'super_admin' && a.role !== 'super_admin') return 1;
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();

    const response: AdminApiResponse<{ admins: typeof sanitizedAdmins; statistics: any }> = {
      success: true,
      data: {
        admins: sanitizedAdmins,
        statistics: {
          total_admins: allAdmins.length,
          super_admins: superAdminUsers.length,
          regular_admins: adminUsers.length,
          active_admins: allAdmins.filter(u => u.is_active).length,
          verified_admins: allAdmins.filter(u => u.is_verified).length,
          two_factor_enabled: allAdmins.filter(u => u.two_factor_enabled).length
        }
      },
      meta: {
        message: 'Admin users retrieved successfully'
      }
    };
    return NextResponse.json(response);
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: {
        code: 'ADMIN_LIST_FAILED',
        message: 'Failed to retrieve admin users',
        details: { error: error instanceof Error ? error.message : 'Unknown error' }
      }
    } as AdminApiResponse<never>, { status: 500 });
  }

/**
 * POST /api/admin/admins - Create new admin (super admin only)
 */
export const POST = requireSuperAdmin(async (request: NextRequest, context) => {
  try {
    const body: CreateUserRequest = await request.json();
    // Validate required fields
    if (!body.email) {
      return NextResponse.json({
        success: false,
        error: {
          code: 'VALIDATION_ERROR',
          message: 'Email is required',
          details: { field: 'email' }
        }
      } as AdminApiResponse<never>, { status: 400 });
    }
    // Validate email format
    if (!validateEmail(body.email)) {
      return NextResponse.json({
        success: false,
        error: {
          code: 'VALIDATION_ERROR',
          message: 'Invalid email format',
          details: { field: 'email', value: body.email }
        }
      } as AdminApiResponse<never>, { status: 400 });
    }
    // Force role to admin (cannot create super admin through this endpoint)
    const adminRole = 'admin';
    const adminUtils = getAdminDatabaseUtils();
    // Check if email already exists
    const existingUsers = await adminUtils.getUsersWithRoleFilter({ search: body.email });
    if (existingUsers.data.length > 0) {
      return NextResponse.json({
        success: false,
        error: {
          code: 'EMAIL_ALREADY_EXISTS',
          message: 'A user with this email address already exists',
          details: { email: body.email }
        }
      } as AdminApiResponse<never>, { status: 409 });
    }
    // Hash password if provided
    let passwordHash: string | undefined;
    if (body.password) {
      passwordHash = await hashPassword(body.password);
    }
    // Create admin user
    const userId = await adminUtils.createUserWithRole({
      email: body.email,
      full_name: body.full_name,
      password_hash: passwordHash,
      role: adminRole,
      tenant_id: body.tenant_id || 'default',
      created_by: context.user.user_id

    // Get created user for response
    const createdUser = await adminUtils.getUserWithRole(userId);
    if (!createdUser) {
      throw new Error('Failed to retrieve created admin user');
    }
    // Log admin creation
    await adminUtils.createAuditLog({
      user_id: context.user.user_id,
      action: 'admin.create',
      resource_type: 'user',
      resource_id: userId,
      details: {
        email: body.email,
        role: adminRole,
        full_name: body.full_name,
        send_invitation: body.send_invitation,
        created_by: context.user.email
      },
      ip_address: request.headers.get('x-forwarded-for')?.split(',')[0] || 'unknown',
      user_agent: request.headers.get('user-agent') || undefined

    // Remove sensitive information from response
    const responseUser = {
      user_id: createdUser.user_id,
      email: createdUser.email,
      full_name: createdUser.full_name,
      role: createdUser.role,
      is_verified: createdUser.is_verified,
      is_active: createdUser.is_active,
      created_at: createdUser.created_at,
      updated_at: createdUser.updated_at,
      two_factor_enabled: createdUser.two_factor_enabled
    };
    const response: AdminApiResponse<{ admin: typeof responseUser; invitation_sent?: boolean }> = {
      success: true,
      data: {
        admin: responseUser,
        invitation_sent: body.send_invitation || false
      },
      meta: {
        message: 'Admin user created successfully',
        next_steps: body.send_invitation 
          ? ['Admin will receive invitation email', 'Admin must verify email and set password', 'Recommend enabling two-factor authentication']
          : body.password 
            ? ['Admin can log in immediately', 'Recommend enabling two-factor authentication']
            : ['Admin needs password set', 'Send invitation or provide temporary password']
      }
    };
    return NextResponse.json(response, { status: 201 });
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: {
        code: 'ADMIN_CREATION_FAILED',
        message: 'Failed to create admin user',
        details: { error: error instanceof Error ? error.message : 'Unknown error' }
      }
    } as AdminApiResponse<never>, { status: 500 });
  }
