/**
 * Audit Log Cleanup and Retention Management
 * 
 * This module provides functionality for managing audit log retention,
 * cleanup operations, and archival processes.
 */

import { getDatabaseClient } from '@/lib/database/client';
import { getAuditLogger, AUDIT_ACTIONS, AUDIT_RESOURCE_TYPES, AuditLogger } from './audit-logger';

/**
 * Audit log retention policies
 */
export interface AuditRetentionPolicy {
  id: string;
  name: string;
  description: string;
  retention_days: number;
  resource_types?: string[];
  actions?: string[];
  enabled: boolean;
  created_at: Date;
  updated_at: Date;
}

/**
 * Cleanup operation result
 */
export interface CleanupResult {
  success: boolean;
  deleted_count: number;
  archived_count?: number;
  error?: string;
  duration_ms: number;
  policy_applied: string;
}

/**
 * Cleanup statistics
 */
export interface CleanupStats {
  total_logs: number;
  logs_to_delete: number;
  logs_to_archive: number;
  oldest_log_date: Date | null;
  newest_log_date: Date | null;
  size_estimate_mb: number;
}

/**
 * Default retention policies
 */
export const DEFAULT_RETENTION_POLICIES: Omit<AuditRetentionPolicy, 'id' | 'created_at' | 'updated_at'>[] = [
  {
    name: 'Security Events - Long Term',
    description: 'Keep security-related audit logs for 2 years',
    retention_days: 730,
    resource_types: [AUDIT_RESOURCE_TYPES.SECURITY_POLICY],
    actions: [
      AUDIT_ACTIONS.SECURITY_BREACH_DETECTED,
      AUDIT_ACTIONS.SECURITY_ALERT_CREATE,
      AUDIT_ACTIONS.SECURITY_IP_BLOCKED,
      AUDIT_ACTIONS.AUTH_LOGIN_FAILED
    ],
    enabled: true
  },
  {
    name: 'Admin Actions - Medium Term',
    description: 'Keep admin management actions for 1 year',
    retention_days: 365,
    resource_types: [AUDIT_RESOURCE_TYPES.ADMIN, AUDIT_RESOURCE_TYPES.SYSTEM_CONFIG],
    actions: [
      AUDIT_ACTIONS.ADMIN_CREATE,
      AUDIT_ACTIONS.ADMIN_PROMOTE,
      AUDIT_ACTIONS.ADMIN_DEMOTE,
      AUDIT_ACTIONS.USER_ROLE_CHANGE,
      AUDIT_ACTIONS.SYSTEM_CONFIG_UPDATE
    ],
    enabled: true
  },
  {
    name: 'User Management - Medium Term',
    description: 'Keep user management actions for 6 months',
    retention_days: 180,
    resource_types: [AUDIT_RESOURCE_TYPES.USER],
    actions: [
      AUDIT_ACTIONS.USER_CREATE,
      AUDIT_ACTIONS.USER_UPDATE,
      AUDIT_ACTIONS.USER_DELETE,
      AUDIT_ACTIONS.USER_ACTIVATE,
      AUDIT_ACTIONS.USER_DEACTIVATE
    ],
    enabled: true
  },
  {
    name: 'Authentication Events - Short Term',
    description: 'Keep regular authentication events for 90 days',
    retention_days: 90,
    resource_types: [AUDIT_RESOURCE_TYPES.SESSION],
    actions: [
      AUDIT_ACTIONS.AUTH_LOGIN,
      AUDIT_ACTIONS.AUTH_LOGOUT,
      AUDIT_ACTIONS.AUTH_SESSION_EXPIRED
    ],
    enabled: true
  },
  {
    name: 'General Activities - Short Term',
    description: 'Keep general audit activities for 30 days',
    retention_days: 30,
    enabled: true
  }
];

/**
 * Audit cleanup manager class
 */
export class AuditCleanupManager {
  private db: ReturnType<typeof getDatabaseClient>;
  private auditLogger: AuditLogger;

  constructor() {
    this.db = getDatabaseClient();
    this.auditLogger = getAuditLogger();
  }

  /**
   * Get cleanup statistics
   */
  async getCleanupStats(policyId?: string): Promise<CleanupStats> {
    let whereClause = '';
    let queryParams: any[] = [];

    if (policyId) {
      // This would require implementing policy-specific filtering
      // For now, we'll get general stats
    }

    const statsQuery = `
        COUNT(*) as total_logs,
        MIN(timestamp) as oldest_log_date,
        MAX(timestamp) as newest_log_date,
        pg_size_pretty(pg_total_relation_size('audit_logs')) as table_size
      ${whereClause}
    `;

    const result = await this.db.query(statsQuery, queryParams);
    const stats = result.rows[0];

    // Calculate logs to delete based on default 90-day retention
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - 90);

    const deleteCountQuery = `
      SELECT COUNT(*) as logs_to_delete
      WHERE timestamp < $1
    `;

    const deleteResult = await this.db.query(deleteCountQuery, [cutoffDate]);

    return {
      total_logs: parseInt(stats.total_logs),
      logs_to_delete: parseInt(deleteResult.rows[0].logs_to_delete),
      logs_to_archive: 0, // Archive functionality not implemented yet
      oldest_log_date: stats.oldest_log_date ? new Date(stats.oldest_log_date) : null,
      newest_log_date: stats.newest_log_date ? new Date(stats.newest_log_date) : null,
      size_estimate_mb: 0 // Would need to parse pg_size_pretty result
    };
  }

  /**
   * Clean up audit logs based on retention policy
   */
  async cleanupLogs(
    retentionDays: number,
    resourceTypes?: string[],
    actions?: string[],
    dryRun: boolean = false
  ): Promise<CleanupResult> {
    const startTime = Date.now();
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - retentionDays);

    try {
      let whereConditions = ['timestamp < $1'];
      let queryParams: any[] = [cutoffDate];
      let paramIndex = 2;

      // Add resource type filter
      if (resourceTypes && resourceTypes.length > 0) {
        const placeholders = resourceTypes.map(() => `$${paramIndex++}`).join(',');
        whereConditions.push(`resource_type IN (${placeholders})`);
        queryParams.push(...resourceTypes);
      }

      // Add action filter
      if (actions && actions.length > 0) {
        const placeholders = actions.map(() => `$${paramIndex++}`).join(',');
        whereConditions.push(`action IN (${placeholders})`);
        queryParams.push(...actions);
      }

      const whereClause = whereConditions.join(' AND ');

      // First, count how many logs will be affected
      const countQuery = `
        SELECT COUNT(*) as count
        WHERE ${whereClause}
      `;

      const countResult = await this.db.query(countQuery, queryParams);
      const deleteCount = parseInt(countResult.rows[0].count);

      if (dryRun) {
        return {
          success: true,
          deleted_count: deleteCount,
          duration_ms: Date.now() - startTime,
          policy_applied: `Dry run: ${retentionDays} days retention`
        };
      }

      // Perform the actual deletion
      const deleteQuery = `
        WHERE ${whereClause}
      `;

      await this.db.query(deleteQuery, queryParams);

      // Log the cleanup operation
      await this.auditLogger.log(
        'system', // System user ID
        AUDIT_ACTIONS.AUDIT_LOG_CLEANUP,
        AUDIT_RESOURCE_TYPES.AUDIT_LOG,
        {
          details: {
            retention_days: retentionDays,
            deleted_count: deleteCount,
            cutoff_date: cutoffDate.toISOString(),
            resource_types: resourceTypes,
            actions: actions
          }
        }
      );

      return {
        success: true,
        deleted_count: deleteCount,
        duration_ms: Date.now() - startTime,
        policy_applied: `${retentionDays} days retention`
      };

    } catch (error) {
      return {
        success: false,
        deleted_count: 0,
        error: error instanceof Error ? error.message : 'Unknown error',
        duration_ms: Date.now() - startTime,
        policy_applied: `${retentionDays} days retention (failed)`
      };
    }
  }

  /**
   * Clean up logs using default policies
   */
  async cleanupWithDefaultPolicies(dryRun: boolean = false): Promise<CleanupResult[]> {
    const results: CleanupResult[] = [];

    for (const policy of DEFAULT_RETENTION_POLICIES) {
      if (!policy.enabled) continue;

      const result = await this.cleanupLogs(
        policy.retention_days,
        policy.resource_types,
        policy.actions,
        dryRun
      );

      results.push({
        ...result,
        policy_applied: policy.name

    }

    return results;
  }

  /**
   * Archive old audit logs to a separate table
   */
  async archiveLogs(
    retentionDays: number,
    resourceTypes?: string[],
    actions?: string[]
  ): Promise<CleanupResult> {
    const startTime = Date.now();
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - retentionDays);

    try {
      // Create archive table if it doesn't exist
      await this.createArchiveTable();

      let whereConditions = ['timestamp < $1'];
      let queryParams: any[] = [cutoffDate];
      let paramIndex = 2;

      // Add filters
      if (resourceTypes && resourceTypes.length > 0) {
        const placeholders = resourceTypes.map(() => `$${paramIndex++}`).join(',');
        whereConditions.push(`resource_type IN (${placeholders})`);
        queryParams.push(...resourceTypes);
      }

      if (actions && actions.length > 0) {
        const placeholders = actions.map(() => `$${paramIndex++}`).join(',');
        whereConditions.push(`action IN (${placeholders})`);
        queryParams.push(...actions);
      }

      const whereClause = whereConditions.join(' AND ');

      // Move logs to archive table
      const archiveQuery = `
        WITH archived_logs AS (
          WHERE ${whereClause}
          RETURNING *
        )
        SELECT *, NOW() as archived_at
      `;

      const result = await this.db.query(archiveQuery, queryParams);
      const archivedCount = result.rowCount || 0;

      // Log the archive operation
      await this.auditLogger.log(
        'system',
        'audit.log_archive',
        AUDIT_RESOURCE_TYPES.AUDIT_LOG,
        {
          details: {
            retention_days: retentionDays,
            archived_count: archivedCount,
            cutoff_date: cutoffDate.toISOString(),
            resource_types: resourceTypes,
            actions: actions
          }
        }
      );

      return {
        success: true,
        deleted_count: 0,
        archived_count: archivedCount,
        duration_ms: Date.now() - startTime,
        policy_applied: `Archive: ${retentionDays} days retention`
      };

    } catch (error) {
      return {
        success: false,
        deleted_count: 0,
        archived_count: 0,
        error: error instanceof Error ? error.message : 'Unknown error',
        duration_ms: Date.now() - startTime,
        policy_applied: `Archive: ${retentionDays} days retention (failed)`
      };
    }
  }

  /**
   * Create archive table for old audit logs
   */
  private async createArchiveTable(): Promise<void> {
    const createTableQuery = `
      CREATE TABLE IF NOT EXISTS audit_logs_archive (
        id UUID,
        user_id UUID,
        action VARCHAR(100),
        resource_type VARCHAR(50),
        resource_id VARCHAR(255),
        details JSONB,
        ip_address INET,
        user_agent TEXT,
        timestamp TIMESTAMP WITH TIME ZONE,
        archived_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
      )
    `;

    await this.db.query(createTableQuery);

    // Create indexes for the archive table
    const indexQueries = [
      'CREATE INDEX IF NOT EXISTS idx_audit_logs_archive_timestamp ON audit_logs_archive(timestamp DESC)',
      'CREATE INDEX IF NOT EXISTS idx_audit_logs_archive_user_id ON audit_logs_archive(user_id)',
      'CREATE INDEX IF NOT EXISTS idx_audit_logs_archive_action ON audit_logs_archive(action)',
      'CREATE INDEX IF NOT EXISTS idx_audit_logs_archive_archived_at ON audit_logs_archive(archived_at DESC)'
    ];

    for (const indexQuery of indexQueries) {
      await this.db.query(indexQuery);
    }
  }

  /**
   * Get archive statistics
   */
  async getArchiveStats(): Promise<{
    total_archived: number;
    oldest_archived: Date | null;
    newest_archived: Date | null;
    archive_size_mb: number;
  }> {
    try {
      const statsQuery = `
          COUNT(*) as total_archived,
          MIN(timestamp) as oldest_archived,
          MAX(timestamp) as newest_archived,
          pg_size_pretty(pg_total_relation_size('audit_logs_archive')) as archive_size
      `;

      const result = await this.db.query(statsQuery);
      const stats = result.rows[0];

      return {
        total_archived: parseInt(stats.total_archived || '0'),
        oldest_archived: stats.oldest_archived ? new Date(stats.oldest_archived) : null,
        newest_archived: stats.newest_archived ? new Date(stats.newest_archived) : null,
        archive_size_mb: 0 // Would need to parse pg_size_pretty result
      };
    } catch (error) {
      return {
        total_archived: 0,
        oldest_archived: null,
        newest_archived: null,
        archive_size_mb: 0
      };
    }
  }

  /**
   * Vacuum and analyze audit logs table for performance
   */
  async optimizeAuditTable(): Promise<{ success: boolean; duration_ms: number; error?: string }> {
    const startTime = Date.now();

    try {
      // Vacuum and analyze the audit_logs table
      await this.db.query('VACUUM ANALYZE audit_logs');

      // Also optimize the archive table if it exists
      try {
        await this.db.query('VACUUM ANALYZE audit_logs_archive');
      } catch {
        // Archive table might not exist, ignore error
      }

      return {
        success: true,
        duration_ms: Date.now() - startTime
      };
    } catch (error) {
      return {
        success: false,
        duration_ms: Date.now() - startTime,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Schedule automatic cleanup (this would be called by a cron job or scheduler)
   */
  async scheduleCleanup(): Promise<void> {
    // This would typically be implemented as a background job
    // For now, we'll just run the default cleanup policies
    const results = await this.cleanupWithDefaultPolicies(false);
    
    // Log the scheduled cleanup results
    await this.auditLogger.log(
      'system',
      'audit.scheduled_cleanup',
      AUDIT_RESOURCE_TYPES.AUDIT_LOG,
      {
        details: {
          cleanup_results: results,
          scheduled_at: new Date().toISOString()
        }
      }
    );
  }
}

/**
 * Singleton cleanup manager instance
 */
let cleanupManagerInstance: AuditCleanupManager | null = null;

/**
 * Get the audit cleanup manager instance
 */
export function getAuditCleanupManager(): AuditCleanupManager {
  if (!cleanupManagerInstance) {
    cleanupManagerInstance = new AuditCleanupManager();
  }
  return cleanupManagerInstance;
}

/**
 * Convenience functions for common cleanup operations
 */
export const auditCleanup = {
  /**
   * Clean up logs older than specified days
   */
  cleanupOlderThan: (days: number, dryRun: boolean = false) =>
    getAuditCleanupManager().cleanupLogs(days, undefined, undefined, dryRun),

  /**
   * Clean up authentication logs older than 90 days
   */
  cleanupAuthLogs: (dryRun: boolean = false) =>
    getAuditCleanupManager().cleanupLogs(
      90,
      [AUDIT_RESOURCE_TYPES.SESSION],
      [AUDIT_ACTIONS.AUTH_LOGIN, AUDIT_ACTIONS.AUTH_LOGOUT],
      dryRun
    ),

  /**
   * Clean up user management logs older than 180 days
   */
  cleanupUserLogs: (dryRun: boolean = false) =>
    getAuditCleanupManager().cleanupLogs(
      180,
      [AUDIT_RESOURCE_TYPES.USER],
      undefined,
      dryRun
    ),

  /**
   * Archive old logs instead of deleting them
   */
  archiveOldLogs: (days: number) =>
    getAuditCleanupManager().archiveLogs(days),

  /**
   * Get cleanup statistics
   */
  getStats: () =>
    getAuditCleanupManager().getCleanupStats(),

  /**
   * Optimize audit table performance
   */
  optimize: () =>
    getAuditCleanupManager().optimizeAuditTable(),

  /**
   * Run default cleanup policies
   */
  runDefaultCleanup: (dryRun: boolean = false) =>
    getAuditCleanupManager().cleanupWithDefaultPolicies(dryRun),
};