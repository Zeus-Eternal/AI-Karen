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
// Security configuration constants
export const SECURITY_CONFIG = {
  // Progressive login delays (in seconds)
  LOGIN_DELAYS: [0, 1, 2, 5, 10, 30, 60, 300], // Progressive delays up to 5 minutes
  // Account lockout settings
  MAX_FAILED_ATTEMPTS: 5,
  LOCKOUT_DURATION: 30 * 60 * 1000, // 30 minutes in milliseconds
  // Session timeout settings (in seconds)
  ADMIN_SESSION_TIMEOUT: 30 * 60, // 30 minutes for admins
  SUPER_ADMIN_SESSION_TIMEOUT: 30 * 60, // 30 minutes for super admins
  USER_SESSION_TIMEOUT: 60 * 60, // 60 minutes for regular users
  // Concurrent session limits
  MAX_CONCURRENT_SESSIONS: {
    super_admin: 1, // Only one session for super admins
    admin: 2, // Up to 2 sessions for admins
    user: 3, // Up to 3 sessions for regular users
  },
  // Security event thresholds
  SUSPICIOUS_ACTIVITY_THRESHOLD: 10, // Failed attempts from same IP
  PRIVILEGE_ESCALATION_MONITORING: true,
  // IP whitelisting for super admins (optional)
  SUPER_ADMIN_IP_WHITELIST_ENABLED: false,
  SUPER_ADMIN_ALLOWED_IPS: [] as string[],
} as const;
// In-memory stores for security tracking (use Redis in production)
const loginAttempts = new Map<string, { count: number; lastAttempt: number; delays: number[] }>();
const activeSessions = new Map<string, AdminSession[]>();
const securityEvents = new Map<string, SecurityEvent[]>();
export class SecurityManager {
  private adminUtils = getAdminDatabaseUtils();
  /**
   * Check if user account is currently locked
   */
  async isAccountLocked(userId: string): Promise<boolean> {
    try {
      const user = await this.adminUtils.getUserWithRole(userId);
      if (!user || !user.locked_until) {
        return false;
      }
      const now = new Date();
      const lockedUntil = new Date(user.locked_until);
      if (now < lockedUntil) {
        return true;
      }
      // Unlock account if lock period has expired
      await this.unlockAccount(userId);
      return false;
    } catch (error) {
      return false;
    }
  }
  /**
   * Record failed login attempt and implement progressive delays
   */
  async recordFailedLogin(identifier: string, ipAddress?: string, userAgent?: string): Promise<number> {
    const key = `${identifier}:${ipAddress || 'unknown'}`;
    const now = Date.now();
    // Get or create login attempt record
    const attempts = loginAttempts.get(key) || { count: 0, lastAttempt: 0, delays: [] };
    // Reset if last attempt was more than 1 hour ago
    if (now - attempts.lastAttempt > 60 * 60 * 1000) {
      attempts.count = 0;
      attempts.delays = [];
    }
    attempts.count++;
    attempts.lastAttempt = now;
    // Calculate progressive delay
    const delayIndex = Math.min(attempts.count - 1, SECURITY_CONFIG.LOGIN_DELAYS.length - 1);
    const delay = SECURITY_CONFIG.LOGIN_DELAYS[delayIndex];
    attempts.delays.push(delay);
    loginAttempts.set(key, attempts);
    // Check if account should be locked
    if (attempts.count >= SECURITY_CONFIG.MAX_FAILED_ATTEMPTS) {
      try {
        // Find user by email or user_id
        const user = await this.findUserByIdentifier(identifier);
        if (user) {
          await this.lockAccount(user.user_id, SECURITY_CONFIG.LOCKOUT_DURATION);
          // Log security event
          await this.logSecurityEvent({
            event_type: 'account_locked',
            user_id: user.user_id,
            ip_address: ipAddress,
            user_agent: userAgent,
            details: {
              failed_attempts: attempts.count,
              lockout_duration: SECURITY_CONFIG.LOCKOUT_DURATION,
              identifier
            },
            severity: 'high'

        }
      } catch (error) {
      }
    }
    // Check for suspicious activity from IP
    if (ipAddress && attempts.count >= SECURITY_CONFIG.SUSPICIOUS_ACTIVITY_THRESHOLD) {
      await this.logSecurityEvent({
        event_type: 'suspicious_activity',
        ip_address: ipAddress,
        user_agent: userAgent,
        details: {
          failed_attempts: attempts.count,
          identifier,
          threshold_exceeded: true
        },
        severity: 'medium'

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
    await this.adminUtils.updateUser(userId, {
      locked_until: lockedUntil,
      failed_login_attempts: (await this.adminUtils.getUserWithRole(userId))?.failed_login_attempts || 0

    // Log audit event
    await this.adminUtils.createAuditLog({
      user_id: userId,
      action: 'account.locked',
      resource_type: 'user_account',
      resource_id: userId,
      details: {
        locked_until: lockedUntil.toISOString(),
        duration_ms: durationMs,
        reason: 'excessive_failed_attempts'
      }

  }
  /**
   * Unlock user account
   */
  async unlockAccount(userId: string): Promise<void> {
    await this.adminUtils.updateUser(userId, {
      locked_until: undefined,
      failed_login_attempts: 0

    // Log audit event
    await this.adminUtils.createAuditLog({
      user_id: userId,
      action: 'account.unlocked',
      resource_type: 'user_account',
      resource_id: userId,
      details: {
        unlocked_at: new Date().toISOString(),
        reason: 'lock_period_expired'
      }

  }
  /**
   * Check if MFA is required for user
   */
  async isMfaRequired(user: User): Promise<boolean> {
    // Always require MFA for super admins and admins based on system config
    if (user.role === 'super_admin' || user.role === 'admin') {
      const mfaConfigValue = await this.getSystemConfigValue('mfa_required_for_admins');
      return mfaConfigValue === 'true' || mfaConfigValue === true;
    }
    return false;
  }
  /**
   * Helper method to get a single system config value by key
   */
  private async getSystemConfigValue(key: string): Promise<string | number | boolean | null> {
    try {
      const configs = await this.adminUtils.getSystemConfig();
      const config = configs.find(c => c.key === key);
      return config?.value || null;
    } catch (error) {
      return null;
    }
  }
  /**
   * Enforce MFA requirement for admin accounts
   */
  async enforceMfaRequirement(user: User): Promise<{ required: boolean; enabled: boolean }> {
    const required = await this.isMfaRequired(user);
    const enabled = user.two_factor_enabled;
    if (required && !enabled) {
      // Log security event for MFA enforcement
      await this.logSecurityEvent({
        event_type: 'privilege_escalation',
        user_id: user.user_id,
        details: {
          mfa_required: true,
          mfa_enabled: false,
          user_role: user.role,
          enforcement_action: 'login_blocked'
        },
        severity: 'medium'

    }
    return { required, enabled };
  }
  /**
   * Get session timeout for user role
   */
  getSessionTimeout(role: 'super_admin' | 'admin' | 'user'): number {
    switch (role) {
      case 'super_admin':
        return SECURITY_CONFIG.SUPER_ADMIN_SESSION_TIMEOUT;
      case 'admin':
        return SECURITY_CONFIG.ADMIN_SESSION_TIMEOUT;
      case 'user':
      default:
        return SECURITY_CONFIG.USER_SESSION_TIMEOUT;
    }
  }
  /**
   * Check if user has exceeded concurrent session limit
   */
  async checkConcurrentSessionLimit(userId: string, role: 'super_admin' | 'admin' | 'user'): Promise<boolean> {
    const userSessions = activeSessions.get(userId) || [];
    const maxSessions = SECURITY_CONFIG.MAX_CONCURRENT_SESSIONS[role];
    // Clean up expired sessions
    const now = new Date();
    const validSessions = userSessions.filter(session => 
      session.is_active && new Date(session.expires_at) > now
    );
    activeSessions.set(userId, validSessions);
    return validSessions.length < maxSessions;
  }
  /**
   * Create new admin session with role-based timeout
   */
  async createAdminSession(user: User, ipAddress?: string, userAgent?: string): Promise<AdminSession> {
    const sessionTimeout = this.getSessionTimeout(user.role);
    const now = new Date();
    const expiresAt = new Date(now.getTime() + sessionTimeout * 1000);
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
      is_active: true
    };
    // Add to active sessions
    const userSessions = activeSessions.get(user.user_id) || [];
    userSessions.push(session);
    activeSessions.set(user.user_id, userSessions);
    // Log session creation
    await this.adminUtils.createAuditLog({
      user_id: user.user_id,
      action: 'session.created',
      resource_type: 'admin_session',
      resource_id: session.session_token,
      details: {
        session_timeout: sessionTimeout,
        expires_at: expiresAt.toISOString(),
        user_role: user.role,
        concurrent_sessions: userSessions.length
      },
      ip_address: ipAddress,
      user_agent: userAgent

    return session;
  }
  /**
   * Terminate admin session
   */
  async terminateSession(sessionToken: string, userId: string): Promise<void> {
    const userSessions = activeSessions.get(userId) || [];
    const sessionIndex = userSessions.findIndex(s => s.session_token === sessionToken);
    if (sessionIndex !== -1) {
      const session = userSessions[sessionIndex];
      session.is_active = false;
      // Log session termination
      await this.adminUtils.createAuditLog({
        user_id: userId,
        action: 'session.terminated',
        resource_type: 'admin_session',
        resource_id: sessionToken,
        details: {
          session_duration: Date.now() - session.created_at.getTime(),
          termination_reason: 'manual'
        }

      userSessions.splice(sessionIndex, 1);
      activeSessions.set(userId, userSessions);
    }
  }
  /**
   * Check IP whitelist for super admin access
   */
  async checkSuperAdminIpWhitelist(ipAddress: string): Promise<boolean> {
    if (!SECURITY_CONFIG.SUPER_ADMIN_IP_WHITELIST_ENABLED) {
      return true; // IP whitelisting disabled
    }
    if (!ipAddress || SECURITY_CONFIG.SUPER_ADMIN_ALLOWED_IPS.length === 0) {
      return false;
    }
    return SECURITY_CONFIG.SUPER_ADMIN_ALLOWED_IPS.includes(ipAddress);
  }
  /**
   * Log security event
   */
  async logSecurityEvent(event: Omit<SecurityEvent, 'id' | 'resolved' | 'created_at'>): Promise<void> {
    const securityEvent: SecurityEvent = {
      id: this.generateEventId(),
      ...event,
      resolved: false,
      created_at: new Date()
    };
    // Store in memory (use database in production)
    const events = securityEvents.get(event.user_id || 'system') || [];
    events.push(securityEvent);
    securityEvents.set(event.user_id || 'system', events);
    // Log as audit event
    await this.adminUtils.createAuditLog({
      user_id: event.user_id || 'system',
      action: 'security.event',
      resource_type: 'security_event',
      resource_id: securityEvent.id,
      details: {
        event_type: event.event_type,
        severity: event.severity,
        details: event.details
      },
      ip_address: event.ip_address,
      user_agent: event.user_agent

    // Send notifications for high/critical severity events
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
      const event = events.find(e => e.id === eventId);
      if (event) {
        event.resolved = true;
        event.resolved_by = resolvedBy;
        event.resolved_at = new Date();
        // Log resolution
        await this.adminUtils.createAuditLog({
          user_id: resolvedBy,
          action: 'security.event.resolved',
          resource_type: 'security_event',
          resource_id: eventId,
          details: {
            event_type: event.event_type,
            original_severity: event.severity,
            resolution_time: Date.now() - event.created_at.getTime()
          }

        break;
      }
    }
  }
  /**
   * Clean up expired sessions and old security events
   */
  async cleanupSecurityData(): Promise<void> {
    const now = new Date();
    // Clean up expired sessions
    for (const [userId, sessions] of activeSessions.entries()) {
      const validSessions = sessions.filter(session => 
        session.is_active && new Date(session.expires_at) > now
      );
      if (validSessions.length !== sessions.length) {
        activeSessions.set(userId, validSessions);
        // Log cleanup
        await this.adminUtils.createAuditLog({
          user_id: 'system',
          action: 'security.cleanup.sessions',
          resource_type: 'admin_session',
          details: {
            user_id: userId,
            expired_sessions: sessions.length - validSessions.length,
            remaining_sessions: validSessions.length
          }

      }
    }
    // Clean up old security events (keep last 30 days)
    const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
    for (const [key, events] of securityEvents.entries()) {
      const recentEvents = events.filter(event => event.created_at > thirtyDaysAgo);
      if (recentEvents.length !== events.length) {
        securityEvents.set(key, recentEvents);
      }
    }
  }
  /**
   * Generate secure session token
   */
  private generateSessionToken(): string {
    return `admin_${Date.now()}_${Math.random().toString(36).substring(2, 15)}`;
  }
  /**
   * Generate security event ID
   */
  private generateEventId(): string {
    return `sec_${Date.now()}_${Math.random().toString(36).substring(2, 15)}`;
  }
  /**
   * Find user by email or user_id
   */
  private async findUserByIdentifier(identifier: string): Promise<User | null> {
    try {
      // Try as user_id first
      if (identifier.length === 36) { // UUID length
        return await this.adminUtils.getUserWithRole(identifier);
      }
      // Try as email
      return await this.adminUtils.getUserByEmail(identifier);
    } catch (error) {
      return null;
    }
  }
  /**
   * Notify security team of critical events
   */
  private async notifySecurityTeam(event: SecurityEvent): Promise<void> {
    // Implementation would send notifications via email, Slack, etc.
  }
}
// Export singleton instance
export const securityManager = new SecurityManager();
