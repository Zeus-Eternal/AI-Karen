/**
 * MFA Manager Tests
 * 
 * Tests for TOTP-based MFA implementation, backup codes,
 * and MFA enforcement policies.
 */

import { MfaManager } from '../mfa-manager';
import { getAdminDatabaseUtils } from '@/lib/database/admin-utils';
import * as speakeasy from 'speakeasy';
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
};

const mockSpeakeasy = speakeasy as jest.Mocked<typeof speakeasy>;

(getAdminDatabaseUtils as jest.Mock).mockReturnValue(mockAdminUtils);

describe('MfaManager', () => {
  let mfaManager: MfaManager;
  
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
    mfaManager = new MfaManager();
    jest.clearAllMocks();
  });

  describe('MFA Setup', () => {
    it('should generate MFA setup data', async () => {
      mockSpeakeasy.generateSecret.mockReturnValue({
        base32: 'JBSWY3DPEHPK3PXP',
        otpauth_url: 'otpauth://totp/AI%20Karen%20Admin%20(test@example.com)?secret=JBSWY3DPEHPK3PXP&issuer=AI%20Karen'
      } as any);

      const setupData = await mfaManager.generateMfaSetup(mockUser);

      expect(setupData.secret).toBe('JBSWY3DPEHPK3PXP');
      expect(setupData.manualEntryKey).toBe('JBSWY3DPEHPK3PXP');
      expect(setupData.backupCodes).toHaveLength(10);
      expect(setupData.qrCodeUrl).toContain('data:image/png;base64');
      
      expect(mockSpeakeasy.generateSecret).toHaveBeenCalledWith({
        name: 'AI Karen Admin (test@example.com)',
        issuer: 'AI Karen',
        length: 32
      });
    });

    it('should enable MFA after successful verification', async () => {
      mockSpeakeasy.totp.verify.mockReturnValue(true);
      
      const success = await mfaManager.enableMfa(
        'user-123',
        'JBSWY3DPEHPK3PXP',
        '123456',
        ['BACKUP1', 'BACKUP2']
      );

      expect(success).toBe(true);
      expect(mockAdminUtils.updateUser).toHaveBeenCalledWith('user-123', {
        two_factor_enabled: true,
        two_factor_secret: 'JBSWY3DPEHPK3PXP'
      });
      expect(mockAdminUtils.createAuditLog).toHaveBeenCalledWith(
        expect.objectContaining({
          action: 'mfa.enabled',
          user_id: 'user-123'
        })
      );
    });

    it('should not enable MFA with invalid verification code', async () => {
      mockSpeakeasy.totp.verify.mockReturnValue(false);
      
      const success = await mfaManager.enableMfa(
        'user-123',
        'JBSWY3DPEHPK3PXP',
        'invalid',
        ['BACKUP1', 'BACKUP2']
      );

      expect(success).toBe(false);
      expect(mockAdminUtils.updateUser).not.toHaveBeenCalled();
    });

    it('should disable MFA', async () => {
      await mfaManager.disableMfa('user-123', 'admin-456');

      expect(mockAdminUtils.updateUser).toHaveBeenCalledWith('user-123', {
        two_factor_enabled: false,
        two_factor_secret: undefined
      });
      expect(mockAdminUtils.createAuditLog).toHaveBeenCalledWith(
        expect.objectContaining({
          action: 'mfa.disabled',
          user_id: 'admin-456'
        })
      );
    });
  });

  describe('MFA Verification', () => {
    const mfaEnabledUser: User = {
      ...mockUser,
      two_factor_enabled: true,
      two_factor_secret: 'JBSWY3DPEHPK3PXP',
      preferences: {
        mfa_backup_codes: ['BACKUP1', 'BACKUP2', 'BACKUP3']
      }
    };

    it('should verify valid TOTP code', async () => {
      mockAdminUtils.getUserById.mockResolvedValue(mfaEnabledUser);
      mockSpeakeasy.totp.verify.mockReturnValue(true);

      const result = await mfaManager.verifyMfaCode('user-123', '123456');

      expect(result.valid).toBe(true);
      expect(result.usedBackupCode).toBeUndefined();
      expect(mockAdminUtils.createAuditLog).toHaveBeenCalledWith(
        expect.objectContaining({
          action: 'mfa.verified',
          details: expect.objectContaining({
            method: 'totp'
          })
        })
      );
    });

    it('should verify valid backup code', async () => {
      mockAdminUtils.getUserById.mockResolvedValue(mfaEnabledUser);
      mockSpeakeasy.totp.verify.mockReturnValue(false); // TOTP fails

      const result = await mfaManager.verifyMfaCode('user-123', 'BACKUP1');

      expect(result.valid).toBe(true);
      expect(result.usedBackupCode).toBe(true);
      expect(result.remainingBackupCodes).toBe(2);
      expect(mockAdminUtils.createAuditLog).toHaveBeenCalledWith(
        expect.objectContaining({
          action: 'mfa.backup_code_used',
          details: expect.objectContaining({
            method: 'backup_code',
            remaining_codes: 2
          })
        })
      );
    });

    it('should reject invalid codes', async () => {
      mockAdminUtils.getUserById.mockResolvedValue(mfaEnabledUser);
      mockSpeakeasy.totp.verify.mockReturnValue(false);

      const result = await mfaManager.verifyMfaCode('user-123', 'INVALID');

      expect(result.valid).toBe(false);
      expect(mockAdminUtils.createAuditLog).toHaveBeenCalledWith(
        expect.objectContaining({
          action: 'mfa.verification_failed'
        })
      );
    });

    it('should handle user without MFA enabled', async () => {
      mockAdminUtils.getUserById.mockResolvedValue(mockUser);

      const result = await mfaManager.verifyMfaCode('user-123', '123456');

      expect(result.valid).toBe(false);
    });
  });

  describe('MFA Status', () => {
    it('should get MFA status for user without MFA', async () => {
      mockAdminUtils.getUserById.mockResolvedValue(mockUser);
      mockAdminUtils.getSystemConfig.mockResolvedValue({ value: 'false' });

      const status = await mfaManager.getMfaStatus('user-123');

      expect(status.enabled).toBe(false);
      expect(status.required).toBe(false);
      expect(status.setupComplete).toBe(false);
      expect(status.backupCodesRemaining).toBe(0);
    });

    it('should get MFA status for user with MFA enabled', async () => {
      const mfaUser = {
        ...mockUser,
        two_factor_enabled: true,
        two_factor_secret: 'SECRET',
        preferences: { mfa_backup_codes: ['CODE1', 'CODE2'] }
      };
      mockAdminUtils.getUserById.mockResolvedValue(mfaUser);
      mockAdminUtils.getSystemConfig.mockResolvedValue({ value: 'true' });

      const status = await mfaManager.getMfaStatus('user-123');

      expect(status.enabled).toBe(true);
      expect(status.required).toBe(true);
      expect(status.setupComplete).toBe(true);
      expect(status.backupCodesRemaining).toBe(2);
    });
  });

  describe('MFA Requirements', () => {
    it('should require MFA for super admin', async () => {
      const superAdmin = { ...mockUser, role: 'super_admin' as const };
      mockAdminUtils.getSystemConfig.mockResolvedValue({ value: 'true' });

      const required = await mfaManager.isMfaRequired(superAdmin);

      expect(required).toBe(true);
    });

    it('should require MFA for admin when configured', async () => {
      mockAdminUtils.getSystemConfig.mockResolvedValue({ value: true });

      const required = await mfaManager.isMfaRequired(mockUser);

      expect(required).toBe(true);
    });

    it('should not require MFA for regular user', async () => {
      const regularUser = { ...mockUser, role: 'user' as const };

      const required = await mfaManager.isMfaRequired(regularUser);

      expect(required).toBe(false);
    });

    it('should enforce MFA requirement during login', async () => {
      const adminWithoutMfa = { ...mockUser, two_factor_enabled: false };
      mockAdminUtils.getSystemConfig.mockResolvedValue({ value: 'true' });

      const enforcement = await mfaManager.enforceMfaRequirement(adminWithoutMfa);

      expect(enforcement.canProceed).toBe(false);
      expect(enforcement.requiresSetup).toBe(true);
      expect(enforcement.message).toContain('Multi-factor authentication is required');
    });

    it('should allow login when MFA is properly set up', async () => {
      const adminWithMfa = { ...mockUser, two_factor_enabled: true };
      mockAdminUtils.getSystemConfig.mockResolvedValue({ value: 'true' });

      const enforcement = await mfaManager.enforceMfaRequirement(adminWithMfa);

      expect(enforcement.canProceed).toBe(true);
      expect(enforcement.requiresSetup).toBe(false);
    });
  });

  describe('Backup Codes', () => {
    it('should regenerate backup codes', async () => {
      const newCodes = await mfaManager.regenerateBackupCodes('user-123', 'admin-456');

      expect(newCodes).toHaveLength(10);
      expect(newCodes.every(code => typeof code === 'string' && code.length === 8)).toBe(true);
      expect(mockAdminUtils.createAuditLog).toHaveBeenCalledWith(
        expect.objectContaining({
          action: 'mfa.backup_codes_regenerated',
          user_id: 'admin-456'
        })
      );
    });

    it('should consume backup codes when used', async () => {
      const userWithBackupCodes = {
        ...mockUser,
        two_factor_enabled: true,
        two_factor_secret: 'SECRET',
        preferences: { mfa_backup_codes: ['CODE1', 'CODE2', 'CODE3'] }
      };
      
      mockAdminUtils.getUserById.mockResolvedValue(userWithBackupCodes);
      mockSpeakeasy.totp.verify.mockReturnValue(false);

      // Use first backup code
      const result = await mfaManager.verifyMfaCode('user-123', 'CODE1');

      expect(result.valid).toBe(true);
      expect(result.remainingBackupCodes).toBe(2);
      
      // Verify the code was removed from preferences
      expect(mockAdminUtils.updateUser).toHaveBeenCalledWith('user-123', {
        preferences: { mfa_backup_codes: ['CODE2', 'CODE3'] }
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle database errors gracefully', async () => {
      mockAdminUtils.getUserById.mockRejectedValue(new Error('Database error'));

      const result = await mfaManager.verifyMfaCode('user-123', '123456');

      expect(result.valid).toBe(false);
    });

    it('should handle missing user', async () => {
      mockAdminUtils.getUserById.mockResolvedValue(null);

      const status = await mfaManager.getMfaStatus('nonexistent-user');

      expect(status.enabled).toBe(false);
      expect(status.required).toBe(false);
      expect(status.setupComplete).toBe(false);
    });
  });
});