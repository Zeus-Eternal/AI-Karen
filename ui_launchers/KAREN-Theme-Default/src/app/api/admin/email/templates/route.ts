/**
 * Email Templates API
 *
 * API endpoints for managing email templates including CRUD operations,
 * validation, and preview generation.
 */
import { NextRequest, NextResponse } from 'next/server';

// Note: Removed 'force-dynamic' to allow static export
import { adminAuthMiddleware } from '@/lib/middleware/admin-auth';
import {  EmailTemplate, CreateEmailTemplateRequest, EmailTemplateFilter } from '@/lib/email/types';
import { PaginatedResponse } from '@/types/admin';
import { EmailTemplateManager, TemplateEngine } from '@/lib/email/template-engine';
import { auditLogger } from '@/lib/audit/audit-logger';
/**
 * GET /api/admin/email/templates
 * List email templates with filtering and pagination
 */
export async function GET(request: NextRequest) {
  try {
    const authResult = await adminAuthMiddleware(request, ['admin', 'super_admin']);
    if (!authResult.success) {
      return NextResponse.json({ error: authResult.error }, { status: authResult.status });
    }
    const { searchParams } = new URL(request.url);
    const page = parseInt(searchParams.get('page') || '1');
    const limit = parseInt(searchParams.get('limit') || '10');
    const templateType = searchParams.get('template_type') as EmailTemplate['template_type'] | null;
    const isActive = searchParams.get('is_active') === 'true' ? true : 
                    searchParams.get('is_active') === 'false' ? false : undefined;
    const search = searchParams.get('search') || undefined;
    const filter: EmailTemplateFilter = {
      template_type: templateType || undefined,
      is_active: isActive,
      search,
    };
    // In a real implementation, this would query the database
    // For now, return mock data
    const mockTemplates: EmailTemplate[] = await EmailTemplateManager.createDefaultTemplates(authResult.user?.user_id || 'unknown');
    // Apply filters
    let filteredTemplates = mockTemplates;
    if (filter.template_type) {
      filteredTemplates = filteredTemplates.filter(t => t.template_type === filter.template_type);
    }
    if (filter.is_active !== undefined) {
      filteredTemplates = filteredTemplates.filter(t => t.is_active === filter.is_active);
    }
    if (filter.search) {
      const searchLower = filter.search.toLowerCase();
      filteredTemplates = filteredTemplates.filter(t => 
        t.name.toLowerCase().includes(searchLower) ||
        t.subject.toLowerCase().includes(searchLower)
      );
    }
    // Apply pagination
    const startIndex = (page - 1) * limit;
    const endIndex = startIndex + limit;
    const paginatedTemplates = filteredTemplates.slice(startIndex, endIndex);
    const response: PaginatedResponse<EmailTemplate> = {
      data: paginatedTemplates,
      pagination: {
        page,
        limit,
        total: filteredTemplates.length,
        total_pages: Math.ceil(filteredTemplates.length / limit),
        has_next: endIndex < filteredTemplates.length,
        has_prev: page > 1,
      },
    };
    // Log audit event
    await auditLogger.log(
      authResult.user?.user_id || 'unknown',
      'email_templates_listed',
      'email_template',
      {
        resourceId: undefined,
        details: { 
          filter,
          pagination: { page, limit } 
        },
        request: request
      }
    );
    return NextResponse.json(response);
  } catch {
    return NextResponse.json(
      { error: 'Failed to list email templates' },
      { status: 500 }
    );
  }
}
/**
 * POST /api/admin/email/templates
 * Create new email template
 */
export async function POST(request: NextRequest) {
  try {
    const authResult = await adminAuthMiddleware(request, ['super_admin']);
    if (!authResult.success) {
      return NextResponse.json({ error: authResult.error }, { status: authResult.status });
    }
    const body: CreateEmailTemplateRequest = await request.json();
    // Validate request
    if (!body.name || !body.subject || !body.html_content || !body.template_type) {
      return NextResponse.json(
        { error: 'Missing required fields: name, subject, html_content, template_type' },
        { status: 400 }
      );
    }
    // Create template
    const template = EmailTemplateManager.createTemplate(body, authResult.user?.user_id || 'unknown');
    // Validate template
    const validation = TemplateEngine.validateTemplate(template);
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
      'email_template_created',
      'email_template',
      {
        resourceId: template.id,
        details: { 
          template_name: template.name,
          template_type: template.template_type 
        },
        request: request
      }
    );
    return NextResponse.json({ 
      success: true, 
      data: template,
      validation: validation.warnings.length > 0 ? { warnings: validation.warnings } : undefined
    }, { status: 201 });
  } catch {
    return NextResponse.json(
      { error: 'Failed to create email template' },
      { status: 500 }
    );
  }
}
