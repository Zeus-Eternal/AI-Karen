import { LoginCredentials, LoginResponse, User } from '@/types/auth';
import { enhancedApiClient } from '@/lib/enhanced-api-client';
import { getServiceErrorHandler } from './errorHandler';

const normalizeError = (error: unknown): Error => {
  return error instanceof Error ? error : new Error(typeof error === 'string' ? error : 'Unknown error');
};
export class AuthService {
  private apiClient = enhancedApiClient;
  private errorHandler = getServiceErrorHandler();
  constructor() {
    // API client handles all endpoint configuration automatically
  }
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    try {
      const response = await this.apiClient.post<LoginResponse>(
        '/api/auth/login',
        credentials
      );
      return response.data;
    } catch (error: unknown) {
      const normalizedError = normalizeError(error);
      const serviceError = this.errorHandler.handleError(normalizedError, {
        service: 'AuthService',
        method: 'login',
        endpoint: '/api/auth/login',
      });

      // Throw user-friendly error message
      throw new Error(serviceError.userMessage);
    }
  }
  async setupTwoFactor(): Promise<{ otpauth_url: string }> {
    try {
      const response = await this.apiClient.get<{ otpauth_url: string }>(
        '/api/auth/setup_2fa'
      );
      return response.data;
    } catch (error: unknown) {
      throw new Error(`Failed to start 2FA setup: ${normalizeError(error).message}`);
    }
  }
  async confirmTwoFactor(code: string): Promise<void> {
    try {
      await this.apiClient.post('/api/auth/confirm_2fa', { code });
    } catch (error: unknown) {
      throw new Error(`Failed to enable 2FA: ${normalizeError(error).message}`);
    }
  }
  async register(credentials: LoginCredentials): Promise<LoginResponse> {
    try {
      const response = await this.apiClient.post<LoginResponse>(
        '/api/auth/register',
        credentials
      );
      return response.data;
    } catch (error: unknown) {
      throw new Error(`Register failed: ${normalizeError(error).message}`);
    }
  }
  async getCurrentUser(): Promise<User> {
    try {
      const response = await this.apiClient.get<User>('/api/auth/me');
      return response.data;
    } catch (error: unknown) {
      const err = error as { status?: number; isNetworkError?: boolean; isTimeoutError?: boolean; message?: string };
      // Handle authentication errors specifically
      if (err.status === 401) {
        // User is not authenticated - this is expected behavior, not an error
        throw new Error('Not authenticated');
      } else if (err.status === 403) {
        // User is authenticated but not authorized
        throw new Error('Access forbidden');
      } else if (err.isNetworkError) {
        // Actual network connectivity issue
        throw new Error('Network error. Please check your connection and try again.');
      } else if (err.isTimeoutError) {
        // Request timeout
        throw new Error('Request timeout. Please try again.');
      } else {
        // Other server errors
        throw new Error(`Server error: ${err.message || 'Unknown error'}`);
      }
    }
  }
  async updateCredentials(newUsername?: string, newPassword?: string): Promise<LoginResponse> {
    try {
      const response = await this.apiClient.post<LoginResponse>(
        '/api/auth/update_credentials',
        {
          new_username: newUsername,
          new_password: newPassword,
        }
      );

      return response.data;
    } catch (error: unknown) {
      throw new Error(`Failed to update credentials: ${normalizeError(error).message}`);
    }
  }
  async updateUserPreferences(_token: string, preferences: unknown): Promise<void> {
    try {
      await this.apiClient.put('/api/users/me/preferences', preferences);
    } catch (error: unknown) {
      throw new Error(`Failed to update preferences: ${normalizeError(error).message}`);
    }
  }
  async uploadAvatar(file: File): Promise<string> {
    try {
      const response = await this.apiClient.upload<{ avatar_url: string }>('/api/users/me/avatar', file);
      return response.data.avatar_url;
    } catch (error: unknown) {
      throw new Error(`Failed to upload avatar: ${normalizeError(error).message}`);
    }
  }
  async logout(): Promise<void> {
    try {
      await this.apiClient.post('/api/auth/logout');
    } catch {
      // Logout should not throw errors, just log them
    }
  }
  async requestPasswordReset(email: string): Promise<void> {
    try {
      await this.apiClient.post('/api/auth/request_password_reset', { email });
    } catch (error: unknown) {
      throw new Error(`Failed to request password reset: ${normalizeError(error).message}`);
    }
  }
  async resetPassword(token: string, newPassword: string): Promise<void> {
    try {
      await this.apiClient.post('/api/auth/reset_password', { 
        token, 
        new_password: newPassword 
      });

    } catch (error: unknown) {
      throw new Error(`Failed to reset password: ${normalizeError(error).message}`);
    }
  }
  // Token and user persistence removed for HttpOnly cookie approach
  saveToken(_: string): void {}
  getToken(): string | null { return null; }
  removeToken(): void {}
  saveUser(_: User): void {}
  getUser(): User | null { return null; }
  removeUser(): void {}
}
export const authService = new AuthService();
// Global instance used by hooks that rely on lazy initialization
let authServiceInstance: AuthService | null = null;
export function getAuthService(): AuthService {
  if (!authServiceInstance) {
    authServiceInstance = new AuthService();
  }
  return authServiceInstance;
}
export function initializeAuthService(): AuthService {
  authServiceInstance = new AuthService();
  return authServiceInstance;
}
