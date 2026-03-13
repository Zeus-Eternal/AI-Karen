/**
 * Admin Component Exports
 *
 * Central barrel export for all admin-related components, types, and utilities.
 * Provides comprehensive user management, monitoring, and administrative functionality.
 */

// Main Admin Dashboard
export { AdminDashboard } from './AdminDashboard';
export type { AdminDashboardProps, DashboardView } from './AdminDashboard';

// Admin Management Interface
export { default as AdminManagementInterface } from './AdminManagementInterface';
export type { AdminStatusFilter, AdminUser, InviteAdminForm } from './AdminManagementInterface';

// Bulk Operations
export { BulkUserOperations } from './BulkUserOperations';
export type {
  BulkUserOperationsProps,
  OperationType,
  RoleTarget,
  ExportFormat as BulkExportFormat,
  OperationProgress,
} from './BulkUserOperations';

// Performance Dashboard
export { PerformanceDashboard } from './PerformanceDashboard';
export type {
  PerformanceDashboardProps,
  ExportFormat as PerformanceExportFormat,
} from './PerformanceDashboard';

// Security Settings
export { default as SecuritySettingsPanel } from './SecuritySettingsPanel';
export type {
  SecuritySettings,
  SecurityAlert,
  BlockedIP,
} from './SecuritySettingsPanel';

// Super Admin Dashboard
export { default as SuperAdminDashboard } from './SuperAdminDashboard';

// System Configuration
export { default as SystemConfigurationPanel } from './SystemConfigurationPanel';
export type { SystemConfig } from './SystemConfigurationPanel';

// User Activity Monitor
export { UserActivityMonitor } from './UserActivityMonitor';
export type {
  UserActivityMonitorProps,
  ViewMode,
} from './UserActivityMonitor';

// User Creation Form
export { default as UserCreationForm } from './UserCreationForm';
export type {
  UserCreationFormProps,
  FormData as UserCreationFormData,
  FormErrors as UserCreationFormErrors,
} from './UserCreationForm';

// User Edit Modal
export { UserEditModal } from './UserEditModal';
export type {
  UserEditModalProps,
  Role as UserRole,
  FormData as UserEditFormData,
  FormErrors as UserEditFormErrors,
} from './UserEditModal';

// User Management Table
export { UserManagementTable } from './UserManagementTable';
export type {
  UserManagementTableProps,
  TableColumn as UserTableColumn,
} from './UserManagementTable';

// User Search Filters
export { UserSearchFilters } from './UserSearchFilters';
export type { UserSearchFiltersProps } from './UserSearchFilters';

// Virtualized User Table
export { VirtualizedUserTable } from './VirtualizedUserTable';
export type {
  VirtualizedUserTableProps,
  TableColumn as VirtualizedTableColumn,
  RowProps as VirtualizedRowProps,
} from './VirtualizedUserTable';

// Subdirectory exports
// export * from './audit';
// export * from './enhanced';
