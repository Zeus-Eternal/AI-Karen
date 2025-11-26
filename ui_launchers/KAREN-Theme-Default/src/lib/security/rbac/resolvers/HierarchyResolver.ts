/**
 * Hierarchy Resolver
 * 
 * This class is responsible for resolving role hierarchies and providing hierarchy-related utilities.
 * It provides methods to analyze and manipulate role hierarchies, check role relationships,
 * and resolve inheritance chains.
 */

import { RoleName, RoleHierarchy } from '../types';
import {
  RoleNotFoundError,
  CircularInheritanceError
} from '../utils/errors';
import { roleRegistry } from '../registries/RoleRegistry';
import { ROLE_HIERARCHY_LEVELS } from '../config';

/**
 * The HierarchyResolver class handles role hierarchy resolution and provides hierarchy-related utilities.
 */
export class HierarchyResolver {
  private hierarchyCache: Map<string, RoleHierarchy> = new Map();
  private isInitialized = false;

  /**
   * Initialize the hierarchy resolver
   */
  public initialize(): void {
    if (this.isInitialized) {
      return;
    }

    this.hierarchyCache.clear();
    this.isInitialized = true;
  }

  /**
   * Get the role hierarchy
   * @returns A RoleHierarchy object representing the role hierarchy
   */
  public getHierarchy(): RoleHierarchy {
    if (!this.isInitialized) {
      this.initialize();
    }

    // Check if we have a cached hierarchy
    if (this.hierarchyCache.has('default')) {
      return { ...this.hierarchyCache.get('default')! };
    }

    // Build the hierarchy
    const hierarchy: RoleHierarchy = {};
    const allRoles = roleRegistry.getAllRoleNames();

    // Initialize all roles with default values
    for (const roleName of allRoles) {
      hierarchy[roleName] = {
        level: ROLE_HIERARCHY_LEVELS[roleName] || 0,
        parent: null,
        children: []
      };
    }

    // Set up parent-child relationships
    for (const roleName of allRoles) {
      const role = roleRegistry.getRole(roleName);
      
      if (role.inherits_from) {
        // Ensure the parent role exists
        if (!hierarchy[role.inherits_from]) {
          throw new RoleNotFoundError(role.inherits_from);
        }
        
        // Set the parent
        hierarchy[roleName].parent = role.inherits_from;
        
        // Add this role as a child of the parent
        hierarchy[role.inherits_from].children.push(roleName);
      }
    }

    // Cache the hierarchy
    this.hierarchyCache.set('default', { ...hierarchy });

    return hierarchy;
  }

  /**
   * Get the hierarchy level for a role
   * @param roleName The role name to get the level for
   * @returns The hierarchy level of the role
   * @throws RoleNotFoundError if the role is not found
   */
  public getRoleLevel(roleName: RoleName): number {
    const hierarchy = this.getHierarchy();
    const roleInfo = hierarchy[roleName];
    
    if (!roleInfo) {
      throw new RoleNotFoundError(roleName);
    }
    
    return roleInfo.level;
  }

  /**
   * Get the parent role for a role
   * @param roleName The role name to get the parent for
   * @returns The parent role name, or null if the role has no parent
   * @throws RoleNotFoundError if the role is not found
   */
  public getParentRole(roleName: RoleName): RoleName | null {
    const hierarchy = this.getHierarchy();
    const roleInfo = hierarchy[roleName];
    
    if (!roleInfo) {
      throw new RoleNotFoundError(roleName);
    }
    
    return roleInfo.parent;
  }

  /**
   * Get the child roles for a role
   * @param roleName The role name to get the children for
   * @returns An array of child role names
   * @throws RoleNotFoundError if the role is not found
   */
  public getChildRoles(roleName: RoleName): RoleName[] {
    const hierarchy = this.getHierarchy();
    const roleInfo = hierarchy[roleName];
    
    if (!roleInfo) {
      throw new RoleNotFoundError(roleName);
    }
    
    return [...roleInfo.children];
  }

  /**
   * Get all descendant roles for a role (children, grandchildren, etc.)
   * @param roleName The role name to get the descendants for
   * @returns An array of descendant role names
   * @throws RoleNotFoundError if the role is not found
   */
  public getDescendantRoles(roleName: RoleName): RoleName[] {
    const descendants: RoleName[] = [];
    
    const traverse = (currentRole: RoleName): void => {
      const children = this.getChildRoles(currentRole);
      for (const child of children) {
        descendants.push(child);
        traverse(child);
      }
    };
    
    traverse(roleName);
    return descendants;
  }

  /**
   * Get all ancestor roles for a role (parent, grandparent, etc.)
   * @param roleName The role name to get the ancestors for
   * @returns An array of ancestor role names
   * @throws RoleNotFoundError if the role is not found
   */
  public getAncestorRoles(roleName: RoleName): RoleName[] {
    const ancestors: RoleName[] = [];
    let currentRole = roleName;
    
    // eslint-disable-next-line no-constant-condition
    while (true) {
      const parent = this.getParentRole(currentRole);
      if (!parent) {
        break;
      }
      ancestors.push(parent);
      currentRole = parent;
    }
    
    return ancestors;
  }

  /**
   * Get the inheritance chain for a role
   * @param roleName The role name to get the inheritance chain for
   * @returns An array of role names representing the inheritance chain
   * @throws RoleNotFoundError if the role is not found
   */
  public getInheritanceChain(roleName: RoleName): RoleName[] {
    const ancestors = this.getAncestorRoles(roleName);
    return [roleName, ...ancestors.reverse()];
  }

  /**
   * Check if one role is an ancestor of another
   * @param ancestorRole The potential ancestor role
   * @param descendantRole The potential descendant role
   * @returns True if the ancestorRole is an ancestor of descendantRole, false otherwise
   */
  public isAncestor(ancestorRole: RoleName, descendantRole: RoleName): boolean {
    try {
      const ancestors = this.getAncestorRoles(descendantRole);
      return ancestors.includes(ancestorRole);
    } catch (error) {
      if (error instanceof RoleNotFoundError) {
        return false;
      }
      throw error;
    }
  }

  /**
   * Check if one role is a descendant of another
   * @param descendantRole The potential descendant role
   * @param ancestorRole The potential ancestor role
   * @returns True if the descendantRole is a descendant of ancestorRole, false otherwise
   */
  public isDescendant(descendantRole: RoleName, ancestorRole: RoleName): boolean {
    return this.isAncestor(ancestorRole, descendantRole);
  }

  /**
   * Check if one role has a higher or equal hierarchy level than another
   * @param roleA The first role
   * @param roleB The second role
   * @returns True if roleA has a higher or equal hierarchy level than roleB, false otherwise
   */
  public isHigherOrEqual(roleA: RoleName, roleB: RoleName): boolean {
    try {
      const levelA = this.getRoleLevel(roleA);
      const levelB = this.getRoleLevel(roleB);
      return levelA >= levelB;
    } catch (error) {
      if (error instanceof RoleNotFoundError) {
        return false;
      }
      throw error;
    }
  }

  /**
   * Check if one role has a strictly higher hierarchy level than another
   * @param roleA The first role
   * @param roleB The second role
   * @returns True if roleA has a strictly higher hierarchy level than roleB, false otherwise
   */
  public isStrictlyHigher(roleA: RoleName, roleB: RoleName): boolean {
    try {
      const levelA = this.getRoleLevel(roleA);
      const levelB = this.getRoleLevel(roleB);
      return levelA > levelB;
    } catch (error) {
      if (error instanceof RoleNotFoundError) {
        return false;
      }
      throw error;
    }
  }

  /**
   * Get the lowest common ancestor of two roles
   * @param roleA The first role
   * @param roleB The second role
   * @returns The lowest common ancestor role, or null if there is no common ancestor
   */
  public getLowestCommonAncestor(roleA: RoleName, roleB: RoleName): RoleName | null {
    try {
      const ancestorsA = new Set(this.getAncestorRoles(roleA));
      ancestorsA.add(roleA); // Include the role itself
      
      const ancestorsB = this.getAncestorRoles(roleB);
      
      // Check roleB and its ancestors
      if (ancestorsA.has(roleB)) {
        return roleB;
      }
      
      for (const ancestor of ancestorsB) {
        if (ancestorsA.has(ancestor)) {
          return ancestor;
        }
      }
      
      return null;
    } catch (error) {
      if (error instanceof RoleNotFoundError) {
        return null;
      }
      throw error;
    }
  }

  /**
   * Check if the role hierarchy is valid (no circular references)
   * @returns True if the hierarchy is valid, false otherwise
   */
  public validateHierarchy(): boolean {
    try {
      const allRoles = roleRegistry.getAllRoleNames();
      
      for (const roleName of allRoles) {
        // This will throw a CircularInheritanceError if there's a circular reference
        roleRegistry.getInheritanceChain(roleName);
      }
      
      return true;
    } catch (error) {
      if (error instanceof CircularInheritanceError) {
        return false;
      }
      throw error;
    }
  }

  /**
   * Get the highest role in the hierarchy
   * @returns The highest role name, or null if there are no roles
   */
  public getHighestRole(): RoleName | null {
    const hierarchy = this.getHierarchy();
    let highestRole: RoleName | null = null;
    let highestLevel = -1;
    
    for (const [roleName, roleInfo] of Object.entries(hierarchy)) {
      if (roleInfo.level > highestLevel) {
        highestLevel = roleInfo.level;
        highestRole = roleName as RoleName;
      }
    }
    
    return highestRole;
  }

  /**
   * Get the lowest role in the hierarchy
   * @returns The lowest role name, or null if there are no roles
   */
  public getLowestRole(): RoleName | null {
    const hierarchy = this.getHierarchy();
    let lowestRole: RoleName | null = null;
    let lowestLevel = Infinity;
    
    for (const [roleName, roleInfo] of Object.entries(hierarchy)) {
      if (roleInfo.level < lowestLevel) {
        lowestLevel = roleInfo.level;
        lowestRole = roleName as RoleName;
      }
    }
    
    return lowestRole;
  }

  /**
   * Get all roles at a specific hierarchy level
   * @param level The hierarchy level
   * @returns An array of role names at the specified level
   */
  public getRolesAtLevel(level: number): RoleName[] {
    const hierarchy = this.getHierarchy();
    const roles: RoleName[] = [];
    
    for (const [roleName, roleInfo] of Object.entries(hierarchy)) {
      if (roleInfo.level === level) {
        roles.push(roleName as RoleName);
      }
    }
    
    return roles;
  }

  /**
   * Get the hierarchy path between two roles
   * @param fromRole The starting role
   * @param toRole The ending role
   * @returns An array of role names representing the path from fromRole to toRole, or null if no path exists
   */
  public getHierarchyPath(fromRole: RoleName, toRole: RoleName): RoleName[] | null {
    try {
      // If fromRole is an ancestor of toRole, go up from toRole to fromRole
      if (this.isAncestor(fromRole, toRole)) {
        const path: RoleName[] = [toRole];
        let currentRole = toRole;
        
        while (currentRole !== fromRole) {
          const parent = this.getParentRole(currentRole);
          if (!parent) {
            break;
          }
          path.push(parent);
          currentRole = parent;
        }
        
        return path.reverse();
      }
      
      // If toRole is an ancestor of fromRole, go up from fromRole to toRole
      if (this.isAncestor(toRole, fromRole)) {
        const path: RoleName[] = [fromRole];
        let currentRole = fromRole;
        
        while (currentRole !== toRole) {
          const parent = this.getParentRole(currentRole);
          if (!parent) {
            break;
          }
          path.push(parent);
          currentRole = parent;
        }
        
        return path;
      }
      
      // If they have a common ancestor, find the path through the common ancestor
      const commonAncestor = this.getLowestCommonAncestor(fromRole, toRole);
      if (commonAncestor) {
        const pathFrom = this.getHierarchyPath(fromRole, commonAncestor) || [];
        const pathTo = this.getHierarchyPath(commonAncestor, toRole) || [];
        
        // Remove the common ancestor from the second path to avoid duplication
        pathTo.shift();
        
        return [...pathFrom, ...pathTo];
      }
      
      return null;
    } catch (error) {
      if (error instanceof RoleNotFoundError) {
        return null;
      }
      throw error;
    }
  }

  /**
   * Clear the hierarchy cache
   */
  public clearCache(): void {
    this.hierarchyCache.clear();
  }
}

// Export a singleton instance
export const hierarchyResolver = new HierarchyResolver();