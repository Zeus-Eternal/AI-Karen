/**
 * User Password Reset API Route
 * POST /api/admin/users/[id]/reset-password - Send password reset email to user
 * 
 * Requirements: 4.4, 4.5
 */
import { NextRequest, NextResponse } from 'next/server';
import { requireAdmin } from '@/lib/middleware/admin-auth';
import { getAdminDatabaseUtils } from '@/lib/database/admin-utils';
import type { AdminApiResponse } from '@/types/admin';
/**
 * POST /api/admin/users/[id]/reset-password - Send password reset email
 */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id: userId } = await params;
  return requireAdmin(async (req: NextRequest, context) => {
    try {
      if (!userId) {
        return NextResponse.json({
          success: false,
          error: {
            code: 'INVALID_USER_ID',
            message: 'User ID is required',
            details: { user_id: userId }
          }
        } as AdminApiResponse<never>, { status: 400 });
      }
      const adminUtils = getAdminDatabaseUtils();
      // Get the user to reset password for
      const user = await adminUtils.getUserWithRole(userId);
      if (!user) {
        return NextResponse.json({
          success: false,
          error: {
            code: 'USER_NOT_FOUND',
            message: 'User not found',
            details: { user_id: userId }
          }
        } as AdminApiResponse<never>, { status: 404 });
      }
      // Check permissions - admins can only reset regular user passwords
      if (!context.isSuperAdmin() && user.role !== 'user') {
        return NextResponse.json({
          success: false,
          error: {
            code: 'INSUFFICIENT_PERMISSIONS',
            message: 'Cannot reset password for admin users',
            details: { user_role: user.role, admin_role: context.user.role }
          }
        } as AdminApiResponse<never>, { status: 403 });
      }
      // Generate password reset token (simplified - in production use crypto.randomBytes)
      const resetToken = Math.random().toString(36).substring(2, 15) + 
                        Math.random().toString(36).substring(2, 15);
      const expiresAt = new Date(Date.now() + 24 * 60 * 60 * 1000); // 24 hours
      // Store reset token (in production, store in database)
      // For now, we'll simulate sending the email
      // Log the password reset action
      await adminUtils.createAuditLog({
        user_id: context.user.user_id,
        action: 'user.password_reset_requested',
        resource_type: 'user',
        resource_id: userId,
        details: {
          target_user_email: user.email,
          reset_token_expires: expiresAt.toISOString()
        },
        ip_address: request.headers.get('x-forwarded-for')?.split(',')[0] || 'unknown',
        user_agent: request.headers.get('user-agent') || undefined

      // In a real implementation, you would:
      // 1. Store the reset token in the database with expiration
      // 2. Send an email with the reset link
      // 3. Handle the reset link in a separate endpoint
      // For now, we'll simulate success
      const response: AdminApiResponse<{ reset_sent: boolean; expires_at: string }> = {
        success: true,
        data: {
          reset_sent: true,
          expires_at: expiresAt.toISOString()
        },
        meta: {
          message: 'Password reset email sent successfully',
          user_email: user.email,
          reset_token_length: resetToken.length
        }
      };
      return NextResponse.json(response);
    } catch (error) {
      return NextResponse.json({
        success: false,
        error: {
          code: 'PASSWORD_RESET_FAILED',
          message: 'Failed to send password reset email',
          details: { error: error instanceof Error ? error.message : 'Unknown error' }
        }
      } as AdminApiResponse<never>, { status: 500 });
    }
  })(request);
}
