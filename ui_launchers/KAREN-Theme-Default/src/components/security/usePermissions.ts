"use client";

import { useMemo } from "react";
import { useAuth } from "@/hooks/use-auth";
import {
  ROLE_HIERARCHY,
  ROLE_PERMISSIONS,
  getHighestRole,
  normalizePermission,
  normalizePermissionList,
  type Permission,
  type UserRole,
} from "./rbac-shared";

export interface UsePermissionsResult {
  hasRole: (role: UserRole) => boolean;
  hasPermission: (permission: Permission) => boolean;
  canAccess: (options: { role?: UserRole; permission?: Permission }) => boolean;
  userRole: UserRole;
  isAuthenticated: boolean;
}

export function usePermissions(): UsePermissionsResult {
  const { user, isAuthenticated } = useAuth();

  const userRole = useMemo<UserRole>(() => getHighestRole(user?.roles), [user?.roles]);
  const userRoleLevel = ROLE_HIERARCHY[userRole] ?? 0;

  const hasRole = (role: UserRole): boolean => {
    if (!isAuthenticated) return false;
    const requiredRoleLevel = ROLE_HIERARCHY[role] ?? 0;
    return userRoleLevel >= requiredRoleLevel;
  };

  const hasPermission = (permission: Permission): boolean => {
    if (!isAuthenticated) return false;
    const canonical = normalizePermission(permission);
    if (!canonical) return false;
    const explicitPermissions = normalizePermissionList(user?.permissions);
    const userPermissions = explicitPermissions.length
      ? explicitPermissions
      : ROLE_PERMISSIONS[userRole] ?? [];
    return userPermissions.includes(canonical);
  };

  const canAccess = (options: { role?: UserRole; permission?: Permission }): boolean => {
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
}
