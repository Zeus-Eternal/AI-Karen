"use client";

import * as React from 'react';
import { Permission, AccessContext } from '@/lib/security/rbac/types';
import { useRBAC } from '@/providers/rbac-hooks';

import { PermissionGate } from './PermissionGate';

export interface WithPermissionOptions<P extends object = object> {
  requireAll?: boolean;
  fallback?: React.ComponentType<P>;
  showFallback?: boolean;
}

export function withPermission<P extends object>(
  Component: React.ComponentType<P>,
  permission: Permission | Permission[],
  options: WithPermissionOptions<P> = {},
) {
  const { requireAll = false, fallback: FallbackComponent } = options;

  return function PermissionWrappedComponent(props: P) {
    return (
      <PermissionGate
        permissions={permission}
        requireAll={requireAll}
        fallback={FallbackComponent ? <FallbackComponent {...props} /> : undefined}
      >
        <Component {...props} />
      </PermissionGate>
    );
  };
}

export interface UsePermissionGateResult {
  hasAccess: boolean;
  permissionResult: unknown;
  canRender: boolean;
}

export function usePermissionGate(
  permission: Permission | Permission[],
  requireAll: boolean = false,
  context?: Partial<AccessContext>,
): UsePermissionGateResult {
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
    canRender: hasAccess,
  };
}
