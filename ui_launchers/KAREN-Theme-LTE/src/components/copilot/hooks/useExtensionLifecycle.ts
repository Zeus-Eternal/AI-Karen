import { useState, useEffect, useCallback, useRef } from 'react';
import {
  CoPilotExtension,
  ExtensionConfig,
  ExtensionHealthStatus
} from '../types/extension';
import ExtensionLifecycleService, {
  ExtensionLifecycleState,
  ExtensionLifecycleEventType,
  ExtensionLifecycleEvent
} from '../services/ExtensionLifecycleService';

interface UseExtensionLifecycleOptions {
  /** Auto-initialize lifecycle service */
  autoInitialize?: boolean;
  
  /** Extensions to load automatically */
  extensions?: CoPilotExtension[];
  
  /** Configuration for extensions */
  configs?: Record<string, Partial<ExtensionConfig>>;
}

interface UseExtensionLifecycleResult {
  /** Lifecycle service instance */
  lifecycleService: ExtensionLifecycleService;
  
  /** Lifecycle states for all extensions */
  lifecycleStates: Map<string, ExtensionLifecycleState>;
  
  /** Loading state */
  isLoading: boolean;
  
  /** Error state */
  error: string | null;
  
  /** Load an extension */
  loadExtension: (extension: CoPilotExtension, config?: Partial<ExtensionConfig>) => Promise<boolean>;
  
  /** Unload an extension */
  unloadExtension: (extensionId: string) => Promise<boolean>;
  
  /** Enable an extension */
  enableExtension: (extensionId: string) => Promise<boolean>;
  
  /** Disable an extension */
  disableExtension: (extensionId: string) => Promise<boolean>;
  
  /** Restart an extension */
  restartExtension: (extensionId: string) => Promise<boolean>;
  
  /** Update an extension */
  updateExtension: (extensionId: string, newExtension: CoPilotExtension) => Promise<boolean>;
  
  /** Get lifecycle state for an extension */
  getLifecycleState: (extensionId: string) => ExtensionLifecycleState;
  
  /** Get all lifecycle states */
  getAllLifecycleStates: () => Map<string, ExtensionLifecycleState>;
  
  /** Add lifecycle event listener */
  addLifecycleEventListener: (
    eventType: ExtensionLifecycleEventType, 
    listener: (event: ExtensionLifecycleEvent) => void
  ) => void;
  
  /** Remove lifecycle event listener */
  removeLifecycleEventListener: (
    eventType: ExtensionLifecycleEventType, 
    listener: (event: ExtensionLifecycleEvent) => void
  ) => void;
  
  /** Perform health check on all extensions */
  performHealthCheck: () => Promise<Map<string, ExtensionHealthStatus>>;
}

/**
 * React hook for managing CoPilot extension lifecycle
 */
export const useExtensionLifecycle = (options: UseExtensionLifecycleOptions = {}): UseExtensionLifecycleResult => {
  const {
    autoInitialize = true,
    extensions = [],
    configs = {}
  } = options;
  
  // State
  const [lifecycleService] = useState(() => ExtensionLifecycleService.getInstance());
  const [lifecycleStates, setLifecycleStates] = useState<Map<string, ExtensionLifecycleState>>(new Map());
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Refs
  const isMountedRef = useRef(true);
  const eventListenersRef = useRef<Map<ExtensionLifecycleEventType, Function[]>>(new Map());
  
  // Initialize extensions
  const initializeExtensions = useCallback(async () => {
    if (!autoInitialize) {
      setIsLoading(false);
      return;
    }
    
    try {
      setIsLoading(true);
      setError(null);
      
      // Load provided extensions
      const loadPromises = extensions.map(async (extension) => {
        try {
          const config = configs[extension.id];
          const success = await lifecycleService.loadExtension(extension, config);
          if (!success) {
            console.warn(`Failed to load extension ${extension.id}`);
          }
          return success;
        } catch (err) {
          console.error(`Error loading extension ${extension.id}:`, err);
          return false;
        }
      });
      
      await Promise.all(loadPromises);
      
      // Update state
      if (isMountedRef.current) {
        setLifecycleStates(new Map(lifecycleService.getAllLifecycleStates()));
      }
    } catch (err) {
      console.error('Failed to initialize extensions:', err);
      if (isMountedRef.current) {
        setError('Failed to initialize extensions');
      }
    } finally {
      if (isMountedRef.current) {
        setIsLoading(false);
      }
    }
  }, [autoInitialize, extensions, configs, lifecycleService]);
  
  // Initialize on mount
  useEffect(() => {
    initializeExtensions();
    
    // Set up event listeners to update state
    const handleStateChange = (event: ExtensionLifecycleEvent) => {
      if (isMountedRef.current) {
        setLifecycleStates(new Map(lifecycleService.getAllLifecycleStates()));
      }
    };
    
    lifecycleService.addLifecycleEventListener(
      ExtensionLifecycleEventType.STATE_CHANGED, 
      handleStateChange
    );
    lifecycleService.addLifecycleEventListener(
      ExtensionLifecycleEventType.LOADED, 
      handleStateChange
    );
    lifecycleService.addLifecycleEventListener(
      ExtensionLifecycleEventType.UNLOADED, 
      handleStateChange
    );
    lifecycleService.addLifecycleEventListener(
      ExtensionLifecycleEventType.ENABLED, 
      handleStateChange
    );
    lifecycleService.addLifecycleEventListener(
      ExtensionLifecycleEventType.DISABLED, 
      handleStateChange
    );
    lifecycleService.addLifecycleEventListener(
      ExtensionLifecycleEventType.RESTARTED, 
      handleStateChange
    );
    lifecycleService.addLifecycleEventListener(
      ExtensionLifecycleEventType.UPDATED, 
      handleStateChange
    );
    lifecycleService.addLifecycleEventListener(
      ExtensionLifecycleEventType.FAILED, 
      handleStateChange
    );
    
    return () => {
      isMountedRef.current = false;
      
      // Clean up event listeners
      lifecycleService.removeLifecycleEventListener(
        ExtensionLifecycleEventType.STATE_CHANGED, 
        handleStateChange
      );
      lifecycleService.removeLifecycleEventListener(
        ExtensionLifecycleEventType.LOADED, 
        handleStateChange
      );
      lifecycleService.removeLifecycleEventListener(
        ExtensionLifecycleEventType.UNLOADED, 
        handleStateChange
      );
      lifecycleService.removeLifecycleEventListener(
        ExtensionLifecycleEventType.ENABLED, 
        handleStateChange
      );
      lifecycleService.removeLifecycleEventListener(
        ExtensionLifecycleEventType.DISABLED, 
        handleStateChange
      );
      lifecycleService.removeLifecycleEventListener(
        ExtensionLifecycleEventType.RESTARTED, 
        handleStateChange
      );
      lifecycleService.removeLifecycleEventListener(
        ExtensionLifecycleEventType.UPDATED, 
        handleStateChange
      );
      lifecycleService.removeLifecycleEventListener(
        ExtensionLifecycleEventType.FAILED, 
        handleStateChange
      );
    };
  }, [initializeExtensions, lifecycleService]);
  
  // Load an extension
  const loadExtension = useCallback(async (
    extension: CoPilotExtension, 
    config?: Partial<ExtensionConfig>
  ): Promise<boolean> => {
    try {
      const success = await lifecycleService.loadExtension(extension, config);
      
      if (success && isMountedRef.current) {
        setLifecycleStates(new Map(lifecycleService.getAllLifecycleStates()));
      }
      
      return success;
    } catch (err) {
      console.error(`Failed to load extension ${extension.id}:`, err);
      if (isMountedRef.current) {
        setError(`Failed to load extension ${extension.id}`);
      }
      return false;
    }
  }, [lifecycleService]);
  
  // Unload an extension
  const unloadExtension = useCallback(async (
    extensionId: string
  ): Promise<boolean> => {
    try {
      const success = await lifecycleService.unloadExtension(extensionId);
      
      if (success && isMountedRef.current) {
        setLifecycleStates(new Map(lifecycleService.getAllLifecycleStates()));
      }
      
      return success;
    } catch (err) {
      console.error(`Failed to unload extension ${extensionId}:`, err);
      if (isMountedRef.current) {
        setError(`Failed to unload extension ${extensionId}`);
      }
      return false;
    }
  }, [lifecycleService]);
  
  // Enable an extension
  const enableExtension = useCallback(async (
    extensionId: string
  ): Promise<boolean> => {
    try {
      const success = await lifecycleService.enableExtension(extensionId);
      
      if (success && isMountedRef.current) {
        setLifecycleStates(new Map(lifecycleService.getAllLifecycleStates()));
      }
      
      return success;
    } catch (err) {
      console.error(`Failed to enable extension ${extensionId}:`, err);
      if (isMountedRef.current) {
        setError(`Failed to enable extension ${extensionId}`);
      }
      return false;
    }
  }, [lifecycleService]);
  
  // Disable an extension
  const disableExtension = useCallback(async (
    extensionId: string
  ): Promise<boolean> => {
    try {
      const success = await lifecycleService.disableExtension(extensionId);
      
      if (success && isMountedRef.current) {
        setLifecycleStates(new Map(lifecycleService.getAllLifecycleStates()));
      }
      
      return success;
    } catch (err) {
      console.error(`Failed to disable extension ${extensionId}:`, err);
      if (isMountedRef.current) {
        setError(`Failed to disable extension ${extensionId}`);
      }
      return false;
    }
  }, [lifecycleService]);
  
  // Restart an extension
  const restartExtension = useCallback(async (
    extensionId: string
  ): Promise<boolean> => {
    try {
      const success = await lifecycleService.restartExtension(extensionId);
      
      if (success && isMountedRef.current) {
        setLifecycleStates(new Map(lifecycleService.getAllLifecycleStates()));
      }
      
      return success;
    } catch (err) {
      console.error(`Failed to restart extension ${extensionId}:`, err);
      if (isMountedRef.current) {
        setError(`Failed to restart extension ${extensionId}`);
      }
      return false;
    }
  }, [lifecycleService]);
  
  // Update an extension
  const updateExtension = useCallback(async (
    extensionId: string, 
    newExtension: CoPilotExtension
  ): Promise<boolean> => {
    try {
      const success = await lifecycleService.updateExtension(extensionId, newExtension);
      
      if (success && isMountedRef.current) {
        setLifecycleStates(new Map(lifecycleService.getAllLifecycleStates()));
      }
      
      return success;
    } catch (err) {
      console.error(`Failed to update extension ${extensionId}:`, err);
      if (isMountedRef.current) {
        setError(`Failed to update extension ${extensionId}`);
      }
      return false;
    }
  }, [lifecycleService]);
  
  // Get lifecycle state for an extension
  const getLifecycleState = useCallback((extensionId: string): ExtensionLifecycleState => {
    return lifecycleService.getLifecycleState(extensionId);
  }, [lifecycleService]);
  
  // Get all lifecycle states
  const getAllLifecycleStates = useCallback((): Map<string, ExtensionLifecycleState> => {
    return new Map(lifecycleService.getAllLifecycleStates());
  }, [lifecycleService]);
  
  // Add lifecycle event listener
  const addLifecycleEventListener = useCallback((
    eventType: ExtensionLifecycleEventType, 
    listener: (event: ExtensionLifecycleEvent) => void
  ): void => {
    lifecycleService.addLifecycleEventListener(eventType, listener);
    
    // Track for cleanup
    if (!eventListenersRef.current.has(eventType)) {
      eventListenersRef.current.set(eventType, []);
    }
    eventListenersRef.current.get(eventType)?.push(listener);
  }, [lifecycleService]);
  
  // Remove lifecycle event listener
  const removeLifecycleEventListener = useCallback((
    eventType: ExtensionLifecycleEventType, 
    listener: (event: ExtensionLifecycleEvent) => void
  ): void => {
    lifecycleService.removeLifecycleEventListener(eventType, listener);
    
    // Remove from tracking
    const listeners = eventListenersRef.current.get(eventType);
    if (listeners) {
      const index = listeners.indexOf(listener);
      if (index !== -1) {
        listeners.splice(index, 1);
      }
    }
  }, [lifecycleService]);
  
  // Perform health check on all extensions
  const performHealthCheck = useCallback(async (): Promise<Map<string, ExtensionHealthStatus>> => {
    try {
      return await lifecycleService.performHealthCheck();
    } catch (err) {
      console.error('Failed to perform health check:', err);
      if (isMountedRef.current) {
        setError('Failed to perform health check');
      }
      return new Map();
    }
  }, [lifecycleService]);
  
  return {
    lifecycleService,
    lifecycleStates,
    isLoading,
    error,
    loadExtension,
    unloadExtension,
    enableExtension,
    disableExtension,
    restartExtension,
    updateExtension,
    getLifecycleState,
    getAllLifecycleStates,
    addLifecycleEventListener,
    removeLifecycleEventListener,
    performHealthCheck
  };
};

export default useExtensionLifecycle;