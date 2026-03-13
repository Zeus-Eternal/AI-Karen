/**
 * Audit Logs API Route
 * GET /api/admin/system/audit-logs   - Get audit logs with filtering
 * POST /api/admin/system/audit-logs  - Advanced operations (search, stats, export, user_activity, recent, compliance_export)
 *
 * Requirements: 5.1, 5.2, 5.3
 */

import { NextRequest, NextResponse } from 'next/server';
import { requireAdmin } from '@/lib/middleware/admin-auth';
import { getAuditLogger, auditLog } from '@/lib/audit/audit-logger';
import { AuditSearchParser, auditPagination } from '@/lib/audit/audit-filters';
import { getAuditLogExporter } from '@/lib/audit/audit-export';
import type { AdminApiResponse, AuditLogFilter, PaginationParams } from '@/types/admin';

/* ---------------- helpers ---------------- */

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

function parseDateSafe(v?: string | null): Date | undefined {
  if (!v) return undefined;
  const d = new Date(v);
  return Number.isNaN(d.getTime()) ? undefined : d;
}

function clamp(n: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, n));
}

/* ---------------- GET /api/admin/system/audit-logs ---------------- */

export const GET = requireAdmin(async (request: NextRequest, context) => {
  try {
    const { searchParams } = new URL(request.url);

    // Base filter
    const filter: AuditLogFilter = {
      user_id: searchParams.get('user_id') || undefined,
      action: searchParams.get('action') || undefined,
      resource_type: searchParams.get('resource_type') || undefined,
      start_date: parseDateSafe(searchParams.get('start_date')),
      end_date: parseDateSafe(searchParams.get('end_date')),
      ip_address: searchParams.get('ip_address') || undefined,
    };

    // Pagination & sorting
    const pageRaw = parseInt(searchParams.get('page') || '1', 10);
    const limitRaw = parseInt(searchParams.get('limit') || '50', 10);
    const pagination: PaginationParams = {
      page: clamp(Number.isFinite(pageRaw) ? pageRaw : 1, 1, 100000),
      limit: clamp(Number.isFinite(limitRaw) ? limitRaw : 50, 1, 200), // cap at 200/page
      sort_by: searchParams.get('sort_by') || 'timestamp',
      sort_order: (searchParams.get('sort_order') as 'asc' | 'desc') || 'desc',
    };

    // Search string -> augment filter
    const searchQuery = searchParams.get('search');
    if (searchQuery && searchQuery.trim().length > 0) {
      const parsed = AuditSearchParser.parseSearchQuery(searchQuery);
      Object.assign(filter, parsed.filters);
    }

    const auditLogger = getAuditLogger();

    // Role-based access: non-super-admins restricted
    if (!context.isSuperAdmin()) {
      // They can view their own logs.
      // If they ask for a different user, only allow certain actions.
      const requestedUserId = filter.user_id;
      if (!requestedUserId) {
        filter.user_id = context.user.user_id;
      } else if (requestedUserId !== context.user.user_id) {
        const allowedActions = new Set([
          'user.create',
          'user.update',
          'user.delete',
          'user.bulk_activate',
          'user.bulk_deactivate',
          'user.bulk_role_change',
          'user.bulk_export',
          'user.import_create',
          'user.import_completed',
        ]);
        if (!filter.action || !allowedActions.has(filter.action)) {
          return NextResponse.json(
            {
              success: false,
              error: {
                code: 'INSUFFICIENT_PERMISSIONS',
                message:
                  'Regular admins may only view their own audit logs or limited user-management actions.',
                details: {
                  requested_user_id: requestedUserId,
                  current_user_id: context.user.user_id,
                  allowed_actions: Array.from(allowedActions),
                },
              },
            } as AdminApiResponse<never>,
            noStore({ status: 403 })
          );
        }
      }
    }

    const result = await auditLogger.getAuditLogs(filter, pagination);

    // Record the view (dataExported is used system-wide for access logging)
    await auditLog.dataExported(context.user.user_id, 'audit_view', result.data.length, request);

    // Simple statistics for the current page of results (cheap)
    const action_breakdown = result.data.reduce<Record<string, number>>((acc, log) => {
      acc[log.action] = (acc[log.action] || 0) + 1;
      return acc;
    }, {});
    const resource_type_breakdown = result.data.reduce<Record<string, number>>((acc, log) => {
      acc[log.resource_type] = (acc[log.resource_type] || 0) + 1;
      return acc;
    }, {});
    const unique_users = new Set(result.data.map((l) => l.user_id)).size;
    const dateStamps = result.data.map((l) => new Date(l.timestamp).getTime()).filter((t) => !Number.isNaN(t));
    const date_range =
      dateStamps.length > 0
        ? { earliest: new Date(Math.min(...dateStamps)), latest: new Date(Math.max(...dateStamps)) }
        : null;

    const response: AdminApiResponse<
      typeof result & {
        statistics: {
          action_breakdown: Record<string, number>;
          resource_type_breakdown: Record<string, number>;
          unique_users: number;
          date_range: typeof date_range;
        };
      }
    > = {
      success: true,
      data: {
        ...result,
        statistics: {
          action_breakdown,
          resource_type_breakdown,
          unique_users,
          date_range,
        },
      },
      meta: {
        filter_applied: filter,
        pagination_applied: pagination,
        total_filtered: result.pagination.total,
        access_level: context.isSuperAdmin() ? 'full' : 'restricted',
        message: 'Audit logs retrieved successfully',
      },
    };

    return NextResponse.json(response, noStore());
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: {
          code: 'AUDIT_LOGS_RETRIEVAL_FAILED',
          message: 'Failed to retrieve audit logs',
          details: { error_message: error instanceof Error ? error.message : 'Unknown error' },
        },
      } as AdminApiResponse<never>,
      noStore({ status: 500 })
    );
  }
});

/* ---------------- POST /api/admin/system/audit-logs ---------------- */

type PostActions =
  | 'search'
  | 'stats'
  | 'export'
  | 'user_activity'
  | 'recent'
  | 'compliance_export';

export const POST = requireAdmin(async (request: NextRequest, context) => {
  try {
    const body = (await request.json()) as {
      action: PostActions;
      query?: string;
      filter?: AuditLogFilter;
      export_options?: {
        format?: 'json' | 'csv' | 'xlsx';
        filename?: string;
        fields?: string[];
        include_headers?: boolean;
      };
      pagination?: PaginationParams;
      start_date?: string;
      end_date?: string;
      target_user_id?: string;
      limit?: number;
      compliance_type?: string;
      date_range?: { start: string; end: string };
    };

    const { action } = body;
    const auditLogger = getAuditLogger();
    const exporter = getAuditLogExporter();

    switch (action) {
      case 'search': {
        const query = body.query || '';
        const pg = body.pagination || auditPagination.default();
        // Hard caps
        pg.page = clamp(pg.page || 1, 1, 100000);
        pg.limit = clamp(pg.limit || 50, 1, 200);

        const searchResult = await auditLogger.searchAuditLogs(query, pg);

        await auditLogger.log(context.user.user_id, 'audit.log_view', 'audit_log', {
          details: { search_query: query, results_count: searchResult.data.length },
          request,
        });

        return NextResponse.json(
          {
            success: true,
            data: searchResult,
          } as AdminApiResponse<typeof searchResult>,
          noStore()
        );
      }

      case 'stats': {
        const start = parseDateSafe(body.start_date);
        const end = parseDateSafe(body.end_date);

        const stats = await auditLogger.getAuditLogStats(start, end);

        return NextResponse.json(
          {
            success: true,
            data: stats,
          } as AdminApiResponse<typeof stats>,
          noStore()
        );
      }

      case 'export': {
        const exportFormat = body.export_options?.format || 'json';
        if (!['json', 'csv', 'xlsx'].includes(exportFormat)) {
          return NextResponse.json(
            {
              success: false,
              error: {
                code: 'INVALID_EXPORT_FORMAT',
                message: 'Invalid export format',
                details: { provided_format: exportFormat, allowed_formats: ['json', 'csv', 'xlsx'] },
              },
            } as AdminApiResponse<never>,
            noStore({ status: 400 })
          );
        }

        // Enforce access for non-super admins
        const exportFilter: AuditLogFilter = body.filter || {};
        if (!context.isSuperAdmin()) {
          exportFilter.user_id = context.user.user_id;
        }

          const exportResult = await exporter.exportLogs({
            format: exportFormat as 'json' | 'csv' | 'xlsx',
            filter: exportFilter,
            filename: body.export_options?.filename,
            fields: body.export_options?.fields,
            includeHeaders: body.export_options?.include_headers,
            maxRecords: 10_000, // safety cap
          });

        if (!exportResult.success) {
          return NextResponse.json(
            {
              success: false,
              error: {
                code: 'EXPORT_FAILED',
                message: exportResult.error || 'Export failed',
                details: { export_format: exportFormat },
              },
            } as AdminApiResponse<never>,
            noStore({ status: 500 })
          );
        }

        await auditLog.dataExported(
          context.user.user_id,
          exportFormat,
          exportResult.recordCount,
          request
        );

        return NextResponse.json(
          {
            success: true,
            data: {
              export: {
                filename: exportResult.filename,
                record_count: exportResult.recordCount,
                file_size: exportResult.fileSize,
                format: exportFormat,
              },
            },
          } as AdminApiResponse<{
            export: { filename: string; record_count: number; file_size: number; format: string };
          }>,
          noStore()
        );
      }

      case 'user_activity': {
        const targetId = context.isSuperAdmin() ? body.target_user_id : context.user.user_id;
        if (!targetId) {
          return NextResponse.json(
            {
              success: false,
              error: {
                code: 'VALIDATION_ERROR',
                message: 'target_user_id is required for user_activity',
              },
            } as AdminApiResponse<never>,
            noStore({ status: 400 })
          );
        }

        const pg = body.pagination || auditPagination.default();
        pg.page = clamp(pg.page || 1, 1, 100000);
        pg.limit = clamp(pg.limit || 50, 1, 200);

        const userLogs = await auditLogger.getUserAuditLogs(targetId, pg);

        return NextResponse.json(
          {
            success: true,
            data: userLogs,
          } as AdminApiResponse<typeof userLogs>,
          noStore()
        );
      }

      case 'recent': {
        const limit = clamp(body.limit ?? 100, 1, 500);
        const recentLogs = await auditLogger.getRecentAuditLogs(limit);

        return NextResponse.json(
          {
            success: true,
            data: recentLogs,
          } as AdminApiResponse<typeof recentLogs>,
          noStore()
        );
      }

      case 'compliance_export': {
        if (!context.isSuperAdmin()) {
          return NextResponse.json(
            {
              success: false,
              error: {
                code: 'INSUFFICIENT_PERMISSIONS',
                message: 'Compliance exports require super admin privileges',
                details: { required_role: 'super_admin', current_role: context.user.role },
              },
            } as AdminApiResponse<never>,
            noStore({ status: 403 })
          );
        }

          const complianceTypeInput =
            typeof body.compliance_type === 'string' ? body.compliance_type.toUpperCase() : 'SOX';
          const allowedComplianceTypes = ['SOX', 'GDPR', 'HIPAA', 'PCI_DSS'] as const;
          if (!allowedComplianceTypes.includes(complianceTypeInput as typeof allowedComplianceTypes[number])) {
            return NextResponse.json(
              {
                success: false,
                error: {
                  code: 'INVALID_COMPLIANCE_TYPE',
                  message: 'Invalid compliance export type',
                  details: { provided_type: body.compliance_type, allowed: allowedComplianceTypes },
                },
              } as AdminApiResponse<never>,
              noStore({ status: 400 }),
            );
          }
          const complianceType = complianceTypeInput as (typeof allowedComplianceTypes)[number];
          const range = body.date_range
            ? {
                start_date: parseDateSafe(body.date_range.start),
                end_date: parseDateSafe(body.date_range.end),
              }
          : undefined;

        const exportResult = await getAuditLogExporter().exportForCompliance(
          complianceType,
          range
        );

        if (!exportResult.success) {
          return NextResponse.json(
            {
              success: false,
              error: {
                code: 'COMPLIANCE_EXPORT_FAILED',
                message: exportResult.error || 'Compliance export failed',
                details: { compliance_type: complianceType },
              },
            } as AdminApiResponse<never>,
            noStore({ status: 500 })
          );
        }

        await getAuditLogger().log(context.user.user_id, 'audit.compliance_export', 'audit_log', {
          details: {
            compliance_type: complianceType,
            record_count: exportResult.recordCount,
            date_range: body.date_range || null,
          },
          request,
        });

        return NextResponse.json(
          {
            success: true,
            data: {
              export: {
                filename: exportResult.filename,
                record_count: exportResult.recordCount,
                file_size: exportResult.fileSize,
                compliance_type: complianceType,
              },
            },
          } as AdminApiResponse<{
            export: {
              filename: string;
              record_count: number;
              file_size: number;
              compliance_type: string;
            };
          }>,
          noStore()
        );
      }

      default:
        return NextResponse.json(
          {
            success: false,
            error: {
              code: 'INVALID_ACTION',
              message: 'Invalid action specified',
              details: {
                provided_action: action,
                allowed_actions: ['search', 'stats', 'export', 'user_activity', 'recent', 'compliance_export'],
              },
            },
          } as AdminApiResponse<never>,
          noStore({ status: 400 })
        );
    }
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: {
          code: 'AUDIT_LOGS_OPERATION_FAILED',
          message: 'Failed to process audit logs request',
          details: { error_message: error instanceof Error ? error.message : 'Unknown error' },
        },
      } as AdminApiResponse<never>,
      noStore({ status: 500 })
    );
  }
});
