/**
 * usePermissions Hook
 * 
 * This hook provides access to the RBAC permission system for React components.
 * It allows components to check if the current user has specific permissions.
 */

import { useState, useEffect, useCallback } from 'react';
import { Permission, UsePermissionsReturn } from '../../lib/security/rbac/types';
import { rbacService } from '../../lib/security/rbac/RBACService';

/**
 * Hook for checking permissions in React components
 * @returns An object with permission checking functions and state
 */
export const usePermissions = (): UsePermissionsReturn => {
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Initialize the RBAC service if needed
  useEffect(() => {
    const initializeRBAC = async () => {
      try {
        setIsLoading(true);
        setError(null);
        await rbacService.initialize();
        
        // Get the current user's permissions
        const userPermissions = rbacService.getUserPermissions();
        setPermissions(userPermissions);
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

  // Function to refresh the permissions
  const refresh = useCallback(async (): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Get the current user's permissions
      const userPermissions = rbacService.getUserPermissions();
      setPermissions(userPermissions);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      console.error('Error refreshing permissions:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    permissions,
    isLoading,
    error,
    refresh
  };
};

export default usePermissions;