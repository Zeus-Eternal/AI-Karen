import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { SecureTokenManager, TokenData, createAuthHeader, secureApiCall } from '../tokenSecurity';

// Mock crypto API
const mockCrypto = {
  subtle: {
    generateKey: vi.fn(),
    importKey: vi.fn(),
    exportKey: vi.fn(),
    encrypt: vi.fn(),
    decrypt: vi.fn()
  },
  getRandomValues: vi.fn()
};

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn()
};

// Mock fetch
const mockFetch = vi.fn();

// Mock telemetry
const mockTrack = vi.fn();
const mockTelemetry = { track: mockTrack };

// Setup global mocks
Object.defineProperty(global, 'crypto', {
  value: mockCrypto,
  writable: true
});

Object.defineProperty(global, 'localStorage', {
  value: mockLocalStorage,
  writable: true
});

Object.defineProperty(global, 'fetch', {
  value: mockFetch,
  writable: true
});

// Mock btoa/atob
Object.defineProperty(global, 'btoa', {
  value: (str: string) => Buffer.from(str, 'binary').toString('base64'),
  writable: true
});

Object.defineProperty(global, 'atob', {
  value: (str: string) => Buffer.from(str, 'base64').toString('binary'),
  writable: true
});

describe('SecureTokenManager', () => {
  let tokenManager: SecureTokenManager;
  let mockEncryptionKey: CryptoKey;

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Reset singleton instance
    (SecureTokenManager as any).instance = undefined;
    
    // Mock encryption key
    mockEncryptionKey = {} as CryptoKey;
    
    // Setup crypto mocks
    mockCrypto.subtle.generateKey.mockResolvedValue(mockEncryptionKey);
    mockCrypto.subtle.importKey.mockResolvedValue(mockEncryptionKey);
    mockCrypto.subtle.exportKey.mockResolvedValue(new ArrayBuffer(32));
    mockCrypto.getRandomValues.mockReturnValue(new Uint8Array(12));
    
    // Mock encryption/decryption
    mockCrypto.subtle.encrypt.mockResolvedValue(new ArrayBuffer(100));
    mockCrypto.subtle.decrypt.mockImplementation(async () => {
      const testData = JSON.stringify({
        accessToken: 'test-token',
        expiresAt: Date.now() + 3600000,
        issuedAt: Date.now()
      });
      return new TextEncoder().encode(testData);
    });
    
    tokenManager = SecureTokenManager.getInstance();
    tokenManager.setTelemetry(mockTelemetry);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Singleton Pattern', () => {
    it('returns the same instance', () => {
      const instance1 = SecureTokenManager.getInstance();
      const instance2 = SecureTokenManager.getInstance();
      expect(instance1).toBe(instance2);
    });
  });

  describe('Token Storage', () => {
    it('stores tokens securely', async () => {
      const tokenData: TokenData = {
        accessToken: 'test-access-token',
        refreshToken: 'test-refresh-token',
        expiresAt: Date.now() + 3600000,
        issuedAt: Date.now(),
        userId: 'user123'
      };

      await tokenManager.storeTokens(tokenData);

      expect(mockCrypto.subtle.encrypt).toHaveBeenCalled();
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'secure_tokens',
        expect.any(String)
      );
      expect(mockTrack).toHaveBeenCalledWith('tokens_stored', {
        hasRefreshToken: true,
        expiresIn: expect.any(Number),
        userId: 'user123'
      });
    });

    it('throws error for invalid token data', async () => {
      const invalidTokenData = {} as TokenData;

      await expect(tokenManager.storeTokens(invalidTokenData))
        .rejects.toThrow('Access token is required');
    });

    it('handles encryption failures', async () => {
      mockCrypto.subtle.encrypt.mockRejectedValue(new Error('Encryption failed'));

      const tokenData: TokenData = {
        accessToken: 'test-token',
        expiresAt: Date.now() + 3600000,
        issuedAt: Date.now()
      };

      await expect(tokenManager.storeTokens(tokenData))
        .rejects.toThrow('Failed to encrypt token data');
    });
  });

  describe('Token Retrieval', () => {
    it('retrieves and decrypts tokens', async () => {
      mockLocalStorage.getItem.mockReturnValue('encrypted-token-data');

      const tokens = await tokenManager.getTokens();

      expect(mockCrypto.subtle.decrypt).toHaveBeenCalled();
      expect(tokens).toEqual({
        accessToken: 'test-token',
        expiresAt: expect.any(Number),
        issuedAt: expect.any(Number)
      });
    });

    it('returns null when no tokens stored', async () => {
      mockLocalStorage.getItem.mockReturnValue(null);

      const tokens = await tokenManager.getTokens();

      expect(tokens).toBeNull();
    });

    it('handles decryption failures', async () => {
      mockLocalStorage.getItem.mockReturnValue('corrupted-data');
      mockCrypto.subtle.decrypt.mockRejectedValue(new Error('Decryption failed'));

      const tokens = await tokenManager.getTokens();

      expect(tokens).toBeNull();
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('secure_tokens');
      expect(mockTrack).toHaveBeenCalledWith('token_decryption_failed', {
        error: 'Decryption failed'
      });
    });
  });

  describe('Token Validation', () => {
    it('validates valid tokens', () => {
      const tokenData: TokenData = {
        accessToken: 'valid-token',
        expiresAt: Date.now() + 3600000,
        issuedAt: Date.now()
      };

      const validation = tokenManager.validateToken(tokenData);

      expect(validation).toEqual({
        isValid: true,
        isExpired: false,
        expiresIn: expect.any(Number),
        needsRefresh: false,
        reason: undefined
      });
    });

    it('identifies expired tokens', () => {
      const tokenData: TokenData = {
        accessToken: 'expired-token',
        expiresAt: Date.now() - 1000,
        issuedAt: Date.now() - 3600000
      };

      const validation = tokenManager.validateToken(tokenData);

      expect(validation).toEqual({
        isValid: false,
        isExpired: true,
        expiresIn: 0,
        needsRefresh: false,
        reason: 'Token expired'
      });
    });

    it('identifies tokens needing refresh', () => {
      const tokenData: TokenData = {
        accessToken: 'soon-to-expire-token',
        refreshToken: 'refresh-token',
        expiresAt: Date.now() + 60000, // 1 minute
        issuedAt: Date.now()
      };

      const validation = tokenManager.validateToken(tokenData);

      expect(validation.needsRefresh).toBe(true);
    });

    it('rejects tokens without access token', () => {
      const tokenData = {
        expiresAt: Date.now() + 3600000,
        issuedAt: Date.now()
      } as TokenData;

      const validation = tokenManager.validateToken(tokenData);

      expect(validation).toEqual({
        isValid: false,
        isExpired: false,
        expiresIn: 0,
        needsRefresh: false,
        reason: 'Missing access token'
      });
    });

    it('rejects tokens that are too old', () => {
      const tokenData: TokenData = {
        accessToken: 'old-token',
        expiresAt: Date.now() + 3600000,
        issuedAt: Date.now() - (25 * 60 * 60 * 1000) // 25 hours ago
      };

      const validation = tokenManager.validateToken(tokenData);

      expect(validation).toEqual({
        isValid: false,
        isExpired: true,
        expiresIn: 0,
        needsRefresh: false,
        reason: 'Token too old'
      });
    });
  });

  describe('Token Refresh', () => {
    it('refreshes tokens successfully', async () => {
      // Mock stored tokens
      mockLocalStorage.getItem.mockReturnValue('encrypted-token-data');
      
      // Mock successful refresh response
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          accessToken: 'new-access-token',
          refreshToken: 'new-refresh-token',
          expiresIn: 3600,
          userId: 'user123'
        })
      });

      const refreshedTokens = await tokenManager.refreshTokens('/api/auth/refresh');

      expect(mockFetch).toHaveBeenCalledWith('/api/auth/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refreshToken: 'test-token' })
      });

      expect(refreshedTokens).toEqual({
        accessToken: 'new-access-token',
        refreshToken: 'new-refresh-token',
        expiresAt: expect.any(Number),
        issuedAt: expect.any(Number),
        userId: 'user123',
        scope: undefined
      });

      expect(mockTrack).toHaveBeenCalledWith('tokens_refreshed', {
        userId: 'user123',
        expiresIn: expect.any(Number)
      });
    });

    it('handles refresh failures', async () => {
      mockLocalStorage.getItem.mockReturnValue('encrypted-token-data');
      mockFetch.mockResolvedValue({
        ok: false,
        status: 401
      });

      await expect(tokenManager.refreshTokens())
        .rejects.toThrow('Token refresh failed: 401');

      expect(mockTrack).toHaveBeenCalledWith('token_refresh_failed', {
        error: 'Token refresh failed: 401'
      });
    });

    it('prevents multiple simultaneous refresh attempts', async () => {
      mockLocalStorage.getItem.mockReturnValue('encrypted-token-data');
      mockFetch.mockImplementation(() => new Promise(resolve => {
        setTimeout(() => resolve({
          ok: true,
          json: async () => ({ accessToken: 'new-token', expiresIn: 3600 })
        }), 100);
      }));

      // Start two refresh attempts simultaneously
      const promise1 = tokenManager.refreshTokens();
      const promise2 = tokenManager.refreshTokens();

      const [result1, result2] = await Promise.all([promise1, promise2]);

      // Should be the same result (only one API call made)
      expect(result1).toEqual(result2);
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });
  });

  describe('Access Token Retrieval', () => {
    it('returns valid access token', async () => {
      mockLocalStorage.getItem.mockReturnValue('encrypted-token-data');

      const accessToken = await tokenManager.getAccessToken();

      expect(accessToken).toBe('test-token');
    });

    it('returns null for expired tokens', async () => {
      // Mock expired token
      mockCrypto.subtle.decrypt.mockImplementation(async () => {
        const expiredData = JSON.stringify({
          accessToken: 'expired-token',
          expiresAt: Date.now() - 1000,
          issuedAt: Date.now() - 3600000
        });
        return new TextEncoder().encode(expiredData);
      });

      mockLocalStorage.getItem.mockReturnValue('encrypted-token-data');

      const accessToken = await tokenManager.getAccessToken();

      expect(accessToken).toBeNull();
    });

    it('attempts refresh for tokens needing refresh', async () => {
      // Mock token needing refresh
      mockCrypto.subtle.decrypt.mockImplementation(async () => {
        const tokenData = JSON.stringify({
          accessToken: 'soon-to-expire',
          refreshToken: 'refresh-token',
          expiresAt: Date.now() + 60000, // 1 minute
          issuedAt: Date.now()
        });
        return new TextEncoder().encode(tokenData);
      });

      mockLocalStorage.getItem.mockReturnValue('encrypted-token-data');
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          accessToken: 'refreshed-token',
          expiresIn: 3600
        })
      });

      const accessToken = await tokenManager.getAccessToken();

      expect(mockFetch).toHaveBeenCalled();
      expect(accessToken).toBe('refreshed-token');
    });
  });

  describe('Token Clearing', () => {
    it('clears all tokens', async () => {
      await tokenManager.clearTokens();

      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('secure_tokens');
      expect(mockTrack).toHaveBeenCalledWith('tokens_cleared', {});
    });
  });

  describe('Authentication Status', () => {
    it('returns true when authenticated', async () => {
      mockLocalStorage.getItem.mockReturnValue('encrypted-token-data');

      const isAuth = await tokenManager.isAuthenticated();

      expect(isAuth).toBe(true);
    });

    it('returns false when not authenticated', async () => {
      mockLocalStorage.getItem.mockReturnValue(null);

      const isAuth = await tokenManager.isAuthenticated();

      expect(isAuth).toBe(false);
    });
  });

  describe('Token Info', () => {
    it('returns token information', async () => {
      mockLocalStorage.getItem.mockReturnValue('encrypted-token-data');

      const tokenInfo = await tokenManager.getTokenInfo();

      expect(tokenInfo).toEqual({
        isAuthenticated: true,
        expiresIn: expect.any(Number),
        needsRefresh: false
      });
    });

    it('returns null when no tokens', async () => {
      mockLocalStorage.getItem.mockReturnValue(null);

      const tokenInfo = await tokenManager.getTokenInfo();

      expect(tokenInfo).toBeNull();
    });
  });
});

describe('Utility Functions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (SecureTokenManager as any).instance = undefined;
  });

  describe('createAuthHeader', () => {
    it('creates authorization header with valid token', async () => {
      mockLocalStorage.getItem.mockReturnValue('encrypted-token-data');

      const header = await createAuthHeader();

      expect(header).toEqual({
        Authorization: 'Bearer test-token'
      });
    });

    it('returns empty object when no token', async () => {
      mockLocalStorage.getItem.mockReturnValue(null);

      const header = await createAuthHeader();

      expect(header).toEqual({});
    });
  });

  describe('secureApiCall', () => {
    it('makes API call with auth header', async () => {
      mockLocalStorage.getItem.mockReturnValue('encrypted-token-data');
      mockFetch.mockResolvedValue({ ok: true, status: 200 });

      await secureApiCall('/api/test');

      expect(mockFetch).toHaveBeenCalledWith('/api/test', {
        headers: {
          Authorization: 'Bearer test-token'
        }
      });
    });

    it('handles 401 responses with token refresh', async () => {
      mockLocalStorage.getItem.mockReturnValue('encrypted-token-data');
      
      // First call returns 401, second call succeeds
      mockFetch
        .mockResolvedValueOnce({ ok: false, status: 401 })
        .mockResolvedValueOnce({ ok: true, status: 200 })
        .mockResolvedValueOnce({ // For refresh call
          ok: true,
          json: async () => ({
            accessToken: 'new-token',
            expiresIn: 3600
          })
        });

      const response = await secureApiCall('/api/test');

      expect(mockFetch).toHaveBeenCalledTimes(3); // Original + refresh + retry
      expect(response.ok).toBe(true);
    });

    it('clears tokens on refresh failure', async () => {
      mockLocalStorage.getItem.mockReturnValue('encrypted-token-data');
      
      // First call returns 401, refresh fails
      mockFetch
        .mockResolvedValueOnce({ ok: false, status: 401 })
        .mockResolvedValueOnce({ ok: false, status: 401 }); // Refresh fails

      await expect(secureApiCall('/api/test'))
        .rejects.toThrow('Authentication failed');

      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('secure_tokens');
    });
  });
});