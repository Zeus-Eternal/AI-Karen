/**
 * Enhanced Authentication Middleware Tests
 * 
 * Tests for integrated security features including progressive delays,
 * MFA enforcement, session management, and IP security.
 */

import { NextRequest } from 'next/server';
import { EnhancedAuthMiddleware } from '../enhanced-auth-middleware';
import { securityManager } from '../security-manager';
import { mfaManager } from '../mfa-manager';
import { sessionTimeoutManager } from '../session-timeout-manager';
import { ipSecurityManager } from '../ip-security-manager';
import { getAdminDatabaseUtils } from '@/lib/database/admin-utils';
import type { User } from '@/types/admin';

// Mock dependencies
jest.mock('../security-manager');
jest.mock('../mfa-manager');
jest.mock('../session-timeout-manager');
jest.mock('../ip-security-manager');
jest.mock('@/lib/database/admin-utils');

const mockSecurityManager = securityManager as jest.Mocked<typeof securityManager>;
const mockMfaManager = mfaManager as jest.Mocked<typeof mfaManager>;
const mockSessionManager = sessionTimeoutManager as jest.Mocked<typeof sessionTimeoutManager>;
const mockIpManager = ipSecurityManager as jest.Mocked<typeof ipSecurityManager>;

const mockAdminUtils = {
  getUserById: jest.fn(),
  updateUser: jest.fn(),
  createAuditLog: jest.fn(),
  getUsers: jest.fn(),
};

(getAdminDatabaseUtils as jest.Mock).mockReturnValue(mockAdminUtils);

describe('EnhancedAuthMiddleware', () => {
  let authMiddleware: EnhancedAuthMiddleware;
  
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
    two_factor_enabled: true,
    locked_until: undefined,
  };

  beforeEach(() => {
    authMiddleware = new EnhancedAuthMiddleware();
    jest.clearAllMocks();

  describe('User Authentication', () => {
    it('should authenticate user successfully with all security checks', async () => {
      // Setup mocks for successful authentication
      mockAdminUtils.getUsers.mockResolvedValue({ data: [mockUser] });
      mockSecurityManager.isAccountLocked.mockResolvedValue(false);
      mockIpManager.checkIpAccess.mockResolvedValue({ allowed: true });
      mockMfaManager.enforceMfaRequirement.mockResolvedValue({ canProceed: true, requiresSetup: false });
      mockMfaManager.verifyMfaCode.mockResolvedValue({ valid: true });
      mockSecurityManager.checkConcurrentSessionLimit.mockResolvedValue(true);
      mockSessionManager.createSession.mockResolvedValue({
        session_token: 'session-123',
        user_id: 'user-123',
        user_email: 'test@example.com',
        user_role: 'admin',
        created_at: new Date(),
        last_accessed: new Date(),
        expires_at: new Date(Date.now() + 30 * 60 * 1000),
        is_active: true

      const result = await authMiddleware.authenticateUser(
        'test@example.com',
        'password123',
        '123456',
        '192.168.1.1',
        'test-agent'
      );

      expect(result.success).toBe(true);
      expect(result.user).toEqual(mockUser);
      expect(result.sessionToken).toBe('session-123');
      expect(result.mfaRequired).toBe(false);

      // Verify security checks were called
      expect(mockSecurityManager.isAccountLocked).toHaveBeenCalledWith('user-123');
      expect(mockIpManager.checkIpAccess).toHaveBeenCalledWith('192.168.1.1', mockUser);
      expect(mockMfaManager.verifyMfaCode).toHaveBeenCalledWith('user-123', '123456');
      expect(mockSecurityManager.clearFailedAttempts).toHaveBeenCalledWith('test@example.com', '192.168.1.1');

    it('should reject authentication for locked account', async () => {
      mockAdminUtils.getUsers.mockResolvedValue({ data: [mockUser] });
      mockSecurityManager.isAccountLocked.mockResolvedValue(true);

      const result = await authMiddleware.authenticateUser(
        'test@example.com',
        'password123',
        undefined,
        '192.168.1.1'
      );

      expect(result.success).toBe(false);
      expect(result.error?.code).toBe('ACCOUNT_LOCKED');
      expect(mockSecurityManager.recordFailedLogin).toHaveBeenCalled();

    it('should reject authentication for blocked IP', async () => {
      mockAdminUtils.getUsers.mockResolvedValue({ data: [mockUser] });
      mockSecurityManager.isAccountLocked.mockResolvedValue(false);
      mockIpManager.checkIpAccess.mockResolvedValue({ 
        allowed: false, 
        reason: 'IP not whitelisted' 

      const result = await authMiddleware.authenticateUser(
        'test@example.com',
        'password123',
        undefined,
        '192.168.1.1'
      );

      expect(result.success).toBe(false);
      expect(result.error?.code).toBe('IP_ACCESS_DENIED');
      expect(result.error?.message).toBe('IP not whitelisted');

    it('should apply progressive delay for invalid credentials', async () => {
      mockAdminUtils.getUsers.mockResolvedValue({ data: [] }); // No user found
      mockSecurityManager.recordFailedLogin.mockResolvedValue(5); // 5 second delay

      const result = await authMiddleware.authenticateUser(
        'invalid@example.com',
        'wrongpassword',
        undefined,
        '192.168.1.1'
      );

      expect(result.success).toBe(false);
      expect(result.delay).toBe(5);
      expect(result.error?.code).toBe('INVALID_CREDENTIALS');
      expect(mockSecurityManager.recordFailedLogin).toHaveBeenCalled();
      expect(mockIpManager.recordFailedAttempt).toHaveBeenCalled();

    it('should require MFA setup for admin without MFA', async () => {
      const userWithoutMfa = { ...mockUser, two_factor_enabled: false };
      mockAdminUtils.getUsers.mockResolvedValue({ data: [userWithoutMfa] });
      mockSecurityManager.isAccountLocked.mockResolvedValue(false);
      mockIpManager.checkIpAccess.mockResolvedValue({ allowed: true });
      mockMfaManager.enforceMfaRequirement.mockResolvedValue({
        canProceed: false,
        requiresSetup: true,
        message: 'MFA setup required'

      const result = await authMiddleware.authenticateUser(
        'test@example.com',
        'password123',
        undefined,
        '192.168.1.1'
      );

      expect(result.success).toBe(false);
      expect(result.mfaRequired).toBe(true);
      expect(result.error?.code).toBe('MFA_SETUP_REQUIRED');

    it('should require TOTP code when MFA is enabled', async () => {
      mockAdminUtils.getUsers.mockResolvedValue({ data: [mockUser] });
      mockSecurityManager.isAccountLocked.mockResolvedValue(false);
      mockIpManager.checkIpAccess.mockResolvedValue({ allowed: true });
      mockMfaManager.enforceMfaRequirement.mockResolvedValue({ canProceed: true, requiresSetup: false });

      const result = await authMiddleware.authenticateUser(
        'test@example.com',
        'password123',
        undefined, // No TOTP code provided
        '192.168.1.1'
      );

      expect(result.success).toBe(false);
      expect(result.mfaRequired).toBe(true);
      expect(result.error?.code).toBe('MFA_CODE_REQUIRED');

    it('should reject invalid MFA code', async () => {
      mockAdminUtils.getUsers.mockResolvedValue({ data: [mockUser] });
      mockSecurityManager.isAccountLocked.mockResolvedValue(false);
      mockIpManager.checkIpAccess.mockResolvedValue({ allowed: true });
      mockMfaManager.enforceMfaRequirement.mockResolvedValue({ canProceed: true, requiresSetup: false });
      mockMfaManager.verifyMfaCode.mockResolvedValue({ valid: false });

      const result = await authMiddleware.authenticateUser(
        'test@example.com',
        'password123',
        'invalid-code',
        '192.168.1.1'
      );

      expect(result.success).toBe(false);
      expect(result.error?.code).toBe('INVALID_MFA_CODE');
      expect(mockSecurityManager.recordFailedLogin).toHaveBeenCalled();

    it('should reject when session limit exceeded', async () => {
      mockAdminUtils.getUsers.mockResolvedValue({ data: [mockUser] });
      mockSecurityManager.isAccountLocked.mockResolvedValue(false);
      mockIpManager.checkIpAccess.mockResolvedValue({ allowed: true });
      mockMfaManager.enforceMfaRequirement.mockResolvedValue({ canProceed: true, requiresSetup: false });
      mockMfaManager.verifyMfaCode.mockResolvedValue({ valid: true });
      mockSecurityManager.checkConcurrentSessionLimit.mockResolvedValue(false);

      const result = await authMiddleware.authenticateUser(
        'test@example.com',
        'password123',
        '123456',
        '192.168.1.1'
      );

      expect(result.success).toBe(false);
      expect(result.error?.code).toBe('SESSION_LIMIT_EXCEEDED');


  describe('Session Validation', () => {
    it('should validate session successfully', async () => {
      const mockSessionStatus = {
        isValid: true,
        expiresAt: new Date(Date.now() + 30 * 60 * 1000),
        timeRemaining: 1800,
        warningActive: false,
        extensionsUsed: 0,
        maxExtensions: 3
      };

      const mockSession = {
        session_token: 'session-123',
        user_id: 'user-123',
        user_email: 'test@example.com',
        user_role: 'admin',
        ip_address: '192.168.1.1',
        user_agent: 'test-agent',
        created_at: new Date(),
        last_accessed: new Date(),
        expires_at: new Date(Date.now() + 30 * 60 * 1000),
        is_active: true,
        extensionsUsed: 0
      };

      mockSessionManager.getSessionStatus.mockReturnValue(mockSessionStatus);
      mockSessionManager.updateSessionActivity.mockResolvedValue(true);
      mockSessionManager.getUserSessions.mockReturnValue([mockSession]);
      mockAdminUtils.getUserById.mockResolvedValue(mockUser);
      mockMfaManager.isMfaRequired.mockResolvedValue(true);

      const context = await authMiddleware.validateSession('session-123', '192.168.1.1');

      expect(context).toBeDefined();
      expect(context!.user).toEqual(mockUser);
      expect(context!.sessionToken).toBe('session-123');
      expect(context!.ipAddress).toBe('192.168.1.1');
      expect(context!.mfaRequired).toBe(true);
      expect(context!.mfaVerified).toBe(true);

    it('should return null for invalid session', async () => {
      mockSessionManager.getSessionStatus.mockReturnValue(null);

      const context = await authMiddleware.validateSession('invalid-session');

      expect(context).toBeNull();

    it('should return null for expired session', async () => {
      mockSessionManager.getSessionStatus.mockReturnValue({
        isValid: false,
        expiresAt: new Date(Date.now() - 1000),
        timeRemaining: 0,
        warningActive: false,
        extensionsUsed: 0,
        maxExtensions: 3

      const context = await authMiddleware.validateSession('expired-session');

      expect(context).toBeNull();

    it('should log IP mismatch but continue validation', async () => {
      const mockSessionStatus = {
        isValid: true,
        expiresAt: new Date(Date.now() + 30 * 60 * 1000),
        timeRemaining: 1800,
        warningActive: false,
        extensionsUsed: 0,
        maxExtensions: 3
      };

      const mockSession = {
        session_token: 'session-123',
        user_id: 'user-123',
        user_email: 'test@example.com',
        user_role: 'admin',
        ip_address: '192.168.1.1', // Original IP
        user_agent: 'test-agent',
        created_at: new Date(),
        last_accessed: new Date(),
        expires_at: new Date(Date.now() + 30 * 60 * 1000),
        is_active: true,
        extensionsUsed: 0
      };

      mockSessionManager.getSessionStatus.mockReturnValue(mockSessionStatus);
      mockSessionManager.updateSessionActivity.mockResolvedValue(true);
      mockSessionManager.getUserSessions.mockReturnValue([mockSession]);
      mockAdminUtils.getUserById.mockResolvedValue(mockUser);
      mockMfaManager.isMfaRequired.mockResolvedValue(false);

      const context = await authMiddleware.validateSession('session-123', '192.168.1.2'); // Different IP

      expect(context).toBeDefined();
      expect(mockAdminUtils.createAuditLog).toHaveBeenCalledWith(
        expect.objectContaining({
          action: 'security.ip_mismatch'
        })
      );


  describe('Enhanced Logout', () => {
    it('should logout successfully with security cleanup', async () => {
      await authMiddleware.logout('session-123', 'user-123');

      expect(mockSessionManager.terminateSession).toHaveBeenCalledWith('session-123', 'user_logout');
      expect(mockAdminUtils.createAuditLog).toHaveBeenCalledWith(
        expect.objectContaining({
          action: 'auth.logout',
          user_id: 'user-123'
        })
      );


  describe('Middleware Wrapper', () => {
    const createMockRequest = (sessionToken?: string, ip?: string): NextRequest => {
      const headers = new Headers();
      if (sessionToken) {
        headers.set('authorization', `Bearer ${sessionToken}`);
      }
      if (ip) {
        headers.set('x-forwarded-for', ip);
      }
      headers.set('user-agent', 'test-agent');

      return new NextRequest('http://localhost/api/test', { headers });
    };

    const mockHandler = jest.fn().mockResolvedValue(new Response('OK'));

    it('should allow access with valid session and role', async () => {
      const request = createMockRequest('session-123', '192.168.1.1');
      
      const mockContext = {
        user: mockUser,
        sessionToken: 'session-123',
        ipAddress: '192.168.1.1',
        userAgent: 'test-agent',
        mfaRequired: false,
        mfaVerified: true,
        sessionStatus: {
          isValid: true,
          expiresAt: new Date(),
          timeRemaining: 1800,
          warningActive: false
        }
      };

      jest.spyOn(authMiddleware, 'validateSession').mockResolvedValue(mockContext);

      const response = await authMiddleware.withEnhancedAuth(
        request,
        mockHandler,
        { requiredRole: 'admin' }
      );

      expect(mockHandler).toHaveBeenCalledWith(request, mockContext);

    it('should reject access without session token', async () => {
      const request = createMockRequest(); // No session token

      const response = await authMiddleware.withEnhancedAuth(request, mockHandler);

      expect(response.status).toBe(401);
      expect(mockHandler).not.toHaveBeenCalled();

    it('should reject access with invalid session', async () => {
      const request = createMockRequest('invalid-session');
      
      jest.spyOn(authMiddleware, 'validateSession').mockResolvedValue(null);

      const response = await authMiddleware.withEnhancedAuth(request, mockHandler);

      expect(response.status).toBe(401);
      expect(mockHandler).not.toHaveBeenCalled();

    it('should reject access with insufficient role', async () => {
      const request = createMockRequest('session-123');
      
      const mockContext = {
        user: { ...mockUser, role: 'user' as const },
        sessionToken: 'session-123',
        ipAddress: '192.168.1.1',
        userAgent: 'test-agent',
        mfaRequired: false,
        mfaVerified: false,
        sessionStatus: {
          isValid: true,
          expiresAt: new Date(),
          timeRemaining: 1800,
          warningActive: false
        }
      };

      jest.spyOn(authMiddleware, 'validateSession').mockResolvedValue(mockContext);

      const response = await authMiddleware.withEnhancedAuth(
        request,
        mockHandler,
        { requiredRole: 'admin' }
      );

      expect(response.status).toBe(403);
      expect(mockHandler).not.toHaveBeenCalled();

    it('should reject access when MFA required but not verified', async () => {
      const request = createMockRequest('session-123');
      
      const mockContext = {
        user: mockUser,
        sessionToken: 'session-123',
        ipAddress: '192.168.1.1',
        userAgent: 'test-agent',
        mfaRequired: true,
        mfaVerified: false,
        sessionStatus: {
          isValid: true,
          expiresAt: new Date(),
          timeRemaining: 1800,
          warningActive: false
        }
      };

      jest.spyOn(authMiddleware, 'validateSession').mockResolvedValue(mockContext);

      const response = await authMiddleware.withEnhancedAuth(
        request,
        mockHandler,
        { requireMfa: true }
      );

      expect(response.status).toBe(403);
      expect(mockHandler).not.toHaveBeenCalled();

    it('should reject access when IP not whitelisted', async () => {
      const request = createMockRequest('session-123', '192.168.1.1');
      
      const mockContext = {
        user: mockUser,
        sessionToken: 'session-123',
        ipAddress: '192.168.1.1',
        userAgent: 'test-agent',
        mfaRequired: false,
        mfaVerified: true,
        sessionStatus: {
          isValid: true,
          expiresAt: new Date(),
          timeRemaining: 1800,
          warningActive: false
        }
      };

      jest.spyOn(authMiddleware, 'validateSession').mockResolvedValue(mockContext);
      mockIpManager.checkIpAccess.mockResolvedValue({ 
        allowed: false, 
        reason: 'IP not whitelisted' 

      const response = await authMiddleware.withEnhancedAuth(
        request,
        mockHandler,
        { checkIpWhitelist: true }
      );

      expect(response.status).toBe(403);
      expect(mockHandler).not.toHaveBeenCalled();


  describe('Error Handling', () => {
    it('should handle authentication errors gracefully', async () => {
      mockAdminUtils.getUsers.mockRejectedValue(new Error('Database error'));

      const result = await authMiddleware.authenticateUser(
        'test@example.com',
        'password123'
      );

      expect(result.success).toBe(false);
      expect(result.error?.code).toBe('AUTHENTICATION_ERROR');

    it('should handle session validation errors gracefully', async () => {
      mockSessionManager.getSessionStatus.mockImplementation(() => {
        throw new Error('Session error');

      const context = await authMiddleware.validateSession('session-123');

      expect(context).toBeNull();


