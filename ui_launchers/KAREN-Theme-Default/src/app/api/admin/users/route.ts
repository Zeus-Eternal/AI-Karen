// app/api/admin/users/route.ts
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
import type {
  AdminApiResponse,
  CreateUserRequest,
  UserListFilter,
  PaginationParams,
  User,
} from '@/types/admin';

// ---------- helpers ----------
const MAX_LIMIT = 100;
const DEFAULT_LIMIT = 20;

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

function parseDateSafe(value: string | null): Date | undefined {
  if (!value) return undefined;
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? undefined : d;
}

function clampPage(n: number) {
  return Number.isFinite(n) && n > 0 ? Math.floor(n) : 1;
}
function clampLimit(n: number) {
  const v = Number.isFinite(n) && n > 0 ? Math.floor(n) : DEFAULT_LIMIT;
  return Math.min(v, MAX_LIMIT);
}

function sanitizeUser(u: User) {
  return {
    user_id: u.user_id,
    email: u.email,
    full_name: u.full_name,
    role: u.role,
    roles: u.roles || [],
    tenant_id: u.tenant_id || 'default',
    preferences: u.preferences || {},
    is_verified: u.is_verified,
    is_active: u.is_active,
    created_at: u.created_at,
    updated_at: u.updated_at,
    last_login_at: u.last_login_at,
    two_factor_enabled: u.two_factor_enabled,
    failed_login_attempts: u.failed_login_attempts,
    locked_until: u.locked_until,
  };
}

/**
 * GET /api/admin/users - List users with filtering and pagination
 */
export const GET = requireAdmin(async (request: NextRequest, context) => {
  try {
    const { searchParams } = new URL(request.url);

    // Parse filter parameters (date-safe)
    const filter: UserListFilter = {
      role: ((): 'super_admin' | 'admin' | 'user' | undefined => {
        const r = searchParams.get('role');
        return r === 'super_admin' || r === 'admin' || r === 'user' ? r : undefined;
      })(),
      is_active: searchParams.get('is_active') ? searchParams.get('is_active') === 'true' : undefined,
      is_verified: searchParams.get('is_verified') ? searchParams.get('is_verified') === 'true' : undefined,
      search: searchParams.get('search') || undefined,
      created_after: parseDateSafe(searchParams.get('created_after')),
      created_before: parseDateSafe(searchParams.get('created_before')),
      last_login_after: parseDateSafe(searchParams.get('last_login_after')),
      last_login_before: parseDateSafe(searchParams.get('last_login_before')),
    };

    // Parse pagination parameters (clamped)
    const pagination: PaginationParams = {
      page: clampPage(parseInt(searchParams.get('page') || '1', 10)),
      limit: clampLimit(parseInt(searchParams.get('limit') || String(DEFAULT_LIMIT), 10)),
      sort_by: searchParams.get('sort_by') || 'created_at',
      sort_order: ((): 'asc' | 'desc' => (searchParams.get('sort_order') === 'asc' ? 'asc' : 'desc'))(),
    };

    const adminUtils = getAdminDatabaseUtils();

    // RBAC: Non-super admins cannot request super_admin explicitly
    if (!context.isSuperAdmin() && filter.role === 'super_admin') {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'INSUFFICIENT_PERMISSIONS',
            message: 'Cannot access super admin user data',
            details: { required_role: 'super_admin' },
          },
        } as AdminApiResponse<never>,
        noStore({ status: 403 }),
      );
    }

    const result = await adminUtils.getUsersWithRoleFilter(filter, pagination);

    // RBAC post-filter: if caller is not super_admin, hide any super_admin users from the result set
    const visible = context.isSuperAdmin()
      ? result.data
      : result.data.filter((u: User) => u.role !== 'super_admin');

    const sanitizedUsers = visible.map(sanitizeUser);

    const response: AdminApiResponse<typeof result> = {
      success: true,
      data: {
        ...result,
        data: sanitizedUsers,
      },
      meta: {
        filter_applied: filter,
        pagination_applied: pagination,
        total_filtered: (result.pagination?.total as number) ?? sanitizedUsers.length,
      },
    };

    return NextResponse.json(response, noStore());
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: {
          code: 'USER_LIST_FAILED',
          message: 'Failed to retrieve user list',
          details: { error: error instanceof Error ? error.message : 'Unknown error' },
        },
      } as AdminApiResponse<never>,
      noStore({ status: 500 }),
    );
  }
});

/**
 * POST /api/admin/users - Create new user
 */
export const POST = requireAdmin(async (request: NextRequest, context) => {
  try {
    const body: CreateUserRequest = await request.json();

    // Validate required fields
    if (!body.email) {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Email is required',
            details: { field: 'email' },
          },
        } as AdminApiResponse<never>,
        noStore({ status: 400 }),
      );
    }

    // Validate email format
    if (!validateEmail(body.email)) {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Invalid email format',
            details: { field: 'email', value: body.email },
          },
        } as AdminApiResponse<never>,
        noStore({ status: 400 }),
      );
    }

    const rawRole = body.role as string | undefined;
    // Validate role permissions
    const requestedRole: 'user' | 'admin' = rawRole === 'admin' ? 'admin' : 'user';

    // Disallow creating super_admin via this endpoint (defense in depth)
    if (rawRole === 'super_admin') {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'INVALID_ROLE',
            message: 'Cannot create super admin users through this endpoint',
            details: { requested_role: body.role },
          },
        } as AdminApiResponse<never>,
        noStore({ status: 400 }),
      );
    }

    // Non-super admins cannot create admin users
    if (requestedRole === 'admin' && !context.isSuperAdmin()) {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'INSUFFICIENT_PERMISSIONS',
            message: 'Super admin role required to create admin users',
            details: { requested_role: requestedRole, user_role: context.user.role },
          },
        } as AdminApiResponse<never>,
        noStore({ status: 403 }),
      );
    }

    const adminUtils = getAdminDatabaseUtils();

    // Email uniqueness (prefer exact lookup if available)
    let emailExists = false;
    if (typeof adminUtils.findUserByEmail === 'function') {
      const found = await adminUtils.findUserByEmail(body.email);
      emailExists = !!found;
    } else {
      const existing = await adminUtils.getUsersWithRoleFilter({ search: body.email });
      emailExists =
        existing?.data?.some(
          (u: User) => String(u.email).toLowerCase() === String(body.email).toLowerCase(),
        ) || false;
    }

    if (emailExists) {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'EMAIL_ALREADY_EXISTS',
            message: 'A user with this email address already exists',
            details: { email: body.email },
          },
        } as AdminApiResponse<never>,
        noStore({ status: 409 }),
      );
    }

    // Hash password if provided
    let passwordHash: string | undefined;
    if (body.password) {
      passwordHash = await hashPassword(body.password);
    }

    // Create user
    const userId: string = await adminUtils.createUserWithRole({
      email: body.email,
      full_name: body.full_name,
      password_hash: passwordHash,
      role: requestedRole,
      tenant_id: body.tenant_id || 'default',
      created_by: context.user.user_id,
    });

    // Fetch created user for response
    const createdUser: User | null = await adminUtils.getUserWithRole(userId);
    if (!createdUser) {
      throw new Error('Failed to retrieve created user');
    }

    // Audit log
    await adminUtils.createAuditLog({
      user_id: context.user.user_id,
      action: 'user.create',
      resource_type: 'user',
      resource_id: userId,
      details: {
        email: body.email,
        role: requestedRole,
        full_name: body.full_name,
        send_invitation: body.send_invitation,
      },
      ip_address: request.headers.get('x-forwarded-for')?.split(',')[0] || 'unknown',
      user_agent: request.headers.get('user-agent') || undefined,
    });

    // Build response
    const responseUser = sanitizeUser(createdUser);
    const response: AdminApiResponse<{ user: typeof responseUser; invitation_sent?: boolean }> = {
      success: true,
      data: {
        user: responseUser,
        invitation_sent: body.send_invitation || false,
      },
      meta: {
        message: 'User created successfully',
        next_steps: body.send_invitation
          ? ['User will receive invitation email', 'User must verify email and set password']
          : body.password
          ? ['User can log in immediately', 'Recommend enabling two-factor authentication']
          : ['User needs password set', 'Send invitation or provide temporary password'],
      },
    };

    return NextResponse.json(response, noStore({ status: 201 }));
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: {
          code: 'USER_CREATION_FAILED',
          message: 'Failed to create user',
          details: { error: error instanceof Error ? error.message : 'Unknown error' },
        },
      } as AdminApiResponse<never>,
      noStore({ status: 500 }),
    );
  }
});
