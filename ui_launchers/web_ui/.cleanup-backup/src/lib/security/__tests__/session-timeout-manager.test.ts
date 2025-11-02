/**
 * Session Timeout Manager Tests
 * 
 * Tests for role-based session timeout management, automatic cleanup,
 * warning notifications, and session extension.
 */

import { SessionTimeoutManager } from '../session-timeout-manager';
import { getAdminDatabaseUtils } from '@/lib/database/admin-utils';
import type { User } from '@/types/admin';

// Mock dependencies
jest.mock('@/lib/database/admin-utils');

const mockAdminUtils = {
  createAuditLog: jest.fn(),
};

(getAdminDatabaseUtils as jest.Mock).mockReturnValue(mockAdminUtils);

describe('SessionTimeoutManager', () => {
  let sessionManager: SessionTimeoutManager;
  
  const mockUser: User = {
    user_id: 'user-123',
    email: 'test@example.com',
    full_name: 'Test User',
    role: 'admin',
    roles: ['admin'],
    tenant_id: 'tenant-1',
    preferences: {},
    is_verified: true,
    is_active: true,
    created_at: new Date(),
    updated_at: new Date(),
    failed_login_attempts: 0,
    two_factor_enabled: false,
  };

  beforeEach(() => {
    sessionManager = new SessionTimeoutManager();
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    sessionManager.destroy();
    jest.useRealTimers();
  });

  describe('Session Creation', () => {
    it('should create session with correct timeout for admin', async () => {
      const session = await sessionManager.createSession(
        mockUser,
        'session-123',
        '192.168.1.1',
        'test-agent'
      );

      expect(session.session_token).toBe('session-123');
      expect(session.user_id).toBe('user-123');
      expect(session.user_role).toBe('admin');
      expect(session.ip_address).toBe('192.168.1.1');
      expect(session.user_agent).toBe('test-agent');
      expect(session.is_active).toBe(true);

      // Check timeout (30 minutes for admin)
      const expectedTimeout = 30 * 60 * 1000;
      const actualTimeout = session.expires_at.getTime() - session.created_at.getTime();
      expect(actualTimeout).toBe(expectedTimeout);

      expect(mockAdminUtils.createAuditLog).toHaveBeenCalledWith(
        expect.objectContaining({
          action: 'session.created',
          user_id: 'user-123'
        })
      );
    });

    it('should create session with correct timeout for super admin', async () => {
      const superAdminUser = { ...mockUser, role: 'super_admin' as const };
      
      const session = await sessionManager.createSession(superAdminUser, 'session-456');

      // Check timeout (30 minutes for super admin)
      const expectedTimeout = 30 * 60 * 1000;
      const actualTimeout = session.expires_at.getTime() - session.created_at.getTime();
      expect(actualTimeout).toBe(expectedTimeout);
    });

    it('should create session with correct timeout for regular user', async () => {
      const regularUser = { ...mockUser, role: 'user' as const };
      
      const session = await sessionManager.createSession(regularUser, 'session-789');

      // Check timeout (60 minutes for regular user)
      const expectedTimeout = 60 * 60 * 1000;
      const actualTimeout = session.expires_at.getTime() - session.created_at.getTime();
      expect(actualTimeout).toBe(expectedTimeout);
    });
  });

  describe('Session Activity Updates', () => {
    it('should update session activity for valid session', async () => {
      const session = await sessionManager.createSession(mockUser, 'session-123');
      
      const updated = await sessionManager.updateSessionActivity('session-123');
      
      expect(updated).toBe(true);
    });

    it('should reject activity update for expired session', async () => {
      const session = await sessionManager.createSession(mockUser, 'session-123');
      
      // Fast forward past expiry
      jest.advanceTimersByTime(31 * 60 * 1000); // 31 minutes
      
      const updated = await sessionManager.updateSessionActivity('session-123');
      
      expect(updated).toBe(false);
    });

    it('should reject activity update for non-existent session', async () => {
      const updated = await sessionManager.updateSessionActivity('nonexistent-session');
      
      expect(updated).toBe(false);
    });
  });

  describe('Session Extension', () => {
    it('should extend session successfully', async () => {
      const session = await sessionManager.createSession(mockUser, 'session-123');
      const originalExpiry = session.expires_at;
      
      const result = await sessionManager.extendSession('session-123', 'user-123');
      
      expect(result.success).toBe(true);
      expect(result.newExpiryTime).toBeDefined();
      expect(result.newExpiryTime!.getTime()).toBeGreaterThan(originalExpiry.getTime());
      expect(result.message).toContain('extended by 15 minutes');

      expect(mockAdminUtils.createAuditLog).toHaveBeenCalledWith(
        expect.objectContaining({
          action: 'session.extended',
          user_id: 'user-123'
        })
      );
    });

    it('should reject extension when max extensions reached', async () => {
      const session = await sessionManager.createSession(mockUser, 'session-123');
      
      // Extend to maximum (3 times for admin)
      for (let i = 0; i < 3; i++) {
        await sessionManager.extendSession('session-123', 'user-123');
      }
      
      // Try to extend beyond maximum
      const result = await sessionManager.extendSession('session-123', 'user-123');
      
      expect(result.success).toBe(false);
      expect(result.message).toContain('Maximum session extensions');
    });

    it('should reject extension for non-existent session', async () => {
      const result = await sessionManager.extendSession('nonexistent-session', 'user-123');
      
      expect(result.success).toBe(false);
      expect(result.message).toBe('Session not found or inactive');
    });
  });

  describe('Session Status', () => {
    it('should return correct session status', async () => {
      const session = await sessionManager.createSession(mockUser, 'session-123');
      
      const status = sessionManager.getSessionStatus('session-123');
      
      expect(status).toBeDefined();
      expect(status!.isValid).toBe(true);
      expect(status!.expiresAt).toEqual(session.expires_at);
      expect(status!.timeRemaining).toBeGreaterThan(0);
      expect(status!.extensionsUsed).toBe(0);
      expect(status!.maxExtensions).toBe(3); // Admin max extensions
    });

    it('should return null for non-existent session', () => {
      const status = sessionManager.getSessionStatus('nonexistent-session');
      
      expect(status).toBeNull();
    });

    it('should show warning when session is expiring soon', async () => {
      const session = await sessionManager.createSession(mockUser, 'session-123');
      
      // Fast forward to warning threshold (5 minutes before expiry)
      jest.advanceTimersByTime(26 * 60 * 1000); // 26 minutes (4 minutes remaining)
      
      const status = sessionManager.getSessionStatus('session-123');
      
      expect(status!.warningActive).toBe(true);
      expect(status!.timeRemaining).toBeLessThan(5 * 60); // Less than 5 minutes
    });
  });

  describe('Session Termination', () => {
    it('should terminate session manually', async () => {
      const session = await sessionManager.createSession(mockUser, 'session-123');
      
      await sessionManager.terminateSession('session-123', 'manual');
      
      const status = sessionManager.getSessionStatus('session-123');
      expect(status).toBeNull();
    });

    it('should terminate all user sessions', async () => {
      // Create multiple sessions for the same user
      await sessionManager.createSession(mockUser, 'session-1');
      await sessionManager.createSession(mockUser, 'session-2');
      await sessionManager.createSession(mockUser, 'session-3');
      
      const terminatedCount = await sessionManager.terminateUserSessions('user-123', 'admin_action');
      
      expect(terminatedCount).toBe(3);
      
      // Verify all sessions are terminated
      expect(sessionManager.getSessionStatus('session-1')).toBeNull();
      expect(sessionManager.getSessionStatus('session-2')).toBeNull();
      expect(sessionManager.getSessionStatus('session-3')).toBeNull();
    });
  });

  describe('Session Statistics', () => {
    it('should provide accurate session statistics', async () => {
      // Create sessions for different roles
      await sessionManager.createSession(mockUser, 'admin-session');
      await sessionManager.createSession({ ...mockUser, role: 'super_admin' }, 'super-admin-session');
      await sessionManager.createSession({ ...mockUser, role: 'user' }, 'user-session');
      
      const stats = sessionManager.getSessionStatistics();
      
      expect(stats.totalActiveSessions).toBe(3);
      expect(stats.sessionsByRole.admin).toBe(1);
      expect(stats.sessionsByRole.super_admin).toBe(1);
      expect(stats.sessionsByRole.user).toBe(1);
      expect(stats.averageSessionDuration).toBeGreaterThan(0);
    });

    it('should count expiring sessions correctly', async () => {
      const session = await sessionManager.createSession(mockUser, 'session-123');
      
      // Fast forward to within 10 minutes of expiry
      jest.advanceTimersByTime(25 * 60 * 1000); // 25 minutes (5 minutes remaining)
      
      const stats = sessionManager.getSessionStatistics();
      
      expect(stats.expiringSoon).toBe(1);
    });
  });

  describe('Automatic Cleanup', () => {
    it('should clean up expired sessions automatically', async () => {
      const session = await sessionManager.createSession(mockUser, 'session-123');
      
      // Fast forward past expiry
      jest.advanceTimersByTime(35 * 60 * 1000); // 35 minutes
      
      // Trigger cleanup
      jest.advanceTimersByTime(60 * 1000); // 1 minute for cleanup interval
      
      const status = sessionManager.getSessionStatus('session-123');
      expect(status).toBeNull();
    });
  });

  describe('Session Warnings', () => {
    it('should trigger warning before session expiry', async () => {
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();
      
      const session = await sessionManager.createSession(mockUser, 'session-123');
      
      // Fast forward to warning time (5 minutes before expiry)
      jest.advanceTimersByTime(25 * 60 * 1000); // 25 minutes
      
      expect(mockAdminUtils.createAuditLog).toHaveBeenCalledWith(
        expect.objectContaining({
          action: 'session.warning'
        })
      );
      
      consoleSpy.mockRestore();
    });
  });

  describe('User Sessions', () => {
    it('should get all active sessions for a user', async () => {
      await sessionManager.createSession(mockUser, 'session-1');
      await sessionManager.createSession(mockUser, 'session-2');
      
      const userSessions = sessionManager.getUserSessions('user-123');
      
      expect(userSessions).toHaveLength(2);
      expect(userSessions.every(s => s.user_id === 'user-123')).toBe(true);
      expect(userSessions.every(s => s.is_active)).toBe(true);
    });

    it('should return empty array for user with no sessions', () => {
      const userSessions = sessionManager.getUserSessions('nonexistent-user');
      
      expect(userSessions).toHaveLength(0);
    });
  });

  describe('Error Handling', () => {
    it('should handle audit log errors gracefully', async () => {
      mockAdminUtils.createAuditLog.mockRejectedValue(new Error('Audit log error'));
      
      // Should not throw
      await expect(sessionManager.createSession(mockUser, 'session-123')).resolves.toBeDefined();
    });
  });
});