/**
 * Email Service Configuration
 * 
 * Configuration management for email services including SMTP, API providers,
 * and service health monitoring.
 */
import { EmailServiceConfig, EmailQueueConfig, EmailServiceHealth } from './types';
// Default email service configuration
export const DEFAULT_EMAIL_CONFIG: EmailServiceConfig = {
  provider: 'smtp',
  smtp_host: process.env.SMTP_HOST || 'localhost',
  smtp_port: parseInt(process.env.SMTP_PORT || '587'),
  smtp_secure: process.env.SMTP_SECURE === 'true',
  smtp_user: process.env.SMTP_USER || '',
  smtp_password: process.env.SMTP_PASSWORD || '',
  api_key: process.env.EMAIL_API_KEY || '',
  api_secret: process.env.EMAIL_API_SECRET || '',
  from_email: process.env.EMAIL_FROM || 'noreply@ai-karen.com',
  from_name: process.env.EMAIL_FROM_NAME || 'AI Karen Admin',
  reply_to_email: process.env.EMAIL_REPLY_TO || '',
  enabled: process.env.EMAIL_ENABLED !== 'false',
  test_mode: process.env.EMAIL_ === 'true',
};
// Default email queue configuration
export const DEFAULT_QUEUE_CONFIG: EmailQueueConfig = {
  max_retries: parseInt(process.env.EMAIL_MAX_RETRIES || '3'),
  retry_delay_minutes: parseInt(process.env.EMAIL_RETRY_DELAY || '5'),
  batch_size: parseInt(process.env.EMAIL_BATCH_SIZE || '10'),
  rate_limit_per_minute: parseInt(process.env.EMAIL_RATE_LIMIT || '60'),
  priority_processing: process.env.EMAIL_PRIORITY_PROCESSING === 'true',
};
// Email provider configurations
export const EMAIL_PROVIDERS = {
  smtp: {
    name: 'SMTP',
    description: 'Generic SMTP server',
    required_fields: ['smtp_host', 'smtp_port', 'smtp_user', 'smtp_password'],
    optional_fields: ['smtp_secure'],
  },
  sendgrid: {
    name: 'SendGrid',
    description: 'SendGrid email service',
    required_fields: ['api_key'],
    optional_fields: [],
  },
  ses: {
    name: 'Amazon SES',
    description: 'Amazon Simple Email Service',
    required_fields: ['api_key', 'api_secret'],
    optional_fields: [],
  },
  mailgun: {
    name: 'Mailgun',
    description: 'Mailgun email service',
    required_fields: ['api_key'],
    optional_fields: [],
  },
  postmark: {
    name: 'Postmark',
    description: 'Postmark email service',
    required_fields: ['api_key'],
    optional_fields: [],
  },
} as const;
// Email template defaults
export const DEFAULT_TEMPLATES = {
  admin_invitation: {
    name: 'Admin Invitation',
    subject: 'You have been invited to join {{system_name}} as an administrator',
    html_content: `
      <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2>Administrator Invitation</h2>
        <p>Hello {{full_name}},</p>
        <p>You have been invited to join <strong>{{system_name}}</strong> as an administrator by {{invited_by_name}}.</p>
        <p>To accept this invitation and set up your account, please click the button below:</p>
        <div style="text-align: center; margin: 30px 0;">
          <a href="{{invitation_link}}" style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block;">Accept Invitation</a>
        </div>
        <p>This invitation will expire on {{expiry_date}}.</p>
        <p>If you have any questions, please contact your system administrator.</p>
        <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
        <p style="color: #666; font-size: 12px;">This is an automated message from {{system_name}}. Please do not reply to this email.</p>
      </div>
    `,
    text_content: `
Hello {{full_name}},
You have been invited to join {{system_name}} as an administrator by {{invited_by_name}}.
To accept this invitation and set up your account, please visit:
{{invitation_link}}
This invitation will expire on {{expiry_date}}.
If you have any questions, please contact your system administrator.
This is an automated message from {{system_name}}. Please do not reply to this email.
    `,
    variables: ['full_name', 'system_name', 'invited_by_name', 'invitation_link', 'expiry_date'],
  },
  user_welcome: {
    name: 'User Welcome',
    subject: 'Welcome to {{system_name}}!',
    html_content: `
      <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2>Welcome to {{system_name}}!</h2>
        <p>Hello {{full_name}},</p>
        <p>Your account has been successfully created by {{created_by_name}}.</p>
        <p><strong>Account Details:</strong></p>
        <ul>
          <li>Email: {{email}}</li>
          <li>Role: {{role}}</li>
          <li>Account Created: {{created_date}}</li>
        </ul>
        <p>To get started, please click the button below to set up your password:</p>
        <div style="text-align: center; margin: 30px 0;">
          <a href="{{setup_link}}" style="background-color: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block;">Set Up Password</a>
        </div>
        <p>If you have any questions, please contact your administrator.</p>
        <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
        <p style="color: #666; font-size: 12px;">This is an automated message from {{system_name}}. Please do not reply to this email.</p>
      </div>
    `,
    text_content: `
Welcome to {{system_name}}!
Hello {{full_name}},
Your account has been successfully created by {{created_by_name}}.
Account Details:
- Email: {{email}}
- Role: {{role}}
- Account Created: {{created_date}}
To get started, please visit the following link to set up your password:
{{setup_link}}
If you have any questions, please contact your administrator.
This is an automated message from {{system_name}}. Please do not reply to this email.
    `,
    variables: ['full_name', 'system_name', 'created_by_name', 'email', 'role', 'created_date', 'setup_link'],
  },
  security_alert: {
    name: 'Security Alert',
    subject: 'Security Alert: {{alert_type}} - {{system_name}}',
    html_content: `
      <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background-color: #dc3545; color: white; padding: 15px; border-radius: 4px 4px 0 0;">
          <h2 style="margin: 0;">🚨 Security Alert</h2>
        </div>
        <div style="border: 1px solid #dc3545; border-top: none; padding: 20px; border-radius: 0 0 4px 4px;">
          <p><strong>Alert Type:</strong> {{alert_type}}</p>
          <p><strong>Time:</strong> {{alert_time}}</p>
          <p><strong>User:</strong> {{user_email}}</p>
          <p><strong>IP Address:</strong> {{ip_address}}</p>
          <p><strong>Description:</strong></p>
          <p>{{alert_description}}</p>
          {{#if action_required}}
          <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 4px; margin: 20px 0;">
            <p style="margin: 0;"><strong>Action Required:</strong> {{action_required}}</p>
          </div>
          {{/if}}
          <p>If this was not you, please contact your system administrator immediately.</p>
        </div>
        <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
        <p style="color: #666; font-size: 12px;">This is an automated security alert from {{system_name}}. Please do not reply to this email.</p>
      </div>
    `,
    text_content: `
🚨 SECURITY ALERT 🚨
Alert Type: {{alert_type}}
Time: {{alert_time}}
User: {{user_email}}
IP Address: {{ip_address}}
Description:
{{alert_description}}
{{#if action_required}}
ACTION REQUIRED: {{action_required}}
{{/if}}
If this was not you, please contact your system administrator immediately.
This is an automated security alert from {{system_name}}. Please do not reply to this email.
    `,
    variables: ['alert_type', 'alert_time', 'user_email', 'ip_address', 'alert_description', 'action_required', 'system_name'],
  },
} as const;
// Email validation patterns
export const EMAIL_VALIDATION = {
  email_regex: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  disposable_domains: [
    '10minutemail.com',
    'guerrillamail.com',
    'mailinator.com',
    'tempmail.org',
    'throwaway.email',
  ],
  role_based_prefixes: [
    'admin',
    'administrator',
    'support',
    'help',
    'info',
    'contact',
    'sales',
    'marketing',
    'noreply',
    'no-reply',
  ],
};
// Rate limiting configuration
export const RATE_LIMITS = {
  per_user_per_hour: 10,
  per_template_per_hour: 100,
  bulk_operations_per_day: 5,
  admin_notifications_per_hour: 50,
};
// Email service health check configuration
export const HEALTH_CHECK_CONFIG = {
  interval_minutes: 5,
  timeout_seconds: 30,
  failure_threshold: 3,
  recovery_threshold: 2,
};
/**
 * Get email service configuration from environment variables and database
 */
export async function getEmailServiceConfig(): Promise<EmailServiceConfig> {
  // In a real implementation, this would fetch from the database
  // and merge with environment variables
  return {
    ...DEFAULT_EMAIL_CONFIG,
    // Override with database values if available
  };
}
/**
 * Validate email service configuration
 */
export function validateEmailConfig(config: Partial<EmailServiceConfig>): { isValid: boolean; errors: string[] } {
  const errors: string[] = [];
  if (!config.provider) {
    errors.push('Email provider is required');
  } else if (!(config.provider in EMAIL_PROVIDERS)) {
    errors.push('Invalid email provider');
  } else {
    const provider = EMAIL_PROVIDERS[config.provider];
    // Check required fields
    for (const field of provider.required_fields) {
      if (!config[field as keyof EmailServiceConfig]) {
        errors.push(`${field} is required for ${provider.name}`);
      }
    }
  }
  if (!config.from_email) {
    errors.push('From email address is required');
  } else if (!EMAIL_VALIDATION.email_regex.test(config.from_email)) {
    errors.push('Invalid from email address format');
  }
  if (config.reply_to_email && !EMAIL_VALIDATION.email_regex.test(config.reply_to_email)) {
    errors.push('Invalid reply-to email address format');
  }
  return {
    isValid: errors.length === 0,
    errors,
  };
}
/**
 * Test email service connection
 */
export async function testEmailService(config: EmailServiceConfig): Promise<EmailServiceHealth> {
  const startTime = Date.now();
  try {
    // This would implement actual connection testing based on provider
    // For now, return a mock response
    const isConnected = config.enabled && config.from_email !== '';
    return {
      provider: config.provider,
      is_connected: isConnected,
      last_test_at: new Date(),
      test_result: isConnected ? 'success' : 'failure',
      error_message: isConnected ? undefined : 'Service not properly configured',
      queue_size: 0,
      processing_rate: 0,
      failure_rate: 0,
      last_successful_send: isConnected ? new Date() : undefined,
    };
  } catch (error) {
    return {
      provider: config.provider,
      is_connected: false,
      last_test_at: new Date(),
      test_result: 'failure',
      error_message: error instanceof Error ? error.message : 'Unknown error',
      queue_size: 0,
      processing_rate: 0,
      failure_rate: 0,
    };
  }
}
/**
 * Get system name for email templates
 */
export function getSystemName(): string {
  return process.env.SYSTEM_NAME || 'AI Karen Admin System';
}
/**
 * Get base URL for email links
 */
export function getBaseUrl(): string {
  return process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:8000';
}
