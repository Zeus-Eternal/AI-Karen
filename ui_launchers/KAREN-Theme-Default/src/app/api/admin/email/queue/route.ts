/**
 * Email Queue Management API (Prod-Grade)
 *
 * GET  /api/admin/email/queue?include_items=true|false&limit=1..500&status=all|pending|failed
 * POST /api/admin/email/queue   { action: "retry_failed" | "clear_queue" }
 *
 * Auth: admin | super_admin (super_admin required for clear_queue)
 * Security: no-store, nosniff, CSP, frame deny
 * Observability: audit logs on view/retry/clear + error paths
 */

import { NextRequest, NextResponse } from "next/server";
import { adminAuthMiddleware } from "@/lib/middleware/admin-auth";
import { emailQueueManager } from "@/lib/email/email-queue";
import { auditLogger } from "@/lib/audit/audit-logger";

export const dynamic = "force-dynamic";

type QueueStatusFilter = "all" | "pending" | "failed";

const SECURITY_HEADERS = {
  "Cache-Control": "no-store",
  "X-Content-Type-Options": "nosniff",
  "Content-Security-Policy": "default-src 'none'",
  "X-Frame-Options": "DENY",
} as const;

function ipFrom(req: NextRequest): string {
  return (
    req.headers.get("x-forwarded-for") ||
    req.headers.get("x-real-ip") ||
    "unknown"
  );
}

async function safeAudit(
  req: NextRequest,
  userId: string,
  event: string,
  entityType: string,
  details: Record<string, unknown> = {}
) {
  try {
    await auditLogger.log(userId, event, entityType, {
      resourceId: undefined,
      details,
      request: req,
      ip_address: ipFrom(req),
    });
  } catch {
    // swallow audit errors
  }
}

/**
 * GET /api/admin/email/queue
 * Query params:
 *   - include_items=true|false  (default: false)
 *   - limit=<number>            (default: 50, min: 1, max: 500)
 *   - status=all|pending|failed (default: all, applied only if items requested)
 */
export async function GET(request: NextRequest) {
  const startedAt = Date.now();
  try {
    const auth = await adminAuthMiddleware(request, ["admin", "super_admin"]);
    if (!auth.success) {
      return NextResponse.json(
        { success: false, error: auth.error },
        { status: auth.status, headers: SECURITY_HEADERS }
      );
    }

    const { searchParams } = new URL(request.url);
    const includeItems = searchParams.get("include_items") === "true";

    // limit parsing/coercion
    const limitRaw = searchParams.get("limit");
    const limitNum = Number.isFinite(Number(limitRaw)) ? Number(limitRaw) : 50;
    const limit = Math.max(1, Math.min(500, limitNum));

    // optional status (for item filtering; ignored if items not requested)
    const statusParam = (searchParams.get("status") || "all").toLowerCase();
    const status: QueueStatusFilter =
      statusParam === "pending" || statusParam === "failed" ? statusParam : "all";

    // Stats are always returned
    const stats = emailQueueManager.getQueueStats();

    // Items are optional (and limited)
    let items: unknown = null;
    if (includeItems) {
      try {
        let allItems = emailQueueManager.getQueueItems();

        // Optional filter if items support a "status" field
        if (status !== "all") {
          // Gracefully handle if items don't have a "status" field
          // @ts-expect-error — tolerate heterogeneous shapes
          allItems = allItems.filter((it: unknown) => (it?.status ?? "unknown") === status);
        }

        items = allItems.slice(0, limit);
      } catch {
        items = null; // still return stats if item retrieval fails
      }
    }

    await safeAudit(request, auth.user?.user_id || "unknown", "email_queue_viewed", "email_queue", {
      include_items: includeItems,
      limit,
      status,
      queue_size: stats.total,
      durationMs: Date.now() - startedAt,
    });

    return NextResponse.json(
      {
        success: true,
        data: {
          statistics: stats,
          items,
        },
      },
      { status: 200, headers: SECURITY_HEADERS }
    );
  } catch (error: unknown) {
    await safeAudit(request, "unknown", "email_queue_error", "email_queue", {
      error:
        error instanceof Error ? error.message : String(error),
    });
    return NextResponse.json(
      { success: false, error: "Failed to get email queue information" },
      { status: 500, headers: SECURITY_HEADERS }
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
      return NextResponse.json(
        { success: false, error: auth.error },
        { status: auth.status, headers: SECURITY_HEADERS }
      );
    }

    const body = (await request.json()) ?? {};
    const action = String(body.action || "").toLowerCase();

    if (action === "retry_failed") {
      const retriedCount = emailQueueManager.retryFailedItems();

      await safeAudit(
        request,
        auth.user?.user_id || "unknown",
        "email_queue_retry_failed",
        "email_queue",
        { retried_count: retriedCount }
      );

      return NextResponse.json(
        {
          success: true,
          message: `${retriedCount} failed items marked for retry`,
          retried_count: retriedCount,
          timestamp: new Date().toISOString(),
        },
        { status: 200, headers: SECURITY_HEADERS }
      );
    }

    if (action === "clear_queue") {
      if (auth.user?.role !== "super_admin") {
        return NextResponse.json(
          { success: false, error: "Only super admins can clear the email queue" },
          { status: 403, headers: SECURITY_HEADERS }
        );
      }

      const queueSizeBefore = emailQueueManager.getQueueStats().total;
      emailQueueManager.clearQueue();

      await safeAudit(
        request,
        auth.user?.user_id || "unknown",
        "email_queue_cleared",
        "email_queue",
        { cleared_items: queueSizeBefore }
      );

      return NextResponse.json(
        {
          success: true,
          message: `Email queue cleared (${queueSizeBefore} items removed)`,
          cleared_count: queueSizeBefore,
          timestamp: new Date().toISOString(),
        },
        { status: 200, headers: SECURITY_HEADERS }
      );
    }

    return NextResponse.json(
      {
        success: false,
        error: "Invalid action. Supported actions: retry_failed, clear_queue",
      },
      { status: 400, headers: SECURITY_HEADERS }
    );
  } catch (error: unknown) {
    await safeAudit(request, "unknown", "email_queue_error", "email_queue", {
      error: error instanceof Error ? error.message : String(error),
    });
    return NextResponse.json(
      { success: false, error: "Failed to manage email queue" },
      { status: 500, headers: SECURITY_HEADERS }
    );
  }
}
