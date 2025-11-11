// ui_launchers/web_ui/src/app/api/admin/setup/create-super-admin/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { getAdminDatabaseUtils } from '@/lib/database/admin-utils';
import { validateSuperAdminCreation, hashPassword } from '@/lib/auth/setup-validation';
import type { CreateSuperAdminRequest, AdminApiResponse, User } from '@/types/admin';

export const dynamic = 'force-dynamic';

/**
 * Create the initial super admin account during first-run setup
 * POST /api/admin/setup/create-super-admin
 */
export async function POST(request: NextRequest) {
  try {
    const body: CreateSuperAdminRequest = await safeParseJson(request);

    // Validate the request data
    const validationResult = await validateSuperAdminCreation(body);
    if (!validationResult.isValid) {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Invalid super admin creation data',
            details: validationResult.errors,
          },
        },
        { status: 400 },
      );
    }

    const adminUtils = getAdminDatabaseUtils();

    // Double-check that no super admin exists (security measure)
    const existingSuperAdmins = await adminUtils.getUsersByRole('super_admin');
    if (Array.isArray(existingSuperAdmins) && existingSuperAdmins.length > 0) {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'SETUP_ALREADY_COMPLETED',
            message: 'Super admin already exists. First-run setup has been completed.',
            details: { existing_count: existingSuperAdmins.length },
          },
        },
        { status: 409 },
      );
    }

    // Check if email is already in use (any role)
    const existingUser = await adminUtils.getUsersWithRoleFilter({ search: body.email });
    const existingCount = existingUser?.data?.length ?? 0;
    if (existingCount > 0) {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'EMAIL_ALREADY_EXISTS',
            message: 'An account with this email address already exists',
            details: { email: body.email },
          },
        },
        { status: 409 },
      );
    }

    // Hash the password
    const passwordHash = await hashPassword(body.password);

    // Create the super admin user (temporary role = admin)
    const userId: string = await adminUtils.createUserWithRole({
      email: body.email,
      full_name: body.full_name,
      password_hash: passwordHash,
      role: 'admin', // will be escalated to super_admin immediately after creation
      tenant_id: 'default',
      created_by: 'system', // Special marker for system-created user
    });

    // Escalate to super_admin (bypasses normal RBAC restrictions)
    await adminUtils.updateUserRole(userId, 'super_admin', 'system');

    // Fetch the created user for response
    const createdUser = await adminUtils.getUserWithRole(userId);
    if (!createdUser) {
      throw new Error('Failed to retrieve created super admin user');
    }

    // Audit log
    await adminUtils.createAuditLog({
      user_id: userId,
      action: 'super_admin.first_run_setup',
      resource_type: 'user',
      resource_id: userId,
      details: {
        email: body.email,
        full_name: body.full_name,
        setup_method: 'first_run',
      },
      ip_address: getClientIP(request),
      user_agent: request.headers.get('user-agent') || undefined,
    });

    // Send email verification (best-effort; non-fatal on failure)
    try {
      await sendSuperAdminVerificationEmail(body.email, body.full_name, userId);
    } catch {
      // swallow email errors; setup must still succeed
    }

    // Prepare safe response shape
    const responseUser: Partial<User> = {
      user_id: createdUser.user_id,
      email: createdUser.email,
      full_name: createdUser.full_name,
      role: createdUser.role,
      is_verified: createdUser.is_verified,
      is_active: createdUser.is_active,
      created_at: createdUser.created_at,
    };

    const response: AdminApiResponse<{ user: Partial<User>; setup_completed: boolean }> = {
      success: true,
      data: {
        user: responseUser,
        setup_completed: true,
      },
      meta: {
        message: 'Super admin account created successfully',
        next_steps: [
          'Complete email verification',
          'Set up two-factor authentication',
          'Review system configuration',
        ],
      },
    };

    return NextResponse.json(response, {
      status: 201,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        Pragma: 'no-cache',
        Expires: '0',
      },
    });
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: {
          code: 'SUPER_ADMIN_CREATION_FAILED',
          message: 'Failed to create super admin account',
          details: { error: error instanceof Error ? error.message : 'Unknown error' },
        },
      },
      { status: 500 },
    );
  }
}

/** --------------------------
 * Helpers
 * ------------------------- */

/**
 * Extract client IP address from request
 */
function getClientIP(request: NextRequest): string {
  const forwarded = request.headers.get('x-forwarded-for');
  const realIP = request.headers.get('x-real-ip');
  const remoteAddr = request.headers.get('remote-addr');
  if (forwarded) return forwarded.split(',')[0].trim();
  return realIP || remoteAddr || 'unknown';
}

/**
 * Safe JSON parse with typed expectation
 */
async function safeParseJson<T>(request: NextRequest): Promise<T> {
  try {
    return (await request.json()) as T;
  } catch {
    throw new Error('Invalid JSON body');
  }
}

/**
 * Send email verification to newly created super admin
 */
async function sendSuperAdminVerificationEmail(email: string, fullName: string, userId: string): Promise<void> {
  const verificationToken = await generateEmailVerificationToken(email, userId);
  const baseUrl = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000';
  const verificationLink = `${baseUrl}/verify-email?token=${verificationToken}`;

  const emailTemplate = {
    id: 'super_admin_verification',
    name: 'Super Admin Email Verification',
    subject: 'Verify your Super Admin account - {{system_name}}',
    html_content: `
      <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background-color: #007bff; color: white; padding: 20px; border-radius: 4px 4px 0 0;">
          <h2 style="margin: 0;">🔐 Super Admin Account Created</h2>
        </div>
        <div style="border: 1px solid #007bff; border-top: none; padding: 20px; border-radius: 0 0 4px 4px;">
          <p>Hello {{full_name}},</p>
          <p>Your Super Administrator account has been successfully created for <strong>{{system_name}}</strong>.</p>
          <p><strong>Account Details:</strong></p>
          <ul>
            <li>Email: {{email}}</li>
            <li>Role: Super Administrator</li>
            <li>Created: {{created_date}}</li>
          </ul>
          <p>To complete your account setup and verify your email address, please click the button below:</p>
          <div style="text-align: center; margin: 30px 0;">
            <a href="{{verification_link}}" style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block;">Verify Email Address</a>
          </div>
          <p><strong>Important:</strong> This verification link will expire in 24 hours for security reasons.</p>
          <p>Once verified, you can:</p>
          <ul>
            <li>Access the Super Admin dashboard</li>
            <li>Manage other administrators</li>
            <li>Configure system settings</li>
            <li>View audit logs and security reports</li>
          </ul>
          <p>If you did not create this account, please ignore this email.</p>
        </div>
        <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
        <p style="color: #666; font-size: 12px;">This is an automated message from {{system_name}}. Please do not reply to this email.</p>
      </div>
    `,
    text_content: `
Hello {{full_name}},
Your Super Administrator account has been successfully created for {{system_name}}.
Account Details:
- Email: {{email}}
- Role: Super Administrator
- Created: {{created_date}}
To complete your account setup and verify your email address, please visit:
{{verification_link}}
Important: This verification link will expire in 24 hours for security reasons.
Once verified, you can:
- Access the Super Admin dashboard
- Manage other administrators
- Configure system settings
- View audit logs and security reports
If you did not create this account, please ignore this email.
This is an automated message from {{system_name}}. Please do not reply to this email.
    `,
    variables: ['full_name', 'system_name', 'email', 'created_date', 'verification_link'],
    template_type: 'email_verification' as const,
    is_active: true,
    created_by: 'system',
    created_at: new Date(),
    updated_at: new Date(),
  };

  const variables = {
    full_name: fullName,
    system_name: process.env.NEXT_PUBLIC_APP_NAME || 'AI Karen Admin',
    email,
    created_date: new Date().toLocaleDateString(),
    verification_link: verificationLink,
  };

  const { EmailService } = await import('@/lib/email/email-service');
  const emailService = new EmailService();
  await emailService.initialize();
  await emailService.sendTemplateEmail(email, emailTemplate, variables, { priority: 'high' });
}

/**
 * Generate a signed email verification token (base64url payload + random suffix)
 * Uses Web Crypto where available (Edge/Node18+)
 */
async function generateEmailVerificationToken(email: string, userId: string): Promise<string> {
  const expiresAt = Date.now() + 24 * 60 * 60 * 1000; // 24h
  const payload = { email, userId, type: 'email_verification', timestamp: Date.now(), expires: expiresAt };

  // base64url without padding
  const base64url = Buffer.from(JSON.stringify(payload)).toString('base64url');

  // 16 random bytes suffix
  const rand = await webcryptoGetRandomBytesHex(16);

  return `${base64url}.${rand}`;
}

async function webcryptoGetRandomBytesHex(len: number): Promise<string> {
  const bytes = new Uint8Array(len);
  // Prefer globalThis.crypto if available (Edge runtime / Node 18+)
  if (typeof globalThis.crypto?.getRandomValues === 'function') {
    globalThis.crypto.getRandomValues(bytes);
  } else {
    // Fallback to Node crypto
    const nodeCrypto = await import('crypto');
    const buf: Buffer = nodeCrypto.randomBytes(len);
    buf.copy(Buffer.from(bytes.buffer));
  }
  return Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}
