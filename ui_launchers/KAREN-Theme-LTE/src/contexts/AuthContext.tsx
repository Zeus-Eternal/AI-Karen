"use client";

import { createContext, useContext, useEffect, useState, useRef } from 'react';
import { type User, type AuthState, type LoginCredentials, type AuthResponse } from '@/types/auth';
import { verifyToken } from '@/lib/jwt';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  authState: AuthState;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<boolean>;
  refreshSession: () => Promise<boolean>;
  clearError: () => void;
  hasRole: (role: string) => boolean;
  hasPermission: (permission: string) => boolean;
  isAdmin: () => boolean;
  isSuperAdmin: () => boolean;
  isLoggingIn: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [isClient, setIsClient] = useState(false);
  const isMountedRef = useRef(false); // Track if component is mounted
  const [authState, setAuthState] = useState<AuthState>({
    isLoading: false,
    error: null,
    isRefreshing: false,
    lastActivity: null
  });

  useEffect(() => {
    setIsClient(true);
    // Run checkAuth once on mount
    checkAuth();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty dependency array - run once on mount

  const login = async (credentials: LoginCredentials) => {
    setIsLoggingIn(true);
    setAuthState((prev: AuthState) => ({ ...prev, isLoading: true, error: null }));

    try {
      // Use backend URL from environment variable for API calls
      const backendUrl = process.env.NEXT_PUBLIC_KAREN_BACKEND_URL || 'http://localhost:8000';
      const response = await fetch(`${backendUrl}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Login failed');
      }

      const data: AuthResponse = await response.json();

      if (data.success && data.user) {
        setUser(data.user);
        setIsAuthenticated(true);
        setAuthState((prev: AuthState) => ({
          ...prev,
          isLoading: false,
          lastActivity: new Date(),
          error: null
        }));
      } else {
        throw new Error(data.error || 'Login failed');
      }
    } catch (error) {
      setAuthState((prev: AuthState) => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Login failed'
      }));
    } finally {
      setIsLoggingIn(false);
    }
  };

  const logout = () => {
    // Clear the auth cookie
    if (isClient) {
      document.cookie = 'token=; Path=/; Max-Age=0';
    }
    
    setUser(null);
    setIsAuthenticated(false);
    setAuthState({
      isLoading: false,
      error: null,
      isRefreshing: false,
      lastActivity: null
    });
  };

  const checkAuth = async (): Promise<boolean> => {
    if (!isClient) return false;
    if (isMountedRef.current) return false; // Prevent multiple calls
    
    isMountedRef.current = true; // Mark as called
    
    setAuthState((prev: AuthState) => ({ ...prev, isLoading: true }));

    try {
      // Check if there's a token in cookies
      const cookies = document.cookie.split(';').reduce((acc, cookie) => {
        const [key, value] = cookie.trim().split('=');
        if (key && value) {
          acc[key] = value;
        }
        return acc;
      }, {} as Record<string, string>);

      const token = cookies.token;

      if (!token) {
        setUser(null);
        setIsAuthenticated(false);
        setAuthState(prev => ({ ...prev, isLoading: false }));
        return false;
      }

      // Verify the token
      const payload = verifyToken(token);
      
      if (payload) {
        // Create user object from token payload
        const user: User = {
          userId: payload.userId,
          email: payload.email,
          roles: payload.roles,
          profile: {
            firstName: 'Test',
            lastName: 'User'
          }
        };

        setUser(user);
        setIsAuthenticated(true);
        setAuthState((prev: AuthState) => ({
          ...prev,
          isLoading: false,
          lastActivity: new Date()
        }));
        return true;
      } else {
        // Token is invalid, clear it
        document.cookie = 'token=; Path=/; Max-Age=0';
        setUser(null);
        setIsAuthenticated(false);
        setAuthState(prev => ({ ...prev, isLoading: false }));
        return false;
      }
    } catch (error) {
      setAuthState((prev: AuthState) => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Auth check failed'
      }));
      return false;
    }
  };

  const refreshSession = async (): Promise<boolean> => {
    setAuthState((prev: AuthState) => ({ ...prev, isRefreshing: true }));

    try {
      // Simulate refreshing session
      await new Promise(resolve => setTimeout(resolve, 500));
      
      setAuthState((prev: AuthState) => ({ ...prev, isRefreshing: false, lastActivity: new Date() }));
      return true;
    } catch (error) {
      setAuthState((prev: AuthState) => ({
        ...prev,
        isRefreshing: false,
        error: error instanceof Error ? error.message : 'Session refresh failed'
      }));
      return false;
    }
  };

  const clearError = () => {
    setAuthState((prev: AuthState) => ({ ...prev, error: null }));
  };

  const hasRole = (role: string): boolean => {
    return user?.roles?.includes(role) ?? false;
  };

  const hasPermission = (permission: string): boolean => {
    return user?.permissions?.includes(permission) ?? false;
  };

  const isAdmin = (): boolean => {
    return hasRole('admin') || hasRole('super_admin');
  };

  const isSuperAdmin = (): boolean => {
    return hasRole('super_admin');
  };

  const value: AuthContextType = {
    user,
    isAuthenticated,
    authState,
    login,
    logout,
    checkAuth,
    refreshSession,
    clearError,
    hasRole,
    hasPermission,
    isAdmin,
    isSuperAdmin,
    isLoggingIn
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
