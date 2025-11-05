/**
 * Database utilities index file
 * 
 * Exports all database utility functions and classes for the admin management system
 */

export { AdminDatabaseUtils, getAdminDatabaseUtils } from './admin-utils';
export { 
  getDatabaseClient,
  setDatabaseClient,
  closeDatabaseClient
} from './client';

// Re-export types that are commonly used with database utilities
export type { 
  DatabaseClientConfig,
  DatabaseClient,
  AdminDatabaseUtilsType
} from '@/types/admin';
