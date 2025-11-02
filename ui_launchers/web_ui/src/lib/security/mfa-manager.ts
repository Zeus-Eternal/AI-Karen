/**
 * Multi-Factor Authentication (MFA) Manager
 * 
 * Implements TOTP-based MFA for admin accounts with QR code generation,
 * backup codes, and MFA enforcement policies.
 * 
 * Requirements: 5.4, 5.5, 5.6
 */

import * as speakeasy from 'speakeasy';
import * as QRCode from 'qrcode';
import { getAdminDatabaseUtils } from '@/lib/database/admin-utils';
import type { User } from '@/types/admin';

export interface MfaSetupData {
  secret: string;
  qrCodeUrl: string;
  backupCodes: string[];
  manualEntryKey: string;
}

export interface MfaVerificationResult {
  valid: boolean;
  usedBackupCode?: boolean;
  remainingBackupCodes?: number;
}

export interface MfaStatus {
  enabled: boolean;
  required: boolean;
  setupComplete: boolean;
  backupCodesRemaining: number;
  lastUsed?: Date;
}

export class MfaManager {
  private adminUtils = getAdminDatabaseUtils();
  private readonly APP_NAME = 'AI Karen Admin';
  private readonly ISSUER = 'AI Karen';

  /**
   * Generate MFA setup data for a user
   */
  async generateMfaSetup(user: User): Promise<MfaSetupData> {
    // Generate secret
    const secret = speakeasy.generateSecret({
      name: `${this.APP_NAME} (${user.email})`,
      issuer: this.ISSUER,
      length: 32

    // Generate QR code URL
    const qrCodeUrl = await QRCode.toDataURL(secret.otpauth_url!);

    // Generate backup codes
    const backupCodes = this.generateBackupCodes();

    return {
      secret: secret.base32,
      qrCodeUrl,
      backupCodes,
      manualEntryKey: secret.base32
    };
  }

  /**
   * Enable MFA for a user after verification
   */
  async enableMfa(userId: string, secret: string, verificationCode: string, backupCodes: string[]): Promise<boolean> {
    // Verify the code first
    const isValid = this.verifyTotpCode(secret, verificationCode);
    
    if (!isValid) {
      return false;
    }

    // Store MFA data in user record
    await this.adminUtils.updateUser(userId, {
      two_factor_enabled: true,
      two_factor_secret: secret

    // Store backup codes securely (in production, encrypt these)
    await this.storeBackupCodes(userId, backupCodes);

    // Log MFA enablement
    await this.adminUtils.createAuditLog({
      user_id: userId,
      action: 'mfa.enabled',
      resource_type: 'user_security',
      resource_id: userId,
      details: {
        method: 'totp',
        backup_codes_generated: backupCodes.length,
        enabled_at: new Date().toISOString()
      }

    return true;
  }

  /**
   * Disable MFA for a user
   */
  async disableMfa(userId: string, adminUserId: string): Promise<void> {
    await this.adminUtils.updateUser(userId, {
      two_factor_enabled: false,
      two_factor_secret: undefined

    // Remove backup codes
    await this.removeBackupCodes(userId);

    // Log MFA disablement
    await this.adminUtils.createAuditLog({
      user_id: adminUserId,
      action: 'mfa.disabled',
      resource_type: 'user_security',
      resource_id: userId,
      details: {
        disabled_by: adminUserId,
        disabled_at: new Date().toISOString(),
        reason: 'admin_action'
      }

  }

  /**
   * Verify TOTP code or backup code
   */
  async verifyMfaCode(userId: string, code: string): Promise<MfaVerificationResult> {
    const user = await this.adminUtils.getUserWithRole(userId);
    
    if (!user || !user.two_factor_enabled || !user.two_factor_secret) {
      return { valid: false };
    }

    // First try TOTP verification
    const totpValid = this.verifyTotpCode(user.two_factor_secret, code);
    
    if (totpValid) {
      // Log successful MFA verification
      await this.adminUtils.createAuditLog({
        user_id: userId,
        action: 'mfa.verified',
        resource_type: 'user_authentication',
        resource_id: userId,
        details: {
          method: 'totp',
          verified_at: new Date().toISOString()
        }

      return { valid: true };
    }

    // Try backup code verification
    const backupResult = await this.verifyBackupCode(userId, code);
    
    if (backupResult.valid) {
      // Log backup code usage
      await this.adminUtils.createAuditLog({
        user_id: userId,
        action: 'mfa.backup_code_used',
        resource_type: 'user_authentication',
        resource_id: userId,
        details: {
          method: 'backup_code',
          remaining_codes: backupResult.remainingBackupCodes,
          used_at: new Date().toISOString()
        }

      return {
        valid: true,
        usedBackupCode: true,
        remainingBackupCodes: backupResult.remainingBackupCodes
      };
    }

    // Log failed MFA verification
    await this.adminUtils.createAuditLog({
      user_id: userId,
      action: 'mfa.verification_failed',
      resource_type: 'user_authentication',
      resource_id: userId,
      details: {
        failed_at: new Date().toISOString(),
        code_length: code.length
      }

    return { valid: false };
  }

  /**
   * Get MFA status for a user
   */
  async getMfaStatus(userId: string): Promise<MfaStatus> {
    const user = await this.adminUtils.getUserWithRole(userId);
    
    if (!user) {
      return {
        enabled: false,
        required: false,
        setupComplete: false,
        backupCodesRemaining: 0
      };
    }

    const required = await this.isMfaRequired(user);
    const backupCodes = await this.getBackupCodes(userId);

    return {
      enabled: user.two_factor_enabled,
      required,
      setupComplete: user.two_factor_enabled && !!user.two_factor_secret,
      backupCodesRemaining: backupCodes.length,
      lastUsed: user.last_login_at
    };
  }

  /**
   * Generate new backup codes for a user
   */
  async regenerateBackupCodes(userId: string, adminUserId: string): Promise<string[]> {
    const newBackupCodes = this.generateBackupCodes();
    
    await this.storeBackupCodes(userId, newBackupCodes);

    // Log backup code regeneration
    await this.adminUtils.createAuditLog({
      user_id: adminUserId,
      action: 'mfa.backup_codes_regenerated',
      resource_type: 'user_security',
      resource_id: userId,
      details: {
        regenerated_by: adminUserId,
        new_codes_count: newBackupCodes.length,
        regenerated_at: new Date().toISOString()
      }

    return newBackupCodes;
  }

  /**
   * Check if MFA is required for a user based on role and system policy
   */
  async isMfaRequired(user: User): Promise<boolean> {
    // Always require MFA for super admins and admins
    if (user.role === 'super_admin' || user.role === 'admin') {
      const mfaConfigs = await this.adminUtils.getSystemConfig('mfa_required_for_admins');
      const mfaConfig = mfaConfigs.find(config => config.key === 'mfa_required_for_admins');
      return mfaConfig?.value === 'true' || mfaConfig?.value === true;
    }
    
    return false;
  }

  /**
   * Enforce MFA requirement during login
   */
  async enforceMfaRequirement(user: User): Promise<{ canProceed: boolean; requiresSetup: boolean; message?: string }> {
    const required = await this.isMfaRequired(user);
    
    if (!required) {
      return { canProceed: true, requiresSetup: false };
    }

    if (!user.two_factor_enabled) {
      return {
        canProceed: false,
        requiresSetup: true,
        message: 'Multi-factor authentication is required for admin accounts. Please set up MFA to continue.'
      };
    }

    return { canProceed: true, requiresSetup: false };
  }

  /**
   * Verify TOTP code using speakeasy
   */
  private verifyTotpCode(secret: string, code: string): boolean {
    return speakeasy.totp.verify({
      secret,
      encoding: 'base32',
      token: code,
      window: 2 // Allow 2 time steps (60 seconds) of drift

  }

  /**
   * Generate backup codes
   */
  private generateBackupCodes(count: number = 10): string[] {
    const codes: string[] = [];
    
    for (let i = 0; i < count; i++) {
      // Generate 8-character alphanumeric code
      const code = Math.random().toString(36).substring(2, 10).toUpperCase();
      codes.push(code);
    }
    
    return codes;
  }

  /**
   * Store backup codes securely (in production, encrypt these)
   */
  private async storeBackupCodes(userId: string, codes: string[]): Promise<void> {
    // In a real implementation, these should be encrypted
    // For now, we'll store them in the user's preferences
    const user = await this.adminUtils.getUserWithRole(userId);
    if (user) {
      const preferences = user.preferences || {};
      preferences.mfa_backup_codes = codes;
      
      await this.adminUtils.updateUser(userId, { preferences });
    }
  }

  /**
   * Get backup codes for a user
   */
  private async getBackupCodes(userId: string): Promise<string[]> {
    const user = await this.adminUtils.getUserWithRole(userId);
    return user?.preferences?.mfa_backup_codes || [];
  }

  /**
   * Remove backup codes for a user
   */
  private async removeBackupCodes(userId: string): Promise<void> {
    const user = await this.adminUtils.getUserWithRole(userId);
    if (user) {
      const preferences = user.preferences || {};
      delete preferences.mfa_backup_codes;
      
      await this.adminUtils.updateUser(userId, { preferences });
    }
  }

  /**
   * Verify and consume a backup code
   */
  private async verifyBackupCode(userId: string, code: string): Promise<{ valid: boolean; remainingBackupCodes?: number }> {
    const backupCodes = await this.getBackupCodes(userId);
    const codeIndex = backupCodes.indexOf(code.toUpperCase());
    
    if (codeIndex === -1) {
      return { valid: false };
    }

    // Remove the used backup code
    backupCodes.splice(codeIndex, 1);
    await this.storeBackupCodes(userId, backupCodes);

    return {
      valid: true,
      remainingBackupCodes: backupCodes.length
    };
  }
}

// Export singleton instance
export const mfaManager = new MfaManager();