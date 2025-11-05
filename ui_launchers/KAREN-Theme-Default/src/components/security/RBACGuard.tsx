"use client";

import React, { useMemo } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useFeature } from "@/hooks/use-feature";
import { useTelemetry } from "@/hooks/use-telemetry";

export type UserRole = "admin" | "user" | "guest" | "moderator" | "developer";
export type Permission =
  | "chat.send"
  | "chat.code_assistance"
  | "chat.explanations"
  | "chat.documentation"
  | "chat.analysis"
  | "voice.input"
  | "voice.output"
  | "attachments.upload"
  | "attachments.download"
  | "admin.settings"
  | "admin.users"
  | "developer.debug"
  | "moderator.content";

interface RBACGuardProps {
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

/** Role hierarchy — higher index means higher privilege and inherits below. */
const ROLE_HIERARCHY: Record<UserRole, number> = {
  guest: 0,
  user: 1,
  moderator: 2,
  developer: 3,
  admin: 4,
} as const;

/** Permissions by role (admin includes all). */
const ROLE_PERMISSIONS: Record<UserRole, Permission[]> = {
  guest: ["chat.send"],
  user: [
    "chat.send",
    "chat.code_assistance",
    "chat.explanations",
    "chat.documentation",
    "chat.analysis",
    "voice.input",
    "voice.output",
    "attachments.upload",
    "attachments.download",
  ],
  moderator: [
    "chat.send",
    "chat.code_assistance",
    "chat.explanations",
    "chat.documentation",
    "chat.analysis",
    "voice.input",
    "voice.output",
    "attachments.upload",
    "attachments.download",
    "moderator.content",
  ],
  developer: [
    "chat.send",
    "chat.code_assistance",
    "chat.explanations",
    "chat.documentation",
    "chat.analysis",
    "voice.input",
    "voice.output",
    "attachments.upload",
    "attachments.download",
    "developer.debug",
  ],
  admin: [
    "chat.send",
    "chat.code_assistance",
    "chat.explanations",
    "chat.documentation",
    "chat.analysis",
    "voice.input",
    "voice.output",
    "attachments.upload",
    "attachments.download",
    "moderator.content",
    "developer.debug",
    "admin.settings",
    "admin.users",
  ],
} as const;

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

/** Helper: compute the highest role a user possesses. */
function getHighestRole(roles: string[] | undefined | null): UserRole {
  if (!roles || roles.length === 0) return "guest";
  let best: UserRole = "guest";
  let bestLevel = ROLE_HIERARCHY[best];
  for (const r of roles) {
    const role = (r as UserRole) || "guest";
    const lvl = ROLE_HIERARCHY[role] ?? 0;
    if (lvl > bestLevel) {
      best = role;
      bestLevel = lvl;
    }
  }
  return best;
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
  const userRole = useMemo<UserRole>(() => getHighestRole(user.roles), [user.roles]);
  const userRoleLevel = ROLE_HIERARCHY[userRole] ?? 0;

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

/**
 * Utility hook for checking permissions inside components.
 *
 * NOTE ON FEATURE FLAGS:
 * Hooks cannot be called conditionally or from arbitrary functions.
 * Therefore, this helper does NOT evaluate feature flags internally.
 * Use <RBACGuard featureFlag="flag.key"> to enforce a flag at render-time.
 */
export const usePermissions = () => {
  const { user, isAuthenticated } = useAuth();

  const userRole = useMemo<UserRole>(() => getHighestRole(user?.roles), [user?.roles]);
  const userRoleLevel = ROLE_HIERARCHY[userRole] ?? 0;

  const hasRole = (role: UserRole): boolean => {
    if (!isAuthenticated) return false;
    const requiredRoleLevel = ROLE_HIERARCHY[role] ?? 0;
    return userRoleLevel >= requiredRoleLevel;
    // Higher roles inherit lower by design.
  };

  const hasPermission = (permission: Permission): boolean => {
    if (!isAuthenticated) return false;
    const userPermissions = ROLE_PERMISSIONS[userRole] ?? [];
    return userPermissions.includes(permission);
  };

  /**
   * Lightweight composite check for role/permission.
   * Feature flags are intentionally NOT checked here (see note above).
   */
  const canAccess = (options: {
    role?: UserRole;
    permission?: Permission;
    /** Deprecated: Not evaluated here. Use <RBACGuard featureFlag="...">. */
    featureFlag?: string;
  }): boolean => {
    if (options.role && !hasRole(options.role)) return false;
    if (options.permission && !hasPermission(options.permission)) return false;
    return true;
  };

  return {
    hasRole,
    hasPermission,
    canAccess,
    userRole,
    isAuthenticated,
  };
};

export default RBACGuard;
