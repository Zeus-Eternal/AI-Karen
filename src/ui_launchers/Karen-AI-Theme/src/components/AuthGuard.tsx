"use client";

import { useAuth } from "@/lib/useAuth";
import { useRouter } from "next/navigation";
import { useEffect, ReactNode } from "react";

interface AuthGuardProps {
  children: ReactNode;
  requiredPermissions?: string[];
  redirectTo?: string;
  fallback?: ReactNode;
}

export function AuthGuard({ 
  children, 
  requiredPermissions = [], 
  redirectTo = "/login", 
  fallback 
}: AuthGuardProps) {
  const { isAuthenticated, isLoading, user, hasPermission } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading) {
      if (!isAuthenticated) {
        router.push(redirectTo);
        return;
      }

      // Check if user has required permissions
      if (requiredPermissions.length > 0) {
        const hasAllPermissions = requiredPermissions.every(permission => 
          hasPermission(permission)
        );
        
        if (!hasAllPermissions) {
          // User doesn't have required permissions
          // You could redirect to an unauthorized page or show an error
          router.push("/unauthorized");
          return;
        }
      }
    }
  }, [isAuthenticated, isLoading, user, requiredPermissions, hasPermission, router, redirectTo]);

  // Show loading state or fallback while checking auth
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
      </div>
    );
  }

  // If not authenticated and we have a fallback, show it
  if (!isAuthenticated && fallback) {
    return <>{fallback}</>;
  }

  // If authenticated and has permissions, render children
  if (isAuthenticated && (!requiredPermissions.length || requiredPermissions.every(permission => hasPermission(permission)))) {
    return <>{children}</>;
  }

  // Otherwise, return null (will redirect due to useEffect)
  return null;
}

// Higher-order component for route protection
export function withAuth<P extends object>(
  Component: React.ComponentType<P>,
  options: {
    requiredPermissions?: string[];
    redirectTo?: string;
    fallback?: ReactNode;
  } = {}
) {
  return function AuthenticatedComponent(props: P) {
    return (
      <AuthGuard {...options}>
        <Component {...props} />
      </AuthGuard>
    );
  };
}

// Hook for checking permissions in components
export function usePermission() {
  const { hasPermission, isAuthenticated, isLoading } = useAuth();
  
  return {
    hasPermission,
    isAuthenticated,
    isLoading,
    requirePermission: (permission: string) => {
      return isAuthenticated && !isLoading && hasPermission(permission);
    }
  };
}