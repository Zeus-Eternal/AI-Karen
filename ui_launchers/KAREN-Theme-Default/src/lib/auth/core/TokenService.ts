/**
 * Token Service
 * 
 * Simple, straightforward token management for authentication.
 * Handles token storage, retrieval, and refresh without unnecessary complexity.
 */

// Types
export interface TokenInfo {
  token: string;
  expiresAt?: number;
  refreshToken?: string;
}

// Token Service Implementation
export class TokenService {
  private static instance: TokenService | null = null;
  private tokenKey = "auth_token";
  private refreshKey = "refresh_token";
  private tokenExpiresKey = "token_expires";

  /**
   * Get the singleton instance of the TokenService
   */
  public static getInstance(): TokenService {
    if (!TokenService.instance) {
      TokenService.instance = new TokenService();
    }
    return TokenService.instance;
  }

  /**
   * Private constructor to enforce singleton pattern
   */
  private constructor() {}

  /**
   * Set authentication token
   */
  public setToken(token: string, expiresAt?: number, refreshToken?: string): void {
    if (typeof window === "undefined") {
      return;
    }

    try {
      // Store access token
      localStorage.setItem(this.tokenKey, token);

      // Store expiration if provided
      if (expiresAt) {
        localStorage.setItem(this.tokenExpiresKey, expiresAt.toString());
      }

      // Store refresh token if provided
      if (refreshToken) {
        localStorage.setItem(this.refreshKey, refreshToken);
      }
    } catch (error) {
      console.error("Failed to store token:", error);
    }
  }

  /**
   * Get authentication token
   */
  public getToken(): string | null {
    if (typeof window === "undefined") {
      return null;
    }

    try {
      const token = localStorage.getItem(this.tokenKey);
      
      // Check if token is expired
      if (token && this.isTokenExpired()) {
        this.clearToken();
        return null;
      }

      return token;
    } catch (error) {
      console.error("Failed to retrieve token:", error);
      return null;
    }
  }

  /**
   * Get refresh token
   */
  public getRefreshToken(): string | null {
    if (typeof window === "undefined") {
      return null;
    }

    try {
      return localStorage.getItem(this.refreshKey);
    } catch (error) {
      console.error("Failed to retrieve refresh token:", error);
      return null;
    }
  }

  /**
   * Get token info including expiration
   */
  public getTokenInfo(): TokenInfo | null {
    const token = this.getToken();
    const refreshToken = this.getRefreshToken();
    const expiresAt = this.getTokenExpiration();

    if (!token) {
      return null;
    }

    return {
      token,
      refreshToken: refreshToken || undefined,
      expiresAt: expiresAt || undefined,
    };
  }

  /**
   * Get token expiration time
   */
  public getTokenExpiration(): number | null {
    if (typeof window === "undefined") {
      return null;
    }

    try {
      const expiresAt = localStorage.getItem(this.tokenExpiresKey);
      return expiresAt ? parseInt(expiresAt, 10) : null;
    } catch (error) {
      console.error("Failed to retrieve token expiration:", error);
      return null;
    }
  }

  /**
   * Check if token is expired
   */
  public isTokenExpired(): boolean {
    const expiresAt = this.getTokenExpiration();
    if (!expiresAt) {
      return false;
    }

    // Add 30-second buffer to account for clock skew
    const now = Math.floor(Date.now() / 1000);
    return expiresAt <= now + 30;
  }

  /**
   * Check if token is about to expire (within 5 minutes)
   */
  public isTokenExpiringSoon(): boolean {
    const expiresAt = this.getTokenExpiration();
    if (!expiresAt) {
      return false;
    }

    // Check if token expires within 5 minutes
    const now = Math.floor(Date.now() / 1000);
    return expiresAt <= now + 300;
  }

  /**
   * Refresh token if it's about to expire
   */
  public async refreshTokenIfNeeded(): Promise<boolean> {
    if (!this.isTokenExpiringSoon()) {
      return true;
    }

    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      return false;
    }

    try {
      const response = await fetch("/api/auth/refresh", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
        credentials: "include",
      });

      if (!response.ok) {
        throw new Error(`Token refresh failed: ${response.status}`);
      }

      const data = await response.json();
      const newToken = data.access_token;
      const newExpiresAt = data.expires_in 
        ? Math.floor(Date.now() / 1000) + data.expires_in
        : undefined;
      const newRefreshToken = data.refresh_token;

      if (!newToken) {
        throw new Error("No access token in refresh response");
      }

      this.setToken(newToken, newExpiresAt, newRefreshToken);
      return true;
    } catch (error) {
      console.error("Token refresh failed:", error);
      this.clearToken();
      return false;
    }
  }

  /**
   * Clear all tokens
   */
  public clearToken(): void {
    if (typeof window === "undefined") {
      return;
    }

    try {
      localStorage.removeItem(this.tokenKey);
      localStorage.removeItem(this.refreshKey);
      localStorage.removeItem(this.tokenExpiresKey);
    } catch (error) {
      console.error("Failed to clear tokens:", error);
    }
  }

  /**
   * Set token in HTTP Authorization header
   */
  public getAuthHeader(): Record<string, string> {
    const token = this.getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  /**
   * Check if token exists and is valid
   */
  public hasValidToken(): boolean {
    return !!this.getToken();
  }
}

// Export singleton instance
export const tokenService = TokenService.getInstance();