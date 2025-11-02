/**
 * Email Sending API
 * 
 * API endpoints for sending emails including template-based emails,
 * bulk operations, and notification triggers.
 */
import { NextRequest, NextResponse } from 'next/server';
import { adminAuthMiddleware } from '@/lib/middleware/admin-auth';
import { 
  SendEmailRequest,
  BulkEmailRequest,
  EmailNotificationType 
} from '@/lib/email/types';
import { emailService, notificationService } from '@/lib/email/email-service';
import { emailQueueManager } from '@/lib/email/email-queue';
import { auditLogger } from '@/lib/audit/audit-logger';
/**
 * POST /api/admin/email/send
 * Send individual email
 */
export async function POST(request: NextRequest) {
  try {
    const authResult = await adminAuthMiddleware(request, ['admin', 'super_admin']);
    if (!authResult.success) {
      return NextResponse.json({ error: authResult.error }, { status: authResult.status });
    }
    const body: SendEmailRequest = await request.json();
    // Validate request
    if (!body.to) {
      return NextResponse.json(
        { error: 'Recipient email address is required' },
        { status: 400 }
      );
    }
    if (!body.template_id && (!body.subject || !body.html_content)) {
      return NextResponse.json(
        { error: 'Either template_id or subject and html_content are required' },
        { status: 400 }
      );
    }
    // Initialize email service if needed
    if (!emailService.getConfig()) {
      await emailService.initialize();
    }
    let result;
    if (body.template_id) {
      // Send template-based email
      // In a real implementation, get template from database
      const mockTemplates = await import('@/lib/email/template-engine').then(m => 
        m.EmailTemplateManager.createDefaultTemplates('system')
      );
      const template = mockTemplates.find(t => t.id === body.template_id);
      if (!template) {
        return NextResponse.json(
          { error: 'Email template not found' },
          { status: 404 }
        );
      }
      result = await emailService.sendTemplateEmail(
        body.to,
        template,
        body.template_variables || {},
        {
          priority: body.priority,
          scheduledAt: body.scheduled_at,
        }
      );
    } else {
      // Send simple email
      result = await emailService.sendEmail(
        body.to,
        body.subject!,
        body.html_content!,
        body.text_content,
        {
          priority: body.priority,
          scheduledAt: body.scheduled_at,
        }
      );
    }
    // Log audit event
    await auditLogger.log(
      authResult.user?.user_id || 'unknown',
      'email_sent',
      'email',
      {
        resourceId: result.message_id,
        details: { 
          recipient: body.to,
          template_id: body.template_id,
          subject: body.subject,
          success: result.success
        },
        request: request
      }
    );
    if (result.success) {
      return NextResponse.json({
        success: true,
        message_id: result.message_id,
        message: 'Email sent successfully'
      });
    } else {
      return NextResponse.json(
        { 
          success: false,
          error: result.error,
          retry_after: result.retry_after
        },
        { status: 400 }
      );
    }
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to send email' },
      { status: 500 }
    );
  }
}
