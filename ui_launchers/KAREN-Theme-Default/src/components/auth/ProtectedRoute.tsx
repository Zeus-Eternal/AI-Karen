"use client";

import React, { ReactNode, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/use-auth';
import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardContent } from '@/components/ui/card';
export interface ProtectedRouteProps {
  children: ReactNode;
  requiredRole?: 'super_admin' | 'admin' | 'user';
  requiredPermission?: string;
  fallback?: ReactNode;
  redirectTo?: string;
  showLoadingState?: boolean;
  loadingMessage?: string;
}
export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requiredRole,
  requiredPermission,
  fallback,
  redirectTo = '/unauthorized',
  showLoadingState = true,
  loadingMessage = 'Checking permissions...'
}) => {
  const { isAuthenticated, hasRole, hasPermission, user, authState } = useAuth();
  const router = useRouter();
  const hasRedirectedRef = useRef(false);
  const isMountedRef = useRef(false);
  const lastAuthStateRef = useRef(isAuthenticated);

  // Track mount state to avoid hydration issues
  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);
  // Handle authentication and authorization
  useEffect(() => {
    // Don't run on server or before initialization
    if (!isMountedRef.current || typeof window === 'undefined') return;

    // Reset redirect flag when user successfully authenticates (false -> true transition)
    if (!lastAuthStateRef.current && isAuthenticated) {
      hasRedirectedRef.current = false;
      lastAuthStateRef.current = isAuthenticated;
      return; // Don't redirect on the same render where auth state changed
    }
    lastAuthStateRef.current = isAuthenticated;

    // Don't redirect multiple times
    if (hasRedirectedRef.current) return;

    // If still loading, wait
    if (authState.isLoading) return;

    // Don't redirect immediately after successful login (prevent race conditions)
    const justLoggedIn = isAuthenticated && authState.lastActivity &&
      (Date.now() - authState.lastActivity.getTime()) < 1000;
    if (justLoggedIn) return;

    // If not authenticated, redirect to login
    if (!isAuthenticated) {
      const currentPath = window.location.pathname + window.location.search;
      // Avoid redirect loops - don't redirect if already on login or unauthorized pages
      if (currentPath !== '/login' && currentPath !== '/unauthorized' && !currentPath.startsWith('/login')) {
        sessionStorage.setItem('redirectAfterLogin', currentPath);
        hasRedirectedRef.current = true;
        router.replace('/login');
      }
      return;
    }
    // Check role requirement if specified
    if (requiredRole && !hasRole(requiredRole)) {
      hasRedirectedRef.current = true;
      router.replace(redirectTo);
      return;
    }
    // Check permission requirement if specified
    if (requiredPermission && !hasPermission(requiredPermission)) {
      hasRedirectedRef.current = true;
      router.replace(redirectTo);
      return;
    }
  }, [isAuthenticated, authState.isLoading, authState.lastActivity, requiredRole, requiredPermission, redirectTo, hasRole, hasPermission, user?.role, router]);
  // Don't show loading state if we're on login page to prevent flash
  const isOnLoginPage = typeof window !== 'undefined' && window.location.pathname === '/login';
  // Show loading state while checking authentication
  if (authState.isLoading && showLoadingState && !isOnLoginPage) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Card className="w-full max-w-md">
          <CardContent className="p-6 sm:p-4 md:p-6">
            <div className="flex flex-col items-center space-y-4">
              <Skeleton className="h-12 w-12 rounded-full " />
              <div className="space-y-2 text-center">
                <Skeleton className="h-4 w-48 " />
                <Skeleton className="h-3 w-32 " />
              </div>
              <div className="text-sm text-muted-foreground md:text-base lg:text-lg">
                {loadingMessage}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }
  // If not authenticated, don't render anything (redirect is handled above)
  if (!isAuthenticated) {
    return null;
  }
  // Check role requirement if specified
  if (requiredRole && !hasRole(requiredRole)) {
    if (fallback) {
      return <>{fallback}</>;
    }
    return null; // Redirect is handled above
  }
  // Check permission requirement if specified
  if (requiredPermission && !hasPermission(requiredPermission)) {
    if (fallback) {
      return <>{fallback}</>;
    }
    return null; // Redirect is handled above
  }
  // Render children if all checks pass
  return <>{children}</>;
};
