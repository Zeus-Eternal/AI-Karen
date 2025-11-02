'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useFirstRunSetup } from '@/hooks/useFirstRunSetup';
import { Brain } from 'lucide-react';

export interface SetupRouteGuardProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

/**
 * Route guard that protects setup routes from being accessed when setup is already completed
 * Redirects to login if super admin already exists
 */
export const SetupRouteGuard: React.FC<SetupRouteGuardProps> = ({ 
  children, 
  fallback 
}) => {
  const router = useRouter();
  const { isFirstRun, setupCompleted, isLoading, error } = useFirstRunSetup();

  useEffect(() => {
    // If not loading and setup is completed or not first run, redirect to login
    if (!isLoading && (!isFirstRun || setupCompleted)) {
      router.replace('/login');
    }
  }, [isFirstRun, setupCompleted, isLoading, router]);

  // Show loading state while checking setup status
  if (isLoading) {
    return fallback || (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 dark:from-gray-950 dark:via-gray-900 dark:to-purple-950">
        <div className="text-center space-y-4">
          <div className="relative">
            <Brain className="h-16 w-16 text-primary mx-auto animate-pulse sm:w-auto md:w-full" />
            <div className="absolute inset-0 h-16 w-16 bg-primary/20 rounded-full blur-xl animate-pulse sm:w-auto md:w-full" />
          </div>
          <div className="space-y-2">
            <h2 className="text-xl font-semibold text-foreground">
              Checking Setup Status
            </h2>
            <p className="text-muted-foreground">
              Please wait while we verify your system configuration...
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Show error state if there's an error checking setup status
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 dark:from-gray-950 dark:via-gray-900 dark:to-purple-950 p-4 sm:p-4 md:p-6">
        <div className="text-center space-y-4 max-w-md">
          <Brain className="h-16 w-16 text-red-500 mx-auto sm:w-auto md:w-full" />
          <div className="space-y-2">
            <h2 className="text-xl font-semibold text-red-600">
              Setup Check Failed
            </h2>
            <p className="text-muted-foreground">
              Unable to verify setup status. Please try refreshing the page.
            </p>
            <p className="text-sm text-red-600 bg-red-50 dark:bg-red-950/20 p-3 rounded-md md:text-base lg:text-lg">
              {error}
            </p>
          </div>
          <button
            onClick={() = aria-label="Button"> window.location.reload()}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
          >
            Refresh Page
          </button>
        </div>
      </div>
    );
  }

  // If setup is already completed or not first run, don't render children
  // (redirect will happen in useEffect)
  if (!isFirstRun || setupCompleted) {
    return null;
  }

  // Render children if this is first run and setup is not completed
  return <>{children}</>;
};

/**
 * Hook to check if current route should allow setup access
 */
export function useSetupRouteAccess() {
  const { isFirstRun, setupCompleted, isLoading } = useFirstRunSetup();
  
  return {
    canAccessSetup: !isLoading && isFirstRun && !setupCompleted,
    shouldRedirectToLogin: !isLoading && (!isFirstRun || setupCompleted),
    isCheckingAccess: isLoading
  };
}

/**
 * Higher-order component for setup route protection
 */
export function withSetupRouteGuard<P extends object>(
  Component: React.ComponentType<P>
) {
  const WrappedComponent = (props: P) => {
    return (
      <SetupRouteGuard>
        <Component {...props} />
      </SetupRouteGuard>
    );
  };

  WrappedComponent.displayName = `withSetupRouteGuard(${Component.displayName || Component.name})`;
  
  return WrappedComponent;
}

/**
 * Component that redirects to setup if first run is detected
 */
export const FirstRunRedirect: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const router = useRouter();
  const { isFirstRun, setupCompleted, isLoading } = useFirstRunSetup();

  useEffect(() => {
    // If first run and setup not completed, redirect to setup
    if (!isLoading && isFirstRun && !setupCompleted) {
      router.replace('/setup');
    }
  }, [isFirstRun, setupCompleted, isLoading, router]);

  // Don't render children if redirecting to setup
  if (!isLoading && isFirstRun && !setupCompleted) {
    return null;
  }

  return <>{children}</>;
};