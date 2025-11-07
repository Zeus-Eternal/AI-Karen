/**
 * Email Sending API
 *
 * API endpoints for sending emails including template-based emails,
 * bulk operations, and notification triggers.
 */
import { NextRequest, NextResponse } from "next/server";
import { adminAuthMiddleware } from "@/lib/middleware/admin-auth";
import {
  SendEmailRequest,
  EmailNotificationType,
} from "@/lib/email/types";
import { emailService, notificationService } from "@/lib/email/email-service";
import { emailQueueManager } from "@/lib/email/email-queue";
import { auditLogger } from "@/lib/audit/audit-logger";

/**
 * POST /api/admin/email/send
 * Send individual email (raw or template). If `scheduled_at` is in the future,
 * the email is queued instead of being sent immediately.
 */
export async function POST(request: NextRequest) {
  try {
    // --- AuthZ ---
    const authResult = await adminAuthMiddleware(request, [
      "admin",
      "super_admin",
    ]);
    if (!authResult.success) {
      return NextResponse.json(
        { error: authResult.error },
        { status: authResult.status }
      );
    }

    // --- Parse + Validate ---
    const body: SendEmailRequest = await request.json();

    // Basic recipient check
    if (!body.to || (Array.isArray(body.to) && body.to.length === 0)) {
      return NextResponse.json(
        { error: "Recipient email address is required" },
        { status: 400 }
      );
    }

    // Content check: template_id OR (subject AND html_content)
    const hasTemplate = !!body.template_id;
    const hasRaw =
      !!body.subject && !!body.html_content && typeof body.subject === "string";

    if (!hasTemplate && !hasRaw) {
      return NextResponse.json(
        {
          error:
            "Either template_id or both subject and html_content are required",
        },
        { status: 400 }
      );
    }

    // Optional: notification_type sanity (if present)
    if (
      body.notification_type &&
      !Object.values(EmailNotificationType).includes(body.notification_type)
    ) {
      return NextResponse.json(
        { error: "Invalid notification_type" },
        { status: 400 }
      );
    }

    // --- Init email service if needed ---
    if (!emailService.getConfig()) {
      await emailService.initialize();
    }

    // If scheduled in the future, enqueue and return immediately
    const now = Date.now();
    const scheduledAt =
      body.scheduled_at != null ? new Date(body.scheduled_at).getTime() : null;

    if (scheduledAt && !Number.isNaN(scheduledAt) && scheduledAt > now) {
      // Enqueue job
      const job = await emailQueueManager.enqueue({
        ...body,
        enqueued_at: new Date().toISOString(),
        run_at: new Date(scheduledAt).toISOString(),
        requested_by: authResult.user?.user_id || "unknown",
      });

      // Audit log (queued)
      await auditLogger.log(
        authResult.user?.user_id || "unknown",
        "email_queued",
        "email",
        {
          resourceId: job.id,
          details: {
            recipient: body.to,
            template_id: body.template_id,
            subject: body.subject,
            run_at: new Date(scheduledAt).toISOString(),
          },
        }
      );

      return NextResponse.json(
        {
          success: true,
          queued: true,
          job_id: job.id,
          message: "Email queued for future delivery",
        },
        { status: 202 }
      );
    }

    // --- Immediate send path ---
    let result:
      | {
          success: true;
          message_id: string;
        }
      | {
          success: false;
          error: string;
          retry_after?: number;
        };

    if (hasTemplate) {
      // Template-based email
      // In a real implementation you'd load templates from DB.
      const { EmailTemplateManager } = await import(
        "@/lib/email/template-engine"
      );
      const mockTemplates = EmailTemplateManager.createDefaultTemplates(
        "system"
      );
      const template = mockTemplates.find((t) => t.id === body.template_id);

      if (!template) {
        return NextResponse.json(
          { error: "Email template not found" },
          { status: 404 }
        );
      }

      result = await emailService.sendTemplateEmail(
        body.to,
        template,
        body.template_variables || {},
        {
          priority: body.priority,
          scheduledAt: undefined, // already handled above
        }
      );
    } else {
      // Raw content email
      result = await emailService.sendEmail(
        body.to,
        body.subject as string,
        body.html_content as string,
        body.text_content,
        {
          priority: body.priority,
          scheduledAt: undefined, // already handled above
        }
      );
    }

    // Optional: fire notification side-effect if requested
    if (result.success && body.notification_type) {
      try {
        await notificationService.notifyEmailEvent({
          type: body.notification_type,
          recipient: body.to,
          meta: {
            subject: body.subject,
            template_id: body.template_id,
            message_id: result.success ? result.message_id : undefined,
          },
        });
      } catch {
        // Non-fatal: don't block the email response
      }
    }

    // --- Audit log (send attempt) ---
    await auditLogger.log(
      authResult.user?.user_id || "unknown",
      "email_sent",
      "email",
      {
        resourceId: result.success ? result.message_id : undefined,
        details: {
          recipient: body.to,
          template_id: body.template_id,
          subject: body.subject,
          success: result.success,
          error: !result.success ? (result as any).error : undefined,
        },
      }
    );

    // --- Response ---
    if (result.success) {
      return NextResponse.json(
        {
          success: true,
          message_id: result.message_id,
          message: "Email sent successfully",
        },
        { status: 200 }
      );
    }

    return NextResponse.json(
      {
        success: false,
        error: result.error,
        retry_after: result.retry_after,
      },
      { status: 400 }
    );
  } catch (error) {
    // Final catch-all
    return NextResponse.json(
      { error: "Failed to send email" },
      { status: 500 }
    );
  }
}
