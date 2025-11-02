/**
 * Admin Authentication and Authorization Middleware
 * 
 * Provides role-based permission checking and security measures for admin API endpoints.
 * Requirements: 2.5, 6.4
 */
import { NextRequest, NextResponse } from 'next/server';
import { getAdminDatabaseUtils } from '@/lib/database/admin-utils';
import type { User, AdminApiResponse } from '@/types/admin';
// Rate limiting storage (in-memory for simplicity, use Redis in production)
const rateLimitStore = new Map<string, { count: number; resetTime: number }>();
export interface AdminAuthContext {
  user: User;
  hasPermission: (permission: string) => boolean;
  hasRole: (role: 'super_admin' | 'admin' | 'user') => boolean;
  isAdmin: () => boolean;
  isSuperAdmin: () => boolean;
}
/**
 * Extract and validate session from request cookies
 */
async function validateAdminSession(request: NextRequest): Promise<User | null> {
  try {
    // Forward session validation to existing auth endpoint
    const response = await fetch(new URL('/api/auth/validate-session', request.url), {
      method: 'GET',
      headers: {
        'Cookie': request.headers.get('cookie') || '',
        'Content-Type': 'application/json',
      },

    if (!response.ok) {
      return null;
    }
    const data = await response.json();
    if (!data.valid || !data.user) {
      return null;
    }
    const userData = data.user;
    // Ensure user has admin role
    if (!userData.role || !['admin', 'super_admin'].includes(userData.role)) {
      return null;
    }
    return {
      user_id: userData.user_id,
      email: userData.email,
      full_name: userData.full_name,
      role: userData.role,
      roles: userData.roles || [userData.role],
      tenant_id: userData.tenant_id,
      preferences: userData.preferences || {},
      is_verified: userData.is_verified,
      is_active: userData.is_active,
      created_at: new Date(userData.created_at),
      updated_at: new Date(userData.updated_at),
      last_login_at: userData.last_login_at ? new Date(userData.last_login_at) : undefined,
      failed_login_attempts: userData.failed_login_attempts || 0,
      locked_until: userData.locked_until ? new Date(userData.locked_until) : undefined,
      two_factor_enabled: userData.two_factor_enabled || false,
      created_by: userData.created_by
    };
  } catch (error) {
    return null;
  }
}
/**
 * Rate limiting for admin endpoints
 */
function checkRateLimit(request: NextRequest, limit: number = 100, windowMs: number = 60000): boolean {
  const clientIP = getClientIP(request);
  const key = `admin_rate_limit:${clientIP}`;
  const now = Date.now();
  const current = rateLimitStore.get(key);
  if (!current || now > current.resetTime) {
    // Reset or initialize rate limit
    rateLimitStore.set(key, { count: 1, resetTime: now + windowMs });
    return true;
  }
  if (current.count >= limit) {
    return false;
  }
  current.count++;
  return true;
}
/**
 * Extract client IP address from request
 */
function getClientIP(request: NextRequest): string {
  const forwarded = request.headers.get('x-forwarded-for');
  const realIP = request.headers.get('x-real-ip');
  const remoteAddr = request.headers.get('remote-addr');
  if (forwarded) {
    return forwarded.split(',')[0].trim();
  }
  return realIP || remoteAddr || 'unknown';
}
/**
 * Create admin authentication context
 */
async function createAdminContext(user: User): Promise<AdminAuthContext> {
  const adminUtils = getAdminDatabaseUtils();
  const permissions = await adminUtils.getUserPermissions(user.user_id);
  const permissionNames = permissions.map(p => p.name);
  return {
    user,
    hasPermission: (permission: string) => {
      // Super admins have all permissions
      if (user.role === 'super_admin') return true;
      return permissionNames.includes(permission);
    },
    hasRole: (role: 'super_admin' | 'admin' | 'user') => user.role === role,
    isAdmin: () => ['admin', 'super_admin'].includes(user.role),
    isSuperAdmin: () => user.role === 'super_admin'
  };
}
/**
 * Admin authentication middleware
 */
export async function withAdminAuth<T>(
  request: NextRequest,
  handler: (request: NextRequest, context: AdminAuthContext) => Promise<NextResponse>,
  options: {
    requiredRole?: 'admin' | 'super_admin';
    requiredPermission?: string;
    rateLimit?: { limit: number; windowMs: number };
  } = {}
): Promise<NextResponse> {
  try {
    // Check rate limiting
    const rateLimitConfig = options.rateLimit || { limit: 100, windowMs: 60000 };
    if (!checkRateLimit(request, rateLimitConfig.limit, rateLimitConfig.windowMs)) {
      return NextResponse.json({
        success: false,
        error: {
          code: 'RATE_LIMIT_EXCEEDED',
          message: 'Too many requests. Please try again later.',
          details: { limit: rateLimitConfig.limit, windowMs: rateLimitConfig.windowMs }
        }
      } as AdminApiResponse<never>, { status: 429 });
    }
    // Validate admin session
    const user = await validateAdminSession(request);
    if (!user) {
      return NextResponse.json({
        success: false,
        error: {
          code: 'UNAUTHORIZED',
          message: 'Valid admin session required',
          details: { required_role: 'admin' }
        }
      } as AdminApiResponse<never>, { status: 401 });
    }
    // Create admin context
    const context = await createAdminContext(user);
    // Check required role
    if (options.requiredRole) {
      if (options.requiredRole === 'super_admin' && !context.isSuperAdmin()) {
        return NextResponse.json({
          success: false,
          error: {
            code: 'INSUFFICIENT_PERMISSIONS',
            message: 'Super admin role required',
            details: { required_role: 'super_admin', user_role: user.role }
          }
        } as AdminApiResponse<never>, { status: 403 });
      }
      if (options.requiredRole === 'admin' && !context.isAdmin()) {
        return NextResponse.json({
          success: false,
          error: {
            code: 'INSUFFICIENT_PERMISSIONS',
            message: 'Admin role required',
            details: { required_role: 'admin', user_role: user.role }
          }
        } as AdminApiResponse<never>, { status: 403 });
      }
    }
    // Check required permission
    if (options.requiredPermission && !context.hasPermission(options.requiredPermission)) {
      return NextResponse.json({
        success: false,
        error: {
          code: 'INSUFFICIENT_PERMISSIONS',
          message: 'Required permission not granted',
          details: { required_permission: options.requiredPermission, user_role: user.role }
        }
      } as AdminApiResponse<never>, { status: 403 });
    }
    // Log admin API access
    const adminUtils = getAdminDatabaseUtils();
    await adminUtils.createAuditLog({
      user_id: user.user_id,
      action: 'admin_api.access',
      resource_type: 'api_endpoint',
      resource_id: request.nextUrl.pathname,
      details: {
        method: request.method,
        endpoint: request.nextUrl.pathname,
        user_agent: request.headers.get('user-agent'),
        required_role: options.requiredRole,
        required_permission: options.requiredPermission
      },
      ip_address: getClientIP(request),
      user_agent: request.headers.get('user-agent') || undefined

    // Call the handler with admin context
    return await handler(request, context);
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: {
        code: 'INTERNAL_SERVER_ERROR',
        message: 'Internal server error during authentication',
        details: { error_message: error instanceof Error ? error.message : 'Unknown error' }
      }
    } as AdminApiResponse<never>, { status: 500 });
  }
}
/**
 * Simplified admin auth wrapper for basic admin access
 */
export function requireAdmin<T>(
  handler: (request: NextRequest, context: AdminAuthContext) => Promise<NextResponse>
) {
  return (request: NextRequest) => withAdminAuth(request, handler, { requiredRole: 'admin' });
}
/**
 * Simplified admin auth wrapper for super admin access
 */
export function requireSuperAdmin<T>(
  handler: (request: NextRequest, context: AdminAuthContext) => Promise<NextResponse>
) {
  return (request: NextRequest) => withAdminAuth(request, handler, { requiredRole: 'super_admin' });
}
/**
 * Admin auth wrapper with custom permission requirement
 */
export function requirePermission<T>(
  permission: string,
  handler: (request: NextRequest, context: AdminAuthContext) => Promise<NextResponse>
) {
  return (request: NextRequest) => withAdminAuth(request, handler, { requiredPermission: permission });
}
/**
 * Legacy admin auth middleware function for backward compatibility
 * Returns auth result object instead of NextResponse
 */
export async function adminAuthMiddleware(
  request: NextRequest,
  requiredRole?: 'admin' | 'super_admin' | string[] | string
): Promise<{ success: boolean; user?: User; error?: any; status?: number }> {
  try {
    // Validate admin session
    const user = await validateAdminSession(request);
    if (!user) {
      return {
        success: false,
        error: { code: 'UNAUTHORIZED', message: 'Valid admin session required' },
        status: 401
      };
    }
    // Create admin context for permission checking
    const context = await createAdminContext(user);
    // Handle different role requirement formats
    if (requiredRole) {
      if (typeof requiredRole === 'string') {
        if (requiredRole === 'super_admin' && !context.isSuperAdmin()) {
          return {
            success: false,
            error: { code: 'INSUFFICIENT_PERMISSIONS', message: 'Super admin role required' },
            status: 403
          };
        }
        if (requiredRole === 'admin' && !context.isAdmin()) {
          return {
            success: false,
            error: { code: 'INSUFFICIENT_PERMISSIONS', message: 'Admin role required' },
            status: 403
          };
        }
      } else if (Array.isArray(requiredRole)) {
        if (!requiredRole.includes(user.role)) {
          return {
            success: false,
            error: { code: 'INSUFFICIENT_PERMISSIONS', message: 'Required role not granted' },
            status: 403
          };
        }
      }
    }
    return { success: true, user };
  } catch (error) {
    return {
      success: false,
      error: { code: 'INTERNAL_SERVER_ERROR', message: 'Authentication error' },
      status: 500
    };
  }
}
