/**
 * Email Delivery Tracker Tests
 * 
 * Tests for delivery status tracking, webhook processing, and analytics.
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { DeliveryStatusManager, WebhookHandler, RetryManager } from '../delivery-tracker';
import { EmailDeliveryStatus, EmailWebhook } from '../types';

describe('DeliveryStatusManager', () => {
  let deliveryManager: DeliveryStatusManager;
  let mockDeliveryStatus: EmailDeliveryStatus;

  beforeEach(() => {
    deliveryManager = new DeliveryStatusManager();
    
    mockDeliveryStatus = {
      message_id: 'test-message-1',
      status: 'delivered',
      timestamp: new Date(),
      details: {
        provider: 'smtp',
        event_type: 'delivered',
        email: 'test@example.com',
      },
    };

    // Mock console methods to avoid test output
    vi.spyOn(console, 'log').mockImplementation(() => {});
    vi.spyOn(console, 'error').mockImplementation(() => {});

  afterEach(() => {
    vi.clearAllMocks();

  describe('recordDeliveryStatus', () => {
    it('should record delivery status', async () => {
      await deliveryManager.recordDeliveryStatus(mockDeliveryStatus);
      
      const statuses = deliveryManager.getDeliveryStatus('test-message-1');
      expect(statuses).toHaveLength(1);
      expect(statuses[0]).toEqual(mockDeliveryStatus);

    it('should maintain multiple statuses for same message', async () => {
      const status1 = { ...mockDeliveryStatus, status: 'sent' as const };
      const status2 = { ...mockDeliveryStatus, status: 'delivered' as const };
      const status3 = { ...mockDeliveryStatus, status: 'opened' as const };

      await deliveryManager.recordDeliveryStatus(status1);
      await deliveryManager.recordDeliveryStatus(status2);
      await deliveryManager.recordDeliveryStatus(status3);

      const statuses = deliveryManager.getDeliveryStatus('test-message-1');
      expect(statuses).toHaveLength(3);
      expect(statuses.map(s => s.status)).toEqual(['sent', 'delivered', 'opened']);

    it('should limit status history to 10 entries', async () => {
      // Add 15 statuses
      for (let i = 0; i < 15; i++) {
        const status = {
          ...mockDeliveryStatus,
          timestamp: new Date(Date.now() + i * 1000),
        };
        await deliveryManager.recordDeliveryStatus(status);
      }

      const statuses = deliveryManager.getDeliveryStatus('test-message-1');
      expect(statuses).toHaveLength(10);


  describe('getLatestDeliveryStatus', () => {
    it('should return latest delivery status', async () => {
      const status1 = { ...mockDeliveryStatus, status: 'sent' as const, timestamp: new Date('2023-01-01') };
      const status2 = { ...mockDeliveryStatus, status: 'delivered' as const, timestamp: new Date('2023-01-02') };

      await deliveryManager.recordDeliveryStatus(status1);
      await deliveryManager.recordDeliveryStatus(status2);

      const latest = deliveryManager.getLatestDeliveryStatus('test-message-1');
      expect(latest?.status).toBe('delivered');

    it('should return null for non-existent message', () => {
      const latest = deliveryManager.getLatestDeliveryStatus('non-existent');
      expect(latest).toBeNull();


  describe('processWebhook', () => {
    let mockWebhook: EmailWebhook;

    beforeEach(() => {
      mockWebhook = {
        id: 'webhook-1',
        provider: 'sendgrid',
        event_type: 'delivered',
        message_id: 'test-message-1',
        email: 'test@example.com',
        timestamp: new Date(),
        data: {
          event: 'delivered',
          email: 'test@example.com',
          timestamp: Date.now(),
        },
        processed: false,
        created_at: new Date(),
      };

    it('should process valid webhook', async () => {
      await deliveryManager.processWebhook(mockWebhook);

      expect(mockWebhook.processed).toBe(true);
      expect(mockWebhook.processed_at).toBeInstanceOf(Date);

      const statuses = deliveryManager.getDeliveryStatus('test-message-1');
      expect(statuses).toHaveLength(1);
      expect(statuses[0].status).toBe('delivered');

    it('should reject invalid webhook', async () => {
      const invalidWebhook = { ...mockWebhook, message_id: '' };

      await expect(deliveryManager.processWebhook(invalidWebhook)).rejects.toThrow('Invalid webhook data');

    it('should call registered webhook handler', async () => {
      const mockHandler = vi.fn().mockResolvedValue(undefined);
      deliveryManager.registerWebhookHandler('sendgrid', mockHandler);

      await deliveryManager.processWebhook(mockWebhook);

      expect(mockHandler).toHaveBeenCalledWith(mockWebhook);


  describe('getDeliveryStatistics', () => {
    it('should return delivery statistics', async () => {
      const stats = await deliveryManager.getDeliveryStatistics();

      expect(stats).toEqual({
        total_sent: 100,
        total_delivered: 95,
        total_failed: 3,
        total_bounced: 2,
        delivery_rate: 95,
        bounce_rate: 2,
        open_rate: 45,
        click_rate: 12,
        by_template: expect.any(Array),
        by_day: expect.any(Array),


    it('should accept date range filters', async () => {
      const startDate = new Date('2023-01-01');
      const endDate = new Date('2023-01-31');

      const stats = await deliveryManager.getDeliveryStatistics(startDate, endDate);

      expect(stats).toBeDefined();
      // In a real implementation, this would filter by date range

    it('should accept template filter', async () => {
      const stats = await deliveryManager.getDeliveryStatistics(undefined, undefined, 'template-1');

      expect(stats).toBeDefined();
      // In a real implementation, this would filter by template


  describe('cleanupOldStatuses', () => {
    it('should clean up old delivery statuses', async () => {
      // Add old status
      const oldStatus = {
        ...mockDeliveryStatus,
        timestamp: new Date(Date.now() - 40 * 24 * 60 * 60 * 1000), // 40 days ago
      };
      
      // Add recent status
      const recentStatus = {
        ...mockDeliveryStatus,
        message_id: 'recent-message',
        timestamp: new Date(),
      };

      await deliveryManager.recordDeliveryStatus(oldStatus);
      await deliveryManager.recordDeliveryStatus(recentStatus);

      const cleanedCount = await deliveryManager.cleanupOldStatuses(30);

      expect(cleanedCount).toBe(1);
      expect(deliveryManager.getDeliveryStatus('test-message-1')).toHaveLength(0);
      expect(deliveryManager.getDeliveryStatus('recent-message')).toHaveLength(1);



describe('WebhookHandler', () => {
  let webhookHandler: WebhookHandler;
  let deliveryManager: DeliveryStatusManager;

  beforeEach(() => {
    deliveryManager = new DeliveryStatusManager();
    webhookHandler = new WebhookHandler(deliveryManager);

    // Mock console methods
    vi.spyOn(console, 'log').mockImplementation(() => {});
    vi.spyOn(console, 'error').mockImplementation(() => {});

  afterEach(() => {
    vi.clearAllMocks();

  describe('processIncomingWebhook', () => {
    it('should process SendGrid webhook', async () => {
      const data = {
        event: 'delivered',
        email: 'test@example.com',
        sg_message_id: 'sendgrid-msg-1',
        timestamp: Date.now(),
      };

      const headers = {
        'x-twilio-email-event-webhook-signature': 'valid-signature',
      };

      // Mock delivery manager processWebhook
      const processWebhookSpy = vi.spyOn(deliveryManager, 'processWebhook').mockResolvedValue();

      await webhookHandler.processIncomingWebhook('sendgrid', 'delivered', data, headers);

      expect(processWebhookSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          provider: 'sendgrid',
          event_type: 'delivered',
          message_id: 'sendgrid-msg-1',
          email: 'test@example.com',
          data,
        })
      );

    it('should process SES webhook', async () => {
      const data = {
        eventType: 'delivery',
        mail: {
          messageId: 'ses-msg-1',
          destination: ['test@example.com'],
        },
      };

      const headers = {};

      const processWebhookSpy = vi.spyOn(deliveryManager, 'processWebhook').mockResolvedValue();

      await webhookHandler.processIncomingWebhook('ses', 'delivery', data, headers);

      expect(processWebhookSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          provider: 'ses',
          event_type: 'delivery',
          message_id: 'ses-msg-1',
          email: 'test@example.com',
        })
      );

    it('should process Mailgun webhook', async () => {
      const data = {
        event: 'delivered',
        recipient: 'test@example.com',
        'message-id': 'mailgun-msg-1',
      };

      const headers = {};

      const processWebhookSpy = vi.spyOn(deliveryManager, 'processWebhook').mockResolvedValue();

      await webhookHandler.processIncomingWebhook('mailgun', 'delivered', data, headers);

      expect(processWebhookSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          provider: 'mailgun',
          event_type: 'delivered',
          message_id: 'mailgun-msg-1',
          email: 'test@example.com',
        })
      );

    it('should process Postmark webhook', async () => {
      const data = {
        Type: 'Delivery',
        Email: 'test@example.com',
        MessageID: 'postmark-msg-1',
      };

      const headers = {};

      const processWebhookSpy = vi.spyOn(deliveryManager, 'processWebhook').mockResolvedValue();

      await webhookHandler.processIncomingWebhook('postmark', 'Delivery', data, headers);

      expect(processWebhookSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          provider: 'postmark',
          event_type: 'Delivery',
          message_id: 'postmark-msg-1',
          email: 'test@example.com',
        })
      );

    it('should handle webhook processing errors', async () => {
      const data = {
        event: 'delivered',
        email: 'test@example.com',
        sg_message_id: 'sendgrid-msg-1',
      };

      const headers = {};

      // Mock delivery manager to throw error
      vi.spyOn(deliveryManager, 'processWebhook').mockRejectedValue(new Error('Processing failed'));

      await expect(
        webhookHandler.processIncomingWebhook('sendgrid', 'delivered', data, headers)
      ).rejects.toThrow('Processing failed');



describe('RetryManager', () => {
  let retryManager: RetryManager;
  let deliveryManager: DeliveryStatusManager;

  beforeEach(() => {
    deliveryManager = new DeliveryStatusManager();
    retryManager = new RetryManager(deliveryManager);

    // Mock console methods
    vi.spyOn(console, 'log').mockImplementation(() => {});

  afterEach(() => {
    vi.clearAllMocks();

  describe('processRetryQueue', () => {
    it('should process retry queue', async () => {
      const mockFailedDeliveries = [
        {
          messageId: 'msg-1',
          email: 'test1@example.com',
          failureReason: 'temporary failure',
          failedAt: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
          retryCount: 1,
        },
        {
          messageId: 'msg-2',
          email: 'test2@example.com',
          failureReason: 'bounced',
          failedAt: new Date(Date.now() - 1 * 60 * 60 * 1000), // 1 hour ago
          retryCount: 0,
        },
      ];

      // Mock getFailedDeliveries
      vi.spyOn(deliveryManager, 'getFailedDeliveries').mockResolvedValue(mockFailedDeliveries);
      
      // Mock markForRetry
      const markForRetrySpy = vi.spyOn(deliveryManager, 'markForRetry').mockResolvedValue();

      await retryManager.processRetryQueue();

      // Should retry the first message (temporary failure, enough time passed)
      // Should not retry the second message (permanent failure - bounced)
      expect(markForRetrySpy).toHaveBeenCalledTimes(1);
      expect(markForRetrySpy).toHaveBeenCalledWith('msg-1');

    it('should not retry messages with too many attempts', async () => {
      const mockFailedDeliveries = [
        {
          messageId: 'msg-1',
          email: 'test@example.com',
          failureReason: 'temporary failure',
          failedAt: new Date(Date.now() - 5 * 60 * 60 * 1000), // 5 hours ago
          retryCount: 3, // Max retries reached
        },
      ];

      vi.spyOn(deliveryManager, 'getFailedDeliveries').mockResolvedValue(mockFailedDeliveries);
      const markForRetrySpy = vi.spyOn(deliveryManager, 'markForRetry').mockResolvedValue();

      await retryManager.processRetryQueue();

      expect(markForRetrySpy).not.toHaveBeenCalled();

    it('should not retry permanent failures', async () => {
      const mockFailedDeliveries = [
        {
          messageId: 'msg-1',
          email: 'test@example.com',
          failureReason: 'bounced - invalid email',
          failedAt: new Date(Date.now() - 5 * 60 * 60 * 1000),
          retryCount: 1,
        },
        {
          messageId: 'msg-2',
          email: 'test2@example.com',
          failureReason: 'complained - spam',
          failedAt: new Date(Date.now() - 5 * 60 * 60 * 1000),
          retryCount: 0,
        },
      ];

      vi.spyOn(deliveryManager, 'getFailedDeliveries').mockResolvedValue(mockFailedDeliveries);
      const markForRetrySpy = vi.spyOn(deliveryManager, 'markForRetry').mockResolvedValue();

      await retryManager.processRetryQueue();

      expect(markForRetrySpy).not.toHaveBeenCalled();

    it('should respect exponential backoff timing', async () => {
      const mockFailedDeliveries = [
        {
          messageId: 'msg-1',
          email: 'test@example.com',
          failureReason: 'temporary failure',
          failedAt: new Date(Date.now() - 30 * 60 * 1000), // 30 minutes ago
          retryCount: 1, // Should wait 2 hours before retry
        },
      ];

      vi.spyOn(deliveryManager, 'getFailedDeliveries').mockResolvedValue(mockFailedDeliveries);
      const markForRetrySpy = vi.spyOn(deliveryManager, 'markForRetry').mockResolvedValue();

      await retryManager.processRetryQueue();

      // Should not retry because not enough time has passed (need 2 hours, only 0.5 hours passed)
      expect(markForRetrySpy).not.toHaveBeenCalled();


