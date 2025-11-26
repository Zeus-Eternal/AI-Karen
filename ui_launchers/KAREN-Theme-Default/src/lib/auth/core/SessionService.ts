/**
 * Session Service
 * 
 * Lightweight session management that integrates with cookies
 * and provides session validation and refresh functionality.
 */

import { TokenService } from "./TokenService";

// Types
export interface SessionInfo {
  id: string;
  userId: string;
  expiresAt: number;
  isActive: boolean;
  lastActivity: Date;
  userAgent?: string;
  ipAddress?: string;
}

export interface SessionValidationResult {
  valid: boolean;
  session?: SessionInfo;
  error?: string;
}

// Session Service Implementation
export class SessionService {
  private static instance: SessionService | null = null;
  private sessionCookieName = "kari_session";
  private sessionValidationInterval = 5 * 60 * 1000; // 5 minutes
  private sessionValidationTimer: ReturnType<typeof setInterval> | null = null;

  /**
   * Get the singleton instance of the SessionService
   */
  public static getInstance(): SessionService {
    if (!SessionService.instance) {
      SessionService.instance = new SessionService();
    }
    return SessionService.instance;
  }

  /**
   * Private constructor to enforce singleton pattern
   */
  private constructor() {}

  /**
   * Get current session ID from cookie
   */
  public getSessionId(): string | null {
    if (typeof window === "undefined") {
      return null;
    }

    const cookieString = document.cookie || "";
    const cookies = cookieString.split(";").map(cookie => cookie.trim());
    
    for (const cookie of cookies) {
      const [name, value] = cookie.split("=");
      if (name === this.sessionCookieName) {
        return decodeURIComponent(value);
      }
    }

    return null;
  }

  /**
   * Check if session cookie exists
   */
  public hasSessionCookie(): boolean {
    return !!this.getSessionId();
  }

  /**
   * Validate current session
   */
  public async validateSession(): Promise<SessionValidationResult> {
    try {
      const sessionId = this.getSessionId();
      if (!sessionId) {
        return { valid: false, error: "No session cookie found" };
      }

      // Check if we have a valid token
      const tokenService = TokenService.getInstance();
      if (!tokenService.hasValidToken()) {
        return { valid: false, error: "No valid token found" };
      }

      // Check if token is expired
      if (tokenService.isTokenExpired()) {
        tokenService.clearToken();
        return { valid: false, error: "Token expired" };
      }

      // Try to refresh token if needed
      if (tokenService.isTokenExpiringSoon()) {
        const refreshSuccess = await tokenService.refreshTokenIfNeeded();
        if (!refreshSuccess) {
          return { valid: false, error: "Failed to refresh token" };
        }
      }

      // Validate session with backend
      const response = await fetch("/api/auth/validate-session", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          ...tokenService.getAuthHeader(),
        },
        credentials: "include",
      });

      if (!response.ok) {
        // If validation fails, clear tokens and return invalid
        if (response.status === 401 || response.status === 403) {
          tokenService.clearToken();
        }
        return { 
          valid: false, 
          error: `Session validation failed: ${response.status}` 
        };
      }

      const data = await response.json();
      
      if (!data.valid) {
        tokenService.clearToken();
        return { valid: false, error: data.error || "Invalid session" };
      }

      // Create session info
      const session: SessionInfo = {
        id: sessionId,
        userId: data.user_id || data.user?.user_id,
        expiresAt: data.expires_at || Math.floor(Date.now() / 1000) + 3600, // Default 1 hour
        isActive: true,
        lastActivity: new Date(),
        userAgent: data.user_agent,
        ipAddress: data.ip_address,
      };

      return { valid: true, session };
    } catch (error) {
      console.error("Session validation error:", error);
      return { 
        valid: false, 
        error: error instanceof Error ? error.message : "Session validation failed" 
      };
    }
  }

  /**
   * Refresh session
   */
  public async refreshSession(): Promise<boolean> {
    try {
      const tokenService = TokenService.getInstance();
      
      // Try to refresh token if needed
      if (tokenService.isTokenExpiringSoon()) {
        const refreshSuccess = await tokenService.refreshTokenIfNeeded();
        if (!refreshSuccess) {
          return false;
        }
      }

      // Refresh session with backend
      const response = await fetch("/api/auth/refresh-session", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          ...tokenService.getAuthHeader(),
        },
        credentials: "include",
      });

      return response.ok;
    } catch (error) {
      console.error("Session refresh error:", error);
      return false;
    }
  }

  /**
   * End current session
   */
  public async endSession(): Promise<void> {
    try {
      const sessionId = this.getSessionId();
      if (!sessionId) {
        return;
      }

      // Call logout endpoint to clear server-side session
      await fetch("/api/auth/logout", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        credentials: "include",
      });
    } catch (error) {
      console.error("Session end error:", error);
    } finally {
      // Clear client-side tokens
      TokenService.getInstance().clearToken();
      
      // Clear session cookie
      if (typeof window !== "undefined") {
        document.cookie = `${this.sessionCookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
      }
    }
  }

  /**
   * Start automatic session validation
   */
  public startSessionValidation(): void {
    if (this.sessionValidationTimer) {
      clearInterval(this.sessionValidationTimer);
    }

    this.sessionValidationTimer = setInterval(async () => {
      const result = await this.validateSession();
      if (!result.valid) {
        console.warn("Automatic session validation failed:", result.error);
        this.stopSessionValidation();
        this.endSession().catch(console.error);
        
        // Redirect to login page
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
      }
    }, this.sessionValidationInterval);
  }

  /**
   * Stop automatic session validation
   */
  public stopSessionValidation(): void {
    if (this.sessionValidationTimer) {
      clearInterval(this.sessionValidationTimer);
      this.sessionValidationTimer = null;
    }
  }

  /**
   * Get session info
   */
  public async getSessionInfo(): Promise<SessionInfo | null> {
    const result = await this.validateSession();
    return result.session || null;
  }

  /**
   * Check if session is active
   */
  public async isSessionActive(): Promise<boolean> {
    const result = await this.validateSession();
    return result.valid;
  }
}

// Export singleton instance
export const sessionService = SessionService.getInstance();