"use client";

import React, { useMemo } from "react";
import { useAuth } from "@/hooks/use-auth";
import { useFeature } from "@/hooks/use-feature";
import { useTelemetry } from "@/hooks/use-telemetry";
import {
  ROLE_HIERARCHY,
  ROLE_PERMISSIONS,
  getHighestRole,
  type Permission,
  type UserRole,
} from "./rbac-shared";
export type { Permission, UserRole } from "./rbac-shared";

export interface RBACGuardProps {
  children: React.ReactNode;
  requiredRole?: UserRole;
  requiredPermission?: Permission;
  /** Feature flag key to gate this block. */
  featureFlag?: string;
  /** Rendered if access is denied. Defaults to null. */
  fallback?: React.ReactNode;
  /** Optional callback when access is denied. */
  onAccessDenied?: (reason: string) => void;
  className?: string;
}

/** Safely emit telemetry without risking render errors. */
function safeTrack(
  track: ((name: string, props?: Record<string, unknown>) => void) | undefined,
  name: string,
  props?: Record<string, unknown>
) {
  try {
    track?.(name, props);
  } catch {
    /* swallow */
  }
}

export const RBACGuard: React.FC<RBACGuardProps> = ({
  children,
  requiredRole,
  requiredPermission,
  featureFlag,
  fallback = null,
  onAccessDenied,
  className,
}) => {
  const { user, isAuthenticated } = useAuth();
  const { track } = useTelemetry();

  // Feature flag gate (hooks must be called unconditionally)
  // If no flag provided, consider it enabled.
  const isFeatureEnabled = useFeature(featureFlag);
  const userRoles = user?.roles;
  const userRole = useMemo<UserRole>(() => getHighestRole(userRoles), [userRoles]);
  const userRoleLevel = ROLE_HIERARCHY[userRole] ?? 0;

  if (featureFlag && !isFeatureEnabled) {
    safeTrack(track, "rbac_access_denied", {
      reason: "feature_disabled",
      featureFlag,
      userId: user?.userId ?? null,
    });
    onAccessDenied?.("Feature is currently disabled");
    return <>{fallback}</>;
  }

  // Authentication gate
  if (!isAuthenticated || !user) {
    safeTrack(track, "rbac_access_denied", {
      reason: "not_authenticated",
      requiredRole: requiredRole ?? null,
      requiredPermission: requiredPermission ?? null,
      userId: null,
    });
    onAccessDenied?.("Authentication required");
    return <>{fallback}</>;
  }

  // Role resolution (supports multi-role users; we take the highest)
  // Role check
  if (requiredRole) {
    const requiredRoleLevel = ROLE_HIERARCHY[requiredRole] ?? 0;
    if (userRoleLevel < requiredRoleLevel) {
      safeTrack(track, "rbac_access_denied", {
        reason: "insufficient_role",
        userRole,
        requiredRole,
        userId: user.userId,
      });
      onAccessDenied?.(
        `Role '${requiredRole}' required, but user has '${userRole}'.`
      );
      return <>{fallback}</>;
    }
  }

  // Permission check
  if (requiredPermission) {
    const userPermissions = ROLE_PERMISSIONS[userRole] ?? [];
    if (!userPermissions.includes(requiredPermission)) {
      safeTrack(track, "rbac_access_denied", {
        reason: "insufficient_permission",
        userRole,
        requiredPermission,
        userPermissions,
        userId: user.userId,
      });
      onAccessDenied?.(`Permission '${requiredPermission}' required`);
      return <>{fallback}</>;
    }
  }

  // Access granted
  safeTrack(track, "rbac_access_granted", {
    userRole,
    requiredRole: requiredRole ?? null,
    requiredPermission: requiredPermission ?? null,
    featureFlag: featureFlag ?? null,
    userId: user.userId,
  });

  return (
    <div className={className} data-rbac-protected="true">
      {children}
    </div>
  );
};

export default RBACGuard;
