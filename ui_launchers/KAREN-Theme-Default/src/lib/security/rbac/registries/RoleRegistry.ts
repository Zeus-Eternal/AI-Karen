/**
 * Role Registry
 * 
 * This class manages the registration and retrieval of roles in the RBAC system.
 * It provides a centralized way to register, validate, and retrieve role definitions.
 */

import { RoleName, RoleDefinition } from '../types';
import {
  RoleNotFoundError,
  InvalidRoleDefinitionError,
  CircularInheritanceError
} from '../utils/errors';

/**
 * The RoleRegistry class manages role definitions and provides methods to register,
 * validate, and retrieve roles.
 */
export class RoleRegistry {
  private roles: Map<RoleName, RoleDefinition> = new Map();
  private isInitialized = false;

  /**
   * Initialize the role registry with default roles
   */
  public initialize(): void {
    if (this.isInitialized) {
      return;
    }

    // Clear any existing roles
    this.roles.clear();

    // Add default roles from the configuration
    this.isInitialized = true;
  }

  /**
   * Register a new role or update an existing one
   * @param name The name of the role
   * @param definition The role definition
   * @throws InvalidRoleDefinitionError if the role definition is invalid
   * @throws CircularInheritanceError if the role creates a circular inheritance
   */
  public registerRole(name: RoleName, definition: RoleDefinition): void {
    this.validateRoleDefinition(name, definition);
    this.checkForCircularInheritance(name, definition);
    
    this.roles.set(name, definition);
  }

  /**
   * Register multiple roles at once
   * @param roles An object mapping role names to their definitions
   * @throws InvalidRoleDefinitionError if any role definition is invalid
   * @throws CircularInheritanceError if any role creates a circular inheritance
   */
  public registerRoles(roles: Record<RoleName, RoleDefinition>): void {
    // First validate all roles
    for (const [name, definition] of Object.entries(roles)) {
      this.validateRoleDefinition(name as RoleName, definition);
    }

    // Then check for circular inheritance
    for (const [name, definition] of Object.entries(roles)) {
      this.checkForCircularInheritance(name as RoleName, definition);
    }

    // Finally register all roles
    for (const [name, definition] of Object.entries(roles)) {
      this.roles.set(name as RoleName, definition);
    }
  }

  /**
   * Get a role definition by name
   * @param name The name of the role
   * @returns The role definition
   * @throws RoleNotFoundError if the role is not found
   */
  public getRole(name: RoleName): RoleDefinition {
    const role = this.roles.get(name);
    if (!role) {
      throw new RoleNotFoundError(name);
    }
    return { ...role }; // Return a copy to prevent mutation
  }

  /**
   * Check if a role exists
   * @param name The name of the role
   * @returns True if the role exists, false otherwise
   */
  public hasRole(name: RoleName): boolean {
    return this.roles.has(name);
  }

  /**
   * Get all registered role names
   * @returns An array of all role names
   */
  public getAllRoleNames(): RoleName[] {
    return Array.from(this.roles.keys());
  }

  /**
   * Get all registered role definitions
   * @returns An object mapping role names to their definitions
   */
  public getAllRoles(): Record<RoleName, RoleDefinition> {
    const result: Record<RoleName, RoleDefinition> = {};
    for (const [name, definition] of this.roles.entries()) {
      result[name] = { ...definition }; // Return copies to prevent mutation
    }
    return result;
  }

  /**
   * Remove a role from the registry
   * @param name The name of the role to remove
   * @throws RoleNotFoundError if the role is not found
   */
  public removeRole(name: RoleName): void {
    if (!this.roles.has(name)) {
      throw new RoleNotFoundError(name);
    }
    this.roles.delete(name);
  }

  /**
   * Clear all roles from the registry
   */
  public clear(): void {
    this.roles.clear();
    this.isInitialized = false;
  }

  /**
   * Get the number of registered roles
   * @returns The number of registered roles
   */
  public size(): number {
    return this.roles.size;
  }

  /**
   * Check if the registry is initialized
   * @returns True if the registry is initialized, false otherwise
   */
  public initialized(): boolean {
    return this.isInitialized;
  }

  /**
   * Get the inheritance chain for a role
   * @param roleName The name of the role
   * @returns An array of role names representing the inheritance chain
   * @throws RoleNotFoundError if the role is not found
   * @throws CircularInheritanceError if a circular inheritance is detected
   */
  public getInheritanceChain(roleName: RoleName): RoleName[] {
    const chain: RoleName[] = [];
    const visited = new Set<RoleName>();
    
    const traverse = (name: RoleName): void => {
      if (visited.has(name)) {
        throw new CircularInheritanceError(name, chain);
      }
      
      visited.add(name);
      chain.push(name);
      
      const role = this.getRole(name);
      if (role.inherits_from) {
        traverse(role.inherits_from);
      }
    };
    
    traverse(roleName);
    return chain;
  }

  /**
   * Get all roles that inherit from the specified role
   * @param roleName The name of the parent role
   * @returns An array of role names that inherit from the specified role
   */
  public getInheritingRoles(roleName: RoleName): RoleName[] {
    const result: RoleName[] = [];
    
    for (const [name, definition] of this.roles.entries()) {
      if (definition.inherits_from === roleName) {
        result.push(name);
      }
    }
    
    return result;
  }

  /**
   * Validate a role definition
   * @param name The name of the role
   * @param definition The role definition to validate
   * @throws InvalidRoleDefinitionError if the role definition is invalid
   */
  private validateRoleDefinition(name: RoleName, definition: RoleDefinition): void {
    if (!name || typeof name !== 'string') {
      throw new InvalidRoleDefinitionError(
        name as string,
        'Role name must be a non-empty string'
      );
    }

    if (!definition || typeof definition !== 'object') {
      throw new InvalidRoleDefinitionError(
        name,
        'Role definition must be an object'
      );
    }

    if (!definition.description || typeof definition.description !== 'string') {
      throw new InvalidRoleDefinitionError(
        name,
        'Role description must be a non-empty string'
      );
    }

    if (definition.inherits_from !== null && 
        (typeof definition.inherits_from !== 'string' || !definition.inherits_from)) {
      throw new InvalidRoleDefinitionError(
        name,
        'Role inherits_from must be either null or a non-empty string'
      );
    }

    if (!Array.isArray(definition.permissions)) {
      throw new InvalidRoleDefinitionError(
        name,
        'Role permissions must be an array'
      );
    }

    // Check that all permissions are strings
    for (const permission of definition.permissions) {
      if (typeof permission !== 'string' || !permission) {
        throw new InvalidRoleDefinitionError(
          name,
          `Permission '${permission}' must be a non-empty string`
        );
      }
    }

    // Check that the role doesn't inherit from itself
    if (definition.inherits_from === name) {
      throw new InvalidRoleDefinitionError(
        name,
        'Role cannot inherit from itself'
      );
    }
  }

  /**
   * Check for circular inheritance in a role definition
   * @param name The name of the role
   * @param definition The role definition to check
   * @throws CircularInheritanceError if a circular inheritance is detected
   */
  private checkForCircularInheritance(name: RoleName, definition: RoleDefinition): void {
    if (!definition.inherits_from) {
      return; // No inheritance, no circularity possible
    }

    const visited = new Set<RoleName>();
    const chain: RoleName[] = [];
    
    const traverse = (currentName: RoleName): void => {
      if (currentName === name) {
        throw new CircularInheritanceError(name, [...chain, currentName]);
      }
      
      if (visited.has(currentName)) {
        return; // Already visited this node, no circularity involving the current role
      }
      
      visited.add(currentName);
      chain.push(currentName);
      
      const currentRole = this.roles.get(currentName);
      if (currentRole && currentRole.inherits_from) {
        traverse(currentRole.inherits_from);
      }
    };
    
    traverse(definition.inherits_from);
  }
}

// Export a singleton instance
export const roleRegistry = new RoleRegistry();