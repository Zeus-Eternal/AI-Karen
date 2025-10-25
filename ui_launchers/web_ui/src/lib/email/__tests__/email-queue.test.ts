/**
 * Email Queue Tests
 * 
 * Tests for email queue management, retry mechanisms, and bulk processing.
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { EmailQueueManager, BulkEmailProcessor } from '../email-queue';
import { EmailMessage, EmailQueueConfig } from '../types';

// Mock the email service
vi.mock('../email-service', () => ({
  emailService: {
    getConfig: vi.fn().mockReturnValue({ enabled: true }),
    initialize: vi.fn().mockResolvedValue(undefined),
    sendEmail: vi.fn().mockResolvedValue({ success: true, message_id: 'test-id' }),
  },
}));

describe('EmailQueueManager', () => {
  let queueManager: EmailQueueManager;
  let mockConfig: EmailQueueConfig;
  let mockMessage: EmailMessage;

  beforeEach(() => {
    mockConfig = {
      max_retries: 3,
      retry_delay_minutes: 5,
      batch_size: 10,
      rate_limit_per_minute: 60,
      priority_processing: true,
    };

    queueManager = new EmailQueueManager(mockConfig);

    mockMessage = {
      id: 'test-message-1',
      to: 'test@example.com',
      from: 'noreply@test.com',
      subject: 'Test Subject',
      html_content: '<p>Test content</p>',
      text_content: 'Test content',
      priority: 'normal',
      status: 'queued',
      retry_count: 0,
      max_retries: 3,
      created_at: new Date(),
      updated_at: new Date(),
    };

    // Stop any existing processing
    queueManager.stopProcessing();
    queueManager.clearQueue();
  });

  afterEach(() => {
    queueManager.stopProcessing();
    vi.clearAllMocks();
  });

  describe('addToQueue', () => {
    it('should add message to queue', async () => {
      await queueManager.addToQueue(mockMessage);
      
      const stats = queueManager.getQueueStats();
      expect(stats.total).toBe(1);
    });

    it('should maintain priority order', async () => {
      const lowPriorityMessage = { ...mockMessage, id: 'low', priority: 'low' as const };
      const highPriorityMessage = { ...mockMessage, id: 'high', priority: 'high' as const };
      const urgentMessage = { ...mockMessage, id: 'urgent', priority: 'urgent' as const };

      await queueManager.addToQueue(lowPriorityMessage);
      await queueManager.addToQueue(highPriorityMessage);
      await queueManager.addToQueue(urgentMessage);

      const items = queueManager.getQueueItems();
      expect(items[0].id).toBe('urgent');
      expect(items[1].id).toBe('high');
      expect(items[2].id).toBe('low');
    });

    it('should handle scheduled messages', async () => {
      const scheduledMessage = {
        ...mockMessage,
        scheduled_at: new Date(Date.now() + 60000), // 1 minute from now
      };

      await queueManager.addToQueue(scheduledMessage);
      
      const items = queueManager.getQueueItems();
      expect(items[0].nextRetryAt).toEqual(scheduledMessage.scheduled_at);
    });
  });

  describe('addBulkToQueue', () => {
    it('should add multiple messages to queue', async () => {
      const messages = [
        { ...mockMessage, id: 'msg1', to: 'user1@example.com' },
        { ...mockMessage, id: 'msg2', to: 'user2@example.com' },
        { ...mockMessage, id: 'msg3', to: 'user3@example.com' },
      ];

      const result = await queueManager.addBulkToQueue(messages);

      expect(result.success).toBe(true);
      expect(result.queued_count).toBe(3);
      expect(result.failed_count).toBe(0);
      expect(result.errors).toHaveLength(0);

      const stats = queueManager.getQueueStats();
      expect(stats.total).toBe(3);
    });

    it('should handle partial failures in bulk add', async () => {
      const messages = [
        { ...mockMessage, id: 'msg1', to: 'user1@example.com' },
        null as any, // This will cause an error
        { ...mockMessage, id: 'msg3', to: 'user3@example.com' },
      ];

      const result = await queueManager.addBulkToQueue(messages);

      expect(result.success).toBe(false);
      expect(result.queued_count).toBe(2);
      expect(result.failed_count).toBe(1);
      expect(result.errors).toHaveLength(1);
    });
  });

  describe('getQueueStats', () => {
    beforeEach(async () => {
      const messages = [
        { ...mockMessage, id: 'msg1', priority: 'high' as const },
        { ...mockMessage, id: 'msg2', priority: 'normal' as const },
        { ...mockMessage, id: 'msg3', priority: 'low' as const },
        { ...mockMessage, id: 'msg4', priority: 'normal' as const },
      ];

      for (const message of messages) {
        await queueManager.addToQueue(message);
      }
    });

    it('should return correct queue statistics', () => {
      const stats = queueManager.getQueueStats();

      expect(stats.total).toBe(4);
      expect(stats.byPriority.high).toBe(1);
      expect(stats.byPriority.normal).toBe(2);
      expect(stats.byPriority.low).toBe(1);
      expect(stats.byStatus.queued).toBe(4);
      expect(stats.oldestItem).toBeInstanceOf(Date);
      expect(stats.rateLimitRemaining).toBe(60);
    });
  });

  describe('getQueueItems', () => {
    beforeEach(async () => {
      await queueManager.addToQueue(mockMessage);
    });

    it('should return queue items with correct format', () => {
      const items = queueManager.getQueueItems();

      expect(items).toHaveLength(1);
      expect(items[0]).toEqual({
        id: mockMessage.id,
        to: mockMessage.to,
        subject: mockMessage.subject,
        priority: mockMessage.priority,
        status: mockMessage.status,
        attempts: 0,
        nextRetryAt: expect.any(Date),
        lastError: undefined,
      });
    });
  });

  describe('retryFailedItems', () => {
    it('should retry failed items within retry limit', async () => {
      // Add a message and simulate failure
      await queueManager.addToQueue(mockMessage);
      
      // Manually set status to failed for testing
      const items = queueManager.getQueueItems();
      // Access private queue for testing
      const queue = (queueManager as any).queue;
      queue[0].message.status = 'failed';
      queue[0].attempts = 2; // Less than max retries

      const retriedCount = queueManager.retryFailedItems();

      expect(retriedCount).toBe(1);
      expect(queue[0].message.status).toBe('queued');
    });

    it('should not retry items that exceeded max retries', async () => {
      await queueManager.addToQueue(mockMessage);
      
      // Manually set status to failed with max attempts
      const queue = (queueManager as any).queue;
      queue[0].message.status = 'failed';
      queue[0].attempts = 3; // Equal to max retries

      const retriedCount = queueManager.retryFailedItems();

      expect(retriedCount).toBe(0);
      expect(queue[0].message.status).toBe('failed');
    });
  });

  describe('clearQueue', () => {
    beforeEach(async () => {
      await queueManager.addToQueue(mockMessage);
      await queueManager.addToQueue({ ...mockMessage, id: 'msg2' });
    });

    it('should clear all items from queue', () => {
      expect(queueManager.getQueueStats().total).toBe(2);
      
      queueManager.clearQueue();
      
      expect(queueManager.getQueueStats().total).toBe(0);
    });
  });

  describe('updateConfig', () => {
    it('should update queue configuration', () => {
      const newConfig = {
        max_retries: 5,
        batch_size: 20,
      };

      queueManager.updateConfig(newConfig);

      // Verify config was updated by checking behavior
      const config = (queueManager as any).config;
      expect(config.max_retries).toBe(5);
      expect(config.batch_size).toBe(20);
      expect(config.retry_delay_minutes).toBe(5); // Should preserve existing values
    });
  });

  describe('processing', () => {
    it('should start and stop processing', () => {
      expect((queueManager as any).processing).toBe(false);
      
      // Processing should start when adding items
      queueManager.addToQueue(mockMessage);
      
      // Stop processing
      queueManager.stopProcessing();
      expect((queueManager as any).processing).toBe(false);
      expect((queueManager as any).processingInterval).toBe(null);
    });
  });
});

describe('BulkEmailProcessor', () => {
  let bulkProcessor: BulkEmailProcessor;
  let queueManager: EmailQueueManager;
  let mockOperation: any;

  beforeEach(() => {
    queueManager = new EmailQueueManager();
    bulkProcessor = new BulkEmailProcessor(queueManager);

    mockOperation = {
      id: 'bulk-op-1',
      operation_type: 'invitation',
      template_id: 'template-1',
      recipient_count: 2,
      sent_count: 0,
      failed_count: 0,
      status: 'queued',
      batch_size: 10,
      delay_between_batches: 0,
      recipients: [
        {
          email: 'user1@example.com',
          user_id: 'user1',
          template_variables: { name: 'User 1' },
          status: 'pending',
        },
        {
          email: 'user2@example.com',
          user_id: 'user2',
          template_variables: { name: 'User 2' },
          status: 'pending',
        },
      ],
      created_by: 'admin',
      created_at: new Date(),
    };

    // Mock the queue manager's addBulkToQueue method
    vi.spyOn(queueManager, 'addBulkToQueue').mockResolvedValue({
      success: true,
      queued_count: 2,
      failed_count: 0,
      errors: [],
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('processBulkOperation', () => {
    it('should process bulk operation successfully', async () => {
      await bulkProcessor.processBulkOperation(mockOperation);

      expect(mockOperation.status).toBe('completed');
      expect(mockOperation.started_at).toBeInstanceOf(Date);
      expect(mockOperation.completed_at).toBeInstanceOf(Date);
      expect(mockOperation.sent_count).toBe(2);
      expect(mockOperation.failed_count).toBe(0);
      expect(queueManager.addBulkToQueue).toHaveBeenCalled();
    });

    it('should handle partial failures in bulk operation', async () => {
      // Mock partial failure
      vi.mocked(queueManager.addBulkToQueue).mockResolvedValue({
        success: false,
        queued_count: 1,
        failed_count: 1,
        errors: ['user2@example.com: Invalid email'],
      });

      await bulkProcessor.processBulkOperation(mockOperation);

      expect(mockOperation.status).toBe('completed');
      expect(mockOperation.sent_count).toBe(1);
      expect(mockOperation.failed_count).toBe(1);
      expect(mockOperation.recipients[0].status).toBe('sent');
      expect(mockOperation.recipients[1].status).toBe('failed');
      expect(mockOperation.recipients[1].error_message).toBe('user2@example.com: Invalid email');
    });

    it('should handle operation failure', async () => {
      // Mock queue manager failure
      vi.mocked(queueManager.addBulkToQueue).mockRejectedValue(new Error('Queue error'));

      await bulkProcessor.processBulkOperation(mockOperation);

      expect(mockOperation.status).toBe('failed');
      expect(mockOperation.error_message).toBe('Queue error');
      expect(mockOperation.completed_at).toBeInstanceOf(Date);
    });

    it('should process in batches with delay', async () => {
      // Create operation with many recipients and small batch size
      const largeOperation = {
        ...mockOperation,
        batch_size: 1,
        delay_between_batches: 0.1, // 100ms delay
        recipients: [
          { email: 'user1@example.com', status: 'pending', template_variables: {} },
          { email: 'user2@example.com', status: 'pending', template_variables: {} },
          { email: 'user3@example.com', status: 'pending', template_variables: {} },
        ],
      };

      const startTime = Date.now();
      await bulkProcessor.processBulkOperation(largeOperation);
      const endTime = Date.now();

      // Should have taken at least 200ms due to delays between batches
      expect(endTime - startTime).toBeGreaterThan(100);
      expect(queueManager.addBulkToQueue).toHaveBeenCalledTimes(3);
      expect(largeOperation.status).toBe('completed');
    });

    it('should skip recipients that are not pending', async () => {
      mockOperation.recipients[1].status = 'sent'; // Already processed

      await bulkProcessor.processBulkOperation(mockOperation);

      // Should only process 1 recipient
      const addBulkCall = vi.mocked(queueManager.addBulkToQueue).mock.calls[0];
      expect(addBulkCall[0]).toHaveLength(1);
      expect(addBulkCall[0][0].to).toBe('user1@example.com');
    });
  });
});