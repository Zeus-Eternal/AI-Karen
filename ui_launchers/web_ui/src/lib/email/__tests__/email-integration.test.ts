/**
 * Email Integration Tests
 * 
 * Integration tests for the complete email system including templates,
 * queue management, delivery tracking, and API endpoints.
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { EmailIntegration } from '../index';

// Mock all the dependencies
vi.mock('../email-service', () => ({
  emailService: {
    initialize: vi.fn().mockResolvedValue(undefined),
    sendAdminInvitation: vi.fn().mockResolvedValue({ success: true, message_id: 'msg-1' }),
    sendUserWelcome: vi.fn().mockResolvedValue({ success: true, message_id: 'msg-2' }),
    sendSecurityAlert: vi.fn().mockResolvedValue({ success: true, message_id: 'msg-3' }),
    testConnection: vi.fn().mockResolvedValue({
      provider: 'smtp',
      is_connected: true,
      last_test_at: new Date(),
      test_result: 'success',
      queue_size: 0,
      processing_rate: 0,
      failure_rate: 0,
    }),
  },
}));

vi.mock('../email-queue', () => ({
  emailQueueManager: {
    getQueueStats: vi.fn().mockReturnValue({
      total: 5,
      byPriority: { high: 2, normal: 2, low: 1 },
      byStatus: { queued: 3, sending: 1, sent: 1 },
      rateLimitRemaining: 55,
    }),
  },
}));

vi.mock('../delivery-tracker', () => ({
  deliveryStatusManager: {
    getDeliveryStatistics: vi.fn().mockResolvedValue({
      total_sent: 100,
      total_delivered: 95,
      total_failed: 3,
      total_bounced: 2,
      delivery_rate: 95,
      bounce_rate: 2,
      open_rate: 45,
      click_rate: 12,
      by_template: [],
      by_day: [],
    }),
  },
}));

describe('EmailIntegration', () => {
  let emailIntegration: EmailIntegration;

  beforeEach(() => {
    emailIntegration = EmailIntegration.getInstance();
    vi.clearAllMocks();

  afterEach(() => {
    vi.clearAllMocks();

  describe('singleton pattern', () => {
    it('should return same instance', () => {
      const instance1 = EmailIntegration.getInstance();
      const instance2 = EmailIntegration.getInstance();
      
      expect(instance1).toBe(instance2);


  describe('initialize', () => {
    it('should initialize email service', async () => {
      await emailIntegration.initialize();
      
      const { emailService } = await import('../email-service');
      expect(emailService.initialize).toHaveBeenCalledTimes(1);


  describe('sendAdminInvitation', () => {
    it('should send admin invitation email', async () => {
      const result = await emailIntegration.sendAdminInvitation(
        'admin@example.com',
        'John Admin',
        'Super Admin',
        'https://example.com/invite/123',
        new Date()
      );

      expect(result.success).toBe(true);
      expect(result.message_id).toBe('msg-1');

      const { emailService } = await import('../email-service');
      expect(emailService.sendAdminInvitation).toHaveBeenCalledWith(
        'admin@example.com',
        'John Admin',
        'Super Admin',
        'https://example.com/invite/123',
        expect.any(Date)
      );


  describe('sendUserWelcome', () => {
    it('should send user welcome email', async () => {
      const result = await emailIntegration.sendUserWelcome(
        'user@example.com',
        'John User',
        'User',
        'Admin User',
        'https://example.com/setup/123'
      );

      expect(result.success).toBe(true);
      expect(result.message_id).toBe('msg-2');

      const { emailService } = await import('../email-service');
      expect(emailService.sendUserWelcome).toHaveBeenCalledWith(
        'user@example.com',
        'John User',
        'User',
        'Admin User',
        'https://example.com/setup/123'
      );


  describe('sendSecurityAlert', () => {
    it('should send security alert email', async () => {
      const result = await emailIntegration.sendSecurityAlert(
        'user@example.com',
        'Failed Login',
        'Multiple failed login attempts detected',
        '192.168.1.100',
        'Change your password'
      );

      expect(result.success).toBe(true);
      expect(result.message_id).toBe('msg-3');

      const { emailService } = await import('../email-service');
      expect(emailService.sendSecurityAlert).toHaveBeenCalledWith(
        'user@example.com',
        'Failed Login',
        'Multiple failed login attempts detected',
        '192.168.1.100',
        'Change your password'
      );

    it('should send security alert without action required', async () => {
      const result = await emailIntegration.sendSecurityAlert(
        'user@example.com',
        'Account Locked',
        'Account has been locked due to suspicious activity',
        '192.168.1.100'
      );

      expect(result.success).toBe(true);

      const { emailService } = await import('../email-service');
      expect(emailService.sendSecurityAlert).toHaveBeenCalledWith(
        'user@example.com',
        'Account Locked',
        'Account has been locked due to suspicious activity',
        '192.168.1.100',
        undefined
      );


  describe('getServiceHealth', () => {
    it('should return email service health', async () => {
      const health = await emailIntegration.getServiceHealth();

      expect(health).toEqual({
        provider: 'smtp',
        is_connected: true,
        last_test_at: expect.any(Date),
        test_result: 'success',
        queue_size: 0,
        processing_rate: 0,
        failure_rate: 0,

      const { emailService } = await import('../email-service');
      expect(emailService.testConnection).toHaveBeenCalledTimes(1);


  describe('getQueueStats', () => {
    it('should return queue statistics', async () => {
      const stats = await emailIntegration.getQueueStats();

      expect(stats).toEqual({
        total: 5,
        byPriority: { high: 2, normal: 2, low: 1 },
        byStatus: { queued: 3, sending: 1, sent: 1 },
        rateLimitRemaining: 55,



  describe('getDeliveryStats', () => {
    it('should return delivery statistics', async () => {
      const stats = await emailIntegration.getDeliveryStats();

      expect(stats).toEqual({
        total_sent: 100,
        total_delivered: 95,
        total_failed: 3,
        total_bounced: 2,
        delivery_rate: 95,
        bounce_rate: 2,
        open_rate: 45,
        click_rate: 12,
        by_template: [],
        by_day: [],

      const { deliveryStatusManager } = await import('../delivery-tracker');
      expect(deliveryStatusManager.getDeliveryStatistics).toHaveBeenCalledWith(
        undefined,
        undefined,
        undefined
      );

    it('should return delivery statistics with filters', async () => {
      const startDate = new Date('2023-01-01');
      const endDate = new Date('2023-01-31');
      const templateId = 'template-1';

      await emailIntegration.getDeliveryStats(startDate, endDate, templateId);

      const { deliveryStatusManager } = await import('../delivery-tracker');
      expect(deliveryStatusManager.getDeliveryStatistics).toHaveBeenCalledWith(
        startDate,
        endDate,
        templateId
      );



describe('Email Integration Workflow', () => {
  let emailIntegration: EmailIntegration;

  beforeEach(async () => {
    emailIntegration = EmailIntegration.getInstance();
    await emailIntegration.initialize();

  afterEach(() => {
    vi.clearAllMocks();

  describe('admin invitation workflow', () => {
    it('should complete full admin invitation workflow', async () => {
      // 1. Send admin invitation
      const invitationResult = await emailIntegration.sendAdminInvitation(
        'newadmin@example.com',
        'New Admin',
        'Super Admin',
        'https://example.com/invite/abc123',
        new Date(Date.now() + 7 * 24 * 60 * 60 * 1000) // 7 days from now
      );

      expect(invitationResult.success).toBe(true);

      // 2. Check queue stats
      const queueStats = await emailIntegration.getQueueStats();
      expect(queueStats.total).toBeGreaterThan(0);

      // 3. Check service health
      const health = await emailIntegration.getServiceHealth();
      expect(health.is_connected).toBe(true);

      // 4. Check delivery stats
      const deliveryStats = await emailIntegration.getDeliveryStats();
      expect(deliveryStats.total_sent).toBeGreaterThan(0);


  describe('user welcome workflow', () => {
    it('should complete full user welcome workflow', async () => {
      // 1. Send user welcome email
      const welcomeResult = await emailIntegration.sendUserWelcome(
        'newuser@example.com',
        'New User',
        'User',
        'Admin User',
        'https://example.com/setup/xyz789'
      );

      expect(welcomeResult.success).toBe(true);

      // 2. Verify email was queued
      const queueStats = await emailIntegration.getQueueStats();
      expect(queueStats).toBeDefined();

      // 3. Check delivery tracking
      const deliveryStats = await emailIntegration.getDeliveryStats();
      expect(deliveryStats).toBeDefined();


  describe('security alert workflow', () => {
    it('should complete full security alert workflow', async () => {
      // 1. Send security alert
      const alertResult = await emailIntegration.sendSecurityAlert(
        'user@example.com',
        'Suspicious Login',
        'Login attempt from unusual location detected',
        '203.0.113.1',
        'Please verify this was you and consider enabling 2FA'
      );

      expect(alertResult.success).toBe(true);

      // 2. Verify high priority processing
      const queueStats = await emailIntegration.getQueueStats();
      expect(queueStats.byPriority.high).toBeGreaterThan(0);

      // 3. Check service health for urgent processing
      const health = await emailIntegration.getServiceHealth();
      expect(health.is_connected).toBe(true);


  describe('bulk operations workflow', () => {
    it('should handle multiple email types in sequence', async () => {
      // Send multiple different types of emails
      const results = await Promise.all([
        emailIntegration.sendAdminInvitation(
          'admin1@example.com',
          'Admin 1',
          'Super Admin',
          'https://example.com/invite/1',
          new Date()
        ),
        emailIntegration.sendUserWelcome(
          'user1@example.com',
          'User 1',
          'User',
          'Admin',
          'https://example.com/setup/1'
        ),
        emailIntegration.sendSecurityAlert(
          'user2@example.com',
          'Account Locked',
          'Account locked due to failed attempts',
          '192.168.1.1'
        ),
      ]);

      // All should succeed
      results.forEach(result => {
        expect(result.success).toBe(true);

      // Check final stats
      const queueStats = await emailIntegration.getQueueStats();
      const deliveryStats = await emailIntegration.getDeliveryStats();
      const health = await emailIntegration.getServiceHealth();

      expect(queueStats).toBeDefined();
      expect(deliveryStats).toBeDefined();
      expect(health.is_connected).toBe(true);


  describe('error handling workflow', () => {
    it('should handle service failures gracefully', async () => {
      // Mock service failure
      const { emailService } = await import('../email-service');
      vi.mocked(emailService.sendAdminInvitation).mockResolvedValueOnce({
        success: false,
        error: 'Service temporarily unavailable',

      const result = await emailIntegration.sendAdminInvitation(
        'admin@example.com',
        'Admin',
        'Super Admin',
        'https://example.com/invite/123',
        new Date()
      );

      expect(result.success).toBe(false);
      expect(result.error).toBe('Service temporarily unavailable');

      // Service health should still be checkable
      const health = await emailIntegration.getServiceHealth();
      expect(health).toBeDefined();


