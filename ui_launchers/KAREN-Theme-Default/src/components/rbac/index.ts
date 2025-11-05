/**
 * RBAC Components Export
 * 
 * This module exports all RBAC-related components and utilities
 * for role-based access control throughout the application.
 */

import { export { PermissionGate, withPermission, usePermissionGate } from './PermissionGate';
import { export { RoleManagement } from './RoleManagement';

// Re-export RBAC provider and hook
import { export { RBACProvider, useRBAC } from '@/providers/rbac-provider';

// Re-export RBAC types
export type {
import { } from '@/types/rbac';