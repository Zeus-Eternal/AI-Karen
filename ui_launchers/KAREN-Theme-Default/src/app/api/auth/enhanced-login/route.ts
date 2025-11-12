// app/api/auth/enhanced/route.ts
/**
 * Enhanced Login API Endpoint
 *
 * Implements secure authentication with progressive delays, account lockout,
 * MFA enforcement, session management, and IP security.
 *
 * Requirements: 5.4, 5.5, 5.6
 */
import { NextRequest, NextResponse } from 'next/server';
import { enhancedAuthMiddleware } from '@/lib/security/enhanced-auth-middleware';
import { securityManager } from '@/lib/security/security-manager';
import { ipSecurityManager } from '@/lib/security/ip-security-manager';
import type { AdminApiResponse } from '@/types/admin';
import type { BlockedIpEntry } from '@/lib/database/admin-utils';

interface LoginRequest {
  email: string;
  password: string;
  totp_code?: string;
  remember_me?: boolean;
}

interface LoginResponse {
  user: {
    user_id: string;
    email: string;
    full_name?: string;
    role: string;
    two_factor_enabled: boolean;
  };
  session_token: string;
  expires_at: string;
  mfa_required: boolean;
  session_timeout: number;
}

interface SessionValidationResponse {
  valid: true;
  user: {
    user_id: string;
    email: string;
    full_name?: string;
    role: string;
    two_factor_enabled: boolean;
  };
  session: {
    expires_at: string;
    time_remaining: number;
    warning_active: boolean;
  };
  security: {
    mfa_required: boolean;
    mfa_verified: boolean;
    ip_address: string;
  };
}

const SESSION_COOKIE = 'session_token';

export async function POST(request: NextRequest): Promise<NextResponse> {
  // Parse body safely
  let body: LoginRequest | null = null;
  try {
    body = (await request.json()) as LoginRequest;
  } catch {
    return jsonError('MALFORMED_BODY', 'Invalid JSON body', 400);
  }

  const { email, password, totp_code, remember_me } = body ?? ({} as LoginRequest);

  // Validate required fields
  const missing: string[] = [];
  if (!email) missing.push('email');
  if (!password) missing.push('password');
  if (missing.length) {
    return NextResponse.json(
      {
        success: false,
        error: {
          code: 'MISSING_CREDENTIALS',
          message: 'Email and password are required',
          details: { missing_fields: missing },
        },
      } as AdminApiResponse<never>,
      withCommonHeaders(400),
    );
  }

  // Extract client information
  const ipAddress = getClientIP(request);
  const userAgent = request.headers.get('user-agent') || undefined;

  // IP block check
  const blockedIps = await ipSecurityManager.getBlockedIps().catch<BlockedIpEntry[]>(() => []);
  const blockInfo = blockedIps.find((entry) => entry.ipAddress === ipAddress);
  if (blockInfo) {
    return NextResponse.json(
      {
        success: false,
        error: {
          code: 'IP_BLOCKED',
          message: 'IP address is temporarily blocked',
          details: {
            ip_address: ipAddress,
            blocked_until: blockInfo?.expiresAt,
            reason: blockInfo?.reason,
          },
        },
      } as AdminApiResponse<never>,
      withCommonHeaders(429),
    );
  }

  // Attempt authentication (progressive delays, lockout, MFA handled in middleware)
  const authResult = await enhancedAuthMiddleware.authenticateUser(
    email,
    password,
    totp_code,
    ipAddress,
    userAgent,
  );

  // Failure path
  if (!authResult.success) {
    const statusCode = getStatusCodeForError(authResult.error?.code);

    // Apply server-side delay (progressive throttling)
    const delaySec = Number(authResult.delay || 0);
    if (delaySec > 0) {
      await new Promise((r) => setTimeout(r, delaySec * 1000));
    }

    return NextResponse.json(
      {
        success: false,
        error: authResult.error,
        meta: {
          delay_applied: delaySec,
          mfa_required: Boolean(authResult.mfaRequired),
          ip_address: ipAddress,
        },
      } as AdminApiResponse<never>,
      withCommonHeaders(statusCode),
    );
  }

  // Success path
  const { user, sessionToken } = authResult;
  if (!user || !sessionToken) {
    return jsonError('AUTHENTICATION_ERROR', 'Authentication succeeded but user data is missing', 500);
  }

  // If middleware indicates MFA step-up still required, surface it (defensive)
  if (authResult.mfaRequired && !authResult.mfaVerified) {
    return NextResponse.json(
      {
        success: false,
        error: {
          code: 'MFA_CODE_REQUIRED',
          message: 'MFA required to complete login',
        },
        meta: {
          mfa_required: true,
          ip_address: ipAddress,
        },
      } as AdminApiResponse<never>,
      withCommonHeaders(403),
    );
  }

  // Session timeout by role
  const sessionTimeout = securityManager.getSessionTimeout(user.role);
  const expiresAt = new Date(Date.now() + sessionTimeout * 1000);

  const responseData: LoginResponse = {
    user: {
      user_id: user.user_id,
      email: user.email,
      full_name: user.full_name,
      role: user.role,
      two_factor_enabled: Boolean(user.two_factor_enabled),
    },
    session_token: sessionToken,
    expires_at: expiresAt.toISOString(),
    mfa_required: false,
    session_timeout: sessionTimeout,
  };

  // Build response
  const response = NextResponse.json(
    {
      success: true,
      data: responseData,
      meta: {
        login_time: new Date().toISOString(),
        ip_address: ipAddress,
        user_agent: userAgent,
        session_timeout: sessionTimeout,
      },
    } as AdminApiResponse<LoginResponse>,
    withCommonHeaders(200),
  );

  // Set secure session cookie
  response.cookies.set(SESSION_COOKIE, sessionToken, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'strict',
    maxAge: remember_me ? 30 * 24 * 60 * 60 : sessionTimeout, // 30d or role-based session
    path: '/',
  });

  // Security headers (defense-in-depth)
  setSecurityHeaders(response);

  return response;
}

/**
 * Enhanced logout endpoint
 */
export async function DELETE(request: NextRequest): Promise<NextResponse> {
  try {
    const sessionToken = extractSessionToken(request);
    if (!sessionToken) {
      return NextResponse.json(
        {
          success: false,
          error: { code: 'NO_SESSION', message: 'No active session to logout' },
        } as AdminApiResponse<never>,
        withCommonHeaders(400),
      );
    }

    const authContext = await enhancedAuthMiddleware.validateSession(sessionToken);
    if (authContext) {
      await enhancedAuthMiddleware.logout(sessionToken, authContext.user.user_id);
    }

    const response = NextResponse.json(
      {
        success: true,
        data: {
          message: 'Successfully logged out',
          logout_time: new Date().toISOString(),
        },
      } as AdminApiResponse<{ message: string; logout_time: string }>,
      withCommonHeaders(200),
    );

    // Clear cookie
    response.cookies.delete(SESSION_COOKIE);
    setSecurityHeaders(response);

    return response;
  } catch {
    return NextResponse.json(
      {
        success: false,
        error: { code: 'LOGOUT_ERROR', message: 'An error occurred during logout' },
      } as AdminApiResponse<never>,
      withCommonHeaders(500),
    );
  }
}

/**
 * Session validation endpoint
 */
export async function GET(request: NextRequest): Promise<NextResponse> {
  try {
    const sessionToken = extractSessionToken(request);
    if (!sessionToken) {
      return NextResponse.json(
        {
          success: false,
          error: { code: 'NO_SESSION_TOKEN', message: 'Session token required' },
        } as AdminApiResponse<never>,
        withCommonHeaders(401),
      );
    }

    const ipAddress = getClientIP(request);
    const authContext = await enhancedAuthMiddleware.validateSession(sessionToken, ipAddress);

    if (!authContext) {
      return NextResponse.json(
        {
          success: false,
          error: { code: 'INVALID_SESSION', message: 'Session is invalid or expired' },
        } as AdminApiResponse<never>,
        withCommonHeaders(401),
      );
    }

    const response: AdminApiResponse<{
      valid: true;
      user: {
        user_id: string;
        email: string;
        full_name?: string | null;
        role: string;
        two_factor_enabled: boolean;
      };
      session: {
        expires_at: string;
        time_remaining: number;
        warning_active: boolean;
      };
      security: {
        mfa_required: boolean;
        mfa_verified: boolean;
        ip_address?: string | null;
      };
    }> = {
      success: true,
      data: {
        valid: true,
        user: {
          user_id: authContext.user.user_id,
          email: authContext.user.email,
          full_name: authContext.user.full_name,
          role: authContext.user.role,
          two_factor_enabled: authContext.user.two_factor_enabled,
        },
        session: {
          expires_at: authContext.sessionStatus.expiresAt.toISOString(),
          time_remaining: authContext.sessionStatus.timeRemaining,
          warning_active: authContext.sessionStatus.warningActive,
        },
        security: {
          mfa_required: authContext.mfaRequired,
          mfa_verified: authContext.mfaVerified,
          ip_address: authContext.ipAddress,
        },
      },
    };

    return NextResponse.json(response, withCommonHeaders(200));
  } catch {
    return NextResponse.json(
      {
        success: false,
        error: { code: 'VALIDATION_ERROR', message: 'An error occurred during session validation' },
      } as AdminApiResponse<never>,
      withCommonHeaders(500),
    );
  }
}

/* ----------------------- Helpers ----------------------- */

function withCommonHeaders(status: number): ResponseInit {
  return {
    status,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'no-store, max-age=0',
      'Pragma': 'no-cache',
      'Expires': '0',
    },
  };
}

function setSecurityHeaders(res: NextResponse) {
  res.headers.set('X-Content-Type-Options', 'nosniff');
  res.headers.set('X-Frame-Options', 'DENY');
  res.headers.set('X-XSS-Protection', '1; mode=block');
  res.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
}

function getClientIP(request: NextRequest): string {
  const forwarded = request.headers.get('x-forwarded-for');
  const realIP = request.headers.get('x-real-ip');
  const remoteAddr = request.headers.get('remote-addr');
  if (forwarded) return forwarded.split(',')[0].trim();
  return realIP || remoteAddr || 'unknown';
}

function extractSessionToken(request: NextRequest): string | null {
  // Prefer cookie API (works on both Edge/Node runtimes)
  const cookieVal = request.cookies?.get?.(SESSION_COOKIE)?.value;
  if (cookieVal) return cookieVal;

  // Fallback to Authorization: Bearer
  const authHeader = request.headers.get('authorization');
  if (authHeader?.startsWith('Bearer ')) return authHeader.substring(7);

  // As a last resort, parse raw Cookie header
  const raw = request.headers.get('cookie');
  if (raw) {
    const match = raw.match(new RegExp(`${SESSION_COOKIE}=([^;]+)`));
    if (match) return match[1];
  }
  return null;
}

function getStatusCodeForError(errorCode?: string): number {
  switch (errorCode) {
    case 'ACCOUNT_LOCKED':
    case 'IP_ACCESS_DENIED':
    case 'SESSION_LIMIT_EXCEEDED':
      return 429; // Too Many Requests
    case 'INVALID_CREDENTIALS':
    case 'INVALID_MFA_CODE':
      return 401; // Unauthorized
    case 'MFA_SETUP_REQUIRED':
    case 'MFA_CODE_REQUIRED':
      return 403; // Forbidden (MFA step-up)
    case 'AUTHENTICATION_ERROR':
      return 500;
    default:
      return 500; // Internal Server Error
  }
}

function jsonError(code: string, message: string, status: number): NextResponse {
  return NextResponse.json(
    {
      success: false,
      error: { code, message },
    } as AdminApiResponse<never>,
    withCommonHeaders(status),
  );
}
