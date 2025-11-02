/**
 * Database Utility Functions for Admin Management System
 * 
 * This file contains utility functions for role-based queries, audit logging,
 * and other database operations specific to the admin management system.
 */

import {  User, AuditLog, SystemConfig, Permission, RolePermission, UserListFilter, AuditLogFilter, PaginationParams, PaginatedResponse, AuditLogEntry, RoleBasedQuery } from '@/types/admin';

import { DatabaseClient, getDatabaseClient } from './client';

/**
 * Role-based query utilities
 */
export class AdminDatabaseUtils {
  constructor(private db: DatabaseClient) {}

  /**
   * Get user with role information
   */
  async getUserWithRole(userId: string): Promise<User | null> {
    const query = `
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
      WHERE user_id = $1 AND is_active = true
    `;
    
    const result = await this.db.query(query, [userId]);
    return result.rows[0] || null;
  }

  /**
   * Get users with role-based filtering
   */
  async getUsersWithRoleFilter(
    filter: UserListFilter = {},
    pagination: PaginationParams = { page: 1, limit: 20 }
  ): Promise<PaginatedResponse<User>> {
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
      whereConditions.push(`(email ILIKE $${paramIndex} OR full_name ILIKE $${paramIndex})`);
      queryParams.push(`%${filter.search}%`);
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

    // Count total records
    const countQuery = `
      SELECT COUNT(*) as total
      ${whereClause}
    `;
    const countResult = await this.db.query(countQuery, queryParams);
    const total = parseInt(countResult.rows[0].total);

    // Calculate pagination
    const offset = (pagination.page - 1) * pagination.limit;
    const totalPages = Math.ceil(total / pagination.limit);

    // Build ORDER BY clause
    const sortBy = pagination.sort_by || 'created_at';
    const sortOrder = pagination.sort_order || 'desc';
    const orderClause = `ORDER BY ${sortBy} ${sortOrder.toUpperCase()}`;

    // Get paginated data
    const dataQuery = `
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
      ${whereClause}
      ${orderClause}
      LIMIT $${paramIndex++} OFFSET $${paramIndex++}
    `;

    queryParams.push(pagination.limit, offset);
    const dataResult = await this.db.query(dataQuery, queryParams);

    return {
      data: dataResult.rows,
      pagination: {
        page: pagination.page,
        limit: pagination.limit,
        total,
        total_pages: totalPages,
        has_next: pagination.page < totalPages,
        has_prev: pagination.page > 1
      }
    };
  }

  /**
   * Check if user has specific permission
   */
  async userHasPermission(userId: string, permissionName: string): Promise<boolean> {
    const query = `SELECT user_has_permission($1, $2) as has_permission`;
    const result = await this.db.query(query, [userId, permissionName]);
    return result.rows[0]?.has_permission || false;
  }

  /**
   * Get user permissions
   */
  async getUserPermissions(userId: string): Promise<Permission[]> {
    const query = `
      FROM get_user_permissions($1)
    `;
    const result = await this.db.query(query, [userId]);
    return result.rows;
  }

  /**
   * Create audit log entry
   */
  async createAuditLog(entry: AuditLogEntry): Promise<string> {
    const query = `
      SELECT log_audit_event($1, $2, $3, $4, $5, $6, $7) as audit_id
    `;
    const result = await this.db.query(query, [
      entry.user_id,
      entry.action,
      entry.resource_type,
      entry.resource_id || null,
      JSON.stringify(entry.details || {}),
      entry.ip_address || null,
      entry.user_agent || null
    ]);
    return result.rows[0].audit_id;
  }

  /**
   * Get audit logs with filtering
   */
  async getAuditLogs(
    filter: AuditLogFilter = {},
    pagination: PaginationParams = { page: 1, limit: 50 }
  ): Promise<PaginatedResponse<AuditLog>> {
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

    // Count total records
    const countQuery = `
      SELECT COUNT(*) as total
      ${whereClause}
    `;
    const countResult = await this.db.query(countQuery, queryParams);
    const total = parseInt(countResult.rows[0].total);

    // Calculate pagination
    const offset = (pagination.page - 1) * pagination.limit;
    const totalPages = Math.ceil(total / pagination.limit);

    // Get paginated data with user information
    const dataQuery = `
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
      LEFT JOIN auth_users u ON al.user_id = u.user_id
      ${whereClause}
      ORDER BY al.timestamp DESC
      LIMIT $${paramIndex++} OFFSET $${paramIndex++}
    `;

    queryParams.push(pagination.limit, offset);
    const dataResult = await this.db.query(dataQuery, queryParams);

    // Transform results to include user information
    const data = dataResult.rows.map((row: any) => ({
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
        page: pagination.page,
        limit: pagination.limit,
        total,
        total_pages: totalPages,
        has_next: pagination.page < totalPages,
        has_prev: pagination.page > 1
      }
    };
  }

  /**
   * Get system configuration values
   */
  async getSystemConfig(category?: string): Promise<SystemConfig[]> {
    let query = `
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
      LEFT JOIN auth_users u ON sc.updated_by = u.user_id
    `;
    
    let queryParams: any[] = [];
    
    if (category) {
      query += ` WHERE sc.category = $1`;
      queryParams.push(category);
    }
    
    query += ` ORDER BY sc.category, sc.key`;
    
    const result = await this.db.query(query, queryParams);
    
    return result.rows.map((row: any) => ({
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
    const valueType = typeof value;
    const valueStr = valueType === 'object' ? JSON.stringify(value) : String(value);
    
    const query = `
      SET value = $1, value_type = $2, updated_by = $3, updated_at = NOW()
      ${description ? ', description = $5' : ''}
      WHERE key = $4
    `;
    
    const params = description 
      ? [valueStr, valueType, updatedBy, key, description]
      : [valueStr, valueType, updatedBy, key];
    
    await this.db.query(query, params);
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
    const query = `
      INSERT INTO auth_users (
        email, full_name, role, tenant_id, is_verified, is_active, created_at, updated_at
      ) VALUES (
        $1, $2, $3, $4, $5, $6, NOW(), NOW()
      ) RETURNING user_id
    `;
    
    const result = await this.db.query(query, [
      userData.email,
      userData.full_name || null,
      userData.role,
      userData.tenant_id || 'default',
      false, // Email verification required
      true   // Active by default
    ]);
    
    const userId = result.rows[0].user_id;
    
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

    return userId;
  }

  /**
   * Update user role
   */
  async updateUserRole(
    userId: string, 
    newRole: 'super_admin' | 'admin' | 'user',
    updatedBy: string
  ): Promise<void> {
    // Get current user data for audit log
    const currentUser = await this.getUserWithRole(userId);
    if (!currentUser) {
      throw new Error('User not found');
    }
    
    const query = `
      SET role = $1, updated_at = NOW()
      WHERE user_id = $2
    `;
    
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

    const query = `
      SET ${updateFields.join(', ')}
      WHERE user_id = $${paramIndex}
    `;

    await this.db.query(query, queryParams);
  }

  /**
   * Get role-based query information for a user
   */
  async getRoleBasedQuery(userId: string): Promise<RoleBasedQuery | null> {
    const user = await this.getUserWithRole(userId);
    if (!user) return null;
    
    const permissions = await this.getUserPermissions(userId);
    
    return {
      user_id: userId,
      role: user.role,
      permissions: permissions.map(p => p.name)
    };
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
    const roleQuery = await this.getRoleBasedQuery(userId);
    if (!roleQuery) return false;
    
    // Super admins can do everything
    if (roleQuery.role === 'super_admin') return true;
    
    // Check specific permissions
    const requiredPermission = `${resourceType}.${action}`;
    return roleQuery.permissions.includes(requiredPermission);
  }

  /**
   * Parse configuration value based on type
   */
  private parseConfigValue(value: string, type: string): string | number | boolean {
    switch (type) {
      case 'number':
        return parseFloat(value);
      case 'boolean':
        return value.toLowerCase() === 'true';
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
    const query = `
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
      WHERE role = $1 AND is_active = true
    `;
    
    const result = await this.db.query(query, [role]);
    return result.rows;
  }

  /**
   * Check if this is the last super admin
   */
  async isLastSuperAdmin(userId: string): Promise<boolean> {
    const query = `
      SELECT COUNT(*) as count
      WHERE role = 'super_admin' AND is_active = true AND user_id != $1
    `;
    
    const result = await this.db.query(query, [userId]);
    return parseInt(result.rows[0].count) === 0;
  }

  /**
   * Bulk update user status
   */
  async bulkUpdateUserStatus(
    userIds: string[],
    isActive: boolean,
    updatedBy: string
  ): Promise<void> {
    if (userIds.length === 0) return;
    
    const placeholders = userIds.map((_, index) => `$${index + 1}`).join(',');
    const query = `
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

  }

  // Dashboard Statistics Methods

  /**
   * Get total user count
   */
  async getUserCount(): Promise<number> {
    const query = `SELECT COUNT(*) as count FROM auth_users WHERE is_active = true`;
    const result = await this.db.query(query);
    return parseInt(result.rows[0].count);
  }

  /**
   * Get admin count
   */
  async getAdminCount(): Promise<number> {
    const query = `
      SELECT COUNT(*) as count 
      WHERE role IN ('admin', 'super_admin') AND is_active = true
    `;
    const result = await this.db.query(query);
    return parseInt(result.rows[0].count);
  }

  /**
   * Get active user count (logged in within last 24 hours)
   */
  async getActiveUserCount(): Promise<number> {
    const query = `
      SELECT COUNT(*) as count 
      WHERE last_login_at >= NOW() - INTERVAL '24 hours' AND is_active = true
    `;
    const result = await this.db.query(query);
    return parseInt(result.rows[0].count);
  }

  /**
   * Get security alerts count
   */
  async getSecurityAlertsCount(): Promise<number> {
    const query = `
      SELECT COUNT(*) as count 
      WHERE resolved = false AND created_at >= NOW() - INTERVAL '7 days'
    `;
    const result = await this.db.query(query);
    return parseInt(result.rows[0].count);
  }

  /**
   * Get user by email
   */
  async getUserByEmail(email: string): Promise<User | null> {
    const query = `
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
      WHERE email = $1
    `;
    
    const result = await this.db.query(query, [email]);
    return result.rows[0] || null;
  }

  /**
   * Create admin invitation
   */
  async createAdminInvitation(invitation: {
    email: string;
    token: string;
    invitedBy: string;
    expiresAt: Date;
    message?: string;
  }): Promise<{ id: string }> {
    const query = `
      INSERT INTO admin_invitations (
        email, token, invited_by, expires_at, message, created_at
      ) VALUES (
        $1, $2, $3, $4, $5, NOW()
      ) RETURNING id
    `;
    
    const result = await this.db.query(query, [
      invitation.email,
      invitation.token,
      invitation.invitedBy,
      invitation.expiresAt,
      invitation.message || null
    ]);
    
    return { id: result.rows[0].id };
  }

  // Security Settings Methods

  /**
   * Get security settings
   */
  async getSecuritySettings(): Promise<any> {
    const query = `
      WHERE category = 'security'
    `;
    
    const result = await this.db.query(query);
    const settings: any = {};
    
    result.rows.forEach((row: any) => {
      const value = this.parseConfigValue(row.value, row.value_type);
      const keys = row.key.split('.');
      let current = settings;
      
      for (let i = 0; i < keys.length - 1; i++) {
        if (!current[keys[i]]) current[keys[i]] = {};
        current = current[keys[i]];
      }
      
      current[keys[keys.length - 1]] = value;

    return settings;
  }

  /**
   * Update security settings
   */
  async updateSecuritySettings(settings: any): Promise<void> {
    const flattenSettings = (obj: any, prefix = ''): Array<{key: string, value: any}> => {
      const result: Array<{key: string, value: any}> = [];
      
      for (const [key, value] of Object.entries(obj)) {
        const fullKey = prefix ? `${prefix}.${key}` : key;
        
        if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
          result.push(...flattenSettings(value, fullKey));
        } else {
          result.push({ key: fullKey, value });
        }
      }
      
      return result;
    };
    
    const flatSettings = flattenSettings(settings);
    
    for (const setting of flatSettings) {
      const valueType = typeof setting.value;
      const valueStr = Array.isArray(setting.value) || typeof setting.value === 'object' 
        ? JSON.stringify(setting.value) 
        : String(setting.value);
      
      await this.db.query(`
        INSERT INTO system_config (key, value, value_type, category, created_at, updated_at)
        VALUES ($1, $2, $3, 'security', NOW(), NOW())
        ON CONFLICT (key) 
        DO UPDATE SET value = $2, value_type = $3, updated_at = NOW()
      `, [setting.key, valueStr, valueType]);
    }
  }

  /**
   * Get security alerts
   */
  async getSecurityAlerts(options: {
    limit?: number;
    offset?: number;
    severity?: string;
    resolved?: boolean;
    startDate?: Date;
    endDate?: Date;
  } = {}): Promise<any[]> {
    let whereConditions: string[] = [];
    let queryParams: any[] = [];
    let paramIndex = 1;

    if (options.severity) {
      whereConditions.push(`severity = $${paramIndex++}`);
      queryParams.push(options.severity);
    }

    if (options.resolved !== undefined) {
      whereConditions.push(`resolved = $${paramIndex++}`);
      queryParams.push(options.resolved);
    }

    if (options.startDate) {
      whereConditions.push(`created_at >= $${paramIndex++}`);
      queryParams.push(options.startDate);
    }

    if (options.endDate) {
      whereConditions.push(`created_at <= $${paramIndex++}`);
      queryParams.push(options.endDate);
    }

    const whereClause = whereConditions.length > 0 
      ? `WHERE ${whereConditions.join(' AND ')}`
      : '';

    const query = `
        id, type, severity, message, timestamp, ip_address, user_id, resolved, created_at
      ${whereClause}
      LIMIT $${paramIndex++} OFFSET $${paramIndex++}
    `;

    queryParams.push(options.limit || 50, options.offset || 0);
    const result = await this.db.query(query, queryParams);
    return result.rows;
  }

  /**
   * Get security alert by ID
   */
  async getSecurityAlert(alertId: string): Promise<any | null> {
    const query = `
      WHERE id = $1
    `;
    
    const result = await this.db.query(query, [alertId]);
    return result.rows[0] || null;
  }

  /**
   * Resolve security alert
   */
  async resolveSecurityAlert(alertId: string, resolvedBy: string): Promise<void> {
    const query = `
      SET resolved = true, resolved_by = $2, resolved_at = NOW()
      WHERE id = $1
    `;
    
    await this.db.query(query, [alertId, resolvedBy]);
  }

  /**
   * Get blocked IPs
   */
  async getBlockedIPs(options: {
    limit?: number;
    offset?: number;
  } = {}): Promise<any[]> {
    const query = `
        id, ip_address, reason, blocked_at, expires_at, failed_attempts, created_at
      WHERE (expires_at IS NULL OR expires_at > NOW())
      LIMIT $1 OFFSET $2
    `;
    
    const result = await this.db.query(query, [
      options.limit || 50, 
      options.offset || 0
    ]);
    return result.rows;
  }

  /**
   * Get blocked IP by ID
   */
  async getBlockedIP(blockedIpId: string): Promise<any | null> {
    const query = `
      WHERE id = $1
    `;
    
    const result = await this.db.query(query, [blockedIpId]);
    return result.rows[0] || null;
  }

  /**
   * Unblock IP address
   */
  async unblockIP(blockedIpId: string): Promise<void> {
    const query = `DELETE FROM blocked_ips WHERE id = $1`;
    await this.db.query(query, [blockedIpId]);
  }

  /**
   * Get failed login attempts
   */
  async getFailedLoginAttempts(options: {
    startDate?: Date;
    endDate?: Date;
  } = {}): Promise<any[]> {
    let whereConditions: string[] = [];
    let queryParams: any[] = [];
    let paramIndex = 1;

    if (options.startDate) {
      whereConditions.push(`timestamp >= $${paramIndex++}`);
      queryParams.push(options.startDate);
    }

    if (options.endDate) {
      whereConditions.push(`timestamp <= $${paramIndex++}`);
      queryParams.push(options.endDate);
    }

    const whereClause = whereConditions.length > 0 
      ? `WHERE ${whereConditions.join(' AND ')}`
      : '';

    const query = `
      ${whereClause}
    `;
    
    const result = await this.db.query(query, queryParams);
    return result.rows;
  }

  /**
   * Get admin actions
   */
  async getAdminActions(options: {
    startDate?: Date;
    endDate?: Date;
  } = {}): Promise<any[]> {
    let whereConditions: string[] = ['al.action LIKE \'admin.%\''];
    let queryParams: any[] = [];
    let paramIndex = 1;

    if (options.startDate) {
      whereConditions.push(`al.timestamp >= $${paramIndex++}`);
      queryParams.push(options.startDate);
    }

    if (options.endDate) {
      whereConditions.push(`al.timestamp <= $${paramIndex++}`);
      queryParams.push(options.endDate);
    }

    const whereClause = `WHERE ${whereConditions.join(' AND ')}`;

    const query = `
        al.id, al.user_id, al.action, al.resource_type, al.resource_id, 
        al.details, al.timestamp, u.email as user_email
      LEFT JOIN auth_users u ON al.user_id = u.user_id
      ${whereClause}
      ORDER BY al.timestamp DESC
    `;
    
    const result = await this.db.query(query, queryParams);
    return result.rows;
  }

  /**
   * Get user statistics
   */
  async getUserStatistics(options: {
    startDate?: Date;
    endDate?: Date;
  } = {}): Promise<any> {
    const totalUsersQuery = `SELECT COUNT(*) as count FROM auth_users WHERE is_active = true`;
    const activeUsersQuery = `
      SELECT COUNT(*) as count 
      WHERE last_login_at >= NOW() - INTERVAL '24 hours' AND is_active = true
    `;
    
    let newUsersQuery = `SELECT COUNT(*) as count FROM auth_users WHERE is_active = true`;
    let queryParams: any[] = [];
    
    if (options.startDate && options.endDate) {
      newUsersQuery += ` AND created_at BETWEEN $1 AND $2`;
      queryParams = [options.startDate, options.endDate];
    }
    
    const adminUsersQuery = `
      SELECT COUNT(*) as count 
      WHERE role IN ('admin', 'super_admin') AND is_active = true
    `;

    const [totalResult, activeResult, newResult, adminResult] = await Promise.all([
      this.db.query(totalUsersQuery),
      this.db.query(activeUsersQuery),
      this.db.query(newUsersQuery, queryParams),
      this.db.query(adminUsersQuery)
    ]);

    return {
      totalUsers: parseInt(totalResult.rows[0].count),
      activeUsers: parseInt(activeResult.rows[0].count),
      newUsers: parseInt(newResult.rows[0].count),
      adminUsers: parseInt(adminResult.rows[0].count)
    };
  }

  /**
   * Get system health metrics
   */
  async getSystemHealthMetrics(): Promise<any> {
    // This would typically check various system components
    // For now, return a basic health status
    return {
      status: 'healthy',
      uptime: '99.9%',
      lastIncident: null
    };
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