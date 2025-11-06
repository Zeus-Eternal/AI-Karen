/**
 * Security Manager for Admin Management System
 *
 * Implements progressive login delays, account lockout, MFA enforcement,
 * session timeout management, concurrent session limiting, and security event detection.
 *
 * Requirements: 5.4, 5.5, 5.6
 */

import { getAdminDatabaseUtils } from '@/lib/database/admin-utils';
import type { User, SecurityEvent, AdminSession } from '@/types/admin';

// -------- Security configuration constants --------
export const SECURITY_CONFIG = {
  // Progressive login delays (in seconds)
  LOGIN_DELAYS: [0, 1, 2, 5, 10, 30, 60, 300],
  // Account lockout settings
  MAX_FAILED_ATTEMPTS: 5,
  LOCKOUT_DURATION: 30 * 60 * 1000, // 30 minutes (ms)
  // Session timeout settings (in seconds)
  ADMIN_SESSION_TIMEOUT: 30 * 60,
  SUPER_ADMIN_SESSION_TIMEOUT: 30 * 60,
  USER_SESSION_TIMEOUT: 60 * 60,
  // Concurrent session limits
  MAX_CONCURRENT_SESSIONS: {
    super_admin: 1,
    admin: 2,
    user: 3,
  } as const,
  // Security event thresholds
  SUSPICIOUS_ACTIVITY_THRESHOLD: 10, // Failed attempts from same IP
  PRIVILEGE_ESCALATION_MONITORING: true,
  // IP whitelisting for super admins (optional)
  SUPER_ADMIN_IP_WHITELIST_ENABLED: false,
  SUPER_ADMIN_ALLOWED_IPS: [] as string[],

  // Soft policies
  TERMINATE_OLDEST_SESSION_WHEN_LIMIT_REACHED: true, // if false -> reject new session
} as const;

// -------- In-memory stores for security tracking (use Redis in production) --------
export type AttemptRec = { count: number; lastAttempt: number; delays: number[] };
const loginAttempts = new Map<string, AttemptRec>();
const activeSessions = new Map<string, AdminSession[]>();
const securityEvents = new Map<string, SecurityEvent[]>();

// -------- Utils --------
const isoNow = () => new Date().toISOString();

function secureRandomId(prefix: string): string {
  try {
    // Prefer Web Crypto if present
    // @ts-ignore
    if (globalThis.crypto?.getRandomValues) {
      // @ts-ignore
      const arr = new Uint32Array(3);
      // @ts-ignore
      globalThis.crypto.getRandomValues(arr);
      return `${prefix}_${Date.now().toString(36)}_${Array.from(arr)
        .map((n) => n.toString(36))
        .join('')}`;
    }
  } catch {
    // fallthrough
  }
  // Fallback
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 12)}`;
}

export class SecurityManager {
  private adminUtils = getAdminDatabaseUtils();

  /**
   * Check if user account is currently locked
   */
  async isAccountLocked(userId: string): Promise<boolean> {
    try {
      const user = await this.adminUtils.getUserWithRole(userId);
      if (!user || !user.locked_until) return false;

      const now = new Date();
      const lockedUntil = new Date(user.locked_until);
      if (now < lockedUntil) return true;

      // Unlock if expired
      await this.unlockAccount(userId);
      return false;
    } catch {
      // Fail-soft: don't block logins if DB transient error
      return false;
    }
  }

  /**
   * Record failed login attempt and implement progressive delays
   * Returns: delay in seconds before next attempt should be allowed
   */
  async recordFailedLogin(
    identifier: string,
    ipAddress?: string,
    userAgent?: string
  ): Promise<number> {
    const key = `${identifier}:${ipAddress || 'unknown'}`;
    const now = Date.now();

    const attempts: AttemptRec =
      loginAttempts.get(key) || { count: 0, lastAttempt: 0, delays: [] };

    // Reset window after 1 hour
    if (now - attempts.lastAttempt > 60 * 60 * 1000) {
      attempts.count = 0;
      attempts.delays = [];
    }

    attempts.count += 1;
    attempts.lastAttempt = now;

    const delayIndex = Math.min(
      attempts.count - 1,
      SECURITY_CONFIG.LOGIN_DELAYS.length - 1
    );
    const delay = SECURITY_CONFIG.LOGIN_DELAYS[delayIndex];
    attempts.delays.push(delay);
    loginAttempts.set(key, attempts);

    // If attempts exceed threshold, try to lock the account (if we can resolve a user)
    if (attempts.count >= SECURITY_CONFIG.MAX_FAILED_ATTEMPTS) {
      try {
        const user = await this.findUserByIdentifier(identifier);
        if (user) {
          await this.lockAccount(user.user_id, SECURITY_CONFIG.LOCKOUT_DURATION);
          await this.logSecurityEvent({
            event_type: 'account_locked',
            user_id: user.user_id,
            ip_address: ipAddress,
            user_agent: userAgent,
            details: {
              failed_attempts: attempts.count,
              lockout_duration_ms: SECURITY_CONFIG.LOCKOUT_DURATION,
              identifier,
            },
            severity: 'high',
          });
        }
      } catch {
        // ignore
      }
    }

    // Suspicious activity on IP
    if (ipAddress && attempts.count >= SECURITY_CONFIG.SUSPICIOUS_ACTIVITY_THRESHOLD) {
      await this.logSecurityEvent({
        event_type: 'suspicious_activity',
        ip_address: ipAddress,
        user_agent: userAgent,
        details: {
          failed_attempts: attempts.count,
          identifier,
          threshold_exceeded: true,
        },
        severity: 'medium',
      });
    }

    return delay;
  }

  /**
   * Clear failed login attempts after successful login
   */
  clearFailedAttempts(identifier: string, ipAddress?: string): void {
    const key = `${identifier}:${ipAddress || 'unknown'}`;
    loginAttempts.delete(key);
  }

  /**
   * Lock user account for specified duration
   */
  async lockAccount(userId: string, durationMs: number): Promise<void> {
    const lockedUntil = new Date(Date.now() + durationMs);

    const user = await this.adminUtils.getUserWithRole(userId);
    const failedAttempts = user?.failed_login_attempts ?? 0;

    await this.adminUtils.updateUser(userId, {
      locked_until: lockedUntil,
      failed_login_attempts: failedAttempts,
    });

    await this.adminUtils.createAuditLog({
      user_id: userId,
      action: 'account.locked',
      resource_type: 'user_account',
      resource_id: userId,
      details: {
        locked_until: lockedUntil.toISOString(),
        duration_ms: durationMs,
        reason: 'excessive_failed_attempts',
      },
      created_at: new Date(),
    });
  }

  /**
   * Unlock user account
   */
  async unlockAccount(userId: string): Promise<void> {
    await this.adminUtils.updateUser(userId, {
      locked_until: null,
      failed_login_attempts: 0,
    });

    await this.adminUtils.createAuditLog({
      user_id: userId,
      action: 'account.unlocked',
      resource_type: 'user_account',
      resource_id: userId,
      details: {
        unlocked_at: isoNow(),
        reason: 'lock_period_expired',
      },
      created_at: new Date(),
    });
  }

  /**
   * Check if MFA is required for user
   */
  async isMfaRequired(user: User): Promise<boolean> {
    if (user.role === 'super_admin' || user.role === 'admin') {
      const mfaConfigValue = await this.getSystemConfigValue('mfa_required_for_admins');
      return mfaConfigValue === 'true' || mfaConfigValue === true;
    }
    return false;
  }

  /**
   * Helper: get a single system config value by key
   */
  private async getSystemConfigValue(
    key: string
  ): Promise<string | number | boolean | null> {
    try {
      const configs = await this.adminUtils.getSystemConfig();
      const config = configs.find((c: any) => c.key === key);
      return config?.value ?? null;
    } catch {
      return null;
    }
  }

  /**
   * Enforce MFA requirement for admin accounts
   */
  async enforceMfaRequirement(
    user: User
  ): Promise<{ required: boolean; enabled: boolean; blocked: boolean }> {
    const required = await this.isMfaRequired(user);
    const enabled = !!user.two_factor_enabled;

    if (required && !enabled) {
      await this.logSecurityEvent({
        event_type: 'privilege_escalation',
        user_id: user.user_id,
        details: {
          mfa_required: true,
          mfa_enabled: false,
          user_role: user.role,
          enforcement_action: 'login_blocked',
        },
        severity: 'medium',
      });
      return { required, enabled, blocked: true };
    }

    return { required, enabled, blocked: false };
  }

  /**
   * Get session timeout for role (seconds)
   */
  getSessionTimeout(role: 'super_admin' | 'admin' | 'user'): number {
    switch (role) {
      case 'super_admin':
        return SECURITY_CONFIG.SUPER_ADMIN_SESSION_TIMEOUT;
      case 'admin':
        return SECURITY_CONFIG.ADMIN_SESSION_TIMEOUT;
      default:
        return SECURITY_CONFIG.USER_SESSION_TIMEOUT;
    }
  }

  /**
   * Check if user has capacity for a new session (after pruning expired)
   * Returns true if under limit, false if at/over limit.
   */
  async checkConcurrentSessionLimit(
    userId: string,
    role: 'super_admin' | 'admin' | 'user'
  ): Promise<boolean> {
    const now = new Date();
    const sessions = activeSessions.get(userId) || [];
    const valid = sessions.filter((s) => s.is_active && new Date(s.expires_at) > now);
    activeSessions.set(userId, valid);

    return valid.length < SECURITY_CONFIG.MAX_CONCURRENT_SESSIONS[role];
  }

  /**
   * Create new admin session with role-based timeout
   */
  async createAdminSession(
    user: User,
    ipAddress?: string,
    userAgent?: string
  ): Promise<AdminSession> {
    const sessionTimeout = this.getSessionTimeout(user.role);
    const now = new Date();
    const expiresAt = new Date(now.getTime() + sessionTimeout * 1000);

    // Enforce concurrent session limits
    let sessions = activeSessions.get(user.user_id) || [];
    // prune expired
    sessions = sessions.filter((s) => s.is_active && new Date(s.expires_at) > now);

    const max = SECURITY_CONFIG.MAX_CONCURRENT_SESSIONS[user.role];
    if (sessions.length >= max) {
      if (SECURITY_CONFIG.TERMINATE_OLDEST_SESSION_WHEN_LIMIT_REACHED) {
        // find oldest by created_at
        sessions.sort((a, b) => a.created_at.getTime() - b.created_at.getTime());
        const oldest = sessions[0];
        oldest.is_active = false;

        await this.adminUtils.createAuditLog({
          user_id: user.user_id,
          action: 'session.terminated',
          resource_type: 'admin_session',
          resource_id: oldest.session_token,
          details: {
            session_duration_ms: Date.now() - oldest.created_at.getTime(),
            termination_reason: 'limit_enforced',
          },
          ip_address: ipAddress,
          user_agent: userAgent,
          created_at: new Date(),
        });

        // Remove from list
        sessions = sessions.slice(1);
      } else {
        await this.logSecurityEvent({
          event_type: 'concurrent_session_limit',
          user_id: user.user_id,
          ip_address: ipAddress,
          user_agent: userAgent,
          details: {
            attempted_new_session: true,
            current_sessions: sessions.length,
            max_sessions: max,
          },
          severity: user.role === 'super_admin' ? 'high' : 'medium',
        });
        throw new Error('Concurrent session limit reached');
      }
    }

    const session: AdminSession = {
      session_token: this.generateSessionToken(),
      user_id: user.user_id,
      user_email: user.email,
      user_role: user.role,
      ip_address: ipAddress,
      user_agent: userAgent,
      created_at: now,
      last_accessed: now,
      expires_at: expiresAt,
      is_active: true,
    };

    sessions.push(session);
    activeSessions.set(user.user_id, sessions);

    await this.adminUtils.createAuditLog({
      user_id: user.user_id,
      action: 'session.created',
      resource_type: 'admin_session',
      resource_id: session.session_token,
      details: {
        session_timeout_s: sessionTimeout,
        expires_at: expiresAt.toISOString(),
        user_role: user.role,
        concurrent_sessions: sessions.length,
      },
      ip_address: ipAddress,
      user_agent: userAgent,
      created_at: new Date(),
    });

    return session;
  }

  /**
   * Terminate admin session
   */
  async terminateSession(sessionToken: string, userId: string): Promise<void> {
    const sessions = activeSessions.get(userId) || [];
    const idx = sessions.findIndex((s) => s.session_token === sessionToken);
    if (idx === -1) return;

    const session = sessions[idx];
    session.is_active = false;

    await this.adminUtils.createAuditLog({
      user_id: userId,
      action: 'session.terminated',
      resource_type: 'admin_session',
      resource_id: sessionToken,
      details: {
        session_duration_ms: Date.now() - session.created_at.getTime(),
        termination_reason: 'manual',
      },
      created_at: new Date(),
    });

    sessions.splice(idx, 1);
    activeSessions.set(userId, sessions);
  }

  /**
   * Check IP whitelist for super admin access
   */
  async checkSuperAdminIpWhitelist(ipAddress: string): Promise<boolean> {
    if (!SECURITY_CONFIG.SUPER_ADMIN_IP_WHITELIST_ENABLED) return true;
    if (!ipAddress || SECURITY_CONFIG.SUPER_ADMIN_ALLOWED_IPS.length === 0) return false;
    return SECURITY_CONFIG.SUPER_ADMIN_ALLOWED_IPS.includes(ipAddress);
  }

  /**
   * Log security event (and audit)
   */
  async logSecurityEvent(
    event: Omit<SecurityEvent, 'id' | 'resolved' | 'created_at'>
  ): Promise<void> {
    const securityEvent: SecurityEvent = {
      id: this.generateEventId(),
      ...event,
      resolved: false,
      created_at: new Date(),
    };

    const key = event.user_id || 'system';
    const list = securityEvents.get(key) || [];
    list.push(securityEvent);
    securityEvents.set(key, list);

    await this.adminUtils.createAuditLog({
      user_id: event.user_id || 'system',
      action: 'security.event',
      resource_type: 'security_event',
      resource_id: securityEvent.id,
      details: {
        event_type: event.event_type,
        severity: event.severity,
        details: event.details,
      },
      ip_address: event.ip_address,
      user_agent: event.user_agent,
      created_at: new Date(),
    });

    if (event.severity === 'high' || event.severity === 'critical') {
      await this.notifySecurityTeam(securityEvent);
    }
  }

  /**
   * Get security events for user or system
   */
  getSecurityEvents(userId?: string): SecurityEvent[] {
    return securityEvents.get(userId || 'system') || [];
  }

  /**
   * Resolve security event
   */
  async resolveSecurityEvent(eventId: string, resolvedBy: string): Promise<void> {
    for (const [key, events] of securityEvents.entries()) {
      const event = events.find((e) => e.id === eventId);
      if (event) {
        event.resolved = true;
        (event as any).resolved_by = resolvedBy;
        (event as any).resolved_at = new Date();

        await this.adminUtils.createAuditLog({
          user_id: resolvedBy,
          action: 'security.event.resolved',
          resource_type: 'security_event',
          resource_id: eventId,
          details: {
            event_type: event.event_type,
            original_severity: event.severity,
            resolution_time_ms: Date.now() - event.created_at.getTime(),
          },
          created_at: new Date(),
        });
        break;
      }
    }
  }

  /**
   * Clean up expired sessions and old security events
   */
  async cleanupSecurityData(): Promise<void> {
    const now = new Date();

    // Sessions
    for (const [userId, sessions] of activeSessions.entries()) {
      const valid = sessions.filter((s) => s.is_active && new Date(s.expires_at) > now);
      if (valid.length !== sessions.length) {
        activeSessions.set(userId, valid);
        await this.adminUtils.createAuditLog({
          user_id: 'system',
          action: 'security.cleanup.sessions',
          resource_type: 'admin_session',
          details: {
            user_id: userId,
            expired_sessions: sessions.length - valid.length,
            remaining_sessions: valid.length,
          },
          created_at: new Date(),
        });
      }
    }

    // Events: keep last 30 days
    const cutoff = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
    for (const [key, events] of securityEvents.entries()) {
      const recent = events.filter((e) => e.created_at > cutoff);
      if (recent.length !== events.length) {
        securityEvents.set(key, recent);
      }
    }
  }

  /**
   * Generate secure session token
   */
  private generateSessionToken(): string {
    return secureRandomId('admin');
  }

  /**
   * Generate security event ID
   */
  private generateEventId(): string {
    return secureRandomId('sec');
  }

  /**
   * Find user by email or user_id
   */
  private async findUserByIdentifier(identifier: string): Promise<User | null> {
    try {
      // UUID-ish quick gate (adapt if your IDs differ)
      if (identifier.length >= 32) {
        const maybe = await this.adminUtils.getUserWithRole(identifier);
        if (maybe) return maybe;
      }
      return await this.adminUtils.getUserByEmail(identifier);
    } catch {
      return null;
    }
  }

  /**
   * Notify security team of critical/high events (stub)
   */
  private async notifySecurityTeam(_event: SecurityEvent): Promise<void> {
    // Wire to email/Slack/PagerDuty here. Intentionally silent in OSS build.
  }
}

// Export singleton instance
export const securityManager = new SecurityManager();
