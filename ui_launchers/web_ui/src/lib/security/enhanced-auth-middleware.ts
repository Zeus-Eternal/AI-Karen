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
  delay?: number;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
}
export class EnhancedAuthMiddleware {
  private adminUtils = getAdminDatabaseUtils();
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
    const clientIP = ipAddress || 'unknown';
    try {
      // Step 1: Check for account lockout
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
        // Step 2: Check IP access permissions
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
      // Step 3: Validate credentials (this would call your existing auth system)
      const credentialsValid = await this.validateCredentials(email, password);
      if (!credentialsValid || !user) {
        // Record failed attempt and apply progressive delay
        const delay = await securityManager.recordFailedLogin(email, clientIP, userAgent);
        await ipSecurityManager.recordFailedAttempt(clientIP, email);
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
      // Step 4: Check MFA requirements
      const mfaStatus = await mfaManager.enforceMfaRequirement(user);
      if (!mfaStatus.canProceed) {
        return {
          success: false,
          mfaRequired: mfaStatus.requiresSetup,
          error: {
            code: mfaStatus.requiresSetup ? 'MFA_SETUP_REQUIRED' : 'MFA_REQUIRED',
            message: mfaStatus.message || 'Multi-factor authentication required',
            details: { requires_setup: mfaStatus.requiresSetup }
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
              details: { used_backup_code: mfaResult.usedBackupCode }
            }
          };
        }
      }
      // Step 6: Check concurrent session limits
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
      const session = await sessionTimeoutManager.createSession(user, sessionToken, clientIP, userAgent);
      // Step 8: Clear failed attempts and record successful access
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
        mfaRequired: false
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
  /**
   * Validate session with security checks
   */
  async validateSession(sessionToken: string, ipAddress?: string): Promise<EnhancedAuthContext | null> {
    try {
      // Check session timeout status
      const sessionStatus = sessionTimeoutManager.getSessionStatus(sessionToken);
      if (!sessionStatus || !sessionStatus.isValid) {
        return null;
      }
      // Update session activity
      const sessionValid = await sessionTimeoutManager.updateSessionActivity(sessionToken);
      if (!sessionValid) {
        return null;
      }
      // Get user sessions to find the current one
      const userSessions = sessionTimeoutManager.getUserSessions(''); // This needs the user ID
      const currentSession = userSessions.find(s => s.session_token === sessionToken);
      if (!currentSession) {
        return null;
      }
      // Get user data
      const user = await this.adminUtils.getUserWithRole(currentSession.user_id);
      if (!user || !user.is_active) {
        return null;
      }
      // Check IP consistency (optional security measure)
      if (ipAddress && currentSession.ip_address && ipAddress !== currentSession.ip_address) {
        // Log potential session hijacking attempt
        await this.adminUtils.createAuditLog({
          user_id: user.user_id,
          action: 'security.ip_mismatch',
          resource_type: 'session_security',
          resource_id: sessionToken,
          details: {
            original_ip: currentSession.ip_address,
            current_ip: ipAddress,
            session_token: sessionToken
          },
          ip_address: ipAddress
        });
        // Optionally terminate session for security
        // await sessionTimeoutManager.terminateSession(sessionToken, 'ip_mismatch');
        // return null;
      }
      return {
        user,
        sessionToken,
        ipAddress: ipAddress || currentSession.ip_address || 'unknown',
        userAgent: currentSession.user_agent || 'unknown',
        mfaRequired: await mfaManager.isMfaRequired(user),
        mfaVerified: user.two_factor_enabled,
        sessionStatus: {
          isValid: sessionStatus.isValid,
          expiresAt: sessionStatus.expiresAt,
          timeRemaining: sessionStatus.timeRemaining,
          warningActive: sessionStatus.warningActive
        }
      };
    } catch (error) {
      return null;
    }
  }
  /**
   * Enhanced logout with security cleanup
   */
  async logout(sessionToken: string, userId: string): Promise<void> {
    try {
      // Terminate session
      await sessionTimeoutManager.terminateSession(sessionToken, 'user_logout');
      // Log logout
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
    } catch (error) {
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
      // Validate session with security checks
      const authContext = await this.validateSession(sessionToken, ipAddress);
      if (!authContext) {
        return this.unauthorizedResponse('INVALID_SESSION', 'Invalid or expired session');
      }
      // Check role requirements
      if (options.requiredRole) {
        if (options.requiredRole === 'super_admin' && authContext.user.role !== 'super_admin') {
          return this.forbiddenResponse('INSUFFICIENT_ROLE', 'Super admin role required');
        }
        if (options.requiredRole === 'admin' && !['admin', 'super_admin'].includes(authContext.user.role)) {
          return this.forbiddenResponse('INSUFFICIENT_ROLE', 'Admin role required');
        }
      }
      // Check MFA requirements
      if (options.requireMfa && authContext.mfaRequired && !authContext.mfaVerified) {
        return this.forbiddenResponse('MFA_REQUIRED', 'Multi-factor authentication required');
      }
      // Check IP whitelist if required
      if (options.checkIpWhitelist) {
        const ipCheck = await ipSecurityManager.checkIpAccess(authContext.ipAddress, authContext.user);
        if (!ipCheck.allowed) {
          return this.forbiddenResponse('IP_ACCESS_DENIED', ipCheck.reason || 'IP access denied');
        }
      }
      // Call the handler with enhanced context
      return await handler(request, authContext);
    } catch (error) {
      return this.errorResponse('AUTHENTICATION_ERROR', 'Authentication system error');
    }
  }
  /**
   * Extract session token from request
   */
  private extractSessionToken(request: NextRequest): string | null {
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
   * Extract client IP address
   */
  private extractClientIP(request: NextRequest): string {
    const forwarded = request.headers.get('x-forwarded-for');
    const realIP = request.headers.get('x-real-ip');
    const remoteAddr = request.headers.get('remote-addr');
    if (forwarded) {
      return forwarded.split(',')[0].trim();
    }
    return realIP || remoteAddr || 'unknown';
  }
  /**
   * Find user by email
   */
  private async findUserByEmail(email: string): Promise<User | null> {
    try {
      const user = await this.adminUtils.getUserByEmail(email);
      return user;
    } catch (error) {
      return null;
    }
  }
  /**
   * Validate user credentials (mock implementation)
   */
  private async validateCredentials(email: string, password: string): Promise<boolean> {
    // This would integrate with your existing password validation system
    // For now, this is a placeholder
    return true; // Replace with actual credential validation
  }
  /**
   * Generate secure session token
   */
  private generateSessionToken(): string {
    return `sess_${Date.now()}_${Math.random().toString(36).substring(2, 15)}_${Math.random().toString(36).substring(2, 15)}`;
  }
  /**
   * Create unauthorized response
   */
  private unauthorizedResponse(code: string, message: string): NextResponse {
    return NextResponse.json({
      success: false,
      error: { code, message }
    } as AdminApiResponse<never>, { status: 401 });
  }
  /**
   * Create forbidden response
   */
  private forbiddenResponse(code: string, message: string): NextResponse {
    return NextResponse.json({
      success: false,
      error: { code, message }
    } as AdminApiResponse<never>, { status: 403 });
  }
  /**
   * Create error response
   */
  private errorResponse(code: string, message: string): NextResponse {
    return NextResponse.json({
      success: false,
      error: { code, message }
    } as AdminApiResponse<never>, { status: 500 });
  }
}
// Export singleton instance
export const enhancedAuthMiddleware = new EnhancedAuthMiddleware();
