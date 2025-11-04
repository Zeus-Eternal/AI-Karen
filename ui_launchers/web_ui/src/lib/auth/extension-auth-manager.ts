/**
 * Extension Authentication Manager
 * 
 * Handles authentication for extension API calls with automatic token refresh,
 * secure token storage, and authentication state management.
 * 
 * Requirements addressed:
 * - 3.1: Extension integration service error handling
 * - 3.2: Extension API calls with proper authentication
 * - 3.3: Authentication failures and retry logic
 * - 6.1: Development mode authentication support
 * - 6.2: Hot reload support without authentication issues
 */

import { logger } from '@/lib/logger';
import { getConnectionManager, ConnectionError, ErrorCategory } from '@/lib/connection/connection-manager';
import { getTimeoutManager, OperationType } from '@/lib/connection/timeout-manager';
import { getDevelopmentAuthManager, isDevelopmentFeaturesEnabled } from './development-auth';
import { getHotReloadAuthManager } from './hot-reload-auth';

// Token storage interface for secure token management
interface TokenStorage {
  getAccessToken(): string | null;
  getRefreshToken(): string | null;
  setTokens(accessToken: string, refreshToken?: string): void;
  clearTokens(): void;
  isTokenExpiringSoon(token: string): boolean;
}

// Authentication state interface
interface AuthState {
  isAuthenticated: boolean;
  isRefreshing: boolean;
  lastRefresh: Date | null;
  failureCount: number;
  nextRetryAt: Date | null;
}

// Token refresh response interface
interface TokenRefreshResponse {
  access_token: string;
  refresh_token?: string;
  expires_in?: number;
  token_type?: string;
}

// Secure token storage implementation with encryption support
class SecureTokenStorage implements TokenStorage {
  private readonly ACCESS_TOKEN_KEY = 'karen_extension_access_token';
  private readonly REFRESH_TOKEN_KEY = 'karen_extension_refresh_token';
  private readonly ENCRYPTION_KEY = 'karen_extension_auth_key';

  constructor() {
    // Initialize encryption key if not exists
    this.initializeEncryptionKey();
  }

  private initializeEncryptionKey(): void {
    if (typeof window === 'undefined') return;
    
    try {
      if (!localStorage.getItem(this.ENCRYPTION_KEY)) {
        // Generate a simple encryption key for token obfuscation
        const key = btoa(Math.random().toString(36).substring(2, 15) + 
                         Math.random().toString(36).substring(2, 15));
        localStorage.setItem(this.ENCRYPTION_KEY, key);
      }
    } catch (error) {
      logger.warn('Failed to initialize encryption key:', error);
    }
  }

  private encrypt(data: string): string {
    if (typeof window === 'undefined') return data;
    
    try {
      const key = localStorage.getItem(this.ENCRYPTION_KEY);
      if (!key) return data;
      
      // Simple XOR encryption for token obfuscation
      const keyBytes = atob(key);
      let encrypted = '';
      for (let i = 0; i < data.length; i++) {
        encrypted += String.fromCharCode(
          data.charCodeAt(i) ^ keyBytes.charCodeAt(i % keyBytes.length)
        );
      }
      return btoa(encrypted);
    } catch (error) {
      logger.warn('Token encryption failed, storing in plain text:', error);
      return data;
    }
  }

  private decrypt(encryptedData: string): string {
    if (typeof window === 'undefined') return encryptedData;
    
    try {
      const key = localStorage.getItem(this.ENCRYPTION_KEY);
      if (!key) return encryptedData;
      
      const keyBytes = atob(key);
      const encrypted = atob(encryptedData);
      let decrypted = '';
      for (let i = 0; i < encrypted.length; i++) {
        decrypted += String.fromCharCode(
          encrypted.charCodeAt(i) ^ keyBytes.charCodeAt(i % keyBytes.length)
        );
      }
      return decrypted;
    } catch (error) {
      logger.warn('Token decryption failed, returning as-is:', error);
      return encryptedData;
    }
  }

  getAccessToken(): string | null {
    if (typeof window === 'undefined') return null;
    
    try {
      const encrypted = localStorage.getItem(this.ACCESS_TOKEN_KEY);
      if (!encrypted) return null;
      
      const token = this.decrypt(encrypted);
      return token && token !== 'null' && token !== 'undefined' ? token : null;
    } catch (error) {
      logger.warn('Failed to get access token:', error);
      return null;
    }
  }

  getRefreshToken(): string | null {
    if (typeof window === 'undefined') return null;
    
    try {
      const encrypted = localStorage.getItem(this.REFRESH_TOKEN_KEY);
      if (!encrypted) return null;
      
      const token = this.decrypt(encrypted);
      return token && token !== 'null' && token !== 'undefined' ? token : null;
    } catch (error) {
      logger.warn('Failed to get refresh token:', error);
      return null;
    }
  }

  setTokens(accessToken: string, refreshToken?: string): void {
    if (typeof window === 'undefined') return;
    
    try {
      localStorage.setItem(this.ACCESS_TOKEN_KEY, this.encrypt(accessToken));
      
      if (refreshToken) {
        localStorage.setItem(this.REFRESH_TOKEN_KEY, this.encrypt(refreshToken));
      }
      
      logger.debug('Extension auth tokens stored successfully');
    } catch (error) {
      logger.error('Failed to store extension auth tokens:', error);
    }
  }

  clearTokens(): void {
    if (typeof window === 'undefined') return;
    
    try {
      localStorage.removeItem(this.ACCESS_TOKEN_KEY);
      localStorage.removeItem(this.REFRESH_TOKEN_KEY);
      logger.debug('Extension auth tokens cleared');
    } catch (error) {
      logger.warn('Failed to clear extension auth tokens:', error);
    }
  }

  isTokenExpiringSoon(token: string): boolean {
    try {
      // Parse JWT token to check expiration
      const payload = JSON.parse(atob(token.split('.')[1]));
      const expirationTime = payload.exp * 1000; // Convert to milliseconds
      const currentTime = Date.now();
      const timeUntilExpiry = expirationTime - currentTime;

      // Refresh if token expires within 5 minutes
      return timeUntilExpiry < 5 * 60 * 1000;
    } catch (error) {
      logger.warn('Error parsing token expiration:', error);
      return true; // Assume expired if can't parse
    }
  }
}

/**
 * Extension Authentication Manager
 * 
 * Manages authentication for extension API calls with automatic token refresh,
 * secure storage, and comprehensive error handling.
 */
export class ExtensionAuthManager {
  private tokenStorage: TokenStorage;
  private connectionManager = getConnectionManager();
  private timeoutManager = getTimeoutManager();
  private authState: AuthState;
  private refreshPromise: Promise<string | null> | null = null;
  private readonly MAX_RETRY_ATTEMPTS = 3;
  private readonly RETRY_BACKOFF_MS = 1000;

  constructor() {
    this.tokenStorage = new SecureTokenStorage();
    this.authState = {
      isAuthenticated: false,
      isRefreshing: false,
      lastRefresh: null,
      failureCount: 0,
      nextRetryAt: null,
    };

    // Initialize authentication state
    this.initializeAuthState();
    
    // Initialize development and hot reload support
    this.initializeDevelopmentSupport();
  }

  /**
   * Initialize authentication state from stored tokens
   */
  private initializeAuthState(): void {
    const token = this.tokenStorage.getAccessToken();
    if (token && !this.tokenStorage.isTokenExpiringSoon(token)) {
      this.authState.isAuthenticated = true;
      logger.debug('Extension auth manager initialized with valid token');
    } else {
      logger.debug('Extension auth manager initialized without valid token');
    }
  }

  /**
   * Initialize development and hot reload support
   */
  private initializeDevelopmentSupport(): void {
    if (!this.isDevelopmentMode()) {
      return;
    }

    // Initialize development auth manager
    const devAuthManager = getDevelopmentAuthManager();
    if (devAuthManager.isEnabled()) {
      logger.debug('Development authentication support enabled');
    }

    // Initialize hot reload support
    const hotReloadManager = getHotReloadAuthManager();
    hotReloadManager.addHotReloadListener((event) => {
      logger.debug('Hot reload detected in extension auth manager', event);
      // Preserve current authentication state
      this.preserveAuthForHotReload();
    });

  }

  /**
   * Preserve authentication state for hot reload
   */
  private preserveAuthForHotReload(): void {
    try {
      const currentToken = this.tokenStorage.getAccessToken();
      if (currentToken) {
        // Store in session storage for hot reload persistence
        sessionStorage.setItem('extension_auth_hot_reload_token', currentToken);
        logger.debug('Extension auth token preserved for hot reload');
      }
    } catch (error) {
      logger.warn('Failed to preserve extension auth for hot reload:', error);
    }
  }

  /**
   * Get authentication headers for extension API requests
   */
  async getAuthHeaders(): Promise<Record<string, string>> {
    // Check if we should use development authentication
    if (this.isDevelopmentMode()) {
      const devAuthManager = getDevelopmentAuthManager();
      if (devAuthManager.isEnabled()) {
        return await devAuthManager.getDevelopmentAuthHeaders();
      }
    }

    const token = await this.getValidToken();

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'X-Client-Type': 'extension-integration',
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    // Add development mode headers if applicable
    if (this.isDevelopmentMode()) {
      headers['X-Development-Mode'] = 'true';
      headers['X-Skip-Auth'] = 'dev';
    }

    return headers;
  }

  /**
   * Get a valid authentication token, refreshing if necessary
   */
  async getValidToken(): Promise<string | null> {
    // Check if we should use development authentication
    if (this.isDevelopmentMode()) {
      const devAuthManager = getDevelopmentAuthManager();
      if (devAuthManager.isEnabled()) {
        return await devAuthManager.getDevelopmentToken('dev-user');
      }
    }

    // Check if we're in a retry backoff period
    if (this.authState.nextRetryAt && Date.now() < this.authState.nextRetryAt.getTime()) {
      logger.debug('Extension auth in retry backoff period');
      return null;
    }

    let token = this.tokenStorage.getAccessToken();

    // Check for hot reload token restoration
    if (!token) {
      token = this.restoreTokenFromHotReload();
    }

    if (!token) {
      // Try to get token from main auth context
      token = await this.getTokenFromMainAuth();
      if (token) {
        this.tokenStorage.setTokens(token);
        this.authState.isAuthenticated = true;
      }
    }

    if (!token) {
      logger.debug('No extension auth token available');
      return null;
    }

    // Check if token is expiring soon and refresh proactively
    if (this.tokenStorage.isTokenExpiringSoon(token)) {
      try {
        token = await this.refreshToken();
      } catch (error) {
        logger.warn('Failed to refresh token proactively:', error);
        // Continue with existing token if refresh fails
      }
    }

    return token;
  }

  /**
   * Restore token from hot reload if available
   */
  private restoreTokenFromHotReload(): string | null {
    if (typeof window === 'undefined') return null;

    try {
      const hotReloadToken = sessionStorage.getItem('extension_auth_hot_reload_token');
      if (hotReloadToken && hotReloadToken !== 'null' && hotReloadToken !== 'undefined') {
        // Validate token is still valid
        if (!this.tokenStorage.isTokenExpiringSoon(hotReloadToken)) {
          // Store in regular token storage
          this.tokenStorage.setTokens(hotReloadToken);
          // Clean up hot reload storage
          sessionStorage.removeItem('extension_auth_hot_reload_token');
          logger.debug('Extension auth token restored from hot reload');
          return hotReloadToken;
        }
      }
    } catch (error) {
      logger.debug('Failed to restore token from hot reload:', error);
    }

    return null;
  }

  /**
   * Refresh the authentication token
   */
  async refreshToken(): Promise<string | null> {
    // Prevent concurrent refresh attempts
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    this.authState.isRefreshing = true;
    this.refreshPromise = this.performTokenRefresh();

    try {
      const newToken = await this.refreshPromise;
      this.authState.isAuthenticated = !!newToken;
      this.authState.lastRefresh = new Date();
      this.authState.failureCount = 0;
      this.authState.nextRetryAt = null;
      return newToken;
    } catch (error) {
      this.handleRefreshFailure(error);
      throw error;
    } finally {
      this.authState.isRefreshing = false;
      this.refreshPromise = null;
    }
  }

  /**
   * Perform the actual token refresh operation
   */
  private async performTokenRefresh(): Promise<string | null> {
    const refreshToken = this.tokenStorage.getRefreshToken();

    if (!refreshToken) {
      // Try to get fresh tokens from main auth context
      const mainToken = await this.getTokenFromMainAuth();
      if (mainToken) {
        this.tokenStorage.setTokens(mainToken);
        return mainToken;
      }
      
      throw new ConnectionError(
        'No refresh token available',
        ErrorCategory.CONFIGURATION_ERROR,
        false,
        0
      );
    }

    try {
      const timeout = this.timeoutManager.getTimeout(OperationType.AUTHENTICATION);
      
      const result = await this.connectionManager.makeRequest(
        '/api/auth/refresh',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            refresh_token: refreshToken,
          }),
          credentials: 'include',
        },
        {
          timeout,
          retryAttempts: 1,
          exponentialBackoff: false,
        }
      );

      const data = result.data as TokenRefreshResponse;

      if (!data.access_token) {
        throw new ConnectionError(
          'No access token in refresh response',
          ErrorCategory.CONFIGURATION_ERROR,
          false,
          0
        );
      }

      // Store new tokens
      this.tokenStorage.setTokens(data.access_token, data.refresh_token);

      logger.debug('Extension auth token refreshed successfully');
      return data.access_token;
    } catch (error) {
      logger.error('Extension auth token refresh failed:', error);
      
      // Clear invalid tokens
      this.tokenStorage.clearTokens();
      this.authState.isAuthenticated = false;
      
      throw error;
    }
  }

  /**
   * Handle token refresh failures with exponential backoff
   */
  private handleRefreshFailure(error: any): void {
    this.authState.failureCount++;
    
    // Calculate exponential backoff delay
    const backoffMs = this.RETRY_BACKOFF_MS * Math.pow(2, this.authState.failureCount - 1);
    this.authState.nextRetryAt = new Date(Date.now() + backoffMs);
    
    logger.warn(`Extension auth refresh failed (attempt ${this.authState.failureCount}), next retry at:`, 
                this.authState.nextRetryAt);

    // Clear tokens after max failures
    if (this.authState.failureCount >= this.MAX_RETRY_ATTEMPTS) {
      this.tokenStorage.clearTokens();
      this.authState.isAuthenticated = false;
      logger.error('Extension auth max retry attempts reached, clearing tokens');
    }
  }

  /**
   * Get token from main authentication context
   */
  private async getTokenFromMainAuth(): Promise<string | null> {
    if (typeof window === 'undefined') return null;

    try {
      // Try to get token from main auth context
      const mainToken = localStorage.getItem('karen_access_token');
      if (mainToken && mainToken !== 'null' && mainToken !== 'undefined') {
        return mainToken;
      }

      // Fallback to session storage
      const sessionToken = sessionStorage.getItem('kari_session_token');
      if (sessionToken && sessionToken !== 'null' && sessionToken !== 'undefined') {
        return sessionToken;
      }

      // Try to validate existing session
      const timeout = this.timeoutManager.getTimeout(OperationType.SESSION_VALIDATION);
      
      const result = await this.connectionManager.makeRequest(
        '/api/auth/validate-session',
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
        },
        {
          timeout,
          retryAttempts: 1,
          exponentialBackoff: false,
        }
      );

      if (result.data.valid && result.data.token) {
        return result.data.token;
      }

      return null;
    } catch (error) {
      logger.debug('Failed to get token from main auth:', error);
      return null;
    }
  }

  /**
   * Check if running in development mode
   */
  private isDevelopmentMode(): boolean {
    if (!isDevelopmentFeaturesEnabled()) {
      return false;
    }

    if (typeof window === 'undefined') {
      return process.env.NODE_ENV === 'development';
    }

    return (
      process.env.NODE_ENV === 'development' ||
      window.location.hostname === 'localhost' ||
      window.location.hostname === '127.0.0.1' ||
      window.location.search.includes('dev=true')
    );
  }

  /**
   * Clear all authentication state and tokens
   */
  clearAuth(): void {
    this.tokenStorage.clearTokens();
    this.authState = {
      isAuthenticated: false,
      isRefreshing: false,
      lastRefresh: null,
      failureCount: 0,
      nextRetryAt: null,
    };
    this.refreshPromise = null;
    logger.debug('Extension auth state cleared');
  }

  /**
   * Get current authentication state
   */
  getAuthState(): Readonly<AuthState> {
    return { ...this.authState };
  }

  /**
   * Check if currently authenticated
   */
  isAuthenticated(): boolean {
    return this.authState.isAuthenticated && !!this.tokenStorage.getAccessToken();
  }

  /**
   * Force token refresh (useful for testing or manual refresh)
   */
  async forceRefresh(): Promise<string | null> {
    // Clear any existing refresh promise to force a new one
    this.refreshPromise = null;
    return this.refreshToken();
  }
}

// Global instance
let extensionAuthManager: ExtensionAuthManager | null = null;

/**
 * Get the global extension authentication manager instance
 */
export function getExtensionAuthManager(): ExtensionAuthManager {
  if (!extensionAuthManager) {
    extensionAuthManager = new ExtensionAuthManager();
  }
  return extensionAuthManager;
}

/**
 * Initialize a new extension authentication manager instance
 */
export function initializeExtensionAuthManager(): ExtensionAuthManager {
  extensionAuthManager = new ExtensionAuthManager();
  return extensionAuthManager;
}
