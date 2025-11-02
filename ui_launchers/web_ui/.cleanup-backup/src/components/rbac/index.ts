/**
 * RBAC Components Export
 * 
 * This module exports all RBAC-related components and utilities
 * for role-based access control throughout the application.
 */

export { PermissionGate, withPermission, usePermissionGate } from './PermissionGate';
export { RoleManagement } from './RoleManagement';

// Re-export RBAC provider and hook
export { RBACProvider, useRBAC } from '@/providers/rbac-provider';

// Re-export RBAC types
export type {
  Permission,
  Role,
  User,
  AccessContext,
  PermissionCheckResult,
  RoleHierarchy,
  RBACConfig,
  EvilModeConfig,
  EvilModeSession
} from '@/types/rbac';