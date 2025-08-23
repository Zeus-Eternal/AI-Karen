/**
 * Enhanced Protected Route Component with Session Recovery
 * 
 * Implements intelligent session recovery that attempts token refresh
 * before showing login screens, with graceful fallback handling.
 * 
 * Requirements: 1.4, 5.4, 5.5
 */

'use client';

import React, { ReactNode, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2, AlertCircle, RefreshCw } from 'lucide-react';
import { useSession } from '@/hooks/use-session';
import { 
  attemptSessionRecovery, 
  getRecoveryFailureMessage,
  type SessionRecoveryResult 
} from '@/lib/auth/session-recovery';
import { LoginForm } from './LoginForm';

interface ProtectedRouteEnhancedProps {
  children: ReactNode;
  fallback?: ReactNode;
  redirectTo?: string;
  showRecoveryStatus?: boolean;
  onRecoveryFailure?: (result: SessionRecoveryResult) => void;
}

type RecoveryState = 'idle' | 'attempting' | 'success' | 'failed' | 'network_error';

export const ProtectedRouteEnhanced: React.FC<ProtectedRouteEnhancedProps> = ({ 
  children, 
  fallback,
  redirectTo = '/login',
  showRecoveryStatus = true,
  onRecoveryFailure
}) => {
  const { isAuthenticated, isLoading, refreshSession } = useSession();
  const router = useRouter();
  const [recoveryState, setRecoveryState] = useState<RecoveryState>('idle');
  const [recoveryResult, setRecoveryResult] = useState<SessionRecoveryResult | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  // Attempt session recovery when component mounts or when not authenticated
  useEffect(() => {
    const performRecovery = async () => {
      // Skip recovery if already authenticated or still loading initial session
      if (isAuthenticated || isLoading || recoveryState === 'attempting') {
        return;
      }

      setRecoveryState('attempting');
      
      try {
        const result = await attemptSessionRecovery();
        setRecoveryResult(result);

        if (result.success) {
          setRecoveryState('success');
          // Refresh the session hook state
          refreshSession();
        } else {
          if (result.reason === 'network_error') {
            setRecoveryState('network_error');
          } else {
            setRecoveryState('failed');
            // Call failure callback if provided
            onRecoveryFailure?.(result);
          }
        }
      } catch (error) {
        console.error('Session recovery error:', error);
        const failureResult: SessionRecoveryResult = {
          success: false,
          reason: 'invalid_session',
          shouldShowLogin: true,
          message: 'Session recovery failed. Please log in again.',
        };
        setRecoveryResult(failureResult);
        setRecoveryState('failed');
        onRecoveryFailure?.(failureResult);
      }
    };

    performRecovery();
  }, [isAuthenticated, isLoading, recoveryState, refreshSession, onRecoveryFailure]);

  // Handle redirect for failed recovery
  useEffect(() => {
    if (recoveryState === 'failed' && recoveryResult?.shouldShowLogin) {
      const currentPath = window.location.pathname;
      const authPages = ['/login', '/signup', '/reset-password', '/verify-email'];
      
      if (!authPages.includes(currentPath)) {
        // Store the current path for redirect after login
        sessionStorage.setItem('redirectAfterLogin', currentPath);
        router.push(redirectTo);
      }
    }
  }, [recoveryState, recoveryResult, router, redirectTo]);

  // Retry recovery for network errors
  const retryRecovery = async () => {
    if (retryCount >= 3) {
      // Max retries reached, treat as failed
      setRecoveryState('failed');
      setRecoveryResult({
        success: false,
        reason: 'network_error',
        shouldShowLogin: true,
        message: 'Unable to connect. Please check your network and try logging in again.',
      });
      return;
    }

    setRetryCount(prev => prev + 1);
    setRecoveryState('idle'); // This will trigger the recovery effect again
  };

  // Show loading state during initial session load or recovery
  if (isLoading || recoveryState === 'attempting') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center space-y-4">
          <Loader2 className="h-12 w-12 animate-spin mx-auto text-primary" />
          <div className="space-y-2">
            <p className="text-muted-foreground">
              {isLoading ? 'Loading...' : 'Restoring your session...'}
            </p>
            {showRecoveryStatus && recoveryState === 'attempting' && (
              <p className="text-sm text-muted-foreground">
                This may take a moment
              </p>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Show network error with retry option
  if (recoveryState === 'network_error' && showRecoveryStatus) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center space-y-6 max-w-md mx-auto p-6">
          <AlertCircle className="h-16 w-16 mx-auto text-yellow-500" />
          <div className="space-y-2">
            <h2 className="text-xl font-semibold">Connection Issue</h2>
            <p className="text-muted-foreground">
              {recoveryResult?.message || 'Unable to restore your session due to a network error.'}
            </p>
            <p className="text-sm text-muted-foreground">
              Retry attempt {retryCount + 1} of 3
            </p>
          </div>
          <div className="space-y-3">
            <button
              onClick={retryRecovery}
              className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
            >
              <RefreshCw className="h-4 w-4" />
              Try Again
            </button>
            <div>
              <button
                onClick={() => {
                  setRecoveryState('failed');
                  setRecoveryResult({
                    success: false,
                    shouldShowLogin: true,
                    message: 'Please log in to continue.',
                  });
                }}
                className="text-sm text-muted-foreground hover:text-foreground underline"
              >
                Skip to login
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Show login form if recovery failed and we should show login
  if (recoveryState === 'failed' && recoveryResult?.shouldShowLogin) {
    const currentPath = typeof window !== 'undefined' ? window.location.pathname : '';
    const authPages = ['/login', '/signup', '/reset-password', '/verify-email'];
    
    if (authPages.includes(currentPath)) {
      return (
        <div className="space-y-4">
          {showRecoveryStatus && recoveryResult.message && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
              <div className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-yellow-600" />
                <p className="text-sm text-yellow-800">
                  {recoveryResult.message}
                </p>
              </div>
            </div>
          )}
          {fallback || <LoginForm />}
        </div>
      );
    }
    
    // For other pages, the useEffect will handle the redirect
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-muted-foreground">Redirecting to login...</p>
        </div>
      </div>
    );
  }

  // If we have a successful recovery or user is authenticated, show children
  if (isAuthenticated || recoveryState === 'success') {
    return <>{children}</>;
  }

  // Fallback loading state
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center">
        <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4 text-primary" />
        <p className="text-muted-foreground">Loading...</p>
      </div>
    </div>
  );
};

/**
 * Hook for using protected route functionality in components
 */
export function useProtectedRoute() {
  const { isAuthenticated, isLoading } = useSession();
  const [recoveryState, setRecoveryState] = useState<RecoveryState>('idle');

  const ensureAuthenticated = async (): Promise<boolean> => {
    if (isAuthenticated) {
      return true;
    }

    if (isLoading) {
      return false;
    }

    setRecoveryState('attempting');
    
    try {
      const result = await attemptSessionRecovery();
      
      if (result.success) {
        setRecoveryState('success');
        return true;
      } else {
        setRecoveryState('failed');
        return false;
      }
    } catch (error) {
      setRecoveryState('failed');
      return false;
    }
  };

  return {
    isAuthenticated,
    isLoading,
    recoveryState,
    ensureAuthenticated,
  };
}