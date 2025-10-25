/**
 * Role-based hooks for admin management system
 * 
 * Provides convenient hooks for role-based functionality and permission checking
 */

import { useAuth } from '@/contexts/AuthContext';

export interface UseRoleReturn {
  role: 'super_admin' | 'admin' | 'user' | null;
  hasRole: (role: 'super_admin' | 'admin' | 'user') => boolean;
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
  const { user, hasRole, hasPermission, isAdmin, isSuperAdmin } = useAuth();

  const role = user?.role || null;
  const isUser = hasRole('user');
  
  // Derived permissions based on role
  const canManageUsers = hasPermission('user_management');
  const canManageAdmins = hasPermission('admin_management');
  const canManageSystem = hasPermission('system_config');
  const canViewAuditLogs = hasPermission('audit_logs');

  return {
    role,
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
export const useHasRole = (requiredRole: 'super_admin' | 'admin' | 'user'): boolean => {
  const { hasRole } = useAuth();
  return hasRole(requiredRole);
};

/**
 * Hook to check if user has specific permission
 */
export const useHasPermission = (permission: string): boolean => {
  const { hasPermission } = useAuth();
  return hasPermission(permission);
};

/**
 * Hook to check if user is admin (admin or super_admin)
 */
export const useIsAdmin = (): boolean => {
  const { isAdmin } = useAuth();
  return isAdmin();
};

/**
 * Hook to check if user is super admin
 */
export const useIsSuperAdmin = (): boolean => {
  const { isSuperAdmin } = useAuth();
  return isSuperAdmin();
};