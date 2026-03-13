import {
  CoPilotExtension,
  ExtensionContext,
  ExtensionConfig,
  ExtensionRequest,
  ExtensionResponse,
  ExtensionStatus,
  ExtensionLogger,
  ExtensionEvent,
  ExtensionEventType,
  ExtensionUIComponent,
  ExtensionHook,
  ExtensionContextProvider,
  ExtensionHealthStatus,
  ExtensionErrorCode,
  ExtensionRequestType,
  ExtensionResponseStatus
} from '../types/extension';

type ExtensionEventListener = (event: ExtensionEvent) => void;

interface ExtensionContextServices {
  agentService?: Record<string, unknown>;
  uiService?: Record<string, unknown>;
  themeService?: Record<string, unknown>;
  memoryService?: Record<string, unknown>;
  conversationService?: Record<string, unknown>;
  taskService?: Record<string, unknown>;
  voiceService?: Record<string, unknown>;
}

/**
 * Service for managing CoPilot extensions
 */
class ExtensionService {
  private static instance: ExtensionService;
  private extensions: Map<string, CoPilotExtension> = new Map();
  private extensionStatus: Map<string, ExtensionStatus> = new Map();
  private extensionConfigs: Map<string, ExtensionConfig> = new Map();
  private eventListeners: Map<string, ExtensionEventListener[]> = new Map();
  private uiComponents: Map<string, ExtensionUIComponent[]> = new Map();
  private hooks: Map<string, ExtensionHook[]> = new Map();
  private contextProviders: Map<string, ExtensionContextProvider[]> = new Map();

  private constructor() {
    // Initialize with empty state
  }

  public static getInstance(): ExtensionService {
    if (!ExtensionService.instance) {
      ExtensionService.instance = new ExtensionService();
    }
    return ExtensionService.instance;
  }

  /**
   * Register a new extension
   */
  public async registerExtension(extension: CoPilotExtension, config?: Partial<ExtensionConfig>): Promise<boolean> {
    try {
      if (this.extensions.has(extension.id)) {
        console.warn(`Extension ${extension.id} is already registered`);
        return false;
      }

      // Create default config if not provided
      const defaultConfig: ExtensionConfig = {
        settings: {},
        global: {},
        userPreferences: {},
        tenant: {}
      };

      const finalConfig = { ...defaultConfig, ...config };
      this.extensionConfigs.set(extension.id, finalConfig);

      // Create initial status
      const initialStatus: ExtensionStatus = {
        enabled: true,
        initialized: false,
        health: ExtensionHealthStatus.WARNING,
        metrics: {
          requestCount: 0,
          successCount: 0,
          errorCount: 0,
          averageResponseTime: 0
        }
      };
      this.extensionStatus.set(extension.id, initialStatus);

      // Store extension
      this.extensions.set(extension.id, extension);

      // Initialize extension
      await this.initializeExtension(extension.id);

      // Emit extension loaded event
      this.emitEvent({
        type: ExtensionEventType.EXTENSION_LOADED,
        id: this.generateId(),
        source: 'ExtensionService',
        payload: { extensionId: extension.id },
        timestamp: new Date()
      });

      console.log(`Extension ${extension.id} registered successfully`);
      return true;
    } catch (error) {
      console.error(`Failed to register extension ${extension.id}:`, error);
      return false;
    }
  }

  /**
   * Unregister an extension
   */
  public async unregisterExtension(extensionId: string): Promise<boolean> {
    try {
      const extension = this.extensions.get(extensionId);
      if (!extension) {
        console.warn(`Extension ${extensionId} is not registered`);
        return false;
      }

      // Cleanup extension if initialized
      const status = this.extensionStatus.get(extensionId);
      if (status?.initialized && extension.cleanup) {
        await extension.cleanup();
      }

      // Remove from all maps
      this.extensions.delete(extensionId);
      this.extensionStatus.delete(extensionId);
      this.extensionConfigs.delete(extensionId);
      this.uiComponents.delete(extensionId);
      this.hooks.delete(extensionId);
      this.contextProviders.delete(extensionId);

      // Emit extension unloaded event
      this.emitEvent({
        type: ExtensionEventType.EXTENSION_UNLOADED,
        id: this.generateId(),
        source: 'ExtensionService',
        payload: { extensionId },
        timestamp: new Date()
      });

      console.log(`Extension ${extensionId} unregistered successfully`);
      return true;
    } catch (error) {
      console.error(`Failed to unregister extension ${extensionId}:`, error);
      return false;
    }
  }

  /**
   * Initialize an extension
   */
  private async initializeExtension(extensionId: string): Promise<void> {
    try {
      const extension = this.extensions.get(extensionId);
      const config = this.extensionConfigs.get(extensionId);
      const status = this.extensionStatus.get(extensionId);

      if (!extension || !config || !status) {
        throw new Error(`Extension ${extensionId} not found`);
      }

      // Create extension context
      const context: ExtensionContext = {
        agentService: {}, // Will be injected
        uiService: {},    // Will be injected
        themeService: {}, // Will be injected
        memoryService: {}, // Will be injected
        conversationService: {}, // Will be injected
        taskService: {}, // Will be injected
        voiceService: {}, // Will be injected
        config,
        logger: this.createExtensionLogger(extensionId)
      };

      // Initialize extension
      await extension.initialize(context);

      // Update status
      status.initialized = true;
      status.health = ExtensionHealthStatus.HEALTHY;
      this.extensionStatus.set(extensionId, status);

      console.log(`Extension ${extensionId} initialized successfully`);
    } catch (error) {
      console.error(`Failed to initialize extension ${extensionId}:`, error);
      
      // Update status with error
      const status = this.extensionStatus.get(extensionId);
      if (status) {
        status.initialized = false;
        status.health = ExtensionHealthStatus.ERROR;
        status.lastError = {
          code: ExtensionErrorCode.EXECUTION_ERROR,
          message: error instanceof Error ? error.message : String(error),
          stack: error instanceof Error ? error.stack : undefined
        };
        this.extensionStatus.set(extensionId, status);
      }
    }
  }

  /**
   * Execute an extension request
   */
  public async executeExtensionRequest(
    extensionId: string, 
    request: Omit<ExtensionRequest, 'id'>
  ): Promise<ExtensionResponse> {
    try {
      const extension = this.extensions.get(extensionId);
      const status = this.extensionStatus.get(extensionId);

      if (!extension) {
        return {
          id: this.generateId(),
          status: ExtensionResponseStatus.ERROR,
          error: {
            code: ExtensionErrorCode.NOT_FOUND,
            message: `Extension ${extensionId} not found`
          }
        };
      }

      if (!status?.enabled) {
        return {
          id: this.generateId(),
          status: ExtensionResponseStatus.ERROR,
          error: {
            code: ExtensionErrorCode.GENERAL_ERROR,
            message: `Extension ${extensionId} is disabled`
          }
        };
      }

      if (!status?.initialized) {
        return {
          id: this.generateId(),
          status: ExtensionResponseStatus.ERROR,
          error: {
            code: ExtensionErrorCode.GENERAL_ERROR,
            message: `Extension ${extensionId} is not initialized`
          }
        };
      }

      // Create full request with ID
      const fullRequest: ExtensionRequest = {
        ...request,
        id: this.generateId()
      };

      // Record start time
      const startTime = Date.now();

      // Execute extension
      const response = await extension.execute(fullRequest);

      // Update metrics
      if (status) {
        status.metrics.requestCount++;
        status.metrics.lastExecution = new Date();
        
        const executionTime = Date.now() - startTime;
        status.metrics.averageResponseTime = 
          (status.metrics.averageResponseTime * (status.metrics.requestCount - 1) + executionTime) / 
          status.metrics.requestCount;

        if (response.status === ExtensionResponseStatus.SUCCESS) {
          status.metrics.successCount++;
        } else {
          status.metrics.errorCount++;
        }

        this.extensionStatus.set(extensionId, status);
      }

      return response;
    } catch (error) {
      console.error(`Failed to execute request on extension ${extensionId}:`, error);
      
      // Update status with error
      const status = this.extensionStatus.get(extensionId);
      if (status) {
        status.metrics.errorCount++;
        status.lastError = {
          code: ExtensionErrorCode.EXECUTION_ERROR,
          message: error instanceof Error ? error.message : String(error),
          stack: error instanceof Error ? error.stack : undefined
        };
        this.extensionStatus.set(extensionId, status);
      }

      return {
        id: this.generateId(),
        status: ExtensionResponseStatus.ERROR,
        error: {
          code: ExtensionErrorCode.EXECUTION_ERROR,
          message: error instanceof Error ? error.message : String(error)
        }
      };
    }
  }

  /**
   * Get all registered extensions
   */
  public getExtensions(): CoPilotExtension[] {
    return Array.from(this.extensions.values());
  }

  /**
   * Get an extension by ID
   */
  public getExtension(extensionId: string): CoPilotExtension | undefined {
    return this.extensions.get(extensionId);
  }

  /**
   * Get extension status
   */
  public getExtensionStatus(extensionId: string): ExtensionStatus | undefined {
    return this.extensionStatus.get(extensionId);
  }

  /**
   * Get extension configuration
   */
  public getExtensionConfig(extensionId: string): ExtensionConfig | undefined {
    return this.extensionConfigs.get(extensionId);
  }

  /**
   * Update extension configuration
   */
  public async updateExtensionConfig(
    extensionId: string, 
    config: Partial<ExtensionConfig>
  ): Promise<boolean> {
    try {
      const currentConfig = this.extensionConfigs.get(extensionId);
      if (!currentConfig) {
        return false;
      }

      const updatedConfig = { ...currentConfig, ...config };
      this.extensionConfigs.set(extensionId, updatedConfig);

      // Notify extension of config update
      const request: Omit<ExtensionRequest, 'id'> = {
        type: ExtensionRequestType.UPDATE_CONFIG,
        payload: { config: updatedConfig },
        metadata: {},
        userContext: {
          userId: '',
          roles: [],
          permissions: [],
          preferences: {}
        },
        sessionContext: {
          sessionId: ''
        }
      };

      await this.executeExtensionRequest(extensionId, request);
      return true;
    } catch (error) {
      console.error(`Failed to update config for extension ${extensionId}:`, error);
      return false;
    }
  }

  /**
   * Enable or disable an extension
   */
  public async setExtensionEnabled(extensionId: string, enabled: boolean): Promise<boolean> {
    try {
      const status = this.extensionStatus.get(extensionId);
      if (!status) {
        return false;
      }

      status.enabled = enabled;
      this.extensionStatus.set(extensionId, status);

      if (!enabled && status.initialized) {
        const extension = this.extensions.get(extensionId);
        if (extension?.cleanup) {
          await extension.cleanup();
        }
        status.initialized = false;
        this.extensionStatus.set(extensionId, status);
      } else if (enabled && !status.initialized) {
        await this.initializeExtension(extensionId);
      }

      return true;
    } catch (error) {
      console.error(`Failed to set enabled state for extension ${extensionId}:`, error);
      return false;
    }
  }

  /**
   * Add an event listener
   */
  public addEventListener(eventType: string, listener: ExtensionEventListener): void {
    if (!this.eventListeners.has(eventType)) {
      this.eventListeners.set(eventType, []);
    }
    this.eventListeners.get(eventType)?.push(listener);
  }

  /**
   * Remove an event listener
   */
  public removeEventListener(eventType: string, listener: ExtensionEventListener): void {
    const listeners = this.eventListeners.get(eventType);
    if (listeners) {
      const index = listeners.indexOf(listener);
      if (index !== -1) {
        listeners.splice(index, 1);
      }
    }
  }

  /**
   * Emit an event
   */
  private emitEvent(event: ExtensionEvent): void {
    const listeners = this.eventListeners.get(event.type);
    if (listeners) {
      listeners.forEach(listener => {
        try {
          listener(event);
        } catch (error) {
          console.error(`Error in event listener for ${event.type}:`, error);
        }
      });
    }
  }

  /**
   * Register a UI component
   */
  public registerUIComponent(extensionId: string, component: ExtensionUIComponent): void {
    if (!this.uiComponents.has(extensionId)) {
      this.uiComponents.set(extensionId, []);
    }
    this.uiComponents.get(extensionId)?.push(component);
  }

  /**
   * Get UI components for an extension
   */
  public getUIComponents(extensionId: string): ExtensionUIComponent[] {
    return this.uiComponents.get(extensionId) || [];
  }

  /**
   * Get all UI components
   */
  public getAllUIComponents(): ExtensionUIComponent[] {
    const components: ExtensionUIComponent[] = [];
    for (const extensionComponents of this.uiComponents.values()) {
      components.push(...extensionComponents);
    }
    return components;
  }

  /**
   * Register a hook
   */
  public registerHook(extensionId: string, hook: ExtensionHook): void {
    if (!this.hooks.has(extensionId)) {
      this.hooks.set(extensionId, []);
    }
    this.hooks.get(extensionId)?.push(hook);
  }

  /**
   * Get hooks for an extension
   */
  public getHooks(extensionId: string): ExtensionHook[] {
    return this.hooks.get(extensionId) || [];
  }

  /**
   * Register a context provider
   */
  public registerContextProvider(extensionId: string, provider: ExtensionContextProvider): void {
    if (!this.contextProviders.has(extensionId)) {
      this.contextProviders.set(extensionId, []);
    }
    this.contextProviders.get(extensionId)?.push(provider);
  }

  /**
   * Get context providers for an extension
   */
  public getContextProviders(extensionId: string): ExtensionContextProvider[] {
    return this.contextProviders.get(extensionId) || [];
  }

  /**
   * Create a logger for an extension
   */
  private createExtensionLogger(extensionId: string): ExtensionLogger {
    return {
      debug: (message: string, ...args: unknown[]) => {
        console.debug(`[${extensionId}] DEBUG:`, message, ...args);
      },
      info: (message: string, ...args: unknown[]) => {
        console.info(`[${extensionId}] INFO:`, message, ...args);
      },
      warn: (message: string, ...args: unknown[]) => {
        console.warn(`[${extensionId}] WARN:`, message, ...args);
      },
      error: (message: string, ...args: unknown[]) => {
        console.error(`[${extensionId}] ERROR:`, message, ...args);
      }
    };
  }

  /**
   * Generate a unique ID
   */
  private generateId(): string {
    return `ext_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Inject services into extension context
   */
  public injectServices(
    extensionId: string,
    services: ExtensionContextServices
  ): void {
    const config = this.extensionConfigs.get(extensionId);
    if (!config) {
      return;
    }

    void services;

    // Update the context in the config
    // Note: In a real implementation, we would need to update the actual context
    // that was passed to the extension during initialization
    console.log(`Services injected for extension ${extensionId}`);
  }
}

export default ExtensionService;
