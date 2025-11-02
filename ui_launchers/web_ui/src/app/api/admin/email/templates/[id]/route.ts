/**
 * Individual Email Template API
 * 
 * API endpoints for managing individual email templates including
 * get, update, delete, and preview operations.
 */
import { NextRequest, NextResponse } from 'next/server';
import { adminAuthMiddleware } from '@/lib/middleware/admin-auth';
import { 
  EmailTemplate, 
  UpdateEmailTemplateRequest,
  EmailTemplateVariables 
} from '@/lib/email/types';
import { EmailTemplateManager, TemplateEngine } from '@/lib/email/template-engine';
import { auditLogger } from '@/lib/audit/audit-logger';
/**
 * GET /api/admin/email/templates/[id]
 * Get email template by ID
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const authResult = await adminAuthMiddleware(request, ['admin', 'super_admin']);
    if (!authResult.success) {
      return NextResponse.json({ error: authResult.error }, { status: authResult.status });
    }
    const { id: templateId } = await params;
    // In a real implementation, this would query the database
    // For now, return mock data
    const mockTemplates = await EmailTemplateManager.createDefaultTemplates('system');
    const template = mockTemplates.find(t => t.id === templateId);
    if (!template) {
      return NextResponse.json(
        { error: 'Email template not found' },
        { status: 404 }
      );
    }
    // Log audit event
    await auditLogger.log(
      authResult.user?.user_id || 'unknown',
      'email_template_viewed',
      'email_template',
      {
        resourceId: templateId,
        details: { template_name: template.name },
        request: request
      }
    );
    return NextResponse.json({ success: true, data: template });
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to get email template' },
      { status: 500 }
    );
  }
}
/**
 * PUT /api/admin/email/templates/[id]
 * Update email template
 */
export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const authResult = await adminAuthMiddleware(request, ['super_admin']);
    if (!authResult.success) {
      return NextResponse.json({ error: authResult.error }, { status: authResult.status });
    }
    const { id: templateId } = await params;
    const body: UpdateEmailTemplateRequest = await request.json();
    // Get existing template
    const mockTemplates = await EmailTemplateManager.createDefaultTemplates('system');
    const existingTemplate = mockTemplates.find(t => t.id === templateId);
    if (!existingTemplate) {
      return NextResponse.json(
        { error: 'Email template not found' },
        { status: 404 }
      );
    }
    // Update template
    const updatedTemplate = EmailTemplateManager.updateTemplate(existingTemplate, body);
    // Validate updated template
    const validation = TemplateEngine.validateTemplate(updatedTemplate);
    if (!validation.is_valid) {
      return NextResponse.json(
        { 
          error: 'Template validation failed',
          details: {
            errors: validation.errors,
            warnings: validation.warnings,
          }
        },
        { status: 400 }
      );
    }
    // In a real implementation, save to database here
    // Log audit event
    await auditLogger.log(
      authResult.user?.user_id || 'unknown',
      'email_template_updated',
      'email_template',
      {
        resourceId: templateId,
        details: { 
        template_name: updatedTemplate.name,
        changes: Object.keys(body)
      },
        request: request
      }
    );
    return NextResponse.json({ 
      success: true, 
      data: updatedTemplate,
      validation: validation.warnings.length > 0 ? { warnings: validation.warnings } : undefined
    });
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to update email template' },
      { status: 500 }
    );
  }
}
/**
 * DELETE /api/admin/email/templates/[id]
 * Delete email template
 */
export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const authResult = await adminAuthMiddleware(request, ['super_admin']);
    if (!authResult.success) {
      return NextResponse.json({ error: authResult.error }, { status: authResult.status });
    }
    const { id: templateId } = await params;
    // Get existing template
    const mockTemplates = await EmailTemplateManager.createDefaultTemplates('system');
    const existingTemplate = mockTemplates.find(t => t.id === templateId);
    if (!existingTemplate) {
      return NextResponse.json(
        { error: 'Email template not found' },
        { status: 404 }
      );
    }
    // Prevent deletion of default templates
    if (templateId.startsWith('default_')) {
      return NextResponse.json(
        { error: 'Cannot delete default system templates' },
        { status: 400 }
      );
    }
    // In a real implementation, delete from database here
    // Log audit event
    await auditLogger.log(
      authResult.user?.user_id || 'unknown',
      'email_template_deleted',
      'email_template',
      {
        resourceId: templateId,
        details: { template_name: existingTemplate.name },
        request: request
      }
    );
    return NextResponse.json({ success: true });
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to delete email template' },
      { status: 500 }
    );
  }
}
