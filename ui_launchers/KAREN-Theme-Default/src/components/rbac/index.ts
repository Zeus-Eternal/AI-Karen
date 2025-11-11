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
export { PermissionGate } from './PermissionGate';
export type {
  PermissionGateProps,
  PermissionDeniedFallbackProps,
} from './PermissionGate';
export { withPermission, usePermissionGate } from './permission-gate-helpers';
export type {
  WithPermissionOptions,
  UsePermissionGateResult,
} from './permission-gate-helpers';

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
export { RBACProvider } from '@/providers/rbac-provider';
export { useRBAC } from '@/providers/rbac-hooks';
export type { RBACContextValue } from '@/providers/rbac-provider';

// Re-export RBAC types
export type {
  Role,
  Permission,
  User,
  AccessContext,
  PermissionCheckResult,
  RoleHierarchy,
  Restriction,
} from '@/types/rbac';
