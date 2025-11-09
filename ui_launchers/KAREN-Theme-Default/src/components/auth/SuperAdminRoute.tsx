"use client";

import React, { ReactNode } from 'react';
import { ProtectedRoute } from './ProtectedRoute';
import { NavigationLayout } from '@/components/navigation/NavigationLayout';

export interface SuperAdminRouteProps {
  children: ReactNode;
  requiredPermission?: string;
  fallback?: ReactNode;
  redirectTo?: string;
  showNavigation?: boolean;
  showBreadcrumbs?: boolean;
  loadingMessage?: string;
}

/**
 * Route protection component for super admin access
 * Requires user to be authenticated and have super_admin role
 * Automatically wraps content with NavigationLayout for super admin interface
 */
export const SuperAdminRoute: React.FC<SuperAdminRouteProps> = ({ 
  children, 
  requiredPermission,
  fallback,
  redirectTo = '/unauthorized',
  showNavigation = true,
  showBreadcrumbs = true,
  loadingMessage = 'Loading super admin interface...'
}) => {
  return (
    <ProtectedRoute
      requiredRole="super_admin"
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