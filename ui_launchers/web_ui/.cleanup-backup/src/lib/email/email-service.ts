/**
 * Email Service Implementation
 * 
 * Core email service for sending emails, managing templates, and handling
 * different email providers (SMTP, SendGrid, SES, etc.).
 */

import { 
  EmailMessage, 
  EmailServiceConfig, 
  SendEmailResponse, 
  EmailTemplate,
  EmailTemplateVariables,
  EmailNotification,
  EmailNotificationType,
  BulkEmailOperation,
  EmailServiceHealth
} from './types';
import { TemplateEngine, EmailTemplateManager } from './template-engine';
import { getEmailServiceConfig, testEmailService } from './config';

/**
 * Email Service Provider Interface
 */
interface EmailProvider {
  send(message: EmailMessage): Promise<SendEmailResponse>;
  testConnection(): Promise<boolean>;
}

/**
 * SMTP Email Provider
 */
class SMTPProvider implements EmailProvider {
  constructor(private config: EmailServiceConfig) {}
  
  async send(message: EmailMessage): Promise<SendEmailResponse> {
    // In a real implementation, this would use nodemailer or similar
    // For now, return a mock response
    if (this.config.test_mode) {
      console.log('SMTP Test Mode - Email would be sent:', {
        to: message.to,
        subject: message.subject,
        html: message.html_content.substring(0, 100) + '...',
      });
      
      return {
        success: true,
        message_id: `smtp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      };
    }
    
    // Simulate sending
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          success: true,
          message_id: `smtp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        });
      }, 100);
    });
  }
  
  async testConnection(): Promise<boolean> {
    return this.config.enabled && !!this.config.smtp_host;
  }
}

/**
 * SendGrid Email Provider
 */
class SendGridProvider implements EmailProvider {
  constructor(private config: EmailServiceConfig) {}
  
  async send(message: EmailMessage): Promise<SendEmailResponse> {
    if (this.config.test_mode) {
      console.log('SendGrid Test Mode - Email would be sent:', {
        to: message.to,
        subject: message.subject,
      });
      
      return {
        success: true,
        message_id: `sg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      };
    }
    
    // In a real implementation, this would use @sendgrid/mail
    return {
      success: true,
      message_id: `sg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    };
  }
  
  async testConnection(): Promise<boolean> {
    return this.config.enabled && !!this.config.api_key;
  }
}

/**
 * Main Email Service
 */
export class EmailService {
  private provider: EmailProvider | null = null;
  private config: EmailServiceConfig | null = null;
  
  /**
   * Initialize email service
   */
  async initialize(): Promise<void> {
    this.config = await getEmailServiceConfig();
    this.provider = this.createProvider(this.config);
  }
  
  /**
   * Create email provider based on configuration
   */
  private createProvider(config: EmailServiceConfig): EmailProvider {
    switch (config.provider) {
      case 'smtp':
        return new SMTPProvider(config);
      case 'sendgrid':
        return new SendGridProvider(config);
      case 'ses':
      case 'mailgun':
      case 'postmark':
        // For now, fall back to SMTP for other providers
        return new SMTPProvider(config);
      default:
        throw new Error(`Unsupported email provider: ${config.provider}`);
    }
  }
  
  /**
   * Send email using template
   */
  async sendTemplateEmail(
    to: string,
    template: EmailTemplate,
    variables: EmailTemplateVariables,
    options: {
      priority?: EmailMessage['priority'];
      scheduledAt?: Date;
      replyTo?: string;
    } = {}
  ): Promise<SendEmailResponse> {
    if (!this.provider || !this.config) {
      throw new Error('Email service not initialized');
    }
    
    if (!this.config.enabled) {
      return {
        success: false,
        error: 'Email service is disabled',
      };
    }
    
    // Render template
    const subject = TemplateEngine.render(template.subject, variables);
    const htmlContent = TemplateEngine.render(template.html_content, variables);
    const textContent = TemplateEngine.render(template.text_content, variables);
    
    // Create email message
    const message: EmailMessage = {
      id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      to,
      from: this.config.from_email,
      subject,
      html_content: htmlContent,
      text_content: textContent,
      template_id: template.id,
      template_variables: variables,
      priority: options.priority || 'normal',
      status: 'queued',
      scheduled_at: options.scheduledAt,
      retry_count: 0,
      max_retries: 3,
      created_at: new Date(),
      updated_at: new Date(),
    };
    
    // Send email
    try {
      const result = await this.provider.send(message);
      
      // Update message status
      message.status = result.success ? 'sent' : 'failed';
      message.sent_at = result.success ? new Date() : undefined;
      message.failed_at = result.success ? undefined : new Date();
      message.error_message = result.error;
      message.updated_at = new Date();
      
      // In a real implementation, save message to database here
      
      return result;
    } catch (error) {
      message.status = 'failed';
      message.failed_at = new Date();
      message.error_message = error instanceof Error ? error.message : 'Unknown error';
      message.updated_at = new Date();
      
      return {
        success: false,
        error: message.error_message,
      };
    }
  }
  
  /**
   * Send simple email without template
   */
  async sendEmail(
    to: string,
    subject: string,
    htmlContent: string,
    textContent?: string,
    options: {
      priority?: EmailMessage['priority'];
      scheduledAt?: Date;
      replyTo?: string;
    } = {}
  ): Promise<SendEmailResponse> {
    if (!this.provider || !this.config) {
      throw new Error('Email service not initialized');
    }
    
    if (!this.config.enabled) {
      return {
        success: false,
        error: 'Email service is disabled',
      };
    }
    
    const message: EmailMessage = {
      id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      to,
      from: this.config.from_email,
      subject,
      html_content: htmlContent,
      text_content: textContent || this.htmlToText(htmlContent),
      priority: options.priority || 'normal',
      status: 'queued',
      scheduled_at: options.scheduledAt,
      retry_count: 0,
      max_retries: 3,
      created_at: new Date(),
      updated_at: new Date(),
    };
    
    try {
      const result = await this.provider.send(message);
      
      message.status = result.success ? 'sent' : 'failed';
      message.sent_at = result.success ? new Date() : undefined;
      message.failed_at = result.success ? undefined : new Date();
      message.error_message = result.error;
      message.updated_at = new Date();
      
      return result;
    } catch (error) {
      message.status = 'failed';
      message.failed_at = new Date();
      message.error_message = error instanceof Error ? error.message : 'Unknown error';
      message.updated_at = new Date();
      
      return {
        success: false,
        error: message.error_message,
      };
    }
  }
  
  /**
   * Send admin invitation email
   */
  async sendAdminInvitation(
    email: string,
    fullName: string,
    invitedByName: string,
    invitationLink: string,
    expiryDate: Date
  ): Promise<SendEmailResponse> {
    // Get admin invitation template
    const templates = await EmailTemplateManager.createDefaultTemplates('system');
    const template = templates.find(t => t.template_type === 'admin_invitation');
    
    if (!template) {
      return {
        success: false,
        error: 'Admin invitation template not found',
      };
    }
    
    const variables = {
      full_name: fullName,
      system_name: 'AI Karen Admin System',
      invited_by_name: invitedByName,
      invitation_link: invitationLink,
      expiry_date: expiryDate.toLocaleDateString(),
    };
    
    return this.sendTemplateEmail(email, template, variables, { priority: 'high' });
  }
  
  /**
   * Send user welcome email
   */
  async sendUserWelcome(
    email: string,
    fullName: string,
    role: string,
    createdByName: string,
    setupLink: string
  ): Promise<SendEmailResponse> {
    const templates = await EmailTemplateManager.createDefaultTemplates('system');
    const template = templates.find(t => t.template_type === 'user_welcome');
    
    if (!template) {
      return {
        success: false,
        error: 'User welcome template not found',
      };
    }
    
    const variables = {
      full_name: fullName,
      system_name: 'AI Karen Admin System',
      email,
      role,
      created_by_name: createdByName,
      created_date: new Date().toLocaleDateString(),
      setup_link: setupLink,
    };
    
    return this.sendTemplateEmail(email, template, variables, { priority: 'normal' });
  }
  
  /**
   * Send security alert email
   */
  async sendSecurityAlert(
    email: string,
    alertType: string,
    alertDescription: string,
    ipAddress: string,
    actionRequired?: string
  ): Promise<SendEmailResponse> {
    const templates = await EmailTemplateManager.createDefaultTemplates('system');
    const template = templates.find(t => t.template_type === 'security_alert');
    
    if (!template) {
      return {
        success: false,
        error: 'Security alert template not found',
      };
    }
    
    const variables = {
      alert_type: alertType,
      alert_time: new Date().toLocaleString(),
      user_email: email,
      ip_address: ipAddress,
      alert_description: alertDescription,
      action_required: actionRequired || '',
      system_name: 'AI Karen Admin System',
    };
    
    return this.sendTemplateEmail(email, template, variables, { priority: 'urgent' });
  }
  
  /**
   * Test email service connection
   */
  async testConnection(): Promise<EmailServiceHealth> {
    if (!this.config) {
      await this.initialize();
    }
    
    return testEmailService(this.config!);
  }
  
  /**
   * Convert HTML to plain text (basic implementation)
   */
  private htmlToText(html: string): string {
    return html
      .replace(/<[^>]*>/g, '') // Remove HTML tags
      .replace(/&nbsp;/g, ' ') // Replace non-breaking spaces
      .replace(/&amp;/g, '&') // Replace HTML entities
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'")
      .replace(/\s+/g, ' ') // Normalize whitespace
      .trim();
  }
  
  /**
   * Get service configuration
   */
  getConfig(): EmailServiceConfig | null {
    return this.config;
  }
  
  /**
   * Update service configuration
   */
  async updateConfig(newConfig: Partial<EmailServiceConfig>): Promise<void> {
    if (this.config) {
      this.config = { ...this.config, ...newConfig };
      this.provider = this.createProvider(this.config);
    }
  }
}

/**
 * Notification Service for admin actions
 */
export class NotificationService {
  constructor(private emailService: EmailService) {}
  
  /**
   * Send notification for admin action
   */
  async sendAdminActionNotification(
    type: EmailNotificationType,
    recipientEmail: string,
    data: Record<string, any>
  ): Promise<SendEmailResponse> {
    switch (type) {
      case 'admin_invitation':
        return this.emailService.sendAdminInvitation(
          recipientEmail,
          data.fullName,
          data.invitedByName,
          data.invitationLink,
          data.expiryDate
        );
        
      case 'user_welcome':
        return this.emailService.sendUserWelcome(
          recipientEmail,
          data.fullName,
          data.role,
          data.createdByName,
          data.setupLink
        );
        
      case 'security_alert':
        return this.emailService.sendSecurityAlert(
          recipientEmail,
          data.alertType,
          data.alertDescription,
          data.ipAddress,
          data.actionRequired
        );
        
      default:
        return {
          success: false,
          error: `Unsupported notification type: ${type}`,
        };
    }
  }
  
  /**
   * Send bulk notifications
   */
  async sendBulkNotifications(
    type: EmailNotificationType,
    recipients: Array<{ email: string; data: Record<string, any> }>
  ): Promise<{ success: number; failed: number; errors: string[] }> {
    const results = {
      success: 0,
      failed: 0,
      errors: [] as string[],
    };
    
    for (const recipient of recipients) {
      try {
        const result = await this.sendAdminActionNotification(type, recipient.email, recipient.data);
        
        if (result.success) {
          results.success++;
        } else {
          results.failed++;
          results.errors.push(`${recipient.email}: ${result.error}`);
        }
      } catch (error) {
        results.failed++;
        results.errors.push(`${recipient.email}: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    }
    
    return results;
  }
}

// Singleton instances
export const emailService = new EmailService();
export const notificationService = new NotificationService(emailService);