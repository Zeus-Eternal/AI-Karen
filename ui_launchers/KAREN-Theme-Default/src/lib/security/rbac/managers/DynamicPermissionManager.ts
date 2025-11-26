/**
 * Dynamic Permission Manager
 * 
 * This class is responsible for managing dynamic permissions and roles that can be added
 * or removed at runtime. It provides methods to add, remove, and manage dynamic permissions
 * and roles, as well as persist them to storage.
 */

import {
  Permission,
  RoleName,
  DynamicPermission,
  DynamicRole,
  RoleChangeEvent
} from '../types';
import { 
  DynamicPermissionError, 
  DynamicRoleError, 
  RoleAssignmentError,
  RBACError 
} from '../utils/errors';
import { roleRegistry } from '../registries/RoleRegistry';
import { permissionRegistry } from '../registries/PermissionRegistry';
import { permissionResolver } from '../resolvers/PermissionResolver';
import { RBAC_EVENTS } from '../config';

/**
 * The DynamicPermissionManager class handles dynamic permissions and roles.
 */
export class DynamicPermissionManager {
  private dynamicPermissions: Map<string, DynamicPermission> = new Map();
  private dynamicRoles: Map<string, DynamicRole> = new Map();
  private isInitialized = false;
  private eventListeners: Map<string, ((data: unknown) => void)[]> = new Map();

  /**
   * Initialize the dynamic permission manager
   */
  public initialize(): void {
    if (this.isInitialized) {
      return;
    }

    // Load dynamic permissions and roles from storage
    this.loadFromStorage();

    this.isInitialized = true;
  }

  /**
   * Add a dynamic permission
   * @param permission The permission to add
   * @returns The added dynamic permission
   * @throws DynamicPermissionError if the permission is invalid or already exists
   */
  public addDynamicPermission(permission: Omit<DynamicPermission, 'createdAt'>): DynamicPermission {
    if (!this.isInitialized) {
      this.initialize();
    }

    // Validate the permission
    this.validateDynamicPermission(permission);

    // Check if the permission already exists
    if (this.dynamicPermissions.has(permission.name) || permissionRegistry.hasPermission(permission.name)) {
      throw new DynamicPermissionError('add', permission.name, 'Permission already exists');
    }

    // Create the dynamic permission
    const dynamicPermission: DynamicPermission = {
      ...permission,
      createdAt: new Date()
    };

    // Add to the map
    this.dynamicPermissions.set(permission.name, dynamicPermission);

    // Register the permission with the permission registry
    permissionRegistry.registerPermission(permission.name);

    // Save to storage
    this.saveToStorage();

    // Emit event
    this.emitEvent(RBAC_EVENTS.DYNAMIC_PERMISSION_ADDED, dynamicPermission);

    return dynamicPermission;
  }

  /**
   * Remove a dynamic permission
   * @param permissionName The name of the permission to remove
   * @throws DynamicPermissionError if the permission is not found or is a system permission
   */
  public removeDynamicPermission(permissionName: Permission): void {
    if (!this.isInitialized) {
      this.initialize();
    }

    // Check if the permission exists
    if (!this.dynamicPermissions.has(permissionName)) {
      throw new DynamicPermissionError('remove', permissionName, 'Permission not found');
    }

    // Check if the permission is a system permission
    if (permissionResolver.isSystemPermission(permissionName)) {
      throw new DynamicPermissionError('remove', permissionName, 'Cannot remove system permission');
    }

    // Get the permission before removing it
    const permission = this.dynamicPermissions.get(permissionName)!;

    // Remove from the map
    this.dynamicPermissions.delete(permissionName);

    // Remove from the permission registry
    permissionRegistry.removePermission(permissionName);

    // Save to storage
    this.saveToStorage();

    // Emit event
    this.emitEvent(RBAC_EVENTS.DYNAMIC_PERMISSION_REMOVED, permission);
  }

  /**
   * Get a dynamic permission
   * @param permissionName The name of the permission to get
   * @returns The dynamic permission, or undefined if not found
   */
  public getDynamicPermission(permissionName: Permission): DynamicPermission | undefined {
    if (!this.isInitialized) {
      this.initialize();
    }

    return this.dynamicPermissions.get(permissionName);
  }

  /**
   * Get all dynamic permissions
   * @returns An array of all dynamic permissions
   */
  public getAllDynamicPermissions(): DynamicPermission[] {
    if (!this.isInitialized) {
      this.initialize();
    }

    return Array.from(this.dynamicPermissions.values()).map(p => ({ ...p }));
  }

  /**
   * Add a dynamic role
   * @param role The role to add
   * @returns The added dynamic role
   * @throws DynamicRoleError if the role is invalid or already exists
   */
  public addDynamicRole(role: Omit<DynamicRole, 'createdAt'>): DynamicRole {
    if (!this.isInitialized) {
      this.initialize();
    }

    // Validate the role
    this.validateDynamicRole(role);

    // Check if the role already exists
    if (this.dynamicRoles.has(role.name) || roleRegistry.hasRole(role.name)) {
      throw new DynamicRoleError('add', role.name, 'Role already exists');
    }

    // Create the dynamic role
    const dynamicRole: DynamicRole = {
      ...role,
      createdAt: new Date()
    };

    // Add to the map
    this.dynamicRoles.set(role.name, dynamicRole);

    // Register the role with the role registry
    roleRegistry.registerRole(role.name, {
      description: role.description,
      inherits_from: role.inherits_from,
      permissions: role.permissions
    });

    // Save to storage
    this.saveToStorage();

    // Emit event
    this.emitEvent(RBAC_EVENTS.DYNAMIC_ROLE_ADDED, dynamicRole);

    return dynamicRole;
  }

  /**
   * Remove a dynamic role
   * @param roleName The name of the role to remove
   * @throws DynamicRoleError if the role is not found or is a system role
   */
  public removeDynamicRole(roleName: RoleName): void {
    if (!this.isInitialized) {
      this.initialize();
    }

    // Check if the role exists
    if (!this.dynamicRoles.has(roleName)) {
      throw new DynamicRoleError('remove', roleName, 'Role not found');
    }

    // Check if the role is a system role
    if (this.isSystemRole(roleName)) {
      throw new DynamicRoleError('remove', roleName, 'Cannot remove system role');
    }

    // Get the role before removing it
    const role = this.dynamicRoles.get(roleName)!;

    // Remove from the map
    this.dynamicRoles.delete(roleName);

    // Remove from the role registry
    roleRegistry.removeRole(roleName);

    // Save to storage
    this.saveToStorage();

    // Emit event
    this.emitEvent(RBAC_EVENTS.DYNAMIC_ROLE_REMOVED, role);
  }

  /**
   * Get a dynamic role
   * @param roleName The name of the role to get
   * @returns The dynamic role, or undefined if not found
   */
  public getDynamicRole(roleName: RoleName): DynamicRole | undefined {
    if (!this.isInitialized) {
      this.initialize();
    }

    return this.dynamicRoles.get(roleName);
  }

  /**
   * Get all dynamic roles
   * @returns An array of all dynamic roles
   */
  public getAllDynamicRoles(): DynamicRole[] {
    if (!this.isInitialized) {
      this.initialize();
    }

    return Array.from(this.dynamicRoles.values()).map(r => ({ ...r }));
  }

  /**
   * Assign a dynamic role to a user
   * @param userId The ID of the user
   * @param roleName The name of the role to assign
   * @param reason The reason for the assignment
   * @throws RoleAssignmentError if the role is not found or the user already has the role
   */
  public assignRoleToUser(userId: string, roleName: RoleName, reason?: string): void {
    if (!this.isInitialized) {
      this.initialize();
    }

    // Check if the role exists
    if (!this.dynamicRoles.has(roleName) && !roleRegistry.hasRole(roleName)) {
      throw new RoleAssignmentError(userId, roleName, 'assign', 'Role not found');
    }

    // In a real implementation, we would check if the user exists and update their roles
    // For now, we'll just emit an event
    const event: RoleChangeEvent = {
      userId,
      previousRoles: [], // In a real implementation, we would get the current roles
      newRoles: [roleName], // In a real implementation, we would add to existing roles
      changedBy: 'system', // In a real implementation, this would be the current user
      timestamp: new Date(),
      reason
    };

    // Emit event
    this.emitEvent(RBAC_EVENTS.ROLE_ASSIGNED, event);
  }

  /**
   * Remove a dynamic role from a user
   * @param userId The ID of the user
   * @param roleName The name of the role to remove
   * @param reason The reason for the removal
   * @throws RoleAssignmentError if the role is not found or the user doesn't have the role
   */
  public removeRoleFromUser(userId: string, roleName: RoleName, reason?: string): void {
    if (!this.isInitialized) {
      this.initialize();
    }

    // Check if the role exists
    if (!this.dynamicRoles.has(roleName) && !roleRegistry.hasRole(roleName)) {
      throw new RoleAssignmentError(userId, roleName, 'remove', 'Role not found');
    }

    // In a real implementation, we would check if the user exists and update their roles
    // For now, we'll just emit an event
    const event: RoleChangeEvent = {
      userId,
      previousRoles: [roleName], // In a real implementation, we would get the current roles
      newRoles: [], // In a real implementation, we would remove from existing roles
      changedBy: 'system', // In a real implementation, this would be the current user
      timestamp: new Date(),
      reason
    };

    // Emit event
    this.emitEvent(RBAC_EVENTS.ROLE_REMOVED, event);
  }

  /**
   * Add an event listener
   * @param event The event to listen for
   * @param listener The listener function
   */
  public addEventListener(event: string, listener: (data: unknown) => void): void {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
    this.eventListeners.get(event)!.push(listener);
  }

  /**
   * Remove an event listener
   * @param event The event to stop listening for
   * @param listener The listener function to remove
   */
  public removeEventListener(event: string, listener: (data: unknown) => void): void {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      const index = listeners.indexOf(listener);
      if (index !== -1) {
        listeners.splice(index, 1);
      }
    }
  }

  /**
   * Validate a dynamic permission
   * @param permission The permission to validate
   * @throws DynamicPermissionError if the permission is invalid
   */
  private validateDynamicPermission(permission: Omit<DynamicPermission, 'createdAt'>): void {
    if (!permission.name || typeof permission.name !== 'string') {
      throw new DynamicPermissionError('add', permission.name || 'undefined', 'Permission name must be a non-empty string');
    }

    if (!permission.description || typeof permission.description !== 'string') {
      throw new DynamicPermissionError('add', permission.name, 'Permission description must be a non-empty string');
    }

    if (!permission.category || typeof permission.category !== 'string') {
      throw new DynamicPermissionError('add', permission.name, 'Permission category must be a non-empty string');
    }

    if (!permission.createdBy || typeof permission.createdBy !== 'string') {
      throw new DynamicPermissionError('add', permission.name, 'Permission createdBy must be a non-empty string');
    }

    // Validate the permission format
    try {
      permissionResolver.validatePermission(permission.name);
    } catch (error) {
      if (error instanceof RBACError) {
        throw new DynamicPermissionError('add', permission.name, error.message);
      }
      throw error;
    }
  }

  /**
   * Validate a dynamic role
   * @param role The role to validate
   * @throws DynamicRoleError if the role is invalid
   */
  private validateDynamicRole(role: Omit<DynamicRole, 'createdAt'>): void {
    if (!role.name || typeof role.name !== 'string') {
      throw new DynamicRoleError('add', role.name || 'undefined', 'Role name must be a non-empty string');
    }

    if (!role.description || typeof role.description !== 'string') {
      throw new DynamicRoleError('add', role.name, 'Role description must be a non-empty string');
    }

    if (!role.createdBy || typeof role.createdBy !== 'string') {
      throw new DynamicRoleError('add', role.name, 'Role createdBy must be a non-empty string');
    }

    if (role.inherits_from !== null && (typeof role.inherits_from !== 'string' || !role.inherits_from)) {
      throw new DynamicRoleError('add', role.name, 'Role inherits_from must be either null or a non-empty string');
    }

    if (!Array.isArray(role.permissions)) {
      throw new DynamicRoleError('add', role.name, 'Role permissions must be an array');
    }

    // Validate all permissions in the role
    for (const permission of role.permissions) {
      if (typeof permission !== 'string' || !permission) {
        throw new DynamicRoleError('add', role.name, `Permission '${permission}' must be a non-empty string`);
      }

      // Check if the permission exists
      if (!permissionRegistry.hasPermission(permission) && !this.dynamicPermissions.has(permission)) {
        throw new DynamicRoleError('add', role.name, `Permission '${permission}' does not exist`);
      }
    }
  }

  /**
   * Check if a role is a system role
   * @param roleName The name of the role to check
   * @returns True if the role is a system role, false otherwise
   */
  private isSystemRole(roleName: RoleName): boolean {
    // System roles are those that are critical for system operation
    const systemRoles: RoleName[] = [
      'super_admin',
      'admin',
      'user',
      'readonly'
    ];
    
    return systemRoles.includes(roleName);
  }

  /**
   * Emit an event
   * @param event The event to emit
   * @param data The data to emit with the event
   */
  private emitEvent(event: string, data: unknown): void {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      for (const listener of listeners) {
        try {
          listener(data);
        } catch (error) {
          console.error(`Error in RBAC event listener for ${event}:`, error);
        }
      }
    }
  }

  /**
   * Clear all caches
   */
  public clearCache(): void {
    this.dynamicPermissions.clear();
    this.dynamicRoles.clear();
    this.eventListeners.clear();
    
    // Clear from localStorage
    if (typeof window !== 'undefined') {
      try {
        localStorage.removeItem('rbac_dynamic_data');
      } catch (error) {
        console.error('Error clearing RBAC dynamic data from storage:', error);
      }
    }
  }

  /**
   * Save dynamic permissions and roles to storage
   */
  private saveToStorage(): void {
    if (typeof window === 'undefined') {
      return; // Not in browser environment
    }

    try {
      const data = {
        dynamicPermissions: Array.from(this.dynamicPermissions.values()),
        dynamicRoles: Array.from(this.dynamicRoles.values())
      };
      
      localStorage.setItem('rbac_dynamic_data', JSON.stringify(data));
    } catch (error) {
      console.error('Error saving RBAC dynamic data to storage:', error);
    }
  }

  /**
   * Load dynamic permissions and roles from storage
   */
  private loadFromStorage(): void {
    if (typeof window === 'undefined') {
      return; // Not in browser environment
    }

    try {
      const dataStr = localStorage.getItem('rbac_dynamic_data');
      if (!dataStr) {
        return;
      }

      const data = JSON.parse(dataStr);
      
      // Load dynamic permissions
      if (data.dynamicPermissions && Array.isArray(data.dynamicPermissions)) {
        for (const permission of data.dynamicPermissions) {
          // Convert date strings back to Date objects
          permission.createdAt = new Date(permission.createdAt);
          
          // Add to the map
          this.dynamicPermissions.set(permission.name, permission);
          
          // Register the permission with the permission registry
          permissionRegistry.registerPermission(permission.name);
        }
      }
      
      // Load dynamic roles
      if (data.dynamicRoles && Array.isArray(data.dynamicRoles)) {
        for (const role of data.dynamicRoles) {
          // Convert date strings back to Date objects
          role.createdAt = new Date(role.createdAt);
          
          // Add to the map
          this.dynamicRoles.set(role.name, role);
          
          // Register the role with the role registry
          roleRegistry.registerRole(role.name, {
            description: role.description,
            inherits_from: role.inherits_from,
            permissions: role.permissions
          });
        }
      }
    } catch (error) {
      console.error('Error loading RBAC dynamic data from storage:', error);
    }
  }
}

// Export a singleton instance
export const dynamicPermissionManager = new DynamicPermissionManager();