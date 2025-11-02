/**
 * Admin Performance Report API
 * 
 * Provides endpoints for collecting and analyzing performance metrics
 * from admin operations.
 * 
 * Requirements: 7.3, 7.5
 */
import { NextRequest, NextResponse } from 'next/server';
import { withAdminAuth, type AdminAuthContext } from '@/lib/middleware/admin-auth';
import { adminPerformanceMonitor, PerformanceReporter } from '@/lib/performance/admin-performance-monitor';
import { getQueryOptimizer } from '@/lib/database/query-optimizer';
import type { PerformanceReport } from '@/types/admin';
async function handleGET(request: NextRequest, _context: AdminAuthContext) {
  try {
    const { searchParams } = new URL(request.url);
    const format = searchParams.get('format') || 'json';
    const includeRecommendations = searchParams.get('recommendations') !== 'false';
    // Generate performance report
    const report = PerformanceReporter.generateReport();
    // Add database-specific metrics if requested
    if (searchParams.get('include_db_stats') === 'true') {
      try {
        const queryOptimizer = getQueryOptimizer();
        const [queryPerformance, tableStats] = await Promise.all([
          queryOptimizer.getQueryPerformanceAnalysis(),
          queryOptimizer.getTableStatistics()
        ]);
        (report as any).database_analysis = {
          query_performance: queryPerformance,
          table_statistics: tableStats
        };
      } catch (error) {
      }
    }
    if (format === 'csv') {
      const csvData = PerformanceReporter.exportMetrics('csv');
      return new NextResponse(csvData, {
        headers: {
          'Content-Type': 'text/csv',
          'Content-Disposition': 'attachment; filename="admin-performance-report.csv"'
        }

    }
    return NextResponse.json({
      success: true,
      data: report,
      timestamp: new Date().toISOString()

  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: {
          message: 'Failed to generate performance report',
          details: error instanceof Error ? error.message : 'Unknown error'
        }
      },
      { status: 500 }
    );
  }
}
async function handlePOST(request: NextRequest, context: AdminAuthContext) {
  try {
    const report: PerformanceReport = await request.json();
    // Store the performance report (in a real implementation, you might save to database)
    // You could implement alerting here for performance issues
    if (report.database.slowQueries > 10) {
    }
    if (report.api.avgResponseTime > 2000) {
    }
    return NextResponse.json({
      success: true,
      message: 'Performance report received',
      timestamp: new Date().toISOString()

  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: {
          message: 'Failed to process performance report',
          details: error instanceof Error ? error.message : 'Unknown error'
        }
      },
      { status: 500 }
    );
  }
}
async function handleDELETE(request: NextRequest, context: AdminAuthContext) {
  try {
    // Clear all performance metrics
    adminPerformanceMonitor.clearAllMetrics();
    return NextResponse.json({
      success: true,
      message: 'Performance metrics cleared',
      timestamp: new Date().toISOString()

  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: {
          message: 'Failed to clear performance metrics',
          details: error instanceof Error ? error.message : 'Unknown error'
        }
      },
      { status: 500 }
    );
  }
}
// Export route handlers with admin authentication
export async function GET(request: NextRequest) {
  return withAdminAuth(request, handleGET, { requiredPermission: 'system.config.read' });
}
export async function POST(request: NextRequest) {
  return withAdminAuth(request, handlePOST, { requiredPermission: 'system.config.read' });
}
export async function DELETE(request: NextRequest) {
  return withAdminAuth(request, handleDELETE, { requiredPermission: 'system.config.update' });
}
