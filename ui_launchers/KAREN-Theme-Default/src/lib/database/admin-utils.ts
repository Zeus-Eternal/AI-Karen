/**
 * Database Utility Functions for Admin Management System
 * 
 * This file contains utility functions for role-based queries, audit logging,
 * and other database operations specific to the admin management system.
 */

import { 
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
  RoleBasedQuery 
} from '@/types/admin';
import { DatabaseClient, getDatabaseClient } from './client';

/**
 * Error classes for specific admin database operations
 */
export class AdminDatabaseError extends Error {
  constructor(
    message: string,
    public operation: string,
    public originalError?: unknown
  ) {
    super(message);
    this.name = 'AdminDatabaseError';
  }
}

export class UserNotFoundError extends AdminDatabaseError {
  constructor(userId: string) {
    super(`User not found: ${userId}`, 'getUser');
    this.name = 'UserNotFoundError';
  }
}

export class PermissionDeniedError extends AdminDatabaseError {
  constructor(userId: string, permission: string) {
    super(`User ${userId} lacks permission: ${permission}`, 'checkPermission');
    this.name = 'PermissionDeniedError';
  }
}

/**
 * Role-based query utilities
 */
export class AdminDatabaseUtils {
  private readonly DEFAULT_PAGE_SIZE = 20;
  private readonly DEFAULT_AUDIT_LOG_SIZE = 50;

  constructor(private db: DatabaseClient) {}

  /**
   * Safe query execution with error handling
   */
  private async executeQuery<T>(
    operation: string,
    query: string,
    params: any[] = []
  ): Promise<T[]> {
    try {
      const result = await this.db.query(query, params);
      return result.rows as T[];
    } catch (error) {
      throw new AdminDatabaseError(
        `Database operation failed: ${operation}`,
        operation,
        error
      );
    }
  }

  /**
   * Get user with role information
   */
  async getUserWithRole(userId: string): Promise<User | null> {
    if (!userId || typeof userId !== 'string') {
      throw new AdminDatabaseError('Invalid user ID provided', 'getUserWithRole');
    }

    const query = `
      SELECT 
        user_id,
        email,
        full_name,
        role,
        roles,
        tenant_id,
        preferences,
        is_verified,
        is_active,
        created_at,
        updated_at,
        last_login_at,
        failed_login_attempts,
        locked_until,
        two_factor_enabled,
        two_factor_secret
      FROM auth_users 
      WHERE user_id = $1 AND is_active = true
    `;
    
    const result = await this.executeQuery<User>(`getUserWithRole-${userId}`, query, [userId]);
    return result[0] || null;
  }

  /**
   * Get users with role-based filtering
   */
  async getUsersWithRoleFilter(
    filter: UserListFilter = {},
    pagination: PaginationParams = { page: 1, limit: this.DEFAULT_PAGE_SIZE }
  ): Promise<PaginatedResponse<User>> {
    // Validate pagination parameters
    const page = Math.max(1, pagination.page || 1);
    const limit = Math.min(Math.max(1, pagination.limit || this.DEFAULT_PAGE_SIZE), 1000); // Cap at 1000 for safety
    
    let whereConditions: string[] = [];
    let queryParams: any[] = [];
    let paramIndex = 1;

    // Build WHERE conditions based on filter
    if (filter.role) {
      whereConditions.push(`role = $${paramIndex++}`);
      queryParams.push(filter.role);
    }

    if (filter.is_active !== undefined) {
      whereConditions.push(`is_active = $${paramIndex++}`);
      queryParams.push(filter.is_active);
    }

    if (filter.is_verified !== undefined) {
      whereConditions.push(`is_verified = $${paramIndex++}`);
      queryParams.push(filter.is_verified);
    }

    if (filter.search) {
      const searchTerm = `%${filter.search}%`;
      whereConditions.push(`(email ILIKE $${paramIndex} OR full_name ILIKE $${paramIndex})`);
      queryParams.push(searchTerm);
      paramIndex++;
    }

    if (filter.created_after) {
      whereConditions.push(`created_at >= $${paramIndex++}`);
      queryParams.push(filter.created_after);
    }

    if (filter.created_before) {
      whereConditions.push(`created_at <= $${paramIndex++}`);
      queryParams.push(filter.created_before);
    }

    if (filter.last_login_after) {
      whereConditions.push(`last_login_at >= $${paramIndex++}`);
      queryParams.push(filter.last_login_after);
    }

    if (filter.last_login_before) {
      whereConditions.push(`last_login_at <= $${paramIndex++}`);
      queryParams.push(filter.last_login_before);
    }

    const whereClause = whereConditions.length > 0 
      ? `WHERE ${whereConditions.join(' AND ')}`
      : '';

    try {
      // Count total records
      const countQuery = `SELECT COUNT(*) as total FROM auth_users ${whereClause}`;
      const countResult = await this.executeQuery<{ total: string }>('countUsers', countQuery, queryParams);
      const total = parseInt(countResult[0]?.total || '0');

      // Calculate pagination
      const offset = (page - 1) * limit;
      const totalPages = Math.ceil(total / limit);

      // Validate page bounds
      if (page > totalPages && totalPages > 0) {
        throw new AdminDatabaseError(`Page ${page} exceeds total pages ${totalPages}`, 'getUsersWithRoleFilter');
      }

      // Build ORDER BY clause safely
      const validSortColumns = ['created_at', 'updated_at', 'last_login_at', 'email', 'full_name'];
      const sortBy = validSortColumns.includes(pagination.sort_by || '') 
        ? pagination.sort_by 
        : 'created_at';
      
      const sortOrder = pagination.sort_order?.toLowerCase() === 'asc' ? 'ASC' : 'DESC';
      const orderClause = `ORDER BY ${sortBy} ${sortOrder}`;

      // Get paginated data
      const dataQuery = `
        SELECT 
          user_id,
          email,
          full_name,
          role,
          roles,
          tenant_id,
          preferences,
          is_verified,
          is_active,
          created_at,
          updated_at,
          last_login_at,
          failed_login_attempts,
          locked_until,
          two_factor_enabled
        FROM auth_users 
        ${whereClause}
        ${orderClause}
        LIMIT $${paramIndex++} OFFSET $${paramIndex++}
      `;

      const dataParams = [...queryParams, limit, offset];
      const dataResult = await this.executeQuery<User>('getUsersData', dataQuery, dataParams);

      return {
        data: dataResult,
        pagination: {
          page,
          limit,
          total,
          total_pages: totalPages,
          has_next: page < totalPages,
          has_prev: page > 1
        }
      };
    } catch (error) {
      if (error instanceof AdminDatabaseError) throw error;
      throw new AdminDatabaseError(
        'Failed to fetch users with filters',
        'getUsersWithRoleFilter',
        error
      );
    }
  }

  /**
   * Check if user has specific permission
   */
  async userHasPermission(userId: string, permissionName: string): Promise<boolean> {
    if (!userId || !permissionName) {
      return false;
    }

    try {
      const query = `SELECT user_has_permission($1, $2) as has_permission`;
      const result = await this.executeQuery<{ has_permission: boolean }>(
        `checkPermission-${userId}-${permissionName}`,
        query, 
        [userId, permissionName]
      );
      return result[0]?.has_permission || false;
    } catch (error) {
      // If the function doesn't exist, fall back to basic role check
      if (error instanceof AdminDatabaseError) {
        const user = await this.getUserWithRole(userId);
        return user?.role === 'super_admin';
      }
      throw error;
    }
  }

  /**
   * Get user permissions
   */
  async getUserPermissions(userId: string): Promise<Permission[]> {
    if (!userId) {
      return [];
    }

    try {
      const query = `SELECT * FROM get_user_permissions($1)`;
      return await this.executeQuery<Permission>('getUserPermissions', query, [userId]);
    } catch (error) {
      // Fallback if function doesn't exist
      if (error instanceof AdminDatabaseError) {
        const user = await this.getUserWithRole(userId);
        if (user?.role === 'super_admin') {
          return [{ name: 'all', description: 'All permissions' } as Permission];
        }
      }
      throw error;
    }
  }

  /**
   * Create audit log entry
   */
  async createAuditLog(entry: AuditLogEntry): Promise<string> {
    if (!entry.user_id || !entry.action || !entry.resource_type) {
      throw new AdminDatabaseError('Missing required audit log fields', 'createAuditLog');
    }

    try {
      const query = `SELECT log_audit_event($1, $2, $3, $4, $5, $6, $7) as audit_id`;
      const result = await this.executeQuery<{ audit_id: string }>('createAuditLog', query, [
        entry.user_id,
        entry.action,
        entry.resource_type,
        entry.resource_id || null,
        JSON.stringify(entry.details || {}),
        entry.ip_address || null,
        entry.user_agent || null
      ]);
      return result[0]?.audit_id || '';
    } catch (error) {
      // Fallback to direct insert if function doesn't exist
      if (error instanceof AdminDatabaseError) {
        const insertQuery = `
          INSERT INTO audit_logs (
            user_id, action, resource_type, resource_id, details, ip_address, user_agent, timestamp
          ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
          RETURNING id
        `;
        const result = await this.executeQuery<{ id: string }>('createAuditLogFallback', insertQuery, [
          entry.user_id,
          entry.action,
          entry.resource_type,
          entry.resource_id || null,
          JSON.stringify(entry.details || {}),
          entry.ip_address || null,
          entry.user_agent || null
        ]);
        return result[0]?.id || '';
      }
      throw error;
    }
  }

  /**
   * Get audit logs with filtering
   */
  async getAuditLogs(
    filter: AuditLogFilter = {},
    pagination: PaginationParams = { page: 1, limit: this.DEFAULT_AUDIT_LOG_SIZE }
  ): Promise<PaginatedResponse<AuditLog>> {
    const page = Math.max(1, pagination.page || 1);
    const limit = Math.min(Math.max(1, pagination.limit || this.DEFAULT_AUDIT_LOG_SIZE), 1000);
    
    let whereConditions: string[] = [];
    let queryParams: any[] = [];
    let paramIndex = 1;

    // Build WHERE conditions
    if (filter.user_id) {
      whereConditions.push(`al.user_id = $${paramIndex++}`);
      queryParams.push(filter.user_id);
    }

    if (filter.action) {
      whereConditions.push(`al.action = $${paramIndex++}`);
      queryParams.push(filter.action);
    }

    if (filter.resource_type) {
      whereConditions.push(`al.resource_type = $${paramIndex++}`);
      queryParams.push(filter.resource_type);
    }

    if (filter.start_date) {
      whereConditions.push(`al.timestamp >= $${paramIndex++}`);
      queryParams.push(filter.start_date);
    }

    if (filter.end_date) {
      whereConditions.push(`al.timestamp <= $${paramIndex++}`);
      queryParams.push(filter.end_date);
    }

    if (filter.ip_address) {
      whereConditions.push(`al.ip_address = $${paramIndex++}`);
      queryParams.push(filter.ip_address);
    }

    const whereClause = whereConditions.length > 0 
      ? `WHERE ${whereConditions.join(' AND ')}`
      : '';

    try {
      // Count total records
      const countQuery = `SELECT COUNT(*) as total FROM audit_logs al ${whereClause}`;
      const countResult = await this.executeQuery<{ total: string }>('countAuditLogs', countQuery, queryParams);
      const total = parseInt(countResult[0]?.total || '0');

      // Calculate pagination
      const offset = (page - 1) * limit;
      const totalPages = Math.ceil(total / limit);

      // Get paginated data with user information
      const dataQuery = `
        SELECT 
          al.id,
          al.user_id,
          al.action,
          al.resource_type,
          al.resource_id,
          al.details,
          al.ip_address,
          al.user_agent,
          al.timestamp,
          u.email as user_email,
          u.full_name as user_full_name
        FROM audit_logs al
        LEFT JOIN auth_users u ON al.user_id = u.user_id
        ${whereClause}
        ORDER BY al.timestamp DESC
        LIMIT $${paramIndex++} OFFSET $${paramIndex++}
      `;

      const dataParams = [...queryParams, limit, offset];
      const dataResult = await this.executeQuery<any>('getAuditLogsData', dataQuery, dataParams);

      // Transform results to include user information
      const data: AuditLog[] = dataResult.map((row: any) => ({
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
      }));

      return {
        data,
        pagination: {
          page,
          limit,
          total,
          total_pages: totalPages,
          has_next: page < totalPages,
          has_prev: page > 1
        }
      };
    } catch (error) {
      throw new AdminDatabaseError(
        'Failed to fetch audit logs',
        'getAuditLogs',
        error
      );
    }
  }

  /**
   * Get system configuration values
   */
  async getSystemConfig(category?: string): Promise<SystemConfig[]> {
    let query = `
      SELECT 
        sc.id,
        sc.key,
        sc.value,
        sc.value_type,
        sc.category,
        sc.description,
        sc.updated_by,
        sc.updated_at,
        sc.created_at,
        u.email as updated_by_email,
        u.full_name as updated_by_name
      FROM system_config sc
      LEFT JOIN auth_users u ON sc.updated_by = u.user_id
    `;
    
    let queryParams: any[] = [];
    
    if (category) {
      query += ` WHERE sc.category = $1`;
      queryParams.push(category);
    }
    
    query += ` ORDER BY sc.category, sc.key`;
    
    try {
      const result = await this.executeQuery<any>('getSystemConfig', query, queryParams);
      
      return result.map((row: any) => ({
        id: row.id,
        key: row.key,
        value: this.parseConfigValue(row.value, row.value_type),
        value_type: row.value_type,
        category: row.category,
        description: row.description,
        updated_by: row.updated_by,
        updated_at: row.updated_at,
        created_at: row.created_at,
        updated_by_user: row.updated_by_email ? {
          user_id: row.updated_by,
          email: row.updated_by_email,
          full_name: row.updated_by_name
        } : undefined
      }));
    } catch (error) {
      throw new AdminDatabaseError(
        'Failed to fetch system configuration',
        'getSystemConfig',
        error
      );
    }
  }

  /**
   * Update system configuration value
   */
  async updateSystemConfig(
    key: string, 
    value: string | number | boolean, 
    updatedBy: string,
    description?: string
  ): Promise<void> {
    if (!key || !updatedBy) {
      throw new AdminDatabaseError('Missing required parameters for config update', 'updateSystemConfig');
    }

    const valueType = typeof value;
    const valueStr = valueType === 'object' ? JSON.stringify(value) : String(value);
    
    const query = description 
      ? `UPDATE system_config SET value = $1, value_type = $2, updated_by = $3, updated_at = NOW(), description = $5 WHERE key = $4`
      : `UPDATE system_config SET value = $1, value_type = $2, updated_by = $3, updated_at = NOW() WHERE key = $4`;
    
    const params = description 
      ? [valueStr, valueType, updatedBy, key, description]
      : [valueStr, valueType, updatedBy, key];
    
    try {
      await this.db.query(query, params);
    } catch (error) {
      throw new AdminDatabaseError(
        `Failed to update system config for key: ${key}`,
        'updateSystemConfig',
        error
      );
    }
  }

  /**
   * Create new user with role
   */
  async createUserWithRole(
    userData: {
      email: string;
      full_name?: string;
      password_hash?: string;
      role: 'admin' | 'user';
      tenant_id?: string;
      created_by: string;
    }
  ): Promise<string> {
    if (!userData.email || !userData.role || !userData.created_by) {
      throw new AdminDatabaseError('Missing required user data', 'createUserWithRole');
    }

    try {
      const query = `
        INSERT INTO auth_users (
          email, full_name, role, tenant_id, is_verified, is_active, created_at, updated_at
        ) VALUES (
          $1, $2, $3, $4, $5, $6, NOW(), NOW()
        ) RETURNING user_id
      `;
      
      const result = await this.executeQuery<{ user_id: string }>('createUserWithRole', query, [
        userData.email,
        userData.full_name || null,
        userData.role,
        userData.tenant_id || 'default',
        false, // Email verification required
        true   // Active by default
      ]);
      
      const userId = result[0]?.user_id;
      
      if (!userId) {
        throw new AdminDatabaseError('Failed to create user - no user ID returned', 'createUserWithRole');
      }
      
      // Create password hash if provided
      if (userData.password_hash) {
        await this.db.query(
          `INSERT INTO auth_password_hashes (user_id, password_hash, created_at, updated_at) 
           VALUES ($1, $2, NOW(), NOW())`,
          [userId, userData.password_hash]
        );
      }
      
      // Log the user creation
      await this.createAuditLog({
        user_id: userData.created_by,
        action: 'user.create',
        resource_type: 'user',
        resource_id: userId,
        details: {
          email: userData.email,
          role: userData.role,
          full_name: userData.full_name
        }
      });

      return userId;
    } catch (error) {
      throw new AdminDatabaseError(
        'Failed to create user with role',
        'createUserWithRole',
        error
      );
    }
  }

  /**
   * Update user role
   */
  async updateUserRole(
    userId: string, 
    newRole: 'super_admin' | 'admin' | 'user',
    updatedBy: string
  ): Promise<void> {
    if (!userId || !newRole || !updatedBy) {
      throw new AdminDatabaseError('Missing required parameters for role update', 'updateUserRole');
    }

    try {
      // Get current user data for audit log
      const currentUser = await this.getUserWithRole(userId);
      if (!currentUser) {
        throw new UserNotFoundError(userId);
      }
      
      const query = `UPDATE auth_users SET role = $1, updated_at = NOW() WHERE user_id = $2`;
      await this.db.query(query, [newRole, userId]);
      
      // Log the role change
      await this.createAuditLog({
        user_id: updatedBy,
        action: 'user.role_change',
        resource_type: 'user',
        resource_id: userId,
        details: {
          email: currentUser.email,
          old_role: currentUser.role,
          new_role: newRole
        }
      });
    } catch (error) {
      if (error instanceof UserNotFoundError) throw error;
      throw new AdminDatabaseError(
        `Failed to update user role for ${userId}`,
        'updateUserRole',
        error
      );
    }
  }

  /**
   * Update user fields
   */
  async updateUser(
    userId: string,
    updates: {
      last_login_at?: Date;
      failed_login_attempts?: number;
      locked_until?: Date | null;
      two_factor_enabled?: boolean;
      two_factor_secret?: string;
      is_active?: boolean;
      preferences?: Record<string, any>;
    }
  ): Promise<void> {
    if (!userId) {
      throw new AdminDatabaseError('User ID is required', 'updateUser');
    }

    const updateFields: string[] = [];
    const queryParams: any[] = [];
    let paramIndex = 1;

    if (updates.last_login_at !== undefined) {
      updateFields.push(`last_login_at = $${paramIndex++}`);
      queryParams.push(updates.last_login_at);
    }

    if (updates.failed_login_attempts !== undefined) {
      updateFields.push(`failed_login_attempts = $${paramIndex++}`);
      queryParams.push(updates.failed_login_attempts);
    }

    if (updates.locked_until !== undefined) {
      updateFields.push(`locked_until = $${paramIndex++}`);
      queryParams.push(updates.locked_until);
    }

    if (updates.two_factor_enabled !== undefined) {
      updateFields.push(`two_factor_enabled = $${paramIndex++}`);
      queryParams.push(updates.two_factor_enabled);
    }

    if (updates.two_factor_secret !== undefined) {
      updateFields.push(`two_factor_secret = $${paramIndex++}`);
      queryParams.push(updates.two_factor_secret);
    }

    if (updates.is_active !== undefined) {
      updateFields.push(`is_active = $${paramIndex++}`);
      queryParams.push(updates.is_active);
    }

    if (updates.preferences !== undefined) {
      updateFields.push(`preferences = $${paramIndex++}`);
      queryParams.push(JSON.stringify(updates.preferences));
    }

    if (updateFields.length === 0) {
      return; // No updates to perform
    }

    updateFields.push(`updated_at = NOW()`);
    queryParams.push(userId);

    const query = `UPDATE auth_users SET ${updateFields.join(', ')} WHERE user_id = $${paramIndex}`;

    try {
      await this.db.query(query, queryParams);
    } catch (error) {
      throw new AdminDatabaseError(
        `Failed to update user ${userId}`,
        'updateUser',
        error
      );
    }
  }

  /**
   * Get role-based query information for a user
   */
  async getRoleBasedQuery(userId: string): Promise<RoleBasedQuery | null> {
    if (!userId) {
      return null;
    }

    try {
      const user = await this.getUserWithRole(userId);
      if (!user) return null;
      
      const permissions = await this.getUserPermissions(userId);
      
      return {
        user_id: userId,
        role: user.role,
        permissions: permissions.map(p => p.name)
      };
    } catch (error) {
      throw new AdminDatabaseError(
        `Failed to get role-based query for user ${userId}`,
        'getRoleBasedQuery',
        error
      );
    }
  }

  /**
   * Check if user can perform action on resource
   */
  async canUserPerformAction(
    userId: string,
    action: string,
    resourceType: string,
    resourceId?: string
  ): Promise<boolean> {
    if (!userId || !action || !resourceType) {
      return false;
    }

    try {
      const roleQuery = await this.getRoleBasedQuery(userId);
      if (!roleQuery) return false;
      
      // Super admins can do everything
      if (roleQuery.role === 'super_admin') return true;
      
      // Check specific permissions
      const requiredPermission = `${resourceType}.${action}`;
      return roleQuery.permissions.includes(requiredPermission);
    } catch (error) {
      // If we can't determine permissions, deny access
      return false;
    }
  }

  /**
   * Parse configuration value based on type
   */
  private parseConfigValue(value: string, type: string): string | number | boolean {
    if (value === null || value === undefined) {
      return value;
    }

    switch (type) {
      case 'number':
        const num = parseFloat(value);
        return isNaN(num) ? value : num;
      case 'boolean':
        return value.toLowerCase() === 'true' || value === '1';
      case 'json':
        try {
          return JSON.parse(value);
        } catch {
          return value;
        }
      default:
        return value;
    }
  }

  /**
   * Get users by role
   */
  async getUsersByRole(role: 'super_admin' | 'admin' | 'user'): Promise<User[]> {
    if (!role) {
      return [];
    }

    const query = `
      SELECT 
        user_id,
        email,
        full_name,
        role,
        roles,
        tenant_id,
        preferences,
        is_verified,
        is_active,
        created_at,
        updated_at,
        last_login_at,
        failed_login_attempts,
        locked_until,
        two_factor_enabled
      FROM auth_users 
      WHERE role = $1 AND is_active = true
    `;
    
    try {
      return await this.executeQuery<User>('getUsersByRole', query, [role]);
    } catch (error) {
      throw new AdminDatabaseError(
        `Failed to get users by role: ${role}`,
        'getUsersByRole',
        error
      );
    }
  }

  /**
   * Check if this is the last super admin
   */
  async isLastSuperAdmin(userId: string): Promise<boolean> {
    if (!userId) {
      return false;
    }

    try {
      const query = `
        SELECT COUNT(*) as count
        FROM auth_users 
        WHERE role = 'super_admin' AND is_active = true AND user_id != $1
      `;
      
      const result = await this.executeQuery<{ count: string }>('isLastSuperAdmin', query, [userId]);
      return parseInt(result[0]?.count || '0') === 0;
    } catch (error) {
      throw new AdminDatabaseError(
        `Failed to check if user is last super admin: ${userId}`,
        'isLastSuperAdmin',
        error
      );
    }
  }

  /**
   * Bulk update user status
   */
  async bulkUpdateUserStatus(
    userIds: string[],
    isActive: boolean,
    updatedBy: string
  ): Promise<void> {
    if (!userIds || userIds.length === 0 || !updatedBy) {
      return;
    }

    // Safety limit for bulk operations
    if (userIds.length > 1000) {
      throw new AdminDatabaseError('Too many users for bulk operation (max 1000)', 'bulkUpdateUserStatus');
    }

    try {
      const placeholders = userIds.map((_, index) => `$${index + 1}`).join(',');
      const query = `
        UPDATE auth_users 
        SET is_active = $${userIds.length + 1}, updated_at = NOW()
        WHERE user_id IN (${placeholders})
      `;
      
      await this.db.query(query, [...userIds, isActive]);
      
      // Log bulk operation
      await this.createAuditLog({
        user_id: updatedBy,
        action: isActive ? 'user.bulk_activate' : 'user.bulk_deactivate',
        resource_type: 'user',
        details: {
          user_ids: userIds,
          count: userIds.length
        }
      });
    } catch (error) {
      throw new AdminDatabaseError(
        `Failed to bulk update user status for ${userIds.length} users`,
        'bulkUpdateUserStatus',
        error
      );
    }
  }

  // Additional utility methods with proper error handling...

  /**
   * Get user by email
   */
  async getUserByEmail(email: string): Promise<User | null> {
    if (!email) {
      return null;
    }

    const query = `
      SELECT 
        user_id,
        email,
        full_name,
        role,
        roles,
        tenant_id,
        preferences,
        is_verified,
        is_active,
        created_at,
        updated_at,
        last_login_at,
        failed_login_attempts,
        locked_until,
        two_factor_enabled
      FROM auth_users 
      WHERE email = $1
    `;
    
    try {
      const result = await this.executeQuery<User>('getUserByEmail', query, [email]);
      return result[0] || null;
    } catch (error) {
      throw new AdminDatabaseError(
        `Failed to get user by email: ${email}`,
        'getUserByEmail',
        error
      );
    }
  }

  /**
   * Get total user count
   */
  async getUserCount(): Promise<number> {
    try {
      const query = `SELECT COUNT(*) as count FROM auth_users WHERE is_active = true`;
      const result = await this.executeQuery<{ count: string }>('getUserCount', query);
      return parseInt(result[0]?.count || '0');
    } catch (error) {
      throw new AdminDatabaseError('Failed to get user count', 'getUserCount', error);
    }
  }

  /**
   * Get admin count
   */
  async getAdminCount(): Promise<number> {
    try {
      const query = `
        SELECT COUNT(*) as count 
        FROM auth_users 
        WHERE role IN ('admin', 'super_admin') AND is_active = true
      `;
      const result = await this.executeQuery<{ count: string }>('getAdminCount', query);
      return parseInt(result[0]?.count || '0');
    } catch (error) {
      throw new AdminDatabaseError('Failed to get admin count', 'getAdminCount', error);
    }
  }

  /**
   * Get active user count (logged in within last 24 hours)
   */
  async getActiveUserCount(): Promise<number> {
    try {
      const query = `
        SELECT COUNT(*) as count 
        FROM auth_users 
        WHERE last_login_at >= NOW() - INTERVAL '24 hours' AND is_active = true
      `;
      const result = await this.executeQuery<{ count: string }>('getActiveUserCount', query);
      return parseInt(result[0]?.count || '0');
    } catch (error) {
      throw new AdminDatabaseError('Failed to get active user count', 'getActiveUserCount', error);
    }
  }
}

/**
 * Convenience function to get AdminDatabaseUtils instance
 */
export function getAdminDatabaseUtils(client?: DatabaseClient): AdminDatabaseUtils {
  const dbClient = client || getDatabaseClient();
  return new AdminDatabaseUtils(dbClient);
}

/**
 * Convenience function to get AdminDatabaseUtils instance (alias)
 */
export function getAdminUtils(client?: DatabaseClient): AdminDatabaseUtils {
  return getAdminDatabaseUtils(client);
}