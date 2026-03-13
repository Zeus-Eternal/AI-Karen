/**
 * Role-based hooks for admin management system
 * 
 * Provides convenient hooks for role-based functionality and permission checking
 */

import { useAuth } from '@/hooks/use-auth';

import { RoleName } from '@/lib/security/rbac/types';

export interface UseRoleReturn {
  role: RoleName | null;
  hasRole: (role: RoleName) => boolean;
  hasPermission: (permission: string) => boolean;
  isAdmin: boolean;
  isSuperAdmin: boolean;
  isUser: boolean;
  canManageUsers: boolean;
  canManageAdmins: boolean;
  canManageSystem: boolean;
  canViewAuditLogs: boolean;
}

/**
 * Hook for role-based functionality
 * Provides easy access to user role information and permission checking
 */
export const useRole = (): UseRoleReturn => {
  const { user } = useAuth();

  const role = user?.role || null;
  
  // Helper functions
  const hasRole = (checkRole: RoleName): boolean => {
    return role === checkRole;
  };
  
  const hasPermission = (permission: string): boolean => {
    return user?.permissions?.includes(permission) || false;
  };
  
  const isAdmin = (): boolean => {
    return role === RoleName.ADMIN || role === RoleName.DEVELOPER;
  };
  
  const isSuperAdmin = (): boolean => {
    return role === RoleName.DEVELOPER;
  };
  
  const isUser = hasRole(RoleName.USER);
  
  // Derived permissions based on role
  const canManageUsers = hasPermission('admin:read') || isAdmin();
  const canManageAdmins = hasPermission('admin:write') || isSuperAdmin();
  const canManageSystem = hasPermission('admin:system') || isSuperAdmin();
  const canViewAuditLogs = hasPermission('audit:read') || isAdmin();

  return {
    role: role as RoleName | null,
    hasRole,
    hasPermission,
    isAdmin: isAdmin(),
    isSuperAdmin: isSuperAdmin(),
    isUser,
    canManageUsers,
    canManageAdmins,
    canManageSystem,
    canViewAuditLogs,
  };
};

/**
 * Hook to check if user has specific role
 */
export const useHasRole = (requiredRole: RoleName): boolean => {
  const { user } = useAuth();
  return user?.role === requiredRole;
};

/**
 * Hook to check if user has specific permission
 */
export const useHasPermission = (permission: string): boolean => {
  const { user } = useAuth();
  return user?.permissions?.includes(permission) || false;
};

/**
 * Hook to check if user is admin (admin or super_admin)
 */
export const useIsAdmin = (): boolean => {
  const { user } = useAuth();
  return user?.role === RoleName.ADMIN || user?.role === RoleName.DEVELOPER;
};

/**
 * Hook to check if user is super admin
 */
export const useIsSuperAdmin = (): boolean => {
  const { user } = useAuth();
  return user?.role === RoleName.DEVELOPER;
};