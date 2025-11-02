/**
 * Session Timeout Manager for Admin Management System
 * 
 * Implements role-based session timeout management with automatic cleanup,
 * warning notifications, and graceful session extension.
 * 
 * Requirements: 5.5
 */
import { getAdminDatabaseUtils } from '@/lib/database/admin-utils';
import type { User, AdminSession } from '@/types/admin';
export interface ConcurrentSessionSummary {
  user_id: string;
  email: string;
  role: string;
  session_count: number;
  last_activity: string;
  active_sessions: Array<{
    session_token: string;
    ip_address?: string;
    user_agent?: string;
    created_at: string;
    last_accessed: string;
    expires_at: string;
  }>;
}
export interface SessionTimeoutConfig {
  warningThreshold: number; // Seconds before expiry to show warning
  extensionDuration: number; // Seconds to extend session
  maxExtensions: number; // Maximum number of extensions allowed
  cleanupInterval: number; // Interval for cleanup in milliseconds
}
export interface SessionStatus {
  isValid: boolean;
  expiresAt: Date;
  timeRemaining: number; // Seconds
  warningActive: boolean;
  extensionsUsed: number;
  maxExtensions: number;
}
export class SessionTimeoutManager {
  private adminUtils = getAdminDatabaseUtils();
  private cleanupInterval: NodeJS.Timeout | null = null;
  private sessionWarnings = new Map<string, NodeJS.Timeout>();
  // Role-based timeout configurations (in seconds)
  private readonly TIMEOUT_CONFIG = {
    super_admin: {
      timeout: 30 * 60, // 30 minutes
      warningThreshold: 5 * 60, // 5 minutes warning
      extensionDuration: 15 * 60, // 15 minutes extension
      maxExtensions: 2, // Maximum 2 extensions
      cleanupInterval: 60 * 1000 // 1 minute cleanup interval
    },
    admin: {
      timeout: 30 * 60, // 30 minutes
      warningThreshold: 5 * 60, // 5 minutes warning
      extensionDuration: 15 * 60, // 15 minutes extension
      maxExtensions: 3, // Maximum 3 extensions
      cleanupInterval: 60 * 1000 // 1 minute cleanup interval
    },
    user: {
      timeout: 60 * 60, // 60 minutes
      warningThreshold: 10 * 60, // 10 minutes warning
      extensionDuration: 30 * 60, // 30 minutes extension
      maxExtensions: 5, // Maximum 5 extensions
      cleanupInterval: 5 * 60 * 1000 // 5 minutes cleanup interval
    }
  };
  // In-memory session storage (use Redis in production)
  private activeSessions = new Map<string, AdminSession & { extensionsUsed: number }>();
  constructor() {
    this.startCleanupProcess();
  }
  /**
   * Create a new session with role-based timeout
   */
  async createSession(user: User, sessionToken: string, ipAddress?: string, userAgent?: string): Promise<AdminSession> {
    const config = this.TIMEOUT_CONFIG[user.role];
    const now = new Date();
    const expiresAt = new Date(now.getTime() + config.timeout * 1000);
    const session: AdminSession & { extensionsUsed: number } = {
      session_token: sessionToken,
      user_id: user.user_id,
      user_email: user.email,
      user_role: user.role,
      ip_address: ipAddress,
      user_agent: userAgent,
      created_at: now,
      last_accessed: now,
      expires_at: expiresAt,
      is_active: true,
      extensionsUsed: 0
    };
    this.activeSessions.set(sessionToken, session);
    // Schedule warning notification
    this.scheduleWarning(sessionToken, config.warningThreshold);
    // Log session creation
    await this.adminUtils.createAuditLog({
      user_id: user.user_id,
      action: 'session.created',
      resource_type: 'admin_session',
      resource_id: sessionToken,
      details: {
        timeout_seconds: config.timeout,
        expires_at: expiresAt.toISOString(),
        user_role: user.role,
        warning_threshold: config.warningThreshold
      },
      ip_address: ipAddress,
      user_agent: userAgent

    return session;
  }
  /**
   * Update session last accessed time
   */
  async updateSessionActivity(sessionToken: string): Promise<boolean> {
    const session = this.activeSessions.get(sessionToken);
    if (!session || !session.is_active) {
      return false;
    }
    const now = new Date();
    // Check if session has expired
    if (now > session.expires_at) {
      await this.expireSession(sessionToken, 'timeout');
      return false;
    }
    // Update last accessed time
    session.last_accessed = now;
    this.activeSessions.set(sessionToken, session);
    return true;
  }
  /**
   * Extend session timeout
   */
  async extendSession(sessionToken: string, userId: string): Promise<{ success: boolean; newExpiryTime?: Date; message?: string }> {
    const session = this.activeSessions.get(sessionToken);
    if (!session || !session.is_active) {
      return { success: false, message: 'Session not found or inactive' };
    }
    const config = this.TIMEOUT_CONFIG[session.user_role as keyof typeof this.TIMEOUT_CONFIG];
    // Check if maximum extensions reached
    if (session.extensionsUsed >= config.maxExtensions) {
      return { 
        success: false, 
        message: `Maximum session extensions (${config.maxExtensions}) reached` 
      };
    }
    // Extend session
    const now = new Date();
    const newExpiryTime = new Date(now.getTime() + config.extensionDuration * 1000);
    session.expires_at = newExpiryTime;
    session.extensionsUsed++;
    session.last_accessed = now;
    this.activeSessions.set(sessionToken, session);
    // Clear existing warning and schedule new one
    this.clearWarning(sessionToken);
    this.scheduleWarning(sessionToken, config.warningThreshold);
    // Log session extension
    await this.adminUtils.createAuditLog({
      user_id: userId,
      action: 'session.extended',
      resource_type: 'admin_session',
      resource_id: sessionToken,
      details: {
        extension_duration: config.extensionDuration,
        new_expiry: newExpiryTime.toISOString(),
        extensions_used: session.extensionsUsed,
        max_extensions: config.maxExtensions
      }

    return { 
      success: true, 
      newExpiryTime,
      message: `Session extended by ${config.extensionDuration / 60} minutes` 
    };
  }
  /**
   * Get session status
   */
  getSessionStatus(sessionToken: string): SessionStatus | null {
    const session = this.activeSessions.get(sessionToken);
    if (!session) {
      return null;
    }
    const now = new Date();
    const timeRemaining = Math.max(0, Math.floor((session.expires_at.getTime() - now.getTime()) / 1000));
    const config = this.TIMEOUT_CONFIG[session.user_role as keyof typeof this.TIMEOUT_CONFIG];
    const warningActive = timeRemaining <= config.warningThreshold && timeRemaining > 0;
    return {
      isValid: session.is_active && timeRemaining > 0,
      expiresAt: session.expires_at,
      timeRemaining,
      warningActive,
      extensionsUsed: session.extensionsUsed,
      maxExtensions: config.maxExtensions
    };
  }
  /**
   * Terminate session manually
   */
  async terminateSession(sessionToken: string, reason: string = 'manual'): Promise<void> {
    const session = this.activeSessions.get(sessionToken);
    if (session) {
      await this.expireSession(sessionToken, reason);
    }
  }
  /**
   * Get all active sessions for a user
   */
  getUserSessions(userId: string): (AdminSession & { extensionsUsed: number })[] {
    const userSessions: (AdminSession & { extensionsUsed: number })[] = [];
    for (const session of this.activeSessions.values()) {
      if (session.user_id === userId && session.is_active) {
        userSessions.push(session);
      }
    }
    return userSessions;
  }
  /**
   * Terminate all sessions for a user
   */
  async terminateUserSessions(userId: string, reason: string = 'admin_action'): Promise<number> {
    const userSessions = this.getUserSessions(userId);
    for (const session of userSessions) {
      await this.expireSession(session.session_token, reason);
    }
    return userSessions.length;
  }
  /**
   * Get session statistics
   */
  getSessionStatistics(): {
    totalActiveSessions: number;
    sessionsByRole: Record<string, number>;
    averageSessionDuration: number;
    expiringSoon: number;
  } {
    const now = new Date();
    const stats = {
      totalActiveSessions: 0,
      sessionsByRole: {} as Record<string, number>,
      averageSessionDuration: 0,
      expiringSoon: 0
    };
    let totalDuration = 0;
    for (const session of this.activeSessions.values()) {
      if (session.is_active) {
        stats.totalActiveSessions++;
        // Count by role
        stats.sessionsByRole[session.user_role] = (stats.sessionsByRole[session.user_role] || 0) + 1;
        // Calculate duration
        const duration = now.getTime() - session.created_at.getTime();
        totalDuration += duration;
        // Check if expiring soon (within 10 minutes)
        const timeRemaining = session.expires_at.getTime() - now.getTime();
        if (timeRemaining <= 10 * 60 * 1000 && timeRemaining > 0) {
          stats.expiringSoon++;
        }
      }
    }
    if (stats.totalActiveSessions > 0) {
      stats.averageSessionDuration = Math.floor(totalDuration / stats.totalActiveSessions / 1000); // in seconds
    }
    return stats;
  }
  getConcurrentSessionsByUser(limit = 10): ConcurrentSessionSummary[] {
    const aggregated = new Map<
      string,
      {
        user_id: string;
        email: string;
        role: string;
        session_count: number;
        last_activity: Date;
        sessions: Array<AdminSession & { extensionsUsed: number }>;
      }
    >();
    for (const session of this.activeSessions.values()) {
      if (!session.is_active) {
        continue;
      }
      const existing = aggregated.get(session.user_id);
      if (!existing) {
        aggregated.set(session.user_id, {
          user_id: session.user_id,
          email: session.user_email,
          role: session.user_role,
          session_count: 1,
          last_activity: session.last_accessed,
          sessions: [session]

        continue;
      }
      existing.session_count += 1;
      existing.sessions.push(session);
      if (session.last_accessed > existing.last_activity) {
        existing.last_activity = session.last_accessed;
      }
    }
    return Array.from(aggregated.values())
      .sort((a, b) => {
        if (b.session_count !== a.session_count) {
          return b.session_count - a.session_count;
        }
        return b.last_activity.getTime() - a.last_activity.getTime();
      })
      .slice(0, limit)
      .map(summary => ({
        user_id: summary.user_id,
        email: summary.email,
        role: summary.role,
        session_count: summary.session_count,
        last_activity: summary.last_activity.toISOString(),
        active_sessions: summary.sessions.map(activeSession => ({
          session_token: activeSession.session_token,
          ip_address: activeSession.ip_address,
          user_agent: activeSession.user_agent,
          created_at: activeSession.created_at.toISOString(),
          last_accessed: activeSession.last_accessed.toISOString(),
          expires_at: activeSession.expires_at.toISOString()
        }))
      }));
  }
  /**
   * Schedule warning notification for session expiry
   */
  private scheduleWarning(sessionToken: string, warningThreshold: number): void {
    const session = this.activeSessions.get(sessionToken);
    if (!session) return;
    const now = new Date();
    const warningTime = session.expires_at.getTime() - warningThreshold * 1000;
    const delay = Math.max(0, warningTime - now.getTime());
    const warningTimeout = setTimeout(() => {
      this.triggerSessionWarning(sessionToken);
    }, delay);
    this.sessionWarnings.set(sessionToken, warningTimeout);
  }
  /**
   * Clear warning for session
   */
  private clearWarning(sessionToken: string): void {
    const warning = this.sessionWarnings.get(sessionToken);
    if (warning) {
      clearTimeout(warning);
      this.sessionWarnings.delete(sessionToken);
    }
  }
  /**
   * Trigger session warning (in production, this would send notifications)
   */
  private async triggerSessionWarning(sessionToken: string): Promise<void> {
    const session = this.activeSessions.get(sessionToken);
    if (!session || !session.is_active) return;
    const timeRemaining = Math.max(0, Math.floor((session.expires_at.getTime() - Date.now()) / 1000));
    // Log warning
    await this.adminUtils.createAuditLog({
      user_id: session.user_id,
      action: 'session.warning',
      resource_type: 'admin_session',
      resource_id: sessionToken,
      details: {
        time_remaining: timeRemaining,
        expires_at: session.expires_at.toISOString(),
        extensions_used: session.extensionsUsed,
        warning_triggered_at: new Date().toISOString()
      }

    // In production, send real-time notification to user
  }
  /**
   * Expire a session
   */
  private async expireSession(sessionToken: string, reason: string): Promise<void> {
    const session = this.activeSessions.get(sessionToken);
    if (!session) return;
    session.is_active = false;
    this.clearWarning(sessionToken);
    // Log session expiry
    await this.adminUtils.createAuditLog({
      user_id: session.user_id,
      action: 'session.expired',
      resource_type: 'admin_session',
      resource_id: sessionToken,
      details: {
        reason,
        session_duration: Date.now() - session.created_at.getTime(),
        extensions_used: session.extensionsUsed,
        expired_at: new Date().toISOString()
      }

    // Remove from active sessions
    this.activeSessions.delete(sessionToken);
  }
  /**
   * Start automatic cleanup process
   */
  private startCleanupProcess(): void {
    // Run cleanup every minute
    this.cleanupInterval = setInterval(() => {
      this.cleanupExpiredSessions();
    }, 60 * 1000);
  }
  /**
   * Clean up expired sessions
   */
  private async cleanupExpiredSessions(): Promise<void> {
    const now = new Date();
    const expiredSessions: string[] = [];
    for (const [sessionToken, session] of this.activeSessions.entries()) {
      if (session.is_active && now > session.expires_at) {
        expiredSessions.push(sessionToken);
      }
    }
    for (const sessionToken of expiredSessions) {
      await this.expireSession(sessionToken, 'timeout');
    }
    if (expiredSessions.length > 0) {
    }
  }
  /**
   * Stop cleanup process
   */
  destroy(): void {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
      this.cleanupInterval = null;
    }
    // Clear all warnings
    for (const warning of this.sessionWarnings.values()) {
      clearTimeout(warning);
    }
    this.sessionWarnings.clear();
  }
}
// Export singleton instance
export const sessionTimeoutManager = new SessionTimeoutManager();
