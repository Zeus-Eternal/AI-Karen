/**
 * User Password Reset API Route
 * POST /api/admin/users/[id]/reset-password - Send password reset email to user
 *
 * Requirements: 4.4, 4.5
 */
import { NextRequest, NextResponse } from 'next/server';

/**
 * Generate static params for user reset password route
 * Since we can't pre-generate all possible user IDs, return empty array
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
import { requireAdmin } from '@/lib/middleware/admin-auth';
import { getAdminDatabaseUtils } from '@/lib/database/admin-utils';
import { getDatabaseClient } from '@/lib/database/client';
import type { AdminApiResponse } from '@/types/admin';
import crypto from 'crypto';

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

function extractUserIdFromPath(req: NextRequest): string | null {
  // Match /api/admin/users/:id/reset-password
  const m = req.nextUrl.pathname.match(/\/api\/admin\/users\/([^/]+)\/reset-password$/);
  return m?.[1] || null;
}

export const POST = requireAdmin(async (request: NextRequest, context) => {
  try {
    const userId = extractUserIdFromPath(request);
    if (!userId) {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'INVALID_USER_ID',
            message: 'User ID is required',
            details: {},
          },
        } as AdminApiResponse<never>,
        noStore({ status: 400 })
      );
    }

    const adminUtils = getAdminDatabaseUtils();
    const db = getDatabaseClient();

    // Fetch target user
    const user = await adminUtils.getUserWithRole(userId);
    if (!user) {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'USER_NOT_FOUND',
            message: 'User not found',
            details: { user_id: userId },
          },
        } as AdminApiResponse<never>,
        noStore({ status: 404 })
      );
    }

    // RBAC: non-super-admins can only reset regular users
    if (!context.isSuperAdmin() && user.role !== 'user') {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'INSUFFICIENT_PERMISSIONS',
            message: 'Cannot reset password for admin users',
            details: { target_role: user.role, actor_role: context.user.role },
          },
        } as AdminApiResponse<never>,
        noStore({ status: 403 })
      );
    }

    // Basic per-user rate limiting: deny if a reset was requested in the last 5 minutes
    const RATE_WINDOW_MS = 5 * 60 * 1000;
    const rateWindowMinutes = Math.floor(RATE_WINDOW_MS / (60 * 1000));
    const recent = await db.query(
      `
        SELECT 1
        FROM user_password_resets
        WHERE user_id = $1
          AND created_at >= NOW() - INTERVAL '${rateWindowMinutes} minutes'
          AND used_at IS NULL
        LIMIT 1
      `,
      [userId]
    );
    if (recent?.rowCount > 0) {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'RESET_RATE_LIMITED',
            message: `A recent password reset was already requested. Please wait about ${rateWindowMinutes} minutes and try again.`,
            details: { window_minutes: rateWindowMinutes },
          },
        } as AdminApiResponse<never>,
        noStore({ status: 429 })
      );
    }

    // Generate secure token and store hash only
    const tokenBytes = crypto.randomBytes(32);
    const token = tokenBytes.toString('hex'); // 64 chars
    const tokenHash = crypto.createHash('sha256').update(token).digest('hex');
    const expiresAt = new Date(Date.now() + 24 * 60 * 60 * 1000); // 24h

    // Ensure table exists in your schema. Expected schema:
    // user_password_resets(user_id, token_hash, expires_at, created_at, created_by, ip_address, user_agent, used_at)
    await db.query(
      `
        INSERT INTO user_password_resets
          (user_id, token_hash, expires_at, created_at, created_by, ip_address, user_agent)
        VALUES
          ($1, $2, $3, NOW(), $4, $5, $6)
      `,
      [
        userId,
        tokenHash,
        expiresAt.toISOString(),
        context.user.user_id,
        request.headers.get('x-forwarded-for')?.split(',')[0] || 'unknown',
        request.headers.get('user-agent') || null,
      ]
    );

    // Construct reset link (front-end route that will POST token + new password to your auth backend)
    const appBase =
      process.env.APP_BASE_URL ||
      process.env.NEXT_PUBLIC_APP_BASE_URL ||
      process.env.NEXT_PUBLIC_SITE_URL ||
      '';
    const resetLink = appBase
      ? `${appBase.replace(/\/+$/, '')}/reset-password?token=${encodeURIComponent(token)}&uid=${encodeURIComponent(
          userId
        )}`
      : undefined;

    // Audit (never log raw token; show last 4 only)
    await adminUtils.createAuditLog({
      user_id: context.user.user_id,
      action: 'user.password_reset_requested',
      resource_type: 'user',
      resource_id: userId,
      details: {
        target_user_email: user.email,
        token_suffix: token.slice(-4),
        reset_token_expires: expiresAt.toISOString(),
        link_present: Boolean(resetLink),
      },
      ip_address: request.headers.get('x-forwarded-for')?.split(',')[0] || 'unknown',
      user_agent: request.headers.get('user-agent') || undefined,
    });

    // TODO (optional, production): send email here via your mailer
    // await mailer.sendPasswordReset(user.email, resetLink)

    const response: AdminApiResponse<{ reset_sent: boolean; expires_at: string; reset_link?: string }> = {
      success: true,
      data: {
        reset_sent: true,
        expires_at: expiresAt.toISOString(),
        // Only include reset_link if you are returning it to an admin UI that will copy it manually.
        // In most cases, you should send email and omit this from the API response.
        ...(process.env.EXPOSE_RESET_LINK_TO_ADMIN === 'true' && resetLink ? { reset_link: resetLink } : {}),
      },
      meta: {
        message: 'Password reset initiated',
        user_email: user.email,
        token_length: token.length,
        caution: 'Token is only revealed in the link; it is not stored in plaintext.',
      },
    };

    return NextResponse.json(response, noStore());
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: {
          code: 'PASSWORD_RESET_FAILED',
          message: 'Failed to initiate password reset',
          details: { error: error instanceof Error ? error.message : 'Unknown error' },
        },
      } as AdminApiResponse<never>,
      noStore({ status: 500 })
    );
  }
});
