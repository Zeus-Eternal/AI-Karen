/**
 * Permission and role utility functions
 * 
 * Provides utility functions for role-based access control and permission checking
 */

export type UserRole = 'super_admin' | 'admin' | 'user';

export interface PermissionCheck {
  hasRole: (role: UserRole) => boolean;
  hasPermission: (permission: string) => boolean;
  isAdmin: () => boolean;
  isSuperAdmin: () => boolean;
}

/**
 * Default permissions for each role
 */
export const ROLE_PERMISSIONS: Record<UserRole, string[]> = {
  super_admin: [
    'user_management',
    'admin_management', 
    'system_config',
    'audit_logs',
    'security_settings',
    'user_create',
    'user_edit',
    'user_delete',
    'admin_create',
    'admin_edit',
    'admin_delete',
    'system_backup',
    'system_restore',
    'security_monitor'
  ],
  admin: [
    'user_management',
    'user_create',
    'user_edit',
    'user_delete',
    'user_view'
  ],
  user: []
};

/**
 * Check if a role has a specific permission
 */
export function roleHasPermission(role: UserRole, permission: string): boolean {
  return ROLE_PERMISSIONS[role]?.includes(permission) ?? false;
}

/**
 * Check if a role is higher or equal to another role
 */
export function roleHierarchy(userRole: UserRole, requiredRole: UserRole): boolean {
  const hierarchy: Record<UserRole, number> = {
    user: 1,
    admin: 2,
    super_admin: 3
  };

  return hierarchy[userRole] >= hierarchy[requiredRole];
}

/**
 * Get all permissions for a role
 */
export function getRolePermissions(role: UserRole): string[] {
  return ROLE_PERMISSIONS[role] || [];
}

/**
 * Check if user has required role (considering hierarchy)
 */
export function hasRequiredRole(userRole: UserRole, requiredRole: UserRole): boolean {
  return roleHierarchy(userRole, requiredRole);
}

/**
 * Utility function to create permission checker from user data
 */
export function createPermissionChecker(
  userRole?: UserRole, 
  userRoles?: string[], 
  userPermissions?: string[]
): PermissionCheck {
  const role = userRole || determineUserRole(userRoles || []);
  
  return {
    hasRole: (requiredRole: UserRole) => hasRequiredRole(role, requiredRole),
    hasPermission: (permission: string) => {
      // Check explicit permissions first
      if (userPermissions?.includes(permission)) {
        return true;
      }
      // Fall back to role-based permissions
      return roleHasPermission(role, permission);
    },
    isAdmin: () => role === 'admin' || role === 'super_admin',
    isSuperAdmin: () => role === 'super_admin'
  };
}

/**
 * Determine primary role from roles array
 */
export function determineUserRole(roles: string[]): UserRole {
  if (roles.includes('super_admin')) return 'super_admin';
  if (roles.includes('admin')) return 'admin';
  return 'user';
}

/**
 * Validate role string
 */
export function isValidRole(role: string): role is UserRole {
  return ['super_admin', 'admin', 'user'].includes(role);
}

/**
 * Get role display name
 */
export function getRoleDisplayName(role: UserRole): string {
  switch (role) {
    case 'super_admin':
      return 'Super Admin';
    case 'admin':
      return 'Admin';
    case 'user':
      return 'User';
    default:
      return 'Unknown';
  }
}

/**
 * Get role description
 */
export function getRoleDescription(role: UserRole): string {
  switch (role) {
    case 'super_admin':
      return 'Full system access including user management, admin management, and system configuration';
    case 'admin':
      return 'User management access with ability to create, edit, and delete user accounts';
    case 'user':
      return 'Standard user access with no administrative privileges';
    default:
      return 'Unknown role';
  }
}

/**
 * Check if role can manage another role
 */
export function canManageRole(managerRole: UserRole, targetRole: UserRole): boolean {
  // Super admins can manage everyone
  if (managerRole === 'super_admin') {
    return true;
  }
  
  // Admins can manage users but not other admins or super admins
  if (managerRole === 'admin') {
    return targetRole === 'user';
  }
  
  // Users cannot manage anyone
  return false;
}