/**
 * Audit Logs API Route
 * GET /api/admin/system/audit-logs - Get audit logs with filtering
 * POST /api/admin/system/audit-logs - Export audit logs and advanced operations
 * 
 * Requirements: 5.1, 5.2, 5.3
 */
import { NextRequest, NextResponse } from 'next/server';
import { requireAdmin } from '@/lib/middleware/admin-auth';
import { getAdminDatabaseUtils } from '@/lib/database/admin-utils';
import { getAuditLogger, auditLog } from '@/lib/audit/audit-logger';
import { AuditSearchParser, auditPagination } from '@/lib/audit/audit-filters';
import { getAuditLogExporter } from '@/lib/audit/audit-export';
import type {  AdminApiResponse, AuditLogFilter, PaginationParams } from '@/types/admin';
/**
 * GET /api/admin/system/audit-logs - Get audit logs with filtering
 */
export const GET = requireAdmin(async (request: NextRequest, context) => {
  try {
    const { searchParams } = new URL(request.url);
    // Parse filter parameters
    const filter: AuditLogFilter = {
      user_id: searchParams.get('user_id') || undefined,
      action: searchParams.get('action') || undefined,
      resource_type: searchParams.get('resource_type') || undefined,
      start_date: searchParams.get('start_date') ? new Date(searchParams.get('start_date')!) : undefined,
      end_date: searchParams.get('end_date') ? new Date(searchParams.get('end_date')!) : undefined,
      ip_address: searchParams.get('ip_address') || undefined,
    };
    // Parse pagination parameters
    const pagination: PaginationParams = {
      page: parseInt(searchParams.get('page') || '1'),
      limit: Math.min(parseInt(searchParams.get('limit') || '50'), 200), // Max 200 per page for audit logs
      sort_by: searchParams.get('sort_by') || 'timestamp',
      sort_order: (searchParams.get('sort_order') as 'asc' | 'desc') || 'desc'
    };
    // Handle search query parsing
    const searchQuery = searchParams.get('search');
    if (searchQuery) {
      const parsed = AuditSearchParser.parseSearchQuery(searchQuery);
      Object.assign(filter, parsed.filters);
    }
    const auditLogger = getAuditLogger();
    // Non-super admins have restricted access to audit logs
    if (!context.isSuperAdmin()) {
      // Regular admins can only see their own actions and user management actions
      if (!filter.user_id) {
        filter.user_id = context.user.user_id;
      } else if (filter.user_id !== context.user.user_id) {
        // Check if requesting logs for user management actions only
        const allowedActions = ['user.create', 'user.update', 'user.delete', 'user.bulk_activate', 'user.bulk_deactivate'];
        if (!filter.action || !allowedActions.includes(filter.action)) {
          return NextResponse.json({
            success: false,
            error: {
              code: 'INSUFFICIENT_PERMISSIONS',
              message: 'Regular admins can only view their own audit logs or user management actions',
              details: { 
                requested_user_id: filter.user_id,
                current_user_id: context.user.user_id,
                allowed_actions: allowedActions
              }
            }
          } as AdminApiResponse<never>, { status: 403 });
        }
      }
    }
    const result = await auditLogger.getAuditLogs(filter, pagination);
    // Log the audit log access
    await auditLog.dataExported(
      context.user.user_id,
      'audit_view',
      result.data.length,
      request
    );
    // Get action statistics for the current filter
    const actionStats = result.data.reduce((acc, log) => {
      acc[log.action] = (acc[log.action] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    // Get resource type statistics
    const resourceStats = result.data.reduce((acc, log) => {
      acc[log.resource_type] = (acc[log.resource_type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    // Get unique users in the result set
    const uniqueUsers = Array.from(
      new Set(result.data.map(log => log.user_id))
    ).length;
    // Get date range of results
    const dates = result.data.map(log => new Date(log.timestamp).getTime());
    const dateRange = dates.length > 0 ? {
      earliest: new Date(Math.min(...dates)),
      latest: new Date(Math.max(...dates))
    } : null;
    const response: AdminApiResponse<typeof result & {
      statistics: {
        action_breakdown: Record<string, number>;
        resource_type_breakdown: Record<string, number>;
        unique_users: number;
        date_range: typeof dateRange;
      };
    }> = {
      success: true,
      data: {
        ...result,
        statistics: {
          action_breakdown: actionStats,
          resource_type_breakdown: resourceStats,
          unique_users: uniqueUsers,
          date_range: dateRange
        }
      },
      meta: {
        filter_applied: filter,
        pagination_applied: pagination,
        total_filtered: result.pagination.total,
        access_level: context.isSuperAdmin() ? 'full' : 'restricted',
        message: 'Audit logs retrieved successfully'
      }
    };
    return NextResponse.json(response);
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: {
        code: 'AUDIT_LOGS_RETRIEVAL_FAILED',
        message: 'Failed to retrieve audit logs',
        details: { error_message: error instanceof Error ? error.message : 'Unknown error' }
      }
    } as AdminApiResponse<never>, { status: 500 });
  }

/**
 * POST /api/admin/system/audit-logs - Advanced audit log operations
 */
export const POST = requireAdmin(async (request: NextRequest, context) => {
  try {
    const body = await request.json();
    const { action, filter, export_options, pagination } = body;
    const auditLogger = getAuditLogger();
    const exporter = getAuditLogExporter();
    switch (action) {
      case 'search':
        {
          const { query } = body;
          const searchResult = await auditLogger.searchAuditLogs(
            query,
            pagination || auditPagination.default()
          );
          // Log the search action
          await auditLogger.log(
            context.user.user_id,
            'audit.log_view',
            'audit_log',
            {
              details: { search_query: query, results_count: searchResult.data.length },
              request
            }
          );
          return NextResponse.json({
            success: true,
            data: searchResult

        }
      case 'stats':
        {
          const { start_date, end_date } = body;
          const stats = await auditLogger.getAuditLogStats(
            start_date ? new Date(start_date) : undefined,
            end_date ? new Date(end_date) : undefined
          );
          return NextResponse.json({
            success: true,
            data: stats

        }
      case 'export':
        {
          // Validate export format
          const exportFormat = export_options?.format || 'json';
          if (!['json', 'csv', 'xlsx'].includes(exportFormat)) {
            return NextResponse.json({
              success: false,
              error: {
                code: 'INVALID_EXPORT_FORMAT',
                message: 'Invalid export format',
                details: { provided_format: exportFormat, allowed_formats: ['json', 'csv', 'xlsx'] }
              }
            } as AdminApiResponse<never>, { status: 400 });
          }
          // Apply access restrictions for non-super admins
          let exportFilter = filter || {};
          if (!context.isSuperAdmin()) {
            exportFilter.user_id = context.user.user_id;
          }
          const exportResult = await exporter.exportLogs({
            format: exportFormat,
            filter: exportFilter,
            ...export_options,
            maxRecords: 10000 // Limit exports to 10k records

          if (!exportResult.success) {
            return NextResponse.json({
              success: false,
              error: {
                code: 'EXPORT_FAILED',
                message: exportResult.error || 'Export failed',
                details: { export_format: exportFormat }
              }
            } as AdminApiResponse<never>, { status: 500 });
          }
          // Log the export action
          await auditLog.dataExported(
            context.user.user_id,
            exportFormat,
            exportResult.recordCount,
            request
          );
          return NextResponse.json({
            success: true,
            data: {
              export: {
                filename: exportResult.filename,
                record_count: exportResult.recordCount,
                file_size: exportResult.fileSize,
                format: exportFormat
              }
            }

        }
      case 'user_activity':
        {
          const { target_user_id } = body;
          // Non-super admins can only view their own activity
          const userId = context.isSuperAdmin() ? target_user_id : context.user.user_id;
          const userLogs = await auditLogger.getUserAuditLogs(
            userId,
            pagination || auditPagination.default()
          );
          return NextResponse.json({
            success: true,
            data: userLogs

        }
      case 'recent':
        {
          const { limit = 100 } = body;
          const recentLogs = await auditLogger.getRecentAuditLogs(Math.min(limit, 500));
          return NextResponse.json({
            success: true,
            data: recentLogs

        }
      case 'compliance_export':
        {
          const { compliance_type, date_range } = body;
          if (!context.isSuperAdmin()) {
            return NextResponse.json({
              success: false,
              error: {
                code: 'INSUFFICIENT_PERMISSIONS',
                message: 'Compliance exports require super admin privileges',
                details: { required_role: 'super_admin', current_role: context.user.role }
              }
            } as AdminApiResponse<never>, { status: 403 });
          }
          const exportResult = await exporter.exportForCompliance(
            compliance_type,
            date_range ? {
              start_date: new Date(date_range.start),
              end_date: new Date(date_range.end)
            } : undefined
          );
          if (!exportResult.success) {
            return NextResponse.json({
              success: false,
              error: {
                code: 'COMPLIANCE_EXPORT_FAILED',
                message: exportResult.error || 'Compliance export failed',
                details: { compliance_type }
              }
            } as AdminApiResponse<never>, { status: 500 });
          }
          // Log the compliance export
          await auditLogger.log(
            context.user.user_id,
            'audit.compliance_export',
            'audit_log',
            {
              details: {
                compliance_type,
                record_count: exportResult.recordCount,
                date_range
              },
              request
            }
          );
          return NextResponse.json({
            success: true,
            data: {
              export: {
                filename: exportResult.filename,
                record_count: exportResult.recordCount,
                file_size: exportResult.fileSize,
                compliance_type
              }
            }

        }
      default:
        return NextResponse.json({
          success: false,
          error: {
            code: 'INVALID_ACTION',
            message: 'Invalid action specified',
            details: { provided_action: action, allowed_actions: ['search', 'stats', 'export', 'user_activity', 'recent', 'compliance_export'] }
          }
        } as AdminApiResponse<never>, { status: 400 });
    }
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: {
        code: 'AUDIT_LOGS_OPERATION_FAILED',
        message: 'Failed to process audit logs request',
        details: { error_message: error instanceof Error ? error.message : 'Unknown error' }
      }
    } as AdminApiResponse<never>, { status: 500 });
  }
