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

// Rate limit cleanup interval (clean up every 5 minutes)
const RATE_LIMIT_CLEANUP_INTERVAL = 5 * 60 * 1000;

// Initialize rate limit cleanup
if (typeof global !== 'undefined') {
  setInterval(() => {
    const now = Date.now();
    for (const [key, value] of rateLimitStore.entries()) {
      if (now > value.resetTime) {
        rateLimitStore.delete(key);
      }
    }
  }, RATE_LIMIT_CLEANUP_INTERVAL);
}

export interface AdminAuthContext {
  user: User;
  hasPermission: (permission: string) => Promise<boolean>;
  hasRole: (role: 'super_admin' | 'admin' | 'user') => boolean;
  isAdmin: () => boolean;
  isSuperAdmin: () => boolean;
}

export interface AdminAuthOptions {
  requiredRole?: 'admin' | 'super_admin';
  requiredPermission?: string;
  rateLimit?: { limit: number; windowMs: number };
  skipAuditLog?: boolean;
}

export interface AdminAuthResult {
  success: boolean;
  user?: User;
  error?: {
    code: string;
    message: string;
    details?: Record<string, any>;
  };
  status?: number;
}

/**
 * Extract and validate session from request cookies
 */
async function validateAdminSession(request: NextRequest): Promise<User | null> {
  try {
    // Validate request URL
    if (!request.url) {
      console.error('Invalid request URL');
      return null;
    }

    // Forward session validation to existing auth endpoint
    const validateUrl = new URL('/api/auth/validate-session', request.url);
    
    const response = await fetch(validateUrl, {
      method: 'GET',
      headers: {
        'Cookie': request.headers.get('cookie') || '',
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      console.warn(`Session validation failed with status: ${response.status}`);
      return null;
    }

    const data = await response.json();
    
    if (!data.valid || !data.user) {
      console.warn('Invalid session or missing user data');
      return null;
    }

    const userData = data.user;
    
    // Ensure user has admin role
    if (!userData.role || !['admin', 'super_admin'].includes(userData.role)) {
      console.warn(`User role not authorized: ${userData.role}`);
      return null;
    }

    // Validate required user fields
    if (!userData.user_id || !userData.email) {
      console.warn('User missing required fields');
      return null;
    }

    return {
      user_id: userData.user_id,
      email: userData.email,
      full_name: userData.full_name || '',
      role: userData.role,
      roles: userData.roles || [userData.role],
      tenant_id: userData.tenant_id || 'default',
      preferences: userData.preferences || {},
      is_verified: Boolean(userData.is_verified),
      is_active: Boolean(userData.is_active),
      created_at: new Date(userData.created_at),
      updated_at: new Date(userData.updated_at),
      last_login_at: userData.last_login_at ? new Date(userData.last_login_at) : undefined,
      failed_login_attempts: userData.failed_login_attempts || 0,
      locked_until: userData.locked_until ? new Date(userData.locked_until) : undefined,
      two_factor_enabled: Boolean(userData.two_factor_enabled),
      created_by: userData.created_by
    };
  } catch (error) {
    console.error('Session validation error:', error);
    return null;
  }
}

/**
 * Rate limiting for admin endpoints
 */
function checkRateLimit(
  request: NextRequest, 
  limit: number = 100, 
  windowMs: number = 60000
): { allowed: boolean; remaining: number; resetTime: number } {
  const clientIP = getClientIP(request);
  const key = `admin_rate_limit:${clientIP}:${request.nextUrl.pathname}`;
  const now = Date.now();
  
  let current = rateLimitStore.get(key);
  
  if (!current || now > current.resetTime) {
    // Reset or initialize rate limit
    current = { count: 1, resetTime: now + windowMs };
    rateLimitStore.set(key, current);
    return {
      allowed: true,
      remaining: limit - 1,
      resetTime: current.resetTime
    };
  }
  
  if (current.count >= limit) {
    return {
      allowed: false,
      remaining: 0,
      resetTime: current.resetTime
    };
  }
  
  current.count++;
  return {
    allowed: true,
    remaining: limit - current.count,
    resetTime: current.resetTime
  };
}

/**
 * Extract client IP address from request
 */
function getClientIP(request: NextRequest): string {
  try {
    const forwarded = request.headers.get('x-forwarded-for');
    const realIP = request.headers.get('x-real-ip');
    const remoteAddr = request.headers.get('remote-addr');
    const cfConnectingIP = request.headers.get('cf-connecting-ip');
    
    // Cloudflare
    if (cfConnectingIP) {
      return cfConnectingIP.split(',')[0].trim();
    }
    
    // Standard proxy headers
    if (forwarded) {
      return forwarded.split(',')[0].trim();
    }
    
    return realIP || remoteAddr || 'unknown';
  } catch (error) {
    return 'unknown';
  }
}

/**
 * Create admin authentication context
 */
async function createAdminContext(user: User): Promise<AdminAuthContext> {
  const adminUtils = getAdminDatabaseUtils();
  
  try {
    const permissions = await adminUtils.getUserPermissions(user.user_id);
    const permissionNames = permissions.map(p => p.name);
    
    return {
      user,
      hasPermission: async (permission: string): Promise<boolean> => {
        // Super admins have all permissions
        if (user.role === 'super_admin') return true;
        return permissionNames.includes(permission);
      },
      hasRole: (role: 'super_admin' | 'admin' | 'user') => user.role === role,
      isAdmin: () => ['admin', 'super_admin'].includes(user.role),
      isSuperAdmin: () => user.role === 'super_admin'
    };
  } catch (error) {
    console.error('Error creating admin context:', error);
    // Return context with basic role checks if permission fetch fails
    return {
      user,
      hasPermission: async () => false,
      hasRole: (role: 'super_admin' | 'admin' | 'user') => user.role === role,
      isAdmin: () => ['admin', 'super_admin'].includes(user.role),
      isSuperAdmin: () => user.role === 'super_admin'
    };
  }
}

/**
 * Create standardized error response
 */
function createErrorResponse(
  code: string,
  message: string,
  status: number,
  details?: Record<string, any>
): NextResponse {
  return NextResponse.json({
    success: false,
    error: {
      code,
      message,
      details
    }
  } as AdminApiResponse<never>, { status });
}

/**
 * Log admin API access
 */
async function logAdminAccess(
  user: User,
  request: NextRequest,
  options: AdminAuthOptions
): Promise<void> {
  if (options.skipAuditLog) {
    return;
  }

  try {
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
        required_permission: options.requiredPermission,
        query_params: Object.fromEntries(request.nextUrl.searchParams)
      },
      ip_address: getClientIP(request),
      user_agent: request.headers.get('user-agent') || undefined
    });
  } catch (error) {
    console.error('Failed to log admin access:', error);
    // Don't fail the request if logging fails
  }
}

/**
 * Admin authentication middleware
 */
export async function withAdminAuth<T>(
  request: NextRequest,
  handler: (request: NextRequest, context: AdminAuthContext) => Promise<NextResponse>,
  options: AdminAuthOptions = {}
): Promise<NextResponse> {
  try {
    // Check rate limiting
    const rateLimitConfig = options.rateLimit || { limit: 100, windowMs: 60000 };
    const rateLimitResult = checkRateLimit(request, rateLimitConfig.limit, rateLimitConfig.windowMs);
    
    if (!rateLimitResult.allowed) {
      return createErrorResponse(
        'RATE_LIMIT_EXCEEDED',
        'Too many requests. Please try again later.',
        429,
        { 
          limit: rateLimitConfig.limit, 
          windowMs: rateLimitConfig.windowMs,
          resetTime: new Date(rateLimitResult.resetTime).toISOString()
        }
      );
    }

    // Validate admin session
    const user = await validateAdminSession(request);
    if (!user) {
      return createErrorResponse(
        'UNAUTHORIZED',
        'Valid admin session required',
        401,
        { required_role: 'admin' }
      );
    }

    // Create admin context
    const context = await createAdminContext(user);

    // Check required role
    if (options.requiredRole) {
      if (options.requiredRole === 'super_admin' && !context.isSuperAdmin()) {
        return createErrorResponse(
          'INSUFFICIENT_PERMISSIONS',
          'Super admin role required',
          403,
          { required_role: 'super_admin', user_role: user.role }
        );
      }
      
      if (options.requiredRole === 'admin' && !context.isAdmin()) {
        return createErrorResponse(
          'INSUFFICIENT_PERMISSIONS',
          'Admin role required',
          403,
          { required_role: 'admin', user_role: user.role }
        );
      }
    }

    // Check required permission
    if (options.requiredPermission) {
      const hasPermission = await context.hasPermission(options.requiredPermission);
      if (!hasPermission) {
        return createErrorResponse(
          'INSUFFICIENT_PERMISSIONS',
          'Required permission not granted',
          403,
          { 
            required_permission: options.requiredPermission, 
            user_role: user.role 
          }
        );
      }
    }

    // Log admin API access
    await logAdminAccess(user, request, options);

    // Add rate limit headers to successful responses
    const response = await handler(request, context);
    
    // Add rate limit headers
    response.headers.set('X-RateLimit-Limit', rateLimitConfig.limit.toString());
    response.headers.set('X-RateLimit-Remaining', rateLimitResult.remaining.toString());
    response.headers.set('X-RateLimit-Reset', Math.ceil(rateLimitResult.resetTime / 1000).toString());
    
    return response;

  } catch (error) {
    console.error('Admin auth middleware error:', error);
    
    return createErrorResponse(
      'INTERNAL_SERVER_ERROR',
      'Internal server error during authentication',
      500,
      { 
        error_message: error instanceof Error ? error.message : 'Unknown error',
        path: request.nextUrl.pathname
      }
    );
  }
}

/**
 * Simplified admin auth wrapper for basic admin access
 */
export function requireAdmin(
  handler: (request: NextRequest, context: AdminAuthContext) => Promise<NextResponse>,
  options: Omit<AdminAuthOptions, 'requiredRole'> = {}
) {
  return (request: NextRequest) => 
    withAdminAuth(request, handler, { ...options, requiredRole: 'admin' });
}

/**
 * Simplified admin auth wrapper for super admin access
 */
export function requireSuperAdmin(
  handler: (request: NextRequest, context: AdminAuthContext) => Promise<NextResponse>,
  options: Omit<AdminAuthOptions, 'requiredRole'> = {}
) {
  return (request: NextRequest) => 
    withAdminAuth(request, handler, { ...options, requiredRole: 'super_admin' });
}

/**
 * Admin auth wrapper with custom permission requirement
 */
export function requirePermission(
  permission: string,
  handler: (request: NextRequest, context: AdminAuthContext) => Promise<NextResponse>,
  options: Omit<AdminAuthOptions, 'requiredPermission'> = {}
) {
  return (request: NextRequest) => 
    withAdminAuth(request, handler, { ...options, requiredPermission: permission });
}

/**
 * Legacy admin auth middleware function for backward compatibility
 * Returns auth result object instead of NextResponse
 */
export async function adminAuthMiddleware(
  request: NextRequest,
  requiredRole?: 'admin' | 'super_admin' | string[] | string
): Promise<AdminAuthResult> {
  try {
    // Validate admin session
    const user = await validateAdminSession(request);
    if (!user) {
      return {
        success: false,
        error: { 
          code: 'UNAUTHORIZED', 
          message: 'Valid admin session required' 
        },
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
            error: { 
              code: 'INSUFFICIENT_PERMISSIONS', 
              message: 'Super admin role required' 
            },
            status: 403
          };
        }
        if (requiredRole === 'admin' && !context.isAdmin()) {
          return {
            success: false,
            error: { 
              code: 'INSUFFICIENT_PERMISSIONS', 
              message: 'Admin role required' 
            },
            status: 403
          };
        }
      } else if (Array.isArray(requiredRole)) {
        if (!requiredRole.includes(user.role)) {
          return {
            success: false,
            error: { 
              code: 'INSUFFICIENT_PERMISSIONS', 
              message: 'Required role not granted' 
            },
            status: 403
          };
        }
      }
    }

    return { success: true, user };
  } catch (error) {
    console.error('Admin auth middleware error:', error);
    
    return {
      success: false,
      error: { 
        code: 'INTERNAL_SERVER_ERROR', 
        message: 'Authentication error',
        details: {
          error_message: error instanceof Error ? error.message : 'Unknown error'
        }
      },
      status: 500
    };
  }
}

/**
 * Utility function to check if a request is from an admin
 */
export async function isAdminRequest(request: NextRequest): Promise<boolean> {
  try {
    const user = await validateAdminSession(request);
    return user !== null && ['admin', 'super_admin'].includes(user.role);
  } catch {
    return false;
  }
}

/**
 * Get current admin user from request (for use in server components)
 */
export async function getCurrentAdmin(request: NextRequest): Promise<User | null> {
  return await validateAdminSession(request);
}

/**
 * Clear rate limit for a specific IP (useful for testing)
 */
export function clearRateLimit(ip: string, pathname?: string): void {
  if (pathname) {
    const key = `admin_rate_limit:${ip}:${pathname}`;
    rateLimitStore.delete(key);
  } else {
    // Clear all rate limits for this IP
    for (const key of rateLimitStore.keys()) {
      if (key.startsWith(`admin_rate_limit:${ip}:`)) {
        rateLimitStore.delete(key);
      }
    }
  }
}

/**
 * Get rate limit info for monitoring
 */
export function getRateLimitInfo(): Array<{
  key: string;
  count: number;
  resetTime: number;
  remaining: number;
}> {
  const info: Array<{
    key: string;
    count: number;
    resetTime: number;
    remaining: number;
  }> = [];

  for (const [key, value] of rateLimitStore.entries()) {
    const limit = 100; // Default limit
    info.push({
      key,
      count: value.count,
      resetTime: value.resetTime,
      remaining: Math.max(0, limit - value.count)
    });
  }
  
  return info;
}