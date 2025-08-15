'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { SecureTokenManager, TokenData, TokenValidationResult } from '@/lib/tokenSecurity';
import { useTelemetry } from '@/hooks/use-telemetry';

interface TokenContextValue {
  isAuthenticated: boolean;
  isLoading: boolean;
  tokenInfo: {
    expiresIn: number;
    needsRefresh: boolean;
  } | null;
  storeTokens: (tokenData: TokenData) => Promise<void>;
  getAccessToken: () => Promise<string | null>;
  refreshTokens: (endpoint?: string) => Promise<TokenData | null>;
  clearTokens: () => Promise<void>;
  validateToken: (tokenData: TokenData) => TokenValidationResult;
}

const TokenContext = createContext<TokenContextValue | null>(null);

interface TokenProviderProps {
  children: React.ReactNode;
  refreshEndpoint?: string;
  autoRefresh?: boolean;
  refreshThreshold?: number; // Minutes before expiry to auto-refresh
}

export const TokenProvider: React.FC<TokenProviderProps> = ({
  children,
  refreshEndpoint = '/api/auth/refresh',
  autoRefresh = true,
  refreshThreshold = 5
}) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [tokenInfo, setTokenInfo] = useState<{
    expiresIn: number;
    needsRefresh: boolean;
  } | null>(null);

  const telemetry = useTelemetry();
  const tokenManager = SecureTokenManager.getInstance();

  // Initialize telemetry
  useEffect(() => {
    tokenManager.setTelemetry(telemetry);
  }, [telemetry]);

  // Check authentication status on mount
  useEffect(() => {
    checkAuthStatus();
  }, []);

  // Auto-refresh timer
  useEffect(() => {
    if (!autoRefresh || !tokenInfo?.needsRefresh) {
      return;
    }

    const refreshTimer = setTimeout(async () => {
      try {
        await refreshTokens(refreshEndpoint);
      } catch (error) {
        console.error('Auto-refresh failed:', error);
        telemetry.track('auto_refresh_failed', {
          error: error instanceof Error ? error.message : 'Unknown error'
        });
      }
    }, Math.max(1000, tokenInfo.expiresIn - (refreshThreshold * 60 * 1000)));

    return () => clearTimeout(refreshTimer);
  }, [tokenInfo, autoRefresh, refreshThreshold, refreshEndpoint]);

  const checkAuthStatus = useCallback(async () => {
    try {
      setIsLoading(true);
      const info = await tokenManager.getTokenInfo();
      
      if (info) {
        setIsAuthenticated(info.isAuthenticated);
        setTokenInfo({
          expiresIn: info.expiresIn,
          needsRefresh: info.needsRefresh
        });
      } else {
        setIsAuthenticated(false);
        setTokenInfo(null);
      }
    } catch (error) {
      console.error('Auth status check failed:', error);
      setIsAuthenticated(false);
      setTokenInfo(null);
    } finally {
      setIsLoading(false);
    }
  }, [tokenManager]);

  const storeTokens = useCallback(async (tokenData: TokenData) => {
    try {
      await tokenManager.storeTokens(tokenData);
      await checkAuthStatus();
      
      telemetry.track('tokens_stored_via_context', {
        userId: tokenData.userId,
        hasRefreshToken: !!tokenData.refreshToken
      });
    } catch (error) {
      telemetry.track('token_storage_context_failed', {
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      throw error;
    }
  }, [tokenManager, checkAuthStatus, telemetry]);

  const getAccessToken = useCallback(async () => {
    try {
      const token = await tokenManager.getAccessToken();
      
      // Update auth status if token retrieval changed it
      if (!token && isAuthenticated) {
        await checkAuthStatus();
      }
      
      return token;
    } catch (error) {
      telemetry.track('access_token_context_failed', {
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      return null;
    }
  }, [tokenManager, isAuthenticated, checkAuthStatus, telemetry]);

  const refreshTokens = useCallback(async (endpoint?: string) => {
    try {
      const refreshedTokens = await tokenManager.refreshTokens(endpoint || refreshEndpoint);
      
      if (refreshedTokens) {
        await checkAuthStatus();
        telemetry.track('tokens_refreshed_via_context', {
          userId: refreshedTokens.userId
        });
      }
      
      return refreshedTokens;
    } catch (error) {
      telemetry.track('token_refresh_context_failed', {
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      
      // Clear tokens on refresh failure
      await clearTokens();
      throw error;
    }
  }, [tokenManager, refreshEndpoint, checkAuthStatus, telemetry]);

  const clearTokens = useCallback(async () => {
    try {
      await tokenManager.clearTokens();
      setIsAuthenticated(false);
      setTokenInfo(null);
      
      telemetry.track('tokens_cleared_via_context', {});
    } catch (error) {
      telemetry.track('token_clear_context_failed', {
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  }, [tokenManager, telemetry]);

  const validateToken = useCallback((tokenData: TokenData) => {
    return tokenManager.validateToken(tokenData);
  }, [tokenManager]);

  const contextValue: TokenContextValue = {
    isAuthenticated,
    isLoading,
    tokenInfo,
    storeTokens,
    getAccessToken,
    refreshTokens,
    clearTokens,
    validateToken
  };

  return (
    <TokenContext.Provider value={contextValue}>
      {children}
    </TokenContext.Provider>
  );
};

export const useTokens = (): TokenContextValue => {
  const context = useContext(TokenContext);
  
  if (!context) {
    throw new Error('useTokens must be used within a TokenProvider');
  }
  
  return context;
};

// Higher-order component for protecting routes
export const withTokenProtection = <P extends object>(
  Component: React.ComponentType<P>,
  options: {
    redirectTo?: string;
    fallback?: React.ComponentType;
    requireAuth?: boolean;
  } = {}
) => {
  const {
    redirectTo = '/login',
    fallback: Fallback,
    requireAuth = true
  } = options;

  return function ProtectedComponent(props: P) {
    const { isAuthenticated, isLoading } = useTokens();

    if (isLoading) {
      return Fallback ? <Fallback /> : <div>Loading...</div>;
    }

    if (requireAuth && !isAuthenticated) {
      // In a real app, you'd use your router's redirect mechanism
      if (typeof window !== 'undefined') {
        window.location.href = redirectTo;
      }
      return Fallback ? <Fallback /> : <div>Redirecting to login...</div>;
    }

    return <Component {...props} />;
  };
};

// Hook for automatic token refresh
export const useAutoRefresh = (
  options: {
    enabled?: boolean;
    threshold?: number; // Minutes before expiry
    onRefreshSuccess?: (tokens: TokenData) => void;
    onRefreshError?: (error: Error) => void;
  } = {}
) => {
  const {
    enabled = true,
    threshold = 5,
    onRefreshSuccess,
    onRefreshError
  } = options;

  const { tokenInfo, refreshTokens } = useTokens();
  const telemetry = useTelemetry();

  useEffect(() => {
    if (!enabled || !tokenInfo?.needsRefresh) {
      return;
    }

    const thresholdMs = threshold * 60 * 1000;
    const refreshTime = Math.max(1000, tokenInfo.expiresIn - thresholdMs);

    const timer = setTimeout(async () => {
      try {
        const refreshedTokens = await refreshTokens();
        if (refreshedTokens) {
          onRefreshSuccess?.(refreshedTokens);
          telemetry.track('auto_refresh_success', {
            userId: refreshedTokens.userId
          });
        }
      } catch (error) {
        const err = error instanceof Error ? error : new Error('Unknown error');
        onRefreshError?.(err);
        telemetry.track('auto_refresh_error', {
          error: err.message
        });
      }
    }, refreshTime);

    return () => clearTimeout(timer);
  }, [enabled, threshold, tokenInfo, refreshTokens, onRefreshSuccess, onRefreshError, telemetry]);
};

export default TokenContext;