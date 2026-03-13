/**
 * Role-Based Access Control (RBAC) Service
 * 
 * Manages user roles, permissions, and access control
 * for the application security system.
 */

import type { RoleName, Role } from './types';

export interface RBACUser {
  id: string;
  username: string;
  email: string;
  roles: RoleName[];
  is_active: boolean;
}

export interface RoleCheckResult {
  hasRole: boolean;
  role?: RoleName;
  reason?: string;
}

export interface PermissionCheckResult {
  hasPermission: boolean;
  permission?: string;
  reason?: string;
}

// RBAC Service Implementation
export class RBACService {
  private static instance: RBACService | null = null;
  private currentUser: RBACUser | null = null;

  /**
   * Get the singleton instance of the RBACService
   */
  public static getInstance(): RBACService {
    if (!RBACService.instance) {
      RBACService.instance = new RBACService();
    }
    return RBACService.instance;
  }

  /**
   * Private constructor to enforce singleton pattern
   */
  private constructor() {}

  /**
   * Set the current user for RBAC checks
   */
  public setCurrentUser(user: RBACUser | null): void {
    this.currentUser = user;
  }

  /**
   * Get the current user
   */
  public getCurrentUser(): RBACUser | null {
    return this.currentUser;
  }

  /**
   * Check if the current user has a specific role
   */
  public hasRole(role: RoleName): RoleCheckResult {
    if (!this.currentUser || !this.currentUser.is_active) {
      return { hasRole: false };
    }

    const hasRole = this.currentUser.roles.includes(role);
    return {
      hasRole,
      role: hasRole ? role : undefined
    };
  }

  /**
   * Check if the current user has a specific permission
   */
  public hasPermission(permission: string): PermissionCheckResult {
    if (!this.currentUser || !this.currentUser.is_active) {
      return { hasPermission: false };
    }

    // Simple permission check - in a real implementation, this would be more complex
    // based on a permission matrix or role-permission mapping
    const hasPermission = this.checkPermissionByRole(permission, this.currentUser.roles);
    
    return {
      hasPermission,
      permission: hasPermission ? permission : undefined
    };
  }

  /**
   * Get the highest role from a list of roles
   */
  public getHighestRole(roles: RoleName[]): RoleName | undefined {
    if (!roles || roles.length === 0) {
      return undefined;
    }

    const roleHierarchy: RoleName[] = [
      'super_admin',
      'admin',
      'moderator',
      'user',
      'guest',
      'readonly'
    ];

    for (const role of roleHierarchy) {
      if (roles.includes(role)) {
        return role;
      }
    }

    return roles[0]; // fallback to first role if not in hierarchy
  }

  /**
   * Check if the current user is an admin
   */
  public isAdmin(): boolean {
    return this.hasRole('admin').hasRole || this.hasRole('super_admin').hasRole;
  }

  /**
   * Check if the current user is a super admin
   */
  public isSuperAdmin(): boolean {
    return this.hasRole('super_admin').hasRole;
  }

  /**
   * Get all permissions for the current user
   */
  public getUserPermissions(): string[] {
    if (!this.currentUser || !this.currentUser.is_active) {
      return [];
    }

    const permissions: string[] = [];
    
    for (const role of this.currentUser.roles) {
      permissions.push(...this.getPermissionsForRole(role));
    }

    return [...new Set(permissions)]; // Remove duplicates
  }

  /**
   * Check permission based on role
   */
  private checkPermissionByRole(permission: string, roles: RoleName[]): boolean {
    for (const role of roles) {
      const rolePermissions = this.getPermissionsForRole(role);
      if (rolePermissions.includes(permission)) {
        return true;
      }
    }
    return false;
  }

  /**
   * Get permissions for a specific role
   */
  private getPermissionsForRole(role: RoleName): string[] {
    const rolePermissions: Record<RoleName, string[]> = {
      super_admin: [
        'all', 'users.create', 'users.read', 'users.update', 'users.delete',
        'roles.create', 'roles.read', 'roles.update', 'roles.delete',
        'system.config', 'system.monitor', 'system.backup',
        'content.create', 'content.read', 'content.update', 'content.delete',
        'analytics.read', 'analytics.export'
      ],
      admin: [
        'users.read', 'users.update',
        'roles.read',
        'content.create', 'content.read', 'content.update', 'content.delete',
        'analytics.read'
      ],
      moderator: [
        'content.read', 'content.update',
        'analytics.read'
      ],
      user: [
        'content.read', 'content.create',
        'profile.read', 'profile.update'
      ],
      guest: [
        'content.read'
      ],
      readonly: [
        'content.read',
        'profile.read',
        'analytics.read'
      ],
      trainer: [
        'content.read',
        'profile.read',
        'analytics.read'
      ],
      analyst: [
        'content.read',
        'analytics.read'
      ],
      model_manager: [
        'content.create', 'content.read', 'content.update',
        'analytics.read'
      ],
      data_steward: [
        'content.read', 'content.update',
        'analytics.read'
      ],
      routing_admin: [
        'content.read', 'content.update',
        'analytics.read'
      ],
      routing_operator: [
        'content.read',
        'analytics.read'
      ],
      routing_auditor: [
        'content.read',
        'analytics.read'
      ]
    };

    return rolePermissions[role] || [];
  }

  /**
   * Initialize the RBAC service with configuration
   */
  public initialize(config?: any): void {
    // Initialize service with configuration if provided
    // This is a placeholder for actual initialization logic
  }

  /**
   * Check if current user has any of the specified permissions
   */
  public hasAnyPermission(permissions: string[]): PermissionCheckResult {
    if (!this.currentUser || !this.currentUser.is_active) {
      return { hasPermission: false };
    }

    for (const permission of permissions) {
      const result = this.hasPermission(permission);
      if (result.hasPermission) {
        return { hasPermission: true, permission };
      }
    }

    return { hasPermission: false };
  }

  /**
   * Check if current user has all of the specified permissions
   */
  public hasAllPermissions(permissions: string[]): PermissionCheckResult {
    if (!this.currentUser || !this.currentUser.is_active) {
      return { hasPermission: false };
    }

    for (const permission of permissions) {
      const result = this.hasPermission(permission);
      if (!result.hasPermission) {
        return { hasPermission: false };
      }
    }

    return { hasPermission: true, permission: permissions[0] };
  }

  /**
   * Check if current user has any of the specified roles
   */
  public hasAnyRole(roles: RoleName[]): RoleCheckResult {
    if (!this.currentUser || !this.currentUser.is_active) {
      return { hasRole: false };
    }

    for (const role of roles) {
      const result = this.hasRole(role);
      if (result.hasRole) {
        return { hasRole: true, role };
      }
    }

    return { hasRole: false };
  }

  /**
   * Check if current user has all of the specified roles
   */
  public hasAllRoles(roles: RoleName[]): RoleCheckResult {
    if (!this.currentUser || !this.currentUser.is_active) {
      return { hasRole: false };
    }

    for (const role of roles) {
      const result = this.hasRole(role);
      if (!result.hasRole) {
        return { hasRole: false };
      }
    }

    return { hasRole: true, role: roles[0] };
  }

  /**
   * Get roles for the current user
   */
  public getUserRoles(): RoleName[] {
    if (!this.currentUser || !this.currentUser.is_active) {
      return [];
    }
    return this.currentUser.roles;
  }

  /**
   * Get all available roles
   */
  public getAllRoles(): Role[] {
    return [
      { name: 'super_admin', displayName: 'Super Admin', description: 'Full system access', permissions: this.getPermissionsForRole('super_admin'), level: 5 },
      { name: 'admin', displayName: 'Admin', description: 'Administrative access', permissions: this.getPermissionsForRole('admin'), level: 4 },
      { name: 'moderator', displayName: 'Moderator', description: 'Content moderation', permissions: this.getPermissionsForRole('moderator'), level: 3 },
      { name: 'user', displayName: 'User', description: 'Standard user access', permissions: this.getPermissionsForRole('user'), level: 2 },
      { name: 'guest', displayName: 'Guest', description: 'Limited guest access', permissions: this.getPermissionsForRole('guest'), level: 1 },
      { name: 'readonly', displayName: 'Read Only', description: 'Read-only access', permissions: this.getPermissionsForRole('readonly'), level: 0 }
    ];
  }

  /**
   * Get all available permissions
   */
  public getAllPermissions(): string[] {
    const allPermissions = new Set<string>();
    const roles = this.getAllRoles();
    
    for (const role of roles) {
      for (const permission of role.permissions) {
        allPermissions.add(permission);
      }
    }
    
    return Array.from(allPermissions);
  }

  /**
   * Get all role definitions
   */
  public getAllRoleDefinitions(): Record<RoleName, any> {
    return {
      super_admin: { name: 'super_admin', displayName: 'Super Admin', description: 'Full system access', permissions: this.getPermissionsForRole('super_admin'), level: 5 },
      admin: { name: 'admin', displayName: 'Admin', description: 'Administrative access', permissions: this.getPermissionsForRole('admin'), level: 4 },
      moderator: { name: 'moderator', displayName: 'Moderator', description: 'Content moderation', permissions: this.getPermissionsForRole('moderator'), level: 3 },
      user: { name: 'user', displayName: 'User', description: 'Standard user access', permissions: this.getPermissionsForRole('user'), level: 2 },
      guest: { name: 'guest', displayName: 'Guest', description: 'Limited guest access', permissions: this.getPermissionsForRole('guest'), level: 1 },
      readonly: { name: 'readonly', displayName: 'Read Only', description: 'Read-only access', permissions: this.getPermissionsForRole('readonly'), level: 0 },
      trainer: { name: 'trainer', displayName: 'Trainer', description: 'Training access', permissions: this.getPermissionsForRole('trainer'), level: 2 },
      analyst: { name: 'analyst', displayName: 'Analyst', description: 'Analysis access', permissions: this.getPermissionsForRole('analyst'), level: 3 },
      model_manager: { name: 'model_manager', displayName: 'Model Manager', description: 'Model management access', permissions: this.getPermissionsForRole('model_manager'), level: 4 },
      data_steward: { name: 'data_steward', displayName: 'Data Steward', description: 'Data management access', permissions: this.getPermissionsForRole('data_steward'), level: 3 },
      routing_admin: { name: 'routing_admin', displayName: 'Routing Admin', description: 'Routing administration access', permissions: this.getPermissionsForRole('routing_admin'), level: 4 },
      routing_operator: { name: 'routing_operator', displayName: 'Routing Operator', description: 'Routing operation access', permissions: this.getPermissionsForRole('routing_operator'), level: 3 },
      routing_auditor: { name: 'routing_auditor', displayName: 'Routing Auditor', description: 'Routing audit access', permissions: this.getPermissionsForRole('routing_auditor'), level: 3 }
    };
  }

  /**
   * Get permissions for a specific role
   */
  public getRolePermissions(role: RoleName): string[] {
    return this.getPermissionsForRole(role);
  }

  /**
   * Get statistics about RBAC usage
   */
  public getStatistics(): any {
    return {
      totalUsers: 0, // Would be populated from actual user data
      totalRoles: 6,
      totalPermissions: this.getAllPermissions().length,
      roleDistribution: {
        super_admin: 0,
        admin: 0,
        moderator: 0,
        user: 0,
        guest: 0,
        readonly: 0
      },
      permissionUsage: {},
      activeSessions: 0
    };
  }

  /**
   * Clear all caches
   */
  public clearCaches(): void {
    // Clear any internal caches
  }

  /**
   * Get configuration
   */
  public getConfig(): any {
    return {
      roles: this.getAllRoleDefinitions(),
      permissions: this.getAllPermissions(),
      hierarchy: {
        super_admin: 5,
        admin: 4,
        moderator: 3,
        user: 2,
        guest: 1,
        readonly: 0
      }
    };
  }

  /**
   * Update configuration
   */
  public updateConfig(config: any): void {
    // Update configuration with provided values
  }

  /**
   * Reset the service
   */
  public reset(): void {
    this.currentUser = null;
    this.clearCaches();
  }

  /**
   * Get inheritance chain for a role
   */
  public getInheritanceChain(role: RoleName): RoleName[] {
    const hierarchy: RoleName[] = ['super_admin', 'admin', 'moderator', 'user', 'guest', 'readonly'];
    const roleIndex = hierarchy.indexOf(role);
    return roleIndex >= 0 ? hierarchy.slice(roleIndex) : [];
  }

  /**
   * Check if one role is higher or equal to another
   */
  public isHigherOrEqual(role1: RoleName, role2: RoleName): boolean {
    const hierarchy = ['super_admin', 'admin', 'moderator', 'user', 'guest', 'readonly'];
    const index1 = hierarchy.indexOf(role1);
    const index2 = hierarchy.indexOf(role2);
    return index1 <= index2;
  }
}

// Export singleton instance
export const rbacService = RBACService.getInstance();