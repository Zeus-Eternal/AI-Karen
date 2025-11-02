'use client';

import React from 'react';
import { Permission, AccessContext } from '@/types/rbac';
import { useRBAC } from '@/providers/rbac-provider';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ShieldX, Lock, AlertTriangle } from 'lucide-react';

interface PermissionGateProps {
  permission: Permission | Permission[];
  requireAll?: boolean; // If true, requires all permissions; if false, requires any
  context?: Partial<AccessContext>;
  fallback?: React.ReactNode;
  showFallback?: boolean;
  children: React.ReactNode;
}

/**
 * PermissionGate component that conditionally renders children based on user permissions.
 * Provides graceful degradation for unauthorized access.
 */
export function PermissionGate({
  permission,
  requireAll = false,
  context,
  fallback,
  showFallback = true,
  children
}: PermissionGateProps) {
  const { hasPermission, hasAllPermissions, hasAnyPermission, checkPermission } = useRBAC();

  // Determine if user has required permissions
  const hasAccess = React.useMemo(() => {
    if (Array.isArray(permission)) {
      return requireAll 
        ? hasAllPermissions(permission)
        : hasAnyPermission(permission);
    }
    return hasPermission(permission, context);
  }, [permission, requireAll, context, hasPermission, hasAllPermissions, hasAnyPermission]);

  // Get detailed permission check result for better error messages
  const permissionResult = React.useMemo(() => {
    if (Array.isArray(permission)) {
      // For arrays, check the first permission for detailed info
      return checkPermission(permission[0], context);
    }
    return checkPermission(permission, context);
  }, [permission, context, checkPermission]);

  if (hasAccess) {
    return <>{children}</>;
  }

  // Show fallback if provided
  if (fallback) {
    return <>{fallback}</>;
  }

  // Show default fallback if enabled
  if (showFallback) {
    return <PermissionDeniedFallback permissionResult={permissionResult} />;
  }

  // Don't render anything
  return null;
}

interface PermissionDeniedFallbackProps {
  permissionResult: any;
}

function PermissionDeniedFallback({ permissionResult }: PermissionDeniedFallbackProps) {
  const getIcon = () => {
    if (permissionResult.requiresElevation) {
      return <AlertTriangle className="h-4 w-4 sm:w-auto md:w-full" />;
    }
    if (permissionResult.restrictions?.length > 0) {
      return <Lock className="h-4 w-4 sm:w-auto md:w-full" />;
    }
    return <ShieldX className="h-4 w-4 sm:w-auto md:w-full" />;
  };

  const getVariant = () => {
    if (permissionResult.requiresElevation) {
      return 'default' as const;
    }
    return 'destructive' as const;
  };

  return (
    <Alert variant={getVariant()} className="my-2">
      {getIcon()}
      <AlertDescription>
        {permissionResult.reason}
        {permissionResult.elevationReason && (
          <div className="mt-1 text-sm text-muted-foreground md:text-base lg:text-lg">
            {permissionResult.elevationReason}
          </div>
        )}
      </AlertDescription>
    </Alert>
  );
}

/**
 * Higher-order component that wraps a component with permission checking
 */
export function withPermission<P extends object>(
  Component: React.ComponentType<P>,
  permission: Permission | Permission[],
  options: {
    requireAll?: boolean;
    fallback?: React.ComponentType<P>;
    showFallback?: boolean;
  } = {}
) {
  const { requireAll = false, fallback: FallbackComponent, showFallback = true } = options;

  return function PermissionWrappedComponent(props: P) {
    return (
      <PermissionGate
        permission={permission}
        requireAll={requireAll}
        fallback={FallbackComponent ? <FallbackComponent {...props} /> : undefined}
        showFallback={showFallback}
      >
        <Component {...props} />
      </PermissionGate>
    );
  };
}

/**
 * Hook for conditional rendering based on permissions
 */
export function usePermissionGate(
  permission: Permission | Permission[],
  requireAll: boolean = false,
  context?: Partial<AccessContext>
) {
  const { hasPermission, hasAllPermissions, hasAnyPermission, checkPermission } = useRBAC();

  const hasAccess = React.useMemo(() => {
    if (Array.isArray(permission)) {
      return requireAll 
        ? hasAllPermissions(permission)
        : hasAnyPermission(permission);
    }
    return hasPermission(permission, context);
  }, [permission, requireAll, context, hasPermission, hasAllPermissions, hasAnyPermission]);

  const permissionResult = React.useMemo(() => {
    if (Array.isArray(permission)) {
      return checkPermission(permission[0], context);
    }
    return checkPermission(permission, context);
  }, [permission, context, checkPermission]);

  return {
    hasAccess,
    permissionResult,
    canRender: hasAccess
  };
}