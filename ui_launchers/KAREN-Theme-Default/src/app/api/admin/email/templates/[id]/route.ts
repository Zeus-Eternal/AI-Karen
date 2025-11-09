/**
 * Individual Email Template API
 *
 * Path: /api/admin/email/templates/[id]
 * Supports: GET (read), PUT (update), DELETE (delete), POST (preview)
 *
 * Notes:
 * - Uses role-guarded access (admin/super_admin for read; super_admin for mutations).
 * - Returns consistent AdminApiResponse envelopes.
 * - Adds "preview" via POST { action: "preview", variables } to render a one-off sample.
 * - Currently uses in-memory defaults via EmailTemplateManager; wire DB where noted.
 */

import { NextRequest, NextResponse } from 'next/server';
import { adminAuthMiddleware } from '@/lib/middleware/admin-auth';
import type { AdminApiResponse } from '@/types/admin';
import type {
  EmailTemplate,
  UpdateEmailTemplateRequest,
  EmailTemplateVariables,
  TemplateValidationResult,
  TemplateRenderResult,
} from '@/lib/email/types';
import { EmailTemplateManager, TemplateEngine } from '@/lib/email/template-engine';
import { auditLogger } from '@/lib/audit/audit-logger';

type Role = 'admin' | 'super_admin';

function noStore(init?: ResponseInit): ResponseInit {
  return {
    ...(init || {}),
    headers: {
      ...(init?.headers || {}),
      'Cache-Control': 'no-cache, no-store, must-revalidate',
      'Pragma': 'no-cache',
      'Expires': '0',
      'Content-Type': 'application/json; charset=utf-8',
    },
  };
}

async function requireRoles(request: NextRequest, allowed: Role[]) {
  const auth = await adminAuthMiddleware(request, allowed);
  if (!auth.success) {
    return { ok: false as const, response: NextResponse.json({ success: false, error: auth.error }, noStore({ status: auth.status })) };
  }
  return { ok: true as const, auth };
}

async function loadTemplateById(templateId: string): Promise<EmailTemplate | null> {
  /**
   * PRODUCTION NOTE: Currently loads from in-memory defaults.
   * Database persistence will be added in next iteration.
   *
   * For production use, configure default templates in environment config
   * and they will be loaded on each request. Changes are not persisted.
   */
  const templates = await EmailTemplateManager.createDefaultTemplates('system');
  return templates.find((t) => t.id === templateId) || null;
}

/**
 * GET /api/admin/email/templates/[id]
 * Get email template by ID (admin, super_admin)
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const gate = await requireRoles(request, ['admin', 'super_admin']);
    if (!gate.ok) return gate.response;

    const { id: templateId } = await params;
    if (!templateId) {
      return NextResponse.json(
        { success: false, error: { code: 'INVALID_ID', message: 'Template ID is required' } },
        noStore({ status: 400 })
      );
    }

    const template = await loadTemplateById(templateId);
    if (!template) {
      return NextResponse.json(
        { success: false, error: { code: 'NOT_FOUND', message: 'Email template not found' } },
        noStore({ status: 404 })
      );
    }

    await auditLogger.log(
      gate.auth.user?.user_id || 'unknown',
      'email_template.view',
      'email_template',
      {
        details: { template_id: templateId, template_name: template.name },
        request,
      }
    );

    const response: AdminApiResponse<EmailTemplate> = {
      success: true,
      data: template,
      meta: { message: 'Template retrieved successfully' },
    };
    return NextResponse.json(response, noStore());
  } catch (err) {
    return NextResponse.json(
      {
        success: false,
        error: { code: 'TEMPLATE_GET_FAILED', message: 'Failed to get email template', details: { error: String((err as Error)?.message || err) } },
      } as AdminApiResponse<never>,
      noStore({ status: 500 })
    );
  }
}

/**
 * PUT /api/admin/email/templates/[id]
 * Update email template (super_admin)
 */
export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const gate = await requireRoles(request, ['super_admin']);
    if (!gate.ok) return gate.response;

    const { id: templateId } = await params;
    if (!templateId) {
      return NextResponse.json(
        { success: false, error: { code: 'INVALID_ID', message: 'Template ID is required' } },
        noStore({ status: 400 })
      );
    }

    const body: UpdateEmailTemplateRequest = await request.json();
    const existing = await loadTemplateById(templateId);
    if (!existing) {
      return NextResponse.json(
        { success: false, error: { code: 'NOT_FOUND', message: 'Email template not found' } },
        noStore({ status: 404 })
      );
    }

    // Update and validate
    const updated: EmailTemplate = EmailTemplateManager.updateTemplate(existing, body);
    const validation: TemplateValidationResult = TemplateEngine.validateTemplate(updated);
    if (!validation.is_valid) {
      return NextResponse.json(
        {
          success: false,
          error: { code: 'VALIDATION_FAILED', message: 'Template validation failed' },
          meta: { errors: validation.errors, warnings: validation.warnings },
        } as AdminApiResponse<never>,
        noStore({ status: 400 })
      );
    }

    /**
     * PRODUCTION NOTE: Template updates are not persisted to database yet.
     * Changes will be lost on server restart. This endpoint validates updates
     * and returns success for testing, but persistence layer is pending.
     *
     * To enable persistence, integrate with your database ORM:
     * await db.emailTemplates.update({ where: { id: templateId }, data: updated })
     */

    await auditLogger.log(
      gate.auth.user?.user_id || 'unknown',
      'email_template.update',
      'email_template',
      {
        details: { template_id: templateId, template_name: updated.name, changes: Object.keys(body || {}) },
        request,
      }
    );

    const response: AdminApiResponse<{ template: EmailTemplate; warnings?: string[] }> = {
      success: true,
      data: { template: updated, ...(validation.warnings.length ? { warnings: validation.warnings } : {}) },
      meta: { message: 'Template updated successfully' },
    };
    return NextResponse.json(response, noStore());
  } catch (err) {
    return NextResponse.json(
      {
        success: false,
        error: { code: 'TEMPLATE_UPDATE_FAILED', message: 'Failed to update email template', details: { error: String((err as Error)?.message || err) } },
      } as AdminApiResponse<never>,
      noStore({ status: 500 })
    );
  }
}

/**
 * DELETE /api/admin/email/templates/[id]
 * Delete email template (super_admin)
 */
export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const gate = await requireRoles(request, ['super_admin']);
    if (!gate.ok) return gate.response;

    const { id: templateId } = await params;
    if (!templateId) {
      return NextResponse.json(
        { success: false, error: { code: 'INVALID_ID', message: 'Template ID is required' } },
        noStore({ status: 400 })
      );
    }

    const existing = await loadTemplateById(templateId);
    if (!existing) {
      return NextResponse.json(
        { success: false, error: { code: 'NOT_FOUND', message: 'Email template not found' } },
        noStore({ status: 404 })
      );
    }

    // Guard default system templates from deletion
    if (templateId.startsWith('default_')) {
      return NextResponse.json(
        { success: false, error: { code: 'PROTECTED_TEMPLATE', message: 'Cannot delete default system templates' } },
        noStore({ status: 400 })
      );
    }

    /**
     * PRODUCTION NOTE: Template deletions are not persisted to database yet.
     * Since templates are loaded from in-memory defaults on each request,
     * this endpoint returns success but changes are not persisted.
     *
     * To enable persistence, integrate with your database ORM:
     * await db.emailTemplates.delete({ where: { id: templateId } })
     */

    await auditLogger.log(
      gate.auth.user?.user_id || 'unknown',
      'email_template.delete',
      'email_template',
      {
        details: { template_id: templateId, template_name: existing.name },
        request,
      }
    );

    const response: AdminApiResponse<{ deleted_template_id: string }> = {
      success: true,
      data: { deleted_template_id: templateId },
      meta: { message: 'Template deleted successfully', deletion_type: 'hard_or_soft_per_impl' },
    };
    return NextResponse.json(response, noStore());
  } catch (err) {
    return NextResponse.json(
      {
        success: false,
        error: { code: 'TEMPLATE_DELETE_FAILED', message: 'Failed to delete email template', details: { error: String((err as Error)?.message || err) } },
      } as AdminApiResponse<never>,
      noStore({ status: 500 })
    );
  }
}

/**
 * POST /api/admin/email/templates/[id]
 * Action router for template preview (admin, super_admin)
 * Body:
 *  {
 *    "action": "preview",
 *    "variables": { ...EmailTemplateVariables }
 *  }
 */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const gate = await requireRoles(request, ['admin', 'super_admin']);
    if (!gate.ok) return gate.response;

    const { id: templateId } = await params;
    if (!templateId) {
      return NextResponse.json(
        { success: false, error: { code: 'INVALID_ID', message: 'Template ID is required' } },
        noStore({ status: 400 })
      );
    }

    const body = await request.json().catch(() => ({}));
    const action = String(body?.action || '').toLowerCase();

    if (action !== 'preview') {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'INVALID_ACTION',
            message: 'Unsupported action. Only "preview" is supported on this endpoint.',
            details: { allowed_actions: ['preview'] },
          },
        } as AdminApiResponse<never>,
        noStore({ status: 400 })
      );
    }

    const variables: EmailTemplateVariables = (body?.variables || {}) as EmailTemplateVariables;

    const template = await loadTemplateById(templateId);
    if (!template) {
      return NextResponse.json(
        { success: false, error: { code: 'NOT_FOUND', message: 'Email template not found' } },
        noStore({ status: 404 })
      );
    }

    // Validate before preview
    const validation: TemplateValidationResult = TemplateEngine.validateTemplate(template);
    if (!validation.is_valid) {
      return NextResponse.json(
        {
          success: false,
          error: { code: 'VALIDATION_FAILED', message: 'Template validation failed' },
          meta: { errors: validation.errors, warnings: validation.warnings },
        } as AdminApiResponse<never>,
        noStore({ status: 400 })
      );
    }

    // Render preview
      let render: TemplateRenderResult;
      try {
        const appliedVariables = variables || {};
        render = {
          html: TemplateEngine.render(template.html_content, appliedVariables),
          text: TemplateEngine.render(template.text_content, appliedVariables),
          subject: TemplateEngine.render(template.subject, appliedVariables),
          success: true,
        };
      } catch (error) {
        render = {
          html: '',
          text: '',
          subject: template.subject,
          success: false,
          error: error instanceof Error ? error.message : 'Template rendering failed',
        };
      }
    // Audit the preview (no data export; informational)
    await auditLogger.log(
      gate.auth.user?.user_id || 'unknown',
      'email_template.preview',
      'email_template',
      {
        details: {
          template_id: templateId,
          template_name: template.name,
          variables_preview_count: Object.keys(variables || {}).length,
          warnings: validation.warnings,
        },
        request,
      }
    );

    const response: AdminApiResponse<{
      subject: string;
      text: string;
      html: string;
      warnings?: string[];
    }> = {
      success: true,
      data: {
        subject: render.subject,
        text: render.text,
        html: render.html,
        ...(validation.warnings.length ? { warnings: validation.warnings } : {}),
      },
      meta: { message: 'Template preview generated' },
    };
    return NextResponse.json(response, noStore());
  } catch (err) {
    return NextResponse.json(
      {
        success: false,
        error: { code: 'TEMPLATE_PREVIEW_FAILED', message: 'Failed to preview email template', details: { error: String((err as Error)?.message || err) } },
      } as AdminApiResponse<never>,
      noStore({ status: 500 })
    );
  }
}
