/**
 * RBAC Components Export - Production Grade
 *
 * This module exports all RBAC-related components and utilities
 * for role-based access control throughout the application.
 */

// ============================================================================
// Component Exports
// ============================================================================

// Permission Gate
export { PermissionGate, withPermission, usePermissionGate } from './PermissionGate';
export type {
  PermissionGateProps,
  PermissionDeniedFallbackProps,
} from './PermissionGate';

// Role Management
export { RoleManagement } from './RoleManagement';
export type {
  RoleManagementProps,
  RolesListProps,
  UserRoleTableProps,
  CreateRoleDialogProps,
  EditRoleDialogProps,
  PermissionSelectorProps,
} from './RoleManagement';

// ============================================================================
// Re-exports from RBAC Provider
// ============================================================================

// Re-export RBAC provider and hook
export { RBACProvider, useRBAC } from '@/providers/rbac-provider';

// Re-export RBAC types
export type {
  Role,
  Permission,
  User,
  RBACContext,
} from '@/types/rbac';
