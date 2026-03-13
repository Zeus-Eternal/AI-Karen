import { 
  CoPilotExtension, 
  ExtensionConfig, 
  ExtensionHealthStatus
} from '../types/extension';
import ExtensionService from './ExtensionService';

type ExtensionLifecycleEventListener = (event: ExtensionLifecycleEvent) => void;
type ExtensionLifecycleEventDetails = Record<string, unknown>;

/**
 * Service for managing the lifecycle of CoPilot extensions
 */
class ExtensionLifecycleService {
  private static instance: ExtensionLifecycleService;
  private extensionService: ExtensionService;
  private lifecycleStates: Map<string, ExtensionLifecycleState> = new Map();
  private lifecycleEventListeners: Map<string, ExtensionLifecycleEventListener[]> = new Map();

  private constructor() {
    this.extensionService = ExtensionService.getInstance();
  }

  public static getInstance(): ExtensionLifecycleService {
    if (!ExtensionLifecycleService.instance) {
      ExtensionLifecycleService.instance = new ExtensionLifecycleService();
    }
    return ExtensionLifecycleService.instance;
  }

  /**
   * Load and initialize an extension
   */
  public async loadExtension(extension: CoPilotExtension, config?: Partial<ExtensionConfig>): Promise<boolean> {
    try {
      console.log(`Loading extension ${extension.id}...`);
      
      // Set lifecycle state to loading
      this.setLifecycleState(extension.id, ExtensionLifecycleState.LOADING);
      
      // Register extension with extension service
      const registered = await this.extensionService.registerExtension(extension, config);
      
      if (!registered) {
        this.setLifecycleState(extension.id, ExtensionLifecycleState.FAILED);
        return false;
      }
      
      // Set lifecycle state to loaded
      this.setLifecycleState(extension.id, ExtensionLifecycleState.LOADED);
      
      // Emit load event
      this.emitLifecycleEvent({
        type: ExtensionLifecycleEventType.LOADED,
        extensionId: extension.id,
        timestamp: new Date(),
        details: { version: extension.version }
      });
      
      console.log(`Extension ${extension.id} loaded successfully`);
      return true;
    } catch (error) {
      console.error(`Failed to load extension ${extension.id}:`, error);
      
      // Set lifecycle state to failed
      this.setLifecycleState(extension.id, ExtensionLifecycleState.FAILED);
      
      // Emit failed event
      this.emitLifecycleEvent({
        type: ExtensionLifecycleEventType.FAILED,
        extensionId: extension.id,
        timestamp: new Date(),
        error: error instanceof Error ? error : new Error(String(error))
      });
      
      return false;
    }
  }

  /**
   * Unload an extension
   */
  public async unloadExtension(extensionId: string): Promise<boolean> {
    try {
      console.log(`Unloading extension ${extensionId}...`);
      
      // Check if extension is loaded
      if (this.getLifecycleState(extensionId) === ExtensionLifecycleState.NOT_LOADED) {
        console.warn(`Extension ${extensionId} is not loaded`);
        return true;
      }
      
      // Set lifecycle state to unloading
      this.setLifecycleState(extensionId, ExtensionLifecycleState.UNLOADING);
      
      // Unregister extension with extension service
      const unregistered = await this.extensionService.unregisterExtension(extensionId);
      
      if (!unregistered) {
        this.setLifecycleState(extensionId, ExtensionLifecycleState.FAILED);
        return false;
      }
      
      // Set lifecycle state to not loaded
      this.setLifecycleState(extensionId, ExtensionLifecycleState.NOT_LOADED);
      
      // Emit unload event
      this.emitLifecycleEvent({
        type: ExtensionLifecycleEventType.UNLOADED,
        extensionId: extensionId,
        timestamp: new Date()
      });
      
      console.log(`Extension ${extensionId} unloaded successfully`);
      return true;
    } catch (error) {
      console.error(`Failed to unload extension ${extensionId}:`, error);
      
      // Set lifecycle state to failed
      this.setLifecycleState(extensionId, ExtensionLifecycleState.FAILED);
      
      // Emit failed event
      this.emitLifecycleEvent({
        type: ExtensionLifecycleEventType.FAILED,
        extensionId: extensionId,
        timestamp: new Date(),
        error: error instanceof Error ? error : new Error(String(error))
      });
      
      return false;
    }
  }

  /**
   * Enable an extension
   */
  public async enableExtension(extensionId: string): Promise<boolean> {
    try {
      console.log(`Enabling extension ${extensionId}...`);
      
      // Set lifecycle state to enabling
      this.setLifecycleState(extensionId, ExtensionLifecycleState.ENABLING);
      
      // Enable extension with extension service
      const enabled = await this.extensionService.setExtensionEnabled(extensionId, true);
      
      if (!enabled) {
        this.setLifecycleState(extensionId, ExtensionLifecycleState.FAILED);
        return false;
      }
      
      // Set lifecycle state to loaded (since it's now enabled)
      this.setLifecycleState(extensionId, ExtensionLifecycleState.LOADED);
      
      // Emit enable event
      this.emitLifecycleEvent({
        type: ExtensionLifecycleEventType.ENABLED,
        extensionId: extensionId,
        timestamp: new Date()
      });
      
      console.log(`Extension ${extensionId} enabled successfully`);
      return true;
    } catch (error) {
      console.error(`Failed to enable extension ${extensionId}:`, error);
      
      // Set lifecycle state to failed
      this.setLifecycleState(extensionId, ExtensionLifecycleState.FAILED);
      
      // Emit failed event
      this.emitLifecycleEvent({
        type: ExtensionLifecycleEventType.FAILED,
        extensionId: extensionId,
        timestamp: new Date(),
        error: error instanceof Error ? error : new Error(String(error))
      });
      
      return false;
    }
  }

  /**
   * Disable an extension
   */
  public async disableExtension(extensionId: string): Promise<boolean> {
    try {
      console.log(`Disabling extension ${extensionId}...`);
      
      // Set lifecycle state to disabling
      this.setLifecycleState(extensionId, ExtensionLifecycleState.DISABLING);
      
      // Disable extension with extension service
      const disabled = await this.extensionService.setExtensionEnabled(extensionId, false);
      
      if (!disabled) {
        this.setLifecycleState(extensionId, ExtensionLifecycleState.FAILED);
        return false;
      }
      
      // Set lifecycle state to disabled
      this.setLifecycleState(extensionId, ExtensionLifecycleState.DISABLED);
      
      // Emit disable event
      this.emitLifecycleEvent({
        type: ExtensionLifecycleEventType.DISABLED,
        extensionId: extensionId,
        timestamp: new Date()
      });
      
      console.log(`Extension ${extensionId} disabled successfully`);
      return true;
    } catch (error) {
      console.error(`Failed to disable extension ${extensionId}:`, error);
      
      // Set lifecycle state to failed
      this.setLifecycleState(extensionId, ExtensionLifecycleState.FAILED);
      
      // Emit failed event
      this.emitLifecycleEvent({
        type: ExtensionLifecycleEventType.FAILED,
        extensionId: extensionId,
        timestamp: new Date(),
        error: error instanceof Error ? error : new Error(String(error))
      });
      
      return false;
    }
  }

  /**
   * Restart an extension
   */
  public async restartExtension(extensionId: string): Promise<boolean> {
    try {
      console.log(`Restarting extension ${extensionId}...`);
      
      // Set lifecycle state to restarting
      this.setLifecycleState(extensionId, ExtensionLifecycleState.RESTARTING);
      
      // Get extension and config before unloading
      const extension = this.extensionService.getExtension(extensionId);
      const config = this.extensionService.getExtensionConfig(extensionId);

      if (!extension) {
        this.setLifecycleState(extensionId, ExtensionLifecycleState.FAILED);
        return false;
      }
      
      // Unload extension
      const unloaded = await this.unloadExtension(extensionId);
      
      if (!unloaded) {
        this.setLifecycleState(extensionId, ExtensionLifecycleState.FAILED);
        return false;
      }
      
      // Load extension again
      const loaded = await this.loadExtension(extension, config);
      
      if (!loaded) {
        this.setLifecycleState(extensionId, ExtensionLifecycleState.FAILED);
        return false;
      }
      
      // Emit restart event
      this.emitLifecycleEvent({
        type: ExtensionLifecycleEventType.RESTARTED,
        extensionId: extensionId,
        timestamp: new Date()
      });
      
      console.log(`Extension ${extensionId} restarted successfully`);
      return true;
    } catch (error) {
      console.error(`Failed to restart extension ${extensionId}:`, error);
      
      // Set lifecycle state to failed
      this.setLifecycleState(extensionId, ExtensionLifecycleState.FAILED);
      
      // Emit failed event
      this.emitLifecycleEvent({
        type: ExtensionLifecycleEventType.FAILED,
        extensionId: extensionId,
        timestamp: new Date(),
        error: error instanceof Error ? error : new Error(String(error))
      });
      
      return false;
    }
  }

  /**
   * Update an extension
   */
  public async updateExtension(extensionId: string, newExtension: CoPilotExtension): Promise<boolean> {
    try {
      console.log(`Updating extension ${extensionId}...`);
      
      // Set lifecycle state to updating
      this.setLifecycleState(extensionId, ExtensionLifecycleState.UPDATING);
      
      // Get current extension config
      const config = this.extensionService.getExtensionConfig(extensionId);
      
      // Unload current extension
      const unloaded = await this.unloadExtension(extensionId);
      
      if (!unloaded) {
        this.setLifecycleState(extensionId, ExtensionLifecycleState.FAILED);
        return false;
      }
      
      // Load new extension
      const loaded = await this.loadExtension(newExtension, config);
      
      if (!loaded) {
        this.setLifecycleState(extensionId, ExtensionLifecycleState.FAILED);
        return false;
      }
      
      // Emit update event
      this.emitLifecycleEvent({
        type: ExtensionLifecycleEventType.UPDATED,
        extensionId: extensionId,
        timestamp: new Date(),
        details: { 
          oldVersion: this.extensionService.getExtension(extensionId)?.version,
          newVersion: newExtension.version 
        }
      });
      
      console.log(`Extension ${extensionId} updated successfully`);
      return true;
    } catch (error) {
      console.error(`Failed to update extension ${extensionId}:`, error);
      
      // Set lifecycle state to failed
      this.setLifecycleState(extensionId, ExtensionLifecycleState.FAILED);
      
      // Emit failed event
      this.emitLifecycleEvent({
        type: ExtensionLifecycleEventType.FAILED,
        extensionId: extensionId,
        timestamp: new Date(),
        error: error instanceof Error ? error : new Error(String(error))
      });
      
      return false;
    }
  }

  /**
   * Get lifecycle state of an extension
   */
  public getLifecycleState(extensionId: string): ExtensionLifecycleState {
    return this.lifecycleStates.get(extensionId) || ExtensionLifecycleState.NOT_LOADED;
  }

  /**
   * Get lifecycle states of all extensions
   */
  public getAllLifecycleStates(): Map<string, ExtensionLifecycleState> {
    return new Map(this.lifecycleStates);
  }

  /**
   * Add lifecycle event listener
   */
  public addLifecycleEventListener(
    eventType: ExtensionLifecycleEventType, 
    listener: (event: ExtensionLifecycleEvent) => void
  ): void {
    if (!this.lifecycleEventListeners.has(eventType)) {
      this.lifecycleEventListeners.set(eventType, []);
    }
    this.lifecycleEventListeners.get(eventType)?.push(listener);
  }

  /**
   * Remove lifecycle event listener
   */
  public removeLifecycleEventListener(
    eventType: ExtensionLifecycleEventType, 
    listener: (event: ExtensionLifecycleEvent) => void
  ): void {
    const listeners = this.lifecycleEventListeners.get(eventType);
    if (listeners) {
      const index = listeners.indexOf(listener);
      if (index !== -1) {
        listeners.splice(index, 1);
      }
    }
  }

  /**
   * Set lifecycle state for an extension
   */
  private setLifecycleState(extensionId: string, state: ExtensionLifecycleState): void {
    this.lifecycleStates.set(extensionId, state);
    
    // Emit state change event
    this.emitLifecycleEvent({
      type: ExtensionLifecycleEventType.STATE_CHANGED,
      extensionId,
      timestamp: new Date(),
      details: { state }
    });
  }

  /**
   * Emit lifecycle event
   */
  private emitLifecycleEvent(event: ExtensionLifecycleEvent): void {
    const listeners = this.lifecycleEventListeners.get(event.type);
    if (listeners) {
      listeners.forEach(listener => {
        try {
          listener(event);
        } catch (error) {
          console.error(`Error in lifecycle event listener for ${event.type}:`, error);
        }
      });
    }
  }

  /**
   * Perform health check on all extensions
   */
  public async performHealthCheck(): Promise<Map<string, ExtensionHealthStatus>> {
    const results = new Map<string, ExtensionHealthStatus>();
    
    for (const [extensionId, state] of this.lifecycleStates) {
      try {
        // Skip health check for extensions that are not loaded
        if (state === ExtensionLifecycleState.NOT_LOADED || 
            state === ExtensionLifecycleState.FAILED ||
            state === ExtensionLifecycleState.UNLOADING) {
          continue;
        }
        
        const status = this.extensionService.getExtensionStatus(extensionId);
        
        if (status) {
          // Simple health check based on metrics
          if (status.metrics.errorCount > status.metrics.successCount) {
            status.health = ExtensionHealthStatus.ERROR;
          } else if (status.metrics.errorCount > 0) {
            status.health = ExtensionHealthStatus.WARNING;
          } else {
            status.health = ExtensionHealthStatus.HEALTHY;
          }
          
          results.set(extensionId, status.health);
        }
      } catch (error) {
        console.error(`Health check failed for extension ${extensionId}:`, error);
        results.set(extensionId, ExtensionHealthStatus.ERROR);
      }
    }
    
    return results;
  }
}

/**
 * Extension lifecycle states
 */
export enum ExtensionLifecycleState {
  /** Extension is not loaded */
  NOT_LOADED = 'not_loaded',
  
  /** Extension is being loaded */
  LOADING = 'loading',
  
  /** Extension is loaded and enabled */
  LOADED = 'loaded',
  
  /** Extension is being unloaded */
  UNLOADING = 'unloading',
  
  /** Extension is being enabled */
  ENABLING = 'enabling',
  
  /** Extension is being disabled */
  DISABLING = 'disabling',
  
  /** Extension is disabled */
  DISABLED = 'disabled',
  
  /** Extension is being restarted */
  RESTARTING = 'restarting',
  
  /** Extension is being updated */
  UPDATING = 'updating',
  
  /** Extension operation failed */
  FAILED = 'failed'
}

/**
 * Extension lifecycle event types
 */
export enum ExtensionLifecycleEventType {
  /** Extension was loaded */
  LOADED = 'loaded',
  
  /** Extension was unloaded */
  UNLOADED = 'unloaded',
  
  /** Extension was enabled */
  ENABLED = 'enabled',
  
  /** Extension was disabled */
  DISABLED = 'disabled',
  
  /** Extension was restarted */
  RESTARTED = 'restarted',
  
  /** Extension was updated */
  UPDATED = 'updated',
  
  /** Extension operation failed */
  FAILED = 'failed',
  
  /** Extension state changed */
  STATE_CHANGED = 'state_changed'
}

/**
 * Extension lifecycle event
 */
export interface ExtensionLifecycleEvent {
  /** Event type */
  type: ExtensionLifecycleEventType;
  
  /** Extension ID */
  extensionId: string;
  
  /** Event timestamp */
  timestamp: Date;
  
  /** Event details if any */
  details?: ExtensionLifecycleEventDetails;
  
  /** Error if any */
  error?: Error;
}

export default ExtensionLifecycleService;
