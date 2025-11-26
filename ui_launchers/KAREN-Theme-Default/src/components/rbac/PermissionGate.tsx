/**
 * PermissionGate Component
 * 
 * This component conditionally renders its children based on whether the current user
 * has the specified permissions. It can check for a single permission or multiple permissions,
 * and can require all permissions or any of them.
 */

import React from 'react';
import { PermissionGateProps } from '../../lib/security/rbac/types';
import { useRBAC } from '../hooks/useRBAC';

// Re-export the type for convenience
export type { PermissionGateProps };

/**
 * A component that conditionally renders its children based on permissions
 */
export const PermissionGate: React.FC<PermissionGateProps> = ({
  permissions,
  requireAll = false,
  fallback = null,
  children,
  showError = false
}) => {
  const { hasAnyPermission, hasAllPermissions, error } = useRBAC();

  // Convert single permission to array for uniform handling
  const permissionArray = Array.isArray(permissions) ? permissions : [permissions];

  // Check permissions based on requireAll flag
  const hasRequiredPermissions = requireAll
    ? hasAllPermissions(permissionArray)
    : hasAnyPermission(permissionArray);

  // Show error message if showError is true and there's an error
  if (showError && error) {
    return (
      <div className="rbac-error">
        <p>Error checking permissions: {error}</p>
      </div>
    );
  }

  // Render children if user has required permissions, otherwise render fallback
  return <>{hasRequiredPermissions ? children : fallback}</>;
};

export default PermissionGate;
