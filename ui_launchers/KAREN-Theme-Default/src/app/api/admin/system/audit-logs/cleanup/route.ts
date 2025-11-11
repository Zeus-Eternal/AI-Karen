/**
 * Audit Log Cleanup API Route
 * POST /api/admin/system/audit-logs/cleanup  - Manage audit log cleanup & retention
 * GET  /api/admin/system/audit-logs/cleanup  - Cleanup stats, archive stats, and recommendations
 *
 * Requirements: 5.1, 5.2, 5.3
 */

import { NextRequest, NextResponse } from 'next/server';
import { requireAdmin } from '@/lib/middleware/admin-auth';
import { getAuditCleanupManager, auditCleanup } from '@/lib/audit/audit-cleanup';
import { getAuditLogger } from '@/lib/audit/audit-logger';
import type { AdminApiResponse } from '@/types/admin';

/* ---------------- utilities ---------------- */

function noStore(init?: ResponseInit): ResponseInit {
  return {
    ...(init || {}),
    headers: {
      ...(init?.headers || {}),
      'Cache-Control': 'no-cache, no-store, must-revalidate',
      'Pragma': 'no-cache',
      'Expires': '0',
      'Content-Type': 'application/json; charset=utf-8',
    },
  };
}

function isStringArray(x: unknown): x is string[] {
  return Array.isArray(x) && x.every((v) => typeof v === 'string');
}

function parsePositiveInt(x: unknown): number | undefined {
  const n = typeof x === 'string' ? parseInt(x, 10) : typeof x === 'number' ? x : NaN;
  if (!Number.isFinite(n) || n <= 0) return undefined;
  return Math.floor(n);
}

function boolOrDefault(x: unknown, def: boolean): boolean {
  if (typeof x === 'boolean') return x;
  if (typeof x === 'string') {
    const v = x.toLowerCase().trim();
    if (v === 'true') return true;
    if (v === 'false') return false;
  }
  return def;
}

/* ---------------- POST /cleanup ---------------- */

type CleanupActions =
  | 'get_stats'
  | 'cleanup'
  | 'cleanup_default_policies'
  | 'archive'
  | 'optimize'
  | 'schedule_cleanup'
  | 'cleanup_auth_logs'
  | 'cleanup_user_logs'
  | 'cleanup_older_than';

export const POST = requireAdmin(async (request: NextRequest, context) => {
  try {
    // Super-admin only
    if (!context.isSuperAdmin()) {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'INSUFFICIENT_PERMISSIONS',
            message: 'Audit log cleanup requires super admin privileges',
            details: { required_role: 'super_admin', current_role: context.user.role },
          },
        } as AdminApiResponse<never>,
        noStore({ status: 403 })
      );
    }

    const raw = await request.json();
    const action = String(raw?.action || '');
    const dry_run = boolOrDefault(raw?.dry_run, true);

    // Common optional filters
    const retention_days = parsePositiveInt(raw?.retention_days);
    const resource_types = isStringArray(raw?.resource_types) ? raw.resource_types : undefined;
    const actionFilter = isStringArray(raw?.actions) ? raw.actions : undefined;

    const cleanupManager = getAuditCleanupManager();
    const auditLogger = getAuditLogger();

    switch (action as CleanupActions) {
      case 'get_stats': {
        const [stats, archiveStats] = await Promise.all([
          cleanupManager.getCleanupStats(),
          cleanupManager.getArchiveStats(),
        ]);
        return NextResponse.json(
          {
            success: true,
            data: { cleanup_stats: stats, archive_stats: archiveStats },
          } as AdminApiResponse<any>,
          noStore()
        );
      }

      case 'cleanup': {
        if (!retention_days) {
          return NextResponse.json(
            {
              success: false,
              error: {
                code: 'INVALID_RETENTION_DAYS',
                message: 'Retention days must be a positive number',
                details: { provided_retention_days: raw?.retention_days },
              },
            } as AdminApiResponse<never>,
            noStore({ status: 400 })
          );
        }

        const result = await cleanupManager.cleanupLogs(
          retention_days,
          resource_types,
          actionFilter,
          dry_run
        );

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
              result,
            },
            request,
          }
        );

        return NextResponse.json(
          {
            success: true,
            data: {
              cleanup_result: result,
              dry_run,
              warning: dry_run ? 'This was a dry run. No data was actually deleted.' : undefined,
            },
          } as AdminApiResponse<any>,
          noStore()
        );
      }

      case 'cleanup_default_policies': {
        const results = await cleanupManager.cleanupWithDefaultPolicies(dry_run);

        await auditLogger.log(
          context.user.user_id,
          dry_run ? 'audit.policy_cleanup_preview' : 'audit.policy_cleanup_execute',
          'audit_log',
          {
            details: {
              dry_run,
              policy_results: results,
              total_deleted: results.reduce((sum: number, r: unknown) => sum + (r.deleted_count || 0), 0),
            },
            request,
          }
        );

        return NextResponse.json(
          {
            success: true,
            data: {
              policy_results: results,
              dry_run,
              total_deleted: results.reduce((sum: number, r: unknown) => sum + (r.deleted_count || 0), 0),
              warning: dry_run ? 'This was a dry run. No data was actually deleted.' : undefined,
            },
          } as AdminApiResponse<any>,
          noStore()
        );
      }

      case 'archive': {
        if (!retention_days) {
          return NextResponse.json(
            {
              success: false,
              error: {
                code: 'INVALID_RETENTION_DAYS',
                message: 'Retention days must be a positive number',
                details: { provided_retention_days: raw?.retention_days },
              },
            } as AdminApiResponse<never>,
            noStore({ status: 400 })
          );
        }

        const result = await cleanupManager.archiveLogs(retention_days, resource_types, actionFilter);

        return NextResponse.json(
          {
            success: true,
            data: { archive_result: result },
          } as AdminApiResponse<any>,
          noStore()
        );
      }

      case 'optimize': {
        const result = await cleanupManager.optimizeAuditTable();

        await auditLogger.log(context.user.user_id, 'audit.table_optimize', 'audit_log', {
          details: { optimization_result: result },
          request,
        });

        return NextResponse.json(
          {
            success: true,
            data: { optimization_result: result },
          } as AdminApiResponse<any>,
          noStore()
        );
      }

      case 'schedule_cleanup': {
        await cleanupManager.scheduleCleanup();
        return NextResponse.json(
          {
            success: true,
            data: { message: 'Scheduled cleanup executed successfully' },
          } as AdminApiResponse<{ message: string }>,
          noStore()
        );
      }

      case 'cleanup_auth_logs': {
        const result = await auditCleanup.cleanupAuthLogs(dry_run);
        return NextResponse.json(
          {
            success: true,
            data: {
              cleanup_result: result,
              dry_run,
              warning: dry_run ? 'This was a dry run. No data was actually deleted.' : undefined,
            },
          } as AdminApiResponse<any>,
          noStore()
        );
      }

      case 'cleanup_user_logs': {
        const result = await auditCleanup.cleanupUserLogs(dry_run);
        return NextResponse.json(
          {
            success: true,
            data: {
              cleanup_result: result,
              dry_run,
              warning: dry_run ? 'This was a dry run. No data was actually deleted.' : undefined,
            },
          } as AdminApiResponse<any>,
          noStore()
        );
      }

      case 'cleanup_older_than': {
        const days = parsePositiveInt(raw?.days);
        if (!days) {
          return NextResponse.json(
            {
              success: false,
              error: {
                code: 'INVALID_DAYS',
                message: 'Days must be a positive number',
                details: { provided_days: raw?.days },
              },
            } as AdminApiResponse<never>,
            noStore({ status: 400 })
          );
        }

        const result = await auditCleanup.cleanupOlderThan(days, dry_run);
        return NextResponse.json(
          {
            success: true,
            data: {
              cleanup_result: result,
              dry_run,
              warning: dry_run ? 'This was a dry run. No data was actually deleted.' : undefined,
            },
          } as AdminApiResponse<any>,
          noStore()
        );
      }

      default: {
        return NextResponse.json(
          {
            success: false,
            error: {
              code: 'INVALID_ACTION',
              message: 'Invalid cleanup action specified',
              details: {
                provided_action: action,
                allowed_actions: [
                  'get_stats',
                  'cleanup',
                  'cleanup_default_policies',
                  'archive',
                  'optimize',
                  'schedule_cleanup',
                  'cleanup_auth_logs',
                  'cleanup_user_logs',
                  'cleanup_older_than',
                ],
              },
            },
          } as AdminApiResponse<never>,
          noStore({ status: 400 })
        );
      }
    }
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: {
          code: 'AUDIT_CLEANUP_FAILED',
          message: 'Failed to process audit cleanup request',
          details: { error_message: error instanceof Error ? error.message : 'Unknown error' },
        },
      } as AdminApiResponse<never>,
      noStore({ status: 500 })
    );
  }
});

/* ---------------- GET /cleanup ---------------- */

export const GET = requireAdmin(async (request: NextRequest, context) => {
  try {
    // Super-admin only
    if (!context.isSuperAdmin()) {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'INSUFFICIENT_PERMISSIONS',
            message: 'Audit log cleanup information requires super admin privileges',
            details: { required_role: 'super_admin', current_role: context.user.role },
          },
        } as AdminApiResponse<never>,
        noStore({ status: 403 })
      );
    }

    const cleanupManager = getAuditCleanupManager();
    const [cleanupStats, archiveStats] = await Promise.all([
      cleanupManager.getCleanupStats(),
      cleanupManager.getArchiveStats(),
    ]);

    // lightweight recommendations
    const recommendations: Array<{
      type: 'cleanup' | 'archive' | 'optimize';
      priority: 'low' | 'medium' | 'high';
      message: string;
      action: CleanupActions | 'archive';
      parameters: Record<string, unknown>;
    }> = [];

    if (cleanupStats.logs_to_delete > 1000) {
      recommendations.push({
        type: 'cleanup',
        priority: 'high',
        message: `${cleanupStats.logs_to_delete} logs are older than 90 days and can be cleaned up`,
        action: 'cleanup_older_than',
        parameters: { days: 90 },
      });
    }

    if (cleanupStats.total_logs > 50_000) {
      recommendations.push({
        type: 'archive',
        priority: 'medium',
        message: 'Large number of audit logs detected. Consider archiving old logs.',
        action: 'archive',
        parameters: { retention_days: 365 },
      });
    }

    if (
      cleanupStats.oldest_log_date &&
      new Date(cleanupStats.oldest_log_date).getTime() <
        Date.now() - 365 * 24 * 60 * 60 * 1000
    ) {
      recommendations.push({
        type: 'optimize',
        priority: 'low',
        message: 'Audit table may benefit from optimization due to age of data',
        action: 'optimize',
        parameters: {},
      });
    }

    return NextResponse.json(
      {
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
            general: '30 days',
          },
        },
        meta: {
          message: 'Audit cleanup information retrieved successfully',
          last_updated: new Date().toISOString(),
        },
      } as AdminApiResponse<any>,
      noStore()
    );
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: {
          code: 'AUDIT_CLEANUP_INFO_FAILED',
          message: 'Failed to retrieve audit cleanup information',
          details: { error_message: error instanceof Error ? error.message : 'Unknown error' },
        },
      } as AdminApiResponse<never>,
      noStore({ status: 500 })
    );
  }
});
