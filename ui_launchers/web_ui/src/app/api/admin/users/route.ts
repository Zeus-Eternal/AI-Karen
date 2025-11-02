/**
 * User Management API Routes
 * GET /api/admin/users - List users with filtering and pagination
 * POST /api/admin/users - Create new user
 * 
 * Requirements: 4.2, 4.3, 4.4
 */
import { NextRequest, NextResponse } from 'next/server';
import { requireAdmin } from '@/lib/middleware/admin-auth';
import { getAdminDatabaseUtils } from '@/lib/database/admin-utils';
import { validateEmail, hashPassword } from '@/lib/auth/setup-validation';
import type {  AdminApiResponse, CreateUserRequest, UserListFilter, PaginationParams, User } from '@/types/admin';
/**
 * GET /api/admin/users - List users with filtering and pagination
 */
export const GET = requireAdmin(async (request: NextRequest, context) => {
  try {
    const { searchParams } = new URL(request.url);
    // Parse filter parameters
    const filter: UserListFilter = {
      role: searchParams.get('role') as 'super_admin' | 'admin' | 'user' | undefined,
      is_active: searchParams.get('is_active') ? searchParams.get('is_active') === 'true' : undefined,
      is_verified: searchParams.get('is_verified') ? searchParams.get('is_verified') === 'true' : undefined,
      search: searchParams.get('search') || undefined,
      created_after: searchParams.get('created_after') ? new Date(searchParams.get('created_after')!) : undefined,
      created_before: searchParams.get('created_before') ? new Date(searchParams.get('created_before')!) : undefined,
      last_login_after: searchParams.get('last_login_after') ? new Date(searchParams.get('last_login_after')!) : undefined,
      last_login_before: searchParams.get('last_login_before') ? new Date(searchParams.get('last_login_before')!) : undefined,
    };
    // Parse pagination parameters
    const pagination: PaginationParams = {
      page: parseInt(searchParams.get('page') || '1'),
      limit: Math.min(parseInt(searchParams.get('limit') || '20'), 100), // Max 100 per page
      sort_by: searchParams.get('sort_by') || 'created_at',
      sort_order: (searchParams.get('sort_order') as 'asc' | 'desc') || 'desc'
    };
    const adminUtils = getAdminDatabaseUtils();
    // Non-super admins cannot see super admin users
    if (!context.isSuperAdmin() && (!filter.role || filter.role === 'super_admin')) {
      if (filter.role === 'super_admin') {
        // Explicitly requesting super admins - deny access
        return NextResponse.json({
          success: false,
          error: {
            code: 'INSUFFICIENT_PERMISSIONS',
            message: 'Cannot access super admin user data',
            details: { required_role: 'super_admin' }
          }
        } as AdminApiResponse<never>, { status: 403 });
      }
      // Filter out super admins from general queries
      filter.role = filter.role || 'user';
    }
    const result = await adminUtils.getUsersWithRoleFilter(filter, pagination);
    // Remove sensitive information from response
    const sanitizedUsers = result.data.map((user: User) => ({
      user_id: user.user_id,
      email: user.email,
      full_name: user.full_name,
      role: user.role,
      roles: user.roles || [],
      tenant_id: user.tenant_id || 'default',
      preferences: user.preferences || {},
      is_verified: user.is_verified,
      is_active: user.is_active,
      created_at: user.created_at,
      updated_at: user.updated_at,
      last_login_at: user.last_login_at,
      two_factor_enabled: user.two_factor_enabled,
      failed_login_attempts: user.failed_login_attempts,
      locked_until: user.locked_until
    }));
    const response: AdminApiResponse<typeof result> = {
      success: true,
      data: {
        ...result,
        data: sanitizedUsers
      },
      meta: {
        filter_applied: filter,
        pagination_applied: pagination,
        total_filtered: result.pagination.total
      }
    };
    return NextResponse.json(response);
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: {
        code: 'USER_LIST_FAILED',
        message: 'Failed to retrieve user list',
        details: { error: error instanceof Error ? error.message : 'Unknown error' }
      }
    } as AdminApiResponse<never>, { status: 500 });
  }

/**
 * POST /api/admin/users - Create new user
 */
export const POST = requireAdmin(async (request: NextRequest, context) => {
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
    // Validate role permissions
    const requestedRole = body.role || 'user';
    if ((requestedRole as string) === 'super_admin') {
      return NextResponse.json({
        success: false,
        error: {
          code: 'INVALID_ROLE',
          message: 'Cannot create super admin users through this endpoint',
          details: { requested_role: requestedRole }
        }
      } as AdminApiResponse<never>, { status: 400 });
    }
    // Non-super admins cannot create admin users
    if (requestedRole === 'admin' && !context.isSuperAdmin()) {
      return NextResponse.json({
        success: false,
        error: {
          code: 'INSUFFICIENT_PERMISSIONS',
          message: 'Super admin role required to create admin users',
          details: { requested_role: requestedRole, user_role: context.user.role }
        }
      } as AdminApiResponse<never>, { status: 403 });
    }
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
    // Create user
    const userId = await adminUtils.createUserWithRole({
      email: body.email,
      full_name: body.full_name,
      password_hash: passwordHash,
      role: requestedRole,
      tenant_id: body.tenant_id || 'default',
      created_by: context.user.user_id

    // Get created user for response
    const createdUser = await adminUtils.getUserWithRole(userId);
    if (!createdUser) {
      throw new Error('Failed to retrieve created user');
    }
    // Log user creation
    await adminUtils.createAuditLog({
      user_id: context.user.user_id,
      action: 'user.create',
      resource_type: 'user',
      resource_id: userId,
      details: {
        email: body.email,
        role: requestedRole,
        full_name: body.full_name,
        send_invitation: body.send_invitation
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
    const response: AdminApiResponse<{ user: typeof responseUser; invitation_sent?: boolean }> = {
      success: true,
      data: {
        user: responseUser,
        invitation_sent: body.send_invitation || false
      },
      meta: {
        message: 'User created successfully',
        next_steps: body.send_invitation 
          ? ['User will receive invitation email', 'User must verify email and set password']
          : body.password 
            ? ['User can log in immediately', 'Recommend enabling two-factor authentication']
            : ['User needs password set', 'Send invitation or provide temporary password']
      }
    };
    return NextResponse.json(response, { status: 201 });
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: {
        code: 'USER_CREATION_FAILED',
        message: 'Failed to create user',
        details: { error: error instanceof Error ? error.message : 'Unknown error' }
      }
    } as AdminApiResponse<never>, { status: 500 });
  }
