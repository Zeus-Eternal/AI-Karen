/**
 * Database utilities index file
 * 
 * Exports all database utility functions and classes for the admin management system
 */

export { AdminDatabaseUtils, getAdminDatabaseUtils } from './admin-utils';
export type { 
  DatabaseClient, 
  QueryResult
} from './client';
export { 
  MockDatabaseClient, 
  PostgreSQLClient, 
  DatabaseClientFactory,
  getDatabaseClient,
  setDatabaseClient
} from './client';

// Re-export types that are commonly used with database utilities
export type {
  User,
  AuditLog,
  SystemConfig,
  Permission,
  RolePermission,
  UserListFilter,
  AuditLogFilter,
  PaginationParams,
  PaginatedResponse,
  AuditLogEntry,
  RoleBasedQuery,
  AdminApiResponse
} from '@/types/admin';