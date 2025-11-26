/**
 * RBAC Configuration Constants
 * 
 * This file defines the configuration constants for the Role-Based Access Control (RBAC) system.
 * It includes default values, mappings between frontend and backend, and other configuration options.
 */

import { 
  RBACConfig, 
  RoleMapping, 
  PermissionMapping, 
  RoleName, 
  Permission,
  PermissionCategory 
} from './types';

// Default RBAC configuration
export const DEFAULT_RBAC_CONFIG: RBACConfig = {
  enableCache: true,
  cacheTTL: 5 * 60 * 1000, // 5 minutes
  enableDebugLogging: process.env.NODE_ENV === 'development',
  enableStrictMode: false,
  enableDynamicPermissions: true,
  defaultRole: 'user',
  guestRole: 'readonly'
};

// Mapping between frontend and backend roles
export const ROLE_MAPPINGS: RoleMapping[] = [
  { frontend: 'super_admin', backend: 'super_admin', description: 'Highest privilege role with unrestricted access' },
  { frontend: 'admin', backend: 'admin', description: 'Platform administrator' },
  { frontend: 'trainer', backend: 'trainer', description: 'Training specialist with model and data management access' },
  { frontend: 'analyst', backend: 'analyst', description: 'Read focused analyst role' },
  { frontend: 'user', backend: 'user', description: 'Standard platform user' },
  { frontend: 'readonly', backend: 'readonly', description: 'Read only visibility' },
  { frontend: 'model_manager', backend: 'model_manager', description: 'Operational model management' },
  { frontend: 'data_steward', backend: 'data_steward', description: 'Manage datasets and training corpora' },
  { frontend: 'routing_admin', backend: 'routing_admin', description: 'Full routing administration' },
  { frontend: 'routing_operator', backend: 'routing_operator', description: 'Operational routing control' },
  { frontend: 'routing_auditor', backend: 'routing_auditor', description: 'Read only routing insights' }
];

// Mapping between frontend and backend permissions
export const PERMISSION_MAPPINGS: PermissionMapping[] = [
  { frontend: 'admin:read', backend: 'admin:read', description: 'Read admin settings' },
  { frontend: 'admin:system', backend: 'admin:system', description: 'System administration' },
  { frontend: 'admin:write', backend: 'admin:write', description: 'Write admin settings' },
  { frontend: 'audit:read', backend: 'audit:read', description: 'Read audit logs' },
  { frontend: 'data:delete', backend: 'data:delete', description: 'Delete data' },
  { frontend: 'data:export', backend: 'data:export', description: 'Export data' },
  { frontend: 'data:read', backend: 'data:read', description: 'Read data' },
  { frontend: 'data:write', backend: 'data:write', description: 'Write data' },
  { frontend: 'model:compatibility:check', backend: 'model:compatibility:check', description: 'Check model compatibility' },
  { frontend: 'model:delete', backend: 'model:delete', description: 'Delete models' },
  { frontend: 'model:deploy', backend: 'model:deploy', description: 'Deploy models' },
  { frontend: 'model:download', backend: 'model:download', description: 'Download models' },
  { frontend: 'model:ensure', backend: 'model:ensure', description: 'Ensure models are available' },
  { frontend: 'model:gc', backend: 'model:gc', description: 'Garbage collect models' },
  { frontend: 'model:health:check', backend: 'model:health:check', description: 'Check model health' },
  { frontend: 'model:info', backend: 'model:info', description: 'Get model information' },
  { frontend: 'model:license:accept', backend: 'model:license:accept', description: 'Accept model licenses' },
  { frontend: 'model:license:manage', backend: 'model:license:manage', description: 'Manage model licenses' },
  { frontend: 'model:license:view', backend: 'model:license:view', description: 'View model licenses' },
  { frontend: 'model:list', backend: 'model:list', description: 'List models' },
  { frontend: 'model:pin', backend: 'model:pin', description: 'Pin models' },
  { frontend: 'model:quota:manage', backend: 'model:quota:manage', description: 'Manage model quotas' },
  { frontend: 'model:read', backend: 'model:read', description: 'Read models' },
  { frontend: 'model:registry:read', backend: 'model:registry:read', description: 'Read model registry' },
  { frontend: 'model:registry:write', backend: 'model:registry:write', description: 'Write model registry' },
  { frontend: 'model:remove', backend: 'model:remove', description: 'Remove models' },
  { frontend: 'model:unpin', backend: 'model:unpin', description: 'Unpin models' },
  { frontend: 'model:write', backend: 'model:write', description: 'Write models' },
  { frontend: 'routing:audit', backend: 'routing:audit', description: 'Audit routing' },
  { frontend: 'routing:dry_run', backend: 'routing:dry_run', description: 'Dry run routing' },
  { frontend: 'routing:health', backend: 'routing:health', description: 'Check routing health' },
  { frontend: 'routing:profile:manage', backend: 'routing:profile:manage', description: 'Manage routing profiles' },
  { frontend: 'routing:profile:view', backend: 'routing:profile:view', description: 'View routing profiles' },
  { frontend: 'routing:select', backend: 'routing:select', description: 'Select routing' },
  { frontend: 'scheduler:execute', backend: 'scheduler:execute', description: 'Execute scheduler' },
  { frontend: 'scheduler:read', backend: 'scheduler:read', description: 'Read scheduler' },
  { frontend: 'scheduler:write', backend: 'scheduler:write', description: 'Write scheduler' },
  { frontend: 'security:evil_mode', backend: 'security:evil_mode', description: 'Evil mode security' },
  { frontend: 'security:read', backend: 'security:read', description: 'Read security settings' },
  { frontend: 'security:write', backend: 'security:write', description: 'Write security settings' },
  { frontend: 'training:delete', backend: 'training:delete', description: 'Delete training' },
  { frontend: 'training:execute', backend: 'training:execute', description: 'Execute training' },
  { frontend: 'training:read', backend: 'training:read', description: 'Read training' },
  { frontend: 'training:write', backend: 'training:write', description: 'Write training' },
  { frontend: 'training_data:delete', backend: 'training_data:delete', description: 'Delete training data' },
  { frontend: 'training_data:read', backend: 'training_data:read', description: 'Read training data' },
  { frontend: 'training_data:write', backend: 'training_data:write', description: 'Write training data' }
];

// Permission categories
export const PERMISSION_CATEGORIES: PermissionCategory[] = [
  {
    name: 'Administration',
    description: 'Administrative permissions',
    permissions: ['admin:read', 'admin:system', 'admin:write', 'audit:read']
  },
  {
    name: 'Data Management',
    description: 'Data access and manipulation permissions',
    permissions: ['data:delete', 'data:export', 'data:read', 'data:write']
  },
  {
    name: 'Model Management',
    description: 'Model lifecycle and management permissions',
    permissions: [
      'model:compatibility:check', 'model:delete', 'model:deploy', 'model:download',
      'model:ensure', 'model:gc', 'model:health:check', 'model:info',
      'model:license:accept', 'model:license:manage', 'model:license:view',
      'model:list', 'model:pin', 'model:quota:manage', 'model:read',
      'model:registry:read', 'model:registry:write', 'model:remove',
      'model:unpin', 'model:write'
    ]
  },
  {
    name: 'Routing',
    description: 'Request routing and profile management permissions',
    permissions: [
      'routing:audit', 'routing:dry_run', 'routing:health',
      'routing:profile:manage', 'routing:profile:view', 'routing:select'
    ]
  },
  {
    name: 'Scheduler',
    description: 'Task scheduling and execution permissions',
    permissions: ['scheduler:execute', 'scheduler:read', 'scheduler:write']
  },
  {
    name: 'Security',
    description: 'Security settings and management permissions',
    permissions: ['security:evil_mode', 'security:read', 'security:write']
  },
  {
    name: 'Training',
    description: 'Model training and management permissions',
    permissions: ['training:delete', 'training:execute', 'training:read', 'training:write']
  },
  {
    name: 'Training Data',
    description: 'Training data management permissions',
    permissions: ['training_data:delete', 'training_data:read', 'training_data:write']
  }
];

// Role hierarchy levels (higher number = higher privilege)
export const ROLE_HIERARCHY_LEVELS: Record<RoleName, number> = {
  'readonly': 0,
  'user': 1,
  'analyst': 2,
  'routing_auditor': 3,
  'trainer': 4,
  'data_steward': 5,
  'model_manager': 6,
  'routing_operator': 7,
  'routing_admin': 8,
  'admin': 9,
  'super_admin': 10
};

// Cache keys
export const CACHE_KEYS = {
  USER_PERMISSIONS: (userId: string) => `rbac:user_permissions:${userId}`,
  USER_ROLES: (userId: string) => `rbac:user_roles:${userId}`,
  ROLE_DEFINITIONS: 'rbac:role_definitions',
  PERMISSION_DEFINITIONS: 'rbac:permission_definitions',
  DYNAMIC_PERMISSIONS: 'rbac:dynamic_permissions',
  DYNAMIC_ROLES: 'rbac:dynamic_roles'
};

// Event names
export const RBAC_EVENTS = {
  PERMISSION_GRANTED: 'rbac:permission_granted',
  PERMISSION_REVOKED: 'rbac:permission_revoked',
  ROLE_ASSIGNED: 'rbac:role_assigned',
  ROLE_REMOVED: 'rbac:role_removed',
  DYNAMIC_PERMISSION_ADDED: 'rbac:dynamic_permission_added',
  DYNAMIC_PERMISSION_REMOVED: 'rbac:dynamic_permission_removed',
  DYNAMIC_ROLE_ADDED: 'rbac:dynamic_role_added',
  DYNAMIC_ROLE_REMOVED: 'rbac:dynamic_role_removed',
  CACHE_CLEARED: 'rbac:cache_cleared'
};

// Default permissions for guest users
export const GUEST_PERMISSIONS: Permission[] = [
  'model:info',
  'model:read',
  'training:read'
];

// API endpoints
export const RBAC_API_ENDPOINTS = {
  GET_USER_PERMISSIONS: '/api/rbac/user/permissions',
  GET_USER_ROLES: '/api/rbac/user/roles',
  GET_ALL_ROLES: '/api/rbac/roles',
  GET_ALL_PERMISSIONS: '/api/rbac/permissions',
  ADD_DYNAMIC_PERMISSION: '/api/rbac/permissions/dynamic',
  REMOVE_DYNAMIC_PERMISSION: '/api/rbac/permissions/dynamic/:id',
  ADD_DYNAMIC_ROLE: '/api/rbac/roles/dynamic',
  REMOVE_DYNAMIC_ROLE: '/api/rbac/roles/dynamic/:id',
  ASSIGN_ROLE_TO_USER: '/api/rbac/users/:userId/roles',
  REMOVE_ROLE_FROM_USER: '/api/rbac/users/:userId/roles/:role',
  GET_PERMISSION_AUDIT_LOG: '/api/rbac/audit/permissions',
  GET_ROLE_AUDIT_LOG: '/api/rbac/audit/roles'
};

// Error messages
export const RBAC_ERROR_MESSAGES = {
  ROLE_NOT_FOUND: (role: RoleName) => `Role '${role}' not found`,
  PERMISSION_NOT_FOUND: (permission: Permission) => `Permission '${permission}' not found`,
  CIRCULAR_INHERITANCE: (role: RoleName) => `Circular inheritance detected for role '${role}'`,
  INVALID_ROLE_DEFINITION: (role: RoleName) => `Invalid role definition for '${role}'`,
  INVALID_PERMISSION: (permission: Permission) => `Invalid permission '${permission}'`,
  USER_NOT_FOUND: (userId: string) => `User with ID '${userId}' not found`,
  CACHE_ERROR: (operation: string) => `Cache error during ${operation}`,
  INITIALIZATION_ERROR: (reason: string) => `RBAC initialization error: ${reason}`,
  VALIDATION_ERROR: (field: string, value: unknown) => `Validation error for field '${field}' with value '${value}'`
};

// Local storage keys
export const LOCAL_STORAGE_KEYS = {
  USER_ROLES: 'rbac:user_roles',
  USER_PERMISSIONS: 'rbac:user_permissions',
  LAST_UPDATED: 'rbac:last_updated'
};