import { LoginCredentials, LoginResponse, User } from '@/types/auth';

export class AuthService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  }

  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    const response = await fetch(`${this.baseUrl}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
      credentials: 'include',
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Login failed: ${error}`);
    }

    return response.json();
  }

  async getCurrentUser(): Promise<User> {
    const response = await fetch(`${this.baseUrl}/api/auth/me`, {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Failed to get user: ${error}`);
    }

    return response.json();
  }

  async updateUserPreferences(_token: string, preferences: Partial<User['preferences']>): Promise<void> {
    // TODO: Implement backend endpoint for updating user preferences
    console.log('Updating user preferences:', preferences);
  }

  async logout(): Promise<void> {
    await fetch(`${this.baseUrl}/api/auth/logout`, {
      method: 'POST',
      credentials: 'include',
    });
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

export { AuthService };
