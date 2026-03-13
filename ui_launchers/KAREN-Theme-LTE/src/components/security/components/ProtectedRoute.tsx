/**
 * Protected Route Component for the CoPilot frontend.
 * 
 * This component provides route protection based on authentication,
 * authorization, and other security requirements.
 */

import React, { useEffect, ReactNode } from 'react';
import { useRouter } from 'next/router';
import { useSecurity } from '../contexts/SecurityContext';

// Props interface
interface ProtectedRouteProps {
  children: ReactNode;
  requireAuth?: boolean;
  requireMfa?: boolean;
  permissions?: string[];
  roles?: string[];
  requireAll?: boolean; // If true, require all permissions/roles, if false, require any
  fallbackPath?: string;
  loadingComponent?: ReactNode;
  errorComponent?: ReactNode;
  onUnauthorized?: (reason: string) => void;
}

// Loading component
const DefaultLoadingComponent = () => (
  <div className="flex items-center justify-center min-h-screen">
    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
  </div>
);

// Error component
const DefaultErrorComponent = ({ message }: { message: string }) => (
  <div className="flex items-center justify-center min-h-screen">
    <div className="text-center">
      <h1 className="text-2xl font-bold text-gray-900 mb-4">Access Denied</h1>
      <p className="text-gray-600">{message}</p>
    </div>
  </div>
);

// Protected Route Component
export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requireAuth = true,
  requireMfa = false,
  permissions = [],
  roles = [],
  requireAll = false,
  fallbackPath = '/login',
  loadingComponent = <DefaultLoadingComponent />,
  errorComponent = <DefaultErrorComponent message="You do not have permission to access this page." />,
  onUnauthorized,
}) => {
  const router = useRouter();
  const { auth, user, hasPermission, hasRole, hasAnyPermission, hasAnyRole } = useSecurity();

  // Check if user is authenticated
  const isAuthenticated = auth.isAuthenticated;

  // Check if user has MFA enabled (when required)
  const hasMfa = user?.isMfaEnabled || false;

  // Check permissions
  const hasRequiredPermissions = permissions.length > 0
    ? requireAll
      ? permissions.every(permission => hasPermission(permission))
      : hasAnyPermission(permissions)
    : true;

  // Check roles
  const hasRequiredRoles = roles.length > 0
    ? requireAll
      ? roles.every(role => hasRole(role))
      : hasAnyRole(roles)
    : true;

  // Determine if access is granted
  const accessGranted = (
    (!requireAuth || isAuthenticated) &&
    (!requireMfa || hasMfa) &&
    hasRequiredPermissions &&
    hasRequiredRoles
  );

  // Handle unauthorized access
  useEffect(() => {
    if (auth.isLoading) return;

    if (!accessGranted) {
      let reason = '';
      
      if (requireAuth && !isAuthenticated) {
        reason = 'Authentication required';
      } else if (requireMfa && !hasMfa) {
        reason = 'Multi-factor authentication required';
      } else if (!hasRequiredPermissions) {
        reason = 'Insufficient permissions';
      } else if (!hasRequiredRoles) {
        reason = 'Insufficient role privileges';
      }

      // Call custom unauthorized handler if provided
      if (onUnauthorized) {
        onUnauthorized(reason);
      }

      // Redirect to fallback path
      if (requireAuth && !isAuthenticated) {
        router.push({
          pathname: fallbackPath,
          query: { returnUrl: router.asPath },
        });
      }
    }
  }, [
    accessGranted,
    isAuthenticated,
    hasMfa,
    hasRequiredPermissions,
    hasRequiredRoles,
    auth.isLoading,
    router,
    fallbackPath,
    onUnauthorized,
    requireAuth,
    requireMfa,
  ]);

  // Show loading component while checking auth
  if (auth.isLoading) {
    return <>{loadingComponent}</>;
  }

  // Show error component if access is denied
  if (!accessGranted) {
    return <>{errorComponent}</>;
  }

  // Render children if access is granted
  return <>{children}</>;
};

// Higher-order component for protecting routes
export function withProtection<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  options: Omit<ProtectedRouteProps, 'children'> = {}
) {
  const WithProtectionComponent = (props: P) => (
    <ProtectedRoute {...options}>
      <WrappedComponent {...props} />
    </ProtectedRoute>
  );

  WithProtectionComponent.displayName = `withProtection(${WrappedComponent.displayName || WrappedComponent.name})`;

  return WithProtectionComponent;
}

// Permission-based component
export const PermissionGuard: React.FC<{
  children: ReactNode;
  permissions: string[];
  requireAll?: boolean;
  fallback?: ReactNode;
}> = ({ children, permissions, requireAll = false, fallback = null }) => {
  const { hasPermission, hasAnyPermission } = useSecurity();

  const hasRequiredPermissions = requireAll
    ? permissions.every(permission => hasPermission(permission))
    : hasAnyPermission(permissions);

  if (!hasRequiredPermissions) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};

// Role-based component
export const RoleGuard: React.FC<{
  children: ReactNode;
  roles: string[];
  requireAll?: boolean;
  fallback?: ReactNode;
}> = ({ children, roles, requireAll = false, fallback = null }) => {
  const { hasRole, hasAnyRole } = useSecurity();

  const hasRequiredRoles = requireAll
    ? roles.every(role => hasRole(role))
    : hasAnyRole(roles);

  if (!hasRequiredRoles) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};

// MFA-required component
export const MfaGuard: React.FC<{
  children: ReactNode;
  fallback?: ReactNode;
  redirectTo?: string;
}> = ({ children, fallback = null, redirectTo = '/mfa/setup' }) => {
  const { user } = useSecurity();
  const router = useRouter();
  const hasMfa = user?.isMfaEnabled || false;

  useEffect(() => {
    if (!hasMfa && redirectTo) {
      router.push(redirectTo);
    }
  }, [hasMfa, router, redirectTo]);

  if (!hasMfa) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};

// Auth-required component
export const AuthGuard: React.FC<{
  children: ReactNode;
  fallback?: ReactNode;
  redirectTo?: string;
}> = ({ children, fallback = null, redirectTo = '/login' }) => {
  const { auth } = useSecurity();
  const router = useRouter();
  const { isAuthenticated } = auth;

  useEffect(() => {
    if (!isAuthenticated && redirectTo) {
      router.push({
        pathname: redirectTo,
        query: { returnUrl: router.asPath },
      });
    }
  }, [isAuthenticated, router, redirectTo]);

  if (!isAuthenticated) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};

// Guest-only component (only for non-authenticated users)
export const GuestGuard: React.FC<{
  children: ReactNode;
  fallback?: ReactNode;
  redirectTo?: string;
}> = ({ children, fallback = null, redirectTo = '/dashboard' }) => {
  const { auth } = useSecurity();
  const router = useRouter();
  const { isAuthenticated } = auth;

  useEffect(() => {
    if (isAuthenticated && redirectTo) {
      router.push(redirectTo);
    }
  }, [isAuthenticated, router, redirectTo]);

  if (isAuthenticated) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};

// Export all guards
export {
  DefaultLoadingComponent,
  DefaultErrorComponent,
};
