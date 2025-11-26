/**
 * RoleGate Component
 * 
 * This component conditionally renders its children based on whether the current user
 * has the specified roles. It can check for a single role or multiple roles,
 * and can require all roles or any of them.
 */

import React from 'react';
import { RoleGateProps } from '../../lib/security/rbac/types';
import { useRBAC } from '../hooks/useRBAC';

/**
 * A component that conditionally renders its children based on roles
 */
export const RoleGate: React.FC<RoleGateProps> = ({
  roles,
  requireAll = false,
  fallback = null,
  children,
  showError = false
}) => {
  const { hasAnyRole, hasAllRoles, error } = useRBAC();

  // Convert single role to array for uniform handling
  const roleArray = Array.isArray(roles) ? roles : [roles];

  // Check roles based on requireAll flag
  const hasRequiredRoles = requireAll
    ? hasAllRoles(roleArray)
    : hasAnyRole(roleArray);

  // Show error message if showError is true and there's an error
  if (showError && error) {
    return (
      <div className="rbac-error">
        <p>Error checking roles: {error}</p>
      </div>
    );
  }

  // Render children if user has required roles, otherwise render fallback
  return <>{hasRequiredRoles ? children : fallback}</>;
};

export default RoleGate;