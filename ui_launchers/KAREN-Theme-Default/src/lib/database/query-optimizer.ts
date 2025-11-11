import { DatabaseClient, getDatabaseClient } from './client';
import { DatabasePerformanceMonitor } from '@/lib/performance/admin-performance-monitor';
import { UserCache, UserListCache, AdminCacheManager } from '@/lib/cache/admin-cache';
import type {
  AuditLog,
  BulkOperationResult,
  PaginatedResponse,
  PaginationParams,
  User,
  UserListFilter,
  UserStatistics,
} from '@/types/admin';

type UnknownRecord = Record<string, unknown>;

const VALID_ROLES: ReadonlySet<User['role']> = new Set(['super_admin', 'admin', 'user']);

const toRecord = (value: unknown): UnknownRecord => (
  typeof value === 'object' && value !== null ? (value as UnknownRecord) : {}
);

const toNumber = (value: unknown, fallback = 0): number => {
  if (typeof value === 'number') {
    return Number.isFinite(value) ? value : fallback;
  }
  if (typeof value === 'string') {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }
  return fallback;
};

const toBoolean = (value: unknown): boolean => {
  if (typeof value === 'boolean') {
    return value;
  }
  if (typeof value === 'number') {
    return value !== 0;
  }
  if (typeof value === 'string') {
    const normalized = value.trim().toLowerCase();
    return normalized === 'true' || normalized === '1';
  }
  return Boolean(value);
};

const toOptionalString = (value: unknown): string | undefined => (
  typeof value === 'string' && value.length > 0 ? value : undefined
);

const toMandatoryString = (value: unknown, fallback = ''): string => (
  typeof value === 'string' ? value : fallback
);

const toDate = (value: unknown): Date | undefined => {
  if (value instanceof Date) {
    return new Date(value.getTime());
  }
  if (typeof value === 'string' || typeof value === 'number') {
    const parsed = new Date(value);
    if (!Number.isNaN(parsed.getTime())) {
      return parsed;
    }
  }
  return undefined;
};

const parsePreferences = (value: unknown): User['preferences'] | undefined => {
  if (!value) {
    return undefined;
  }
  if (typeof value === 'string') {
    try {
      const parsed = JSON.parse(value);
      return typeof parsed === 'object' && parsed !== null
        ? (parsed as User['preferences'])
        : undefined;
    } catch {
      return undefined;
    }
  }
  if (typeof value === 'object') {
    return value as User['preferences'];
  }
  return undefined;
};

const parseStringArray = (value: unknown): string[] => {
  if (Array.isArray(value)) {
    return value.filter((item): item is string => typeof item === 'string');
  }
  if (typeof value === 'string' && value.length > 0) {
    return [value];
  }
  return [];
};

const normalizeRole = (value: unknown): User['role'] => {
  if (typeof value === 'string' && VALID_ROLES.has(value as User['role'])) {
    return value as User['role'];
  }
  return 'user';
};

const mapUserRow = (record: UnknownRecord): User => {
  const role = normalizeRole(record.role);
  const roles = parseStringArray(record.roles);
  if (!roles.includes(role)) {
    roles.unshift(role);
  }

  const createdAt = toDate(record.created_at) ?? new Date(0);
  const updatedAt = toDate(record.updated_at) ?? createdAt;

  const lastLogin = toDate(record.last_login_at);
  const lockedUntil = toDate(record.locked_until);

  const twoFactorSecret = record.two_factor_secret === null
    ? null
    : toOptionalString(record.two_factor_secret) ?? null;

  return {
    user_id: toMandatoryString(record.user_id),
    email: toMandatoryString(record.email),
    full_name: toOptionalString(record.full_name),
    role,
    roles,
    tenant_id: toOptionalString(record.tenant_id) ?? 'default',
    preferences: parsePreferences(record.preferences),
    is_verified: toBoolean(record.is_verified),
    is_active: toBoolean(record.is_active),
    created_at: createdAt,
    updated_at: updatedAt,
    last_login_at: lastLogin,
    failed_login_attempts: toNumber(record.failed_login_attempts, 0),
    locked_until: lockedUntil,
    two_factor_enabled: toBoolean(record.two_factor_enabled),
    two_factor_secret: twoFactorSecret,
    created_by: toOptionalString(record.created_by),
  };
};

const parseDetails = (value: unknown): Record<string, unknown> => {
  if (!value) {
    return {};
  }
  if (typeof value === 'string') {
    try {
      const parsed = JSON.parse(value);
      return typeof parsed === 'object' && parsed !== null
        ? (parsed as Record<string, unknown>)
        : {};
    } catch {
      return {};
    }
  }
  if (typeof value === 'object') {
    return value as Record<string, unknown>;
  }
  return {};
};

const mapAuditLogRow = (record: UnknownRecord): AuditLog => {
  const timestamp = toDate(record.timestamp) ?? new Date(0);
  const userEmail = toOptionalString(record.user_email);

  return {
    id: toMandatoryString(record.id),
    user_id: toMandatoryString(record.user_id),
    action: toMandatoryString(record.action),
    resource_type: toMandatoryString(record.resource_type),
    resource_id: toOptionalString(record.resource_id),
    details: parseDetails(record.details),
    ip_address: toOptionalString(record.ip_address),
    user_agent: toOptionalString(record.user_agent),
    timestamp,
    user: userEmail
      ? {
          user_id: toMandatoryString(record.user_id),
          email: userEmail,
          full_name: toOptionalString(record.user_full_name),
        }
      : undefined,
  };
};

const mapUserStatisticsRow = (record: UnknownRecord): UserStatistics => ({
  total_users: toNumber(record.total_users),
  active_users: toNumber(record.active_users),
  verified_users: toNumber(record.verified_users),
  admin_users: toNumber(record.admin_users),
  super_admin_users: toNumber(record.super_admin_users),
  users_created_today: toNumber(record.users_created_today),
  users_created_this_week: toNumber(record.users_created_this_week),
  users_created_this_month: toNumber(record.users_created_this_month),
  last_login_today: toNumber(record.last_login_today),
  two_factor_enabled: toNumber(record.two_factor_enabled),
});

export class QueryOptimizer {
  constructor(private db: DatabaseClient) {}

  /**
   * Optimized user search with full-text search and caching
   */
  async searchUsersOptimized(
    filters: UserListFilter = {},
    pagination: PaginationParams = { page: 1, limit: 20 }
  ): Promise<PaginatedResponse<User>> {
    // Check cache first
    const cachedResult = await UserListCache.get(
      filters, 
      pagination.page, 
      pagination.limit, 
      pagination.sort_by, 
      pagination.sort_order
    );
    
    if (cachedResult) {
      return cachedResult;
    }

    const endQuery = DatabasePerformanceMonitor.startQuery(
      'searchUsersOptimized',
      'SELECT * FROM search_users(...)'
    );

      try {
        const result = await this.db.query(
          'SELECT * FROM search_users($1, $2, $3, $4, $5, $6, $7, $8)',
          [
            filters.search || null,
            filters.role || null,
            filters.is_active ?? null,
            filters.is_verified ?? null,
            pagination.limit,
            (pagination.page - 1) * pagination.limit,
            pagination.sort_by || 'created_at',
            pagination.sort_order || 'desc'
          ]
        );

        const rawRows = result.rows.map(toRecord);
        const totalCount = rawRows.length > 0
          ? toNumber(rawRows[0].total_count, rawRows.length)
          : 0;
        const totalPages = Math.ceil(totalCount / pagination.limit);

        const response: PaginatedResponse<User> = {
          data: rawRows.map(mapUserRow),
          pagination: {
            page: pagination.page,
            limit: pagination.limit,
            total: totalCount,
            total_pages: totalPages,
          has_next: pagination.page < totalPages,
          has_prev: pagination.page > 1
        }
      };

      // Cache the result
      UserListCache.set(
        filters, 
        pagination.page, 
        pagination.limit, 
        response,
        pagination.sort_by, 
        pagination.sort_order
      );

      return response;
    } finally {
      endQuery();
    }
  }

  /**
   * Bulk user operations with transaction support
   */
  async bulkUpdateUsers(
    userIds: string[],
    updates: Partial<Pick<User, 'is_active' | 'role' | 'is_verified'>>,
    updatedBy: string
  ): Promise<BulkOperationResult> {
    if (userIds.length === 0) {
      return { success: true, updatedCount: 0, errors: [] };
    }

    const endQuery = DatabasePerformanceMonitor.startQuery(
      'bulkUpdateUsers',
      `UPDATE auth_users SET ... WHERE user_id IN (${userIds.length} users)`
    );

    try {
      await this.db.query('BEGIN');

        const result = await this.db.query(
          'SELECT * FROM bulk_update_users($1, $2, $3)',
          [userIds, JSON.stringify(updates), updatedBy]
        );

        const updateRecord = result.rows.length > 0 ? toRecord(result.rows[0]) : {};
        const updatedCount = toNumber(updateRecord.updated_count, 0);

      await this.db.query('COMMIT');

      // Invalidate caches for updated users
      userIds.forEach(userId => {
        AdminCacheManager.invalidateUserCaches(userId);
      });
      
      UserListCache.invalidateAll();

      return {
        success: true,
        updatedCount,
        errors: []
      };
    } catch (error) {
      await this.db.query('ROLLBACK');
      
      return {
        success: false,
        updatedCount: 0,
        errors: [error instanceof Error ? error.message : 'Unknown error']
      };
    } finally {
      endQuery();
    }
  }

  /**
   * Optimized audit log retrieval with date partitioning
   */
  async getAuditLogsOptimized(
      filters: {
        user_id?: string;
        action?: string;
        resource_type?: string;
        start_date?: Date;
        end_date?: Date;
      } = {},
      pagination: PaginationParams = { page: 1, limit: 50 }
    ): Promise<PaginatedResponse<AuditLog>> {
    const endQuery = DatabasePerformanceMonitor.startQuery(
      'getAuditLogsOptimized',
      'SELECT * FROM get_audit_logs_optimized(...)'
    );

    try {
      const result = await this.db.query(
        'SELECT * FROM get_audit_logs_optimized($1, $2, $3, $4, $5, $6, $7)',
        [
          filters.user_id || null,
          filters.action || null,
          filters.resource_type || null,
          filters.start_date || null,
          filters.end_date || null,
          pagination.limit,
          (pagination.page - 1) * pagination.limit
        ]
      );

        const rawRows = result.rows.map(toRecord);
        const totalCount = rawRows.length > 0
          ? toNumber(rawRows[0].total_count, rawRows.length)
          : 0;
        const totalPages = Math.ceil(totalCount / pagination.limit);

        return {
          data: rawRows.map(mapAuditLogRow),
          pagination: {
            page: pagination.page,
            limit: pagination.limit,
            total: totalCount,
            total_pages: totalPages,
          has_next: pagination.page < totalPages,
          has_prev: pagination.page > 1
        }
      };
    } finally {
      endQuery();
    }
  }

  /**
   * Get user statistics with materialized view optimization
   */
    async getUserStatisticsOptimized(): Promise<UserStatistics> {
      const endQuery = DatabasePerformanceMonitor.startQuery(
        'getUserStatisticsOptimized',
        'SELECT * FROM user_statistics'
      );

      try {
        const result = await this.db.query('SELECT * FROM user_statistics');
        const record = result.rows.length > 0 ? toRecord(result.rows[0]) : {};
        return mapUserStatisticsRow(record);
      } finally {
        endQuery();
      }
    }

  /**
   * Batch user creation with optimized inserts
   */
  async batchCreateUsers(
    users: Array<{
      email: string;
      full_name?: string;
      role: 'admin' | 'user';
      tenant_id?: string;
    }>,
    createdBy: string
  ): Promise<BulkOperationResult> {
    if (users.length === 0) {
      return { success: true, updatedCount: 0, errors: [] };
    }

    const endQuery = DatabasePerformanceMonitor.startQuery(
      'batchCreateUsers',
      `INSERT INTO auth_users ... (${users.length} users)`
    );

    try {
      await this.db.query('BEGIN');

      const values: unknown[] = [];
      const placeholders: string[] = [];
      let paramIndex = 1;

      users.forEach((user) => {
        placeholders.push(
          `($${paramIndex++}, $${paramIndex++}, $${paramIndex++}, $${paramIndex++}, $${paramIndex++})`
        );
        values.push(
          user.email,
          user.full_name || null,
          user.role,
          user.tenant_id || 'default',
          true // is_active
        );
      });

      const query = `
        INSERT INTO auth_users (email, full_name, role, tenant_id, is_active, created_at, updated_at)
        VALUES ${placeholders.join(', ')}
      `;

        const result = await this.db.query(query, values);
        const createdUsers = result.rows.map(toRecord);

      // Log the batch creation
      await this.db.query(
        `INSERT INTO audit_logs (user_id, action, resource_type, details, timestamp)
         VALUES ($1, $2, $3, $4, NOW())`,
        [
          createdBy,
          'user.batch_create',
          'user',
            JSON.stringify({
              count: createdUsers.length,
              emails: createdUsers.map(user => toMandatoryString(user.email)),
            })
          ]
        );

      await this.db.query('COMMIT');

      // Invalidate caches
      UserListCache.invalidateAll();
      AdminCacheManager.clearAll();

      return {
        success: true,
        updatedCount: createdUsers.length,
        errors: [],
          data: createdUsers
        };
    } catch (error) {
      await this.db.query('ROLLBACK');
      
      return {
        success: false,
        updatedCount: 0,
        errors: [error instanceof Error ? error.message : 'Unknown error']
      };
    } finally {
      endQuery();
    }
  }

  /**
   * Optimized user lookup with caching
   */
  async getUserOptimized(userId: string): Promise<User | null> {
    // Check cache first
    const cachedUser = await UserCache.get(userId);
    if (cachedUser) {
      return cachedUser;
    }

    const endQuery = DatabasePerformanceMonitor.startQuery(
      'getUserOptimized',
      'SELECT * FROM auth_users WHERE user_id = $1'
    );

    try {
        const result = await this.db.query(
          `SELECT
            user_id, email, full_name, role, roles, tenant_id, preferences,
            is_verified, is_active, created_at, updated_at, last_login_at,
            failed_login_attempts, locked_until, two_factor_enabled, two_factor_secret
           WHERE user_id = $1`,
          [userId]
        );

        const record = result.rows.length > 0 ? toRecord(result.rows[0]) : null;
        const user = record ? mapUserRow(record) : null;
        if (user) {
          // Cache the user
          UserCache.set(user);
        }

        return user;
      } finally {
        endQuery();
      }
    }

  /**
   * Refresh materialized views for better performance
   */
  async refreshStatistics(): Promise<void> {
    const endQuery = DatabasePerformanceMonitor.startQuery(
      'refreshStatistics',
      'SELECT refresh_admin_statistics()'
    );

    try {
      await this.db.query('SELECT refresh_admin_statistics()');
    } finally {
      endQuery();
    }
  }

  /**
   * Get query performance analysis
   */
    async getQueryPerformanceAnalysis(): Promise<UnknownRecord[]> {
      const endQuery = DatabasePerformanceMonitor.startQuery(
        'getQueryPerformanceAnalysis',
        'SELECT * FROM analyze_admin_query_performance()'
      );

      try {
        const result = await this.db.query('SELECT * FROM analyze_admin_query_performance()');
        return result.rows.map(toRecord);
      } finally {
        endQuery();
      }
    }

  /**
   * Get table statistics for monitoring
   */
    async getTableStatistics(): Promise<UnknownRecord[]> {
      const endQuery = DatabasePerformanceMonitor.startQuery(
        'getTableStatistics',
        'SELECT * FROM get_admin_table_stats()'
      );

      try {
        const result = await this.db.query('SELECT * FROM get_admin_table_stats()');
        return result.rows.map(toRecord);
      } finally {
        endQuery();
      }
    }
}

/**
 * Convenience function to get QueryOptimizer instance
 */
export function getQueryOptimizer(client?: DatabaseClient): QueryOptimizer {
  const dbClient = client || getDatabaseClient();
  return new QueryOptimizer(dbClient);
}
