/**
 * Email Integration Types
 * 
 * Type definitions for the email integration system including templates,
 * queue management, delivery tracking, and notification preferences.
 */

// Email template types
export interface EmailTemplate {
  id: string;
  name: string;
  subject: string;
  html_content: string;
  text_content: string;
  template_type: 'admin_invitation' | 'user_welcome' | 'security_alert' | 'password_reset' | 'email_verification';
  variables: string[]; // List of template variables like {{name}}, {{link}}
  is_active: boolean;
  created_at: Date;
  updated_at: Date;
  created_by: string;
}

// Email template variables interface
export interface EmailTemplateVariables {
  [key: string]: string | number | boolean | Date;
}

// Email message interface
export interface EmailMessage {
  id: string;
  to: string;
  from: string;
  reply_to?: string;
  subject: string;
  html_content: string;
  text_content: string;
  template_id?: string;
  template_variables?: EmailTemplateVariables;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  status: 'queued' | 'sending' | 'sent' | 'failed' | 'bounced' | 'delivered';
  scheduled_at?: Date;
  sent_at?: Date;
  delivered_at?: Date;
  failed_at?: Date;
  error_message?: string;
  retry_count: number;
  max_retries: number;
  created_at: Date;
  updated_at: Date;
}

// Email queue configuration
export interface EmailQueueConfig {
  max_retries: number;
  retry_delay_minutes: number;
  batch_size: number;
  rate_limit_per_minute: number;
  priority_processing: boolean;
}

// Email service configuration
export interface EmailServiceConfig {
  provider: 'smtp' | 'sendgrid' | 'ses' | 'mailgun' | 'postmark';
  smtp_host?: string;
  smtp_port?: number;
  smtp_secure?: boolean;
  smtp_user?: string;
  smtp_password?: string;
  api_key?: string;
  api_secret?: string;
  from_email: string;
  from_name: string;
  reply_to_email?: string;
  enabled: boolean;
  test_mode: boolean;
}

// Email delivery status tracking
export interface EmailDeliveryStatus {
  message_id: string;
  status: 'sent' | 'delivered' | 'opened' | 'clicked' | 'bounced' | 'complained' | 'failed';
  timestamp: Date;
  details?: Record<string, any>;
  webhook_data?: Record<string, any>;
}

// Email notification types
export type EmailNotificationType = 
  | 'admin_invitation'
  | 'user_welcome'
  | 'user_created'
  | 'role_changed'
  | 'account_locked'
  | 'security_alert'
  | 'password_reset'
  | 'email_verification'
  | 'bulk_operation_complete'
  | 'system_maintenance'
  | 'audit_report';

// Email notification interface
export interface EmailNotification {
  id: string;
  type: EmailNotificationType;
  recipient_email: string;
  recipient_user_id?: string;
  subject: string;
  content: string;
  template_id?: string;
  template_variables?: EmailTemplateVariables;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  send_immediately: boolean;
  scheduled_at?: Date;
  created_by: string;
  created_at: Date;
  
  // Populated fields
  message?: EmailMessage;
  created_by_user?: {
    user_id: string;
    email: string;
    full_name?: string;
  };
}

// Email template customization interface
export interface EmailTemplateCustomization {
  template_id: string;
  custom_subject?: string;
  custom_html_content?: string;
  custom_text_content?: string;
  custom_variables?: EmailTemplateVariables;
  is_active: boolean;
  updated_by: string;
  updated_at: Date;
}

// Email preferences interface
export interface EmailPreferences {
  user_id: string;
  admin_notifications: boolean;
  security_alerts: boolean;
  user_activity_digest: boolean;
  system_maintenance: boolean;
  marketing_emails: boolean;
  digest_frequency: 'daily' | 'weekly' | 'monthly' | 'never';
  preferred_time: string; // HH:MM format
  timezone: string;
  updated_at: Date;
}

// Email statistics interface
export interface EmailStatistics {
  total_sent: number;
  total_delivered: number;
  total_failed: number;
  total_bounced: number;
  delivery_rate: number;
  bounce_rate: number;
  open_rate?: number;
  click_rate?: number;
  by_template: Array<{
    template_id: string;
    template_name: string;
    sent: number;
    delivered: number;
    failed: number;
  }>;
  by_day: Array<{
    date: string;
    sent: number;
    delivered: number;
    failed: number;
  }>;
}

// Email validation interface
export interface EmailValidation {
  email: string;
  is_valid: boolean;
  is_disposable: boolean;
  is_role_based: boolean;
  domain: string;
  mx_records_exist: boolean;
  validation_timestamp: Date;
}

// Bulk email operation interface
export interface BulkEmailOperation {
  id: string;
  operation_type: 'invitation' | 'notification' | 'announcement';
  template_id: string;
  recipient_count: number;
  sent_count: number;
  failed_count: number;
  status: 'queued' | 'processing' | 'completed' | 'failed' | 'cancelled';
  created_by: string;
  created_at: Date;
  started_at?: Date;
  completed_at?: Date;
  error_message?: string;
  
  // Configuration
  batch_size: number;
  delay_between_batches: number;
  
  // Recipients
  recipients: Array<{
    email: string;
    user_id?: string;
    template_variables?: EmailTemplateVariables;
    status: 'pending' | 'sent' | 'failed';
    error_message?: string;
  }>;
}

// Email webhook interface for delivery tracking
export interface EmailWebhook {
  id: string;
  provider: string;
  event_type: string;
  message_id: string;
  email: string;
  timestamp: Date;
  data: Record<string, any>;
  processed: boolean;
  processed_at?: Date;
  created_at: Date;
}

// Email template validation interface
export interface EmailTemplateValidation {
  template_id: string;
  is_valid: boolean;
  errors: string[];
  warnings: string[];
  missing_variables: string[];
  unused_variables: string[];
  html_issues: string[];
  text_issues: string[];
  validated_at: Date;
}

// Email service health interface
export interface EmailServiceHealth {
  provider: string;
  is_connected: boolean;
  last_test_at: Date;
  test_result: 'success' | 'failure';
  error_message?: string;
  queue_size: number;
  processing_rate: number;
  failure_rate: number;
  last_successful_send?: Date;
}

// Email API response interfaces
export interface SendEmailResponse {
  success: boolean;
  message_id?: string;
  error?: string;
  retry_after?: number;
}

export interface EmailTemplateResponse {
  success: boolean;
  template?: EmailTemplate;
  error?: string;
}

export interface EmailQueueResponse {
  success: boolean;
  queued_count: number;
  failed_count: number;
  errors: string[];
}

// Email event types for audit logging
export type EmailEventType = 
  | 'template_created'
  | 'template_updated'
  | 'template_deleted'
  | 'email_sent'
  | 'email_failed'
  | 'bulk_operation_started'
  | 'bulk_operation_completed'
  | 'webhook_received'
  | 'service_configured'
  | 'queue_processed';

// Email audit log interface
export interface EmailAuditLog {
  id: string;
  event_type: EmailEventType;
  user_id?: string;
  email_address?: string;
  template_id?: string;
  message_id?: string;
  details: Record<string, any>;
  ip_address?: string;
  user_agent?: string;
  timestamp: Date;
}

// Request interfaces for API endpoints
export interface CreateEmailTemplateRequest {
  name: string;
  subject: string;
  html_content: string;
  text_content: string;
  template_type: EmailTemplate['template_type'];
  variables: string[];
}

export interface UpdateEmailTemplateRequest {
  name?: string;
  subject?: string;
  html_content?: string;
  text_content?: string;
  variables?: string[];
  is_active?: boolean;
}

export interface SendEmailRequest {
  to: string;
  template_id?: string;
  template_variables?: EmailTemplateVariables;
  subject?: string;
  html_content?: string;
  text_content?: string;
  priority?: EmailMessage['priority'];
  scheduled_at?: Date;
}

export interface BulkEmailRequest {
  template_id: string;
  recipients: Array<{
    email: string;
    user_id?: string;
    template_variables?: EmailTemplateVariables;
  }>;
  batch_size?: number;
  delay_between_batches?: number;
}

export interface UpdateEmailServiceConfigRequest {
  provider?: EmailServiceConfig['provider'];
  smtp_host?: string;
  smtp_port?: number;
  smtp_secure?: boolean;
  smtp_user?: string;
  smtp_password?: string;
  api_key?: string;
  api_secret?: string;
  from_email?: string;
  from_name?: string;
  reply_to_email?: string;
  enabled?: boolean;
  test_mode?: boolean;
}

// Filter interfaces
export interface EmailMessageFilter {
  status?: EmailMessage['status'];
  template_id?: string;
  recipient_email?: string;
  priority?: EmailMessage['priority'];
  created_after?: Date;
  created_before?: Date;
  sent_after?: Date;
  sent_before?: Date;
}

export interface EmailTemplateFilter {
  template_type?: EmailTemplate['template_type'];
  is_active?: boolean;
  created_by?: string;
  search?: string;
}

// Error types for email operations
export type EmailErrorType = 
  | 'invalid_email_address'
  | 'template_not_found'
  | 'template_validation_failed'
  | 'service_not_configured'
  | 'service_unavailable'
  | 'rate_limit_exceeded'
  | 'quota_exceeded'
  | 'invalid_template_variables'
  | 'delivery_failed'
  | 'webhook_validation_failed';

export interface EmailError {
  type: EmailErrorType;
  message: string;
  details?: Record<string, any>;
  retry_after?: number;
}

// Template validation result (alias for EmailTemplateValidation)
export type TemplateValidationResult = EmailTemplateValidation;

// Template render result
export interface TemplateRenderResult {
  html: string;
  text: string;
  subject: string;
  success: boolean;
  error?: string;
}