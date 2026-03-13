/**
 * Security Context Provider for the CoPilot frontend.
 * 
 * This context provides authentication, authorization, and security
 * functionality throughout the application.
 */

import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { 
  AuthState, 
  User, 
  AuthTokens, 
  LoginRequest, 
  LoginResponse, 
  RegisterRequest, 
  RegisterResponse,
  MfaMethod,
  MfaSetupRequest,
  MfaSetupResponse,
  MfaVerifyRequest,
  MfaVerifyResponse,
  DeviceInfo,
  SecurityEvent,
  VulnerabilityScan,
  PasswordChangeForm,
  ProfileForm,
  SecurityContext as ISecurityContext
} from '../types';
import { securityApi, SecurityApiError } from '../services/securityApi';

// Action types
type SecurityAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_USER'; payload: User | null }
  | { type: 'SET_TOKENS'; payload: AuthTokens | null }
  | { type: 'SET_AUTHENTICATED'; payload: boolean }
  | { type: 'SET_LAST_ACTIVITY'; payload: string }
  | { type: 'SET_SESSION_TIMEOUT'; payload: number }
  | { type: 'LOGOUT' }
  | { type: 'CLEAR_ERROR' }
  | { type: 'UPDATE_USER'; payload: Partial<User> };

// Initial state
const initialState: AuthState = {
  user: null,
  tokens: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
  lastActivity: new Date().toISOString(),
  sessionTimeout: 30 * 60 * 1000, // 30 minutes
};

// Reducer
const securityReducer = (state: AuthState, action: SecurityAction): AuthState => {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload, isLoading: false };
    case 'SET_USER':
      return { ...state, user: action.payload };
    case 'SET_TOKENS':
      return { ...state, tokens: action.payload };
    case 'SET_AUTHENTICATED':
      return { ...state, isAuthenticated: action.payload };
    case 'SET_LAST_ACTIVITY':
      return { ...state, lastActivity: action.payload };
    case 'SET_SESSION_TIMEOUT':
      return { ...state, sessionTimeout: action.payload };
    case 'LOGOUT':
      return {
        ...initialState,
        isLoading: false,
      };
    case 'CLEAR_ERROR':
      return { ...state, error: null };
    case 'UPDATE_USER':
      return {
        ...state,
        user: state.user ? { ...state.user, ...action.payload } : null,
      };
    default:
      return state;
  }
};

// Context
const SecurityContext = createContext<ISecurityContext | null>(null);

// Provider props
interface SecurityProviderProps {
  children: ReactNode;
  sessionTimeout?: number;
  autoRefresh?: boolean;
  refreshThreshold?: number;
}

// Provider component
export const SecurityProvider: React.FC<SecurityProviderProps> = ({
  children,
  sessionTimeout = 30 * 60 * 1000, // 30 minutes
  autoRefresh = true,
  refreshThreshold = 5 * 60 * 1000, // 5 minutes
}) => {
  const [state, dispatch] = useReducer(securityReducer, initialState);
  const [isClient, setIsClient] = React.useState(false);
  const refreshTimerRef = React.useRef<NodeJS.Timeout | null>(null);
  const sessionTimerRef = React.useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    setIsClient(true);
  }, []);

  // Initialize auth state from storage
  useEffect(() => {
    if (!isClient) return;

    const initializeAuth = async () => {
      try {
        if (typeof window !== 'undefined') {
          const tokens = localStorage.getItem('auth_tokens');
          const lastActivity = localStorage.getItem('auth_last_activity');

          const clearStoredAuth = () => {
            localStorage.removeItem('auth_tokens');
            localStorage.removeItem('auth_last_activity');

            if (refreshTimerRef.current) {
              clearTimeout(refreshTimerRef.current);
            }

            if (sessionTimerRef.current) {
              clearTimeout(sessionTimerRef.current);
            }

            dispatch({ type: 'LOGOUT' });
          };
          
          if (tokens && lastActivity) {
            const parsedTokens = JSON.parse(tokens);
            const parsedLastActivity = JSON.parse(lastActivity);
            
            // Check if session is still valid
            const now = new Date().getTime();
            const activityTime = new Date(parsedLastActivity).getTime();
            
            if (now - activityTime < sessionTimeout) {
              dispatch({ type: 'SET_TOKENS', payload: parsedTokens });
              dispatch({ type: 'SET_LAST_ACTIVITY', payload: parsedLastActivity });
              dispatch({ type: 'SET_SESSION_TIMEOUT', payload: sessionTimeout });
              
              // Get current user
              try {
                const userResponse = await securityApi.auth.getCurrentUser();

                if (userResponse.success && userResponse.data) {
                  dispatch({ type: 'SET_USER', payload: userResponse.data });
                  dispatch({ type: 'SET_AUTHENTICATED', payload: true });
                }
              } catch (userError) {
                console.error('Error getting current user during initialization:', userError);
                clearStoredAuth();
                return;
              }
              
              // Setup auto refresh
              if (autoRefresh) {
                if (refreshTimerRef.current) {
                  clearTimeout(refreshTimerRef.current);
                }

                const refreshTime = parsedTokens.expiresIn * 1000 - refreshThreshold;
                refreshTimerRef.current = setTimeout(async () => {
                  try {
                    const refreshed = await securityApi.auth.refreshToken(parsedTokens.refreshToken);

                    if (refreshed.success && refreshed.data) {
                      localStorage.setItem('auth_tokens', JSON.stringify(refreshed.data));
                      dispatch({ type: 'SET_TOKENS', payload: refreshed.data });
                    } else {
                      clearStoredAuth();
                    }
                  } catch (refreshError) {
                    console.error('Error refreshing token:', refreshError);
                    clearStoredAuth();
                  }
                }, refreshTime);
              }
              
              // Setup session timeout
              if (sessionTimerRef.current) {
                clearTimeout(sessionTimerRef.current);
              }

              sessionTimerRef.current = setTimeout(() => {
                clearStoredAuth();
              }, sessionTimeout);
            } else {
              // Session expired, clean up
              clearStoredAuth();
            }
          }
        }
      } catch (error) {
        console.error('Error initializing auth:', error);
        if (typeof window !== 'undefined') {
          localStorage.removeItem('auth_tokens');
          localStorage.removeItem('auth_last_activity');
        }
        dispatch({ type: 'LOGOUT' });
      } finally {
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    };

    initializeAuth();
  }, [sessionTimeout, autoRefresh, refreshThreshold, isClient]);

  // Setup auto refresh timer
  const setupAutoRefresh = (tokens: AuthTokens) => {
    if (refreshTimerRef.current) {
      clearTimeout(refreshTimerRef.current);
    }

    const refreshTime = tokens.expiresIn * 1000 - refreshThreshold;
    
    refreshTimerRef.current = setTimeout(async () => {
      try {
        await refreshToken();
      } catch (error) {
        console.error('Error refreshing token:', error);
        logout();
      }
    }, refreshTime);
  };

  // Setup session timeout timer
  const setupSessionTimeout = () => {
    if (sessionTimerRef.current) {
      clearTimeout(sessionTimerRef.current);
    }

    sessionTimerRef.current = setTimeout(() => {
      logout();
    }, sessionTimeout);
  };

  // Update last activity
  const updateLastActivity = () => {
    const now = new Date().toISOString();
    dispatch({ type: 'SET_LAST_ACTIVITY', payload: now });
    
    if (isClient && typeof window !== 'undefined') {
      localStorage.setItem('auth_last_activity', JSON.stringify(now));
    }
    
    // Reset session timeout
    setupSessionTimeout();
  };

  // Store tokens securely
  const storeTokens = (tokens: AuthTokens) => {
    if (isClient && typeof window !== 'undefined') {
      localStorage.setItem('auth_tokens', JSON.stringify(tokens));
    }
    dispatch({ type: 'SET_TOKENS', payload: tokens });
  };

  // Clean up auth data
  const cleanupAuth = () => {
    if (isClient && typeof window !== 'undefined') {
      localStorage.removeItem('auth_tokens');
      localStorage.removeItem('auth_last_activity');
    }
    
    if (refreshTimerRef.current) {
      clearTimeout(refreshTimerRef.current);
    }
    
    if (sessionTimerRef.current) {
      clearTimeout(sessionTimerRef.current);
    }
    
    dispatch({ type: 'LOGOUT' });
  };

  // Get current user
  const getCurrentUser = async (): Promise<User | null> => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'CLEAR_ERROR' });
      
      const response = await securityApi.auth.getCurrentUser();
      
      if (response.success && response.data) {
        dispatch({ type: 'SET_USER', payload: response.data });
        dispatch({ type: 'SET_AUTHENTICATED', payload: true });
        return response.data;
      }
      
      return null;
    } catch (error) {
      const errorMessage = error instanceof SecurityApiError ? error.message : 'Failed to get user';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      return null;
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  // Login
  const login = async (credentials: LoginRequest): Promise<LoginResponse> => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'CLEAR_ERROR' });
      
      const response = await securityApi.auth.login(credentials);
      
      if (response.success && response.data) {
        const { user, tokens, requiresMfa } = response.data;
        
        if (!requiresMfa) {
          // Store tokens and set auth state
          storeTokens(tokens);
          dispatch({ type: 'SET_USER', payload: user });
          dispatch({ type: 'SET_AUTHENTICATED', payload: true });
          updateLastActivity();
          
          // Setup auto refresh
          if (autoRefresh) {
            setupAutoRefresh(tokens);
          }
          
          // Setup session timeout
          setupSessionTimeout();
        }
        
        return response.data;
      }
      
      throw new Error('Login failed');
    } catch (error) {
      const errorMessage = error instanceof SecurityApiError ? error.message : 'Login failed';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      throw error;
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  // Logout
  const logout = async (): Promise<void> => {
    try {
      // Call logout API
      await securityApi.auth.logout();
    } catch (error) {
      console.error('Error during logout:', error);
    } finally {
      // Clean up local state regardless of API call success
      cleanupAuth();
    }
  };

  // Register
  const register = async (userData: RegisterRequest): Promise<RegisterResponse> => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'CLEAR_ERROR' });
      
      const response = await securityApi.auth.register(userData);
      
      if (response.success && response.data) {
        return response.data;
      }
      
      throw new Error('Registration failed');
    } catch (error) {
      const errorMessage = error instanceof SecurityApiError ? error.message : 'Registration failed';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      throw error;
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  // Refresh token
  const refreshToken = async (): Promise<AuthTokens> => {
    try {
      const currentTokens = state.tokens;
      
      if (!currentTokens) {
        throw new Error('No refresh token available');
      }
      
      const response = await securityApi.auth.refreshToken(currentTokens.refreshToken);
      
      if (response.success && response.data) {
        storeTokens(response.data);
        
        // Setup auto refresh for new tokens
        if (autoRefresh) {
          setupAutoRefresh(response.data);
        }
        
        return response.data;
      }
      
      throw new Error('Token refresh failed');
    } catch (error) {
      console.error('Error refreshing token:', error);
      logout();
      throw error;
    }
  };

  // Change password
  const changePassword = async (passwordData: PasswordChangeForm): Promise<void> => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'CLEAR_ERROR' });
      
      await securityApi.auth.changePassword(passwordData);
    } catch (error) {
      const errorMessage = error instanceof SecurityApiError ? error.message : 'Password change failed';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      throw error;
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  // Update profile
  const updateProfile = async (profileData: ProfileForm): Promise<User> => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'CLEAR_ERROR' });
      
      const response = await securityApi.auth.updateProfile(profileData);
      
      if (response.success && response.data) {
        dispatch({ type: 'UPDATE_USER', payload: response.data });
        return response.data;
      }
      
      throw new Error('Profile update failed');
    } catch (error) {
      const errorMessage = error instanceof SecurityApiError ? error.message : 'Profile update failed';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      throw error;
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  // Enable MFA
  const enableMfa = async (method: MfaMethod): Promise<MfaSetupResponse> => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'CLEAR_ERROR' });
      
      const setupData: MfaSetupRequest = { method };
      const response = await securityApi.mfa.setupMfa(setupData);
      
      if (response.success && response.data) {
        return response.data;
      }
      
      throw new Error('MFA setup failed');
    } catch (error) {
      const errorMessage = error instanceof SecurityApiError ? error.message : 'MFA setup failed';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      throw error;
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  // Disable MFA
  const disableMfa = async (): Promise<void> => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'CLEAR_ERROR' });
      
      await securityApi.mfa.disableMfa('');
      
      // Update user state
      if (state.user) {
        dispatch({ type: 'UPDATE_USER', payload: { isMfaEnabled: false } });
      }
    } catch (error) {
      const errorMessage = error instanceof SecurityApiError ? error.message : 'MFA disable failed';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      throw error;
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  // Verify MFA
  const verifyMfa = async (verifyData: MfaVerifyRequest): Promise<MfaVerifyResponse> => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'CLEAR_ERROR' });
      
      const response = await securityApi.mfa.verifyMfaSetup(verifyData);
      
      if (response.success && response.data) {
        // Update user state
        if (state.user) {
          dispatch({ type: 'UPDATE_USER', payload: { isMfaEnabled: true } });
        }
        return response.data;
      }
      
      throw new Error('MFA verification failed');
    } catch (error) {
      const errorMessage = error instanceof SecurityApiError ? error.message : 'MFA verification failed';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      throw error;
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  // Trust device
  const trustDevice = async (deviceId: string): Promise<void> => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'CLEAR_ERROR' });
      
      await securityApi.device.trustDevice(deviceId);
    } catch (error) {
      const errorMessage = error instanceof SecurityApiError ? error.message : 'Device trust failed';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      throw error;
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  // Revoke device
  const revokeDevice = async (deviceId: string): Promise<void> => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'CLEAR_ERROR' });
      
      await securityApi.device.revokeDevice(deviceId);
    } catch (error) {
      const errorMessage = error instanceof SecurityApiError ? error.message : 'Device revoke failed';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      throw error;
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  // Get security events
  const getSecurityEvents = async (): Promise<SecurityEvent[]> => {
    try {
      const response = await securityApi.monitoring.getSecurityEvents();
      
      if (response.success && response.data) {
        return response.data.items;
      }
      
      return [];
    } catch (error) {
      console.error('Error getting security events:', error);
      return [];
    }
  };

  // Get devices
  const getDevices = async (): Promise<DeviceInfo[]> => {
    try {
      const response = await securityApi.device.getDevices();
      
      if (response.success && response.data) {
        return response.data;
      }
      
      return [];
    } catch (error) {
      console.error('Error getting devices:', error);
      return [];
    }
  };

  // Get vulnerability scans
  const getVulnerabilityScans = async (): Promise<VulnerabilityScan[]> => {
    try {
      const response = await securityApi.vulnerability.getVulnerabilityScans();
      
      if (response.success && response.data) {
        return response.data.items;
      }
      
      return [];
    } catch (error) {
      console.error('Error getting vulnerability scans:', error);
      return [];
    }
  };

  // Permission and role checks
  const hasPermission = (permission: string): boolean => {
    return state.user?.permissions.includes(permission) || false;
  };

  const hasRole = (role: string): boolean => {
    return state.user?.roles.includes(role) || false;
  };

  const hasAnyPermission = (permissions: string[]): boolean => {
    if (!state.user?.permissions) return false;
    return permissions.some(permission => state.user!.permissions.includes(permission));
  };

  const hasAnyRole = (roles: string[]): boolean => {
    if (!state.user?.roles) return false;
    return roles.some(role => state.user!.roles.includes(role));
  };

  // Context value
  const contextValue: ISecurityContext = {
    auth: state,
    user: state.user,
    permissions: state.user?.permissions || [],
    roles: state.user?.roles || [],
    hasPermission,
    hasRole,
    hasAnyPermission,
    hasAnyRole,
    login,
    logout,
    register,
    refreshToken,
    changePassword,
    updateProfile,
    enableMfa,
    disableMfa,
    verifyMfa,
    trustDevice,
    revokeDevice,
    getSecurityEvents,
    getDevices,
    getVulnerabilityScans,
  };

  return (
    <SecurityContext.Provider value={contextValue}>
      {children}
    </SecurityContext.Provider>
  );
};

// Hook to use security context
export const useSecurity = (): ISecurityContext => {
  const context = useContext(SecurityContext);
  
  if (!context) {
    throw new Error('useSecurity must be used within a SecurityProvider');
  }
  
  return context;
};

// Export context for direct access
export { SecurityContext };
