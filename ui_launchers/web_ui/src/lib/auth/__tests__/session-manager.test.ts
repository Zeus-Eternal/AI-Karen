/**
 * Tests for simplified session manager
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { SessionManager } from '../session-manager';

// Mock the session functions
vi.mock('../session', () => ({
  validateSession: vi.fn(),
  clearSession: vi.fn(),
  hasSessionCookie: vi.fn(),
}));

import { validateSession, clearSession, hasSessionCookie } from '../session';

const mockValidateSession = validateSession as ReturnType<typeof vi.fn>;
const mockClearSession = clearSession as ReturnType<typeof vi.fn>;
const mockHasSessionCookie = hasSessionCookie as ReturnType<typeof vi.fn>;

describe('SessionManager', () => {
  let sessionManager: SessionManager;

  beforeEach(() => {
    sessionManager = new SessionManager();
    vi.clearAllMocks();
  });

  describe('hasValidSession', () => {
    it('should return true when session cookie exists', () => {
      mockHasSessionCookie.mockReturnValue(true);
      
      expect(sessionManager.hasValidSession()).toBe(true);
      expect(mockHasSessionCookie).toHaveBeenCalledTimes(1);
    });

    it('should return false when session cookie does not exist', () => {
      mockHasSessionCookie.mockReturnValue(false);
      
      expect(sessionManager.hasValidSession()).toBe(false);
      expect(mockHasSessionCookie).toHaveBeenCalledTimes(1);
    });
  });

  describe('clearSession', () => {
    it('should call clearSession function', () => {
      sessionManager.clearSession();
      
      expect(mockClearSession).toHaveBeenCalledTimes(1);
    });
  });

  describe('validateSession', () => {
    it('should return true when session validation succeeds', async () => {
      mockValidateSession.mockResolvedValue(true);
      
      const result = await sessionManager.validateSession();
      
      expect(result).toBe(true);
      expect(mockValidateSession).toHaveBeenCalledTimes(1);
    });

    it('should return false when session validation fails', async () => {
      mockValidateSession.mockResolvedValue(false);
      
      const result = await sessionManager.validateSession();
      
      expect(result).toBe(false);
      expect(mockValidateSession).toHaveBeenCalledTimes(1);
    });

    it('should handle validation errors gracefully', async () => {
      mockValidateSession.mockRejectedValue(new Error('Network error'));
      
      await expect(sessionManager.validateSession()).rejects.toThrow('Network error');
      expect(mockValidateSession).toHaveBeenCalledTimes(1);
    });
  });
});