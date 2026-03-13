/**
 * Secure Storage Utility for the CoPilot frontend.
 * 
 * This utility provides secure storage mechanisms for sensitive data
 * like authentication tokens, using encryption and secure storage APIs.
 */

import { AuthTokens } from '../types';

// Storage keys
const STORAGE_KEYS = {
  AUTH_TOKENS: 'auth_tokens',
  AUTH_LAST_ACTIVITY: 'auth_last_activity',
  DEVICE_FINGERPRINT: 'device_fingerprint',
  MFA_BACKUP_CODES: 'mfa_backup_codes',
  SECURITY_PREFERENCES: 'security_preferences',
} as const;

// Encryption configuration
const ENCRYPTION_CONFIG = {
  ALGORITHM: 'AES-GCM',
  KEY_LENGTH: 256,
  IV_LENGTH: 12,
  SALT_LENGTH: 16,
  ITERATIONS: 100000,
} as const;

// Storage types
type StorageType = 'localStorage' | 'sessionStorage' | 'memory';

// Encrypted data structure
interface EncryptedData {
  data: string;
  iv: string;
  salt: string;
  algorithm: string;
  timestamp: number;
}

// Security preferences
interface SecurityPreferences {
  storageType: StorageType;
  sessionTimeout: number;
  rememberDevice: boolean;
  autoLogout: boolean;
  requireReauth: boolean;
  reauthInterval: number;
}

// Default security preferences
const DEFAULT_SECURITY_PREFERENCES: SecurityPreferences = {
  storageType: 'localStorage',
  sessionTimeout: 30 * 60 * 1000, // 30 minutes
  rememberDevice: false,
  autoLogout: true,
  requireReauth: false,
  reauthInterval: 15 * 60 * 1000, // 15 minutes
};

/**
 * Secure Storage Class
 */
export class SecureStorage {
  private static instance: SecureStorage;
  private encryptionKey: CryptoKey | null = null;
  private memoryStorage: Map<string, unknown> = new Map();
  private securityPreferences: SecurityPreferences = DEFAULT_SECURITY_PREFERENCES;

  private constructor() {
    this.initializeSecurity();
  }

  /**
   * Get singleton instance
   */
  static getInstance(): SecureStorage {
    if (!SecureStorage.instance) {
      SecureStorage.instance = new SecureStorage();
    }
    return SecureStorage.instance;
  }

  /**
   * Initialize security settings
   */
  private async initializeSecurity(): Promise<void> {
    try {
      // Load security preferences
      await this.loadSecurityPreferences();
      
      // Generate or load encryption key
      await this.getEncryptionKey();
      
      // Clean up expired data
      this.cleanupExpiredData();
    } catch (error) {
      console.error('Error initializing secure storage:', error);
    }
  }

  /**
   * Get or generate encryption key
   */
  private async getEncryptionKey(): Promise<CryptoKey> {
    if (this.encryptionKey) {
      return this.encryptionKey;
    }

    try {
      // Try to get existing key from storage
      const storedKey = this.getRawStorageItem('encryption_key');
      
      if (storedKey) {
        const keyData = JSON.parse(storedKey);
        this.encryptionKey = await crypto.subtle.importKey(
          'jwk',
          keyData,
          { name: ENCRYPTION_CONFIG.ALGORITHM },
          false,
          ['encrypt', 'decrypt']
        );
      } else {
        // Generate new key
        this.encryptionKey = await crypto.subtle.generateKey(
          {
            name: ENCRYPTION_CONFIG.ALGORITHM,
            length: ENCRYPTION_CONFIG.KEY_LENGTH,
          },
          true,
          ['encrypt', 'decrypt']
        );
        
        // Store the key
        const exportedKey = await crypto.subtle.exportKey('jwk', this.encryptionKey);
        this.setRawStorageItem('encryption_key', JSON.stringify(exportedKey));
      }
      
      return this.encryptionKey;
    } catch (error) {
      console.error('Error getting encryption key:', error);
      throw error;
    }
  }

  /**
   * Derive key from password
   */
  private async deriveKey(password: string, salt: Uint8Array): Promise<CryptoKey> {
    const encoder = new TextEncoder();
    const keyMaterial = await crypto.subtle.importKey(
      'raw',
      encoder.encode(password),
      { name: 'PBKDF2' },
      false,
      ['deriveBits', 'deriveKey']
    );

    return crypto.subtle.deriveKey(
      {
        name: 'PBKDF2',
        salt: new Uint8Array(salt),
        iterations: ENCRYPTION_CONFIG.ITERATIONS,
        hash: 'SHA-256',
      },
      keyMaterial,
      { name: ENCRYPTION_CONFIG.ALGORITHM, length: ENCRYPTION_CONFIG.KEY_LENGTH },
      false,
      ['encrypt', 'decrypt']
    );
  }

  /**
   * Encrypt data
   */
  private async encrypt(data: string): Promise<EncryptedData> {
    try {
      const key = await this.getEncryptionKey();
      const encoder = new TextEncoder();
      const iv = crypto.getRandomValues(new Uint8Array(ENCRYPTION_CONFIG.IV_LENGTH));
      const salt = crypto.getRandomValues(new Uint8Array(ENCRYPTION_CONFIG.SALT_LENGTH));
      
      const encryptedData = await crypto.subtle.encrypt(
        {
          name: ENCRYPTION_CONFIG.ALGORITHM,
          iv,
        },
        key,
        encoder.encode(data)
      );
      
      return {
        data: this.arrayBufferToBase64(encryptedData),
        iv: this.arrayBufferToBase64(iv.buffer),
        salt: this.arrayBufferToBase64(salt.buffer),
        algorithm: ENCRYPTION_CONFIG.ALGORITHM,
        timestamp: Date.now(),
      };
    } catch (error) {
      console.error('Error encrypting data:', error);
      throw error;
    }
  }

  /**
   * Decrypt data
   */
  private async decrypt(encryptedData: EncryptedData): Promise<string> {
    try {
      const key = await this.getEncryptionKey();
      const iv = this.base64ToArrayBuffer(encryptedData.iv);
      const data = this.base64ToArrayBuffer(encryptedData.data);
      
      const decryptedData = await crypto.subtle.decrypt(
        {
          name: encryptedData.algorithm,
          iv,
        },
        key,
        data
      );
      
      const decoder = new TextDecoder();
      return decoder.decode(decryptedData);
    } catch (error) {
      console.error('Error decrypting data:', error);
      throw error;
    }
  }

  /**
   * Convert ArrayBuffer to Base64
   */
  private arrayBufferToBase64(buffer: ArrayBuffer): string {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i] || 0);
    }
    return btoa(binary);
  }

  /**
   * Convert Base64 to ArrayBuffer
   */
  private base64ToArrayBuffer(base64: string): ArrayBuffer {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i) || 0;
    }
    return bytes.buffer;
  }

  /**
   * Get appropriate storage API
   */
  private getStorageAPI(): Storage | Map<string, unknown> {
    switch (this.securityPreferences.storageType) {
      case 'localStorage':
        return typeof window !== 'undefined' ? window.localStorage : this.memoryStorage;
      case 'sessionStorage':
        return typeof window !== 'undefined' ? window.sessionStorage : this.memoryStorage;
      case 'memory':
        return this.memoryStorage;
      default:
        return this.memoryStorage;
    }
  }

  /**
   * Get raw storage item
   */
  private getRawStorageItem(key: string): string | null {
    const storage = this.getStorageAPI();
    
    if (storage instanceof Map) {
      return (storage.get(key) as string) || null;
    }
    
    try {
      return storage.getItem(key);
    } catch (error) {
      console.error('Error getting storage item:', error);
      return null;
    }
  }

  /**
   * Set raw storage item
   */
  private setRawStorageItem(key: string, value: string): void {
    const storage = this.getStorageAPI();
    
    if (storage instanceof Map) {
      storage.set(key, value);
    } else {
      try {
        storage.setItem(key, value);
      } catch (error) {
        console.error('Error setting storage item:', error);
      }
    }
  }

  /**
   * Remove raw storage item
   */
  private removeRawStorageItem(key: string): void {
    const storage = this.getStorageAPI();
    
    if (storage instanceof Map) {
      storage.delete(key);
    } else {
      try {
        storage.removeItem(key);
      } catch (error) {
        console.error('Error removing storage item:', error);
      }
    }
  }

  /**
   * Clean up expired data
   */
  private cleanupExpiredData(): void {
    try {
      const storage = this.getStorageAPI();
      const keys = storage instanceof Map 
        ? Array.from(storage.keys())
        : Object.keys(storage);
      
      keys.forEach(key => {
        if (key.startsWith('encrypted_')) {
          try {
            const item = this.getRawStorageItem(key);
            if (item) {
              const encryptedData: EncryptedData = JSON.parse(item);
              const maxAge = 24 * 60 * 60 * 1000; // 24 hours
              
              if (Date.now() - encryptedData.timestamp > maxAge) {
                this.removeRawStorageItem(key);
              }
            }
          } catch (error) {
            // Remove invalid items
            this.removeRawStorageItem(key);
          }
        }
      });
    } catch (error) {
      console.error('Error cleaning up expired data:', error);
    }
  }

  /**
   * Load security preferences
   */
  private async loadSecurityPreferences(): Promise<void> {
    try {
      const stored = this.getRawStorageItem(STORAGE_KEYS.SECURITY_PREFERENCES);
      
      if (stored) {
        this.securityPreferences = { ...DEFAULT_SECURITY_PREFERENCES, ...JSON.parse(stored) };
      }
    } catch (error) {
      console.error('Error loading security preferences:', error);
    }
  }

  /**
   * Save security preferences
   */
  private async saveSecurityPreferences(): Promise<void> {
    try {
      this.setRawStorageItem(
        STORAGE_KEYS.SECURITY_PREFERENCES,
        JSON.stringify(this.securityPreferences)
      );
    } catch (error) {
      console.error('Error saving security preferences:', error);
    }
  }

  /**
   * Get encrypted storage item
   */
  public async getItem(key: string): Promise<unknown> {
    try {
      const encryptedKey = `encrypted_${key}`;
      const stored = this.getRawStorageItem(encryptedKey);
      
      if (!stored) {
        return null;
      }
      
      const encryptedData: EncryptedData = JSON.parse(stored);
      const decryptedData = await this.decrypt(encryptedData);
      
      return JSON.parse(decryptedData);
    } catch (error) {
      console.error('Error getting encrypted item:', error);
      return null;
    }
  }

  /**
   * Set encrypted storage item
   */
  public async setItem(key: string, value: unknown): Promise<void> {
    try {
      const encryptedKey = `encrypted_${key}`;
      const data = JSON.stringify(value);
      const encryptedData = await this.encrypt(data);
      
      this.setRawStorageItem(encryptedKey, JSON.stringify(encryptedData));
    } catch (error) {
      console.error('Error setting encrypted item:', error);
      throw error;
    }
  }

  /**
   * Remove encrypted storage item
   */
  public async removeItem(key: string): Promise<void> {
    try {
      const encryptedKey = `encrypted_${key}`;
      this.removeRawStorageItem(encryptedKey);
    } catch (error) {
      console.error('Error removing encrypted item:', error);
    }
  }

  /**
   * Get auth tokens
   */
  public async getAuthTokens(): Promise<AuthTokens | null> {
    return this.getItem(STORAGE_KEYS.AUTH_TOKENS) as Promise<AuthTokens | null>;
  }

  /**
   * Set auth tokens
   */
  public async setAuthTokens(tokens: AuthTokens): Promise<void> {
    await this.setItem(STORAGE_KEYS.AUTH_TOKENS, tokens);
    await this.setItem(STORAGE_KEYS.AUTH_LAST_ACTIVITY, new Date().toISOString());
  }

  /**
   * Remove auth tokens
   */
  public async removeAuthTokens(): Promise<void> {
    await this.removeItem(STORAGE_KEYS.AUTH_TOKENS);
    await this.removeItem(STORAGE_KEYS.AUTH_LAST_ACTIVITY);
  }

  /**
   * Get last activity
   */
  public async getLastActivity(): Promise<string | null> {
    return this.getItem(STORAGE_KEYS.AUTH_LAST_ACTIVITY) as Promise<string | null>;
  }

  /**
   * Set last activity
   */
  public async setLastActivity(): Promise<void> {
    await this.setItem(STORAGE_KEYS.AUTH_LAST_ACTIVITY, new Date().toISOString());
  }

  /**
   * Get device fingerprint
   */
  public async getDeviceFingerprint(): Promise<string | null> {
    return this.getItem(STORAGE_KEYS.DEVICE_FINGERPRINT) as Promise<string | null>;
  }

  /**
   * Set device fingerprint
   */
  public async setDeviceFingerprint(fingerprint: string): Promise<void> {
    await this.setItem(STORAGE_KEYS.DEVICE_FINGERPRINT, fingerprint);
  }

  /**
   * Get MFA backup codes
   */
  public async getMfaBackupCodes(): Promise<string[] | null> {
    return this.getItem(STORAGE_KEYS.MFA_BACKUP_CODES) as Promise<string[] | null>;
  }

  /**
   * Set MFA backup codes
   */
  public async setMfaBackupCodes(codes: string[]): Promise<void> {
    await this.setItem(STORAGE_KEYS.MFA_BACKUP_CODES, codes);
  }

  /**
   * Remove MFA backup codes
   */
  public async removeMfaBackupCodes(): Promise<void> {
    await this.removeItem(STORAGE_KEYS.MFA_BACKUP_CODES);
  }

  /**
   * Get security preferences
   */
  public getSecurityPreferences(): SecurityPreferences {
    return { ...this.securityPreferences };
  }

  /**
   * Set security preferences
   */
  public async setSecurityPreferences(preferences: Partial<SecurityPreferences>): Promise<void> {
    this.securityPreferences = { ...this.securityPreferences, ...preferences };
    await this.saveSecurityPreferences();
  }

  /**
   * Clear all data
   */
  public async clear(): Promise<void> {
    try {
      const storage = this.getStorageAPI();
      const keys = storage instanceof Map 
        ? Array.from(storage.keys())
        : Object.keys(storage);
      
      keys.forEach(key => {
        if (key.startsWith('encrypted_')) {
          this.removeRawStorageItem(key);
        }
      });
      
      // Also clear non-encrypted security items
      this.removeRawStorageItem('encryption_key');
      this.removeRawStorageItem(STORAGE_KEYS.SECURITY_PREFERENCES);
      
      // Reset to defaults
      this.securityPreferences = { ...DEFAULT_SECURITY_PREFERENCES };
    } catch (error) {
      console.error('Error clearing secure storage:', error);
    }
  }

  /**
   * Check if session is valid
   */
  public async isSessionValid(): Promise<boolean> {
    try {
      const lastActivity = await this.getLastActivity();
      
      if (!lastActivity) {
        return false;
      }
      
      const activityTime = new Date(lastActivity).getTime();
      const now = Date.now();
      const elapsed = now - activityTime;
      
      return elapsed < this.securityPreferences.sessionTimeout;
    } catch (error) {
      console.error('Error checking session validity:', error);
      return false;
    }
  }

  /**
   * Generate device fingerprint
   */
  public static generateDeviceFingerprint(): string {
    try {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      
      if (ctx) {
        ctx.textBaseline = 'top';
        ctx.font = '14px Arial';
        ctx.fillText('Device fingerprint', 2, 2);
      }
      
      const fingerprint = [
        navigator.userAgent,
        navigator.language,
        screen.width + 'x' + screen.height,
        new Date().getTimezoneOffset(),
        canvas.toDataURL(),
        navigator.hardwareConcurrency || 0,
        (navigator as unknown as Record<string, unknown>).deviceMemory || 0,
        navigator.platform,
      ].join('|');
      
      // Create hash
      let hash = 0;
      for (let i = 0; i < fingerprint.length; i++) {
        const char = fingerprint.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Convert to 32-bit integer
      }
      
      return Math.abs(hash).toString(16);
    } catch (error) {
      console.error('Error generating device fingerprint:', error);
      return Math.random().toString(36).substring(2);
    }
  }
}

// Export singleton instance
export const secureStorage = SecureStorage.getInstance();

// Export utility functions
export const storageUtils = {
  getAuthTokens: () => secureStorage.getAuthTokens(),
  setAuthTokens: (tokens: AuthTokens) => secureStorage.setAuthTokens(tokens),
  removeAuthTokens: () => secureStorage.removeAuthTokens(),
  getLastActivity: () => secureStorage.getLastActivity(),
  setLastActivity: () => secureStorage.setLastActivity(),
  isSessionValid: () => secureStorage.isSessionValid(),
  getDeviceFingerprint: () => secureStorage.getDeviceFingerprint(),
  setDeviceFingerprint: (fingerprint: string) => secureStorage.setDeviceFingerprint(fingerprint),
  getMfaBackupCodes: () => secureStorage.getMfaBackupCodes(),
  setMfaBackupCodes: (codes: string[]) => secureStorage.setMfaBackupCodes(codes),
  removeMfaBackupCodes: () => secureStorage.removeMfaBackupCodes(),
  getSecurityPreferences: () => secureStorage.getSecurityPreferences(),
  setSecurityPreferences: (preferences: Partial<SecurityPreferences>) => 
    secureStorage.setSecurityPreferences(preferences),
  clear: () => secureStorage.clear(),
  generateDeviceFingerprint: () => SecureStorage.generateDeviceFingerprint(),
};
