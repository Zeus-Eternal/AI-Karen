'use client';

import React, { ReactNode } from 'react';
import { ProtectedRoute } from './ProtectedRoute';
import { NavigationLayout } from '@/components/navigation/NavigationLayout';

interface AdminRouteProps {
  children: ReactNode;
  requiredRole?: 'admin' | 'super_admin';
  requiredPermission?: string;
  fallback?: ReactNode;
  redirectTo?: string;
  showNavigation?: boolean;
  showBreadcrumbs?: boolean;
  loadingMessage?: string;
}

/**
 * Route protection component for admin-level access
 * Requires user to be authenticated and have admin or super_admin role
 * Automatically wraps content with NavigationLayout for admin interface
 */
export const AdminRoute: React.FC<AdminRouteProps> = ({ 
  children, 
  requiredRole = 'admin',
  requiredPermission,
  fallback,
  redirectTo = '/unauthorized',
  showNavigation = true,
  showBreadcrumbs = true,
  loadingMessage = 'Loading admin interface...'
}) => {
  // Determine the effective required role
  // If 'admin' is specified, allow both 'admin' and 'super_admin'
  const effectiveRole = requiredRole === 'admin' ? 'admin' : requiredRole;

  return (
    <ProtectedRoute
      requiredRole={effectiveRole}
      requiredPermission={requiredPermission}
      fallback={fallback}
      redirectTo={redirectTo}
      loadingMessage={loadingMessage}
    >
      {showNavigation ? (
        <NavigationLayout showBreadcrumbs={showBreadcrumbs}>
          {children}
        </NavigationLayout>
      ) : (
        children
      )}
    </ProtectedRoute>
  );
};