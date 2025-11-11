/**
 * Enhanced Authentication Middleware with Security Features
 *
 * Integrates progressive login delays, account lockout, MFA enforcement,
 * session timeout management, and IP security for admin authentication.
 *
 * Requirements: 5.4, 5.5, 5.6
 */
import { NextRequest, NextResponse } from 'next/server';
import { securityManager, SECURITY_CONFIG } from './security-manager';
import { mfaManager } from './mfa-manager';
import { sessionTimeoutManager } from './session-timeout-manager';
import { ipSecurityManager } from './ip-security-manager';
import { getAdminDatabaseUtils } from '@/lib/database/admin-utils';
import type { User, AdminApiResponse } from '@/types/admin';

export interface EnhancedAuthContext {
  user: User;
  sessionToken: string;
  ipAddress: string;
  userAgent: string;
  mfaRequired: boolean;
  mfaVerified: boolean;
  sessionStatus: {
    isValid: boolean;
    expiresAt: Date;
    timeRemaining: number;
    warningActive: boolean;
  };
}

export interface AuthenticationResult {
  success: boolean;
  user?: User;
  sessionToken?: string;
  mfaRequired?: boolean;
  mfaVerified?: boolean;
  delay?: number;
  error?: {
    code: string;
    message: string;
    details?: unknown;
  };
}

export class EnhancedAuthMiddleware {
  private _adminUtils?: ReturnType<typeof getAdminDatabaseUtils>;

  private get adminUtils(): ReturnType<typeof getAdminDatabaseUtils> {
    if (!this._adminUtils) {
      this._adminUtils = getAdminDatabaseUtils();
    }
    return this._adminUtils;
  }

  /**
   * Enhanced login with security features
   */
  async authenticateUser(
    email: string,
    password: string,
    totpCode?: string,
    ipAddress?: string,
    userAgent?: string
  ): Promise<AuthenticationResult> {
    const clientIP = this.normalizeIp(ipAddress || 'unknown');

    try {
      // Step 1: Lookup user and check account lockout
      const user = await this.findUserByEmail(email);

      if (user) {
        const isLocked = await securityManager.isAccountLocked(user.user_id);
        if (isLocked) {
          await securityManager.recordFailedLogin(email, clientIP, userAgent);
          return {
            success: false,
            error: {
              code: 'ACCOUNT_LOCKED',
              message: 'Account is temporarily locked due to excessive failed attempts',
              details: { locked_until: user.locked_until }
            }
          };
        }

        // Step 2: IP access policy (role-aware whitelist + blocks)
        const ipCheck = await ipSecurityManager.checkIpAccess(clientIP, user);
        if (!ipCheck.allowed) {
          await ipSecurityManager.recordFailedAttempt(clientIP, email);
          return {
            success: false,
            error: {
              code: 'IP_ACCESS_DENIED',
              message: ipCheck.reason || 'IP address not allowed',
              details: { ip_address: clientIP }
            }
          };
        }
      }

      // Step 3: Validate credentials (via backend if available)
      const credentialsValid = await this.validateCredentials(email, password);
      if (!credentialsValid) {
        const delay = await securityManager.recordFailedLogin(email, clientIP, userAgent);
        await ipSecurityManager.recordFailedAttempt(clientIP, email);
        if (delay && delay > 0) await this.sleep(delay * 1000);

        return {
          success: false,
          delay,
          error: {
            code: 'INVALID_CREDENTIALS',
            message: 'Invalid email or password',
            details: { delay_seconds: delay }
          }
        };
      }

      // From here, user should exist - verify it's still valid
      if (!user || !user.is_active) {
        const delay = await securityManager.recordFailedLogin(email, clientIP, userAgent);
        await ipSecurityManager.recordFailedAttempt(clientIP, email);
        if (delay && delay > 0) await this.sleep(delay * 1000);

        return {
          success: false,
          delay,
          error: {
            code: 'ACCOUNT_INACTIVE',
            message: 'Account is inactive or does not exist',
            details: { delay_seconds: delay }
          }
        };
      }

      // Step 4: MFA policy gate (role policy + setup enforcement)
      const mfaPolicy = await mfaManager.enforceMfaRequirement(user);
      if (!mfaPolicy.canProceed) {
        return {
          success: false,
          mfaRequired: mfaPolicy.requiresSetup,
          error: {
            code: mfaPolicy.requiresSetup ? 'MFA_SETUP_REQUIRED' : 'MFA_REQUIRED',
            message: mfaPolicy.message || 'Multi-factor authentication required',
            details: { requires_setup: mfaPolicy.requiresSetup }
          }
        };
      }

      // Step 5: Verify MFA if enabled
      if (user.two_factor_enabled) {
        if (!totpCode) {
          return {
            success: false,
            mfaRequired: true,
            error: {
              code: 'MFA_CODE_REQUIRED',
              message: 'TOTP code required for authentication'
            }
          };
        }
        const mfaResult = await mfaManager.verifyMfaCode(user.user_id, totpCode);
        if (!mfaResult.valid) {
          await securityManager.recordFailedLogin(email, clientIP, userAgent);
          return {
            success: false,
            error: {
              code: 'INVALID_MFA_CODE',
              message: 'Invalid TOTP code',
              details: { used_backup_code: mfaResult.usedBackupCode === true }
            }
          };
        }
      }

      // Step 6: Enforce concurrent session limits
      const canCreateSession = await securityManager.checkConcurrentSessionLimit(user.user_id, user.role);
      if (!canCreateSession) {
        return {
          success: false,
          error: {
            code: 'SESSION_LIMIT_EXCEEDED',
            message: 'Maximum concurrent sessions exceeded for your role',
            details: { max_sessions: SECURITY_CONFIG.MAX_CONCURRENT_SESSIONS[user.role] }
          }
        };
      }

      // Step 7: Create secure session
      const sessionToken = this.generateSessionToken();
      await sessionTimeoutManager.createSession(user, sessionToken, clientIP, userAgent);

      // Step 8: Clear failed attempts and record successful IP access
      securityManager.clearFailedAttempts(email, clientIP);
      await ipSecurityManager.recordIpAccess(clientIP, user, userAgent);

      // Step 9: Update user's last login
      await this.adminUtils.updateUser(user.user_id, {
        last_login_at: new Date(),
        failed_login_attempts: 0
      });

      return {
        success: true,
        user,
        sessionToken,
        mfaRequired: false,
        mfaVerified: true
      };
    } catch (error) {
      return {
        success: false,
        error: {
          code: 'AUTHENTICATION_ERROR',
          message: 'Authentication system error',
          details: error instanceof Error ? error.message : 'Unknown error'
        }
      };
    }
  }

  private async findUserByEmail(email: string): Promise<User | null> {
    const normalizedEmail = email.trim().toLowerCase();
    if (!normalizedEmail) {
      return null;
    }

    try {
      if (typeof this.adminUtils.findUserByEmail === 'function') {
        return await this.adminUtils.findUserByEmail(normalizedEmail);
      }

      // Legacy fallback: fetch all users with matching role filters if direct lookup is unavailable
      const users = await this.adminUtils.getUsersWithRoleFilter?.({ search: normalizedEmail }, { page: 1, limit: 1 });
      if (users && Array.isArray(users.data) && users.data.length > 0) {
        return users.data[0];
      }
    } catch (error) {
      console.warn('Failed to locate user by email during authentication:', error);
    }

    return null;
  }

  /**
   * Validate session with security checks
   */
  async validateSession(sessionToken: string, ipAddress?: string): Promise<EnhancedAuthContext | null> {
    try {
      // 1) Check session timeout status
      const status = sessionTimeoutManager.getSessionStatus(sessionToken);
      if (!status || !status.isValid) return null;

      // 2) Touch activity
      const stillValid = await sessionTimeoutManager.updateSessionActivity(sessionToken);
      if (!stillValid) return null;

      // 3) Load the session (prefer direct lookup by token)
      const session =
        sessionTimeoutManager.getSessionByToken?.(sessionToken) ||
        (await sessionTimeoutManager.findSessionByToken?.(sessionToken)); // optional async
      if (!session) return null;

      // 4) Load user
      const user = await this.adminUtils.getUserWithRole(session.user_id);
      if (!user || !user.is_active) return null;

      // 5) Optional IP consistency check
      const normalizedIp = this.normalizeIp(ipAddress || '');
      if (normalizedIp && session.ip_address && normalizedIp !== session.ip_address) {
        await this.adminUtils.createAuditLog({
          user_id: user.user_id,
          action: 'security.ip_mismatch',
          resource_type: 'session_security',
          resource_id: sessionToken,
          details: {
            original_ip: session.ip_address,
            current_ip: normalizedIp,
            session_token: sessionToken
          },
          ip_address: normalizedIp
        });
        // Consider terminating on mismatch if policy requires
        // await sessionTimeoutManager.terminateSession(sessionToken, 'ip_mismatch');
        // return null;
      }

      return {
        user,
        sessionToken,
        ipAddress: normalizedIp || session.ip_address || 'unknown',
        userAgent: session.user_agent || 'unknown',
        mfaRequired: await mfaManager.isMfaRequired(user),
        mfaVerified: !!user.two_factor_enabled, // "enabled" proxy; true verification happened on login
        sessionStatus: {
          isValid: status.isValid,
          expiresAt: status.expiresAt,
          timeRemaining: status.timeRemaining,
          warningActive: status.warningActive
        }
      };
    } catch {
      return null;
    }
  }

  /**
   * Enhanced logout with security cleanup
   */
  async logout(sessionToken: string, userId: string): Promise<void> {
    try {
      await sessionTimeoutManager.terminateSession(sessionToken, 'user_logout');
      await this.adminUtils.createAuditLog({
        user_id: userId,
        action: 'auth.logout',
        resource_type: 'user_session',
        resource_id: sessionToken,
        details: {
          logout_method: 'user_initiated',
          logout_at: new Date().toISOString()
        }
      });
    } catch {
      // best-effort
    }
  }

  /**
   * Middleware wrapper for API routes
   */
  async withEnhancedAuth(
    request: NextRequest,
    handler: (request: NextRequest, context: EnhancedAuthContext) => Promise<NextResponse>,
    options: {
      requiredRole?: 'admin' | 'super_admin';
      requireMfa?: boolean;
      checkIpWhitelist?: boolean;
    } = {}
  ): Promise<NextResponse> {
    try {
      const sessionToken = this.extractSessionToken(request);
      const ipAddress = this.extractClientIP(request);
      const userAgent = request.headers.get('user-agent') || undefined;

      if (!sessionToken) {
        return this.unauthorizedResponse('SESSION_TOKEN_MISSING', 'Session token required');
      }

      const authContext = await this.validateSession(sessionToken, ipAddress);
      if (!authContext) {
        return this.unauthorizedResponse('INVALID_SESSION', 'Invalid or expired session');
      }

      // Role gating
      if (options.requiredRole) {
        if (options.requiredRole === 'super_admin' && authContext.user.role !== 'super_admin') {
          return this.forbiddenResponse('INSUFFICIENT_ROLE', 'Super admin role required');
        }
        if (options.requiredRole === 'admin' && !['admin', 'super_admin'].includes(authContext.user.role)) {
          return this.forbiddenResponse('INSUFFICIENT_ROLE', 'Admin role required');
        }
      }

      // MFA gating
      if (options.requireMfa && authContext.mfaRequired && !authContext.mfaVerified) {
        return this.forbiddenResponse('MFA_REQUIRED', 'Multi-factor authentication required');
      }

      // Optional whitelist check
      if (options.checkIpWhitelist) {
        const ipCheck = await ipSecurityManager.checkIpAccess(authContext.ipAddress, authContext.user);
        if (!ipCheck.allowed) {
          return this.forbiddenResponse('IP_ACCESS_DENIED', ipCheck.reason || 'IP access denied');
        }
      }

      return await handler(request, authContext);
    } catch {
      return this.errorResponse('AUTHENTICATION_ERROR', 'Authentication system error');
    }
  }

  /* --------------------------
   * Helpers
   * ------------------------ */

  private extractSessionToken(request: NextRequest): string | null {
    const authHeader = request.headers.get('authorization');
    if (authHeader && authHeader.startsWith('Bearer ')) {
      return authHeader.substring(7);
    }
    const cookies = request.headers.get('cookie');
    if (cookies) {
      const m = cookies.match(/(?:^|;\s*)session_token=([^;]+)/);
      if (m) return decodeURIComponent(m[1]);
    }
    return null;
  }

  private extractClientIP(request: NextRequest): string {
    const forwarded = request.headers.get('x-forwarded-for');
    const realIP = request.headers.get('x-real-ip');
    const remoteAddr = request.headers.get('remote-addr');

    const ip = (forwarded ? forwarded.split(',')[0].trim() : realIP || remoteAddr || 'unknown');
    return this.normalizeIp(ip);
  }

  private normalizeIp(ip: string): string {
    // Remove brackets/ports and lower-case IPv6 for consistency
    const stripPort = (host: string) => {
      if (host.startsWith('[')) {
        const end = host.indexOf(']');
        return end !== -1 ? host.slice(1, end) : host;
      }
      const idx = host.lastIndexOf(':');
      if (idx > -1 && host.indexOf(':') === idx) {
        const after = host.slice(idx + 1);
        if (/^\d+$/.test(after)) return host.slice(0, idx);
      }
      return host;
    };
    const v = stripPort(ip.trim());
    return v.toLowerCase();
  }

  private async validateCredentials(email: string, password: string): Promise<boolean> {
    try {
      if (this.adminUtils.verifyPassword) {
        return await this.adminUtils.verifyPassword(email, password);
      }
      // If no backend verifier is available, fail-closed in prod; pass-through can be toggled in dev
      return false;
    } catch {
      return false;
    }
  }

  private generateSessionToken(): string {
    // Replace with crypto.randomUUID + HMAC if you want signed tokens
    return `sess_${Date.now()}_${Math.random().toString(36).slice(2, 10)}_${Math.random().toString(36).slice(2, 10)}`;
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(res => setTimeout(res, ms));
  }

  private unauthorizedResponse(code: string, message: string): NextResponse {
    return NextResponse.json(
      { success: false, error: { code, message } } as AdminApiResponse<never>,
      { status: 401 }
    );
  }

  private forbiddenResponse(code: string, message: string): NextResponse {
    return NextResponse.json(
      { success: false, error: { code, message } } as AdminApiResponse<never>,
      { status: 403 }
    );
  }

  private errorResponse(code: string, message: string): NextResponse {
    return NextResponse.json(
      { success: false, error: { code, message } } as AdminApiResponse<never>,
      { status: 500 }
    );
  }
}

// Export singleton instance
export const enhancedAuthMiddleware = new EnhancedAuthMiddleware();
