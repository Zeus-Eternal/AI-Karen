/**
 * useRoles Hook
 * 
 * This hook provides access to the RBAC role system for React components.
 * It allows components to check if the current user has specific roles.
 */

import { useState, useEffect, useCallback } from 'react';
import { RoleName, RoleDefinition, UseRolesReturn } from '../../lib/security/rbac/types';
import { rbacService } from '../../lib/security/rbac/RBACService';

/**
 * Hook for checking roles in React components
 * @returns An object with role checking functions and state
 */
export const useRoles = (): UseRolesReturn => {
  const [roles, setRoles] = useState<RoleName[]>([]);
  const [roleDefinitions, setRoleDefinitions] = useState<Record<RoleName, RoleDefinition>>({});
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Initialize the RBAC service if needed
  useEffect(() => {
    const initializeRBAC = async () => {
      try {
        setIsLoading(true);
        setError(null);
        await rbacService.initialize();
        
        // Get the current user's roles
        const userRoles = rbacService.getUserRoles();
        setRoles(userRoles);
        
        // Get all role definitions
        const allRoleDefinitions = rbacService.getAllRoleDefinitions();
        setRoleDefinitions(allRoleDefinitions);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error';
        setError(errorMessage);
        console.error('Error initializing RBAC service:', err);
      } finally {
        setIsLoading(false);
      }
    };

    initializeRBAC();
  }, []);

  // Function to check if the user has a specific role
  const hasRole = useCallback((role: RoleName): boolean => {
    try {
      const result = rbacService.hasRole(role);
      return result.hasRole;
    } catch (err) {
      console.error(`Error checking role ${role}:`, err);
      return false;
    }
  }, []);

  // Function to check if the user has any of the specified roles
  const hasAnyRole = useCallback((roles: RoleName[]): boolean => {
    try {
      const result = rbacService.hasAnyRole(roles);
      return result.hasRole;
    } catch (err) {
      console.error(`Error checking roles ${roles.join(', ')}:`, err);
      return false;
    }
  }, []);

  // Function to check if the user has all of the specified roles
  const hasAllRoles = useCallback((roles: RoleName[]): boolean => {
    try {
      const result = rbacService.hasAllRoles(roles);
      return result.hasRole;
    } catch (err) {
      console.error(`Error checking roles ${roles.join(', ')}:`, err);
      return false;
    }
  }, []);

  // Function to refresh the roles
  const refresh = useCallback(async (): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Get the current user's roles
      const userRoles = rbacService.getUserRoles();
      setRoles(userRoles);
      
      // Get all role definitions
      const allRoleDefinitions = rbacService.getAllRoleDefinitions();
      setRoleDefinitions(allRoleDefinitions);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      console.error('Error refreshing roles:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    hasRole,
    hasAnyRole,
    hasAllRoles,
    roles,
    roleDefinitions,
    isLoading,
    error,
    refresh
  };
};

export default useRoles;