/**
 * RBAC Service
 * 
 * This is the main entry point for the Role-Based Access Control (RBAC) system.
 * It provides a high-level API for all RBAC operations and coordinates between
 * the different components of the system.
 */

import {
  User,
  RoleName,
  Permission,
  RoleDefinition,
  PermissionCheckResult,
  RoleCheckResult,
  RBACConfig,
  RBACStatistics
} from './types';
import {
  InitializationError,
  UserNotFoundError
} from './utils/errors';
import { DEFAULT_RBAC_CONFIG } from './config';
import { roleRegistry } from './registries/RoleRegistry';
import { permissionRegistry } from './registries/PermissionRegistry';
import { roleResolver } from './resolvers/RoleResolver';
import { permissionResolver } from './resolvers/PermissionResolver';
import { hierarchyResolver } from './resolvers/HierarchyResolver';
import { dynamicPermissionManager } from './managers/DynamicPermissionManager';
import { PERMISSION_CATEGORIES, PERMISSION_MAPPINGS } from './config';

/**
 * The RBACService class provides a high-level API for all RBAC operations.
 * It is implemented as a singleton to ensure a single instance throughout the application.
 */
export class RBACService {
  private static instance: RBACService | null = null;
  private config: RBACConfig;
  private isInitialized = false;
  private currentUser: User | null = null;
  private initializationPromise: Promise<void> | null = null;

  /**
   * Private constructor to enforce singleton pattern
   * @param config The RBAC configuration
   */
  private constructor(config?: Partial<RBACConfig>) {
    this.config = { ...DEFAULT_RBAC_CONFIG, ...config };
  }

  /**
   * Get the singleton instance of the RBACService
   * @param config Optional configuration to override the default
   * @returns The RBACService instance
   */
  public static getInstance(config?: Partial<RBACConfig>): RBACService {
    if (!RBACService.instance) {
      RBACService.instance = new RBACService(config);
    }
    return RBACService.instance;
  }

  /**
   * Initialize the RBAC system
   * @returns A promise that resolves when initialization is complete
   */
  public async initialize(): Promise<void> {
    if (this.isInitialized) {
      return;
    }

    if (this.initializationPromise) {
      return this.initializationPromise;
    }

    this.initializationPromise = this.doInitialize();
    return this.initializationPromise;
  }

  /**
   * Perform the actual initialization
   */
  private async doInitialize(): Promise<void> {
    try {
      // Initialize all components
      roleRegistry.initialize();
      permissionRegistry.initialize();
      dynamicPermissionManager.initialize();
      hierarchyResolver.initialize();

      // Load default roles and permissions
      await this.loadDefaultConfiguration();

      this.isInitialized = true;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      throw new InitializationError(message, error instanceof Error ? error : undefined);
    }
  }

  /**
   * Load the default roles and permissions configuration
   */
  private async loadDefaultConfiguration(): Promise<void> {
    try {
      // In a real implementation, we would load this from an API or config file
      // For now, we'll use the static configuration

      // Register all permissions
      const allPermissions = PERMISSION_MAPPINGS.map(mapping => mapping.frontend);
      permissionRegistry.registerPermissions(allPermissions);

      // Register all permission categories
      permissionRegistry.registerCategories(PERMISSION_CATEGORIES);

      // Create role definitions from the mappings
      const roleDefinitions: Record<RoleName, RoleDefinition> = {};
      
      // This would normally be loaded from a configuration file
      // For now, we'll create minimal role definitions
      roleDefinitions['super_admin'] = {
        description: 'Highest privilege role with unrestricted access',
        inherits_from: null,
        permissions: allPermissions // Super admin has all permissions
      };

      roleDefinitions['admin'] = {
        description: 'Platform administrator',
        inherits_from: null,
        permissions: allPermissions.filter(p => !p.includes('evil_mode')) // Admin has all permissions except evil_mode
      };

      roleDefinitions['user'] = {
        description: 'Standard platform user',
        inherits_from: null,
        permissions: [
          'data:read',
          'model:info',
          'model:read',
          'training:read',
          'training_data:read'
        ]
      };

      roleDefinitions['readonly'] = {
        description: 'Read only visibility',
        inherits_from: null,
        permissions: [
          'model:info',
          'model:read',
          'training:read'
        ]
      };

      // Register all roles
      roleRegistry.registerRoles(roleDefinitions);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      throw new InitializationError(`Failed to load default configuration: ${message}`, error instanceof Error ? error : undefined);
    }
  }

  /**
   * Set the current user
   * @param user The current user
   */
  public setCurrentUser(user: User | null): void {
    this.currentUser = user;
    
    // Clear caches when user changes
    if (this.config.enableCache) {
      roleResolver.clearCache();
      permissionResolver.clearCache();
    }
  }

  /**
   * Get the current user
   * @returns The current user, or null if no user is set
   */
  public getCurrentUser(): User | null {
    return this.currentUser;
  }

  /**
   * Check if the current user has a specific permission
   * @param permission The permission to check
   * @returns A PermissionCheckResult object with the result
   * @throws InitializationError if the RBAC system is not initialized
   * @throws UserNotFoundError if no user is set
   */
  public hasPermission(permission: Permission): PermissionCheckResult {
    try {
      // Try to initialize if not already initialized
      if (!this.isInitialized) {
        this.initialize().catch(error => {
          console.error('RBACService: Failed to auto-initialize:', error);
        });
      }
      
      // If still not initialized, return a safe default
      if (!this.isInitialized) {
        return {
          hasPermission: false,
          reason: 'RBAC system not initialized'
        };
      }
      
      // If no user is set, return a safe default
      if (!this.currentUser) {
        return {
          hasPermission: false,
          reason: 'No user set'
        };
      }

      return permissionResolver.hasPermission(this.currentUser, permission);
    } catch (error) {
      console.error('RBACService: Error checking permission:', error);
      
      // Return a safe default on error
      return {
        hasPermission: false,
        reason: `Error checking permission: ${error instanceof Error ? error.message : 'Unknown error'}`
      };
    }
  }

  /**
   * Check if the current user has any of the specified permissions
   * @param permissions An array of permissions to check
   * @returns A PermissionCheckResult object with the result
   * @throws InitializationError if the RBAC system is not initialized
   * @throws UserNotFoundError if no user is set
   */
  public hasAnyPermission(permissions: Permission[]): PermissionCheckResult {
    this.ensureInitialized();
    this.ensureUserSet();

    return permissionResolver.hasAnyPermission(this.currentUser!, permissions);
  }

  /**
   * Check if the current user has all of the specified permissions
   * @param permissions An array of permissions to check
   * @returns A PermissionCheckResult object with the result
   * @throws InitializationError if the RBAC system is not initialized
   * @throws UserNotFoundError if no user is set
   */
  public hasAllPermissions(permissions: Permission[]): PermissionCheckResult {
    this.ensureInitialized();
    this.ensureUserSet();

    return permissionResolver.hasAllPermissions(this.currentUser!, permissions);
  }

  /**
   * Check if the current user has a specific role
   * @param role The role to check
   * @returns A RoleCheckResult object with the result
   * @throws InitializationError if the RBAC system is not initialized
   * @throws UserNotFoundError if no user is set
   */
  public hasRole(role: RoleName): RoleCheckResult {
    try {
      // Try to initialize if not already initialized
      if (!this.isInitialized) {
        this.initialize().catch(error => {
          console.error('RBACService: Failed to auto-initialize:', error);
        });
      }
      
      // If still not initialized, return a safe default
      if (!this.isInitialized) {
        return {
          hasRole: false,
          reason: 'RBAC system not initialized'
        };
      }
      
      // If no user is set, return a safe default
      if (!this.currentUser) {
        return {
          hasRole: false,
          reason: 'No user set'
        };
      }

      return roleResolver.hasRole(this.currentUser, role);
    } catch (error) {
      console.error('RBACService: Error checking role:', error);
      
      // Return a safe default on error
      return {
        hasRole: false,
        reason: `Error checking role: ${error instanceof Error ? error.message : 'Unknown error'}`
      };
    }
  }

  /**
   * Check if the current user has any of the specified roles
   * @param roles An array of roles to check
   * @returns A RoleCheckResult object with the result
   * @throws InitializationError if the RBAC system is not initialized
   * @throws UserNotFoundError if no user is set
   */
  public hasAnyRole(roles: RoleName[]): RoleCheckResult {
    this.ensureInitialized();
    this.ensureUserSet();

    return roleResolver.hasAnyRole(this.currentUser!, roles);
  }

  /**
   * Check if the current user has all of the specified roles
   * @param roles An array of roles to check
   * @returns A RoleCheckResult object with the result
   * @throws InitializationError if the RBAC system is not initialized
   * @throws UserNotFoundError if no user is set
   */
  public hasAllRoles(roles: RoleName[]): RoleCheckResult {
    this.ensureInitialized();
    this.ensureUserSet();

    return roleResolver.hasAllRoles(this.currentUser!, roles);
  }

  /**
   * Get all permissions for the current user
   * @returns An array of all permissions for the current user
   * @throws InitializationError if the RBAC system is not initialized
   * @throws UserNotFoundError if no user is set
   */
  public getUserPermissions(): Permission[] {
    this.ensureInitialized();
    this.ensureUserSet();

    return permissionResolver.getUserPermissions(this.currentUser!);
  }

  /**
   * Get permissions for a specific role
   * @param role The role name
   * @returns An array of permissions for the role
   * @throws InitializationError if the RBAC system is not initialized
   * @throws RoleNotFoundError if the role is not found
   */
  public getRolePermissions(role: RoleName): Permission[] {
    this.ensureInitialized();
    
    const roleDefinition = roleRegistry.getRole(role);
    return roleDefinition.permissions;
  }

  /**
   * Get the highest role from a list of roles based on the role hierarchy
   * @param roles An array of role names
   * @returns The highest role name, or null if no roles are provided
   * @throws InitializationError if the RBAC system is not initialized
   */
  public getHighestRole(roles: RoleName[]): RoleName | null {
    try {
      // Try to initialize if not already initialized
      if (!this.isInitialized) {
        this.initialize().catch(error => {
          console.error('RBACService: Failed to auto-initialize:', error);
        });
      }
      
      // If still not initialized, return a safe default
      if (!this.isInitialized) {
        return roles.length > 0 ? roles[0] : null;
      }
      
      if (roles.length === 0) {
        return null;
      }

      // Find the role with the highest hierarchy level
      let highestRole = roles[0];
      let highestLevel = -1; // Default to -1 in case getRoleLevel fails
      
      try {
        highestLevel = hierarchyResolver.getRoleLevel(highestRole);
      } catch (error) {
        console.error(`RBACService: Error getting level for role ${highestRole}:`, error);
      }

      for (let i = 1; i < roles.length; i++) {
        const role = roles[i];
        let level = -1; // Default to -1 in case getRoleLevel fails
        
        try {
          level = hierarchyResolver.getRoleLevel(role);
        } catch (error) {
          console.error(`RBACService: Error getting level for role ${role}:`, error);
        }
        
        if (level > highestLevel) {
          highestRole = role;
          highestLevel = level;
        }
      }

      return highestRole;
    } catch (error) {
      console.error('RBACService: Error getting highest role:', error);
      
      // Return a safe default on error
      return roles.length > 0 ? roles[0] : null;
    }
  }

  /**
   * Get all roles for the current user
   * @returns An array of all roles for the current user
   * @throws InitializationError if the RBAC system is not initialized
   * @throws UserNotFoundError if no user is set
   */
  public getUserRoles(): RoleName[] {
    this.ensureInitialized();
    this.ensureUserSet();

    return this.currentUser!.roles;
  }

  /**
   * Get all available roles
   * @returns An array of all available role names
   * @throws InitializationError if the RBAC system is not initialized
   */
  public getAllRoles(): RoleName[] {
    this.ensureInitialized();

    return roleRegistry.getAllRoleNames();
  }

  /**
   * Get all available permissions
   * @returns An array of all available permissions
   * @throws InitializationError if the RBAC system is not initialized
   */
  public getAllPermissions(): Permission[] {
    this.ensureInitialized();

    return permissionRegistry.getAllPermissions();
  }

  /**
   * Get a role definition by name
   * @param roleName The name of the role
   * @returns The role definition
   * @throws InitializationError if the RBAC system is not initialized
   * @throws RoleNotFoundError if the role is not found
   */
  public getRoleDefinition(roleName: RoleName): RoleDefinition {
    this.ensureInitialized();

    return roleRegistry.getRole(roleName);
  }

  /**
   * Get all role definitions
   * @returns An object mapping role names to their definitions
   * @throws InitializationError if the RBAC system is not initialized
   */
  public getAllRoleDefinitions(): Record<RoleName, RoleDefinition> {
    this.ensureInitialized();

    return roleRegistry.getAllRoles();
  }

  /**
   * Get the inheritance chain for a role
   * @param roleName The name of the role
   * @returns An array of role names representing the inheritance chain
   * @throws InitializationError if the RBAC system is not initialized
   * @throws RoleNotFoundError if the role is not found
   */
  public getInheritanceChain(roleName: RoleName): RoleName[] {
    this.ensureInitialized();

    return hierarchyResolver.getInheritanceChain(roleName);
  }

  /**
   * Get all roles that inherit from the specified role
   * @param roleName The parent role name
   * @returns An array of role names that inherit from the specified role
   * @throws InitializationError if the RBAC system is not initialized
   * @throws RoleNotFoundError if the role is not found
   */
  public getInheritingRoles(roleName: RoleName): RoleName[] {
    this.ensureInitialized();

    return hierarchyResolver.getChildRoles(roleName);
  }

  /**
   * Get the hierarchy level for a role
   * @param roleName The role name to get the level for
   * @returns The hierarchy level of the role
   * @throws InitializationError if the RBAC system is not initialized
   * @throws RoleNotFoundError if the role is not found
   */
  public getRoleLevel(roleName: RoleName): number {
    this.ensureInitialized();

    return hierarchyResolver.getRoleLevel(roleName);
  }

  /**
   * Check if one role has a higher or equal hierarchy level than another
   * @param roleA The first role
   * @param roleB The second role
   * @returns True if roleA has a higher or equal hierarchy level than roleB, false otherwise
   * @throws InitializationError if the RBAC system is not initialized
   */
  public isHigherOrEqual(roleA: RoleName, roleB: RoleName): boolean {
    this.ensureInitialized();

    return hierarchyResolver.isHigherOrEqual(roleA, roleB);
  }

  /**
   * Get the RBAC configuration
   * @returns The RBAC configuration
   */
  public getConfig(): RBACConfig {
    return { ...this.config };
  }

  /**
   * Update the RBAC configuration
   * @param config The new configuration or partial configuration
   */
  public updateConfig(config: Partial<RBACConfig>): void {
    this.config = { ...this.config, ...config };

    // Update cache TTL if changed
    if (config.cacheTTL !== undefined) {
      roleResolver.setCacheTTL(config.cacheTTL);
      permissionResolver.setCacheTTL(config.cacheTTL);
    }
  }

  /**
   * Get the RBAC statistics
   * @returns The RBAC statistics
   * @throws InitializationError if the RBAC system is not initialized
   */
  public getStatistics(): RBACStatistics {
    this.ensureInitialized();

    return {
      totalUsers: 0, // In a real implementation, we would get this from a user registry
      totalRoles: roleRegistry.size(),
      totalPermissions: permissionRegistry.size(),
      dynamicRoles: dynamicPermissionManager.getAllDynamicRoles().length,
      dynamicPermissions: dynamicPermissionManager.getAllDynamicPermissions().length,
      cacheHitRate: 0, // In a real implementation, we would track this
      averagePermissionCheckTime: 0, // In a real implementation, we would track this
      lastUpdated: new Date()
    };
  }

  /**
   * Clear all caches
   * @throws InitializationError if the RBAC system is not initialized
   */
  public clearCaches(): void {
    this.ensureInitialized();

    roleResolver.clearCache();
    permissionResolver.clearCache();
    hierarchyResolver.clearCache();
  }

  /**
   * Reset the RBAC system
   * This clears all data and reinitializes the system
   * @returns A promise that resolves when reset is complete
   */
  public async reset(): Promise<void> {
    // Clear all registries
    roleRegistry.clear();
    permissionRegistry.clear();
    dynamicPermissionManager.clearCache();

    // Clear all caches
    this.clearCaches();

    // Reset state
    this.currentUser = null;
    this.isInitialized = false;
    this.initializationPromise = null;

    // Reinitialize
    await this.initialize();
  }

  /**
   * Ensure the RBAC system is initialized
   * @throws InitializationError if the RBAC system is not initialized
   */
  private ensureInitialized(): void {
    if (!this.isInitialized) {
      throw new InitializationError('RBAC system is not initialized');
    }
  }

  /**
   * Ensure a user is set
   * @throws UserNotFoundError if no user is set
   */
  private ensureUserSet(): void {
    if (!this.currentUser) {
      throw new UserNotFoundError('current');
    }
  }
}

// Export the singleton instance
export const rbacService = RBACService.getInstance();