/**
 * Email Service Tests
 *
 * Tests for email service functionality including sending emails,
 * template processing, and provider integration.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { EmailService, NotificationService } from '../email-service';
import { EmailTemplate, EmailServiceConfig } from '../types';
import nodemailerStub from 'nodemailer';

const { mockTransportState } = nodemailerStub as unknown as {
  mockTransportState: {
    createCalls: number;
    sendCalls: Record<string, any>[];
    verifyCalls: number;
  };
};

vi.mock('../config', () => ({
  getEmailServiceConfig: vi.fn(),
  testEmailService: vi.fn(),
  getSystemName: vi.fn(() => 'AI Karen Admin System'),
  DEFAULT_EMAIL_CONFIG: {
    provider: 'smtp',
    smtp_host: 'localhost',
    smtp_port: 587,
    smtp_secure: false,
    smtp_user: 'test@example.com',
    smtp_password: 'password',
    from_email: 'noreply@test.com',
    from_name: 'Test System',
    reply_to_email: 'reply@test.com',
    enabled: true,
    test_mode: true,
  },
}));

vi.mock('../template-engine', () => ({
  EmailTemplateManager: {
    createDefaultTemplates: vi.fn(),
  },
  TemplateEngine: {
    render: vi.fn(),
  },
}));

describe('EmailService', () => {
  let emailService: EmailService;
  let mockConfig: EmailServiceConfig;

  beforeEach(async () => {
    emailService = new EmailService();
    mockConfig = {
      provider: 'smtp',
      smtp_host: 'localhost',
      smtp_port: 587,
      smtp_secure: false,
      smtp_user: 'test@example.com',
      smtp_password: 'password',
      from_email: 'noreply@test.com',
      from_name: 'Test System',
      reply_to_email: 'reply@test.com',
      enabled: true,
      test_mode: true,
    };
    mockTransportState.createCalls = 0;
    mockTransportState.sendCalls = [];
    mockTransportState.verifyCalls = 0;

    const configModule = await import('../config');
    vi.mocked(configModule.getEmailServiceConfig).mockResolvedValue(mockConfig);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('initialize', () => {
    it('loads configuration and prepares provider', async () => {
      await emailService.initialize();

      expect(emailService.getConfig()).toEqual(mockConfig);
      expect(mockTransportState.createCalls).toBeGreaterThan(0);
    });
  });

  describe('sendEmail', () => {
    beforeEach(async () => {
      await emailService.initialize();
    });

    it('sends email successfully in test mode', async () => {
      const result = await emailService.sendEmail(
        'recipient@example.com',
        'Subject',
        '<p>Hello World</p>',
        'Hello World'
      );

      expect(result.success).toBe(true);
      expect(result.message_id).toBeDefined();
      expect(mockTransportState.sendCalls).toHaveLength(0);
    });

    it('invokes SMTP provider when not in test mode', async () => {
      mockConfig.test_mode = false;
      await emailService.updateConfig({ test_mode: false });

      const result = await emailService.sendEmail(
        'recipient@example.com',
        'Subject',
        '<p>Live message</p>',
        'Live message'
      );

      expect(mockTransportState.sendCalls).toHaveLength(1);
      expect(result.success).toBe(true);
      expect(result.message_id).toBe('mock-transport-id');
    });

    it('respects disabled configuration', async () => {
      mockConfig.enabled = false;
      await emailService.updateConfig({ enabled: false });

      const result = await emailService.sendEmail(
        'recipient@example.com',
        'Subject',
        '<p>Body</p>'
      );

      expect(result.success).toBe(false);
      expect(result.error).toBe('Email service is disabled');
    });
  });

  describe('sendTemplateEmail', () => {
    let template: EmailTemplate;

    beforeEach(async () => {
      await emailService.initialize();
      template = {
        id: 'tmpl',
        name: 'Template',
        subject: 'Hello {{name}}',
        html_content: '<p>Hello {{name}}</p>',
        text_content: 'Hello {{name}}',
        template_type: 'user_welcome',
        variables: ['name'],
        is_active: true,
        created_at: new Date(),
        updated_at: new Date(),
        created_by: 'system',
      };

      const templateModule = await import('../template-engine');
      vi.mocked(templateModule.TemplateEngine.render)
        .mockReturnValueOnce('Hello John')
        .mockReturnValueOnce('<p>Hello John</p>')
        .mockReturnValueOnce('Hello John');
    });

    it('renders template and returns success', async () => {
      const result = await emailService.sendTemplateEmail(
        'recipient@example.com',
        template,
        { name: 'John' }
      );

      expect(result.success).toBe(true);
    });
  });

  describe('sendAdminInvitation', () => {
    beforeEach(async () => {
      await emailService.initialize();
      const templateModule = await import('../template-engine');
      vi.mocked(templateModule.EmailTemplateManager.createDefaultTemplates).mockResolvedValue([
        {
          id: 'default_admin_invitation',
          template_type: 'admin_invitation',
          subject: 'Invite',
          html_content: '<p>Invite</p>',
          text_content: 'Invite',
          variables: ['full_name'],
          name: 'Admin Invite',
          is_active: true,
          created_at: new Date(),
          updated_at: new Date(),
          created_by: 'system',
        } as EmailTemplate,
      ]);

      const templateEngine = await import('../template-engine');
      vi.mocked(templateEngine.TemplateEngine.render).mockReturnValue('Rendered');
    });

    it('sends invitation and supports custom message', async () => {
      const result = await emailService.sendAdminInvitation(
        'admin@example.com',
        'Admin User',
        'Super Admin',
        'https://example.com/invite',
        new Date(),
        'Welcome aboard!'
      );

      expect(result.success).toBe(true);
    });
  });

  describe('testConnection', () => {
    it('delegates to configuration health check', async () => {
      await emailService.initialize();
      const configModule = await import('../config');
      const health = {
        provider: 'smtp',
        is_connected: true,
        last_test_at: new Date(),
        test_result: 'success' as const,
        queue_size: 0,
        processing_rate: 0,
        failure_rate: 0,
      };

      vi.mocked(configModule.testEmailService).mockResolvedValue(health);
      const result = await emailService.testConnection();

      expect(result).toEqual(health);
      expect(configModule.testEmailService).toHaveBeenCalledWith(mockConfig);
    });
  });
});

describe('NotificationService', () => {
  let notificationService: NotificationService;
  let mockEmailService: EmailService;

  beforeEach(() => {
    mockEmailService = new EmailService();
    notificationService = new NotificationService(mockEmailService);

    vi.spyOn(mockEmailService, 'sendAdminInvitation').mockResolvedValue({
      success: true,
      message_id: 'test-message-id',
    });
    vi.spyOn(mockEmailService, 'sendUserWelcome').mockResolvedValue({
      success: true,
      message_id: 'test-message-id',
    });
    vi.spyOn(mockEmailService, 'sendSecurityAlert').mockResolvedValue({
      success: true,
      message_id: 'test-message-id',
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('routes admin invitation notifications', async () => {
    const data = {
      fullName: 'Admin User',
      invitedByName: 'Super Admin',
      invitationLink: 'https://example.com/invite',
      expiryDate: new Date(),
      customMessage: 'Please join us!'
    };

    await notificationService.sendAdminActionNotification('admin_invitation', 'admin@example.com', data);

    expect(mockEmailService.sendAdminInvitation).toHaveBeenCalledWith(
      'admin@example.com',
      data.fullName,
      data.invitedByName,
      data.invitationLink,
      data.expiryDate,
      data.customMessage
    );
  });

  it('routes bulk notifications and aggregates results', async () => {
    const recipients = [
      { email: 'user1@example.com', data: { fullName: 'User 1', role: 'User', createdByName: 'Admin', setupLink: 'link1' } },
      { email: 'user2@example.com', data: { fullName: 'User 2', role: 'User', createdByName: 'Admin', setupLink: 'link2' } },
    ];

    const result = await notificationService.sendBulkNotifications('user_welcome', recipients);

    expect(result.success).toBe(2);
    expect(result.failed).toBe(0);
    expect(mockEmailService.sendUserWelcome).toHaveBeenCalledTimes(2);
  });
});
