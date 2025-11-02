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

export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    const body = await request.json() as LoginRequest;
    const { email, password, totp_code, remember_me } = body;

    // Validate required fields
    if (!email || !password) {
      return NextResponse.json({
        success: false,
        error: {
          code: 'MISSING_CREDENTIALS',
          message: 'Email and password are required',
          details: { 
            missing_fields: [
              !email && 'email',
              !password && 'password'
            ].filter(Boolean)
          }
        }
      } as AdminApiResponse<never>, { status: 400 });
    }

    // Extract client information
    const ipAddress = getClientIP(request);
    const userAgent = request.headers.get('user-agent') || undefined;

    // Check if IP is currently blocked
    const blockedIps = ipSecurityManager.getBlockedIps();
    const isBlocked = blockedIps.some(blocked => blocked.ip === ipAddress);
    
    if (isBlocked) {
      const blockInfo = blockedIps.find(blocked => blocked.ip === ipAddress);
      return NextResponse.json({
        success: false,
        error: {
          code: 'IP_BLOCKED',
          message: 'IP address is temporarily blocked',
          details: {
            ip_address: ipAddress,
            blocked_until: blockInfo?.blockedUntil,
            reason: blockInfo?.reason
          }
        }
      } as AdminApiResponse<never>, { status: 429 });
    }

    // Attempt authentication with enhanced security
    const authResult = await enhancedAuthMiddleware.authenticateUser(
      email,
      password,
      totp_code,
      ipAddress,
      userAgent
    );

    // Handle authentication failure
    if (!authResult.success) {
      const statusCode = getStatusCodeForError(authResult.error?.code);
      
      // Apply delay if specified
      if (authResult.delay && authResult.delay > 0) {
        await new Promise(resolve => setTimeout(resolve, (authResult.delay || 0) * 1000));
      }

      return NextResponse.json({
        success: false,
        error: authResult.error,
        meta: {
          delay_applied: authResult.delay || 0,
          mfa_required: authResult.mfaRequired || false,
          ip_address: ipAddress
        }
      } as AdminApiResponse<never>, { status: statusCode });
    }

    // Successful authentication
    const { user, sessionToken } = authResult;
    
    if (!user || !sessionToken) {
      return NextResponse.json({
        success: false,
        error: {
          code: 'AUTHENTICATION_ERROR',
          message: 'Authentication succeeded but user data is missing'
        }
      } as AdminApiResponse<never>, { status: 500 });
    }

    // Get session timeout for user role
    const sessionTimeout = securityManager.getSessionTimeout(user.role);
    const expiresAt = new Date(Date.now() + sessionTimeout * 1000);

    // Prepare response data
    const responseData: LoginResponse = {
      user: {
        user_id: user.user_id,
        email: user.email,
        full_name: user.full_name,
        role: user.role,
        two_factor_enabled: user.two_factor_enabled
      },
      session_token: sessionToken,
      expires_at: expiresAt.toISOString(),
      mfa_required: false,
      session_timeout: sessionTimeout
    };

    // Set secure session cookie
    const response = NextResponse.json({
      success: true,
      data: responseData,
      meta: {
        login_time: new Date().toISOString(),
        ip_address: ipAddress,
        user_agent: userAgent,
        session_timeout: sessionTimeout
      }
    } as AdminApiResponse<LoginResponse>);

    // Set session cookie with security flags
    response.cookies.set('session_token', sessionToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict',
      maxAge: remember_me ? 30 * 24 * 60 * 60 : sessionTimeout, // 30 days if remember_me, otherwise session timeout
      path: '/'
    });

    // Set additional security headers
    response.headers.set('X-Content-Type-Options', 'nosniff');
    response.headers.set('X-Frame-Options', 'DENY');
    response.headers.set('X-XSS-Protection', '1; mode=block');
    response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');

    return response;

  } catch (error) {
    console.error('Enhanced login error:', error);
    
    return NextResponse.json({
      success: false,
      error: {
        code: 'INTERNAL_SERVER_ERROR',
        message: 'An internal server error occurred during authentication',
        details: process.env.NODE_ENV === 'development' ? {
          error_message: error instanceof Error ? error.message : 'Unknown error'
        } : undefined
      }
    } as AdminApiResponse<never>, { status: 500 });
  }
}

/**
 * Enhanced logout endpoint
 */
export async function DELETE(request: NextRequest): Promise<NextResponse> {
  try {
    const sessionToken = extractSessionToken(request);
    
    if (!sessionToken) {
      return NextResponse.json({
        success: false,
        error: {
          code: 'NO_SESSION',
          message: 'No active session to logout'
        }
      } as AdminApiResponse<never>, { status: 400 });
    }

    // Validate session to get user ID
    const authContext = await enhancedAuthMiddleware.validateSession(sessionToken);
    
    if (authContext) {
      // Perform enhanced logout
      await enhancedAuthMiddleware.logout(sessionToken, authContext.user.user_id);
    }

    // Clear session cookie
    const response = NextResponse.json({
      success: true,
      data: {
        message: 'Successfully logged out',
        logout_time: new Date().toISOString()
      }
    } as AdminApiResponse<{ message: string; logout_time: string }>);

    response.cookies.delete('session_token');

    return response;

  } catch (error) {
    console.error('Enhanced logout error:', error);
    
    return NextResponse.json({
      success: false,
      error: {
        code: 'LOGOUT_ERROR',
        message: 'An error occurred during logout'
      }
    } as AdminApiResponse<never>, { status: 500 });
  }
}

/**
 * Session validation endpoint
 */
export async function GET(request: NextRequest): Promise<NextResponse> {
  try {
    const sessionToken = extractSessionToken(request);
    
    if (!sessionToken) {
      return NextResponse.json({
        success: false,
        error: {
          code: 'NO_SESSION_TOKEN',
          message: 'Session token required'
        }
      } as AdminApiResponse<never>, { status: 401 });
    }

    const ipAddress = getClientIP(request);
    const authContext = await enhancedAuthMiddleware.validateSession(sessionToken, ipAddress);
    
    if (!authContext) {
      return NextResponse.json({
        success: false,
        error: {
          code: 'INVALID_SESSION',
          message: 'Session is invalid or expired'
        }
      } as AdminApiResponse<never>, { status: 401 });
    }

    return NextResponse.json({
      success: true,
      data: {
        valid: true,
        user: {
          user_id: authContext.user.user_id,
          email: authContext.user.email,
          full_name: authContext.user.full_name,
          role: authContext.user.role,
          two_factor_enabled: authContext.user.two_factor_enabled
        },
        session: {
          expires_at: authContext.sessionStatus.expiresAt.toISOString(),
          time_remaining: authContext.sessionStatus.timeRemaining,
          warning_active: authContext.sessionStatus.warningActive
        },
        security: {
          mfa_required: authContext.mfaRequired,
          mfa_verified: authContext.mfaVerified,
          ip_address: authContext.ipAddress
        }
      }
    } as AdminApiResponse<any>);

  } catch (error) {
    console.error('Session validation error:', error);
    
    return NextResponse.json({
      success: false,
      error: {
        code: 'VALIDATION_ERROR',
        message: 'An error occurred during session validation'
      }
    } as AdminApiResponse<never>, { status: 500 });
  }
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
 * Extract session token from request
 */
function extractSessionToken(request: NextRequest): string | null {
  // Try Authorization header first
  const authHeader = request.headers.get('authorization');
  if (authHeader && authHeader.startsWith('Bearer ')) {
    return authHeader.substring(7);
  }

  // Try cookie
  const cookies = request.headers.get('cookie');
  if (cookies) {
    const sessionMatch = cookies.match(/session_token=([^;]+)/);
    if (sessionMatch) {
      return sessionMatch[1];
    }
  }

  return null;
}

/**
 * Get appropriate HTTP status code for error type
 */
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
      return 403; // Forbidden (but with specific MFA requirement)
    
    case 'AUTHENTICATION_ERROR':
    default:
      return 500; // Internal Server Error
  }
}