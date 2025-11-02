import { 
import { logger } from '@/lib/logger';
/**
 * Authenticated Extension Service
 * 
 * Extension service with proper authentication handling, error recovery,
 * and graceful degradation for extension API operations.
 * 
 * Requirements addressed:
 * - 3.1: Extension integration service error handling
 * - 3.2: Extension API calls with proper authentication
 * - 3.3: Authentication failures and retry logic
 * - 9.1: Graceful degradation when authentication fails
 * - 9.2: User-friendly error messages and recovery suggestions
 */


  getEnhancedKarenBackendService, 
  EnhancedKarenBackendService,
  ExtensionApiError 
} from '@/lib/auth/enhanced-karen-backend-service';

  getExtensionAuthErrorHandler,
  ExtensionAuthErrorHandler,
  ErrorClassification,
  RecoveryStrategy,
  ErrorContext
} from '@/lib/auth/extension-auth-error-handler';


// Extension interfaces
export interface ExtensionInfo {
  name: string;
  version: string;
  display_name?: string;
  description?: string;
  status: 'active' | 'inactive' | 'error' | 'loading';
  loaded_at?: string;
  error_message?: string;
  capabilities?: {
    background_tasks?: boolean;
    api_endpoints?: boolean;
    ui_components?: boolean;
  };
}

export interface BackgroundTask {
  id: string;
  name: string;
  extension_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  created_at: string;
  updated_at?: string;
  result?: any;
  error?: string;
}

export interface ExtensionEvent {
  id: string;
  extension_name: string;
  event_type: string;
  payload: Record<string, any>;
  timestamp: string;
  severity: 'info' | 'warning' | 'error';
}

// Service state interface
interface ServiceState {
  isOnline: boolean;
  lastError: ErrorClassification | null;
  fallbackMode: boolean;
  retryCount: number;
  lastSuccessfulRequest: Date | null;
}

/**
 * Authenticated Extension Service
 * 
 * Provides authenticated access to extension APIs with comprehensive
 * error handling, retry logic, and graceful degradation.
 */
export class AuthenticatedExtensionService {
  private backendService: EnhancedKarenBackendService;
  private errorHandler: ExtensionAuthErrorHandler;
  private serviceState: ServiceState;
  private eventSubscription: NodeJS.Timeout | null = null;
  private eventCallbacks: ((events: ExtensionEvent[]) => void)[] = [];

  constructor() {
    this.backendService = getEnhancedKarenBackendService();
    this.errorHandler = getExtensionAuthErrorHandler();
    this.serviceState = {
      isOnline: true,
      lastError: null,
      fallbackMode: false,
      retryCount: 0,
      lastSuccessfulRequest: null,
    };
  }

  /**
   * Get list of installed extensions
   */
  async getInstalledExtensions(): Promise<ExtensionInfo[]> {
    const context: ErrorContext = {
      endpoint: '/api/extensions/',
      method: 'GET',
      attempt: 1,
      maxAttempts: 3,
      timestamp: new Date(),
    };

    try {
      const extensions = await this.backendService.getExtensions();
      
      // Update service state on success
      this.updateServiceState(true, null);
      
      // Transform and validate extension data
      return this.transformExtensionData(extensions);
    } catch (error) {
      return this.handleServiceError(error, context, []);
    }
  }

  /**
   * Load an extension
   */
  async loadExtension(name: string): Promise<boolean> {
    const context: ErrorContext = {
      endpoint: `/api/extensions/${name}/load`,
      method: 'POST',
      attempt: 1,
      maxAttempts: 2,
      timestamp: new Date(),
    };

    try {
      await this.backendService.loadExtension(name);
      
      this.updateServiceState(true, null);
      logger.info(`Extension ${name} loaded successfully`);
      
      return true;
    } catch (error) {
      return this.handleServiceError(error, context, false);
    }
  }

  /**
   * Unload an extension
   */
  async unloadExtension(name: string): Promise<boolean> {
    const context: ErrorContext = {
      endpoint: `/api/extensions/${name}/unload`,
      method: 'POST',
      attempt: 1,
      maxAttempts: 2,
      timestamp: new Date(),
    };

    try {
      await this.backendService.unloadExtension(name);
      
      this.updateServiceState(true, null);
      logger.info(`Extension ${name} unloaded successfully`);
      
      return true;
    } catch (error) {
      return this.handleServiceError(error, context, false);
    }
  }

  /**
   * Get background tasks
   */
  async getBackgroundTasks(extensionName?: string): Promise<BackgroundTask[]> {
    const context: ErrorContext = {
      endpoint: '/api/extensions/background-tasks/',
      method: 'GET',
      attempt: 1,
      maxAttempts: 3,
      timestamp: new Date(),
    };

    try {
      const tasks = await this.backendService.getBackgroundTasks(extensionName);
      
      this.updateServiceState(true, null);
      
      return this.transformBackgroundTaskData(tasks);
    } catch (error) {
      return this.handleServiceError(error, context, []);
    }
  }

  /**
   * Register a background task
   */
  async registerBackgroundTask(taskData: {
    name: string;
    extension_name: string;
    schedule?: string;
    parameters?: Record<string, any>;
  }): Promise<string | null> {
    const context: ErrorContext = {
      endpoint: '/api/extensions/background-tasks/',
      method: 'POST',
      attempt: 1,
      maxAttempts: 2,
      timestamp: new Date(),
    };

    try {
      const result = await this.backendService.registerBackgroundTask(taskData);
      
      this.updateServiceState(true, null);
      logger.info(`Background task ${taskData.name} registered successfully`);
      
      return result.task_id || result.id || 'unknown';
    } catch (error) {
      return this.handleServiceError(error, context, null);
    }
  }

  /**
   * Subscribe to extension events
   */
  subscribeToEvents(
    callback: (events: ExtensionEvent[]) => void,
    interval: number = 5000
  ): void {
    // Add callback to list
    this.eventCallbacks.push(callback);

    // Start polling if not already started
    if (!this.eventSubscription) {
      this.startEventPolling(interval);
    }
  }

  /**
   * Unsubscribe from extension events
   */
  unsubscribeFromEvents(callback?: (events: ExtensionEvent[]) => void): void {
    if (callback) {
      // Remove specific callback
      const index = this.eventCallbacks.indexOf(callback);
      if (index > -1) {
        this.eventCallbacks.splice(index, 1);
      }
    } else {
      // Remove all callbacks
      this.eventCallbacks = [];
    }

    // Stop polling if no callbacks remain
    if (this.eventCallbacks.length === 0 && this.eventSubscription) {
      clearInterval(this.eventSubscription);
      this.eventSubscription = null;
    }
  }

  /**
   * Get extension health status
   */
  async getExtensionHealth(): Promise<{
    status: 'healthy' | 'degraded' | 'unhealthy';
    services: Record<string, any>;
    timestamp: string;
  }> {
    try {
      const health = await this.backendService.getExtensionHealth();
      this.updateServiceState(true, null);
      return health;
    } catch (error) {
      logger.warn('Extension health check failed:', error);
      return {
        status: 'unhealthy',
        services: {},
        timestamp: new Date().toISOString(),
      };
    }
  }

  /**
   * Get current service state
   */
  getServiceState(): Readonly<ServiceState> {
    return { ...this.serviceState };
  }

  /**
   * Check if service is in fallback mode
   */
  isInFallbackMode(): boolean {
    return this.serviceState.fallbackMode;
  }

  /**
   * Force exit fallback mode and retry
   */
  async exitFallbackMode(): Promise<boolean> {
    this.serviceState.fallbackMode = false;
    this.serviceState.retryCount = 0;
    
    try {
      // Test connectivity with a simple health check
      await this.getExtensionHealth();
      return true;
    } catch (error) {
      logger.warn('Failed to exit fallback mode:', error);
      return false;
    }
  }

  /**
   * Start event polling
   */
  private startEventPolling(interval: number): void {
    this.eventSubscription = setInterval(async () => {
      if (this.eventCallbacks.length === 0) return;

      try {
        // This would need to be implemented in the backend service
        // For now, we'll create a placeholder
        const events: ExtensionEvent[] = [];
        
        if (events.length > 0) {
          this.eventCallbacks.forEach(callback => {
            try {
              callback(events);
            } catch (error) {
              logger.error('Error in event callback:', error);
            }
          });
        }
      } catch (error) {
        logger.warn('Failed to poll extension events:', error);
      }
    }, interval);
  }

  /**
   * Handle service errors with recovery strategies
   */
  private handleServiceError<T>(
    error: any,
    context: ErrorContext,
    fallbackValue: T
  ): T {
    const classification = this.errorHandler.handleError(error, context);
    
    // Update service state
    this.updateServiceState(false, classification);
    
    // Determine if we should use fallback mode
    if (this.errorHandler.shouldUseFallbackMode(classification)) {
      this.serviceState.fallbackMode = true;
      logger.warn(`Entering fallback mode for ${context.endpoint}`);
    }

    // Log user-friendly error message
    const userMessage = this.errorHandler.getUserFriendlyMessage(classification);
    logger.error(`Extension service error: ${userMessage}`);

    // Return fallback value or re-throw based on error type
    if (classification.severity === 'critical' && !classification.fallbackAvailable) {
      throw error;
    }

    return fallbackValue;
  }

  /**
   * Update service state
   */
  private updateServiceState(
    isOnline: boolean,
    error: ErrorClassification | null
  ): void {
    this.serviceState.isOnline = isOnline;
    this.serviceState.lastError = error;
    
    if (isOnline) {
      this.serviceState.lastSuccessfulRequest = new Date();
      this.serviceState.retryCount = 0;
    } else {
      this.serviceState.retryCount++;
    }
  }

  /**
   * Transform extension data to ensure consistency
   */
  private transformExtensionData(extensions: any[]): ExtensionInfo[] {
    return extensions.map(ext => ({
      name: ext.name || 'unknown',
      version: ext.version || '0.0.0',
      display_name: ext.display_name || ext.name,
      description: ext.description || 'No description available',
      status: this.normalizeStatus(ext.status),
      loaded_at: ext.loaded_at,
      error_message: ext.error_message,
      capabilities: ext.capabilities || {},
    }));
  }

  /**
   * Transform background task data
   */
  private transformBackgroundTaskData(tasks: any[]): BackgroundTask[] {
    return tasks.map(task => ({
      id: task.id || task.task_id || 'unknown',
      name: task.name || 'Unnamed Task',
      extension_name: task.extension_name || 'unknown',
      status: this.normalizeTaskStatus(task.status),
      created_at: task.created_at || new Date().toISOString(),
      updated_at: task.updated_at,
      result: task.result,
      error: task.error,
    }));
  }

  /**
   * Normalize extension status
   */
  private normalizeStatus(status: any): ExtensionInfo['status'] {
    if (typeof status !== 'string') return 'inactive';
    
    const normalized = status.toLowerCase();
    if (['active', 'inactive', 'error', 'loading'].includes(normalized)) {
      return normalized as ExtensionInfo['status'];
    }
    
    return 'inactive';
  }

  /**
   * Normalize task status
   */
  private normalizeTaskStatus(status: any): BackgroundTask['status'] {
    if (typeof status !== 'string') return 'pending';
    
    const normalized = status.toLowerCase();
    if (['pending', 'running', 'completed', 'failed'].includes(normalized)) {
      return normalized as BackgroundTask['status'];
    }
    
    return 'pending';
  }

  /**
   * Cleanup resources
   */
  destroy(): void {
    this.unsubscribeFromEvents();
    this.eventCallbacks = [];
  }
}

// Global instance
let authenticatedExtensionService: AuthenticatedExtensionService | null = null;

/**
 * Get the global authenticated extension service instance
 */
export function getAuthenticatedExtensionService(): AuthenticatedExtensionService {
  if (!authenticatedExtensionService) {
    authenticatedExtensionService = new AuthenticatedExtensionService();
  }
  return authenticatedExtensionService;
}

/**
 * Initialize a new authenticated extension service instance
 */
export function initializeAuthenticatedExtensionService(): AuthenticatedExtensionService {
  authenticatedExtensionService = new AuthenticatedExtensionService();
  return authenticatedExtensionService;
}