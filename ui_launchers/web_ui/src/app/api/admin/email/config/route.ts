import { NextRequest, NextResponse } from 'next/server';
import { adminAuthMiddleware } from '@/lib/middleware/admin-auth';
import { emailService } from '@/lib/email/email-service';
import { auditLogger } from '@/lib/audit/audit-logger';
/**
 * Email Configuration API
 * 
 * API endpoints for managing email service configuration including
 * provider settings, testing connections, and service health monitoring.
 */
import { EmailServiceConfig, UpdateEmailServiceConfigRequest } from '@/lib/email/types';
import { getEmailServiceConfig, validateEmailConfig, testEmailService, EMAIL_PROVIDERS } from '@/lib/email/config';


/**
 * GET /api/admin/email/config
 * Get email service configuration
 */
export async function GET(request: NextRequest) {
  try {
    const authResult = await adminAuthMiddleware(request, ['super_admin']);
    if (!authResult.success || !authResult.user) {
      return NextResponse.json({ error: authResult.error }, { status: authResult.status });
    }
    const config = await getEmailServiceConfig();
    // Remove sensitive information from response
    const safeConfig = {
      ...config,
      smtp_password: config.smtp_password ? '***' : '',
      api_key: config.api_key ? '***' : '',
      api_secret: config.api_secret ? '***' : '',
    };
    // Log audit event
    await auditLogger.log(
      authResult.user?.user_id || 'unknown',
      'email_config_viewed',
      'email_config',
      {
        resourceId: undefined,
        details: { provider: config.provider },
        request: request
      }
    );
    return NextResponse.json({
      success: true,
      data: {
        config: safeConfig,
        providers: EMAIL_PROVIDERS,
      }

  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to get email configuration' },
      { status: 500 }
    );
  }
}
/**
 * PUT /api/admin/email/config
 * Update email service configuration
 */
export async function PUT(request: NextRequest) {
  try {
    const authResult = await adminAuthMiddleware(request, ['super_admin']);
    if (!authResult.success || !authResult.user) {
      return NextResponse.json({ error: authResult.error }, { status: authResult.status });
    }
    const body: UpdateEmailServiceConfigRequest = await request.json();
    // Get current configuration
    const currentConfig = await getEmailServiceConfig();
    // Merge with new configuration
    const newConfig: EmailServiceConfig = {
      ...currentConfig,
      ...body,
    };
    // Validate configuration
    const validation = validateEmailConfig(newConfig);
    if (!validation.isValid) {
      return NextResponse.json(
        { 
          error: 'Invalid email configuration',
          details: validation.errors
        },
        { status: 400 }
      );
    }
    // Test configuration if enabled
    if (newConfig.enabled) {
      const testResult = await testEmailService(newConfig);
      if (!testResult.is_connected) {
        return NextResponse.json(
          { 
            error: 'Email service connection test failed',
            details: testResult.error_message
          },
          { status: 400 }
        );
      }
    }
    // Update email service configuration
    await emailService.updateConfig(newConfig);
    // In a real implementation, save to database here
    // Log audit event
    await auditLogger.log(
      authResult.user?.user_id || 'unknown',
      'email_config_updated',
      'email_config',
      {
        details: { 
          provider: newConfig.provider,
          enabled: newConfig.enabled,
          changes: Object.keys(body)
        },
        request
      }
    );
    return NextResponse.json({
      success: true,
      message: 'Email configuration updated successfully'

  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to update email configuration' },
      { status: 500 }
    );
  }
}
