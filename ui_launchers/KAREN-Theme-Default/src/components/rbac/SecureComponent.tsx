/**
 * SecureComponent
 * 
 * This component conditionally renders its children based on whether the current user
 * has the specified permissions and/or roles. It can check for a single permission/role
 * or multiple permissions/roles, and can require all permissions/roles or any of them.
 */

import React from 'react';
import { SecureComponentProps } from '../../lib/security/rbac/types';
import { useRBAC } from '../hooks/useRBAC';

/**
 * A component that conditionally renders its children based on permissions and/or roles
 */
export const SecureComponent: React.FC<SecureComponentProps> = ({
  permissions,
  roles,
  requireAll = false,
  fallback = null,
  children,
  showError = false
}) => {
  const {
    hasAnyPermission,
    hasAllPermissions,
    hasAnyRole,
    hasAllRoles,
    error
  } = useRBAC();

  // Check if user has required permissions
  let hasRequiredPermissions = true;
  if (permissions) {
    const permissionArray = Array.isArray(permissions) ? permissions : [permissions];
    hasRequiredPermissions = requireAll
      ? hasAllPermissions(permissionArray)
      : hasAnyPermission(permissionArray);
  }

  // Check if user has required roles
  let hasRequiredRoles = true;
  if (roles) {
    const roleArray = Array.isArray(roles) ? roles : [roles];
    hasRequiredRoles = requireAll
      ? hasAllRoles(roleArray)
      : hasAnyRole(roleArray);
  }

  // Determine if user has all required permissions and/or roles
  const hasAccess = hasRequiredPermissions && hasRequiredRoles;

  // Show error message if showError is true and there's an error
  if (showError && error) {
    return (
      <div className="rbac-error">
        <p>Error checking permissions and roles: {error}</p>
      </div>
    );
  }

  // Render children if user has required permissions and/or roles, otherwise render fallback
  return <>{hasAccess ? children : fallback}</>;
};

export default SecureComponent;