/**
 * Audit Log Cleanup API Route
 * POST /api/admin/system/audit-logs/cleanup - Manage audit log cleanup and retention
 * 
 * Requirements: 5.1, 5.2, 5.3
 */

import { NextRequest, NextResponse } from 'next/server';
import { requireAdmin } from '@/lib/middleware/admin-auth';
import { getAuditCleanupManager, auditCleanup } from '@/lib/audit/audit-cleanup';
import { getAuditLogger } from '@/lib/audit/audit-logger';
import type { AdminApiResponse } from '@/types/admin';

/**
 * POST /api/admin/system/audit-logs/cleanup - Audit log cleanup operations
 */
export const POST = requireAdmin(async (request: NextRequest, context) => {
  try {
    // Only super admins can perform cleanup operations
    if (!context.isSuperAdmin()) {
      return NextResponse.json({
        success: false,
        error: {
          code: 'INSUFFICIENT_PERMISSIONS',
          message: 'Audit log cleanup requires super admin privileges',
          details: { required_role: 'super_admin', current_role: context.user.role }
        }
      } as AdminApiResponse<never>, { status: 403 });
    }

    const body = await request.json();
    const { action, retention_days, resource_types, actions: actionFilter, dry_run = true } = body;

    const cleanupManager = getAuditCleanupManager();
    const auditLogger = getAuditLogger();

    switch (action) {
      case 'get_stats':
        {
          const stats = await cleanupManager.getCleanupStats();
          const archiveStats = await cleanupManager.getArchiveStats();

          return NextResponse.json({
            success: true,
            data: {
              cleanup_stats: stats,
              archive_stats: archiveStats
            }
          });
        }

      case 'cleanup':
        {
          if (!retention_days || retention_days < 1) {
            return NextResponse.json({
              success: false,
              error: {
                code: 'INVALID_RETENTION_DAYS',
                message: 'Retention days must be a positive number',
                details: { provided_retention_days: retention_days }
              }
            } as AdminApiResponse<never>, { status: 400 });
          }

          const result = await cleanupManager.cleanupLogs(
            retention_days,
            resource_types,
            actionFilter,
            dry_run
          );

          // Log the cleanup operation
          await auditLogger.log(
            context.user.user_id,
            dry_run ? 'audit.cleanup_preview' : 'audit.cleanup_execute',
            'audit_log',
            {
              details: {
                retention_days,
                resource_types,
                actions: actionFilter,
                dry_run,
                result
              },
              request
            }
          );

          return NextResponse.json({
            success: true,
            data: {
              cleanup_result: result,
              dry_run,
              warning: dry_run ? 'This was a dry run. No data was actually deleted.' : undefined
            }
          });
        }

      case 'cleanup_default_policies':
        {
          const results = await cleanupManager.cleanupWithDefaultPolicies(dry_run);

          // Log the policy-based cleanup
          await auditLogger.log(
            context.user.user_id,
            dry_run ? 'audit.policy_cleanup_preview' : 'audit.policy_cleanup_execute',
            'audit_log',
            {
              details: {
                dry_run,
                policy_results: results,
                total_deleted: results.reduce((sum, r) => sum + r.deleted_count, 0)
              },
              request
            }
          );

          return NextResponse.json({
            success: true,
            data: {
              policy_results: results,
              dry_run,
              total_deleted: results.reduce((sum, r) => sum + r.deleted_count, 0),
              warning: dry_run ? 'This was a dry run. No data was actually deleted.' : undefined
            }
          });
        }

      case 'archive':
        {
          if (!retention_days || retention_days < 1) {
            return NextResponse.json({
              success: false,
              error: {
                code: 'INVALID_RETENTION_DAYS',
                message: 'Retention days must be a positive number',
                details: { provided_retention_days: retention_days }
              }
            } as AdminApiResponse<never>, { status: 400 });
          }

          const result = await cleanupManager.archiveLogs(
            retention_days,
            resource_types,
            actionFilter
          );

          return NextResponse.json({
            success: true,
            data: {
              archive_result: result
            }
          });
        }

      case 'optimize':
        {
          const result = await cleanupManager.optimizeAuditTable();

          // Log the optimization
          await auditLogger.log(
            context.user.user_id,
            'audit.table_optimize',
            'audit_log',
            {
              details: { optimization_result: result },
              request
            }
          );

          return NextResponse.json({
            success: true,
            data: {
              optimization_result: result
            }
          });
        }

      case 'schedule_cleanup':
        {
          await cleanupManager.scheduleCleanup();

          return NextResponse.json({
            success: true,
            data: {
              message: 'Scheduled cleanup executed successfully'
            }
          });
        }

      case 'cleanup_auth_logs':
        {
          const result = await auditCleanup.cleanupAuthLogs(dry_run);

          return NextResponse.json({
            success: true,
            data: {
              cleanup_result: result,
              dry_run,
              warning: dry_run ? 'This was a dry run. No data was actually deleted.' : undefined
            }
          });
        }

      case 'cleanup_user_logs':
        {
          const result = await auditCleanup.cleanupUserLogs(dry_run);

          return NextResponse.json({
            success: true,
            data: {
              cleanup_result: result,
              dry_run,
              warning: dry_run ? 'This was a dry run. No data was actually deleted.' : undefined
            }
          });
        }

      case 'cleanup_older_than':
        {
          const { days } = body;
          
          if (!days || days < 1) {
            return NextResponse.json({
              success: false,
              error: {
                code: 'INVALID_DAYS',
                message: 'Days must be a positive number',
                details: { provided_days: days }
              }
            } as AdminApiResponse<never>, { status: 400 });
          }

          const result = await auditCleanup.cleanupOlderThan(days, dry_run);

          return NextResponse.json({
            success: true,
            data: {
              cleanup_result: result,
              dry_run,
              warning: dry_run ? 'This was a dry run. No data was actually deleted.' : undefined
            }
          });
        }

      default:
        return NextResponse.json({
          success: false,
          error: {
            code: 'INVALID_ACTION',
            message: 'Invalid cleanup action specified',
            details: { 
              provided_action: action, 
              allowed_actions: [
                'get_stats', 'cleanup', 'cleanup_default_policies', 'archive', 
                'optimize', 'schedule_cleanup', 'cleanup_auth_logs', 
                'cleanup_user_logs', 'cleanup_older_than'
              ] 
            }
          }
        } as AdminApiResponse<never>, { status: 400 });
    }

  } catch (error) {
    console.error('Audit cleanup API error:', error);
    
    return NextResponse.json({
      success: false,
      error: {
        code: 'AUDIT_CLEANUP_FAILED',
        message: 'Failed to process audit cleanup request',
        details: { error_message: error instanceof Error ? error.message : 'Unknown error' }
      }
    } as AdminApiResponse<never>, { status: 500 });
  }
});

/**
 * GET /api/admin/system/audit-logs/cleanup - Get cleanup statistics and status
 */
export const GET = requireAdmin(async (request: NextRequest, context) => {
  try {
    // Only super admins can view cleanup information
    if (!context.isSuperAdmin()) {
      return NextResponse.json({
        success: false,
        error: {
          code: 'INSUFFICIENT_PERMISSIONS',
          message: 'Audit log cleanup information requires super admin privileges',
          details: { required_role: 'super_admin', current_role: context.user.role }
        }
      } as AdminApiResponse<never>, { status: 403 });
    }

    const cleanupManager = getAuditCleanupManager();
    
    // Get cleanup and archive statistics
    const [cleanupStats, archiveStats] = await Promise.all([
      cleanupManager.getCleanupStats(),
      cleanupManager.getArchiveStats()
    ]);

    // Calculate recommendations
    const recommendations = [];
    
    if (cleanupStats.logs_to_delete > 1000) {
      recommendations.push({
        type: 'cleanup',
        priority: 'high',
        message: `${cleanupStats.logs_to_delete} logs are older than 90 days and can be cleaned up`,
        action: 'cleanup_older_than',
        parameters: { days: 90 }
      });
    }

    if (cleanupStats.total_logs > 50000) {
      recommendations.push({
        type: 'archive',
        priority: 'medium',
        message: 'Large number of audit logs detected. Consider archiving old logs.',
        action: 'archive',
        parameters: { retention_days: 365 }
      });
    }

    if (cleanupStats.oldest_log_date && cleanupStats.oldest_log_date < new Date(Date.now() - 365 * 24 * 60 * 60 * 1000)) {
      recommendations.push({
        type: 'optimize',
        priority: 'low',
        message: 'Audit table may benefit from optimization due to age of data',
        action: 'optimize',
        parameters: {}
      });
    }

    return NextResponse.json({
      success: true,
      data: {
        cleanup_stats: cleanupStats,
        archive_stats: archiveStats,
        recommendations,
        retention_policies: {
          security_events: '2 years (730 days)',
          admin_actions: '1 year (365 days)',
          user_management: '6 months (180 days)',
          authentication: '90 days',
          general: '30 days'
        }
      },
      meta: {
        message: 'Audit cleanup information retrieved successfully',
        last_updated: new Date().toISOString()
      }
    });

  } catch (error) {
    console.error('Audit cleanup GET API error:', error);
    
    return NextResponse.json({
      success: false,
      error: {
        code: 'AUDIT_CLEANUP_INFO_FAILED',
        message: 'Failed to retrieve audit cleanup information',
        details: { error_message: error instanceof Error ? error.message : 'Unknown error' }
      }
    } as AdminApiResponse<never>, { status: 500 });
  }
});