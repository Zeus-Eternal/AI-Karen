'use client';

import React from 'react';
import { useTelemetry } from '@/hooks/use-telemetry';

export interface TokenData {
  accessToken: string;
  refreshToken?: string;
  expiresAt: number;
  issuedAt: number;
  userId?: string;
  scope?: string[];
}

export interface TokenValidationResult {
  isValid: boolean;
  isExpired: boolean;
  expiresIn: number;
  needsRefresh: boolean;
  reason?: string;
}

// Token storage keys
const TOKEN_STORAGE_KEY = 'secure_tokens';
const TOKEN_ENCRYPTION_KEY = 'token_encryption_key';

// Security constants
const REFRESH_THRESHOLD_MS = 5 * 60 * 1000; // 5 minutes before expiry
const MAX_TOKEN_AGE_MS = 24 * 60 * 60 * 1000; // 24 hours
const ENCRYPTION_ALGORITHM = 'AES-GCM';

/**
 * Secure token storage and management class
 */
export class SecureTokenManager {
  private static instance: SecureTokenManager;
  private encryptionKey: CryptoKey | null = null;
  private tokenData: TokenData | null = null;
  private refreshPromise: Promise<TokenData> | null = null;
  private telemetry: ReturnType<typeof useTelemetry> | null = null;

  private constructor() {
    this.initializeEncryption();
  }

  public static getInstance(): SecureTokenManager {
    if (!SecureTokenManager.instance) {
      SecureTokenManager.instance = new SecureTokenManager();
    }
    return SecureTokenManager.instance;
  }

  public setTelemetry(telemetry: ReturnType<typeof useTelemetry>): void {
    this.telemetry = telemetry;
  }

  /**
   * Initialize encryption for token storage
   */
  private async initializeEncryption(): Promise<void> {
    try {
      // Check if we have a stored encryption key
      const storedKey = localStorage.getItem(TOKEN_ENCRYPTION_KEY);
      
      if (storedKey) {
        // Import existing key
        const keyData = JSON.parse(storedKey);
        this.encryptionKey = await crypto.subtle.importKey(
          'raw',
          new Uint8Array(keyData),
          { name: ENCRYPTION_ALGORITHM },
          false,
          ['encrypt', 'decrypt']
        );
      } else {
        // Generate new encryption key
        this.encryptionKey = await crypto.subtle.generateKey(
          { name: ENCRYPTION_ALGORITHM, length: 256 },
          true,
          ['encrypt', 'decrypt']
        );

        // Store the key (in production, consider more secure storage)
        const exportedKey = await crypto.subtle.exportKey('raw', this.encryptionKey);
        localStorage.setItem(TOKEN_ENCRYPTION_KEY, JSON.stringify(Array.from(new Uint8Array(exportedKey))));
      }
    } catch (error) {
      console.error('Failed to initialize token encryption:', error);
      this.telemetry?.track('token_encryption_init_failed', {
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  }

  /**
   * Encrypt token data for storage
   */
  private async encryptTokenData(data: TokenData): Promise<string> {
    if (!this.encryptionKey) {
      throw new Error('Encryption key not initialized');
    }

    try {
      const encoder = new TextEncoder();
      const dataString = JSON.stringify(data);
      const dataBuffer = encoder.encode(dataString);

      const iv = crypto.getRandomValues(new Uint8Array(12));
      const encryptedData = await crypto.subtle.encrypt(
        { name: ENCRYPTION_ALGORITHM, iv },
        this.encryptionKey,
        dataBuffer
      );

      // Combine IV and encrypted data
      const combined = new Uint8Array(iv.length + encryptedData.byteLength);
      combined.set(iv);
      combined.set(new Uint8Array(encryptedData), iv.length);

      return btoa(String.fromCharCode(...combined));
    } catch (error) {
      this.telemetry?.track('token_encryption_failed', {
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      throw new Error('Failed to encrypt token data');
    }
  }

  /**
   * Decrypt token data from storage
   */
  private async decryptTokenData(encryptedData: string): Promise<TokenData> {
    if (!this.encryptionKey) {
      throw new Error('Encryption key not initialized');
    }

    try {
      const combined = new Uint8Array(
        atob(encryptedData).split('').map(char => char.charCodeAt(0))
      );

      const iv = combined.slice(0, 12);
      const encrypted = combined.slice(12);

      const decryptedData = await crypto.subtle.decrypt(
        { name: ENCRYPTION_ALGORITHM, iv },
        this.encryptionKey,
        encrypted
      );

      const decoder = new TextDecoder();
      const dataString = decoder.decode(decryptedData);
      return JSON.parse(dataString);
    } catch (error) {
      this.telemetry?.track('token_decryption_failed', {
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      throw new Error('Failed to decrypt token data');
    }
  }

  /**
   * Store tokens securely
   */
  public async storeTokens(tokenData: TokenData): Promise<void> {
    try {
      // Validate token data
      if (!tokenData.accessToken) {
        throw new Error('Access token is required');
      }

      // Add metadata
      const enrichedTokenData: TokenData = {
        ...tokenData,
        issuedAt: Date.now(),
        expiresAt: tokenData.expiresAt || (Date.now() + MAX_TOKEN_AGE_MS)
      };

      // Encrypt and store
      const encryptedData = await this.encryptTokenData(enrichedTokenData);
      localStorage.setItem(TOKEN_STORAGE_KEY, encryptedData);
      
      // Cache in memory
      this.tokenData = enrichedTokenData;

      this.telemetry?.track('tokens_stored', {
        hasRefreshToken: !!tokenData.refreshToken,
        expiresIn: enrichedTokenData.expiresAt - Date.now(),
        userId: tokenData.userId
      });
    } catch (error) {
      this.telemetry?.track('token_storage_failed', {
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      throw error;
    }
  }

  /**
   * Retrieve tokens from secure storage
   */
  public async getTokens(): Promise<TokenData | null> {
    try {
      // Return cached data if available and valid
      if (this.tokenData) {
        const validation = this.validateToken(this.tokenData);
        if (validation.isValid && !validation.isExpired) {
          return this.tokenData;
        }
      }

      // Load from storage
      const encryptedData = localStorage.getItem(TOKEN_STORAGE_KEY);
      if (!encryptedData) {
        return null;
      }

      const tokenData = await this.decryptTokenData(encryptedData);
      
      // Validate loaded tokens
      const validation = this.validateToken(tokenData);
      if (!validation.isValid || validation.isExpired) {
        await this.clearTokens();
        return null;
      }

      this.tokenData = tokenData;
      return tokenData;
    } catch (error) {
      this.telemetry?.track('token_retrieval_failed', {
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      
      // Clear corrupted data
      await this.clearTokens();
      return null;
    }
  }

  /**
   * Validate token data
   */
  public validateToken(tokenData: TokenData): TokenValidationResult {
    const now = Date.now();
    
    if (!tokenData.accessToken) {
      return {
        isValid: false,
        isExpired: false,
        expiresIn: 0,
        needsRefresh: false,
        reason: 'Missing access token'
      };
    }

    const isExpired = now >= tokenData.expiresAt;
    const expiresIn = tokenData.expiresAt - now;
    const needsRefresh = expiresIn <= REFRESH_THRESHOLD_MS && !!tokenData.refreshToken;

    // Check token age
    const tokenAge = now - tokenData.issuedAt;
    if (tokenAge > MAX_TOKEN_AGE_MS) {
      return {
        isValid: false,
        isExpired: true,
        expiresIn: 0,
        needsRefresh: false,
        reason: 'Token too old'
      };
    }

    return {
      isValid: !isExpired,
      isExpired,
      expiresIn: Math.max(0, expiresIn),
      needsRefresh,
      reason: isExpired ? 'Token expired' : undefined
    };
  }

  /**
   * Get current access token with automatic refresh
   */
  public async getAccessToken(): Promise<string | null> {
    try {
      const tokenData = await this.getTokens();
      if (!tokenData) {
        return null;
      }

      const validation = this.validateToken(tokenData);
      
      if (validation.needsRefresh) {
        // Attempt to refresh token
        const refreshedTokens = await this.refreshTokens();
        return refreshedTokens?.accessToken || null;
      }

      if (!validation.isValid) {
        return null;
      }

      return tokenData.accessToken;
    } catch (error) {
      this.telemetry?.track('access_token_retrieval_failed', {
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      return null;
    }
  }

  /**
   * Refresh tokens using refresh token
   */
  public async refreshTokens(refreshEndpoint: string = '/api/auth/refresh'): Promise<TokenData | null> {
    try {
      // Prevent multiple simultaneous refresh attempts
      if (this.refreshPromise) {
        return await this.refreshPromise;
      }

      const tokenData = await this.getTokens();
      if (!tokenData?.refreshToken) {
        throw new Error('No refresh token available');
      }

      this.refreshPromise = this.performTokenRefresh(refreshEndpoint, tokenData.refreshToken);
      const result = await this.refreshPromise;
      this.refreshPromise = null;

      return result;
    } catch (error) {
      this.refreshPromise = null;
      this.telemetry?.track('token_refresh_failed', {
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      throw error;
    }
  }

  /**
   * Perform the actual token refresh API call
   */
  private async performTokenRefresh(endpoint: string, refreshToken: string): Promise<TokenData> {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refreshToken }),
    });

    if (!response.ok) {
      throw new Error(`Token refresh failed: ${response.status}`);
    }

    const data = await response.json();
    
    const newTokenData: TokenData = {
      accessToken: data.accessToken,
      refreshToken: data.refreshToken || refreshToken,
      expiresAt: data.expiresAt || (Date.now() + (data.expiresIn * 1000)),
      issuedAt: Date.now(),
      userId: data.userId,
      scope: data.scope
    };

    await this.storeTokens(newTokenData);
    
    this.telemetry?.track('tokens_refreshed', {
      userId: newTokenData.userId,
      expiresIn: newTokenData.expiresAt - Date.now()
    });

    return newTokenData;
  }

  /**
   * Clear all stored tokens
   */
  public async clearTokens(): Promise<void> {
    try {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
      this.tokenData = null;
      this.refreshPromise = null;

      this.telemetry?.track('tokens_cleared', {});
    } catch (error) {
      this.telemetry?.track('token_clear_failed', {
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  }

  /**
   * Check if user is authenticated
   */
  public async isAuthenticated(): Promise<boolean> {
    const token = await this.getAccessToken();
    return !!token;
  }

  /**
   * Get token expiration info
   */
  public async getTokenInfo(): Promise<{
    isAuthenticated: boolean;
    expiresIn: number;
    needsRefresh: boolean;
  } | null> {
    const tokenData = await this.getTokens();
    if (!tokenData) {
      return null;
    }

    const validation = this.validateToken(tokenData);
    
    return {
      isAuthenticated: validation.isValid,
      expiresIn: validation.expiresIn,
      needsRefresh: validation.needsRefresh
    };
  }
}

// React hook for token management
export const useSecureTokens = () => {
  const telemetry = useTelemetry();
  const tokenManager = SecureTokenManager.getInstance();
  
  // Set telemetry on first use
  React.useEffect(() => {
    tokenManager.setTelemetry(telemetry);
  }, [telemetry]);

  return {
    storeTokens: (tokenData: TokenData) => tokenManager.storeTokens(tokenData),
    getTokens: () => tokenManager.getTokens(),
    getAccessToken: () => tokenManager.getAccessToken(),
    refreshTokens: (endpoint?: string) => tokenManager.refreshTokens(endpoint),
    clearTokens: () => tokenManager.clearTokens(),
    isAuthenticated: () => tokenManager.isAuthenticated(),
    getTokenInfo: () => tokenManager.getTokenInfo(),
    validateToken: (tokenData: TokenData) => tokenManager.validateToken(tokenData)
  };
};

// Utility function to create Authorization header
export const createAuthHeader = async (): Promise<{ Authorization: string } | {}> => {
  const tokenManager = SecureTokenManager.getInstance();
  const accessToken = await tokenManager.getAccessToken();
  
  if (!accessToken) {
    return {};
  }
  
  return {
    Authorization: `Bearer ${accessToken}`
  };
};

// Fetch wrapper with automatic token handling
export const secureApiCall = async (
  url: string,
  options: RequestInit = {}
): Promise<Response> => {
  const authHeader = await createAuthHeader();
  
  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      ...authHeader
    }
  });

  // Handle token expiration
  if (response.status === 401) {
    const tokenManager = SecureTokenManager.getInstance();
    
    try {
      // Attempt to refresh token
      await tokenManager.refreshTokens();
      
      // Retry the request with new token
      const newAuthHeader = await createAuthHeader();
      return fetch(url, {
        ...options,
        headers: {
          ...options.headers,
          ...newAuthHeader
        }
      });
    } catch (error) {
      // Refresh failed, clear tokens and redirect to login
      await tokenManager.clearTokens();
      throw new Error('Authentication failed');
    }
  }

  return response;
};

export default SecureTokenManager;