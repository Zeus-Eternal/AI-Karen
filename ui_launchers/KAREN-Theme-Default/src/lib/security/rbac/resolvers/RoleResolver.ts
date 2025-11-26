/**
 * Role Resolver
 * 
 * This class is responsible for resolving role permissions and handling role inheritance.
 * It provides methods to check if a user has a specific role, resolve all permissions for a role,
 * and handle role inheritance hierarchies.
 */

import { RoleName, Permission, User, PermissionCheckResult, RoleCheckResult } from '../types';
import { RoleNotFoundError } from '../utils/errors';
import { roleRegistry } from '../registries/RoleRegistry';
import { permissionRegistry } from '../registries/PermissionRegistry';

/**
 * The RoleResolver class handles role resolution and permission checking.
 */
export class RoleResolver {
  private cache: Map<string, { permissions: Permission[]; timestamp: number }> = new Map();
  private cacheTTL: number;

  /**
   * Create a new RoleResolver instance
   * @param cacheTTL The time-to-live for the cache in milliseconds
   */
  constructor(cacheTTL: number = 5 * 60 * 1000) { // Default 5 minutes
    this.cacheTTL = cacheTTL;
  }

  /**
   * Check if a user has a specific role
   * @param user The user to check
   * @param roleName The role name to check for
   * @returns A RoleCheckResult object with the result
   */
  public hasRole(user: User, roleName: RoleName): RoleCheckResult {
    try {
      // Validate inputs
      if (!user || !user.id) {
        return {
          hasRole: false,
          reason: 'Invalid user object'
        };
      }
      
      if (!roleName) {
        return {
          hasRole: false,
          reason: 'Invalid role name'
        };
      }
      
      // Check if the user has roles array
      if (!Array.isArray(user.roles)) {
        console.warn('RoleResolver: User roles is not an array', user);
        return {
          hasRole: false,
          reason: 'User roles is not properly defined'
        };
      }
      
      // Check if the role exists
      try {
        roleRegistry.getRole(roleName);
      } catch (error) {
        if (error instanceof RoleNotFoundError) {
          return {
            hasRole: false,
            reason: `Role '${roleName}' does not exist`
          };
        }
        throw error;
      }
      
      // Check if the user has the role
      const hasRole = user.roles.includes(roleName);
      
      return {
        hasRole,
        reason: hasRole ? 'User has the role' : 'User does not have the role'
      };
    } catch (error) {
      console.error('RoleResolver: Error in hasRole:', error);
      
      // Return a safe default on error
      return {
        hasRole: false,
        reason: `Error checking role: ${error instanceof Error ? error.message : 'Unknown error'}`
      };
    }
  }

  /**
   * Check if a user has any of the specified roles
   * @param user The user to check
   * @param roleNames An array of role names to check for
   * @returns A RoleCheckResult object with the result
   */
  public hasAnyRole(user: User, roleNames: RoleName[]): RoleCheckResult {
    try {
      // Validate inputs
      if (!user || !user.id) {
        return {
          hasRole: false,
          reason: 'Invalid user object'
        };
      }
      
      if (!Array.isArray(roleNames) || roleNames.length === 0) {
        return {
          hasRole: false,
          reason: 'Invalid role names array'
        };
      }
      
      for (const roleName of roleNames) {
        try {
          const result = this.hasRole(user, roleName);
          if (result.hasRole) {
            return {
              hasRole: true,
              reason: `User has role '${roleName}'`
            };
          }
        } catch (error) {
          console.error(`RoleResolver: Error checking role '${roleName}' in hasAnyRole`, error);
          // Continue with other roles
        }
      }
      
      return {
        hasRole: false,
        reason: `User does not have any of the specified roles`
      };
    } catch (error) {
      console.error('RoleResolver: Unexpected error in hasAnyRole', error);
      
      // Return a safe default on error
      return {
        hasRole: false,
        reason: `Error checking roles: ${error instanceof Error ? error.message : 'Unknown error'}`
      };
    }
  }

  /**
   * Check if a user has all of the specified roles
   * @param user The user to check
   * @param roleNames An array of role names to check for
   * @returns A RoleCheckResult object with the result
   */
  public hasAllRoles(user: User, roleNames: RoleName[]): RoleCheckResult {
    try {
      // Validate inputs
      if (!user || !user.id) {
        return {
          hasRole: false,
          reason: 'Invalid user object'
        };
      }
      
      if (!Array.isArray(roleNames) || roleNames.length === 0) {
        return {
          hasRole: false,
          reason: 'Invalid role names array'
        };
      }
      
      const missingRoles: RoleName[] = [];
      
      for (const roleName of roleNames) {
        try {
          const result = this.hasRole(user, roleName);
          if (!result.hasRole) {
            missingRoles.push(roleName);
          }
        } catch (error) {
          console.error(`RoleResolver: Error checking role '${roleName}' in hasAllRoles`, error);
          // Treat error as a missing role
          missingRoles.push(roleName);
        }
      }
      
      if (missingRoles.length > 0) {
        return {
          hasRole: false,
          reason: `User is missing roles: ${missingRoles.join(', ')}`
        };
      }
      
      return {
        hasRole: true,
        reason: 'User has all specified roles'
      };
    } catch (error) {
      console.error('RoleResolver: Unexpected error in hasAllRoles', error);
      
      // Return a safe default on error
      return {
        hasRole: false,
        reason: `Error checking roles: ${error instanceof Error ? error.message : 'Unknown error'}`
      };
    }
  }

  /**
   * Check if a user has a specific permission
   * @param user The user to check
   * @param permission The permission to check for
   * @returns A PermissionCheckResult object with the result
   */
  public hasPermission(user: User, permission: Permission): PermissionCheckResult {
    try {
      // Validate inputs
      if (!user || !user.id) {
        return {
          hasPermission: false,
          reason: 'Invalid user object'
        };
      }
      
      if (!permission) {
        return {
          hasPermission: false,
          reason: 'Invalid permission'
        };
      }
      
      // First, check if the permission exists
      try {
        if (!permissionRegistry.hasPermission(permission)) {
          return {
            hasPermission: false,
            reason: `Permission '${permission}' does not exist`
          };
        }
      } catch (error) {
        console.error(`RoleResolver: Error checking if permission '${permission}' exists`, error);
        return {
          hasPermission: false,
          reason: `Error checking permission '${permission}'`
        };
      }
      
      // Get all permissions for the user's roles
      let userPermissions: Permission[] = [];
      try {
        userPermissions = this.resolveUserPermissions(user);
      } catch (error) {
        console.error(`RoleResolver: Error resolving user permissions for user ${user.id}`, error);
        return {
          hasPermission: false,
          reason: 'Error resolving user permissions'
        };
      }
      
      // Check if the user has the permission
      const hasPermission = userPermissions.includes(permission);
      
      if (hasPermission) {
        // Validate user roles
        if (!Array.isArray(user.roles)) {
          console.warn(`RoleResolver: User roles is not an array for user ${user.id}`);
          return {
            hasPermission: true,
            reason: 'User has the permission (source role unknown)'
          };
        }
        
        // Find which role grants this permission
        for (const roleName of user.roles) {
          try {
            const rolePermissions = this.resolveRolePermissions(roleName);
            if (rolePermissions.includes(permission)) {
              return {
                hasPermission: true,
                reason: `Permission granted by role '${roleName}'`,
                sourceRole: roleName
              };
            }
          } catch (error) {
            console.error(`RoleResolver: Error resolving permissions for role '${roleName}'`, error);
            // Continue with other roles
          }
        }
        
        // If we get here, the user has the permission but we couldn't determine the source role
        return {
          hasPermission: true,
          reason: 'User has the permission (source role unknown)'
        };
      }
      
      return {
        hasPermission: false,
        reason: 'User does not have the permission'
      };
    } catch (error) {
      console.error(`RoleResolver: Unexpected error in hasPermission for user ${user?.id || 'unknown'}`, error);
      
      // Return a safe default on error
      return {
        hasPermission: false,
        reason: `Error checking permission: ${error instanceof Error ? error.message : 'Unknown error'}`
      };
    }
  }

  /**
   * Check if a user has any of the specified permissions
   * @param user The user to check
   * @param permissions An array of permissions to check for
   * @returns A PermissionCheckResult object with the result
   */
  public hasAnyPermission(user: User, permissions: Permission[]): PermissionCheckResult {
    try {
      // Validate inputs
      if (!user || !user.id) {
        return {
          hasPermission: false,
          reason: 'Invalid user object'
        };
      }
      
      if (!Array.isArray(permissions) || permissions.length === 0) {
        return {
          hasPermission: false,
          reason: 'Invalid permissions array'
        };
      }
      
      for (const permission of permissions) {
        try {
          const result = this.hasPermission(user, permission);
          if (result.hasPermission) {
            return result;
          }
        } catch (error) {
          console.error(`RoleResolver: Error checking permission '${permission}' in hasAnyPermission`, error);
          // Continue with other permissions
        }
      }
      
      return {
        hasPermission: false,
        reason: 'User does not have any of the specified permissions'
      };
    } catch (error) {
      console.error('RoleResolver: Unexpected error in hasAnyPermission', error);
      
      // Return a safe default on error
      return {
        hasPermission: false,
        reason: `Error checking permissions: ${error instanceof Error ? error.message : 'Unknown error'}`
      };
    }
  }

  /**
   * Check if a user has all of the specified permissions
   * @param user The user to check
   * @param permissions An array of permissions to check for
   * @returns A PermissionCheckResult object with the result
   */
  public hasAllPermissions(user: User, permissions: Permission[]): PermissionCheckResult {
    try {
      // Validate inputs
      if (!user || !user.id) {
        return {
          hasPermission: false,
          reason: 'Invalid user object'
        };
      }
      
      if (!Array.isArray(permissions) || permissions.length === 0) {
        return {
          hasPermission: false,
          reason: 'Invalid permissions array'
        };
      }
      
      const missingPermissions: Permission[] = [];
      
      for (const permission of permissions) {
        try {
          const result = this.hasPermission(user, permission);
          if (!result.hasPermission) {
            missingPermissions.push(permission);
          }
        } catch (error) {
          console.error(`RoleResolver: Error checking permission '${permission}' in hasAllPermissions`, error);
          // Treat error as a missing permission
          missingPermissions.push(permission);
        }
      }
      
      if (missingPermissions.length > 0) {
        return {
          hasPermission: false,
          reason: `User is missing permissions: ${missingPermissions.join(', ')}`
        };
      }
      
      return {
        hasPermission: true,
        reason: 'User has all specified permissions'
      };
    } catch (error) {
      console.error('RoleResolver: Unexpected error in hasAllPermissions', error);
      
      // Return a safe default on error
      return {
        hasPermission: false,
        reason: `Error checking permissions: ${error instanceof Error ? error.message : 'Unknown error'}`
      };
    }
  }

  /**
   * Resolve all permissions for a user, including inherited permissions
   * @param user The user to resolve permissions for
   * @returns An array of all permissions for the user
   */
  public resolveUserPermissions(user: User): Permission[] {
    try {
      // Validate input
      if (!user || !user.id) {
        console.error('RoleResolver: Invalid user object in resolveUserPermissions');
        return [];
      }
      
      const cacheKey = `user_permissions:${user.id}`;
      const cached = this.cache.get(cacheKey);
      
      // Check if we have a valid cached result
      if (cached && Date.now() - cached.timestamp < this.cacheTTL) {
        return [...cached.permissions];
      }
      
      // Validate user roles
      if (!Array.isArray(user.roles)) {
        console.error(`RoleResolver: User roles is not an array for user ${user.id}`);
        return [];
      }
      
      // Resolve permissions for each role
      const permissionsSet = new Set<Permission>();
      
      for (const roleName of user.roles) {
        try {
          const rolePermissions = this.resolveRolePermissions(roleName);
          rolePermissions.forEach(permission => {
            if (permission) {
              permissionsSet.add(permission);
            }
          });
        } catch (error) {
          console.error(`RoleResolver: Error resolving permissions for role '${roleName}' for user ${user.id}`, error);
          // Continue with other roles
        }
      }
      
      const permissions = Array.from(permissionsSet);
      
      // Cache the result
      try {
        this.cache.set(cacheKey, {
          permissions,
          timestamp: Date.now()
        });
      } catch (error) {
        console.error(`RoleResolver: Error caching permissions for user ${user.id}`, error);
        // Continue without caching
      }
      
      return permissions;
    } catch (error) {
      console.error(`RoleResolver: Unexpected error in resolveUserPermissions for user ${user?.id || 'unknown'}`, error);
      // Return empty array as a safe default
      return [];
    }
  }

  /**
   * Resolve all permissions for a role, including inherited permissions
   * @param roleName The role name to resolve permissions for
   * @returns An array of all permissions for the role
   * @throws RoleNotFoundError if the role is not found
   */
  public resolveRolePermissions(roleName: RoleName): Permission[] {
    try {
      // Validate input
      if (!roleName) {
        console.error('RoleResolver: Invalid role name in resolveRolePermissions');
        return [];
      }
      
      const cacheKey = `role_permissions:${roleName}`;
      const cached = this.cache.get(cacheKey);
      
      // Check if we have a valid cached result
      if (cached && Date.now() - cached.timestamp < this.cacheTTL) {
        return [...cached.permissions];
      }
      
      // Get the role definition
      let role;
      try {
        role = roleRegistry.getRole(roleName);
      } catch (error) {
        if (error instanceof RoleNotFoundError) {
          console.error(`RoleResolver: Role '${roleName}' not found in resolveRolePermissions`);
          return [];
        }
        throw error;
      }
      
      // Validate role object
      if (!role || !role.permissions) {
        console.error(`RoleResolver: Invalid role object for '${roleName}'`, role);
        return [];
      }
      
      // Start with the role's direct permissions
      const permissionsSet = new Set<Permission>();
      
      // Add permissions with validation
      if (Array.isArray(role.permissions)) {
        role.permissions.forEach(permission => {
          if (permission) {
            permissionsSet.add(permission);
          }
        });
      }
      
      // If the role inherits from another role, add those permissions too
      if (role.inherits_from) {
        try {
          const inheritedPermissions = this.resolveRolePermissions(role.inherits_from);
          inheritedPermissions.forEach(permission => {
            if (permission) {
              permissionsSet.add(permission);
            }
          });
        } catch (error) {
          console.error(`RoleResolver: Error resolving inherited permissions for '${roleName}' from '${role.inherits_from}'`, error);
          // Continue with direct permissions only
        }
      }
      
      const permissions = Array.from(permissionsSet);
      
      // Cache the result
      try {
        this.cache.set(cacheKey, {
          permissions,
          timestamp: Date.now()
        });
      } catch (error) {
        console.error(`RoleResolver: Error caching permissions for '${roleName}'`, error);
        // Continue without caching
      }
      
      return permissions;
    } catch (error) {
      console.error(`RoleResolver: Unexpected error in resolveRolePermissions for '${roleName}'`, error);
      // Return empty array as a safe default
      return [];
    }
  }

  /**
   * Get the inheritance chain for a role
   * @param roleName The role name to get the inheritance chain for
   * @returns An array of role names representing the inheritance chain
   * @throws RoleNotFoundError if the role is not found
   */
  public getInheritanceChain(roleName: RoleName): RoleName[] {
    try {
      // Validate input
      if (!roleName) {
        console.error('RoleResolver: Invalid role name in getInheritanceChain');
        return [];
      }
      
      return roleRegistry.getInheritanceChain(roleName);
    } catch (error) {
      console.error(`RoleResolver: Error in getInheritanceChain for role '${roleName}'`, error);
      
      // Return empty array as a safe default
      return [];
    }
  }

  /**
   * Get all roles that inherit from the specified role
   * @param roleName The parent role name
   * @returns An array of role names that inherit from the specified role
   */
  public getInheritingRoles(roleName: RoleName): RoleName[] {
    try {
      // Validate input
      if (!roleName) {
        console.error('RoleResolver: Invalid role name in getInheritingRoles');
        return [];
      }
      
      return roleRegistry.getInheritingRoles(roleName);
    } catch (error) {
      console.error(`RoleResolver: Error in getInheritingRoles for role '${roleName}'`, error);
      
      // Return empty array as a safe default
      return [];
    }
  }

  /**
   * Check if one role inherits from another
   * @param childRole The child role name
   * @param parentRole The parent role name
   * @returns True if the child role inherits from the parent role, false otherwise
   */
  public inheritsFrom(childRole: RoleName, parentRole: RoleName): boolean {
    try {
      // Validate inputs
      if (!childRole || !parentRole) {
        console.error('RoleResolver: Invalid role names in inheritsFrom');
        return false;
      }
      
      const inheritanceChain = this.getInheritanceChain(childRole);
      return inheritanceChain.includes(parentRole);
    } catch (error) {
      console.error(`RoleResolver: Error in inheritsFrom for roles '${childRole}' and '${parentRole}'`, error);
      
      // Return false as a safe default
      return false;
    }
  }

  /**
   * Clear the cache for a specific user
   * @param userId The user ID to clear the cache for
   */
  public clearUserCache(userId: string): void {
    try {
      // Validate input
      if (!userId) {
        console.error('RoleResolver: Invalid user ID in clearUserCache');
        return;
      }
      
      const cacheKey = `user_permissions:${userId}`;
      this.cache.delete(cacheKey);
    } catch (error) {
      console.error(`RoleResolver: Error in clearUserCache for user ${userId}`, error);
    }
  }

  /**
   * Clear the cache for a specific role
   * @param roleName The role name to clear the cache for
   */
  public clearRoleCache(roleName: RoleName): void {
    try {
      // Validate input
      if (!roleName) {
        console.error('RoleResolver: Invalid role name in clearRoleCache');
        return;
      }
      
      const cacheKey = `role_permissions:${roleName}`;
      this.cache.delete(cacheKey);
    } catch (error) {
      console.error(`RoleResolver: Error in clearRoleCache for role ${roleName}`, error);
    }
  }

  /**
   * Clear the entire cache
   */
  public clearCache(): void {
    try {
      this.cache.clear();
    } catch (error) {
      console.error('RoleResolver: Error in clearCache', error);
    }
  }

  /**
   * Set the cache TTL
   * @param ttl The time-to-live for the cache in milliseconds
   */
  public setCacheTTL(ttl: number): void {
    try {
      // Validate input
      if (typeof ttl !== 'number' || ttl < 0) {
        console.error('RoleResolver: Invalid TTL value in setCacheTTL');
        return;
      }
      
      this.cacheTTL = ttl;
    } catch (error) {
      console.error('RoleResolver: Error in setCacheTTL', error);
    }
  }

  /**
   * Get the current cache TTL
   * @returns The current cache TTL in milliseconds
   */
  public getCacheTTL(): number {
    try {
      return this.cacheTTL;
    } catch (error) {
      console.error('RoleResolver: Error in getCacheTTL', error);
      // Return a safe default
      return 5 * 60 * 1000; // 5 minutes
    }
  }
}

// Export a singleton instance
export const roleResolver = new RoleResolver();