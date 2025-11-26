/**
 * useRBAC Hook
 * 
 * This hook combines the functionality of usePermissions and useRoles into a single hook.
 * It provides access to both permission and role checking functions for React components.
 */

import { useState, useEffect, useCallback } from 'react';
import { 
  User, 
  Permission, 
  RoleName, 
  RoleDefinition, 
  UseRBACReturn 
} from '../../lib/security/rbac/types';
import { rbacService } from '../../lib/security/rbac/RBACService';

/**
 * Hook for checking both permissions and roles in React components
 * @returns An object with permission and role checking functions and state
 */
export const useRBAC = (): UseRBACReturn => {
  const [user, setUser] = useState<User | null>(null);
  const [permissions, setPermissions] = useState<Permission[]>([]);
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
        
        // Get the current user
        const currentUser = rbacService.getCurrentUser();
        setUser(currentUser);
        
        if (currentUser) {
          // Get the current user's permissions
          const userPermissions = rbacService.getUserPermissions();
          setPermissions(userPermissions);
          
          // Get the current user's roles
          const userRoles = rbacService.getUserRoles();
          setRoles(userRoles);
        }
        
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

  // Function to check if the user has a specific permission
  const hasPermission = useCallback((permission: Permission): boolean => {
    try {
      const result = rbacService.hasPermission(permission);
      return result.hasPermission ?? false;
    } catch (err) {
      console.error(`Error checking permission ${permission}:`, err);
      return false;
    }
  }, []);

  // Function to check if the user has any of the specified permissions
  const hasAnyPermission = useCallback((permissions: Permission[]): boolean => {
    try {
      const result = rbacService.hasAnyPermission(permissions);
      return result.hasPermission ?? false;
    } catch (err) {
      console.error(`Error checking permissions ${permissions.join(', ')}:`, err);
      return false;
    }
  }, []);

  // Function to check if the user has all of the specified permissions
  const hasAllPermissions = useCallback((permissions: Permission[]): boolean => {
    try {
      const result = rbacService.hasAllPermissions(permissions);
      return result.hasPermission ?? false;
    } catch (err) {
      console.error(`Error checking permissions ${permissions.join(', ')}:`, err);
      return false;
    }
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

  // Function to refresh the permissions and roles
  const refreshPermissions = useCallback(async (): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Get the current user
      const currentUser = rbacService.getCurrentUser();
      setUser(currentUser);
      
      if (currentUser) {
        // Get the current user's permissions
        const userPermissions = rbacService.getUserPermissions();
        setPermissions(userPermissions);
        
        // Get the current user's roles
        const userRoles = rbacService.getUserRoles();
        setRoles(userRoles);
      }
      
      // Get all role definitions
      const allRoleDefinitions = rbacService.getAllRoleDefinitions();
      setRoleDefinitions(allRoleDefinitions);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      console.error('Error refreshing permissions and roles:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    user,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    hasRole,
    hasAnyRole,
    hasAllRoles,
    permissions,
    roles,
    roleDefinitions,
    isLoading,
    error,
    refresh: refreshPermissions,
    refreshPermissions
  };
};

export default useRBAC;