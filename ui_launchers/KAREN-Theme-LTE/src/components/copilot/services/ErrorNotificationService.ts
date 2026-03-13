import { ErrorInfo, ErrorCategory, ErrorSeverity } from './ErrorHandlingService';

/**
 * Notification types
 */
export enum NotificationType {
  /** Toast notification */
  TOAST = 'toast',
  
  /** Modal notification */
  MODAL = 'modal',
  
  /** Inline notification */
  INLINE = 'inline',
  
  /** Banner notification */
  BANNER = 'banner'
}

/**
 * Notification positions
 */
export enum NotificationPosition {
  /** Top right position */
  TOP_RIGHT = 'top-right',
  
  /** Top left position */
  TOP_LEFT = 'top-left',
  
  /** Bottom right position */
  BOTTOM_RIGHT = 'bottom-right',
  
  /** Bottom left position */
  BOTTOM_LEFT = 'bottom-left',
  
  /** Top center position */
  TOP_CENTER = 'top-center',
  
  /** Bottom center position */
  BOTTOM_CENTER = 'bottom-center'
}

/**
 * Notification theme
 */
export enum NotificationTheme {
  /** Light theme */
  LIGHT = 'light',
  
  /** Dark theme */
  DARK = 'dark',
  
  /** System theme */
  SYSTEM = 'system'
}

/**
 * Notification configuration
 */
export interface NotificationConfig {
  /** Notification type */
  type: NotificationType;
  
  /** Notification position */
  position: NotificationPosition;
  
  /** Notification theme */
  theme: NotificationTheme;
  
  /** Whether to auto-close the notification */
  autoClose: boolean;
  
  /** Auto-close duration in milliseconds */
  autoCloseDuration: number;
  
  /** Whether to show close button */
  showCloseButton: boolean;
  
  /** Whether to show progress bar for auto-close */
  showProgressBar: boolean;
  
  /** Maximum number of notifications to show */
  maxNotifications: number;
  
  /** Whether to stack notifications */
  stackNotifications: boolean;
  
  /** Default notification duration by severity */
  durationBySeverity: Record<ErrorSeverity, number>;
}

/**
 * Notification data
 */
export interface NotificationData {
  /** Unique notification ID */
  id: string;
  
  /** Notification title */
  title: string;
  
  /** Notification message */
  message: string;
  
  /** Error information */
  error?: ErrorInfo;
  
  /** Notification type */
  type: NotificationType;
  
  /** Notification severity */
  severity: ErrorSeverity;
  
  /** Notification timestamp */
  timestamp: Date;
  
  /** Whether the notification is visible */
  visible: boolean;
  
  /** Whether the notification is closing */
  closing: boolean;

  /** Whether this notification should auto-close */
  autoClose: boolean;

  /** Auto-close duration for this notification in milliseconds */
  autoCloseDuration: number;
  
  /** Notification actions */
  actions?: NotificationAction[];
  
  /** Custom CSS class */
  className?: string;
}

/**
 * Notification action
 */
export interface NotificationAction {
  /** Action label */
  label: string;
  
  /** Action callback */
  callback: () => void;
  
  /** Action type */
  type?: 'primary' | 'secondary' | 'danger';
  
  /** Whether to close notification when action is clicked */
  closeOnClick?: boolean;
}

interface NotificationEvent {
  type: string;
  timestamp: Date;
  [key: string]: unknown;
}

type NotificationEventListener = (event: NotificationEvent) => void;
type NotificationEventPayload = Record<string, unknown>;

/**
 * Service for managing error notifications
 */
class ErrorNotificationService {
  private static instance: ErrorNotificationService;
  private notifications: Map<string, NotificationData> = new Map();
  private notificationListeners: Map<string, NotificationEventListener[]> = new Map();
  private config: NotificationConfig;
  private notificationQueue: NotificationData[] = [];
  private activeNotifications: Set<string> = new Set();
  
  private constructor() {
    this.config = this.getDefaultConfig();
  }
  
  public static getInstance(): ErrorNotificationService {
    if (!ErrorNotificationService.instance) {
      ErrorNotificationService.instance = new ErrorNotificationService();
    }
    return ErrorNotificationService.instance;
  }
  
  /**
   * Get default configuration
   */
  private getDefaultConfig(): NotificationConfig {
    return {
      type: NotificationType.TOAST,
      position: NotificationPosition.TOP_RIGHT,
      theme: NotificationTheme.SYSTEM,
      autoClose: true,
      autoCloseDuration: 5000,
      showCloseButton: true,
      showProgressBar: true,
      maxNotifications: 5,
      stackNotifications: true,
      durationBySeverity: {
        [ErrorSeverity.LOW]: 3000,
        [ErrorSeverity.MEDIUM]: 5000,
        [ErrorSeverity.HIGH]: 8000,
        [ErrorSeverity.CRITICAL]: 12000
      }
    };
  }
  
  /**
   * Update configuration
   */
  public updateConfig(config: Partial<NotificationConfig>): void {
    this.config = { ...this.config, ...config };
    
    // Emit config updated event
    this.emitNotificationEvent('config_updated', { config: this.config });
  }
  
  /**
   * Get current configuration
   */
  public getConfig(): NotificationConfig {
    return { ...this.config };
  }
  
  /**
   * Show error notification
   */
  public showErrorNotification(
    error: ErrorInfo,
    options?: {
      title?: string;
      message?: string;
      type?: NotificationType;
      position?: NotificationPosition;
      theme?: NotificationTheme;
      autoClose?: boolean;
      autoCloseDuration?: number;
      showCloseButton?: boolean;
      showProgressBar?: boolean;
      actions?: NotificationAction[];
      className?: string;
    }
  ): string {
    // Create notification data
    const notification: NotificationData = {
      id: this.generateNotificationId(),
      title: options?.title || this.getTitleBySeverity(error.severity),
      message: options?.message || error.message,
      error,
      type: options?.type || this.config.type,
      severity: error.severity,
      timestamp: new Date(),
      visible: true,
      closing: false,
      autoClose: options?.autoClose ?? this.config.autoClose,
      autoCloseDuration:
        options?.autoCloseDuration ??
        this.config.durationBySeverity[error.severity] ??
        this.config.autoCloseDuration,
      actions: options?.actions,
      className: options?.className
    };
    
    // Add to notifications map
    this.notifications.set(notification.id, notification);
    
    // Add to queue
    this.notificationQueue.push(notification);
    
    // Process queue
    this.processNotificationQueue();
    
    // Return notification ID
    return notification.id;
  }
  
  /**
   * Show custom notification
   */
  public showNotification(
    title: string,
    message: string,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    options?: {
      type?: NotificationType;
      position?: NotificationPosition;
      theme?: NotificationTheme;
      autoClose?: boolean;
      autoCloseDuration?: number;
      showCloseButton?: boolean;
      showProgressBar?: boolean;
      actions?: NotificationAction[];
      className?: string;
    }
  ): string {
    // Create error info for notification
    const errorInfo: ErrorInfo = {
      id: this.generateErrorId(),
      timestamp: new Date(),
      severity,
      category: ErrorCategory.UNKNOWN,
      code: 'notification',
      message,
      resolved: false,
      count: 1,
      firstOccurrence: new Date(),
      lastOccurrence: new Date()
    };
    
    // Show notification
    return this.showErrorNotification(errorInfo, {
      title,
      message,
      ...options
    });
  }
  
  /**
   * Close notification
   */
  public closeNotification(notificationId: string): boolean {
    const notification = this.notifications.get(notificationId);
    
    if (!notification) {
      return false;
    }
    
    // Mark as closing
    notification.closing = true;
    this.notifications.set(notificationId, notification);
    
    // Emit closing event
    this.emitNotificationEvent('notification_closing', { notification });
    
    // Remove from active notifications
    this.activeNotifications.delete(notificationId);
    
    // Process queue after a short delay
    setTimeout(() => {
      this.removeNotification(notificationId);
      this.processNotificationQueue();
    }, 300);
    
    return true;
  }
  
  /**
   * Remove notification
   */
  public removeNotification(notificationId: string): boolean {
    const removed = this.notifications.delete(notificationId);
    
    if (removed) {
      // Remove from queue
      this.notificationQueue = this.notificationQueue.filter(
        notification => notification.id !== notificationId
      );
      
      // Remove from active notifications
      this.activeNotifications.delete(notificationId);
      
      // Emit removed event
      this.emitNotificationEvent('notification_removed', { notificationId });
    }
    
    return removed;
  }
  
  /**
   * Close all notifications
   */
  public closeAllNotifications(): void {
    // Get all active notification IDs
    const activeIds = Array.from(this.activeNotifications);
    
    // Close each notification
    activeIds.forEach(id => this.closeNotification(id));
  }
  
  /**
   * Remove all notifications
   */
  public removeAllNotifications(): void {
    // Clear notifications map
    this.notifications.clear();
    
    // Clear queue
    this.notificationQueue = [];
    
    // Clear active notifications
    this.activeNotifications.clear();
    
    // Emit cleared event
    this.emitNotificationEvent('notifications_cleared', {});
  }
  
  /**
   * Get notification by ID
   */
  public getNotification(notificationId: string): NotificationData | undefined {
    return this.notifications.get(notificationId);
  }
  
  /**
   * Get all notifications
   */
  public getAllNotifications(includeHidden: boolean = false): NotificationData[] {
    const notifications = Array.from(this.notifications.values());
    
    if (!includeHidden) {
      return notifications.filter(notification => notification.visible);
    }
    
    return notifications;
  }
  
  /**
   * Get active notifications
   */
  public getActiveNotifications(): NotificationData[] {
    return Array.from(this.activeNotifications)
      .map(id => this.notifications.get(id))
      .filter(Boolean) as NotificationData[];
  }
  
  /**
   * Add notification event listener
   */
  public addNotificationEventListener(eventType: string, listener: NotificationEventListener): void {
    if (!this.notificationListeners.has(eventType)) {
      this.notificationListeners.set(eventType, []);
    }
    this.notificationListeners.get(eventType)?.push(listener);
  }
  
  /**
   * Remove notification event listener
   */
  public removeNotificationEventListener(eventType: string, listener: NotificationEventListener): void {
    const listeners = this.notificationListeners.get(eventType);
    if (listeners) {
      const index = listeners.indexOf(listener);
      if (index !== -1) {
        listeners.splice(index, 1);
      }
    }
  }
  
  /**
   * Process notification queue
   */
  private processNotificationQueue(): void {
    // If we have reached the maximum number of notifications, stop
    if (this.activeNotifications.size >= this.config.maxNotifications) {
      return;
    }
    
    // Get the next notification from the queue
    const nextNotification = this.notificationQueue.find(
      notification => 
        notification.visible && 
        !notification.closing && 
        !this.activeNotifications.has(notification.id)
    );
    
    if (!nextNotification) {
      return;
    }
    
    // Add to active notifications
    this.activeNotifications.add(nextNotification.id);
    
    // Emit show event
    this.emitNotificationEvent('notification_show', { notification: nextNotification });
    
    // Schedule auto-close if enabled for this notification
    if (nextNotification.autoClose) {
      const duration = nextNotification.autoCloseDuration;
      
      setTimeout(() => {
        if (this.activeNotifications.has(nextNotification.id)) {
          this.closeNotification(nextNotification.id);
        }
      }, duration);
    }
    
    // Process next notification in queue
    if (this.config.stackNotifications) {
      setTimeout(() => {
        this.processNotificationQueue();
      }, 100);
    }
  }
  
  /**
   * Get title by error severity
   */
  private getTitleBySeverity(severity: ErrorSeverity): string {
    switch (severity) {
      case ErrorSeverity.LOW:
        return 'Notice';
      case ErrorSeverity.MEDIUM:
        return 'Warning';
      case ErrorSeverity.HIGH:
        return 'Error';
      case ErrorSeverity.CRITICAL:
        return 'Critical Error';
      default:
        return 'Notification';
    }
  }
  
  /**
   * Generate a unique notification ID
   */
  private generateNotificationId(): string {
    return `notification_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
  
  /**
   * Generate a unique error ID
   */
  private generateErrorId(): string {
    return `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
  
  /**
   * Emit notification event
   */
  private emitNotificationEvent(eventType: string, data: NotificationEventPayload): void {
    const listeners = this.notificationListeners.get(eventType);
    if (listeners) {
      listeners.forEach(listener => {
        try {
          listener({
            type: eventType,
            timestamp: new Date(),
            ...data
          });
        } catch (error) {
          console.error(`Error in notification event listener for ${eventType}:`, error);
        }
      });
    }
  }
}

export default ErrorNotificationService;
