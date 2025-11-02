/**
 * Email Template Preview API
 * 
 * API endpoint for generating email template previews with 
 * or custom variables for testing and validation.
 */
import { NextRequest, NextResponse } from 'next/server';
import { adminAuthMiddleware } from '@/lib/middleware/admin-auth';
import { EmailTemplateVariables } from '@/lib/email/types';
import { EmailTemplateManager, TemplateEngine } from '@/lib/email/template-engine';
import { auditLogger } from '@/lib/audit/audit-logger';
/**
 * POST /api/admin/email/templates/[id]/preview
 * Generate email template preview
 */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const authResult = await adminAuthMiddleware(request, ['admin', 'super_admin']);
    if (!authResult.success) {
      return NextResponse.json({ error: authResult.error }, { status: authResult.status });
    }
    const { id: templateId } = await params;
    const body = await request.json();
    const customVariables: EmailTemplateVariables | undefined = body.variables;
    // Get template
    const mockTemplates = await EmailTemplateManager.createDefaultTemplates('system');
    const template = mockTemplates.find(t => t.id === templateId);
    if (!template) {
      return NextResponse.json(
        { error: 'Email template not found' },
        { status: 404 }
      );
    }
    // Generate preview
    const preview = EmailTemplateManager.generatePreview(template, customVariables);
    // Validate template with provided variables
    const validation = TemplateEngine.validateTemplate(template, customVariables);
    // Log audit event
    await auditLogger.log(
      authResult.user?.user_id || 'unknown',
      'email_template_previewed',
      'email_template',
      {
        resourceId: templateId,
        details: { 
          template_name: template.name,
          has_custom_variables: !!customVariables
        },
        request: request
      }
    );
    return NextResponse.json({
      success: true,
      data: {
        preview,
        validation: {
          is_valid: validation.is_valid,
          errors: validation.errors,
          warnings: validation.warnings,
          missing_variables: validation.missing_variables,
          unused_variables: validation.unused_variables,
        },
        template_info: {
          id: template.id,
          name: template.name,
          template_type: template.template_type,
          variables: template.variables,
        }
      }
    });
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to generate template preview' },
      { status: 500 }
    );
  }
}
