"use client";

import React, { ReactNode, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
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
  const [hasRedirected, setHasRedirected] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  // Reset redirect flag when authentication state changes
  useEffect(() => {
    setHasRedirected(false);
  }, [isAuthenticated, user?.userId]);
  // Initialize after first render to avoid hydration issues
  useEffect(() => {
    setIsInitialized(true);
  }, []);
  // Handle authentication and authorization
  useEffect(() => {
    // Don't run on server or before initialization
    if (!isInitialized || typeof window === 'undefined') return;
    // Don't redirect multiple times
    if (hasRedirected) return;
    // If still loading, wait
    if (authState.isLoading) return;
    // If not authenticated, redirect to login
    if (!isAuthenticated) {
      const currentPath = window.location.pathname + window.location.search;
      // Avoid redirect loops - don't redirect if already on login or unauthorized pages
      if (currentPath !== '/login' && currentPath !== '/unauthorized' && !currentPath.startsWith('/login')) {
        sessionStorage.setItem('redirectAfterLogin', currentPath);
        setHasRedirected(true);
        // Use a small delay to prevent race conditions
        setTimeout(() => {
          router.replace('/login');
        }, 100);
      }
      return;
    }
    // Check role requirement if specified
    if (requiredRole && !hasRole(requiredRole)) {
      setHasRedirected(true);
      router.replace(redirectTo);
      return;
    }
    // Check permission requirement if specified
    if (requiredPermission && !hasPermission(requiredPermission)) {
      setHasRedirected(true);
      router.replace(redirectTo);
      return;
    }
  }, [isInitialized, isAuthenticated, authState.isLoading, requiredRole, requiredPermission, hasRedirected, redirectTo, hasRole, hasPermission, user?.role, router]);
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
