/**
 * RBAC Type Definitions and Interfaces
 *
 * This file defines the TypeScript interfaces and types for the Role-Based Access Control (RBAC) system.
 * It aligns with the Karen Python backend RBAC system to ensure consistency across the application.
 */

// Evil Mode Types
export interface EvilModeConfig {
  enabled: boolean;
  justificationRequired: boolean;
  timeout: number; // in minutes
  timeLimit: number; // in minutes
  maxActions: number;
  auditLogging: boolean;
  notificationEnabled: boolean;
  allowedRoles: string[];
  warningMessage?: string;
  additionalAuthRequired?: boolean;
  requiredRole?: string;
  confirmationRequired?: boolean;
  auditLevel?: string;
  restrictions?: Restriction[];
}

export interface EvilModeSession {
  id: string;
  sessionId: string;
  userId: string;
  startTime: Date;
  endTime?: Date;
  reason: string;
  justification?: string;
  approvedBy: string;
  isActive: boolean;
  actions: EvilModeAction[];
}

export interface EvilModeAction {
  action: string;
  timestamp: Date;
  resource: string;
  impact: string;
  reversible: boolean;
  details: Record<string, unknown>;
}

// Core permission and role types
export type Permission = string;
export type RoleName = string;

/**
 * Represents a user role with associated permissions
 */
export interface RoleDefinition {
  description: string;
  inherits_from: RoleName | null;
  permissions: Permission[];
}

/**
 * Represents a user with their roles and permissions
 */
export interface User {
  id: string;
  username: string;
  email: string;
  roles: RoleName[];
  is_active: boolean;
  metadata?: {
    isActive?: boolean;
    [key: string]: unknown;
  };
  directPermissions?: Permission[];
  // Additional user properties as needed
}

/**
 * Represents the resolved permissions for a user
 */
export interface ResolvedPermissions {
  permissions: Permission[];
  roles: RoleDefinition[];
  lastUpdated: Date;
}

/**
 * Represents a permission check result
 */
export interface PermissionCheckResult {
  granted?: boolean;
  hasPermission?: boolean;
  reason?: string;
  sourceRole?: RoleName;
  appliedRules?: unknown[];
  restrictions?: Restriction[];
  requiresElevation?: boolean;
  elevationReason?: string;
}

/**
 * Represents a role in the system
 */
export interface Role {
  id: string;
  name: RoleName;
  description: string;
  inherits_from: RoleName | null;
  permissions: Permission[];
  restrictions?: Restriction[];
  parentRoles?: RoleName[];
  metadata?: {
    isSystemRole?: boolean;
    [key: string]: unknown;
  };
}

/**
 * Represents a role conflict
 */
export interface RoleConflict {
  role: RoleName;
  conflictType: 'inheritance' | 'permission' | 'circular';
  details: string;
  permission?: Permission;
  conflictingRoles?: RoleName[];
  resolution?: string;
}

/**
 * Represents an access context
 */
export interface AccessContext {
  resource: string;
  action: string;
  conditions?: Record<string, unknown>;
  timestamp?: Date;
  ipAddress?: string;
  location?: string;
}

/**
 * Represents a restriction
 */
export interface Restriction {
  type: 'time' | 'ip' | 'location' | 'custom' | 'time_limit' | 'ip_restriction';
  condition: string | Record<string, unknown>;
  message?: string;
  active?: boolean;
  config?: Record<string, unknown>;
}

/**
 * Represents an RBAC user
 */
export interface RBACUser {
  id: string;
  username: string;
  email: string;
  roles: RoleName[];
  is_active: boolean;
  directPermissions?: Permission[];
  restrictions?: Restriction[];
  metadata?: Record<string, unknown>;
}

/**
 * Represents a role check result
 */
export interface RoleCheckResult {
  hasRole: boolean;
  reason?: string;
  inheritedFrom?: RoleName[];
}

/**
 * Configuration for the RBAC system
 */
export interface RBACConfig {
  enableCache: boolean;
  cacheTTL: number; // in milliseconds
  enableDebugLogging: boolean;
  enableStrictMode: boolean; // Throw errors instead of returning false
  enableDynamicPermissions: boolean;
  defaultRole: RoleName;
  guestRole: RoleName;
  enableRoleHierarchy?: boolean;
  conflictResolution?: string;
  sessionTimeout?: number;
  requireReauthentication?: boolean;
  auditLevel?: string;
  cachePermissions?: boolean;
}

/**
 * Represents a cache entry for resolved permissions
 */
export interface CacheEntry<T> {
  value: T;
  timestamp: Date;
  ttl: number; // in milliseconds
}

/**
 * Represents a dynamic permission that can be added at runtime
 */
export interface DynamicPermission {
  name: Permission;
  description: string;
  category: string;
  createdAt: Date;
  createdBy: string;
  isActive: boolean;
}

/**
 * Represents a dynamic role that can be added at runtime
 */
export interface DynamicRole {
  name: RoleName;
  description: string;
  inherits_from: RoleName | null;
  permissions: Permission[];
  createdAt: Date;
  createdBy: string;
  isActive: boolean;
}

/**
 * Represents the structure of the permissions configuration file
 */
export interface PermissionsConfig {
  permissions: Permission[];
  roles: Record<RoleName, RoleDefinition>;
}

/**
 * Represents the structure of the RBAC context for React components
 */
export interface RBACContext {
  user: User | null;
  hasPermission: (permission: Permission) => boolean;
  hasRole: (role: RoleName) => boolean;
  hasAnyPermission: (permissions: Permission[]) => boolean;
  hasAllPermissions: (permissions: Permission[]) => boolean;
  hasAnyRole: (roles: RoleName[]) => boolean;
  hasAllRoles: (roles: RoleName[]) => boolean;
  refreshPermissions: () => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

/**
 * Represents the props for the PermissionGate component
 */
export interface PermissionGateProps {
  permissions: Permission | Permission[];
  requireAll?: boolean; // If true, requires all permissions; if false, requires any
  fallback?: React.ReactNode;
  children: React.ReactNode;
  showError?: boolean;
}

/**
 * Represents the props for the RoleGate component
 */
export interface RoleGateProps {
  roles: RoleName | RoleName[];
  requireAll?: boolean; // If true, requires all roles; if false, requires any
  fallback?: React.ReactNode;
  children: React.ReactNode;
  showError?: boolean;
}

/**
 * Represents the props for the SecureComponent component
 */
export interface SecureComponentProps {
  permissions?: Permission | Permission[];
  roles?: RoleName | RoleName[];
  requireAll?: boolean; // If true, requires all permissions/roles; if false, requires any
  fallback?: React.ReactNode;
  children: React.ReactNode;
  showError?: boolean;
}

/**
 * Represents the return value for the usePermissions hook
 */
export interface UsePermissionsReturn {
  hasPermission: (permission: Permission) => boolean;
  hasAnyPermission: (permissions: Permission[]) => boolean;
  hasAllPermissions: (permissions: Permission[]) => boolean;
  permissions: Permission[];
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

/**
 * Represents the return value for the useRoles hook
 */
export interface UseRolesReturn {
  hasRole: (role: RoleName) => boolean;
  hasAnyRole: (roles: RoleName[]) => boolean;
  hasAllRoles: (roles: RoleName[]) => boolean;
  roles: RoleName[];
  roleDefinitions: Record<RoleName, RoleDefinition>;
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

/**
 * Represents the return value for the useRBAC hook
 */
export interface UseRBACReturn extends UsePermissionsReturn, UseRolesReturn {
  user: User | null;
  refreshPermissions: () => Promise<void>;
}

/**
 * Represents the mapping between frontend and backend roles
 */
export interface RoleMapping {
  frontend: RoleName;
  backend: string;
  description: string;
}

/**
 * Represents the mapping between frontend and backend permissions
 */
export interface PermissionMapping {
  frontend: Permission;
  backend: string;
  description: string;
}

/**
 * Represents the backend RBAC API response
 */
export interface BackendRBACResponse {
  success: boolean;
  user: {
    id: string;
    username: string;
    email: string;
    roles: string[];
    is_active: boolean;
  };
  permissions: string[];
  roles: Record<string, {
    description: string;
    inherits_from: string | null;
    permissions: string[];
  }>;
}

/**
 * Represents the error types for the RBAC system
 */
export enum RBACErrorType {
  ROLE_NOT_FOUND = 'ROLE_NOT_FOUND',
  PERMISSION_NOT_FOUND = 'PERMISSION_NOT_FOUND',
  CIRCULAR_INHERITANCE = 'CIRCULAR_INHERITANCE',
  INVALID_ROLE_DEFINITION = 'INVALID_ROLE_DEFINITION',
  INVALID_PERMISSION = 'INVALID_PERMISSION',
  USER_NOT_FOUND = 'USER_NOT_FOUND',
  CACHE_ERROR = 'CACHE_ERROR',
  INITIALIZATION_ERROR = 'INITIALIZATION_ERROR',
  VALIDATION_ERROR = 'VALIDATION_ERROR'
}

/**
 * Represents the structure of a permission category
 */
export interface PermissionCategory {
  name: string;
  description: string;
  permissions: Permission[];
}

/**
 * Represents the structure of a role hierarchy
 */
export interface RoleHierarchy {
  [role: string]: {
    level: number;
    parent: string | null;
    children: string[];
  };
}

export interface RoleHierarchyItem {
  level: number;
  parent: string | null;
  children: string[];
  effectivePermissions?: Permission[];
}

/**
 * Represents the structure of a permission audit log
 */
export interface PermissionAuditLog {
  id: string;
  timestamp: Date;
  userId: string;
  action: 'GRANT' | 'REVOKE' | 'CHECK';
  target: 'PERMISSION' | 'ROLE';
  targetName: string;
  result: 'SUCCESS' | 'FAILURE';
  reason?: string;
  metadata?: Record<string, unknown>;
}

/**
 * Represents the structure of a role change event
 */
export interface RoleChangeEvent {
  userId: string;
  previousRoles: RoleName[];
  newRoles: RoleName[];
  changedBy: string;
  timestamp: Date;
  reason?: string;
}

/**
 * Represents the structure of a permission change event
 */
export interface PermissionChangeEvent {
  permission: Permission;
  action: 'GRANT' | 'REVOKE';
  roles: RoleName[];
  changedBy: string;
  timestamp: Date;
  reason?: string;
}

/**
 * Represents the structure of the RBAC statistics
 */
export interface RBACStatistics {
  totalUsers: number;
  totalRoles: number;
  totalPermissions: number;
  dynamicRoles: number;
  dynamicPermissions: number;
  cacheHitRate: number;
  averagePermissionCheckTime: number;
  lastUpdated: Date;
}