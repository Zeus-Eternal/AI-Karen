/**
 * Security Manager Tests
 * 
 * Tests for progressive login delays, account lockout, MFA enforcement,
 * session timeout management, and security event detection.
 */

import { SecurityManager, SECURITY_CONFIG } from '../security-manager';
import { getAdminDatabaseUtils } from '@/lib/database/admin-utils';
import type { User } from '@/types/admin';

import { vi } from 'vitest';

// Mock dependencies
vi.mock('@/lib/database/admin-utils');

const mockAdminUtils = {
  getUserById: vi.fn(),
  updateUser: vi.fn(),
  createAuditLog: vi.fn(),
  getSystemConfig: vi.fn(),
  getUsers: vi.fn(),
};

(getAdminDatabaseUtils as any).mockReturnValue(mockAdminUtils);

describe('SecurityManager', () => {
  let securityManager: SecurityManager;
  
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
    securityManager = new SecurityManager();
    vi.clearAllMocks();

  describe('Account Lockout', () => {
    it('should detect unlocked account', async () => {
      mockAdminUtils.getUserById.mockResolvedValue(mockUser);
      
      const isLocked = await securityManager.isAccountLocked('user-123');
      
      expect(isLocked).toBe(false);
      expect(mockAdminUtils.getUserById).toHaveBeenCalledWith('user-123');

    it('should detect locked account', async () => {
      const lockedUser = {
        ...mockUser,
        locked_until: new Date(Date.now() + 60000) // Locked for 1 minute
      };
      mockAdminUtils.getUserById.mockResolvedValue(lockedUser);
      
      const isLocked = await securityManager.isAccountLocked('user-123');
      
      expect(isLocked).toBe(true);

    it('should unlock expired lock', async () => {
      const expiredLockUser = {
        ...mockUser,
        locked_until: new Date(Date.now() - 60000) // Expired 1 minute ago
      };
      mockAdminUtils.getUserById.mockResolvedValue(expiredLockUser);
      
      const isLocked = await securityManager.isAccountLocked('user-123');
      
      expect(isLocked).toBe(false);
      expect(mockAdminUtils.updateUser).toHaveBeenCalledWith('user-123', {
        locked_until: undefined,
        failed_login_attempts: 0


    it('should lock account after max failed attempts', async () => {
      mockAdminUtils.getUsers.mockResolvedValue({
        data: [mockUser]

      // Simulate max failed attempts
      for (let i = 0; i < SECURITY_CONFIG.MAX_FAILED_ATTEMPTS; i++) {
        await securityManager.recordFailedLogin('test@example.com', '192.168.1.1');
      }
      
      expect(mockAdminUtils.updateUser).toHaveBeenCalledWith(
        'user-123',
        expect.objectContaining({
          locked_until: expect.any(Date)
        })
      );


  describe('Progressive Login Delays', () => {
    it('should apply progressive delays', async () => {
      const delays: number[] = [];
      
      for (let i = 0; i < 5; i++) {
        const delay = await securityManager.recordFailedLogin('test@example.com', '192.168.1.1');
        delays.push(delay);
      }
      
      // Verify delays are progressive
      expect(delays[0]).toBe(0); // First attempt has no delay
      expect(delays[1]).toBe(1); // Second attempt has 1 second delay
      expect(delays[2]).toBe(2); // Third attempt has 2 second delay
      expect(delays[3]).toBe(5); // Fourth attempt has 5 second delay
      expect(delays[4]).toBe(10); // Fifth attempt has 10 second delay

    it('should reset delays after timeout', async () => {
      // Record failed attempt
      await securityManager.recordFailedLogin('test@example.com', '192.168.1.1');
      
      // Mock time passage (more than 1 hour)
      vi.spyOn(Date, 'now').mockReturnValue(Date.now() + 2 * 60 * 60 * 1000);
      
      // Next attempt should have no delay
      const delay = await securityManager.recordFailedLogin('test@example.com', '192.168.1.1');
      expect(delay).toBe(0);

    it('should clear failed attempts after successful login', () => {
      securityManager.clearFailedAttempts('test@example.com', '192.168.1.1');
      
      // This should not throw and should clear internal state
      expect(() => {
        securityManager.clearFailedAttempts('test@example.com', '192.168.1.1');
      }).not.toThrow();


  describe('MFA Enforcement', () => {
    it('should require MFA for super admin', async () => {
      const superAdminUser = { ...mockUser, role: 'super_admin' as const };
      mockAdminUtils.getSystemConfig.mockResolvedValue({ value: 'true' });
      
      const required = await securityManager.isMfaRequired(superAdminUser);
      
      expect(required).toBe(true);
      expect(mockAdminUtils.getSystemConfig).toHaveBeenCalledWith('mfa_required_for_admins');

    it('should require MFA for admin when configured', async () => {
      mockAdminUtils.getSystemConfig.mockResolvedValue({ value: true });
      
      const required = await securityManager.isMfaRequired(mockUser);
      
      expect(required).toBe(true);

    it('should not require MFA for regular users', async () => {
      const regularUser = { ...mockUser, role: 'user' as const };
      
      const required = await securityManager.isMfaRequired(regularUser);
      
      expect(required).toBe(false);

    it('should enforce MFA requirement', async () => {
      const adminUser = { ...mockUser, two_factor_enabled: false };
      mockAdminUtils.getSystemConfig.mockResolvedValue({ value: 'true' });
      
      const enforcement = await securityManager.enforceMfaRequirement(adminUser);
      
      expect(enforcement.required).toBe(true);
      expect(enforcement.enabled).toBe(false);
      expect(mockAdminUtils.createAuditLog).toHaveBeenCalledWith(
        expect.objectContaining({
          action: 'security.event',
          details: expect.objectContaining({
            event_type: 'privilege_escalation'
          })
        })
      );


  describe('Session Management', () => {
    it('should get correct session timeout for roles', () => {
      expect(securityManager.getSessionTimeout('super_admin')).toBe(SECURITY_CONFIG.SUPER_ADMIN_SESSION_TIMEOUT);
      expect(securityManager.getSessionTimeout('admin')).toBe(SECURITY_CONFIG.ADMIN_SESSION_TIMEOUT);
      expect(securityManager.getSessionTimeout('user')).toBe(SECURITY_CONFIG.USER_SESSION_TIMEOUT);

    it('should check concurrent session limits', async () => {
      const canCreate = await securityManager.checkConcurrentSessionLimit('user-123', 'super_admin');
      
      expect(canCreate).toBe(true); // No existing sessions

    it('should create admin session with proper timeout', async () => {
      const session = await securityManager.createAdminSession(mockUser, '192.168.1.1', 'test-agent');
      
      expect(session.user_id).toBe(mockUser.user_id);
      expect(session.user_role).toBe(mockUser.role);
      expect(session.ip_address).toBe('192.168.1.1');
      expect(session.user_agent).toBe('test-agent');
      expect(session.is_active).toBe(true);
      
      expect(mockAdminUtils.createAuditLog).toHaveBeenCalledWith(
        expect.objectContaining({
          action: 'session.created',
          user_id: mockUser.user_id
        })
      );

    it('should terminate session', async () => {
      const session = await securityManager.createAdminSession(mockUser);
      
      await securityManager.terminateSession(session.session_token, mockUser.user_id);
      
      expect(mockAdminUtils.createAuditLog).toHaveBeenCalledWith(
        expect.objectContaining({
          action: 'session.terminated',
          resource_id: session.session_token
        })
      );


  describe('Security Events', () => {
    it('should log security event', async () => {
      await securityManager.logSecurityEvent({
        event_type: 'suspicious_activity',
        user_id: 'user-123',
        ip_address: '192.168.1.1',
        details: { reason: 'test' },
        severity: 'medium'

      expect(mockAdminUtils.createAuditLog).toHaveBeenCalledWith(
        expect.objectContaining({
          action: 'security.event',
          resource_type: 'security_event'
        })
      );

    it('should get security events', () => {
      const events = securityManager.getSecurityEvents('user-123');
      expect(Array.isArray(events)).toBe(true);

    it('should resolve security event', async () => {
      // First create an event
      await securityManager.logSecurityEvent({
        event_type: 'suspicious_activity',
        user_id: 'user-123',
        details: {},
        severity: 'low'

      const events = securityManager.getSecurityEvents('user-123');
      const eventId = events[0]?.id;
      
      if (eventId) {
        await securityManager.resolveSecurityEvent(eventId, 'admin-123');
        
        expect(mockAdminUtils.createAuditLog).toHaveBeenCalledWith(
          expect.objectContaining({
            action: 'security.event.resolved',
            resource_id: eventId
          })
        );
      }


  describe('IP Whitelisting', () => {
    it('should check super admin IP whitelist when disabled', async () => {
      const allowed = await securityManager.checkSuperAdminIpWhitelist('192.168.1.1');
      expect(allowed).toBe(true); // Disabled by default

    it('should check super admin IP whitelist when enabled', async () => {
      // Enable IP whitelisting
      SECURITY_CONFIG.SUPER_ADMIN_IP_WHITELIST_ENABLED = true;
      SECURITY_CONFIG.SUPER_ADMIN_ALLOWED_IPS = ['192.168.1.100'];
      
      const allowedIP = await securityManager.checkSuperAdminIpWhitelist('192.168.1.100');
      const deniedIP = await securityManager.checkSuperAdminIpWhitelist('192.168.1.1');
      
      expect(allowedIP).toBe(true);
      expect(deniedIP).toBe(false);
      
      // Reset for other tests
      SECURITY_CONFIG.SUPER_ADMIN_IP_WHITELIST_ENABLED = false;


  describe('Cleanup', () => {
    it('should clean up expired sessions and old events', async () => {
      await securityManager.cleanupSecurityData();
      
      expect(mockAdminUtils.createAuditLog).toHaveBeenCalledWith(
        expect.objectContaining({
          action: 'security.cleanup.sessions',
          user_id: 'system'
        })
      );


  describe('Error Handling', () => {
    it('should handle database errors gracefully', async () => {
      mockAdminUtils.getUserById.mockRejectedValue(new Error('Database error'));
      
      const isLocked = await securityManager.isAccountLocked('user-123');
      
      expect(isLocked).toBe(false); // Should default to false on error

    it('should handle missing user gracefully', async () => {
      mockAdminUtils.getUserById.mockResolvedValue(null);
      
      const isLocked = await securityManager.isAccountLocked('nonexistent-user');
      
      expect(isLocked).toBe(false);


