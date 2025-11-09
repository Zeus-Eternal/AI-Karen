"use client";

import React, { ReactNode, useMemo } from "react";
import { ProtectedRoute } from "./ProtectedRoute";
import { NavigationLayout } from "@/components/navigation/NavigationLayout";

/**
 * Props for admin-protected routes within the application.
 * This layer handles both role-based (admin/super_admin) and permission-based gating,
 * while optionally wrapping children with the NavigationLayout shell.
 */
export interface AdminRouteProps {
  /** Route content */
  children: ReactNode;
  /** Minimum required role to access this route */
  requiredRole?: "admin" | "super_admin";
  /** Optional fine-grained permission key (e.g., "security:audit") */
  requiredPermission?: string;
  /** Optional fallback node when unauthorized (default: redirect) */
  fallback?: ReactNode;
  /** Redirection target when unauthorized (default: `/unauthorized`) */
  redirectTo?: string;
  /** Whether to show full navigation layout (sidebar, topbar, breadcrumbs) */
  showNavigation?: boolean;
  /** Whether to show breadcrumbs when using NavigationLayout */
  showBreadcrumbs?: boolean;
  /** Custom loading message while auth state resolves */
  loadingMessage?: string;
}

/**
 * 🔐 AdminRoute
 *
 * Role-based + permission-based gate for admin and super_admin areas.
 * Automatically wraps children inside Kari’s Admin NavigationLayout unless disabled.
 *
 * This is the main shield that prevents unauthorized users from entering
 * critical interfaces like `/admin`, `/system`, `/audit`, `/settings`, etc.
 *
 * Example usage:
 * ```tsx
 * <AdminRoute requiredRole="super_admin">
 *   <SystemConfigPanel />
 * </AdminRoute>
 * ```
 */
export const AdminRoute: React.FC<AdminRouteProps> = ({
  children,
  requiredRole = "admin",
  requiredPermission,
  fallback,
  redirectTo = "/unauthorized",
  showNavigation = true,
  showBreadcrumbs = true,
  loadingMessage = "Loading admin interface...",
}) => {
  // Allow super_admins to access all admin routes by default
  const effectiveRole = useMemo<"admin" | "super_admin">(
    () => (requiredRole === "admin" ? "admin" : "super_admin"),
    [requiredRole]
  );

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
