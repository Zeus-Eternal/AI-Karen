/**
 * RBAC Type Definitions
 *
 * Type definitions for the Role-Based Access Control system
 */

export type RoleName = 'super_admin' | 'admin' | 'moderator' | 'user' | 'guest' | 'readonly' | 'trainer' | 'analyst' | 'model_manager' | 'data_steward' | 'routing_admin' | 'routing_operator' | 'routing_auditor';

export interface Role {
  id?: string;
  name: RoleName;
  displayName: string;
  description: string;
  permissions: Permission[];
  level: number;
  parentRoles?: RoleName[];
  metadata?: Record<string, any>;
  restrictions?: Restriction[];
}

export type Permission = string;

export interface RolePermissionMapping {
  role: RoleName;
  permissions: Permission[];
}

export interface PermissionMapping {
  frontend: Permission;
  backend: Permission;
  description: string;
}

export interface RoleMapping {
  frontend: RoleName;
  backend: RoleName;
  description?: string;
}

export interface RoleMappingIndex {
  [key: string]: RoleName;
}

export interface UserWithRoles {
  id: string;
  username: string;
  email: string;
  roles: RoleName[];
  permissions?: Permission[];
  is_active: boolean;
  metadata?: {
    isActive?: boolean;
    tenant_id?: string;
  };
}

// Missing types that are imported throughout the codebase
export interface User {
  id: string;
  username: string;
  email: string;
  roles: RoleName[];
  permissions?: Permission[];
  is_active: boolean;
  metadata?: {
    isActive?: boolean;
    tenant_id?: string;
    [key: string]: any;
  };
}

export interface RoleDefinition {
  name: RoleName;
  displayName: string;
  description: string;
  permissions: Permission[];
  level: number;
  parentRoles?: RoleName[];
  metadata?: Record<string, any>;
  inherits_from?: RoleName | null;
}

export interface UsePermissionsReturn {
  permissions: Permission[];
  hasPermission: (permission: Permission) => boolean;
  hasAnyPermission: (permissions: Permission[]) => boolean;
  hasAllPermissions: (permissions: Permission[]) => boolean;
  isLoading: boolean;
  error: string | null;
  refresh?: () => Promise<void>;
}

export interface UseRBACReturn {
  user: User | null;
  roles: Role[];
  permissions: Permission[];
  hasRole: (role: RoleName) => boolean;
  hasAnyRole: (roles: RoleName[]) => boolean;
  hasAllRoles: (roles: RoleName[]) => boolean;
  hasPermission: (permission: Permission) => boolean;
  hasAnyPermission: (permissions: Permission[]) => boolean;
  hasAllPermissions: (permissions: Permission[]) => boolean;
  loading: boolean;
  error: string | null;
}

export interface UseRolesReturn {
  roles: Role[];
  userRoles: RoleName[];
  hasRole: (role: RoleName) => boolean;
  hasAnyRole: (roles: RoleName[]) => boolean;
  hasAllRoles: (roles: RoleName[]) => boolean;
  loading: boolean;
  error: string | null;
}

export interface PermissionGateProps {
  permission?: Permission;
  permissions?: Permission[];
  requireAll?: boolean;
  fallback?: React.ReactNode;
  showError?: boolean;
  children: React.ReactNode;
}

export interface RoleGateProps {
  role?: RoleName;
  roles?: RoleName[];
  requireAll?: boolean;
  fallback?: React.ReactNode;
  showError?: boolean;
  children: React.ReactNode;
}

export interface SecureComponentProps {
  permission?: Permission;
  permissions?: Permission[];
  role?: RoleName;
  roles?: RoleName[];
  requireAll?: boolean;
  fallback?: React.ReactNode;
  showError?: boolean;
  children: React.ReactNode;
}

export interface RoleConflict {
  role: RoleName;
  conflictingRoles: RoleName[];
  reason: string;
  permission?: Permission;
  resolution?: string;
}

export interface AccessContext {
  user: User;
  permissions: Permission[];
  roles: RoleName[];
  timestamp: number | Date;
  ipAddress?: string;
}

export interface PermissionCheckResult {
  hasPermission: boolean;
  permission?: Permission;
  reason?: string;
  granted?: boolean;
  sourceRole?: RoleName;
  appliedRules?: string[];
  restrictions?: Restriction[];
  requiresElevation?: boolean;
  elevationReason?: string;
}

export interface RoleCheckResult {
  hasRole: boolean;
  role?: RoleName;
  reason?: string;
}

export interface RoleHierarchy {
  [key: string]: number;
}

export interface Restriction {
  type: string;
  value: any;
  conditions?: Record<string, any>;
  config?: Record<string, any>;
  active?: boolean;
  granted?: boolean;
  getHours?: () => number;
  getMinutes?: () => number;
}

export interface EvilModeConfig {
  enabled: boolean;
  permissions: Permission[];
  restrictions: Restriction[];
  timeLimit?: number;
  warningMessage?: string;
  additionalAuthRequired?: boolean;
  timeout?: number;
  maxActions?: number;
  auditLogging?: boolean;
  notificationEnabled?: boolean;
  allowedRoles?: RoleName[];
  requiredRole?: string;
  confirmationRequired?: boolean;
  auditLevel?: string;
}

export interface EvilModeSession {
  active: boolean;
  startTime: number;
  endTime?: number;
  reason?: string;
  actions?: Array<{
    action: string;
    resource: string;
    timestamp: number;
    impact: 'critical' | 'high' | 'medium' | 'low';
    reversible: boolean;
  }>;
}

export interface RBACConfig {
  roles: Record<RoleName, RoleDefinition>;
  permissions: Permission[];
  hierarchy: RoleHierarchy;
  restrictions: Restriction[];
  enableCache?: boolean;
  enableRoleHierarchy?: boolean;
  cacheTTL?: number;
  justificationRequired?: boolean;
  enableDebugLogging?: boolean;
  enableStrictMode?: boolean;
  enableDynamicPermissions?: boolean;
  defaultRole?: RoleName;
  guestRole?: RoleName;
  conflictResolution?: string;
  sessionTimeout?: number;
  requireReauthentication?: boolean;
  auditLevel?: string;
  cachePermissions?: boolean;
}

export interface RBACUser extends User {
  lastLogin?: Date;
  sessionExpiry?: Date;
  mfaEnabled?: boolean;
  evilMode?: EvilModeSession;
  directPermissions?: Permission[];
  restrictions?: Restriction[];
  metadata?: Record<string, any>;
}

export interface RoleHierarchyItem {
  role: RoleName;
  level: number;
  parentRoles: RoleName[];
  childRoles: RoleName[];
  effectivePermissions?: Permission[];
  parent?: number;
  children?: number[];
}

export interface DynamicPermission {
  name: Permission;
  description: string;
  category: string;
  conditions?: Record<string, any>;
  temporary?: boolean;
  expiresAt?: Date;
  createdAt?: Date;
  createdBy?: string;
}

export interface DynamicRole {
  name: RoleName;
  permissions: Permission[];
  conditions?: Record<string, any>;
  temporary?: boolean;
  expiresAt?: Date;
  createdAt?: Date;
  description?: string;
  inherits_from?: RoleName | null;
  createdBy?: string;
}

export interface RoleChangeEvent {
  type: 'add' | 'remove' | 'modify';
  role: RoleName;
  user: User;
  timestamp: Date;
  reason?: string;
  userId?: string;
  previousRoles?: RoleName[];
  newRoles?: RoleName[];
}

export interface PermissionCategory {
  name: string;
  displayName: string;
  description: string;
  permissions: Permission[];
}

export interface RBACStatistics {
  totalUsers: number;
  totalRoles: number;
  totalPermissions: number;
  roleDistribution: Record<RoleName, number>;
  permissionUsage: Record<Permission, number>;
  activeSessions: number;
}

export enum RBACErrorType {
  INVALID_ROLE = 'INVALID_ROLE',
  INVALID_PERMISSION = 'INVALID_PERMISSION',
  ACCESS_DENIED = 'ACCESS_DENIED',
  USER_NOT_FOUND = 'USER_NOT_FOUND',
  ROLE_NOT_FOUND = 'ROLE_NOT_FOUND',
  PERMISSION_NOT_FOUND = 'PERMISSION_NOT_FOUND',
  INVALID_CONFIGURATION = 'INVALID_CONFIGURATION',
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  SYSTEM_ERROR = 'SYSTEM_ERROR',
  CIRCULAR_INHERITANCE = 'CIRCULAR_INHERITANCE',
  INVALID_ROLE_DEFINITION = 'INVALID_ROLE_DEFINITION',
  CACHE_ERROR = 'CACHE_ERROR',
  INITIALIZATION_ERROR = 'INITIALIZATION_ERROR'
}