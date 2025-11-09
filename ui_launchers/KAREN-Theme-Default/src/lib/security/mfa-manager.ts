/**
 * Multi-Factor Authentication (MFA) Manager
 *
 * Implements TOTP-based MFA for admin accounts with QR code generation,
 * backup codes (securely hashed), and MFA enforcement policies.
 *
 * Requirements: 5.4, 5.5, 5.6
 */

import * as speakeasy from 'speakeasy';
import * as QRCode from 'qrcode';
import { getAdminDatabaseUtils } from '@/lib/database/admin-utils';
import type { User } from '@/types/admin';

export interface MfaSetupData {
  secret: string;          // base32 secret (display once)
  qrCodeUrl: string;       // data URL for enrollment
  backupCodes: string[];   // plaintext codes (display once)
  manualEntryKey: string;  // same as secret (for manual entry)
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

/* ------------------------------------------------------------------ */
/* Utilities: crypto-safe ID & hashing (browser + node compatible)    */
/* ------------------------------------------------------------------ */

async function sha256Hex(input: string): Promise<string> {
  // Browser WebCrypto with proper type checking
  if (typeof globalThis !== 'undefined' &&
      globalThis.crypto &&
      typeof globalThis.crypto.subtle !== 'undefined') {
    try {
      const enc = new TextEncoder().encode(input);
      const buf = await globalThis.crypto.subtle.digest('SHA-256', enc);
      return Array.from(new Uint8Array(buf))
        .map((b) => b.toString(16).padStart(2, '0'))
        .join('');
    } catch (err) {
      console.warn('[MFA] Browser crypto.subtle failed, falling back to Node:', err);
    }
  }

  // Node fallback
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const nodeCrypto = require('crypto');
    return nodeCrypto.createHash('sha256').update(input, 'utf8').digest('hex');
  } catch (err) {
    console.error('[MFA] Node crypto failed, using weak fallback:', err);
    // Last resort (not ideal, but prevents crash)
    let hash = 0;
    for (let i = 0; i < input.length; i++) {
      hash = (hash << 5) - hash + input.charCodeAt(i);
      hash |= 0;
    }
    return `fallback_${Math.abs(hash)}`;
  }
}

function randomBytesHex(len: number): string {
  // Browser crypto with proper type checking
  if (typeof globalThis !== 'undefined' &&
      globalThis.crypto &&
      typeof globalThis.crypto.getRandomValues === 'function') {
    try {
      const arr = new Uint8Array(len);
      globalThis.crypto.getRandomValues(arr);
      return Array.from(arr)
        .map((b) => b.toString(16).padStart(2, '0'))
        .join('')
        .slice(0, len * 2);
    } catch (err) {
      console.warn('[MFA] Browser crypto.getRandomValues failed, falling back to Node:', err);
    }
  }

  // Node fallback
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const nodeCrypto = require('crypto');
    return nodeCrypto.randomBytes(len).toString('hex');
  } catch (err) {
    console.error('[MFA] Node crypto failed, using weak fallback for random bytes:', err);
    // Weak fallback
    return Array.from({ length: len }, () =>
      Math.floor(Math.random() * 256).toString(16).padStart(2, '0')
    ).join('');
  }
}

/* ------------------------------------------------------------------ */

export class MfaManager {
  private _adminUtils: ReturnType<typeof getAdminDatabaseUtils> | null = null;
  private readonly APP_NAME = 'AI Karen Admin';
  private readonly ISSUER = 'AI Karen';

  private get adminUtils() {
    if (!this._adminUtils) {
      this._adminUtils = getAdminDatabaseUtils();
    }
    return this._adminUtils;
  }

  /**
   * Generate MFA setup data for a user
   * - Returns base32 secret + QR code + plaintext backup codes (display once)
   * - DOES NOT persist until `enableMfa` is called
   */
  async generateMfaSetup(user: User): Promise<MfaSetupData> {
    const secret = speakeasy.generateSecret({
      name: `${this.APP_NAME} (${user.email})`,
      issuer: this.ISSUER,
      length: 32,
    });

    const otpauth = secret.otpauth_url!;
    const qrCodeUrl = await QRCode.toDataURL(otpauth);
    const backupCodes = this.generateBackupCodes();

    return {
      secret: secret.base32,
      qrCodeUrl,
      backupCodes,
      manualEntryKey: secret.base32,
    };
  }

  /**
   * Enable MFA for a user after verifying a TOTP code.
   * - Persists the secret and hashed backup codes.
   */
  async enableMfa(
    userId: string,
    secretBase32: string,
    verificationCode: string,
    backupCodesPlain: string[]
  ): Promise<boolean> {
    const isValid = this.verifyTotpCode(secretBase32, verificationCode);
    if (!isValid) return false;

    // Hash backup codes before storing
    const hashed = await Promise.all(
      backupCodesPlain.map((c) => sha256Hex(c.toUpperCase()))
    );

    await this.adminUtils.updateUser(userId, {
      two_factor_enabled: true,
      two_factor_secret: secretBase32,
      // Store hashed backup codes in preferences (server should encrypt at rest)
      preferences: {
        ...(await this.adminUtils.getUserWithRole(userId))?.preferences,
        mfa_backup_codes_hashed: hashed,
      },
    });

    await this.adminUtils.createAuditLog({
      user_id: userId,
      action: 'mfa.enabled',
      resource_type: 'user_security',
      resource_id: userId,
      details: {
        method: 'totp',
        backup_codes_generated: backupCodesPlain.length,
        enabled_at: new Date().toISOString(),
      },
    });

    return true;
  }

  /**
   * Disable MFA (admin action)
   * - Clears secret + backup codes.
   */
  async disableMfa(userId: string, adminUserId: string): Promise<void> {
    const user = await this.adminUtils.getUserWithRole(userId);
    const prefs = { ...(user?.preferences || {}) };
    delete (prefs as any).mfa_backup_codes_hashed;
    delete (prefs as any).mfa_backup_codes; // backward-compat cleanup

    await this.adminUtils.updateUser(userId, {
      two_factor_enabled: false,
      two_factor_secret: null,
      preferences: prefs,
    });

    await this.adminUtils.createAuditLog({
      user_id: adminUserId,
      action: 'mfa.disabled',
      resource_type: 'user_security',
      resource_id: userId,
      details: {
        disabled_by: adminUserId,
        disabled_at: new Date().toISOString(),
        reason: 'admin_action',
      },
    });
  }

  /**
   * Verify TOTP or backup code (consumes backup code if used)
   */
  async verifyMfaCode(userId: string, code: string): Promise<MfaVerificationResult> {
    const user = await this.adminUtils.getUserWithRole(userId);
    if (!user || !user.two_factor_enabled || !user.two_factor_secret) {
      return { valid: false };
    }

    // TOTP first
    const totpValid = this.verifyTotpCode(user.two_factor_secret, code);
    if (totpValid) {
      await this.adminUtils.createAuditLog({
        user_id: userId,
        action: 'mfa.verified',
        resource_type: 'user_authentication',
        resource_id: userId,
        details: { method: 'totp', verified_at: new Date().toISOString() },
      });
      return { valid: true };
    }

    // Backup code (hashed compare)
    const backupResult = await this.verifyBackupCode(userId, code);
    if (backupResult.valid) {
      await this.adminUtils.createAuditLog({
        user_id: userId,
        action: 'mfa.backup_code_used',
        resource_type: 'user_authentication',
        resource_id: userId,
        details: {
          method: 'backup_code',
          remaining_codes: backupResult.remainingBackupCodes,
          used_at: new Date().toISOString(),
        },
      });

      return {
        valid: true,
        usedBackupCode: true,
        remainingBackupCodes: backupResult.remainingBackupCodes,
      };
    }

    await this.adminUtils.createAuditLog({
      user_id: userId,
      action: 'mfa.verification_failed',
      resource_type: 'user_authentication',
      resource_id: userId,
      details: {
        failed_at: new Date().toISOString(),
        code_length: code?.length ?? 0,
      },
    });

    return { valid: false };
  }

  /**
   * Current MFA status for a user
   */
  async getMfaStatus(userId: string): Promise<MfaStatus> {
    const user = await this.adminUtils.getUserWithRole(userId);
    if (!user) {
      return {
        enabled: false,
        required: false,
        setupComplete: false,
        backupCodesRemaining: 0,
      };
    }

    const required = await this.isMfaRequired(user);
    const remaining = await this.getBackupCodesCount(userId);

    return {
      enabled: !!user.two_factor_enabled,
      required,
      setupComplete: !!user.two_factor_enabled && !!user.two_factor_secret,
      backupCodesRemaining: remaining,
      lastUsed: user.last_login_at,
    };
  }

  /**
   * Generate & persist new backup codes (hashed).
   * Returns plaintext codes for display once.
   */
  async regenerateBackupCodes(userId: string, adminUserId: string): Promise<string[]> {
    const newCodes = this.generateBackupCodes();
    const hashed = await Promise.all(newCodes.map((c) => sha256Hex(c.toUpperCase())));
    const user = await this.adminUtils.getUserWithRole(userId);

    await this.adminUtils.updateUser(userId, {
      preferences: {
        ...(user?.preferences || {}),
        mfa_backup_codes_hashed: hashed,
      },
    });

    await this.adminUtils.createAuditLog({
      user_id: adminUserId,
      action: 'mfa.backup_codes_regenerated',
      resource_type: 'user_security',
      resource_id: userId,
      details: {
        regenerated_by: adminUserId,
        new_codes_count: newCodes.length,
        regenerated_at: new Date().toISOString(),
      },
    });

    return newCodes;
  }

  /**
   * MFA policy: required for admins/super_admins if system config says so
   */
  async isMfaRequired(user: User): Promise<boolean> {
    if (user.role === 'super_admin' || user.role === 'admin') {
      // Use consistent API (pull all configs, then find)
      const configs = await this.adminUtils.getSystemConfig();
      const cfg = configs.find((c: any) => c.key === 'mfa_required_for_admins');
      return cfg?.value === 'true' || cfg?.value === true;
    }
    return false;
  }

  /**
   * Enforce MFA requirement during login
   */
  async enforceMfaRequirement(
    user: User
  ): Promise<{ canProceed: boolean; requiresSetup: boolean; message?: string }> {
    const required = await this.isMfaRequired(user);
    if (!required) return { canProceed: true, requiresSetup: false };

    if (!user.two_factor_enabled) {
      return {
        canProceed: false,
        requiresSetup: true,
        message:
          'Multi-factor authentication is required for admin accounts. Please set up MFA to continue.',
      };
    }
    return { canProceed: true, requiresSetup: false };
  }

  /**
   * Verify TOTP code using speakeasy
   */
  private verifyTotpCode(secretBase32: string, code: string): boolean {
    return speakeasy.totp.verify({
      secret: secretBase32,
      encoding: 'base32',
      token: code,
      window: 2, // allow ±1 step (approx 60s drift)
    });
  }

  /**
   * Generate cryptographically-strong backup codes (default 10)
   * Format: 4-4-4 alnum (uppercase) for usability, e.g., "9K3D-1TQZ-7MHF"
   */
  private generateBackupCodes(count: number = 10): string[] {
    const codes: string[] = [];
    for (let i = 0; i < count; i++) {
      // 12 nibbles (~48 bits) -> mapped to base36 then chunked
      const hex = randomBytesHex(8); // 64 bits, plenty entropy
      const base36 = BigInt('0x' + hex).toString(36).toUpperCase().padStart(13, '0');
      const compact = base36.slice(0, 12); // normalize length
      const formatted = `${compact.slice(0, 4)}-${compact.slice(4, 8)}-${compact.slice(8, 12)}`;
      codes.push(formatted);
    }
    return codes;
  }

  /**
   * Return count of remaining (hashed) backup codes
   */
  private async getBackupCodesCount(userId: string): Promise<number> {
    const user = await this.adminUtils.getUserWithRole(userId);
    const prefs = user?.preferences || {};
    const hashed: string[] =
      (prefs as any).mfa_backup_codes_hashed ||
      []; // old plaintext list is ignored for security
    return hashed.length;
  }

  /**
   * Verify and consume a backup code (hash compare)
   */
  private async verifyBackupCode(
    userId: string,
    code: string
  ): Promise<{ valid: boolean; remainingBackupCodes?: number }> {
    const user = await this.adminUtils.getUserWithRole(userId);
    const prefs = user?.preferences || {};
    const list: string[] =
      (prefs as any).mfa_backup_codes_hashed ||
      (prefs as any).mfa_backup_codes ||
      [];

    if (!list.length) return { valid: false };

    const probe = await sha256Hex(code.toUpperCase());
    const idx = list.indexOf(probe);

    if (idx === -1) return { valid: false };

    // consume code
    const updated = [...list.slice(0, idx), ...list.slice(idx + 1)];
    await this.adminUtils.updateUser(userId, {
      preferences: { ...prefs, mfa_backup_codes_hashed: updated, mfa_backup_codes: undefined },
    });

    return { valid: true, remainingBackupCodes: updated.length };
  }
}

// Export singleton instance
export const mfaManager = new MfaManager();
