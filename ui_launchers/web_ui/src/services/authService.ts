import { LoginCredentials, LoginResponse, User } from '@/types/auth';
import { getApiClient } from '@/lib/api-client';

export class AuthService {
  private apiClient = getApiClient();

  constructor() {
    // API client handles all endpoint configuration automatically
  }

  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    try {
      const response = await this.apiClient.post('/api/auth/login', credentials);
      return response.data;
    } catch (error: any) {
      // Handle different types of errors appropriately
      if (error.isNetworkError) {
        throw new Error('Network error. Please check your connection and try again.');
      } else if (error.isTimeoutError) {
        throw new Error('Request timeout. Please try again.');
      } else if (error.status === 401) {
        // Invalid credentials
        throw new Error('Invalid email or password');
      } else if (error.status === 403) {
        // Account issues (not verified, locked, etc.)
        throw new Error('Account access denied. Please check your email for verification or contact support.');
      } else if (error.status === 429) {
        // Rate limiting
        throw new Error('Too many login attempts. Please wait a moment and try again.');
      } else if (error.status >= 500) {
        // Server errors
        throw new Error('Server error. Please try again later or contact support.');
      } else {
        // Try to extract specific error message from response
        let message = 'Login failed';
        if (error.originalError && typeof error.originalError === 'object') {
          message = error.originalError.detail || error.message || message;
        } else if (error.message) {
          message = error.message;
        }
        throw new Error(message);
      }
    }
  }

  async setupTwoFactor(): Promise<{ otpauth_url: string }> {
    try {
      const response = await this.apiClient.get('/api/auth/setup_2fa');
      return response.data;
    } catch (error: any) {
      throw new Error(`Failed to start 2FA setup: ${error.message}`);
    }
  }

  async confirmTwoFactor(code: string): Promise<void> {
    try {
      await this.apiClient.post('/api/auth/confirm_2fa', { code });
    } catch (error: any) {
      throw new Error(`Failed to enable 2FA: ${error.message}`);
    }
  }

  async register(credentials: LoginCredentials): Promise<LoginResponse> {
    try {
      const response = await this.apiClient.post('/api/auth/register', credentials);
      return response.data;
    } catch (error: any) {
      throw new Error(`Register failed: ${error.message}`);
    }
  }

  async getCurrentUser(): Promise<User> {
    try {
      const response = await this.apiClient.get('/api/auth/me');
      return response.data;
    } catch (error: any) {
      // Handle authentication errors specifically
      if (error.status === 401) {
        // User is not authenticated - this is expected behavior, not an error
        throw new Error('Not authenticated');
      } else if (error.status === 403) {
        // User is authenticated but not authorized
        throw new Error('Access forbidden');
      } else if (error.isNetworkError) {
        // Actual network connectivity issue
        throw new Error('Network error. Please check your connection and try again.');
      } else if (error.isTimeoutError) {
        // Request timeout
        throw new Error('Request timeout. Please try again.');
      } else {
        // Other server errors
        throw new Error(`Server error: ${error.message}`);
      }
    }
  }

  async updateCredentials(newUsername?: string, newPassword?: string): Promise<LoginResponse> {
    try {
      const response = await this.apiClient.post('/api/auth/update_credentials', {
        new_username: newUsername,
        new_password: newPassword,
      });
      return response.data;
    } catch (error: any) {
      throw new Error(`Failed to update credentials: ${error.message}`);
    }
  }

  async updateUserPreferences(_token: string, preferences: Partial<User['preferences']>): Promise<void> {
    try {
      await this.apiClient.put('/api/users/me/preferences', preferences);
    } catch (error: any) {
      throw new Error(`Failed to update preferences: ${error.message}`);
    }
  }

  async uploadAvatar(file: File): Promise<string> {
    try {
      const response = await this.apiClient.uploadFile('/api/users/me/avatar', file);
      return response.data.avatar_url as string;
    } catch (error: any) {
      throw new Error(`Failed to upload avatar: ${error.message}`);
    }
  }

  async logout(): Promise<void> {
    try {
      await this.apiClient.post('/api/auth/logout');
    } catch (error) {
      // Logout should not throw errors, just log them
      console.warn('Logout request failed:', error);
    }
  }

  async requestPasswordReset(email: string): Promise<void> {
    try {
      await this.apiClient.post('/api/auth/request_password_reset', { email });
    } catch (error: any) {
      throw new Error(`Failed to request password reset: ${error.message}`);
    }
  }

  async resetPassword(token: string, newPassword: string): Promise<void> {
    try {
      await this.apiClient.post('/api/auth/reset_password', { 
        token, 
        new_password: newPassword 
      });
    } catch (error: any) {
      throw new Error(`Failed to reset password: ${error.message}`);
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


