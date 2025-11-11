import { randomUUID } from 'crypto';
import { NextRequest, NextResponse } from 'next/server';
import { adminAuthMiddleware } from '@/lib/middleware/admin-auth';
import { getAdminUtils } from '@/lib/database/admin-utils';
import { AUDIT_ACTIONS, AUDIT_RESOURCE_TYPES, getAuditLogger } from '@/lib/audit/audit-logger';
import { emailIntegration } from '@/lib/email';
import { getBaseUrl } from '@/lib/email/config';
/**
 * POST /api/admin/admins/invite
 * 
 * Send an invitation to create a new admin account
 */
export async function POST(request: NextRequest) {
  try {
    // Check admin authentication and permissions
    const authResult = await adminAuthMiddleware(request, 'super_admin');
    if (authResult instanceof NextResponse) {
      return authResult;
    }
    const { user: currentUser } = authResult;
    if (!currentUser) {
      return NextResponse.json(
        { error: 'Authentication required' },
        { status: 401 }
      );
    }
    const body = await request.json();
    const email: string = typeof body.email === 'string' ? body.email.trim().toLowerCase() : '';
    const message: string | undefined = typeof body.message === 'string' && body.message.trim().length > 0
      ? body.message.trim()
      : undefined;
    const inviteeName: string | undefined = typeof body.fullName === 'string' && body.fullName.trim().length > 0
      ? body.fullName.trim()
      : undefined;

    if (!email) {
      return NextResponse.json(
        { error: 'Email is required' },
        { status: 400 }
      );
    }
    if (message && message.length > 1000) {
      return NextResponse.json(
        { error: 'Custom message must be 1000 characters or fewer' },
        { status: 400 }
      );
    }
    if (inviteeName && inviteeName.length > 150) {
      return NextResponse.json(
        { error: 'Full name must be 150 characters or fewer' },
        { status: 400 }
      );
    }
    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return NextResponse.json(
        { error: 'Invalid email format' },
        { status: 400 }
      );
    }
    const adminUtils = getAdminUtils();
    const auditLogger = getAuditLogger();
    // Check if user already exists
    const existingUser = await adminUtils.getUserByEmail(email);
    if (existingUser) {
      return NextResponse.json(
        { error: 'User with this email already exists' },
        { status: 409 }
      );
    }
    // Generate invitation token
    const invitationToken = randomUUID();
    const expiresAt = new Date();
    expiresAt.setDate(expiresAt.getDate() + 7); // 7 days expiration
    // Store invitation
    const invitation = await adminUtils.createAdminInvitation({
      email,
      token: invitationToken,
      invitedBy: currentUser.user_id,
      expiresAt,
      message,
    });

    const inviterName = currentUser.full_name?.trim() || currentUser.email;
    const resolvedInviteeName = inviteeName || email.split('@')[0] || email;
    const baseUrl = getBaseUrl();
    const invitationLink = new URL(`/admin/accept-invitation?token=${invitationToken}`, baseUrl).toString();

    await emailIntegration.initialize();
    const emailResult = await emailIntegration.sendAdminInvitation(
      email,
      resolvedInviteeName,
      inviterName,
      invitationLink,
      expiresAt,
      message
    );
    // Log the action
    await auditLogger.log(
      currentUser.user_id,
      AUDIT_ACTIONS.ADMIN_INVITE,
      AUDIT_RESOURCE_TYPES.ADMIN,
      {
        resourceId: invitation.id,
        details: {
          invitedEmail: email,
          hasCustomMessage: Boolean(message),
          emailDeliveryStatus: emailResult.success ? 'sent' : 'failed',
          emailDeliveryError: emailResult.error,
        },
        request,
        ip_address:
          request.headers.get('x-forwarded-for') ||
          request.headers.get('x-real-ip') ||
          undefined,
      }
    );

    if (!emailResult.success) {
      return NextResponse.json(
        {
          message: 'Admin invitation saved, but email delivery failed',
          invitationId: invitation.id,
          emailError: emailResult.error,
        },
        { status: 202 }
      );
    }

    return NextResponse.json({
      message: 'Admin invitation sent successfully',
      invitationId: invitation.id,
    });
  } catch {
    return NextResponse.json(
      { error: 'Failed to send admin invitation' },
      { status: 500 }
    );
  }
}
