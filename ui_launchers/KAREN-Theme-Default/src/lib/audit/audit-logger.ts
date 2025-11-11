/**
 * Audit Logging System
 *
 * This module provides comprehensive audit logging functionality for tracking
 * administrative actions, security events, and system changes.
 */

import { AuditLog, AuditLogEntry, AuditLogFilter, PaginationParams, PaginatedResponse, User } from "@/types/admin";
import { getAdminDatabaseUtils } from "@/lib/database/admin-utils";
import { NextRequest } from "next/server";

/**
 * Audit action types for consistent logging
 */
export const AUDIT_ACTIONS = {
  // User management actions
  USER_CREATE: "user.create",
  USER_UPDATE: "user.update",
  USER_DELETE: "user.delete",
  USER_ACTIVATE: "user.activate",
  USER_DEACTIVATE: "user.deactivate",
  USER_ROLE_CHANGE: "user.role_change",
  USER_PASSWORD_RESET: "user.password_reset",
  USER_BULK_ACTIVATE: "user.bulk_activate",
  USER_BULK_DEACTIVATE: "user.bulk_deactivate",
  USER_BULK_DELETE: "user.bulk_delete",
  USER_EXPORT: "user.export",
  USER_IMPORT: "user.import",

  // Admin management actions
  ADMIN_CREATE: "admin.create",
  ADMIN_PROMOTE: "admin.promote",
  ADMIN_DEMOTE: "admin.demote",
  ADMIN_INVITE: "admin.invite",
  ADMIN_SUSPEND: "admin.suspend",

  // Authentication actions
  AUTH_LOGIN: "auth.login",
  AUTH_LOGOUT: "auth.logout",
  AUTH_LOGIN_FAILED: "auth.login_failed",
  AUTH_PASSWORD_CHANGE: "auth.password_change",
  AUTH_MFA_ENABLE: "auth.mfa_enable",
  AUTH_MFA_DISABLE: "auth.mfa_disable",
  AUTH_SESSION_EXPIRED: "auth.session_expired",

  // System configuration actions
  SYSTEM_CONFIG_UPDATE: "system.config_update",
  SYSTEM_CONFIG_CREATE: "system.config_create",
  SYSTEM_CONFIG_DELETE: "system.config_delete",

  // Security actions
  SECURITY_POLICY_UPDATE: "security.policy_update",
  SECURITY_ALERT_CREATE: "security.alert_create",
  SECURITY_BREACH_DETECTED: "security.breach_detected",
  SECURITY_IP_BLOCKED: "security.ip_blocked",

  // Audit actions
  AUDIT_LOG_VIEW: "audit.log_view",
  AUDIT_LOG_EXPORT: "audit.log_export",
  AUDIT_LOG_CLEANUP: "audit.log_cleanup",

  // Setup actions
  SETUP_SUPER_ADMIN_CREATE: "setup.super_admin_create",
  SETUP_FIRST_RUN_COMPLETE: "setup.first_run_complete",
} as const;

/**
 * Resource types for audit logging
 */
export const AUDIT_RESOURCE_TYPES = {
  USER: "user",
  ADMIN: "admin",
  SYSTEM_CONFIG: "system_config",
  AUDIT_LOG: "audit_log",
  SESSION: "session",
  SECURITY_POLICY: "security_policy",
  SETUP: "setup",
} as const;

/**
 * Extract client information from request
 */
function extractClientInfo(request?: NextRequest): {
  ip_address?: string;
  user_agent?: string;
} {
  if (!request) return {};

  const ip_address = request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ||
    request.headers.get("x-real-ip") ||
    undefined;

  const user_agent = request.headers.get("user-agent") || undefined;

  return { ip_address, user_agent };
}

/**
 * Main audit logger class
 */
export class AuditLogger {
  private _dbUtils: ReturnType<typeof getAdminDatabaseUtils> | null = null;

  private get dbUtils() {
    if (!this._dbUtils) {
      this._dbUtils = getAdminDatabaseUtils();
    }
    return this._dbUtils;
  }

  /**
   * Log an audit event
   */
  async log(
    userId: string,
    action: string,
    resourceType: string,
    options: {
      resourceId?: string;
      details?: Record<string, unknown>;
      request?: NextRequest;
      ip_address?: string;
      user_agent?: string;
    } = {}
  ): Promise<string> {
    const clientInfo = options.request
      ? extractClientInfo(options.request)
      : {};

    const entry: AuditLogEntry = {
      user_id: userId,
      action,
      resource_type: resourceType,
      resource_id: options.resourceId,
      details: options.details || {},
      ip_address: options.ip_address || clientInfo.ip_address,
      user_agent: options.user_agent || clientInfo.user_agent,
    };

    return await this.dbUtils.createAuditLog(entry);
  }

  /**
   * Log user management action
   */
  async logUserAction(
    adminUserId: string,
    action: string,
    targetUserId: string,
    details: Record<string, unknown> = {},
    request?: NextRequest
  ): Promise<string> {
    return await this.log(adminUserId, action, AUDIT_RESOURCE_TYPES.USER, {
      resourceId: targetUserId,
      details,
      request,
    });
  }

  /**
   * Log authentication action
   */
  async logAuthAction(
    userId: string,
    action: string,
    details: Record<string, unknown> = {},
    request?: NextRequest
  ): Promise<string> {
    return await this.log(userId, action, AUDIT_RESOURCE_TYPES.SESSION, {
      details,
      request,
    });
  }

  /**
   * Log system configuration change
   */
  async logSystemConfigAction(
    adminUserId: string,
    action: string,
    configKey: string,
    details: Record<string, unknown> = {},
    request?: NextRequest
  ): Promise<string> {
    return await this.log(
      adminUserId,
      action,
      AUDIT_RESOURCE_TYPES.SYSTEM_CONFIG,
      {
        resourceId: configKey,
        details,
        request,
      }
    );
  }

  /**
   * Log security event
   */
  async logSecurityEvent(
    userId: string,
    action: string,
    details: Record<string, unknown> = {},
    request?: NextRequest
  ): Promise<string> {
    return await this.log(
      userId,
      action,
      AUDIT_RESOURCE_TYPES.SECURITY_POLICY,
      {
        details: {
          ...details,
          severity: details.severity || "medium",
          timestamp: new Date().toISOString(),
        },
        request,
      }
    );
  }

  /**
   * Log bulk operation
   */
  async logBulkOperation(
    adminUserId: string,
    action: string,
    resourceType: string,
    resourceIds: string[],
    details: Record<string, unknown> = {},
    request?: NextRequest
  ): Promise<string> {
    return await this.log(adminUserId, action, resourceType, {
      details: {
        ...details,
        resource_ids: resourceIds,
        count: resourceIds.length,
      },
      request,
    });
  }

  /**
   * Get audit logs with filtering and pagination
   */
  async getAuditLogs(
    filter: AuditLogFilter = {},
    pagination: PaginationParams = { page: 1, limit: 50 }
  ): Promise<PaginatedResponse<AuditLog>> {
    return await this.dbUtils.getAuditLogs(filter, pagination);
  }

  /**
   * Get audit logs for a specific user
   */
  async getUserAuditLogs(
    userId: string,
    pagination: PaginationParams = { page: 1, limit: 50 }
  ): Promise<PaginatedResponse<AuditLog>> {
    return await this.getAuditLogs({ user_id: userId }, pagination);
  }

  /**
   * Get audit logs for a specific resource
   */
  async getResourceAuditLogs(
    resourceType: string,
    resourceId: string,
    pagination: PaginationParams = { page: 1, limit: 50 }
  ): Promise<PaginatedResponse<AuditLog>> {
    return await this.getAuditLogs({ resource_type: resourceType }, pagination);
  }

  /**
   * Get recent audit logs (last 24 hours)
   */
  async getRecentAuditLogs(limit: number = 100): Promise<AuditLog[]> {
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);

    const result = await this.getAuditLogs(
      { start_date: yesterday },
      { page: 1, limit, sort_by: "timestamp", sort_order: "desc" }
    );

    return result.data;
  }

  /**
   * Get audit log statistics
   */
  async getAuditLogStats(
    startDate?: Date,
    endDate?: Date
  ): Promise<{
    total_logs: number;
    unique_users: number;
    top_actions: Array<{ action: string; count: number }>;
    top_resources: Array<{ resource_type: string; count: number }>;
    logs_by_day: Array<{ date: string; count: number }>;
  }> {
    const filter: AuditLogFilter = {};
    if (startDate) filter.start_date = startDate;
    if (endDate) filter.end_date = endDate;

    // This would require additional database queries
    // For now, return basic stats from the existing data
    const logs = await this.getAuditLogs(filter, { page: 1, limit: 10000 });

    const uniqueUsers = new Set(logs.data.map((log) => log.user_id)).size;

    const actionCounts = logs.data.reduce((acc, log) => {
      acc[log.action] = (acc[log.action] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const resourceCounts = logs.data.reduce((acc, log) => {
      acc[log.resource_type] = (acc[log.resource_type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const topActions = Object.entries(actionCounts)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 10)
      .map(([action, count]) => ({ action, count }));

    const topResources = Object.entries(resourceCounts)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 10)
      .map(([resource_type, count]) => ({ resource_type, count }));

    // Group by day
    const logsByDay = logs.data.reduce((acc, log) => {
      const date = new Date(log.timestamp).toISOString().split("T")[0];
      acc[date] = (acc[date] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const logs_by_day = Object.entries(logsByDay)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([date, count]) => ({ date, count }));

    return {
      total_logs: logs.pagination.total,
      unique_users: uniqueUsers,
      top_actions: topActions,
      top_resources: topResources,
      logs_by_day,
    };
  }

  /**
   * Search audit logs by text
   */
  async searchAuditLogs(
    searchTerm: string,
    pagination: PaginationParams = { page: 1, limit: 50 }
  ): Promise<PaginatedResponse<AuditLog>> {
    // This would require a more sophisticated search implementation
    // For now, we'll search in action and resource_type fields
    const allLogs = await this.getAuditLogs({}, { page: 1, limit: 10000 });

    const filteredLogs = allLogs.data.filter(
      (log) =>
        log.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.resource_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (log.user?.email &&
          log.user.email.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (log.resource_id &&
          log.resource_id.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    const startIndex = (pagination.page - 1) * pagination.limit;
    const endIndex = startIndex + pagination.limit;
    const paginatedData = filteredLogs.slice(startIndex, endIndex);

    return {
      data: paginatedData,
      pagination: {
        page: pagination.page,
        limit: pagination.limit,
        total: filteredLogs.length,
        total_pages: Math.ceil(filteredLogs.length / pagination.limit),
        has_next: endIndex < filteredLogs.length,
        has_prev: pagination.page > 1,
      },
    };
  }
}

/**
 * Singleton audit logger instance
 */
let auditLoggerInstance: AuditLogger | null = null;

/**
 * Get the audit logger instance
 */
export function getAuditLogger(): AuditLogger {
  if (!auditLoggerInstance) {
    auditLoggerInstance = new AuditLogger();
  }
  return auditLoggerInstance;
}

/**
 * Convenience functions for common audit logging operations
 */
export const auditLog = {
  // User management
  userCreated: (
    adminId: string,
    userId: string,
    userEmail: string,
    role: string,
    request?: NextRequest
  ) =>
    getAuditLogger().logUserAction(
      adminId,
      AUDIT_ACTIONS.USER_CREATE,
      userId,
      { email: userEmail, role },
      request
    ),

  userUpdated: (
    adminId: string,
    userId: string,
    changes: Record<string, unknown>,
    request?: NextRequest
  ) =>
    getAuditLogger().logUserAction(
      adminId,
      AUDIT_ACTIONS.USER_UPDATE,
      userId,
      { changes },
      request
    ),

  userDeleted: (
    adminId: string,
    userId: string,
    userEmail: string,
    request?: NextRequest
  ) =>
    getAuditLogger().logUserAction(
      adminId,
      AUDIT_ACTIONS.USER_DELETE,
      userId,
      { email: userEmail },
      request
    ),

  userRoleChanged: (
    adminId: string,
    userId: string,
    oldRole: string,
    newRole: string,
    request?: NextRequest
  ) =>
    getAuditLogger().logUserAction(
      adminId,
      AUDIT_ACTIONS.USER_ROLE_CHANGE,
      userId,
      { old_role: oldRole, new_role: newRole },
      request
    ),

  // Authentication
  loginSuccessful: (userId: string, request?: NextRequest) =>
    getAuditLogger().logAuthAction(
      userId,
      AUDIT_ACTIONS.AUTH_LOGIN,
      {},
      request
    ),

  loginFailed: (userId: string, reason: string, request?: NextRequest) =>
    getAuditLogger().logAuthAction(
      userId,
      AUDIT_ACTIONS.AUTH_LOGIN_FAILED,
      { reason },
      request
    ),

  logout: (userId: string, request?: NextRequest) =>
    getAuditLogger().logAuthAction(
      userId,
      AUDIT_ACTIONS.AUTH_LOGOUT,
      {},
      request
    ),

  // System configuration
  configUpdated: (
    adminId: string,
    key: string,
    oldValue: unknown,
    newValue: unknown,
    request?: NextRequest
  ) =>
    getAuditLogger().logSystemConfigAction(
      adminId,
      AUDIT_ACTIONS.SYSTEM_CONFIG_UPDATE,
      key,
      { old_value: oldValue, new_value: newValue },
      request
    ),

  // Security events
  securityBreach: (
    userId: string,
    details: Record<string, unknown>,
    request?: NextRequest
  ) =>
    getAuditLogger().logSecurityEvent(
      userId,
      AUDIT_ACTIONS.SECURITY_BREACH_DETECTED,
      { ...details, severity: "critical" },
      request
    ),

  suspiciousActivity: (
    userId: string,
    details: Record<string, unknown>,
    request?: NextRequest
  ) =>
    getAuditLogger().logSecurityEvent(
      userId,
      AUDIT_ACTIONS.SECURITY_BREACH_DETECTED,
      { ...details, severity: "high" },
      request
    ),

  // Bulk operations
  bulkUserActivation: (
    adminId: string,
    userIds: string[],
    request?: NextRequest
  ) =>
    getAuditLogger().logBulkOperation(
      adminId,
      AUDIT_ACTIONS.USER_BULK_ACTIVATE,
      AUDIT_RESOURCE_TYPES.USER,
      userIds,
      {},
      request
    ),

  bulkUserDeactivation: (
    adminId: string,
    userIds: string[],
    request?: NextRequest
  ) =>
    getAuditLogger().logBulkOperation(
      adminId,
      AUDIT_ACTIONS.USER_BULK_DEACTIVATE,
      AUDIT_RESOURCE_TYPES.USER,
      userIds,
      {},
      request
    ),

  // Data export
  dataExported: (
    adminId: string,
    exportType: string,
    recordCount: number,
    request?: NextRequest
  ) =>
    getAuditLogger().log(
      adminId,
      AUDIT_ACTIONS.USER_EXPORT,
      AUDIT_RESOURCE_TYPES.USER,
      {
        details: { export_type: exportType, record_count: recordCount },
        request,
      }
    ),
};

/**
 * Default audit logger instance for backward compatibility
 */
export const auditLogger = getAuditLogger();
