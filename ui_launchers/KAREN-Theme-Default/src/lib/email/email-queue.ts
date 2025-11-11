/**
 * Email Queue System
 * 
 * Reliable email delivery system with retry mechanisms, rate limiting,
 * and priority processing for admin notifications.
 */
import { EmailMessage, EmailQueueConfig, EmailQueueResponse } from './types';
import { DEFAULT_QUEUE_CONFIG } from './config';
import { emailService } from './email-service';

/**
 * Email Queue Item
 */
export interface QueueItem {
  id: string;
  message: EmailMessage;
  priority: number; // Higher number = higher priority
  attempts: number;
  nextRetryAt: Date;
  createdAt: Date;
  lastError?: string;
}

/**
 * Email Queue Manager
 */
export class EmailQueueManager {
  private queue: QueueItem[] = [];
  private processing = false;
  private config: EmailQueueConfig;
  private processingInterval: NodeJS.Timeout | null = null;
  private rateLimitCounter = 0;
  private rateLimitResetTime = Date.now() + 60000; // Reset every minute
  constructor(config: EmailQueueConfig = DEFAULT_QUEUE_CONFIG) {
    this.config = config;
  }

  /**
   * Add email to queue
   */
  async addToQueue(message: EmailMessage): Promise<void> {
    const priority = this.getPriorityScore(message.priority);
    const queueItem: QueueItem = {
      id: message.id,
      message,
      priority,
      attempts: 0,
      nextRetryAt: message.scheduled_at || new Date(),
      createdAt: new Date(),
    };

    // Insert in priority order
    const insertIndex = this.queue.findIndex(item => item.priority < priority);
    if (insertIndex === -1) {
      this.queue.push(queueItem);
    } else {
      this.queue.splice(insertIndex, 0, queueItem);
    }

    // Start processing if not already running
    if (!this.processing) {
      this.startProcessing();
    }
  }

  /**
   * Add multiple emails to queue
   */
  async addBulkToQueue(messages: EmailMessage[]): Promise<EmailQueueResponse> {
    let queuedCount = 0;
    let failedCount = 0;
    const errors: string[] = [];

    for (const message of messages) {
      try {
        await this.addToQueue(message);
        queuedCount++;
      } catch (error) {
        failedCount++;
        errors.push(`Failed to queue ${message?.to || 'unknown'}: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    }

    return {
      success: failedCount === 0,
      queued_count: queuedCount,
      failed_count: failedCount,
      errors,
    };
  }

  /**
   * Start queue processing
   */
  startProcessing(): void {
    if (this.processing) return;
    this.processing = true;
    this.processingInterval = setInterval(() => {
      this.processQueue();
    }, 5000); // Process every 5 seconds
  }

  /**
   * Stop queue processing
   */
  stopProcessing(): void {
    this.processing = false;
    if (this.processingInterval) {
      clearInterval(this.processingInterval);
      this.processingInterval = null;
    }
  }

  /**
   * Process queue items
   */
  private async processQueue(): Promise<void> {
    if (this.queue.length === 0) {
      return;
    }

    // Check rate limit
    if (!this.checkRateLimit()) {
      return;
    }

    // Get items ready for processing
    const now = new Date();
    const readyItems = this.queue
      .filter(item => item.nextRetryAt <= now)
      .slice(0, this.config.batch_size); // Process up to batch_size emails at once

    if (readyItems.length === 0) {
      return;
    }

    // Process items
    for (const item of readyItems) {
      await this.processQueueItem(item);
    }
  }

  /**
   * Process individual queue item
   */
  private async processQueueItem(item: QueueItem): Promise<void> {
    try {
      item.attempts++;
      item.message.retry_count = item.attempts - 1;
      item.message.status = 'sending';

      // Initialize email service if needed
      if (!emailService.getConfig()) {
        await emailService.initialize();
      }

      // Send email
      const result = await emailService.sendEmail(
        item.message.to,
        item.message.subject,
        item.message.html_content,
        item.message.text_content,
        {
          priority: item.message.priority,
          replyTo: item.message.reply_to,
        }
      );

      if (result.success) {
        // Success - remove from queue
        item.message.status = 'sent';
        item.message.sent_at = new Date();
        this.removeFromQueue(item.id);
        await this.logDeliveryStatus(item.message.id, 'sent', 'Email sent successfully');
      } else {
        // Failed - retry or give up
        await this.handleFailure(item, result.error || 'Unknown error');
      }

      // Update rate limit counter
      this.rateLimitCounter++;
    } catch (error) {
      await this.handleFailure(item, error instanceof Error ? error.message : 'Unknown error');
    }
  }

  /**
   * Handle email sending failure
   */
  private async handleFailure(item: QueueItem, error: string): Promise<void> {
    item.lastError = error;
    item.message.error_message = error;

    if (item.attempts >= this.config.max_retries) {
      // Max retries reached - mark as failed and remove from queue
      item.message.status = 'failed';
      item.message.failed_at = new Date();
      this.removeFromQueue(item.id);
      await this.logDeliveryStatus(item.message.id, 'failed', error);
    } else {
      // Schedule retry
      const retryDelay = this.config.retry_delay_minutes * Math.pow(2, item.attempts - 1); // Exponential backoff
      item.nextRetryAt = new Date(Date.now() + retryDelay * 60000);
      item.message.status = 'queued';
      await this.logDeliveryStatus(item.message.id, 'failed', `Retry ${item.attempts}/${this.config.max_retries}: ${error}`);
    }
  }

  /**
   * Remove item from queue
   */
  private removeFromQueue(itemId: string): void {
    const index = this.queue.findIndex(item => item.id === itemId);
    if (index !== -1) {
      this.queue.splice(index, 1);
    }
  }

  /**
   * Check rate limit
   */
  private checkRateLimit(): boolean {
    const now = Date.now();
    // Reset counter if minute has passed
    if (now >= this.rateLimitResetTime) {
      this.rateLimitCounter = 0;
      this.rateLimitResetTime = now + 60000;
    }
    return this.rateLimitCounter < this.config.rate_limit_per_minute;
  }

  /**
   * Get priority score for message
   */
  private getPriorityScore(priority: EmailMessage['priority']): number {
    switch (priority) {
      case 'urgent': return 100;
      case 'high': return 75;
      case 'normal': return 50;
      case 'low': return 25;
      default: return 50;
    }
  }

  /**
   * Log delivery status
   */
  private async logDeliveryStatus(messageId: string, status: string, details: string): Promise<void> {
    // In a real implementation, this would save to database or log system
    console.log(`Message ID: ${messageId} | Status: ${status} | Details: ${details}`);
  }

  /**
   * Get queue statistics
   */
  getQueueStats(): {
    total: number;
    byPriority: Record<string, number>;
    byStatus: Record<string, number>;
    oldestItem?: Date;
    rateLimitRemaining: number;
  } {
    const stats = {
      total: this.queue.length,
      byPriority: {} as Record<string, number>,
      byStatus: {} as Record<string, number>,
      oldestItem: undefined as Date | undefined,
      rateLimitRemaining: Math.max(0, this.config.rate_limit_per_minute - this.rateLimitCounter),
    };

    // Calculate statistics
    this.queue.forEach(item => {
      // Priority stats
      const priorityKey = item.message.priority;
      stats.byPriority[priorityKey] = (stats.byPriority[priorityKey] || 0) + 1;

      // Status stats
      const statusKey = item.message.status;
      stats.byStatus[statusKey] = (stats.byStatus[statusKey] || 0) + 1;

      // Oldest item
      if (!stats.oldestItem || item.createdAt < stats.oldestItem) {
        stats.oldestItem = item.createdAt;
      }
    });

    return stats;
  }

  /**
   * Clear queue (for testing/maintenance)
   */
  clearQueue(): void {
    this.queue = [];
  }

  /**
   * Get queue items (for monitoring)
   */
  getQueueItems(): Array<{
    id: string;
    to: string;
    subject: string;
    priority: string;
    status: string;
    attempts: number;
    nextRetryAt: Date;
    lastError?: string;
  }> {
    return this.queue.map(item => ({
      id: item.id,
      to: item.message.to,
      subject: item.message.subject,
      priority: item.message.priority,
      status: item.message.status,
      attempts: item.attempts,
      nextRetryAt: item.nextRetryAt,
      lastError: item.lastError,
    }));
  }

  /**
   * Retry failed items
   */
  retryFailedItems(): number {
    let retriedCount = 0;
    const now = new Date();
    this.queue.forEach(item => {
      if (item.message.status === 'failed' && item.attempts < this.config.max_retries) {
        item.nextRetryAt = now;
        item.message.status = 'queued';
        retriedCount++;
      }
    });

    return retriedCount;
  }

  /**
   * Update queue configuration
   */
  updateConfig(newConfig: Partial<EmailQueueConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }
}

/**
 * Bulk Email Processor
 */
export class BulkEmailProcessor {
  constructor(private queueManager: EmailQueueManager) {}

  /**
   * Process bulk email operation
   */
  async processBulkOperation(operation: BulkEmailOperation): Promise<void> {
    operation.status = 'processing';
    operation.started_at = new Date();

    try {
      const messages: EmailMessage[] = [];
      // Create email messages for all recipients
      for (const recipient of operation.recipients) {
        if (recipient.status === 'pending') {
          const message: EmailMessage = {
            id: `bulk_${operation.id}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            to: recipient.email,
            from: 'noreply@ai-karen.com',
            subject: 'Bulk Email',
            html_content: 'Bulk email content',
            text_content: 'Bulk email content',
            template_id: operation.template_id,
            template_variables: recipient.template_variables,
            priority: 'normal',
            status: 'queued',
            retry_count: 0,
            max_retries: 3,
            created_at: new Date(),
            updated_at: new Date(),
          };
          messages.push(message);
        }
      }

      // Add to queue in batches
      const batchSize = operation.batch_size;
      for (let i = 0; i < messages.length; i += batchSize) {
        const batch = messages.slice(i, i + batchSize);
        const result = await this.queueManager.addBulkToQueue(batch);

        operation.sent_count += result.queued_count;
        operation.failed_count += result.failed_count;

        batch.forEach((message, index) => {
          const recipientIndex = i + index;
          if (recipientIndex < operation.recipients.length) {
            const hasError = index < result.errors.length;
            operation.recipients[recipientIndex].status = hasError ? 'failed' : 'sent';
            if (hasError) {
              operation.recipients[recipientIndex].error_message = result.errors[index];
            }
          }
        });

        if (operation.delay_between_batches > 0 && i + batchSize < messages.length) {
          await new Promise(resolve => setTimeout(resolve, operation.delay_between_batches * 1000));
        }
      }

      operation.status = 'completed';
      operation.completed_at = new Date();
    } catch (error) {
      operation.status = 'failed';
      operation.error_message = error instanceof Error ? error.message : 'Unknown error';
      operation.completed_at = new Date();
    }
  }
}

// Singleton instances
export const emailQueueManager = new EmailQueueManager();
export const bulkEmailProcessor = new BulkEmailProcessor(emailQueueManager);

// Auto-start queue processing
emailQueueManager.startProcessing();
