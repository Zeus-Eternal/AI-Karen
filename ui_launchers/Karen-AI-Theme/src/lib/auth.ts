/**
 * Authentication Service for Karen AI Theme
 * 
 * This service handles all authentication-related operations including
 * login, logout, token management, and user session handling.
 */

export interface LoginCredentials {
  email?: string;
  username?: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: {
    user_id: string;
    email: string;
    full_name: string;
    roles: string[];
    is_active: boolean;
    tenant_id: string;
    preferences: Record<string, any>;
    last_login?: string | null;
    permissions?: string[];
  };
  permissions: string[];
}

export interface AuthUser {
  user_id: string;
  email: string;
  full_name: string;
  roles: string[];
  is_active: boolean;
  tenant_id: string;
  preferences: Record<string, any>;
  created_at?: string;
  last_login?: string | null;
  permissions?: string[];
}

// Legacy interfaces for backward compatibility
export interface User {
  id: string;
  username: string;
  email?: string;
  role?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
}

export interface AuthResponse {
  user: User;
  tokens: AuthTokens;
}

class AuthService {
  private readonly API_BASE_URL: string;
  private readonly SESSION_COOKIE_NAME = 'kari_session';
  private readonly LEGACY_ACCESS_COOKIE_NAME = 'access_token';
  private readonly LEGACY_REFRESH_COOKIE_NAME = 'refresh_token';

  constructor() {
    this.API_BASE_URL =
      typeof window === 'undefined'
        ? process.env.NEXT_PUBLIC_KAREN_BACKEND_URL || process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
        : '';
  }

  private clearBrowserCookie(name: string): void {
    if (typeof document === 'undefined') {
      return;
    }

    document.cookie = `${name}=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax`;
  }

  private clearClientCookies(): void {
    this.clearBrowserCookie(this.SESSION_COOKIE_NAME);
    this.clearBrowserCookie(this.LEGACY_ACCESS_COOKIE_NAME);
    this.clearBrowserCookie(this.LEGACY_REFRESH_COOKIE_NAME);
  }

  private async getErrorMessage(response: Response, fallback: string): Promise<string> {
    try {
      const errorData = await response.json();

      if (typeof errorData?.detail === 'string' && errorData.detail.trim()) {
        return errorData.detail;
      }

      if (Array.isArray(errorData?.detail) && errorData.detail.length > 0) {
        return errorData.detail
          .map((issue: Record<string, unknown>) => {
            if (typeof issue?.msg === 'string' && issue.msg.trim()) {
              return issue.msg;
            }
            return null;
          })
          .filter((message: string | null): message is string => Boolean(message))
          .join(', ') || fallback;
      }

      if (typeof errorData?.message === 'string' && errorData.message.trim()) {
        return errorData.message;
      }
    } catch {
      // Fall back to the provided default message when the response is not JSON.
    }

    return fallback;
  }

  /**
   * Login user with credentials
   */
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    try {
      const response = await fetch(`${this.API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(credentials),
      });

      if (!response.ok) {
        throw new Error(await this.getErrorMessage(response, 'Login failed'));
      }

      const data: LoginResponse = await response.json();
      
      // Store tokens in localStorage
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      localStorage.setItem('user_data', JSON.stringify(data.user));

      // The backend owns the production session cookie. Clear legacy client cookies
      // so the app relies on the authenticated backend session instead.
      this.clearBrowserCookie(this.LEGACY_ACCESS_COOKIE_NAME);
      this.clearBrowserCookie(this.LEGACY_REFRESH_COOKIE_NAME);
      
      return data;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      const accessToken = localStorage.getItem('access_token');
      if (refreshToken) {
        await fetch(`${this.API_BASE_URL}/api/auth/logout`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
          },
          credentials: 'include',
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
      // Continue with cleanup even if API call fails
    } finally {
      // Clear all auth data
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user_data');

      this.clearClientCookies();
    }
  }

  /**
   * Refresh access token
   */
  async refreshToken(): Promise<string> {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await fetch(`${this.API_BASE_URL}/api/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const data = await response.json();
      localStorage.setItem('access_token', data.access_token);
      
      return data.access_token;
    } catch (error) {
      console.error('Token refresh error:', error);
      // If refresh fails, logout the user
      await this.logout();
      throw error;
    }
  }

  /**
   * Get current user data
   */
  getCurrentUser(): AuthUser | null {
    try {
      const userData = localStorage.getItem('user_data');
      return userData ? JSON.parse(userData) : null;
    } catch (error) {
      console.error('Error getting user data:', error);
      return null;
    }
  }

  /**
   * Persist current user data in local storage.
   */
  setCurrentUser(user: AuthUser | (AuthUser & Record<string, any>)): void {
    localStorage.setItem('user_data', JSON.stringify(user));
  }

  /**
   * Merge partial current user data into local storage.
   */
  updateCurrentUser(patch: Partial<AuthUser>): void {
    const currentUser = this.getCurrentUser();
    if (!currentUser) {
      return;
    }

    const nextUser: AuthUser = {
      ...currentUser,
      ...patch,
      preferences: {
        ...(currentUser.preferences || {}),
        ...(patch.preferences || {}),
      },
    };

    this.setCurrentUser(nextUser);
  }

  /**
   * Get access token
   */
  getAccessToken(): string | null {
    return localStorage.getItem('access_token');
  }

  /**
   * Get refresh token
   */
  getRefreshToken(): string | null {
    return localStorage.getItem('refresh_token');
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!this.getAccessToken() && !!this.getCurrentUser();
  }

  /**
   * Get user permissions
   */
  getUserPermissions(): string[] {
    const user = this.getCurrentUser();
    return user?.permissions || [];
  }

  /**
   * Check if user has specific permission
   */
  hasPermission(permission: string): boolean {
    const permissions = this.getUserPermissions();
    return permissions.includes(permission);
  }

  /**
   * Check if user has admin role
   */
  isAdmin(): boolean {
    const user = this.getCurrentUser();
    return user?.roles.includes('admin') || false;
  }

  /**
   * Validate current session
   */
  async validateSession(): Promise<boolean> {
    try {
      const accessToken = this.getAccessToken();
      if (!accessToken) {
        return false;
      }

      const response = await fetch(`${this.API_BASE_URL}/api/auth/validate-session`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
        credentials: 'include',
      });

      if (!response.ok) {
        // Try to refresh token if validation fails
        try {
          await this.refreshToken();
          // Retry validation with new token
          const newResponse = await fetch(`${this.API_BASE_URL}/api/auth/validate-session`, {
            method: 'GET',
            headers: {
              'Authorization': `Bearer ${this.getAccessToken()}`,
            },
            credentials: 'include',
          });
          if (!newResponse.ok) {
            return false;
          }

          const refreshedSession = await newResponse.json();
          if (refreshedSession?.user) {
            localStorage.setItem('user_data', JSON.stringify(refreshedSession.user));
          }

          return true;
        } catch (refreshError) {
          return false;
        }
      }

      const session = await response.json();
      if (session?.user) {
        localStorage.setItem('user_data', JSON.stringify(session.user));
      }

      return true;
    } catch (error) {
      console.error('Session validation error:', error);
      return false;
    }
  }

  /**
   * Clear all auth data
   */
  clearAuth(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_data');

    this.clearClientCookies();
  }

  // Backward compatibility methods
  clearAuthData(): void {
    this.clearAuth();
  }

  // Check if token is expired (simple implementation)
  isTokenExpired(token: string): boolean {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.exp < Date.now() / 1000;
    } catch {
      return true;
    }
  }

  // Auto-refresh token before expiration
  async ensureValidToken(): Promise<string> {
    const accessToken = this.getAccessToken();
    
    if (!accessToken) {
      throw new Error('No access token available');
    }

    if (this.isTokenExpired(accessToken)) {
      await this.refreshToken();
      return this.getAccessToken()!;
    }

    return accessToken;
  }

  // Legacy login method for backward compatibility
  async loginLegacy(credentials: { username: string; password: string }): Promise<AuthResponse> {
    const response = await this.login({
      username: credentials.username,
      password: credentials.password
    });

    // Convert to legacy format
    const legacyUser: User = {
      id: response.user.user_id,
      username: response.user.email, // Use email as username for backward compatibility
      email: response.user.email,
      role: response.user.roles[0] || 'user'
    };

    return {
      user: legacyUser,
      tokens: {
        access_token: response.access_token,
        refresh_token: response.refresh_token
      }
    };
  }
}

// Create singleton instance
export const authService = new AuthService();
