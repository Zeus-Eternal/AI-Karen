import { useState, useEffect, useCallback, useRef } from 'react';
import { 
  ExtensionUIComponent, 
  ExtensionUIComponentType, 
  ExtensionUIComponentPosition 
} from '../types/extension';
import ExtensionUIService from '../services/ExtensionUIService';

interface UseExtensionUIOptions {
  /** Auto-initialize UI service */
  autoInitialize?: boolean;
  
  /** Extension ID to filter components by */
  extensionId?: string;
  
  /** Component type to filter by */
  componentType?: ExtensionUIComponentType;
  
  /** Component position to filter by */
  componentPosition?: ExtensionUIComponentPosition;
}

interface UseExtensionUIResult {
  /** UI service instance */
  uiService: ExtensionUIService;
  
  /** UI components */
  components: ExtensionUIComponent[];
  
  /** Loading state */
  isLoading: boolean;
  
  /** Error state */
  error: string | null;
  
  /** Register a UI component */
  registerComponent: (extensionId: string, component: ExtensionUIComponent) => boolean;
  
  /** Unregister a UI component */
  unregisterComponent: (extensionId: string, componentId: string) => boolean;
  
  /** Get UI components for an extension */
  getComponents: (extensionId: string) => ExtensionUIComponent[];
  
  /** Get UI components by position */
  getComponentsByPosition: (position: ExtensionUIComponentPosition) => ExtensionUIComponent[];
  
  /** Get UI components by type */
  getComponentsByType: (type: ExtensionUIComponentType) => ExtensionUIComponent[];
  
  /** Update a UI component */
  updateComponent: (extensionId: string, componentId: string, updates: Partial<ExtensionUIComponent>) => boolean;
  
  /** Set visibility of a UI component */
  setComponentVisibility: (extensionId: string, componentId: string, visible: boolean) => boolean;
  
  /** Set order of a UI component */
  setComponentOrder: (extensionId: string, componentId: string, order: number) => boolean;
  
  /** Update props of a UI component */
  updateComponentProps: (extensionId: string, componentId: string, props: Record<string, any>) => boolean;
  
  /** Unregister all UI components for an extension */
  unregisterAllComponents: (extensionId: string) => boolean;
  
  /** Add component event listener */
  addComponentEventListener: (eventType: string, listener: (event: any) => void) => void;
  
  /** Remove component event listener */
  removeComponentEventListener: (eventType: string, listener: (event: any) => void) => void;
}

/**
 * React hook for managing CoPilot extension UI components
 */
export const useExtensionUI = (options: UseExtensionUIOptions = {}): UseExtensionUIResult => {
  const {
    autoInitialize = true,
    extensionId,
    componentType,
    componentPosition
  } = options;
  
  // State
  const [uiService] = useState(() => ExtensionUIService.getInstance());
  const [components, setComponents] = useState<ExtensionUIComponent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Refs
  const isMountedRef = useRef(true);
  const eventListenersRef = useRef<Map<string, Function[]>>(new Map());
  
  // Update components based on filters
  const updateComponents = useCallback(() => {
    try {
      let filteredComponents: ExtensionUIComponent[] = [];
      
      if (extensionId) {
        // Get components for specific extension
        filteredComponents = uiService.getUIComponents(extensionId);
      } else if (componentPosition) {
        // Get components by position
        filteredComponents = uiService.getUIComponentsByPosition(componentPosition);
      } else if (componentType) {
        // Get components by type
        filteredComponents = uiService.getUIComponentsByType(componentType);
      } else {
        // Get all components
        filteredComponents = [];
        // Note: We don't have a direct method to get all components across all extensions
        // This would require additional implementation in the UI service
      }
      
      if (isMountedRef.current) {
        setComponents(filteredComponents);
      }
    } catch (err) {
      console.error('Failed to update UI components:', err);
      if (isMountedRef.current) {
        setError('Failed to update UI components');
      }
    }
  }, [uiService, extensionId, componentType, componentPosition]);
  
  // Initialize on mount
  useEffect(() => {
    if (autoInitialize) {
      setIsLoading(false);
      updateComponents();
    }
    
    // Set up event listeners to update state
    const handleComponentEvent = () => {
      if (isMountedRef.current) {
        updateComponents();
      }
    };
    
    uiService.addComponentEventListener('component_registered', handleComponentEvent);
    uiService.addComponentEventListener('component_unregistered', handleComponentEvent);
    uiService.addComponentEventListener('component_updated', handleComponentEvent);
    
    return () => {
      isMountedRef.current = false;
      
      // Clean up event listeners
      uiService.removeComponentEventListener('component_registered', handleComponentEvent);
      uiService.removeComponentEventListener('component_unregistered', handleComponentEvent);
      uiService.removeComponentEventListener('component_updated', handleComponentEvent);
      
      // Clean up tracked listeners
      for (const [eventType, listeners] of eventListenersRef.current) {
        for (const listener of listeners) {
          uiService.removeComponentEventListener(eventType, listener as any);
        }
      }
    };
  }, [autoInitialize, updateComponents, uiService]);
  
  // Register a UI component
  const registerComponent = useCallback((
    extensionId: string, 
    component: ExtensionUIComponent
  ): boolean => {
    try {
      const success = uiService.registerUIComponent(extensionId, component);
      
      if (success && isMountedRef.current) {
        updateComponents();
      }
      
      return success;
    } catch (err) {
      console.error(`Failed to register UI component ${component.id}:`, err);
      if (isMountedRef.current) {
        setError(`Failed to register UI component ${component.id}`);
      }
      return false;
    }
  }, [uiService, updateComponents]);
  
  // Unregister a UI component
  const unregisterComponent = useCallback((
    extensionId: string, 
    componentId: string
  ): boolean => {
    try {
      const success = uiService.unregisterUIComponent(extensionId, componentId);
      
      if (success && isMountedRef.current) {
        updateComponents();
      }
      
      return success;
    } catch (err) {
      console.error(`Failed to unregister UI component ${componentId}:`, err);
      if (isMountedRef.current) {
        setError(`Failed to unregister UI component ${componentId}`);
      }
      return false;
    }
  }, [uiService, updateComponents]);
  
  // Get UI components for an extension
  const getComponents = useCallback((extensionId: string): ExtensionUIComponent[] => {
    return uiService.getUIComponents(extensionId);
  }, [uiService]);
  
  // Get UI components by position
  const getComponentsByPosition = useCallback((position: ExtensionUIComponentPosition): ExtensionUIComponent[] => {
    return uiService.getUIComponentsByPosition(position);
  }, [uiService]);
  
  // Get UI components by type
  const getComponentsByType = useCallback((type: ExtensionUIComponentType): ExtensionUIComponent[] => {
    return uiService.getUIComponentsByType(type);
  }, [uiService]);
  
  // Update a UI component
  const updateComponent = useCallback((
    extensionId: string, 
    componentId: string, 
    updates: Partial<ExtensionUIComponent>
  ): boolean => {
    try {
      const success = uiService.updateUIComponent(extensionId, componentId, updates);
      
      if (success && isMountedRef.current) {
        updateComponents();
      }
      
      return success;
    } catch (err) {
      console.error(`Failed to update UI component ${componentId}:`, err);
      if (isMountedRef.current) {
        setError(`Failed to update UI component ${componentId}`);
      }
      return false;
    }
  }, [uiService, updateComponents]);
  
  // Set visibility of a UI component
  const setComponentVisibility = useCallback((
    extensionId: string, 
    componentId: string, 
    visible: boolean
  ): boolean => {
    try {
      const success = uiService.setComponentVisibility(extensionId, componentId, visible);
      
      if (success && isMountedRef.current) {
        updateComponents();
      }
      
      return success;
    } catch (err) {
      console.error(`Failed to set visibility for UI component ${componentId}:`, err);
      if (isMountedRef.current) {
        setError(`Failed to set visibility for UI component ${componentId}`);
      }
      return false;
    }
  }, [uiService, updateComponents]);
  
  // Set order of a UI component
  const setComponentOrder = useCallback((
    extensionId: string, 
    componentId: string, 
    order: number
  ): boolean => {
    try {
      const success = uiService.setComponentOrder(extensionId, componentId, order);
      
      if (success && isMountedRef.current) {
        updateComponents();
      }
      
      return success;
    } catch (err) {
      console.error(`Failed to set order for UI component ${componentId}:`, err);
      if (isMountedRef.current) {
        setError(`Failed to set order for UI component ${componentId}`);
      }
      return false;
    }
  }, [uiService, updateComponents]);
  
  // Update props of a UI component
  const updateComponentProps = useCallback((
    extensionId: string, 
    componentId: string, 
    props: Record<string, any>
  ): boolean => {
    try {
      const success = uiService.updateComponentProps(extensionId, componentId, props);
      
      if (success && isMountedRef.current) {
        updateComponents();
      }
      
      return success;
    } catch (err) {
      console.error(`Failed to update props for UI component ${componentId}:`, err);
      if (isMountedRef.current) {
        setError(`Failed to update props for UI component ${componentId}`);
      }
      return false;
    }
  }, [uiService, updateComponents]);
  
  // Unregister all UI components for an extension
  const unregisterAllComponents = useCallback((extensionId: string): boolean => {
    try {
      const success = uiService.unregisterAllUIComponents(extensionId);
      
      if (success && isMountedRef.current) {
        updateComponents();
      }
      
      return success;
    } catch (err) {
      console.error(`Failed to unregister all UI components for extension ${extensionId}:`, err);
      if (isMountedRef.current) {
        setError(`Failed to unregister all UI components for extension ${extensionId}`);
      }
      return false;
    }
  }, [uiService, updateComponents]);
  
  // Add component event listener
  const addComponentEventListener = useCallback((
    eventType: string, 
    listener: (event: any) => void
  ): void => {
    uiService.addComponentEventListener(eventType, listener);
    
    // Track for cleanup
    if (!eventListenersRef.current.has(eventType)) {
      eventListenersRef.current.set(eventType, []);
    }
    eventListenersRef.current.get(eventType)?.push(listener);
  }, [uiService]);
  
  // Remove component event listener
  const removeComponentEventListener = useCallback((
    eventType: string, 
    listener: (event: any) => void
  ): void => {
    uiService.removeComponentEventListener(eventType, listener);
    
    // Remove from tracking
    const listeners = eventListenersRef.current.get(eventType);
    if (listeners) {
      const index = listeners.indexOf(listener);
      if (index !== -1) {
        listeners.splice(index, 1);
      }
    }
  }, [uiService]);
  
  return {
    uiService,
    components,
    isLoading,
    error,
    registerComponent,
    unregisterComponent,
    getComponents,
    getComponentsByPosition,
    getComponentsByType,
    updateComponent,
    setComponentVisibility,
    setComponentOrder,
    updateComponentProps,
    unregisterAllComponents,
    addComponentEventListener,
    removeComponentEventListener
  };
};

export default useExtensionUI;