/**
 * Security Integration Tests
 * 
 * Tests the complete security system integration including progressive delays,
 * account lockout, MFA enforcement, session management, and IP security.
 */

import { SecurityManager } from '../security-manager';
import { MfaManager } from '../mfa-manager';
import { SessionTimeoutManager } from '../session-timeout-manager';
import { IpSecurityManager } from '../ip-security-manager';
import { EnhancedAuthMiddleware } from '../enhanced-auth-middleware';
import { getAdminDatabaseUtils } from '@/lib/database/admin-utils';
import type { User } from '@/types/admin';

// Mock dependencies
jest.mock('@/lib/database/admin-utils');
jest.mock('speakeasy');
jest.mock('qrcode');

const mockAdminUtils = {
  getUserById: jest.fn(),
  updateUser: jest.fn(),
  createAuditLog: jest.fn(),
  getSystemConfig: jest.fn(),
  getSystemConfigs: jest.fn(),
  getUsers: jest.fn(),
  getUserPermissions: jest.fn(),
};

(getAdminDatabaseUtils as jest.Mock).mockReturnValue(mockAdminUtils);

describe('Security System Integration', () => {
  let securityManager: SecurityManager;
  let mfaManager: MfaManager;
  let sessionManager: SessionTimeoutManager;
  let ipManager: IpSecurityManager;
  let authMiddleware: EnhancedAuthMiddleware;

  const mockUser: User = {
    user_id: 'user-123',
    email: 'admin@example.com',
    full_name: 'Admin User',
    role: 'admin',
    roles: ['admin'],
    tenant_id: 'tenant-1',
    preferences: {},
    is_verified: true,
    is_active: true,
    created_at: new Date(),
    updated_at: new Date(),
    failed_login_attempts: 0,
    two_factor_enabled: true,
    two_factor_secret: 'JBSWY3DPEHPK3PXP',
  };

  const mockSuperAdmin: User = {
    ...mockUser,
    user_id: 'super-admin-123',
    email: 'superadmin@example.com',
    role: 'super_admin',
    roles: ['super_admin'],
  };

  beforeEach(() => {
    securityManager = new SecurityManager();
    mfaManager = new MfaManager();
    sessionManager = new SessionTimeoutManager();
    ipManager = new IpSecurityManager();
    authMiddleware = new EnhancedAuthMiddleware();
    
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    sessionManager.destroy();
    jest.useRealTimers();
  });

  describe('Complete Authentication Flow', () => {
    it('should handle complete successful authentication with all security features', async () => {
      // Setup successful authentication scenario
      mockAdminUtils.getUsers.mockResolvedValue({ data: [mockUser] });
      mockAdminUtils.getUserById.mockResolvedValue(mockUser);
      mockAdminUtils.getSystemConfig.mockResolvedValue({ value: 'true' });
      mockAdminUtils.getSystemConfigs.mockResolvedValue([]);
      
      // Mock successful credential validation
      jest.spyOn(authMiddleware as any, 'validateCredentials').mockResolvedValue(true);
      
      // Mock successful MFA verification
      const mockSpeakeasy = require('speakeasy');
      mockSpeakeasy.totp.verify.mockReturnValue(true);

      const result = await authMiddleware.authenticateUser(
        'admin@example.com',
        'correct-password',
        '123456', // Valid TOTP
        '192.168.1.100',
        'Mozilla/5.0 Test Browser'
      );

      expect(result.success).toBe(true);
      expect(result.user).toBeDefined();
      expect(result.sessionToken).toBeDefined();
      expect(result.mfaRequired).toBe(false);

      // Verify all security components were involved
      expect(mockAdminUtils.createAuditLog).toHaveBeenCalledWith(
        expect.objectContaining({
          action: 'session.created'
        })
      );
    });

    it('should handle progressive security failures', async () => {
      mockAdminUtils.getUsers.mockResolvedValue({ data: [mockUser] });
      mockAdminUtils.getUserById.mockResolvedValue(mockUser);
      
      // Mock failed credential validation
      jest.spyOn(authMiddleware as any, 'validateCredentials').mockResolvedValue(false);

      const results = [];
      
      // Attempt multiple failed logins
      for (let i = 0; i < 6; i++) {
        const result = await authMiddleware.authenticateUser(
          'admin@example.com',
          'wrong-password',
          undefined,
          '192.168.1.100'
        );
        results.push(result);
      }

      // Verify progressive delays
      expect(results[0].delay).toBe(0);  // First attempt
      expect(results[1].delay).toBe(1);  // Second attempt
      expect(results[2].delay).toBe(2);  // Third attempt
      expect(results[4].delay).toBe(10); // Fifth attempt

      // Verify account gets locked after max attempts
      expect(mockAdminUtils.updateUser).toHaveBeenCalledWith(
        'user-123',
        expect.objectContaining({
          locked_until: expect.any(Date)
        })
      );
    });

    it('should enforce MFA requirements for admin users', async () => {
      const adminWithoutMfa = { ...mockUser, two_factor_enabled: false };
      mockAdminUtils.getUsers.mockResolvedValue({ data: [adminWithoutMfa] });
      mockAdminUtils.getUserById.mockResolvedValue(adminWithoutMfa);
      mockAdminUtils.getSystemConfig.mockResolvedValue({ value: 'true' });
      
      jest.spyOn(authMiddleware as any, 'validateCredentials').mockResolvedValue(true);

      const result = await authMiddleware.authenticateUser(
        'admin@example.com',
        'correct-password',
        undefined,
        '192.168.1.100'
      );

      expect(result.success).toBe(false);
      expect(result.error?.code).toBe('MFA_SETUP_REQUIRED');
      expect(result.mfaRequired).toBe(true);
    });
  });

  describe('Session Management Integration', () => {
    it('should create and manage sessions with role-based timeouts', async () => {
      // Create sessions for different roles
      const adminSession = await sessionManager.createSession(
        mockUser,
        'admin-session-123',
        '192.168.1.100',
        'Admin Browser'
      );

      const superAdminSession = await sessionManager.createSession(
        mockSuperAdmin,
        'super-admin-session-456',
        '192.168.1.101',
        'Super Admin Browser'
      );

      // Verify different timeouts
      const adminTimeout = adminSession.expires_at.getTime() - adminSession.created_at.getTime();
      const superAdminTimeout = superAdminSession.expires_at.getTime() - superAdminSession.created_at.getTime();

      expect(adminTimeout).toBe(30 * 60 * 1000); // 30 minutes
      expect(superAdminTimeout).toBe(30 * 60 * 1000); // 30 minutes

      // Test session extension
      const extensionResult = await sessionManager.extendSession('admin-session-123', 'user-123');
      expect(extensionResult.success).toBe(true);

      // Test concurrent session limits
      const canCreateAnother = await securityManager.checkConcurrentSessionLimit('user-123', 'admin');
      expect(canCreateAnother).toBe(true); // Should allow up to 2 sessions for admin
    });

    it('should handle session timeout and cleanup', async () => {
      const session = await sessionManager.createSession(mockUser, 'test-session');
      
      // Fast forward past session expiry
      jest.advanceTimersByTime(35 * 60 * 1000); // 35 minutes
      
      // Trigger cleanup
      jest.advanceTimersByTime(60 * 1000); // 1 minute for cleanup interval
      
      const status = sessionManager.getSessionStatus('test-session');
      expect(status).toBeNull();
    });
  });

  describe('IP Security Integration', () => {
    it('should track and analyze IP access patterns', async () => {
      // Record multiple accesses from same IP
      for (let i = 0; i < 15; i++) {
        await ipManager.recordIpAccess('192.168.1.100', mockUser, 'Test Browser');
      }

      const stats = ipManager.getIpStatistics();
      expect(stats.totalUniqueIps).toBeGreaterThan(0);

      // Record failed attempts to trigger blocking
      for (let i = 0; i < 12; i++) {
        await ipManager.recordFailedAttempt('192.168.1.200', 'attacker@example.com');
      }

      const blockedIps = ipManager.getBlockedIps();
      expect(blockedIps.some(blocked => blocked.ip === '192.168.1.200')).toBe(true);
    });

    it('should enforce IP whitelisting for super admins', async () => {
      // Enable IP whitelisting
      await ipManager.updateConfiguration({
        super_admin_whitelist_enabled: true
      }, 'system');

      // Add IP to whitelist
      await ipManager.addToWhitelist(
        '192.168.1.100',
        'Super Admin Office IP',
        'system',
        mockSuperAdmin.user_id,
        'super_admin'
      );

      // Test allowed IP
      const allowedResult = await ipManager.checkIpAccess('192.168.1.100', mockSuperAdmin);
      expect(allowedResult.allowed).toBe(true);

      // Test blocked IP
      const blockedResult = await ipManager.checkIpAccess('192.168.1.200', mockSuperAdmin);
      expect(blockedResult.allowed).toBe(false);
    });
  });

  describe('MFA Integration', () => {
    it('should handle complete MFA setup and verification flow', async () => {
      const userWithoutMfa = { ...mockUser, two_factor_enabled: false };
      mockAdminUtils.getUserById.mockResolvedValue(userWithoutMfa);

      // Generate MFA setup
      const mockSpeakeasy = require('speakeasy');
      mockSpeakeasy.generateSecret.mockReturnValue({
        base32: 'TESTSECRET123',
        otpauth_url: 'otpauth://totp/test'
      });

      const setupData = await mfaManager.generateMfaSetup(userWithoutMfa);
      expect(setupData.secret).toBe('TESTSECRET123');
      expect(setupData.backupCodes).toHaveLength(10);

      // Enable MFA
      mockSpeakeasy.totp.verify.mockReturnValue(true);
      const enableResult = await mfaManager.enableMfa(
        'user-123',
        'TESTSECRET123',
        '123456',
        setupData.backupCodes
      );
      expect(enableResult).toBe(true);

      // Test MFA verification
      const mfaEnabledUser = { ...userWithoutMfa, two_factor_enabled: true, two_factor_secret: 'TESTSECRET123' };
      mockAdminUtils.getUserById.mockResolvedValue(mfaEnabledUser);

      const verifyResult = await mfaManager.verifyMfaCode('user-123', '123456');
      expect(verifyResult.valid).toBe(true);
    });

    it('should handle backup code usage and regeneration', async () => {
      const userWithMfa = {
        ...mockUser,
        preferences: { mfa_backup_codes: ['BACKUP1', 'BACKUP2', 'BACKUP3'] }
      };
      mockAdminUtils.getUserById.mockResolvedValue(userWithMfa);

      const mockSpeakeasy = require('speakeasy');
      mockSpeakeasy.totp.verify.mockReturnValue(false); // TOTP fails

      // Use backup code
      const result = await mfaManager.verifyMfaCode('user-123', 'BACKUP1');
      expect(result.valid).toBe(true);
      expect(result.usedBackupCode).toBe(true);
      expect(result.remainingBackupCodes).toBe(2);

      // Regenerate backup codes
      const newCodes = await mfaManager.regenerateBackupCodes('user-123', 'admin-456');
      expect(newCodes).toHaveLength(10);
    });
  });

  describe('Security Event Detection and Response', () => {
    it('should detect and log suspicious activities', async () => {
      // Simulate suspicious activity: multiple failed attempts from same IP
      for (let i = 0; i < 15; i++) {
        await securityManager.recordFailedLogin('victim@example.com', '192.168.1.200');
      }

      // Verify security events were logged
      expect(mockAdminUtils.createAuditLog).toHaveBeenCalledWith(
        expect.objectContaining({
          action: 'security.event'
        })
      );

      // Check for security events
      const events = securityManager.getSecurityEvents('system');
      expect(events.length).toBeGreaterThan(0);
    });

    it('should handle privilege escalation monitoring', async () => {
      const regularUser = { ...mockUser, role: 'user' as const };
      mockAdminUtils.getSystemConfig.mockResolvedValue({ value: 'true' });

      // Attempt to enforce MFA on regular user (should not require)
      const enforcement = await securityManager.enforceMfaRequirement(regularUser);
      expect(enforcement.required).toBe(false);

      // Attempt to enforce MFA on admin (should require)
      const adminEnforcement = await securityManager.enforceMfaRequirement(mockUser);
      expect(adminEnforcement.required).toBe(true);
    });
  });

  describe('Error Handling and Recovery', () => {
    it('should handle database failures gracefully', async () => {
      mockAdminUtils.getUserById.mockRejectedValue(new Error('Database connection failed'));

      // Security operations should not crash
      const isLocked = await securityManager.isAccountLocked('user-123');
      expect(isLocked).toBe(false); // Should default to safe state

      const mfaStatus = await mfaManager.getMfaStatus('user-123');
      expect(mfaStatus.enabled).toBe(false); // Should default to safe state
    });

    it('should handle concurrent operations safely', async () => {
      // Simulate concurrent login attempts
      const promises = [];
      for (let i = 0; i < 5; i++) {
        promises.push(
          securityManager.recordFailedLogin('test@example.com', '192.168.1.100')
        );
      }

      const delays = await Promise.all(promises);
      
      // All operations should complete without errors
      expect(delays.every(delay => typeof delay === 'number')).toBe(true);
    });
  });

  describe('Performance and Cleanup', () => {
    it('should perform regular cleanup operations', async () => {
      // Create some test data
      await sessionManager.createSession(mockUser, 'test-session-1');
      await securityManager.logSecurityEvent({
        event_type: 'suspicious_activity',
        user_id: 'user-123',
        details: { test: true },
        severity: 'low'
      });

      // Perform cleanup
      await securityManager.cleanupSecurityData();

      // Verify cleanup was logged
      expect(mockAdminUtils.createAuditLog).toHaveBeenCalledWith(
        expect.objectContaining({
          action: 'security.cleanup.sessions'
        })
      );
    });

    it('should provide comprehensive security statistics', async () => {
      // Create test sessions
      await sessionManager.createSession(mockUser, 'admin-session');
      await sessionManager.createSession(mockSuperAdmin, 'super-admin-session');

      // Get session statistics
      const sessionStats = sessionManager.getSessionStatistics();
      expect(sessionStats.totalActiveSessions).toBe(2);
      expect(sessionStats.sessionsByRole.admin).toBe(1);
      expect(sessionStats.sessionsByRole.super_admin).toBe(1);

      // Get IP statistics
      await ipManager.recordIpAccess('192.168.1.100', mockUser);
      await ipManager.recordIpAccess('192.168.1.101', mockSuperAdmin);

      const ipStats = ipManager.getIpStatistics();
      expect(ipStats.totalUniqueIps).toBeGreaterThan(0);
    });
  });

  describe('Configuration Management', () => {
    it('should handle security configuration updates', async () => {
      // Update IP security configuration
      await ipManager.updateConfiguration({
        max_failed_attempts_per_ip: 5,
        ip_lockout_duration: 60 * 60 * 1000, // 1 hour
        suspicious_activity_threshold: 15
      }, 'admin-123');

      // Verify configuration was logged
      expect(mockAdminUtils.createAuditLog).toHaveBeenCalledWith(
        expect.objectContaining({
          action: 'ip.config_updated'
        })
      );
    });

    it('should load and apply system configurations', async () => {
      mockAdminUtils.getSystemConfigs.mockResolvedValue([
        { key: 'mfa_required_for_admins', value: 'true', category: 'security' },
        { key: 'session_timeout_admin', value: '1800', category: 'security' }
      ]);

      // Configuration should be applied during initialization
      const mfaRequired = await mfaManager.isMfaRequired(mockUser);
      expect(mfaRequired).toBe(true);
    });
  });
});