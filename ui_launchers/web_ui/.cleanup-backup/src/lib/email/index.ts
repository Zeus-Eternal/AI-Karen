/**
 * Email Integration System
 * 
 * Main entry point for the email integration system providing templates,
 * queue management, delivery tracking, and notification services.
 */

// Export types
export * from './types';

// Export configuration
export * from './config';

// Export template engine
export * from './template-engine';

// Export email service
export * from './email-service';

// Export queue management
export * from './email-queue';

// Export delivery tracking
export * from './delivery-tracker';

// Main email integration class
export class EmailIntegration {
  private static instance: EmailIntegration;
  
  private constructor() {}
  
  static getInstance(): EmailIntegration {
    if (!EmailIntegration.instance) {
      EmailIntegration.instance = new EmailIntegration();
    }
    return EmailIntegration.instance;
  }
  
  /**
   * Initialize email integration system
   */
  async initialize(): Promise<void> {
    const { emailService } = await import('./email-service');
    await emailService.initialize();
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
  ) {
    const { emailService } = await import('./email-service');
    return emailService.sendAdminInvitation(email, fullName, invitedByName, invitationLink, expiryDate);
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
  ) {
    const { emailService } = await import('./email-service');
    return emailService.sendUserWelcome(email, fullName, role, createdByName, setupLink);
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
  ) {
    const { emailService } = await import('./email-service');
    return emailService.sendSecurityAlert(email, alertType, alertDescription, ipAddress, actionRequired);
  }
  
  /**
   * Get email service health
   */
  async getServiceHealth() {
    const { emailService } = await import('./email-service');
    return emailService.testConnection();
  }
  
  /**
   * Get queue statistics
   */
  async getQueueStats() {
    const { emailQueueManager } = await import('./email-queue');
    return emailQueueManager.getQueueStats();
  }
  
  /**
   * Get delivery statistics
   */
  async getDeliveryStats(startDate?: Date, endDate?: Date, templateId?: string) {
    const { deliveryStatusManager } = await import('./delivery-tracker');
    return deliveryStatusManager.getDeliveryStatistics(startDate, endDate, templateId);
  }
}

// Export singleton instance
export const emailIntegration = EmailIntegration.getInstance();