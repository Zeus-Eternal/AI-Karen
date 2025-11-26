// ui_launchers/web_ui/src/app/api/admin/security/alerts/[id]/resolve/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { adminAuthMiddleware } from '@/lib/middleware/admin-auth';
import { getAdminUtils } from '@/lib/database/admin-utils';
import { getAuditLogger } from '@/lib/audit/audit-logger';

/**
 * Generate static params for alerts resolve route
 * Since we can't pre-generate all possible alert IDs, return empty array
 */
export function generateStaticParams() {
  // Return sample IDs for static generation
  return [
    { id: '1' },
    { id: '2' },
    { id: '3' }
  ];
}

// Explicitly set dynamic to auto for static export compatibility
export const dynamic = 'auto';

type ResolveBody = {
  resolutionNote?: string; // optional human note for audit trail
};

function getIp(request: NextRequest): string {
  return (
    request.headers.get('x-forwarded-for') ??
    request.headers.get('x-real-ip') ??
    'unknown'
  );
}

/**
 * POST /api/admin/security/alerts/[id]/resolve
 * Resolve a security alert (super_admin only)
 */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    // RBAC: super_admin required
    const authResult = await adminAuthMiddleware(request, 'super_admin');
    if (!authResult.success) {
      return NextResponse.json({ error: authResult.error?.message || 'Unauthorized' }, { status: authResult.status || 401 });
    }

    const { user: currentUser } = authResult;
    if (!currentUser?.user_id) {
      return NextResponse.json({ error: 'User not found' }, { status: 401 });
    }

    const resolvedParams = await params;
    const alertId = resolvedParams?.id;
    if (!alertId || typeof alertId !== 'string') {
      return NextResponse.json({ error: 'Alert ID is required' }, { status: 400 });
    }

    // Optional resolution note
    let body: ResolveBody = {};
    try {
      // If client sends no body, this will throw—swallow to allow empty body.
      body = (await request.json()) as ResolveBody;
    } catch {
      // no-op: empty body is allowed
    }
    const resolutionNote =
      typeof body.resolutionNote === 'string' ? body.resolutionNote.trim() : undefined;

    const adminUtils = getAdminUtils();
    const auditLogger = getAuditLogger();

    // Fetch alert
    const alert = await adminUtils.getSecurityAlert(alertId);
    if (!alert) {
      return NextResponse.json({ error: 'Security alert not found' }, { status: 404 });
    }

    if (alert.resolved) {
      // Enforce idempotency clarity; upstream code treated as 400,
      // but returning 409 better communicates state conflict.
      return NextResponse.json(
        { error: 'Alert is already resolved' },
        { status: 409 }
      );
    }

    // Resolve alert
    const resolvedAt = new Date().toISOString();
    await adminUtils.resolveSecurityAlert(alertId, currentUser.user_id, resolutionNote);

    // Audit log
    await auditLogger.log(
      currentUser.user_id,
      'security.alert.resolve',
      'security_alert',
      {
        resourceId: alertId,
        details: {
          alertType: alert.type,
          alertSeverity: alert.severity,
          originalMessage: alert.message,
          resolutionNote,
          resolvedAt,
        },
        ip_address: getIp(request),
        user_agent: request.headers.get('user-agent') ?? 'unknown',
      }
    );

    // Optionally re-read for response integrity (if supported)
    let updatedAlert: unknown = null;
    try {
      updatedAlert = await adminUtils.getSecurityAlert(alertId);
    } catch {
      // if not supported, we still return a stable response below
    }

    return NextResponse.json(
      {
        message: 'Security alert resolved successfully',
        alertId,
        resolvedBy: currentUser.user_id,
        resolvedAt,
        resolutionNote: resolutionNote ?? null,
        alert: updatedAlert ?? null,
      },
      { status: 200 }
    );
  } catch {
    return NextResponse.json(
      { error: 'Failed to resolve security alert' },
      { status: 500 }
    );
  }
}
