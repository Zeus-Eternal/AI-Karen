import { DatabaseClient, getDatabaseClient } from './client';
import { DatabasePerformanceMonitor } from '@/lib/performance/admin-performance-monitor';
import { UserCache, UserListCache, AdminCacheManager } from '@/lib/cache/admin-cache';
import type { User, UserListFilter, PaginationParams, PaginatedResponse, BulkOperationResult } from '@/types/admin';

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

      const users = result.rows as any[];
      const totalCount = users.length > 0 ? parseInt((users[0] as any).total_count) : 0;
      const totalPages = Math.ceil(totalCount / pagination.limit);

      const response: PaginatedResponse<User> = {
        data: users.map((row: any) => ({
          user_id: row.user_id,
          email: row.email,
          full_name: row.full_name,
          role: row.role,
          is_active: row.is_active,
          is_verified: row.is_verified,
          created_at: row.created_at,
          updated_at: row.updated_at,
          last_login_at: row.last_login_at,
          tenant_id: row.tenant_id || 'default',
          preferences: row.preferences || {},
          roles: row.roles || [],
          failed_login_attempts: row.failed_login_attempts || 0,
          locked_until: row.locked_until,
          two_factor_enabled: row.two_factor_enabled || false,
          two_factor_secret: row.two_factor_secret
        })),
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

      const updatedCount = (result.rows[0] as any)?.updated_count || 0;

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
  ): Promise<PaginatedResponse<any>> {
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

      const logs = result.rows as any[];
      const totalCount = logs.length > 0 ? parseInt((logs[0] as any).total_count) : 0;
      const totalPages = Math.ceil(totalCount / pagination.limit);

      return {
        data: logs.map((row: any) => ({
          id: row.id,
          user_id: row.user_id,
          action: row.action,
          resource_type: row.resource_type,
          resource_id: row.resource_id,
          details: row.details,
          ip_address: row.ip_address,
          user_agent: row.user_agent,
          timestamp: row.timestamp,
          user: row.user_email ? {
            user_id: row.user_id,
            email: row.user_email,
            full_name: row.user_full_name
          } : undefined
        })),
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
  async getUserStatisticsOptimized(): Promise<unknown> {
    const endQuery = DatabasePerformanceMonitor.startQuery(
      'getUserStatisticsOptimized',
      'SELECT * FROM user_statistics'
    );

    try {
      const result = await this.db.query('SELECT * FROM user_statistics');
      return result.rows[0] || {
        total_users: 0,
        active_users: 0,
        admin_users: 0,
        super_admin_users: 0,
        verified_users: 0,
        daily_active_users: 0,
        weekly_active_users: 0,
        new_users_30d: 0,
        new_users_7d: 0,
        last_user_login: null,
        first_user_created: null
      };
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
      const createdUsers = result.rows;

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
            emails: createdUsers.map((u: any) => u.email)
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

      const user = result.rows[0] as User | undefined;
      if (user) {
        // Cache the user
        UserCache.set(user);
      }

      return user || null;
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
  async getQueryPerformanceAnalysis(): Promise<any[]> {
    const endQuery = DatabasePerformanceMonitor.startQuery(
      'getQueryPerformanceAnalysis',
      'SELECT * FROM analyze_admin_query_performance()'
    );

    try {
      const result = await this.db.query('SELECT * FROM analyze_admin_query_performance()');
      return result.rows;
    } finally {
      endQuery();
    }
  }

  /**
   * Get table statistics for monitoring
   */
  async getTableStatistics(): Promise<any[]> {
    const endQuery = DatabasePerformanceMonitor.startQuery(
      'getTableStatistics',
      'SELECT * FROM get_admin_table_stats()'
    );

    try {
      const result = await this.db.query('SELECT * FROM get_admin_table_stats()');
      return result.rows;
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
