/**
 * Admin Performance Report API (Prod-Grade)
 *
 * GET  /api/admin/performance/report?format=json|csv&include_db_stats=true|false&recommendations=true|false
 * POST /api/admin/performance/report           (ingest external perf snapshots)
 * DELETE /api/admin/performance/report         (clear in-memory perf metrics)
 *
 * - Auth: withAdminAuth + granular permissions
 * - Observability: audit logs on success/failure, duration, size
 * - Security: no-store, nosniff, CSP, frame deny
 * - CSV export: file attachment
 * - Recommendations: heuristic triage on hot spots
 */

import { NextRequest, NextResponse } from 'next/server';
import { withAdminAuth, type AdminAuthContext } from '@/lib/middleware/admin-auth';
import { adminPerformanceMonitor, PerformanceReporter } from '@/lib/performance/admin-performance-monitor';
import { getQueryOptimizer } from '@/lib/database/query-optimizer';
import { getAuditLogger } from '@/lib/audit/audit-logger';
import type { PerformanceReport } from '@/types/admin';

export const dynamic = 'force-dynamic';

type ReportFormat = 'json' | 'csv';

const SECURITY_HEADERS = {
  'Cache-Control': 'no-store',
  'X-Content-Type-Options': 'nosniff',
  'Content-Security-Policy': "default-src 'none'",
  'X-Frame-Options': 'DENY',
} as const;

function ipFrom(req: NextRequest): string {
  return (
    req.headers.get('x-forwarded-for') ||
    req.headers.get('x-real-ip') ||
    'unknown'
  );
}

function byteLengthOf(obj: unknown): number {
  try {
    return Buffer.byteLength(JSON.stringify(obj), 'utf8');
  } catch {
    return 0;
  }
}

async function auditSuccess(
  request: NextRequest,
  event: string,
  details: Record<string, unknown>,
  userId?: string
) {
  try {
    const audit = getAuditLogger();
    await audit.log(userId ?? 'unknown', event, 'admin_performance_report', {
      details,
      request,
      ip_address: ipFrom(request),
    });
  } catch {
    // swallow audit failures
  }
}

async function auditError(
  request: NextRequest,
  message: string,
  userId?: string
) {
  try {
    const audit = getAuditLogger();
    await audit.log(userId ?? 'unknown', 'admin.performance.report.error', 'admin_performance_report', {
      details: { message },
      request,
      ip_address: ipFrom(request),
    });
  } catch {
    // swallow audit failures
  }
}

/** Build heuristic recommendations from a PerformanceReport */
function buildRecommendations(report: PerformanceReport) {
  const recs: Array<{
    priority: 'low' | 'medium' | 'high' | 'critical';
    area: string;
    title: string;
    description: string;
    action: string;
  }> = [];

  // API latency triage
  if (report.api?.avgResponseTime >= 2000) {
    recs.push({
      priority: 'high',
      area: 'api',
      title: 'Elevated API Latency',
      description: `Average response time at ${report.api.avgResponseTime}ms indicates saturation or N+1.`,
      action: 'Enable query caching, profile hot endpoints, add p95/p99 SLOs & backpressure.',
    });
  }
  if (report.api?.errorRate && report.api.errorRate > 0.02) {
    recs.push({
      priority: 'high',
      area: 'api',
      title: 'High API Error Rate',
      description: `Error rate ${(report.api.errorRate * 100).toFixed(2)}% exceeds 2% budget.`,
      action: 'Inspect error taxonomy, circuit-breakers, and recent deploy diff.',
    });
  }

  // DB signals
  if (report.database?.slowQueries && report.database.slowQueries > 10) {
    recs.push({
      priority: 'high',
      area: 'database',
      title: 'Excess Slow Queries',
      description: `${report.database.slowQueries} slow queries detected.`,
      action: 'Add indexes, analyze EXPLAIN plans, enable prepared statements & caching.',
    });
  }
  if (report.database?.connections?.poolUtilization && report.database.connections.poolUtilization > 0.8) {
    recs.push({
      priority: 'medium',
      area: 'database',
      title: 'High Pool Utilization',
      description: `Pool utilization ${(report.database.connections.poolUtilization * 100).toFixed(0)}%.`,
      action: 'Increase pool size cautiously, add connection reuse, and audit long transactions.',
    });
  }

  // Cache layer
  if (report.cache?.hitRate !== undefined && report.cache.hitRate < 0.85) {
    recs.push({
      priority: 'medium',
      area: 'cache',
      title: 'Low Cache Hit Rate',
      description: `Hit rate ${(report.cache.hitRate * 100).toFixed(1)}% < target 90%.`,
      action: 'Warm critical keys, align TTLs, co-locate cache with app nodes.',
    });
  }

  // Worker / Background
  if (report.jobs?.backlog && report.jobs.backlog > 100) {
    recs.push({
      priority: 'medium',
      area: 'jobs',
      title: 'Job Backlog Growing',
      description: `Backlog at ${report.jobs.backlog}.`,
      action: 'Scale workers horizontally, add priority queues, and retry/JDL policies.',
    });
  }

  // Frontend SSR
  if (report.frontend?.ssr?.avgRenderMs && report.frontend.ssr.avgRenderMs > 1200) {
    recs.push({
      priority: 'low',
      area: 'frontend',
      title: 'Slow SSR Renders',
      description: `SSR avg ${report.frontend.ssr.avgRenderMs}ms.`,
      action: 'Memoize server components, reduce waterfall fetches, and enable partial revalidation.',
    });
  }

  return recs;
}

/** Export a CSV from the in-memory metrics snapshot */
function exportCSV(report: PerformanceReport, recommendations: ReturnType<typeof buildRecommendations>) {
  const esc = (v: unknown) => {
    const s = String(v ?? '');
    return (s.includes('"') || s.includes(',') || s.includes('\n')) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const lines: string[] = [];

  lines.push(`Generated,${esc(new Date().toISOString())}`);
  lines.push('');

  // API
  if (report.api) {
    lines.push('API METRICS');
    lines.push('Metric,Value');
    lines.push(`avgResponseTime(ms),${esc(report.api.avgResponseTime)}`);
    lines.push(`p95(ms),${esc(report.api.p95)}`);
    lines.push(`p99(ms),${esc(report.api.p99)}`);
    lines.push(`rps,${esc(report.api.rps)}`);
    lines.push(`errorRate,${esc(report.api.errorRate)}`);
    lines.push('');
  }

  // Database
  if (report.database) {
    lines.push('DATABASE METRICS');
    lines.push('Metric,Value');
    lines.push(`slowQueries,${esc(report.database.slowQueries)}`);
    lines.push(`avgQueryTime(ms),${esc(report.database.avgQueryTimeMs)}`);
    lines.push(`poolUtilization,${esc(report.database.connections?.poolUtilization)}`);
    lines.push('');
  }

  // Cache
    if (report.cache) {
      lines.push('CACHE METRICS');
      lines.push('Metric,Value');
      lines.push(`hitRate,${esc(report.cache.hitRate)}`);
      lines.push(`evictionRate,${esc(report.cache.evictionRate)}`);
      lines.push('');
    }

  // Jobs
    if (report.jobs) {
      lines.push('JOB METRICS');
      lines.push('Metric,Value');
      lines.push(`backlog,${esc(report.jobs.backlog)}`);
      lines.push(`processed,${esc(report.jobs.processed)}`);
      lines.push('');
    }

  // Frontend
    if (report.frontend?.ssr) {
      lines.push('FRONTEND SSR');
      lines.push('Metric,Value');
      lines.push(`avgRenderMs,${esc(report.frontend.ssr.avgRenderMs)}`);
      lines.push(`p95Ms,${esc(report.frontend.ssr.p95)}`);
      lines.push('');
    }

  // Recommendations
  if (recommendations?.length) {
    lines.push('RECOMMENDATIONS');
    lines.push('Priority,Area,Title,Description,Action');
    for (const r of recommendations) {
      lines.push([esc(r.priority), esc(r.area), esc(r.title), esc(r.description), esc(r.action)].join(','));
    }
  }

  return lines.join('\n');
}

async function handleGET(request: NextRequest, context: AdminAuthContext) {
  const startedAt = Date.now();
  const userId = context.user?.user_id ?? 'unknown';

  try {
    const { searchParams } = new URL(request.url);
    const formatParam = (searchParams.get('format') || 'json').toLowerCase();
    const format: ReportFormat = formatParam === 'csv' ? 'csv' : 'json';
    const includeRecommendations = searchParams.get('recommendations') !== 'false';
    const includeDbStats = searchParams.get('include_db_stats') === 'true';

    // Snapshot current metrics
    const report: PerformanceReport = PerformanceReporter.generateReport();

    // Optional DB analysis
    if (includeDbStats) {
      try {
        const queryOptimizer = getQueryOptimizer();
        const [queryPerformance, tableStats] = await Promise.all([
          queryOptimizer.getQueryPerformanceAnalysis(),
          queryOptimizer.getTableStatistics(),
        ]);
        (report as unknown).database_analysis = {
          query_performance: queryPerformance,
          table_statistics: tableStats,
        };
      } catch {
        // If DB analysis fails, we still return base report
        (report as unknown).database_analysis = { error: 'db_analysis_failed' };
      }
    }

    const recommendations = includeRecommendations ? buildRecommendations(report) : [];

    // CSV path
    if (format === 'csv') {
      const csvData =
        typeof (PerformanceReporter as unknown).exportMetrics === 'function'
          ? (PerformanceReporter as unknown).exportMetrics('csv')
          : exportCSV(report, recommendations);

      const filename = `admin-performance-report-${new Date().toISOString().split('T')[0]}.csv`;
      await auditSuccess(request, 'admin.performance.report.generate', {
        format,
        durationMs: Date.now() - startedAt,
        sizeBytes: Buffer.byteLength(csvData, 'utf8'),
      }, userId);

      return new NextResponse(csvData, {
        headers: {
          ...SECURITY_HEADERS,
          'Content-Type': 'text/csv; charset=utf-8',
          'Content-Disposition': `attachment; filename="${filename}"`,
        },
      });
    }

    // JSON path
    const payload = {
      success: true,
      data: report,
      recommendations,
      timestamp: new Date().toISOString(),
    };

    await auditSuccess(request, 'admin.performance.report.generate', {
      format,
      durationMs: Date.now() - startedAt,
      sizeBytes: byteLengthOf(payload),
    }, userId);

    return NextResponse.json(payload, { headers: SECURITY_HEADERS });
  } catch (error: Error) {
    await auditError(request, String(error?.message || error), userId);
    return NextResponse.json(
      {
        success: false,
        error: {
          message: 'Failed to generate performance report',
          details: error instanceof Error ? error.message : 'Unknown error',
        },
      },
      { status: 500 }
    );
  }
}

async function handlePOST(request: NextRequest, context: AdminAuthContext) {
  const userId = context.user?.user_id ?? 'unknown';
  try {
    const report: PerformanceReport = await request.json();

    // Here you could persist to DB or trigger alerts; we keep it side-effect-light
    if (report.database?.slowQueries > 10) {
      // trigger alert hook (future)
    }
    if (report.api?.avgResponseTime > 2000) {
      // trigger alert hook (future)
    }

    await auditSuccess(request, 'admin.performance.report.ingest', { hasDatabase: !!report.database, hasApi: !!report.api }, userId);

    return NextResponse.json(
      {
        success: true,
        message: 'Performance report received',
        timestamp: new Date().toISOString(),
      },
      { headers: SECURITY_HEADERS }
    );
  } catch (error: Error) {
    await auditError(request, String(error?.message || error), userId);
    return NextResponse.json(
      {
        success: false,
        error: {
          message: 'Failed to process performance report',
          details: error instanceof Error ? error.message : 'Unknown error',
        },
      },
      { status: 500 }
    );
  }
}

async function handleDELETE(request: NextRequest, context: AdminAuthContext) {
  const userId = context.user?.user_id ?? 'unknown';
  try {
    adminPerformanceMonitor.clearAllMetrics();

    await auditSuccess(request, 'admin.performance.report.clear', {}, userId);

    return NextResponse.json(
      {
        success: true,
        message: 'Performance metrics cleared',
        timestamp: new Date().toISOString(),
      },
      { headers: SECURITY_HEADERS }
    );
  } catch (error: Error) {
    await auditError(request, String(error?.message || error), userId);
    return NextResponse.json(
      {
        success: false,
        error: {
          message: 'Failed to clear performance metrics',
          details: error instanceof Error ? error.message : 'Unknown error',
        },
      },
      { status: 500 }
    );
  }
}

// Export route handlers with admin authentication guards
export async function GET(request: NextRequest) {
  return withAdminAuth(request, handleGET, { requiredPermission: 'system.config.read' });
}

export async function POST(request: NextRequest) {
  return withAdminAuth(request, handlePOST, { requiredPermission: 'system.config.read' });
}

export async function DELETE(request: NextRequest) {
  return withAdminAuth(request, handleDELETE, { requiredPermission: 'system.config.update' });
}
