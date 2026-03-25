// API service for HTTP requests
const API_BASE_URL =
  typeof window !== 'undefined'
    ? ''
    : (process.env.KAREN_BACKEND_URL ||
       process.env.NEXT_PUBLIC_KAREN_BACKEND_URL ||
       process.env.NEXT_PUBLIC_API_BASE_URL ||
       'http://localhost:8000');


export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

class ApiClient {
  private async getAuthHeaders(): Promise<Record<string, string>> {
    try {
      // Try to get a valid access token
      const accessToken = localStorage.getItem('access_token');
      
      if (!accessToken) {
        return {
          'Content-Type': 'application/json'
        };
      }

      // Check if token is expired and refresh if needed
      if (this.isTokenExpired(accessToken)) {
        try {
          await this.refreshAccessToken();
        } catch (error) {
          // If refresh fails, clear auth data and continue without auth
          console.warn('Failed to refresh access token, proceeding without auth');
          return {
            'Content-Type': 'application/json'
          };
        }
      }

      return {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json'
      };
    } catch (error) {
      return {
        'Content-Type': 'application/json'
      };
    }
  }

  private isTokenExpired(token: string): boolean {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.exp < Date.now() / 1000;
    } catch {
      return true;
    }
  }

  private async refreshAccessToken(): Promise<void> {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
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
    } catch (error) {
      // If refresh fails, clear all auth data
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user_data');
      
      if (typeof document !== 'undefined') {
        document.cookie = 'kari_session=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax';
        document.cookie = 'access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
        document.cookie = 'refresh_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
      }
      
      throw error;
    }
  }

  private async request<T>(endpoint: string, init: RequestInit = {}): Promise<T> {
    const send = async (): Promise<Response> => {
      const authHeaders = await this.getAuthHeaders();
      const requestHeaders = {
        ...authHeaders,
        ...((init.headers as Record<string, string> | undefined) || {}),
      };

      return fetch(`${API_BASE_URL}${endpoint}`, {
        ...init,
        headers: requestHeaders,
        credentials: 'include',
      });
    };

    let response = await send();

    if (response.status === 401) {
      try {
        await this.refreshAccessToken();
        response = await send();
      } catch (refreshError) {
        // Fall through to the error handling below with the original/second response.
      }
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        response.status,
        errorData.detail || errorData.message || `HTTP ${response.status}: ${response.statusText}`
      );
    }

    if (response.status === 204) {
      return undefined as T;
    }

    const text = await response.text();
    return (text ? JSON.parse(text) : undefined) as T;
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint);
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined
    });
  }

  async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'DELETE',
    });
  }
}

export const apiClient = new ApiClient();
export default apiClient;
