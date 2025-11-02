/**
 * Email Service Tests
 * 
 * Tests for email service functionality including sending emails,
 * template processing, and provider integration.
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { EmailService, NotificationService } from '../email-service';
import { EmailTemplate, EmailServiceConfig } from '../types';

// Mock the config module
vi.mock('../config', () => ({
  getEmailServiceConfig: vi.fn(),
  testEmailService: vi.fn(),
  DEFAULT_EMAIL_CONFIG: {
    provider: 'smtp',
    smtp_host: 'localhost',
    smtp_port: 587,
    smtp_secure: false,
    smtp_user: 'test@example.com',
    smtp_password: 'password',
    from_email: 'noreply@test.com',
    from_name: 'Test System',
    enabled: true,
    test_mode: true,
  },
}));

// Mock the template engine
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
      enabled: true,
      test_mode: true,
    };

    // Mock the config getter
    const configModule = await import('../config');
    vi.mocked(configModule.getEmailServiceConfig).mockResolvedValue(mockConfig);

  afterEach(() => {
    vi.clearAllMocks();

  describe('initialize', () => {
    it('should initialize email service with configuration', async () => {
      await emailService.initialize();
      
      expect(emailService.getConfig()).toEqual(mockConfig);

    it('should handle initialization errors', async () => {
      const configModule = await import('../config');
      vi.mocked(configModule.getEmailServiceConfig).mockRejectedValue(new Error('Config error'));

      await expect(emailService.initialize()).rejects.toThrow('Config error');


  describe('sendEmail', () => {
    beforeEach(async () => {
      await emailService.initialize();

    it('should send simple email successfully', async () => {
      const result = await emailService.sendEmail(
        'test@example.com',
        'Test Subject',
        '<p>Test HTML content</p>',
        'Test text content'
      );

      expect(result.success).toBe(true);
      expect(result.message_id).toBeDefined();
      expect(result.error).toBeUndefined();

    it('should generate text content from HTML if not provided', async () => {
      const result = await emailService.sendEmail(
        'test@example.com',
        'Test Subject',
        '<p>Test <strong>HTML</strong> content</p>'
      );

      expect(result.success).toBe(true);

    it('should handle disabled email service', async () => {
      mockConfig.enabled = false;
      await emailService.updateConfig(mockConfig);

      const result = await emailService.sendEmail(
        'test@example.com',
        'Test Subject',
        '<p>Test content</p>'
      );

      expect(result.success).toBe(false);
      expect(result.error).toBe('Email service is disabled');

    it('should handle uninitialized service', async () => {
      const uninitializedService = new EmailService();

      await expect(
        uninitializedService.sendEmail(
          'test@example.com',
          'Test Subject',
          '<p>Test content</p>'
        )
      ).rejects.toThrow('Email service not initialized');


  describe('sendTemplateEmail', () => {
    let mockTemplate: EmailTemplate;

    beforeEach(async () => {
      await emailService.initialize();
      
      mockTemplate = {
        id: 'test-template',
        name: 'Test Template',
        subject: 'Hello {{name}}',
        html_content: '<p>Hello {{name}}, welcome to {{system}}!</p>',
        text_content: 'Hello {{name}}, welcome to {{system}}!',
        template_type: 'user_welcome',
        variables: ['name', 'system'],
        is_active: true,
        created_at: new Date(),
        updated_at: new Date(),
        created_by: 'test-user',
      };

      // Mock template rendering
      const templateModule = await import('../template-engine');
      vi.mocked(templateModule.TemplateEngine.render)
        .mockReturnValueOnce('Hello John Doe') // subject
        .mockReturnValueOnce('<p>Hello John Doe, welcome to Test System!</p>') // html
        .mockReturnValueOnce('Hello John Doe, welcome to Test System!'); // text

    it('should send template email successfully', async () => {
      const variables = {
        name: 'John Doe',
        system: 'Test System',
      };

      const result = await emailService.sendTemplateEmail(
        'test@example.com',
        mockTemplate,
        variables
      );

      expect(result.success).toBe(true);
      expect(result.message_id).toBeDefined();

      // Verify template rendering was called
      const templateModule = await import('../template-engine');
      expect(templateModule.TemplateEngine.render).toHaveBeenCalledTimes(3);

    it('should handle template rendering with options', async () => {
      const variables = { name: 'John', system: 'Test' };
      const options = {
        priority: 'high' as const,
        scheduledAt: new Date(),
        replyTo: 'reply@test.com',
      };

      const result = await emailService.sendTemplateEmail(
        'test@example.com',
        mockTemplate,
        variables,
        options
      );

      expect(result.success).toBe(true);


  describe('sendAdminInvitation', () => {
    beforeEach(async () => {
      await emailService.initialize();

      // Mock default templates
      const templateModule = await import('../template-engine');
      const mockTemplates = [{
        id: 'default_admin_invitation',
        template_type: 'admin_invitation',
        subject: 'Admin Invitation',
        html_content: '<p>Invitation content</p>',
        text_content: 'Invitation content',
        variables: ['full_name', 'invited_by_name'],
        name: 'Admin Invitation',
        is_active: true,
        created_at: new Date(),
        updated_at: new Date(),
        created_by: 'system',
      }];
      vi.mocked(templateModule.EmailTemplateManager.createDefaultTemplates).mockResolvedValue(mockTemplates as any);

      // Mock template rendering
      vi.mocked(templateModule.TemplateEngine.render)
        .mockReturnValue('Rendered content');

    it('should send admin invitation email', async () => {
      const result = await emailService.sendAdminInvitation(
        'admin@example.com',
        'John Admin',
        'Super Admin',
        'https://example.com/invite/123',
        new Date()
      );

      expect(result.success).toBe(true);

    it('should handle missing admin invitation template', async () => {
      const templateModule = await import('../template-engine');
      vi.mocked(templateModule.EmailTemplateManager.createDefaultTemplates).mockResolvedValue([]);

      const result = await emailService.sendAdminInvitation(
        'admin@example.com',
        'John Admin',
        'Super Admin',
        'https://example.com/invite/123',
        new Date()
      );

      expect(result.success).toBe(false);
      expect(result.error).toBe('Admin invitation template not found');


  describe('sendUserWelcome', () => {
    beforeEach(async () => {
      await emailService.initialize();

      // Mock default templates
      const templateModule = await import('../template-engine');
      const mockTemplates = [{
        id: 'default_user_welcome',
        template_type: 'user_welcome',
        subject: 'Welcome',
        html_content: '<p>Welcome content</p>',
        text_content: 'Welcome content',
        variables: ['full_name', 'role'],
        name: 'User Welcome',
        is_active: true,
        created_at: new Date(),
        updated_at: new Date(),
        created_by: 'system',
      }];
      vi.mocked(templateModule.EmailTemplateManager.createDefaultTemplates).mockResolvedValue(mockTemplates as any);

      // Mock template rendering
      vi.mocked(templateModule.TemplateEngine.render).mockReturnValue('Rendered content');

    it('should send user welcome email', async () => {
      const result = await emailService.sendUserWelcome(
        'user@example.com',
        'John User',
        'User',
        'Admin User',
        'https://example.com/setup/123'
      );

      expect(result.success).toBe(true);


  describe('sendSecurityAlert', () => {
    beforeEach(async () => {
      await emailService.initialize();

      // Mock default templates
      const templateModule = await import('../template-engine');
      const mockTemplates = [{
        id: 'default_security_alert',
        template_type: 'security_alert',
        subject: 'Security Alert',
        html_content: '<p>Alert content</p>',
        text_content: 'Alert content',
        variables: ['alert_type', 'alert_description'],
        name: 'Security Alert',
        is_active: true,
        created_at: new Date(),
        updated_at: new Date(),
        created_by: 'system',
      }];
      vi.mocked(templateModule.EmailTemplateManager.createDefaultTemplates).mockResolvedValue(mockTemplates as any);

      // Mock template rendering
      vi.mocked(templateModule.TemplateEngine.render).mockReturnValue('Rendered content');

    it('should send security alert email', async () => {
      const result = await emailService.sendSecurityAlert(
        'user@example.com',
        'Failed Login',
        'Multiple failed login attempts detected',
        '192.168.1.100',
        'Change your password'
      );

      expect(result.success).toBe(true);


  describe('testConnection', () => {
    beforeEach(async () => {
      await emailService.initialize();

    it('should test email service connection', async () => {
      const configModule = await import('../config');
      const mockHealthResult = {
        provider: 'smtp',
        is_connected: true,
        last_test_at: new Date(),
        test_result: 'success' as const,
        queue_size: 0,
        processing_rate: 0,
        failure_rate: 0,
      };
      vi.mocked(configModule.testEmailService).mockResolvedValue(mockHealthResult);

      const result = await emailService.testConnection();

      expect(result).toEqual(mockHealthResult);
      expect(configModule.testEmailService).toHaveBeenCalledWith(mockConfig);


  describe('updateConfig', () => {
    beforeEach(async () => {
      await emailService.initialize();

    it('should update email service configuration', async () => {
      const newConfig = {
        enabled: false,
        test_mode: false,
      };

      await emailService.updateConfig(newConfig);

      const updatedConfig = emailService.getConfig();
      expect(updatedConfig?.enabled).toBe(false);
      expect(updatedConfig?.test_mode).toBe(false);



describe('NotificationService', () => {
  let notificationService: NotificationService;
  let mockEmailService: EmailService;

  beforeEach(() => {
    mockEmailService = new EmailService();
    notificationService = new NotificationService(mockEmailService);

    // Mock email service methods
    vi.spyOn(mockEmailService, 'sendAdminInvitation').mockResolvedValue({
      success: true,
      message_id: 'test-message-id',

    vi.spyOn(mockEmailService, 'sendUserWelcome').mockResolvedValue({
      success: true,
      message_id: 'test-message-id',

    vi.spyOn(mockEmailService, 'sendSecurityAlert').mockResolvedValue({
      success: true,
      message_id: 'test-message-id',


  afterEach(() => {
    vi.clearAllMocks();

  describe('sendAdminActionNotification', () => {
    it('should send admin invitation notification', async () => {
      const data = {
        fullName: 'John Admin',
        invitedByName: 'Super Admin',
        invitationLink: 'https://example.com/invite/123',
        expiryDate: new Date(),
      };

      const result = await notificationService.sendAdminActionNotification(
        'admin_invitation',
        'admin@example.com',
        data
      );

      expect(result.success).toBe(true);
      expect(mockEmailService.sendAdminInvitation).toHaveBeenCalledWith(
        'admin@example.com',
        data.fullName,
        data.invitedByName,
        data.invitationLink,
        data.expiryDate
      );

    it('should send user welcome notification', async () => {
      const data = {
        fullName: 'John User',
        role: 'User',
        createdByName: 'Admin',
        setupLink: 'https://example.com/setup/123',
      };

      const result = await notificationService.sendAdminActionNotification(
        'user_welcome',
        'user@example.com',
        data
      );

      expect(result.success).toBe(true);
      expect(mockEmailService.sendUserWelcome).toHaveBeenCalledWith(
        'user@example.com',
        data.fullName,
        data.role,
        data.createdByName,
        data.setupLink
      );

    it('should send security alert notification', async () => {
      const data = {
        alertType: 'Failed Login',
        alertDescription: 'Multiple failed attempts',
        ipAddress: '192.168.1.100',
        actionRequired: 'Change password',
      };

      const result = await notificationService.sendAdminActionNotification(
        'security_alert',
        'user@example.com',
        data
      );

      expect(result.success).toBe(true);
      expect(mockEmailService.sendSecurityAlert).toHaveBeenCalledWith(
        'user@example.com',
        data.alertType,
        data.alertDescription,
        data.ipAddress,
        data.actionRequired
      );

    it('should handle unsupported notification type', async () => {
      const result = await notificationService.sendAdminActionNotification(
        'unsupported_type' as any,
        'user@example.com',
        {}
      );

      expect(result.success).toBe(false);
      expect(result.error).toContain('Unsupported notification type');


  describe('sendBulkNotifications', () => {
    it('should send bulk notifications successfully', async () => {
      const recipients = [
        {
          email: 'user1@example.com',
          data: { fullName: 'User 1', role: 'User', createdByName: 'Admin', setupLink: 'link1' },
        },
        {
          email: 'user2@example.com',
          data: { fullName: 'User 2', role: 'User', createdByName: 'Admin', setupLink: 'link2' },
        },
      ];

      const result = await notificationService.sendBulkNotifications('user_welcome', recipients);

      expect(result.success).toBe(2);
      expect(result.failed).toBe(0);
      expect(result.errors).toHaveLength(0);
      expect(mockEmailService.sendUserWelcome).toHaveBeenCalledTimes(2);

    it('should handle partial failures in bulk notifications', async () => {
      // Mock one success and one failure
      vi.mocked(mockEmailService.sendUserWelcome)
        .mockResolvedValueOnce({ success: true, message_id: 'msg1' })
        .mockResolvedValueOnce({ success: false, error: 'Send failed' });

      const recipients = [
        {
          email: 'user1@example.com',
          data: { fullName: 'User 1', role: 'User', createdByName: 'Admin', setupLink: 'link1' },
        },
        {
          email: 'user2@example.com',
          data: { fullName: 'User 2', role: 'User', createdByName: 'Admin', setupLink: 'link2' },
        },
      ];

      const result = await notificationService.sendBulkNotifications('user_welcome', recipients);

      expect(result.success).toBe(1);
      expect(result.failed).toBe(1);
      expect(result.errors).toHaveLength(1);
      expect(result.errors[0]).toContain('user2@example.com: Send failed');

    it('should handle exceptions in bulk notifications', async () => {
      vi.mocked(mockEmailService.sendUserWelcome)
        .mockRejectedValue(new Error('Network error'));

      const recipients = [
        {
          email: 'user1@example.com',
          data: { fullName: 'User 1', role: 'User', createdByName: 'Admin', setupLink: 'link1' },
        },
      ];

      const result = await notificationService.sendBulkNotifications('user_welcome', recipients);

      expect(result.success).toBe(0);
      expect(result.failed).toBe(1);
      expect(result.errors).toHaveLength(1);
      expect(result.errors[0]).toContain('Network error');


