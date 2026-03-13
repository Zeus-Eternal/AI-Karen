/**
 * Simplified Session Manager
 * 
 * Provides lightweight cookie-based session detection with single API call validation.
 * Removes complex token validation, retry logic, and error handling abstractions.
 * 
 * Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
 */

import { validateSession, clearSession, hasSessionCookie } from './session';

export class SessionManager {
  /**
   * Check if a valid session exists (cookie-based detection)
   */
  hasValidSession(): boolean {
    return hasSessionCookie();
  }

  /**
   * Clear session data and cookies
   */
  clearSession(): void {
    clearSession();
  }

  /**
   * Validate session with backend - single API call, no retries
   */
  async validateSession(): Promise<boolean> {
    return await validateSession();
  }
}

// Export singleton instance
export const sessionManager = new SessionManager();