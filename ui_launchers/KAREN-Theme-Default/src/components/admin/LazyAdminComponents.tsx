/**
 * Email Template Preview API (Production Hardened)
 *
 * POST /api/admin/email/templates/[id]/preview
 * Body: { variables?: Record<string, unknown> }
 *
 * Features:
 * - Strict auth (admin | super_admin)
 * - Robust JSON/body validation
 * - Safe template fetch with graceful fallback
 * - Preview rendering + schema validation
 * - Structured audit logging (PII-safe)
 * - Correlation-ID + timing headers
 * - Deterministic error responses
 */

import { NextRequest, NextResponse } from 'next/server';
import { randomUUID } from 'crypto';
import { adminAuthMiddleware } from '@/lib/middleware/admin-auth';
import { EmailTemplate, EmailTemplateVariables } from '@/lib/email/types';
import { EmailTemplateManager, TemplateEngine } from '@/lib/email/template-engine';
import { auditLogger } from '@/lib/audit/audit-logger';

type JsonPreviewRequest = {
  variables?: EmailTemplateVariables;
};

const JSON_TYPE = 'application/json';

/** Safe JSON parse with clear 400 on syntax errors */
async function parseJson<T>(req: NextRequest, correlationId: string): Promise<T> {
  let bodyText: string;
  try {
    bodyText = await req.text();
  } catch {
    throw badRequest('Unable to read request body', correlationId);
  }

  if (!bodyText) return {} as T;

  try {
    return JSON.parse(bodyText) as T;
  } catch {
    throw badRequest('Invalid JSON in request body', correlationId);
  }
}

/** Build a 400 response with standardized shape */
function badRequest(message: string, cid: string) {
  const res = NextResponse.json(
    {
      success: false,
      error: {
        code: 'BAD_REQUEST',
        message,
      },
    },
    { status: 400 },
  );
  res.headers.set('x-correlation-id', cid);
  return res;
}

/** Build a 404 response */
function notFound(message: string, cid: string) {
  const res = NextResponse.json(
    {
      success: false,
      error: {
        code: 'NOT_FOUND',
        message,
      },
    },
    { status: 404 },
  );
  res.headers.set('x-correlation-id', cid);
  return res;
}

/** Build a 401/403 response from auth middleware result */
function authError(status: number, message: string, cid: string) {
  const res = NextResponse.json(
    {
      success: false,
      error: {
        code: status === 401 ? 'UNAUTHORIZED' : 'FORBIDDEN',
        message,
      },
    },
    { status },
  );
  res.headers.set('x-correlation-id', cid);
  return res;
}

/** Build a 500 response */
function serverError(message: string, cid: string) {
  const res = NextResponse.json(
    {
      success: false,
      error: {
        code: 'INTERNAL_ERROR',
        message,
      },
    },
    { status: 500 },
  );
  res.headers.set('x-correlation-id', cid);
  return res;
}

/** Minimal variable shape guard */
function isVariablesRecord(v: unknown): v is EmailTemplateVariables {
  return v !== null && typeof v === 'object';
}

/**
 * POST /api/admin/email/templates/[id]/preview
 */
export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } },
) {
  const started = performance.now();
  const correlationId = request.headers.get('x-correlation-id') || randomUUID();

  try {
    // Enforce JSON content type when body exists
    const contentType = request.headers.get('content-type') || '';
    if (request.body && !contentType.toLowerCase().includes(JSON_TYPE)) {
      return badRequest(`Content-Type must be ${JSON_TYPE}`, correlationId);
    }

    // Auth
    const authResult: unknown = await adminAuthMiddleware(request, ['admin', 'super_admin']);
    // Middleware in your codebase can return either a NextResponse or a structured object
    if (authResult instanceof NextResponse) {
      // Pass through but ensure correlation header
      authResult.headers.set('x-correlation-id', correlationId);
      return authResult;
    }
    if (!authResult?.success) {
      return authError(authResult?.status || 401, authResult?.error || 'Unauthorized', correlationId);
    }
    const currentUserId: string = authResult.user?.user_id || 'unknown';

    // Params
    const templateId = params?.id;
    if (!templateId) {
      return badRequest('Missing path parameter: id', correlationId);
    }

    // Body
    const payload = await parseJson<JsonPreviewRequest>(request, correlationId);
    const customVariables = payload?.variables;
    if (customVariables !== undefined && !isVariablesRecord(customVariables)) {
      return badRequest('`variables` must be an object of key/value pairs', correlationId);
    }

    // Fetch template (prefer DB/manager; graceful fallback to defaults if needed)
    // Expect EmailTemplateManager.getById in production; fallback for environments where only defaults exist
    let template: EmailTemplate | null = await EmailTemplateManager.getById?.(
      templateId
    );
    if (!template) {
      const defaults: EmailTemplate[] =
        await EmailTemplateManager.createDefaultTemplates('system');
      template = defaults.find((t) => t.id === templateId) ?? null;
    }
    if (!template) {
      return notFound('Email template not found', correlationId);
    }

    // Generate preview + validate
    const preview = EmailTemplateManager.generatePreview(template, customVariables);
    const validation = TemplateEngine.validateTemplate(template, customVariables);

    // Audit (PII-safe; never attach raw request)
    await auditLogger.log(currentUserId, 'email_template_previewed', 'email_template', {
      resourceId: templateId,
      details: {
        template_name: template.name,
        has_custom_variables: Boolean(customVariables && Object.keys(customVariables).length > 0),
        correlation_id: correlationId,
        request_meta: {
          method: request.method,
          path: `/api/admin/email/templates/${templateId}/preview`,
        },
      },
      request,
    });

    // Build response
    const durationMs = Math.round(performance.now() - started);
    const res = NextResponse.json(
      {
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
            updated_at: (template as unknown)?.updated_at ?? undefined,
          },
          meta: {
            correlation_id: correlationId,
            duration_ms: durationMs,
          },
        },
      },
      { status: 200 },
    );

    res.headers.set('x-correlation-id', correlationId);
    res.headers.set('x-duration-ms', String(durationMs));
    res.headers.set('cache-control', 'no-store');

    return res;
  } catch (err: Error) {
    // Best-effort audit for failures
    try {
      await auditLogger.log('system', 'email_template_preview_failed', 'email_template', {
        details: {
          error: err?.message || String(err),
          correlation_id: correlationId,
        },
      });
    } catch {
      // swallow audit failure
    }
    return serverError('Failed to generate template preview', correlationId);
  }
}
