/**
 * Session Recovery System
 * 
 * Implements intelligent session recovery logic that attempts token refresh
 * before showing login screens, with graceful fallback handling.
 * 
 * Requirements: 1.4, 5.2, 5.3, 5.4, 5.5
 */

import { bootSession, refreshToken, clearSession, isAuthenticated } from './session';

export interface SessionRecoveryResult {
  success: boolean;
  reason?: 'no_refresh_token' | 'refresh_failed' | 'network_error' | 'invalid_session';
  shouldShowLogin: boolean;
  message?: string;
}

/**
 * Attempt to recover session using refresh token
 * This is the main entry point for session recovery
 */
export async function attemptSessionRecovery(): Promise<SessionRecoveryResult> {
  try {
    // First, try to boot session from HttpOnly cookie
    await bootSession();
    
    // Check if session was successfully restored
    if (isAuthenticated()) {
      return {
        success: true,
        shouldShowLogin: false,
      };
    }
    
    // If bootSession didn't establish a session, there's no refresh token
    return {
      success: false,
      reason: 'no_refresh_token',
      shouldShowLogin: true,
      message: 'No valid session found. Please log in again.',
    };
  } catch (error: any) {
    // Analyze the error to provide appropriate response
    const errorMessage = error.message?.toLowerCase() || '';
    
    if (errorMessage.includes('network') || errorMessage.includes('fetch') || errorMessage.includes('timeout') || errorMessage.includes('connection')) {
      return {
        success: false,
        reason: 'network_error',
        shouldShowLogin: false, // Don't show login for network errors
        message: 'Network error occurred. Please check your connection and try again.',
      };
    }
    
    if (errorMessage.includes('unauthorized') || errorMessage.includes('401') || errorMessage.includes('authentication')) {
      return {
        success: false,
        reason: 'refresh_failed',
        shouldShowLogin: true,
        message: 'Your session has expired. Please log in again.',
      };
    }
    
    // Generic error - likely invalid session
    return {
      success: false,
      reason: 'invalid_session',
      shouldShowLogin: true,
      message: 'Session could not be restored. Please log in again.',
    };
  }
}

/**
 * Attempt to recover from a 401 error by refreshing the token
 * Used by API clients when they encounter authentication errors
 */
export async function recoverFrom401Error(): Promise<SessionRecoveryResult> {
  try {
    // Attempt token refresh
    await refreshToken();
    
    // Check if refresh was successful
    if (isAuthenticated()) {
      return {
        success: true,
        shouldShowLogin: false,
      };
    }
    
    // Refresh didn't establish valid session
    clearSession();
    return {
      success: false,
      reason: 'refresh_failed',
      shouldShowLogin: true,
      message: 'Session expired. Please log in again.',
    };
  } catch (error: any) {
    // Clear session on any refresh failure
    clearSession();
    
    const errorMessage = error.message?.toLowerCase() || '';
    
    if (errorMessage.includes('network') || errorMessage.includes('fetch') || errorMessage.includes('timeout') || errorMessage.includes('connection')) {
      return {
        success: false,
        reason: 'network_error',
        shouldShowLogin: false,
        message: 'Network error during session refresh. Please try again.',
      };
    }
    
    return {
      success: false,
      reason: 'refresh_failed',
      shouldShowLogin: true,
      message: 'Session expired. Please log in again.',
    };
  }
}

/**
 * Silent session recovery for background operations
 * Returns true if session is valid, false otherwise
 */
export async function silentSessionRecovery(): Promise<boolean> {
  try {
    const result = await attemptSessionRecovery();
    return result.success;
  } catch (error) {
    // Silent recovery should never throw
    console.warn('Silent session recovery failed:', error);
    return false;
  }
}

/**
 * Check if we should attempt session recovery based on current state
 */
export function shouldAttemptRecovery(): boolean {
  // Don't attempt recovery if we already have a valid session
  if (isAuthenticated()) {
    return false;
  }
  
  // Always attempt recovery if no session exists
  return true;
}

/**
 * Get user-friendly message for session recovery failure
 */
export function getRecoveryFailureMessage(reason: SessionRecoveryResult['reason']): string {
  switch (reason) {
    case 'no_refresh_token':
      return 'Please log in to continue.';
    case 'refresh_failed':
      return 'Your session has expired. Please log in again.';
    case 'network_error':
      return 'Network error occurred. Please check your connection and try again.';
    case 'invalid_session':
      return 'Session could not be restored. Please log in again.';
    default:
      return 'Authentication required. Please log in.';
  }
}

/**
 * Determine if error should trigger automatic retry
 */
export function shouldRetryAfterRecovery(reason: SessionRecoveryResult['reason']): boolean {
  // Only retry for successful recovery or network errors
  return reason === undefined || reason === 'network_error';
}