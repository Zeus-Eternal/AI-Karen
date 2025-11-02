/**
 * Email Queue Management API
 * 
 * API endpoints for monitoring and managing the email queue including
 * statistics, queue items, and retry operations.
 */
import { NextRequest, NextResponse } from 'next/server';
import { adminAuthMiddleware } from '@/lib/middleware/admin-auth';
import { emailQueueManager } from '@/lib/email/email-queue';
import { auditLogger } from '@/lib/audit/audit-logger';
/**
 * GET /api/admin/email/queue
 * Get email queue statistics and items
 */
export async function GET(request: NextRequest) {
  try {
    const authResult = await adminAuthMiddleware(request, ['admin', 'super_admin']);
    if (!authResult.success) {
      return NextResponse.json({ error: authResult.error }, { status: authResult.status });
    }
    const { searchParams } = new URL(request.url);
    const includeItems = searchParams.get('include_items') === 'true';
    const limit = parseInt(searchParams.get('limit') || '50');
    // Get queue statistics
    const stats = emailQueueManager.getQueueStats();
    // Get queue items if requested
    let items = null;
    if (includeItems) {
      const allItems = emailQueueManager.getQueueItems();
      items = allItems.slice(0, limit);
    }
    // Log audit event
    await auditLogger.log(
      authResult.user?.user_id || 'unknown',
      'email_queue_viewed',
      'email_queue',
      {
        resourceId: undefined,
        details: { 
          include_items: includeItems,
          queue_size: stats.total
        },
        request: request
      }
    );
    return NextResponse.json({
      success: true,
      data: {
        statistics: stats,
        items: items,
      }

  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to get email queue information' },
      { status: 500 }
    );
  }
}
/**
 * POST /api/admin/email/queue/retry
 * Retry failed email queue items
 */
export async function POST(request: NextRequest) {
  try {
    const authResult = await adminAuthMiddleware(request, ['admin', 'super_admin']);
    if (!authResult.success) {
      return NextResponse.json({ error: authResult.error }, { status: authResult.status });
    }
    const body = await request.json();
    const action = body.action;
    if (action === 'retry_failed') {
      // Retry all failed items
      const retriedCount = emailQueueManager.retryFailedItems();
      // Log audit event
      await auditLogger.log(
      authResult.user?.user_id || 'unknown',
      'email_queue_retry_failed',
      'email_queue',
      {
        resourceId: undefined,
        details: { retried_count: retriedCount },
        request: request
      }
    );
      return NextResponse.json({
        success: true,
        message: `${retriedCount} failed items marked for retry`,
        retried_count: retriedCount,

    } else if (action === 'clear_queue') {
      // Clear entire queue (admin only)
      if (authResult.user?.role !== 'super_admin') {
        return NextResponse.json(
          { error: 'Only super admins can clear the email queue' },
          { status: 403 }
        );
      }
      const queueSize = emailQueueManager.getQueueStats().total;
      emailQueueManager.clearQueue();
      // Log audit event
      await auditLogger.log(
      authResult.user?.user_id || 'unknown',
      'email_queue_cleared',
      'email_queue',
      {
        resourceId: undefined,
        details: { cleared_items: queueSize },
        request: request
      }
    );
      return NextResponse.json({
        success: true,
        message: `Email queue cleared (${queueSize} items removed)`,
        cleared_count: queueSize,

    } else {
      return NextResponse.json(
        { error: 'Invalid action. Supported actions: retry_failed, clear_queue' },
        { status: 400 }
      );
    }
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to manage email queue' },
      { status: 500 }
    );
  }
}
