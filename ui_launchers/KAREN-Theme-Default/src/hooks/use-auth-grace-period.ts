/**
 * Auth Grace Period Hook
 *
 * Provides a centralized way to check if we're past the grace period after login.
 * Components should use this to delay API calls that require authenticated backend sessions.
 *
 * The grace period prevents race conditions where frontend auth state is ready
 * but backend session hasn't fully propagated yet.
 */

"use client";

import { useEffect, useState } from 'react';
import { useAuth } from './use-auth';

/**
 * Grace period duration in milliseconds
 * Must match AUTH_GRACE_PERIOD_MS in auth-interceptor.ts and api-client-integrated.ts
 */
export const AUTH_GRACE_PERIOD_MS = 10000; // 10 seconds

export interface AuthGracePeriodState {
  /** Whether user is authenticated */
  isAuthenticated: boolean;
  /** Whether we're past the grace period and safe to make authenticated API calls */
  isReadyForApiCalls: boolean;
  /** Whether we're currently in the grace period */
  isInGracePeriod: boolean;
  /** Milliseconds remaining in grace period (0 if past grace period) */
  gracePeriodRemaining: number;
}

/**
 * Hook to check if we're past the authentication grace period
 *
 * @returns State object with authentication and grace period info
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const { isReadyForApiCalls, isInGracePeriod } = useAuthGracePeriod();
 *
 *   useEffect(() => {
 *     if (isReadyForApiCalls) {
 *       // Safe to make authenticated API calls
 *       fetchUserData();
 *     }
 *   }, [isReadyForApiCalls]);
 *
 *   if (isInGracePeriod) {
 *     return <div>Preparing your session...</div>;
 *   }
 *
 *   return <div>Ready!</div>;
 * }
 * ```
 */
export function useAuthGracePeriod(): AuthGracePeriodState {
  const { isAuthenticated, authState } = useAuth();
  const [gracePeriodRemaining, setGracePeriodRemaining] = useState(0);

  useEffect(() => {
    if (!isAuthenticated || !authState.lastActivity) {
      setGracePeriodRemaining(0);
      return;
    }

    const updateRemaining = () => {
      const elapsed = Date.now() - authState.lastActivity!.getTime();
      const remaining = Math.max(0, AUTH_GRACE_PERIOD_MS - elapsed);
      setGracePeriodRemaining(remaining);
    };

    // Update immediately
    updateRemaining();

    // Update every 100ms while in grace period
    const interval = setInterval(updateRemaining, 100);

    return () => clearInterval(interval);
  }, [isAuthenticated, authState.lastActivity]);

  const isInGracePeriod = isAuthenticated && gracePeriodRemaining > 0;
  const isReadyForApiCalls = isAuthenticated && gracePeriodRemaining === 0;

  return {
    isAuthenticated,
    isReadyForApiCalls,
    isInGracePeriod,
    gracePeriodRemaining,
  };
}

/**
 * Hook that only returns true when authenticated AND past grace period
 * Simpler version for components that just need a boolean check
 *
 * @returns true if authenticated and safe to make API calls, false otherwise
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const isReady = useIsReadyForApiCalls();
 *
 *   useEffect(() => {
 *     if (isReady) {
 *       fetchData();
 *     }
 *   }, [isReady]);
 * }
 * ```
 */
export function useIsReadyForApiCalls(): boolean {
  const { isReadyForApiCalls } = useAuthGracePeriod();
  return isReadyForApiCalls;
}
