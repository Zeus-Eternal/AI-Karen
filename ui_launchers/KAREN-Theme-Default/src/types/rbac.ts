/**
 * Role-Based Access Control (RBAC) Type Definitions
 * 
 * This module defines the core types for the RBAC system including
 * permissions, roles, users, and access control structures.
 */

export type Permission = 
  // Dashboard permissions
  | 'dashboard:view'
  | 'dashboard:edit'
  | 'dashboard:admin'
  
  // Memory permissions
  | 'memory:view'
  | 'memory:edit'
  | 'memory:delete'
  | 'memory:admin'
  
  // Plugin permissions
  | 'plugins:view'
  | 'plugins:install'
  | 'plugins:configure'
  | 'plugins:admin'
  
  // Model/Provider permissions
  | 'models:view'
  | 'models:configure'
  | 'models:admin'
  
  // Workflow permissions
  | 'workflows:view'
  | 'workflows:create'
  | 'workflows:execute'
  | 'workflows:admin'
  
  // Chat permissions
  | 'chat:basic'
  | 'chat:advanced'
  | 'chat:multimodal'
  
  // Security permissions
  | 'security:view'
  | 'security:audit'
  | 'security:admin'
  | 'security:evil_mode'
  
  // System permissions
  | 'system:view'
  | 'system:configure'
  | 'system:admin'
  
  // User management permissions
  | 'users:view'
  | 'users:manage'
  | 'users:admin';

export interface PermissionRule {
  permission: Permission;
  granted: boolean;
  conditions?: PermissionCondition[];
  inheritedFrom?: string; // Role ID that granted this permission
}

export interface PermissionCondition {
  type: 'time' | 'location' | 'resource' | 'context';
  operator: 'equals' | 'contains' | 'matches' | 'in_range';
  value: unknown;
  description: string;
}

export interface Role {
  id: string;
  name: string;
  description: string;
  permissions: Permission[];
  parentRoles?: string[]; // For role hierarchy
  restrictions?: Restriction[];
  metadata: {
    createdAt: Date;
    updatedAt: Date;
    createdBy: string;
    isSystemRole: boolean;
    priority: number; // For conflict resolution
  };
}

/**
 * Restriction configuration for role-based access control
 */
export interface Restriction {
  type: 'time_limit' | 'resource_quota' | 'feature_limit' | 'ip_restriction';
  description: string;
  config: Record<string, string | number | boolean>;
  active: boolean;
}

/**
 * RBAC-specific user representation for permission evaluation
 *
 * Note: This is different from the main User interface in auth.ts.
 * This representation is optimized for RBAC permission checking and
 * may have a different structure than the canonical User type.
 */
export interface RBACUser {
  id: string;
  username: string;
  email: string;
  roles: string[]; // Role IDs
  directPermissions?: Permission[]; // Direct permissions not from roles
  restrictions?: Restriction[];
  metadata: {
    createdAt: Date;
    lastLogin?: Date;
    isActive: boolean;
    requiresPasswordChange: boolean;
  };
}

/**
 * Alias for backward compatibility
 * @deprecated Use RBACUser to avoid confusion with the canonical User type
 */
export type User = RBACUser;

export interface AccessContext {
  userId: string;
  sessionId: string;
  timestamp: Date;
  ipAddress?: string;
  userAgent?: string;
  resource?: string;
  action?: string;
  additionalContext?: Record<string, unknown>;
}

export interface PermissionCheckResult {
  granted: boolean;
  reason: string;
  appliedRules: PermissionRule[];
  restrictions: Restriction[];
  requiresElevation?: boolean;
  elevationReason?: string;
}

export interface RoleHierarchy {
  roleId: string;
  parentRoles: string[];
  childRoles: string[];
  effectivePermissions: Permission[];
  conflicts: RoleConflict[];
}

export interface RoleConflict {
  permission: Permission;
  conflictingRoles: string[];
  resolution: 'grant' | 'deny' | 'manual';
  resolvedBy?: string;
  resolvedAt?: Date;
}

// RBAC Configuration
export interface RBACConfig {
  enableRoleHierarchy: boolean;
  conflictResolution: 'most_permissive' | 'least_permissive' | 'highest_priority' | 'manual';
  sessionTimeout: number;
  requireReauthentication: boolean;
  auditLevel: 'basic' | 'detailed' | 'comprehensive';
  cachePermissions: boolean;
  cacheTTL: number;
}

// Evil Mode specific types
export interface EvilModeConfig {
  enabled: boolean;
  requiredRole: Permission;
  confirmationRequired: boolean;
  additionalAuthRequired: boolean;
  auditLevel: 'detailed' | 'comprehensive';
  restrictions: Restriction[];
  warningMessage: string;
  timeLimit?: number; // Minutes
}

export interface EvilModeSession {
  userId: string;
  sessionId: string;
  startTime: Date;
  endTime?: Date;
  actions: EvilModeAction[];
  justification: string;
  approvedBy?: string;
}

export interface EvilModeAction {
  action: string;
  timestamp: Date;
  resource: string;
  impact: 'low' | 'medium' | 'high' | 'critical';
  reversible: boolean;
  details: Record<string, unknown>;
}

// Predefined system roles
export const SYSTEM_ROLES = {
  SUPER_ADMIN: 'super_admin',
  ADMIN: 'admin',
  MODERATOR: 'moderator',
  POWER_USER: 'power_user',
  USER: 'user',
  VIEWER: 'viewer',
  GUEST: 'guest'
} as const;

export type SystemRole = typeof SYSTEM_ROLES[keyof typeof SYSTEM_ROLES];
