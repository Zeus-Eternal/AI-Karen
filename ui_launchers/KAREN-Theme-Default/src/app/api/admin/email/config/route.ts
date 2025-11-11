import { NextRequest, NextResponse } from 'next/server';
import crypto from 'crypto';
import { adminAuthMiddleware } from '@/lib/middleware/admin-auth';
import { emailService } from '@/lib/email/email-service';
import { auditLogger } from '@/lib/audit/audit-logger';

import {
  EmailServiceConfig,
  UpdateEmailServiceConfigRequest,
} from '@/lib/email/types';
import {
  getEmailServiceConfig,
  validateEmailConfig,
  testEmailService,
  EMAIL_PROVIDERS,
} from '@/lib/email/config';

/**
 * Email Configuration API (Prod-Grade)
 *
 * - RBAC: super_admin only
 * - GET returns redacted config + provider catalog
 * - PUT validates & (optionally) tests connectivity before saving
 * - Secrets are never echoed back or logged in clear text
 * - Adds ETag and no-store cache semantics
 * - Structured audit logs
 */

const SECRET_KEYS = new Set(['smtp_password', 'api_key', 'api_secret', 'token', 'webhook_secret']);
const MASK = '***';

function redactSecrets<T extends Record<string, unknown>>(obj: T): T {
  const clone: unknown = {};
  for (const [k, v] of Object.entries(obj || {})) {
    if (SECRET_KEYS.has(k)) {
      clone[k] = v ? MASK : '';
    } else {
      clone[k] = v;
    }
  }
  return clone;
}

function summarizeChanges(body: Record<string, unknown>) {
  const summary: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(body || {})) {
    if (SECRET_KEYS.has(k)) summary[k] = '***updated***';
    else summary[k] = isTriviallySerializable(v) ? v : '[complex]';
  }
  return summary;
}

function isTriviallySerializable(v: unknown) {
  return v == null || ['string', 'number', 'boolean'].includes(typeof v);
}

function jsonError(message: string, status = 400, details?: unknown) {
  return NextResponse.json(
    { success: false, error: message, details },
    { status, headers: { 'Cache-Control': 'no-store' } },
  );
}

function toETag(payload: unknown) {
  const buf = Buffer.from(JSON.stringify(payload));
  return `"W/${crypto.createHash('sha256').update(buf).digest('base64url')}"`;
}

/**
 * GET /api/admin/email/config
 * Returns redacted configuration + supported providers list
 */
export async function GET(request: NextRequest) {
  try {
    const auth = await adminAuthMiddleware(request, ['super_admin']);
    if (!auth.success || !auth.user) {
      return NextResponse.json({ error: auth.error }, { status: auth.status });
    }

    const cfg = await getEmailServiceConfig();
    const safeConfig = redactSecrets(cfg);

    // Compute ETag so the UI can short-circuit re-renders if nothing changed
    const etag = toETag({ config: safeConfig, providers: EMAIL_PROVIDERS });

    // If-None-Match handling (lightweight)
    const inm = request.headers.get('if-none-match');
    if (inm && inm === etag) {
      return new NextResponse(null, {
        status: 304,
        headers: {
          ETag: etag,
          'Cache-Control': 'no-store',
        },
      });
    }

    await auditLogger.log(
      auth.user.user_id,
      'email_config_viewed',
      'email_config',
      {
        details: { provider: cfg?.provider, enabled: !!cfg?.enabled },
        request,
      },
    );

    return NextResponse.json(
      {
        success: true,
        data: {
          config: safeConfig,
          providers: EMAIL_PROVIDERS,
        },
      },
      {
        headers: {
          ETag: etag,
          'Cache-Control': 'no-store',
          'X-Kari-Email-Config': '1',
        },
      },
    );
  } catch {
    return jsonError('Failed to get email configuration', 500);
  }
}

/**
 * PUT /api/admin/email/config
 * Partially updates configuration. Validates, optionally tests connectivity, then applies.
 * Body: UpdateEmailServiceConfigRequest
 * Query: ?testOnly=true to validate+test without saving (useful for UI flows)
 */
export async function PUT(request: NextRequest) {
  try {
    const auth = await adminAuthMiddleware(request, ['super_admin']);
    if (!auth.success || !auth.user) {
      return NextResponse.json({ error: auth.error }, { status: auth.status });
    }

    let body: UpdateEmailServiceConfigRequest;
    try {
      body = await request.json();
    } catch {
      return jsonError('Invalid JSON body', 400);
    }

    // testOnly mode lets UI validate credentials without committing
    const url = new URL(request.url);
    const testOnly = url.searchParams.get('testOnly') === 'true';

    const current = await getEmailServiceConfig();
    const merged: EmailServiceConfig = {
      ...current,
      ...body,
    };

    // Validate structure & required fields for the selected provider
    const validation = validateEmailConfig(merged);
    if (!validation.isValid) {
      return jsonError('Invalid email configuration', 400, validation.errors);
    }

    // If enabled or explicitly testOnly, perform a live connectivity test
    if (merged.enabled || testOnly) {
      const test = await testEmailService(merged);
      if (!test.is_connected) {
        return jsonError(
          testOnly ? 'Email service test failed' : 'Email service connection test failed',
          400,
          test.error_message ?? 'Connection check failed',
        );
      }
    }

    if (testOnly) {
      // No persistence, just a pass/fail response
      await auditLogger.log(
        auth.user.user_id,
        'email_config_tested',
        'email_config',
        {
          details: {
            provider: merged.provider,
            enabled: merged.enabled,
            result: 'connected',
            // never log secrets
          },
          request,
        },
      );
      return NextResponse.json(
        { success: true, message: 'Test passed. Configuration is valid and connectable.' },
        { headers: { 'Cache-Control': 'no-store' } },
      );
    }

    // Persist configuration via service abstraction
    await emailService.updateConfig(merged);

    // Audit without secret leakage
    await auditLogger.log(
      auth.user.user_id,
      'email_config_updated',
      'email_config',
      {
        details: {
          provider: merged.provider,
          enabled: merged.enabled,
          changes: summarizeChanges(body as Record<string, unknown>),
        },
        request,
      },
    );

    return NextResponse.json(
      {
        success: true,
        message: 'Email configuration updated successfully',
      },
      { headers: { 'Cache-Control': 'no-store' } },
    );
  } catch {
    return jsonError('Failed to update email configuration', 500);
  }
}

/**
 * OPTIONS preflight
 */
export async function OPTIONS() {
  return new NextResponse(null, {
    status: 204,
    headers: {
      Allow: 'GET,PUT,OPTIONS',
      'Access-Control-Max-Age': '86400',
    },
  });
}
