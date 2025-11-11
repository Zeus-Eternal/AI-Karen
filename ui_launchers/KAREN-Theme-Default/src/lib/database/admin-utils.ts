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
  UserListFilter,
  AuditLogFilter,
  PaginationParams,
  PaginatedResponse,
  AuditLogEntry,
  RoleBasedQuery
} from '@/types/admin';
import bcrypt from 'bcryptjs';
import { createHash, scryptSync, timingSafeEqual } from 'crypto';

import { DatabaseClient, getDatabaseClient } from './client';

function bufferFromValue(value: string | Buffer): Buffer {
  if (Buffer.isBuffer(value)) {
    return Buffer.from(value);
  }

  const trimmed = value.trim();
  if (/^[0-9a-f]+$/i.test(trimmed) && trimmed.length % 2 === 0) {
    return Buffer.from(trimmed, 'hex');
  }

  return Buffer.from(trimmed, 'utf8');
}

function safeCompare(expected: string | Buffer, actual: string | Buffer): boolean {
  const expectedBuffer = bufferFromValue(expected);
  const actualBuffer = bufferFromValue(actual);

  if (expectedBuffer.length !== actualBuffer.length) {
    return false;
  }

  return timingSafeEqual(expectedBuffer, actualBuffer);
}

function verifyPasswordHash(password: string, storedHash: string): boolean {
  if (!storedHash) {
    return false;
  }

  const normalized = storedHash.trim();

  if (/^\$2[aby]\$/i.test(normalized)) {
    try {
      return bcrypt.compareSync(password, normalized);
    } catch (error) {
      console.warn('bcrypt comparison failed', error);
      return false;
    }
  }

  const colonParts = normalized.split(':');
  const dollarParts = normalized.split('$');
  const parts = colonParts.length >= dollarParts.length ? colonParts : dollarParts;
  const algorithm = parts[0]?.toLowerCase();

  if (algorithm === 'scrypt') {
    const params = parts.slice(1).filter(Boolean);
    let salt: string | undefined;
    let digest: string | undefined;
    let N = 16384;
    let r = 8;
    let p = 1;

    if (params.length >= 5) {
      const maybeN = Number(params[0]);
      const maybeR = Number(params[1]);
      const maybeP = Number(params[2]);
      if (maybeN > 0 && maybeR > 0 && maybeP > 0) {
        N = maybeN;
        r = maybeR;
        p = maybeP;
        salt = params[3];
        digest = params[4];
      }
    }

    if (!salt || !digest) {
      salt = params[params.length - 2];
      digest = params[params.length - 1];
    }

    if (salt && digest) {
      try {
        const digestBuffer = bufferFromValue(digest);
        const derived = scryptSync(password, bufferFromValue(salt), digestBuffer.length, { N, r, p });
        return safeCompare(digestBuffer, derived);
      } catch (error) {
        console.warn('scrypt comparison failed', error);
        return false;
      }
    }
  }

  if (algorithm === 'sha256') {
    const salt = parts[1] ?? '';
    const digest = parts[parts.length - 1];
    if (digest) {
      const computed = createHash('sha256').update(`${salt}:${password}`).digest('hex');
      return safeCompare(digest, computed);
    }
  }

  const fallback = createHash('sha256').update(password).digest('hex');
  if (safeCompare(normalized, fallback)) {
    return true;
  }

  return normalized === password;
}

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
interface AdminInvitationRecord {
  id: string;
  email: string;
  token: string;
  invited_by: string;
  message?: string | null;
  expires_at: Date;
  status: 'pending' | 'accepted' | 'expired' | 'revoked';
  created_at: Date;
  updated_at: Date;
}

export interface AdminInvitation {
  id: string;
  email: string;
  token: string;
  invitedBy: string;
  message: string | null;
  expiresAt: Date;
  status: 'pending' | 'accepted' | 'expired' | 'revoked';
  createdAt: Date;
  updatedAt: Date;
}

interface SecurityAlertRecord {
  id: string;
  type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  metadata?: Record<string, unknown> | null;
  detected_at: Date;
  resolved_at?: Date | null;
  resolved_by?: string | null;
  resolution_note?: string | null;
}

interface UserRecord {
  user_id: string;
  email: string;
  full_name?: string | null;
  role: User['role'];
  roles?: unknown;
  tenant_id?: string | null;
  preferences?: unknown;
  is_verified?: boolean | number | null;
  is_active?: boolean | number | null;
  created_at: string | Date;
  updated_at: string | Date;
  last_login_at?: string | Date | null;
  failed_login_attempts?: number | null;
  locked_until?: string | Date | null;
  two_factor_enabled?: boolean | number | null;
  two_factor_secret?: string | null;
  created_by?: string | null;
}

type ConfigValue = string | number | boolean | Record<string, unknown> | unknown[];

export interface SecurityAlert {
  id: string;
  type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  metadata: Record<string, unknown> | null;
  detectedAt: string;
  resolved: boolean;
  resolvedAt?: string | null;
  resolvedBy?: string | null;
  resolutionNote?: string | null;
}

interface BlockedIpRecord {
  id: string;
  ip_address: string;
  reason?: string | null;
  failed_attempts: number;
  blocked_at: Date;
  blocked_by?: string | null;
  expires_at?: Date | null;
}

interface AuditLogRecord {
  id: string;
  user_id: string;
  action: string;
  resource_type: string;
  resource_id?: string | null;
  details?: unknown;
  ip_address?: string | null;
  user_agent?: string | null;
  timestamp: string | Date;
  user_email?: string | null;
  user_full_name?: string | null;
}

interface SystemConfigRow {
  id: string;
  key: string;
  value: string;
  value_type: unknown;
  category: unknown;
  description?: string | null;
  updated_by: string;
  updated_at: string | Date;
  created_at: string | Date;
  updated_by_email?: string | null;
  updated_by_name?: string | null;
}

const SYSTEM_CONFIG_VALUE_TYPES: ReadonlyArray<SystemConfig["value_type"]> = [
  "string",
  "number",
  "boolean",
  "json",
];

const SYSTEM_CONFIG_CATEGORIES: ReadonlyArray<SystemConfig["category"]> = [
  "security",
  "email",
  "general",
  "authentication",
];

function normalizeSystemConfigValueType(
  value: unknown
): SystemConfig["value_type"] {
  if (typeof value === "string") {
    const lower = value.toLowerCase() as SystemConfig["value_type"];
    if (SYSTEM_CONFIG_VALUE_TYPES.includes(lower)) {
      return lower;
    }
  }

  return "string";
}

function normalizeSystemConfigCategory(value: unknown): SystemConfig["category"] {
  if (typeof value === "string") {
    const lower = value.toLowerCase() as SystemConfig["category"];
    if (SYSTEM_CONFIG_CATEGORIES.includes(lower)) {
      return lower;
    }
  }

  return "general";
}

export interface BlockedIpEntry {
  id: string;
  ipAddress: string;
  reason: string | null;
  failedAttempts: number;
  blockedAt: string;
  blockedBy?: string | null;
  expiresAt?: string | null;
}

interface IpWhitelistRecord {
  id: string;
  ip_or_cidr: string;
  description?: string | null;
  user_id?: string | null;
  role_restriction?: 'super_admin' | 'admin' | null;
  created_by: string;
  created_at: Date;
  updated_at?: Date | null;
  is_active?: boolean | null;
}

export interface IpWhitelistEntry {
  id: string;
  ip_or_cidr: string;
  description: string;
  user_id?: string;
  role_restriction?: 'super_admin' | 'admin';
  created_by: string;
  created_at: Date;
  updated_at?: Date;
  is_active: boolean;
}

export interface SecuritySettings {
  mfaEnforcement: {
    enabled: boolean;
    gracePeriodDays: number;
  };
  sessionSecurity: {
    adminTimeoutMinutes: number;
    userTimeoutMinutes: number;
    maxConcurrentSessions: number;
    requireSecureCookies?: boolean;
    sameSite?: 'strict' | 'lax' | 'none';
  };
  ipRestrictions: {
    enabled: boolean;
    maxFailedAttempts: number;
    lockoutMinutes?: number;
    allowedRanges?: string[];
    blockedRanges?: string[];
  };
  monitoring: {
    alertThresholds?: {
      failedLogins: number;
      suspiciousActivity: number;
    };
    logRetentionDays: number;
    emitMetrics?: boolean;
  };
}

const DEFAULT_SECURITY_SETTINGS: SecuritySettings = {
  mfaEnforcement: {
    enabled: true,
    gracePeriodDays: 7,
  },
  sessionSecurity: {
    adminTimeoutMinutes: 30,
    userTimeoutMinutes: 60,
    maxConcurrentSessions: 3,
    requireSecureCookies: true,
    sameSite: 'strict',
  },
  ipRestrictions: {
    enabled: false,
    maxFailedAttempts: 5,
    lockoutMinutes: 30,
    allowedRanges: [],
    blockedRanges: [],
  },
  monitoring: {
    alertThresholds: {
      failedLogins: 10,
      suspiciousActivity: 5,
    },
    logRetentionDays: 90,
    emitMetrics: true,
  },
};

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
    params: unknown[] = []
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

  private mapInvitation(row: AdminInvitationRecord): AdminInvitation {
    return {
      id: row.id,
      email: row.email,
      token: row.token,
      invitedBy: row.invited_by,
      message: row.message ?? null,
      expiresAt: new Date(row.expires_at),
      status: row.status,
      createdAt: new Date(row.created_at),
      updatedAt: new Date(row.updated_at),
    };
  }

  private mapSecurityAlert(row: SecurityAlertRecord): SecurityAlert {
    return {
      id: row.id,
      type: row.type,
      severity: row.severity,
      message: row.message,
      metadata: (row.metadata as Record<string, unknown> | null) ?? null,
      detectedAt: new Date(row.detected_at).toISOString(),
      resolved: Boolean(row.resolved_at),
      resolvedAt: row.resolved_at ? new Date(row.resolved_at).toISOString() : null,
      resolvedBy: row.resolved_by ?? null,
      resolutionNote: row.resolution_note ?? null,
    };
  }

  private mapBlockedIp(row: BlockedIpRecord): BlockedIpEntry {
    return {
      id: row.id,
      ipAddress: row.ip_address,
      reason: row.reason ?? null,
      failedAttempts: row.failed_attempts,
      blockedAt: new Date(row.blocked_at).toISOString(),
      blockedBy: row.blocked_by ?? null,
      expiresAt: row.expires_at ? new Date(row.expires_at).toISOString() : null,
    };
  }

    private mapUserRow(row: UserRecord): User {
      let preferences: User['preferences'] | undefined;
      if (row.preferences) {
        try {
          preferences = typeof row.preferences === 'string'
            ? JSON.parse(row.preferences)
            : (row.preferences as User['preferences']);
        } catch {
          preferences = undefined;
        }
      }

      const roles: string[] = Array.isArray(row.roles)
        ? row.roles.filter((value: unknown): value is string => typeof value === 'string')
        : row.role
          ? [row.role]
          : [];

      return {
        user_id: row.user_id,
        email: row.email,
        full_name: row.full_name ?? undefined,
        role: row.role,
        roles,
        tenant_id: row.tenant_id ?? 'default',
        preferences,
        is_verified: Boolean(row.is_verified),
        is_active: Boolean(row.is_active),
        created_at: new Date(row.created_at),
        updated_at: new Date(row.updated_at),
        last_login_at: row.last_login_at ? new Date(row.last_login_at) : undefined,
        failed_login_attempts: row.failed_login_attempts ?? 0,
        locked_until: row.locked_until ? new Date(row.locked_until) : undefined,
        two_factor_enabled: Boolean(row.two_factor_enabled),
        two_factor_secret: row.two_factor_secret ?? null,
        created_by: row.created_by ?? undefined,
      };
    }

  /**
   * Find user by email with role information
   */
  async findUserByEmail(email: string): Promise<User | null> {
    const normalizedEmail = email.trim().toLowerCase();
    if (!normalizedEmail) {
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
        two_factor_enabled,
        two_factor_secret,
        created_by
      FROM auth_users
      WHERE LOWER(email) = $1
      LIMIT 1
    `;

    try {
      const rows = await this.executeQuery<UserRecord>('findUserByEmail', query, [normalizedEmail]);
      if (!rows.length) {
        return null;
      }

      return this.mapUserRow(rows[0]);
    } catch (error) {
      throw new AdminDatabaseError('Failed to find user by email', 'findUserByEmail', error);
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

  async verifyPassword(email: string, password: string): Promise<boolean> {
    const normalizedEmail = email.trim().toLowerCase();
    if (!normalizedEmail || !password) {
      return false;
    }

    const query = `
      SELECT aph.password_hash
      FROM auth_users u
      LEFT JOIN auth_password_hashes aph ON aph.user_id = u.user_id
      WHERE LOWER(u.email) = $1
      ORDER BY aph.updated_at DESC NULLS LAST, aph.created_at DESC NULLS LAST
      LIMIT 1
    `;

    try {
      const rows = await this.executeQuery<{ password_hash: string | null }>('verifyPassword', query, [normalizedEmail]);
      const storedHash = rows[0]?.password_hash;
      if (!storedHash) {
        return false;
      }

      return verifyPasswordHash(password, storedHash);
    } catch (error) {
      throw new AdminDatabaseError('Failed to verify password', 'verifyPassword', error);
    }
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
    
    const whereConditions: string[] = [];
    const queryParams: unknown[] = [];
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
    
    const whereConditions: string[] = [];
    const queryParams: unknown[] = [];
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
      const dataResult = await this.executeQuery<AuditLogRecord>('getAuditLogsData', dataQuery, dataParams);

      // Transform results to include user information
      const data: AuditLog[] = dataResult.map((row) => {
        const rawDetails = row.details;
        let details: Record<string, unknown> = {};
        if (typeof rawDetails === 'string') {
          try {
            details = JSON.parse(rawDetails) as Record<string, unknown>;
          } catch {
            details = {};
          }
        } else if (rawDetails && typeof rawDetails === 'object') {
          details = rawDetails as Record<string, unknown>;
        }

        return {
          id: row.id,
          user_id: row.user_id,
          action: row.action,
          resource_type: row.resource_type,
          resource_id: row.resource_id ? String(row.resource_id) : undefined,
          details,
          ip_address: row.ip_address ?? undefined,
          user_agent: row.user_agent ?? undefined,
          timestamp: new Date(row.timestamp),
          user: row.user_email
            ? {
                user_id: row.user_id,
                email: row.user_email,
                full_name: row.user_full_name ?? undefined,
              }
            : undefined,
        };
      });

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
    
    const queryParams: unknown[] = [];
    
    if (category) {
      query += ` WHERE sc.category = $1`;
      queryParams.push(category);
    }
    
    query += ` ORDER BY sc.category, sc.key`;
    
    try {
      const result = await this.executeQuery<SystemConfigRow>('getSystemConfig', query, queryParams);

      return result.map((row) => {
        const valueType = normalizeSystemConfigValueType(row.value_type);
        const categoryValue = normalizeSystemConfigCategory(row.category);

        return {
          id: row.id,
          key: row.key,
          value: this.parseConfigValue(row.value, valueType),
          value_type: valueType,
          category: categoryValue,
          description: row.description ?? undefined,
          updated_by: row.updated_by,
          updated_at: new Date(row.updated_at),
          created_at: new Date(row.created_at),
          updated_by_user: row.updated_by_email
            ? {
                user_id: row.updated_by,
                email: row.updated_by_email,
                full_name: row.updated_by_name ?? undefined,
              }
            : undefined,
        };
      });
    } catch (error) {
      throw new AdminDatabaseError(
        'Failed to fetch system configuration',
        'getSystemConfig',
        error
      );
    }
  }

  /**
   * Retrieve structured security settings (with sane defaults)
   */
  async getSecuritySettings(): Promise<SecuritySettings> {
    try {
      const rows = await this.getSystemConfig('security');
      const map = new Map(rows.map((row) => [row.key, row.value]));

      const settings: SecuritySettings = {
        mfaEnforcement: {
          enabled: this.coerceBoolean(map.get('security.mfa.enabled'), DEFAULT_SECURITY_SETTINGS.mfaEnforcement.enabled),
          gracePeriodDays: this.coerceNumber(
            map.get('security.mfa.grace_period_days'),
            DEFAULT_SECURITY_SETTINGS.mfaEnforcement.gracePeriodDays,
            { min: 0, max: 30 },
          ),
        },
        sessionSecurity: {
          adminTimeoutMinutes: this.coerceNumber(
            map.get('security.session.admin_timeout_minutes'),
            DEFAULT_SECURITY_SETTINGS.sessionSecurity.adminTimeoutMinutes,
            { min: 5, max: 480 },
          ),
          userTimeoutMinutes: this.coerceNumber(
            map.get('security.session.user_timeout_minutes'),
            DEFAULT_SECURITY_SETTINGS.sessionSecurity.userTimeoutMinutes,
            { min: 5, max: 1440 },
          ),
          maxConcurrentSessions: this.coerceNumber(
            map.get('security.session.max_concurrent_sessions'),
            DEFAULT_SECURITY_SETTINGS.sessionSecurity.maxConcurrentSessions,
            { min: 1, max: 10 },
          ),
          requireSecureCookies: this.coerceBoolean(
            map.get('security.session.require_secure_cookies'),
            DEFAULT_SECURITY_SETTINGS.sessionSecurity.requireSecureCookies ?? true,
          ),
          sameSite:
            (map.get('security.session.same_site') as SecuritySettings['sessionSecurity']['sameSite']) ||
            DEFAULT_SECURITY_SETTINGS.sessionSecurity.sameSite,
        },
        ipRestrictions: {
          enabled: this.coerceBoolean(
            map.get('security.ip.enabled'),
            DEFAULT_SECURITY_SETTINGS.ipRestrictions.enabled,
          ),
          maxFailedAttempts: this.coerceNumber(
            map.get('security.ip.max_failed_attempts'),
            DEFAULT_SECURITY_SETTINGS.ipRestrictions.maxFailedAttempts,
            { min: 3, max: 20 },
          ),
          lockoutMinutes: this.coerceNumber(
            map.get('security.ip.lockout_minutes'),
            DEFAULT_SECURITY_SETTINGS.ipRestrictions.lockoutMinutes ?? 30,
            { min: 1, max: 1440 },
          ),
          allowedRanges: this.coerceStringArray(
            map.get('security.ip.allowed_ranges'),
            DEFAULT_SECURITY_SETTINGS.ipRestrictions.allowedRanges ?? [],
          ),
          blockedRanges: this.coerceStringArray(
            map.get('security.ip.blocked_ranges'),
            DEFAULT_SECURITY_SETTINGS.ipRestrictions.blockedRanges ?? [],
          ),
        },
        monitoring: {
          alertThresholds: this.coerceAlertThresholds(
            map.get('security.monitoring.alert_thresholds'),
            DEFAULT_SECURITY_SETTINGS.monitoring.alertThresholds ?? { failedLogins: 10, suspiciousActivity: 5 },
          ),
          logRetentionDays: this.coerceNumber(
            map.get('security.monitoring.log_retention_days'),
            DEFAULT_SECURITY_SETTINGS.monitoring.logRetentionDays,
            { min: 7, max: 365 },
          ),
          emitMetrics: this.coerceBoolean(
            map.get('security.monitoring.emit_metrics'),
            DEFAULT_SECURITY_SETTINGS.monitoring.emitMetrics ?? true,
          ),
        },
      };

      return settings;
    } catch (error) {
      throw new AdminDatabaseError('Failed to fetch security settings', 'getSecuritySettings', error);
    }
  }

  /**
   * Update system configuration value
   */
  async updateSystemConfig(
    key: string,
    value: string | number | boolean | Record<string, unknown> | Array<unknown>,
    updatedBy: string,
    description?: string
  ): Promise<void> {
    if (!key || !updatedBy) {
      throw new AdminDatabaseError('Missing required parameters for config update', 'updateSystemConfig');
    }

    const isJson = typeof value === 'object' && value !== null;
    const valueType = isJson ? 'json' : typeof value;
    const valueStr = isJson ? JSON.stringify(value) : String(value);
    
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

  async updateSecuritySettings(settings: Partial<SecuritySettings>, updatedBy: string): Promise<void> {
    if (!updatedBy) {
      throw new AdminDatabaseError('Missing user information for security settings update', 'updateSecuritySettings');
    }

    const updates: Array<{ key: string; value: ConfigValue }> = [];

    if (settings.mfaEnforcement) {
      if (typeof settings.mfaEnforcement.enabled === 'boolean') {
        updates.push({ key: 'security.mfa.enabled', value: settings.mfaEnforcement.enabled });
      }
      if (typeof settings.mfaEnforcement.gracePeriodDays === 'number') {
        updates.push({ key: 'security.mfa.grace_period_days', value: settings.mfaEnforcement.gracePeriodDays });
      }
    }

    if (settings.sessionSecurity) {
      const session = settings.sessionSecurity;
      if (typeof session.adminTimeoutMinutes === 'number') {
        updates.push({ key: 'security.session.admin_timeout_minutes', value: session.adminTimeoutMinutes });
      }
      if (typeof session.userTimeoutMinutes === 'number') {
        updates.push({ key: 'security.session.user_timeout_minutes', value: session.userTimeoutMinutes });
      }
      if (typeof session.maxConcurrentSessions === 'number') {
        updates.push({ key: 'security.session.max_concurrent_sessions', value: session.maxConcurrentSessions });
      }
      if (typeof session.requireSecureCookies === 'boolean') {
        updates.push({ key: 'security.session.require_secure_cookies', value: session.requireSecureCookies });
      }
      if (session.sameSite) {
        updates.push({ key: 'security.session.same_site', value: session.sameSite });
      }
    }

    if (settings.ipRestrictions) {
      const ip = settings.ipRestrictions;
      if (typeof ip.enabled === 'boolean') {
        updates.push({ key: 'security.ip.enabled', value: ip.enabled });
      }
      if (typeof ip.maxFailedAttempts === 'number') {
        updates.push({ key: 'security.ip.max_failed_attempts', value: ip.maxFailedAttempts });
      }
      if (typeof ip.lockoutMinutes === 'number') {
        updates.push({ key: 'security.ip.lockout_minutes', value: ip.lockoutMinutes });
      }
      if (ip.allowedRanges) {
        updates.push({ key: 'security.ip.allowed_ranges', value: ip.allowedRanges });
      }
      if (ip.blockedRanges) {
        updates.push({ key: 'security.ip.blocked_ranges', value: ip.blockedRanges });
      }
    }

    if (settings.monitoring) {
      const monitoring = settings.monitoring;
      if (monitoring.alertThresholds) {
        updates.push({ key: 'security.monitoring.alert_thresholds', value: monitoring.alertThresholds });
      }
      if (typeof monitoring.logRetentionDays === 'number') {
        updates.push({ key: 'security.monitoring.log_retention_days', value: monitoring.logRetentionDays });
      }
      if (typeof monitoring.emitMetrics === 'boolean') {
        updates.push({ key: 'security.monitoring.emit_metrics', value: monitoring.emitMetrics });
      }
    }

    if (updates.length === 0) {
      return;
    }

    for (const update of updates) {
      await this.updateSystemConfig(update.key, update.value, updatedBy);
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
      two_factor_secret?: string | null;
      is_active?: boolean;
      preferences?: Record<string, unknown>;
    }
  ): Promise<void> {
    if (!userId) {
      throw new AdminDatabaseError('User ID is required', 'updateUser');
    }

    const updateFields: string[] = [];
    const queryParams: unknown[] = [];
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
    _resourceId?: string
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
      console.warn('Permission check failed, denying access by default.', error);
      // If we can't determine permissions, deny access
      return false;
    }
  }

  /**
   * Parse configuration value based on type
   */
  private parseConfigValue(
    value: string,
    type: SystemConfig["value_type"] | "object"
  ): string | number | boolean {
    if (value === null || value === undefined) {
      return value;
    }

    switch (type) {
      case 'number': {
        const num = parseFloat(value);
        return isNaN(num) ? value : num;
      }
      case 'boolean':
        return value.toLowerCase() === 'true' || value === '1';
      case 'object':
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

  private coerceBoolean(value: unknown, fallback: boolean): boolean {
    if (typeof value === 'boolean') return value;
    if (typeof value === 'number') return value !== 0;
    if (typeof value === 'string') {
      const normalized = value.trim().toLowerCase();
      if (['true', '1', 'yes', 'on', 'enabled'].includes(normalized)) return true;
      if (['false', '0', 'no', 'off', 'disabled'].includes(normalized)) return false;
    }
    return fallback;
  }

  private coerceNumber(value: unknown, fallback: number, options: { min?: number; max?: number } = {}): number {
    const numeric =
      typeof value === 'number'
        ? value
        : typeof value === 'string'
        ? Number.parseFloat(value)
        : NaN;

    if (!Number.isFinite(numeric)) {
      return fallback;
    }

    let result = numeric;
    if (typeof options.min === 'number') {
      result = Math.max(options.min, result);
    }
    if (typeof options.max === 'number') {
      result = Math.min(options.max, result);
    }
    return result;
  }

  private coerceStringArray(value: unknown, fallback: string[] = []): string[] {
    if (Array.isArray(value)) {
      return value.filter((item): item is string => typeof item === 'string');
    }

    if (typeof value === 'string') {
      const trimmed = value.trim();
      if (!trimmed) return [...fallback];
      try {
        const parsed = JSON.parse(trimmed);
        if (Array.isArray(parsed)) {
          return parsed.filter((item): item is string => typeof item === 'string');
        }
      } catch {
        return trimmed
          .split(',')
          .map((part) => part.trim())
          .filter((part) => part.length > 0);
      }
    }

    return [...fallback];
  }

  private coerceAlertThresholds(
    value: unknown,
    fallback: { failedLogins: number; suspiciousActivity: number },
  ): { failedLogins: number; suspiciousActivity: number } {
    if (typeof value === 'object' && value !== null) {
      const obj = value as Record<string, unknown>;
      return {
        failedLogins: this.coerceNumber(obj.failedLogins, fallback.failedLogins, { min: 0 }),
        suspiciousActivity: this.coerceNumber(obj.suspiciousActivity, fallback.suspiciousActivity, { min: 0 }),
      };
    }

    if (typeof value === 'string') {
      try {
        const parsed = JSON.parse(value);
        if (typeof parsed === 'object' && parsed !== null) {
          const obj = parsed as Record<string, unknown>;
          return {
            failedLogins: this.coerceNumber(obj.failedLogins, fallback.failedLogins, { min: 0 }),
            suspiciousActivity: this.coerceNumber(obj.suspiciousActivity, fallback.suspiciousActivity, { min: 0 }),
          };
        }
      } catch {
        // ignore
      }
    }

    return { ...fallback };
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

  /**
   * Create a new admin invitation record
   */
  async createAdminInvitation(payload: {
    email: string;
    token: string;
    invitedBy: string;
    expiresAt: Date;
    message?: string;
  }): Promise<AdminInvitation> {
    const query = `
      INSERT INTO admin_invitations (
        email,
        token,
        invited_by,
        message,
        expires_at,
        status
      )
      VALUES ($1, $2, $3, $4, $5, 'pending')
      RETURNING id, email, token, invited_by, message, expires_at, status, created_at, updated_at
    `;

    try {
      const rows = await this.executeQuery<AdminInvitationRecord>('createAdminInvitation', query, [
        payload.email,
        payload.token,
        payload.invitedBy,
        payload.message ?? null,
        payload.expiresAt,
      ]);

      const record = rows[0];
      if (!record) {
        throw new Error('Invitation insert returned no rows');
      }

      return this.mapInvitation(record);
    } catch (error) {
      throw new AdminDatabaseError('Failed to create admin invitation', 'createAdminInvitation', error);
    }
  }

  /**
   * Count unresolved security alerts
   */
  async getSecurityAlertsCount(): Promise<number> {
    const query = `
      SELECT COUNT(*) AS count
      FROM security_alerts
      WHERE resolved_at IS NULL
    `;

    try {
      const rows = await this.executeQuery<{ count: string }>('getSecurityAlertsCount', query);
      return parseInt(rows[0]?.count || '0', 10);
    } catch (error) {
      throw new AdminDatabaseError('Failed to count security alerts', 'getSecurityAlertsCount', error);
    }
  }

  /**
   * List security alerts with pagination and optional filters
   */
  async getSecurityAlerts(params: {
    limit: number;
    offset: number;
    severity?: string;
    resolved?: boolean;
  }): Promise<{ data: SecurityAlert[]; total: number }> {
    const filters: string[] = [];
    const values: unknown[] = [];

    if (params.severity) {
      values.push(params.severity);
      filters.push(`severity = $${values.length}`);
    }

    if (typeof params.resolved === 'boolean') {
      values.push(params.resolved);
      filters.push(`(resolved_at IS ${params.resolved ? 'NOT NULL' : 'NULL'})`);
    }

    const whereClause = filters.length ? `WHERE ${filters.join(' AND ')}` : '';

    const baseQuery = `
      SELECT id, type, severity, message, metadata, detected_at, resolved_at, resolved_by, resolution_note
      FROM security_alerts
      ${whereClause}
      ORDER BY detected_at DESC
      LIMIT $${values.length + 1}
      OFFSET $${values.length + 2}
    `;

    const countQuery = `
      SELECT COUNT(*) AS count
      FROM security_alerts
      ${whereClause}
    `;

    try {
      const [rows, countRows] = await Promise.all([
        this.executeQuery<SecurityAlertRecord>('getSecurityAlerts', baseQuery, [...values, params.limit, params.offset]),
        this.executeQuery<{ count: string }>('getSecurityAlertsCountTotal', countQuery, values),
      ]);

      return {
        data: rows.map((row) => this.mapSecurityAlert(row)),
        total: parseInt(countRows[0]?.count || '0', 10),
      };
    } catch (error) {
      throw new AdminDatabaseError('Failed to load security alerts', 'getSecurityAlerts', error);
    }
  }

  /**
   * Fetch single security alert
   */
  async getSecurityAlert(alertId: string): Promise<SecurityAlert | null> {
    if (!alertId) {
      return null;
    }

    const query = `
      SELECT id, type, severity, message, metadata, detected_at, resolved_at, resolved_by, resolution_note
      FROM security_alerts
      WHERE id = $1
    `;

    try {
      const rows = await this.executeQuery<SecurityAlertRecord>('getSecurityAlert', query, [alertId]);
      return rows[0] ? this.mapSecurityAlert(rows[0]) : null;
    } catch (error) {
      throw new AdminDatabaseError('Failed to load security alert', 'getSecurityAlert', error);
    }
  }

  /**
   * Resolve a security alert
   */
  async resolveSecurityAlert(alertId: string, resolvedBy: string, resolutionNote?: string): Promise<void> {
    const query = `
      UPDATE security_alerts
      SET resolved_at = NOW(), resolved_by = $2, resolution_note = $3
      WHERE id = $1 AND resolved_at IS NULL
    `;

    try {
      await this.db.query(query, [alertId, resolvedBy, resolutionNote ?? null]);
    } catch (error) {
      throw new AdminDatabaseError('Failed to resolve security alert', 'resolveSecurityAlert', error);
    }
  }

  /**
   * Persist an IP block entry
   */
  async blockIp(
    ip: string,
    reason?: string | null,
    blockedUntil?: Date | null,
    blockedBy?: string | null,
  ): Promise<void> {
    if (!ip) {
      throw new AdminDatabaseError('IP address is required', 'blockIp');
    }

    const query = `
      INSERT INTO blocked_ips (ip_address, reason, blocked_at, blocked_by, expires_at, failed_attempts)
      VALUES ($1, $2, NOW(), $3, $4, COALESCE((SELECT failed_attempts FROM blocked_ips WHERE ip_address = $1), 0))
      ON CONFLICT (ip_address) DO UPDATE SET
        reason = EXCLUDED.reason,
        blocked_at = NOW(),
        blocked_by = EXCLUDED.blocked_by,
        expires_at = EXCLUDED.expires_at
    `;

    try {
      await this.db.query(query, [ip, reason ?? null, blockedBy ?? null, blockedUntil ?? null]);
    } catch (error) {
      throw new AdminDatabaseError('Failed to persist IP block', 'blockIp', error);
    }
  }

  /**
   * Check if IP is whitelisted with optional user/role constraints
   */
  async isIpWhitelisted(ip: string, userId?: string, role?: 'super_admin' | 'admin'): Promise<boolean> {
    if (!ip) {
      return false;
    }

    const conditions: string[] = [
      'is_active IS DISTINCT FROM FALSE',
      `(ip_or_cidr = $1 OR (POSITION('/' IN ip_or_cidr) > 0 AND inet($1) <<= inet(ip_or_cidr)))`,
    ];
    const params: unknown[] = [ip];
    let index = 2;

    if (userId) {
      conditions.push(`(user_id IS NULL OR user_id = $${index})`);
      params.push(userId);
      index += 1;
    } else {
      conditions.push('user_id IS NULL');
    }

    if (role) {
      conditions.push(`(role_restriction IS NULL OR role_restriction = $${index})`);
      params.push(role);
      index += 1;
    } else {
      conditions.push('role_restriction IS NULL');
    }

    const query = `
      SELECT 1
      FROM ip_whitelist
      WHERE ${conditions.join(' AND ')}
      LIMIT 1
    `;

    try {
      const rows = await this.executeQuery<{ exists: number }>('isIpWhitelisted', query, params);
      return rows.length > 0;
    } catch (error) {
      throw new AdminDatabaseError('Failed to check IP whitelist', 'isIpWhitelisted', error);
    }
  }

  /**
   * Remove an IP block entry by address
   */
  async unblockIp(ip: string): Promise<void> {
    if (!ip) {
      throw new AdminDatabaseError('IP address is required', 'unblockIp');
    }

    const query = `DELETE FROM blocked_ips WHERE ip_address = $1`;

    try {
      await this.db.query(query, [ip]);
    } catch (error) {
      throw new AdminDatabaseError('Failed to remove blocked IP', 'unblockIp', error);
    }
  }

  /**
   * List blocked IP addresses
   */
  async getBlockedIPs(params: { limit?: number; offset?: number }): Promise<PaginatedResponse<BlockedIpEntry>> {
    const limit = Math.max(1, Math.min(params.limit ?? 50, 200));
    const offset = Math.max(0, params.offset ?? 0);

    const dataQuery = `
      SELECT id, ip_address, reason, failed_attempts, blocked_at, blocked_by, expires_at
      FROM blocked_ips
      ORDER BY blocked_at DESC
      LIMIT $1 OFFSET $2
    `;

    const countQuery = `SELECT COUNT(*) AS count FROM blocked_ips`;

    try {
      const [rows, countRows] = await Promise.all([
        this.executeQuery<BlockedIpRecord>('getBlockedIPs', dataQuery, [limit, offset]),
        this.executeQuery<{ count: string }>('getBlockedIPsCount', countQuery),
      ]);

      const total = parseInt(countRows[0]?.count || '0', 10);
      const page = Math.floor(offset / limit) + 1;
      const totalPages = Math.max(1, Math.ceil(total / limit) || 1);

      return {
        data: rows.map((row) => this.mapBlockedIp(row)),
        pagination: {
          page,
          limit,
          total,
          total_pages: totalPages,
          has_next: page < totalPages,
          has_prev: page > 1,
        },
      };
    } catch (error) {
      throw new AdminDatabaseError('Failed to fetch blocked IPs', 'getBlockedIPs', error);
    }
  }

  /**
   * Fetch a single blocked IP entry
   */
  async getBlockedIP(id: string): Promise<BlockedIpEntry | null> {
    if (!id) {
      return null;
    }

    const query = `
      SELECT id, ip_address, reason, failed_attempts, blocked_at, blocked_by, expires_at
      FROM blocked_ips
      WHERE id = $1
    `;

    try {
      const rows = await this.executeQuery<BlockedIpRecord>('getBlockedIP', query, [id]);
      return rows[0] ? this.mapBlockedIp(rows[0]) : null;
    } catch (error) {
      throw new AdminDatabaseError('Failed to load blocked IP', 'getBlockedIP', error);
    }
  }

  /**
   * Remove a blocked IP entry
   */
  async unblockIP(id: string): Promise<void> {
    const query = `DELETE FROM blocked_ips WHERE id = $1`;

    try {
      await this.db.query(query, [id]);
    } catch (error) {
      throw new AdminDatabaseError('Failed to unblock IP', 'unblockIP', error);
    }
  }

  async getIpWhitelistEntries(): Promise<IpWhitelistEntry[]> {
    const query = `
      SELECT id, ip_or_cidr, description, user_id, role_restriction, created_by, created_at, updated_at, is_active
      FROM ip_whitelist
      ORDER BY created_at DESC
    `;

    try {
      const rows = await this.executeQuery<IpWhitelistRecord>('getIpWhitelistEntries', query);
      return rows.map((row) => ({
        id: row.id,
        ip_or_cidr: row.ip_or_cidr,
        description: row.description ?? '',
        user_id: row.user_id ?? undefined,
        role_restriction: row.role_restriction ?? undefined,
        created_by: row.created_by,
        created_at: new Date(row.created_at),
        updated_at: row.updated_at ? new Date(row.updated_at) : undefined,
        is_active: row.is_active !== false,
      }));
    } catch (error) {
      throw new AdminDatabaseError('Failed to fetch whitelist entries', 'getIpWhitelistEntries', error);
    }
  }

  async upsertIpWhitelist(entry: IpWhitelistEntry): Promise<void> {
    const query = `
      INSERT INTO ip_whitelist (id, ip_or_cidr, description, user_id, role_restriction, created_by, created_at, updated_at, is_active)
      VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), $8)
      ON CONFLICT (id) DO UPDATE SET
        ip_or_cidr = EXCLUDED.ip_or_cidr,
        description = EXCLUDED.description,
        user_id = EXCLUDED.user_id,
        role_restriction = EXCLUDED.role_restriction,
        is_active = EXCLUDED.is_active,
        updated_at = NOW()
    `;

    try {
      await this.db.query(query, [
        entry.id,
        entry.ip_or_cidr,
        entry.description ?? null,
        entry.user_id ?? null,
        entry.role_restriction ?? null,
        entry.created_by,
        entry.created_at,
        entry.is_active !== false,
      ]);
    } catch (error) {
      throw new AdminDatabaseError('Failed to upsert whitelist entry', 'upsertIpWhitelist', error);
    }
  }

  async removeIpWhitelist(id: string): Promise<void> {
    const query = `DELETE FROM ip_whitelist WHERE id = $1`;

    try {
      await this.db.query(query, [id]);
    } catch (error) {
      throw new AdminDatabaseError('Failed to remove whitelist entry', 'removeIpWhitelist', error);
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