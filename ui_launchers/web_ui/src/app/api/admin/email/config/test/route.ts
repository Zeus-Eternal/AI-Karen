/**
 * Email Configuration Test API
 * 
 * API endpoint for testing email service configuration and connectivity.
 */
import { NextRequest, NextResponse } from 'next/server';
// Force this route to be dynamic
export const dynamic = 'force-dynamic';
import { adminAuthMiddleware } from '@/lib/middleware/admin-auth';
import { testEmailService, getEmailServiceConfig } from '@/lib/email/config';
import { emailService } from '@/lib/email/email-service';
import { auditLogger } from '@/lib/audit/audit-logger';
/**
 * POST /api/admin/email/config/test
 * Test email service configuration
 */
export async function POST(request: NextRequest) {
  try {
    const authResult = await adminAuthMiddleware(request, ['super_admin']);
    if (!authResult.success) {
      return NextResponse.json({ error: authResult.error }, { status: authResult.status });
    }
    const body = await request.json();
    const testEmail = body.test_email || authResult.user?.email;
    // Get current configuration
    const config = await getEmailServiceConfig();
    if (!config.enabled) {
      return NextResponse.json(
        { error: 'Email service is disabled' },
        { status: 400 }
      );
    }
    // Test service connection
    const healthResult = await testEmailService(config);
    // If connection test passes, send a test email
    let testEmailResult = null;
    if (healthResult.is_connected && testEmail) {
      try {
        // Initialize email service if needed
        if (!emailService.getConfig()) {
          await emailService.initialize();
        }
        testEmailResult = await emailService.sendEmail(
          testEmail,
          'Email Service Test',
          `
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
              <h2>Email Service Test</h2>
              <p>This is a test email to verify that your email service configuration is working correctly.</p>
              <p><strong>Test Details:</strong></p>
              <ul>
                <li>Provider: ${config.provider}</li>
                <li>From: ${config.from_email}</li>
                <li>Test Time: ${new Date().toLocaleString()}</li>
                <li>Tested by: ${authResult.user?.email || 'Unknown'}</li>
              </ul>
              <p>If you received this email, your email service is configured correctly!</p>
            </div>
          `,
          `Email Service Test
This is a test email to verify that your email service configuration is working correctly.
Test Details:
- Provider: ${config.provider}
- From: ${config.from_email}
- Test Time: ${new Date().toLocaleString()}
- Tested by: ${authResult.user?.email || 'Unknown'}
If you received this email, your email service is configured correctly!`,
          { priority: 'normal' }
        );
      } catch (error) {
        testEmailResult = {
          success: false,
          error: error instanceof Error ? error.message : 'Unknown error',
        };
      }
    }
    // Log audit event
    await auditLogger.log(
      authResult.user?.user_id || 'unknown',
      'email_config_tested',
      'email_config',
      {
        resourceId: undefined,
        details: { 
          provider: config.provider,
          connection_success: healthResult.is_connected,
          test_email_sent: !!testEmailResult?.success,
          test_email_recipient: testEmail
        },
        request: request
      }
    );
    return NextResponse.json({
      success: true,
      data: {
        connection_test: {
          success: healthResult.is_connected,
          provider: healthResult.provider,
          error_message: healthResult.error_message,
          last_test_at: healthResult.last_test_at,
        },
        test_email: testEmailResult ? {
          success: testEmailResult.success,
          message_id: testEmailResult.message_id,
          error: testEmailResult.error,
          recipient: testEmail,
        } : null,
      }
    });
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to test email configuration' },
      { status: 500 }
    );
  }
}
