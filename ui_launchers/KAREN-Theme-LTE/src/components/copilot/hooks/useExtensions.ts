import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  CoPilotExtension,
  ExtensionRequest,
  ExtensionResponse,
  ExtensionStatus,
  ExtensionEvent,
  ExtensionEventType,
  ExtensionUIComponent,
  ExtensionHook,
  ExtensionContextProvider,
  ExtensionResponseStatus,
  ExtensionErrorCode
} from '../types/extension';
import ExtensionService from '../services/ExtensionService';

interface UseExtensionsOptions {
  /** Auto-initialize extension service */
  autoInitialize?: boolean;
  
  /** Extensions to load automatically */
  extensions?: CoPilotExtension[];
}

interface UseExtensionsResult {
  /** Extension service instance */
  extensionService: ExtensionService;
  
  /** List of registered extensions */
  extensions: CoPilotExtension[];
  
  /** Extension status map */
  extensionStatus: Map<string, ExtensionStatus>;
  
  /** Loading state */
  isLoading: boolean;
  
  /** Error state */
  error: string | null;
  
  /** Register an extension */
  registerExtension: (extension: CoPilotExtension, config?: any) => Promise<boolean>;
  
  /** Unregister an extension */
  unregisterExtension: (extensionId: string) => Promise<boolean>;
  
  /** Execute an extension request */
  executeExtension: (extensionId: string, request: Omit<ExtensionRequest, 'id'>) => Promise<ExtensionResponse>;
  
  /** Get extension by ID */
  getExtension: (extensionId: string) => CoPilotExtension | undefined;
  
  /** Get extension status */
  getExtensionStatus: (extensionId: string) => ExtensionStatus | undefined;
  
  /** Get UI components for an extension */
  getExtensionUIComponents: (extensionId: string) => ExtensionUIComponent[];
  
  /** Get all UI components */
  getAllUIComponents: () => ExtensionUIComponent[];
  
  /** Get hooks for an extension */
  getExtensionHooks: (extensionId: string) => ExtensionHook[];
  
  /** Get context providers for an extension */
  getExtensionContextProviders: (extensionId: string) => ExtensionContextProvider[];
  
  /** Add event listener */
  addEventListener: (eventType: ExtensionEventType, listener: (event: ExtensionEvent) => void) => void;
  
  /** Remove event listener */
  removeEventListener: (eventType: ExtensionEventType, listener: (event: ExtensionEvent) => void) => void;
  
  /** Enable or disable an extension */
  setExtensionEnabled: (extensionId: string, enabled: boolean) => Promise<boolean>;
  
  /** Update extension configuration */
  updateExtensionConfig: (extensionId: string, config: any) => Promise<boolean>;
}

/**
 * React hook for managing CoPilot extensions
 */
export const useExtensions = (options: UseExtensionsOptions = {}): UseExtensionsResult => {
  const {
    autoInitialize = true,
    extensions = []
  } = options;
  
  // State
  const [extensionService] = useState(() => ExtensionService.getInstance());
  const [extensionsList, setExtensionsList] = useState<CoPilotExtension[]>([]);
  const [extensionStatusMap, setExtensionStatusMap] = useState<Map<string, ExtensionStatus>>(new Map());
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Refs
  const isMountedRef = useRef(true);
  const eventListenersRef = useRef<Map<ExtensionEventType, Function[]>>(new Map());
  
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
          const success = await extensionService.registerExtension(extension);
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
        setExtensionsList(extensionService.getExtensions());
        setExtensionStatusMap(new Map(
          extensionsList.map(ext => [ext.id, extensionService.getExtensionStatus(ext.id)!])
            .filter(([_, status]) => status !== undefined) as [string, ExtensionStatus][]
        ));
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
  }, [autoInitialize, extensions, extensionService, extensionsList]);
  
  // Initialize on mount
  useEffect(() => {
    initializeExtensions();
    
    // Set up event listeners to update state
    const handleExtensionLoaded = (event: ExtensionEvent) => {
      if (isMountedRef.current) {
        setExtensionsList(extensionService.getExtensions());
        const extensionId = event.payload.extensionId;
        const status = extensionService.getExtensionStatus(extensionId);
        if (status) {
          setExtensionStatusMap(prev => new Map(prev).set(extensionId, status));
        }
      }
    };
    
    const handleExtensionUnloaded = (event: ExtensionEvent) => {
      if (isMountedRef.current) {
        setExtensionsList(extensionService.getExtensions());
        const extensionId = event.payload.extensionId;
        setExtensionStatusMap(prev => {
          const newMap = new Map(prev);
          newMap.delete(extensionId);
          return newMap;
        });
      }
    };
    
    extensionService.addEventListener(ExtensionEventType.EXTENSION_LOADED, handleExtensionLoaded);
    extensionService.addEventListener(ExtensionEventType.EXTENSION_UNLOADED, handleExtensionUnloaded);
    
    return () => {
      isMountedRef.current = false;
      extensionService.removeEventListener(ExtensionEventType.EXTENSION_LOADED, handleExtensionLoaded);
      extensionService.removeEventListener(ExtensionEventType.EXTENSION_UNLOADED, handleExtensionUnloaded);
    };
  }, [initializeExtensions, extensionService]);
  
  // Register an extension
  const registerExtension = useCallback(async (
    extension: CoPilotExtension, 
    config?: any
  ): Promise<boolean> => {
    try {
      const success = await extensionService.registerExtension(extension, config);
      
      if (success && isMountedRef.current) {
        setExtensionsList(extensionService.getExtensions());
        const status = extensionService.getExtensionStatus(extension.id);
        if (status) {
          setExtensionStatusMap(prev => new Map(prev).set(extension.id, status));
        }
      }
      
      return success;
    } catch (err) {
      console.error(`Failed to register extension ${extension.id}:`, err);
      if (isMountedRef.current) {
        setError(`Failed to register extension ${extension.id}`);
      }
      return false;
    }
  }, [extensionService]);
  
  // Unregister an extension
  const unregisterExtension = useCallback(async (
    extensionId: string
  ): Promise<boolean> => {
    try {
      const success = await extensionService.unregisterExtension(extensionId);
      
      if (success && isMountedRef.current) {
        setExtensionsList(extensionService.getExtensions());
        setExtensionStatusMap(prev => {
          const newMap = new Map(prev);
          newMap.delete(extensionId);
          return newMap;
        });
      }
      
      return success;
    } catch (err) {
      console.error(`Failed to unregister extension ${extensionId}:`, err);
      if (isMountedRef.current) {
        setError(`Failed to unregister extension ${extensionId}`);
      }
      return false;
    }
  }, [extensionService]);
  
  // Execute an extension request
  const executeExtension = useCallback(async (
    extensionId: string, 
    request: Omit<ExtensionRequest, 'id'>
  ): Promise<ExtensionResponse> => {
    try {
      const response = await extensionService.executeExtensionRequest(extensionId, request);
      
      // Update status after execution
      if (isMountedRef.current) {
        const status = extensionService.getExtensionStatus(extensionId);
        if (status) {
          setExtensionStatusMap(prev => new Map(prev).set(extensionId, status));
        }
      }
      
      return response;
    } catch (err) {
      console.error(`Failed to execute extension ${extensionId}:`, err);
      if (isMountedRef.current) {
        setError(`Failed to execute extension ${extensionId}`);
      }
      
      return {
        id: '',
        status: ExtensionResponseStatus.ERROR,
        error: {
          code: ExtensionErrorCode.EXECUTION_ERROR,
          message: err instanceof Error ? err.message : String(err)
        }
      };
    }
  }, [extensionService]);
  
  // Get extension by ID
  const getExtension = useCallback((extensionId: string): CoPilotExtension | undefined => {
    return extensionService.getExtension(extensionId);
  }, [extensionService]);
  
  // Get extension status
  const getExtensionStatus = useCallback((extensionId: string): ExtensionStatus | undefined => {
    return extensionService.getExtensionStatus(extensionId);
  }, [extensionService]);
  
  // Get UI components for an extension
  const getExtensionUIComponents = useCallback((extensionId: string): ExtensionUIComponent[] => {
    return extensionService.getUIComponents(extensionId);
  }, [extensionService]);
  
  // Get all UI components
  const getAllUIComponents = useCallback((): ExtensionUIComponent[] => {
    return extensionService.getAllUIComponents();
  }, [extensionService]);
  
  // Get hooks for an extension
  const getExtensionHooks = useCallback((extensionId: string): ExtensionHook[] => {
    return extensionService.getHooks(extensionId);
  }, [extensionService]);
  
  // Get context providers for an extension
  const getExtensionContextProviders = useCallback((extensionId: string): ExtensionContextProvider[] => {
    return extensionService.getContextProviders(extensionId);
  }, [extensionService]);
  
  // Add event listener
  const addEventListener = useCallback((
    eventType: ExtensionEventType, 
    listener: (event: ExtensionEvent) => void
  ): void => {
    extensionService.addEventListener(eventType, listener);
    
    // Track for cleanup
    if (!eventListenersRef.current.has(eventType)) {
      eventListenersRef.current.set(eventType, []);
    }
    eventListenersRef.current.get(eventType)?.push(listener);
  }, [extensionService]);
  
  // Remove event listener
  const removeEventListener = useCallback((
    eventType: ExtensionEventType, 
    listener: (event: ExtensionEvent) => void
  ): void => {
    extensionService.removeEventListener(eventType, listener);
    
    // Remove from tracking
    const listeners = eventListenersRef.current.get(eventType);
    if (listeners) {
      const index = listeners.indexOf(listener);
      if (index !== -1) {
        listeners.splice(index, 1);
      }
    }
  }, [extensionService]);
  
  // Enable or disable an extension
  const setExtensionEnabled = useCallback(async (
    extensionId: string, 
    enabled: boolean
  ): Promise<boolean> => {
    try {
      const success = await extensionService.setExtensionEnabled(extensionId, enabled);
      
      if (success && isMountedRef.current) {
        const status = extensionService.getExtensionStatus(extensionId);
        if (status) {
          setExtensionStatusMap(prev => new Map(prev).set(extensionId, status));
        }
      }
      
      return success;
    } catch (err) {
      console.error(`Failed to set enabled state for extension ${extensionId}:`, err);
      if (isMountedRef.current) {
        setError(`Failed to set enabled state for extension ${extensionId}`);
      }
      return false;
    }
  }, [extensionService]);
  
  // Update extension configuration
  const updateExtensionConfig = useCallback(async (
    extensionId: string, 
    config: any
  ): Promise<boolean> => {
    try {
      const success = await extensionService.updateExtensionConfig(extensionId, config);
      
      if (success && isMountedRef.current) {
        const status = extensionService.getExtensionStatus(extensionId);
        if (status) {
          setExtensionStatusMap(prev => new Map(prev).set(extensionId, status));
        }
      }
      
      return success;
    } catch (err) {
      console.error(`Failed to update config for extension ${extensionId}:`, err);
      if (isMountedRef.current) {
        setError(`Failed to update config for extension ${extensionId}`);
      }
      return false;
    }
  }, [extensionService]);
  
  return {
    extensionService,
    extensions: extensionsList,
    extensionStatus: extensionStatusMap,
    isLoading,
    error,
    registerExtension,
    unregisterExtension,
    executeExtension,
    getExtension,
    getExtensionStatus,
    getExtensionUIComponents,
    getAllUIComponents,
    getExtensionHooks,
    getExtensionContextProviders,
    addEventListener,
    removeEventListener,
    setExtensionEnabled,
    updateExtensionConfig
  };
};

export default useExtensions;