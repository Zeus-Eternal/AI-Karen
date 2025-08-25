/**
 * Frontend Session Management System - Main Export
 * 
 * Exports all session management utilities for easy importing
 */

// Core session management
export {
  setSession,
  getSession,
  clearSession,
  isSessionValid,
  getAuthHeader,
  bootSession,
  refreshToken,
  ensureToken,
  getCurrentUser,
  hasRole,
  isAuthenticated,
  login,
  logout,
  type SessionData,
  type TokenRefreshResponse,
} from './session';

// Enhanced API client
export {
  EnhancedApiClient,
  getEnhancedApiClient,
} from './api-client-enhanced';

// React hook
export {
  useSession,
  type UseSessionReturn,
} from '../../hooks/use-session';

// Token validation and session rehydration services
export {
  TokenValidationService,
  TokenExpiredError,
  TokenNetworkError,
} from './token-validation.service';

export {
  SessionRehydrationService,
  type RehydrationState,
} from './session-rehydration.service';