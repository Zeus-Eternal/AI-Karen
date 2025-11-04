/**
 * Email Queue Management API
 *
 * API endpoints for monitoring and managing the email queue including
 * statistics, queue items, and retry/clear operations.
 */
import { NextRequest, NextResponse } from "next/server";
import { adminAuthMiddleware } from "@/lib/middleware/admin-auth";
import { emailQueueManager } from "@/lib/email/email-queue";
import { auditLogger } from "@/lib/audit/audit-logger";

/**
 * GET /api/admin/email/queue
 * Query params:
 *   - include_items=true|false  (default: false)
 *   - limit=<number>            (default: 50, min: 1, max: 500)
 */
export async function GET(request: NextRequest) {
  try {
    const auth = await adminAuthMiddleware(request, ["admin", "super_admin"]);
    if (!auth.success) {
      return NextResponse.json({ error: auth.error }, { status: auth.status });
    }

    const { searchParams } = new URL(request.url);
    const includeItems = searchParams.get("include_items") === "true";

    const limitRaw = searchParams.get("limit");
    const limitNum = Number.isFinite(Number(limitRaw)) ? Number(limitRaw) : 50;
    const limit = Math.max(1, Math.min(500, limitNum));

    // Stats are always returned
    const stats = emailQueueManager.getQueueStats();

    // Items are optional (and limited)
    let items: unknown = null;
    if (includeItems) {
      try {
        const allItems = emailQueueManager.getQueueItems();
        items = allItems.slice(0, limit);
      } catch {
        // If queue items retrieval fails, keep items as null but still return stats
        items = null;
      }
    }

    await auditLogger.log(
      auth.user?.user_id || "unknown",
      "email_queue_viewed",
      "email_queue",
      {
        resourceId: undefined,
        details: {
          include_items: includeItems,
          limit,
          queue_size: stats.total,
        },
      }
    );

    return NextResponse.json(
      {
        success: true,
        data: {
          statistics: stats,
          items,
        },
      },
      { status: 200 }
    );
  } catch {
    return NextResponse.json(
      { error: "Failed to get email queue information" },
      { status: 500 }
    );
  }
}

/**
 * POST /api/admin/email/queue
 * Body:
 *   { "action": "retry_failed" }
 *   { "action": "clear_queue" }  // super_admin only
 */
export async function POST(request: NextRequest) {
  try {
    const auth = await adminAuthMiddleware(request, ["admin", "super_admin"]);
    if (!auth.success) {
      return NextResponse.json({ error: auth.error }, { status: auth.status });
    }

    const body = (await request.json()) ?? {};
    const action = String(body.action || "");

    if (action === "retry_failed") {
      const retriedCount = emailQueueManager.retryFailedItems();

      await auditLogger.log(
        auth.user?.user_id || "unknown",
        "email_queue_retry_failed",
        "email_queue",
        {
          resourceId: undefined,
          details: { retried_count: retriedCount },
        }
      );

      return NextResponse.json(
        {
          success: true,
          message: `${retriedCount} failed items marked for retry`,
          retried_count: retriedCount,
        },
        { status: 200 }
      );
    }

    if (action === "clear_queue") {
      if (auth.user?.role !== "super_admin") {
        return NextResponse.json(
          { error: "Only super admins can clear the email queue" },
          { status: 403 }
        );
      }

      const queueSizeBefore = emailQueueManager.getQueueStats().total;
      emailQueueManager.clearQueue();

      await auditLogger.log(
        auth.user?.user_id || "unknown",
        "email_queue_cleared",
        "email_queue",
        {
          resourceId: undefined,
          details: { cleared_items: queueSizeBefore },
        }
      );

      return NextResponse.json(
        {
          success: true,
          message: `Email queue cleared (${queueSizeBefore} items removed)`,
          cleared_count: queueSizeBefore,
        },
        { status: 200 }
      );
    }

    return NextResponse.json(
      {
        error: "Invalid action. Supported actions: retry_failed, clear_queue",
      },
      { status: 400 }
    );
  } catch {
    return NextResponse.json(
      { error: "Failed to manage email queue" },
      { status: 500 }
    );
  }
}
