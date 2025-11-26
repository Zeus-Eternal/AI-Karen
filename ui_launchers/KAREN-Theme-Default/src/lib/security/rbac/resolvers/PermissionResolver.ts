/**
 * Permission Resolver
 * 
 * This class is responsible for resolving permissions and providing permission-related utilities.
 * It provides methods to check permissions, get permissions by category, and resolve permission
 * relationships.
 */

import { 
  Permission, 
  PermissionCategory, 
  User, 
  PermissionCheckResult,
  RoleName 
} from '../types';
import {
  PermissionNotFoundError
} from '../utils/errors';
import { permissionRegistry } from '../registries/PermissionRegistry';
import { roleRegistry } from '../registries/RoleRegistry';
import { roleResolver } from './RoleResolver';

/**
 * The PermissionResolver class handles permission resolution and provides permission-related utilities.
 */
export class PermissionResolver {
  private cache: Map<string, { result: PermissionCheckResult; timestamp: number }> = new Map();
  private cacheTTL: number;

  /**
   * Create a new PermissionResolver instance
   * @param cacheTTL The time-to-live for the cache in milliseconds
   */
  constructor(cacheTTL: number = 5 * 60 * 1000) { // Default 5 minutes
    this.cacheTTL = cacheTTL;
  }

  /**
   * Check if a user has a specific permission
   * @param user The user to check
   * @param permission The permission to check for
   * @returns A PermissionCheckResult object with the result
   */
  public hasPermission(user: User, permission: Permission): PermissionCheckResult {
    const cacheKey = `user_permission:${user.id}:${permission}`;
    const cached = this.cache.get(cacheKey);
    
    // Check if we have a valid cached result
    if (cached && Date.now() - cached.timestamp < this.cacheTTL) {
      return { ...cached.result };
    }
    
    // Delegate to the RoleResolver
    const result = roleResolver.hasPermission(user, permission);
    
    // Cache the result
    this.cache.set(cacheKey, {
      result,
      timestamp: Date.now()
    });
    
    return result;
  }

  /**
   * Check if a user has any of the specified permissions
   * @param user The user to check
   * @param permissions An array of permissions to check for
   * @returns A PermissionCheckResult object with the result
   */
  public hasAnyPermission(user: User, permissions: Permission[]): PermissionCheckResult {
    for (const permission of permissions) {
      const result = this.hasPermission(user, permission);
      if (result.hasPermission) {
        return result;
      }
    }
    
    return {
      hasPermission: false,
      reason: 'User does not have any of the specified permissions'
    };
  }

  /**
   * Check if a user has all of the specified permissions
   * @param user The user to check
   * @param permissions An array of permissions to check for
   * @returns A PermissionCheckResult object with the result
   */
  public hasAllPermissions(user: User, permissions: Permission[]): PermissionCheckResult {
    const missingPermissions: Permission[] = [];
    
    for (const permission of permissions) {
      const result = this.hasPermission(user, permission);
      if (!result.hasPermission) {
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
  }

  /**
   * Get all permissions for a user
   * @param user The user to get permissions for
   * @returns An array of all permissions for the user
   */
  public getUserPermissions(user: User): Permission[] {
    return roleResolver.resolveUserPermissions(user);
  }

  /**
   * Get all permissions for a role
   * @param roleName The role name to get permissions for
   * @returns An array of all permissions for the role
   * @throws RoleNotFoundError if the role is not found
   */
  public getRolePermissions(roleName: RoleName): Permission[] {
    return roleResolver.resolveRolePermissions(roleName);
  }

  /**
   * Get all permissions in a specific category
   * @param categoryName The name of the category
   * @returns An array of permissions in the category
   * @throws InvalidPermissionError if the category is not found
   */
  public getPermissionsByCategory(categoryName: string): Permission[] {
    return permissionRegistry.getPermissionsInCategory(categoryName);
  }

  /**
   * Get the category for a specific permission
   * @param permission The permission to find the category for
   * @returns The permission category that contains the permission, or undefined if not found
   */
  public getCategoryForPermission(permission: Permission): PermissionCategory | undefined {
    return permissionRegistry.getCategoryForPermission(permission);
  }

  /**
   * Get all permission categories
   * @returns An array of all permission categories
   */
  public getAllCategories(): PermissionCategory[] {
    return permissionRegistry.getAllCategories();
  }

  /**
   * Check if a permission exists
   * @param permission The permission to check
   * @returns True if the permission exists, false otherwise
   */
  public permissionExists(permission: Permission): boolean {
    return permissionRegistry.hasPermission(permission);
  }

  /**
   * Check if a permission category exists
   * @param categoryName The name of the category to check
   * @returns True if the category exists, false otherwise
   */
  public categoryExists(categoryName: string): boolean {
    return permissionRegistry.hasCategory(categoryName);
  }

  /**
   * Get all roles that have a specific permission
   * @param permission The permission to check
   * @returns An array of role names that have the permission
   */
  public getRolesWithPermission(permission: Permission): RoleName[] {
    if (!this.permissionExists(permission)) {
      throw new PermissionNotFoundError(permission);
    }
    
    const roles: RoleName[] = [];
    const allRoles = roleRegistry.getAllRoleNames();
    
    for (const roleName of allRoles) {
      const rolePermissions = this.getRolePermissions(roleName);
      if (rolePermissions.includes(permission)) {
        roles.push(roleName);
      }
    }
    
    return roles;
  }

  /**
   * Get all users that have a specific permission (requires user registry)
   * @param permission The permission to check
   * @param users An array of users to check
   * @returns An array of users that have the permission
   */
  public getUsersWithPermission(permission: Permission, users: User[]): User[] {
    if (!this.permissionExists(permission)) {
      throw new PermissionNotFoundError(permission);
    }
    
    return users.filter(user => this.hasPermission(user, permission).hasPermission);
  }

  /**
   * Check if a permission is a system permission (cannot be modified)
   * @param permission The permission to check
   * @returns True if the permission is a system permission, false otherwise
   */
  public isSystemPermission(permission: Permission): boolean {
    // System permissions are those that are critical for system operation
    const systemPermissions: Permission[] = [
      'admin:system',
      'security:evil_mode'
    ];
    
    return systemPermissions.includes(permission);
  }

  /**
   * Check if a permission is a dynamic permission (can be modified)
   * @param permission The permission to check
   * @returns True if the permission is a dynamic permission, false otherwise
   */
  public isDynamicPermission(permission: Permission): boolean {
    // Dynamic permissions are those that are not system permissions
    return !this.isSystemPermission(permission);
  }

  /**
   * Validate a permission
   * @param permission The permission to validate
   * @throws InvalidPermissionError if the permission is invalid
   */
  public validatePermission(permission: Permission): void {
    if (!this.permissionExists(permission)) {
      throw new PermissionNotFoundError(permission);
    }
  }

  /**
   * Get the resource part of a permission (e.g., "data" from "data:read")
   * @param permission The permission to parse
   * @returns The resource part of the permission
   */
  public getPermissionResource(permission: Permission): string {
    this.validatePermission(permission);
    return permission.split(':')[0];
  }

  /**
   * Get the action part of a permission (e.g., "read" from "data:read")
   * @param permission The permission to parse
   * @returns The action part of the permission
   */
  public getPermissionAction(permission: Permission): string {
    this.validatePermission(permission);
    const parts = permission.split(':');
    return parts.slice(1).join(':'); // Join the remaining parts in case of multi-part actions
  }

  /**
   * Get all permissions for a specific resource
   * @param resource The resource name (e.g., "data")
   * @returns An array of permissions for the resource
   */
  public getPermissionsByResource(resource: string): Permission[] {
    const allPermissions = permissionRegistry.getAllPermissions();
    return allPermissions.filter(permission => 
      this.getPermissionResource(permission) === resource
    );
  }

  /**
   * Get all resources that have permissions
   * @returns An array of all resource names
   */
  public getAllResources(): string[] {
    const allPermissions = permissionRegistry.getAllPermissions();
    const resources = new Set<string>();
    
    for (const permission of allPermissions) {
      const resource = this.getPermissionResource(permission);
      resources.add(resource);
    }
    
    return Array.from(resources);
  }

  /**
   * Get all actions for a specific resource
   * @param resource The resource name (e.g., "data")
   * @returns An array of actions for the resource
   */
  public getActionsByResource(resource: string): string[] {
    const resourcePermissions = this.getPermissionsByResource(resource);
    const actions = new Set<string>();
    
    for (const permission of resourcePermissions) {
      const action = this.getPermissionAction(permission);
      actions.add(action);
    }
    
    return Array.from(actions);
  }

  /**
   * Clear the cache for a specific user
   * @param userId The user ID to clear the cache for
   */
  public clearUserCache(userId: string): void {
    // Clear all cache entries for this user
    const keysToDelete: string[] = [];
    
    for (const [key] of this.cache.entries()) {
      if (key.startsWith(`user_permission:${userId}:`)) {
        keysToDelete.push(key);
      }
    }
    
    for (const key of keysToDelete) {
      this.cache.delete(key);
    }
  }

  /**
   * Clear the cache for a specific permission
   * @param permission The permission to clear the cache for
   */
  public clearPermissionCache(permission: Permission): void {
    // Clear all cache entries for this permission
    const keysToDelete: string[] = [];
    
    for (const [key] of this.cache.entries()) {
      if (key.endsWith(`:${permission}`)) {
        keysToDelete.push(key);
      }
    }
    
    for (const key of keysToDelete) {
      this.cache.delete(key);
    }
  }

  /**
   * Clear the entire cache
   */
  public clearCache(): void {
    this.cache.clear();
  }

  /**
   * Set the cache TTL
   * @param ttl The time-to-live for the cache in milliseconds
   */
  public setCacheTTL(ttl: number): void {
    this.cacheTTL = ttl;
  }

  /**
   * Get the current cache TTL
   * @returns The current cache TTL in milliseconds
   */
  public getCacheTTL(): number {
    return this.cacheTTL;
  }
}

// Export a singleton instance
export const permissionResolver = new PermissionResolver();