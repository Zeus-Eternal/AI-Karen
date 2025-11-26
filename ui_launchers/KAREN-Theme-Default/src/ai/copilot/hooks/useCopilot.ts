import React, { useState, useEffect, useRef, useCallback } from 'react';
import { CopilotEngine } from '../services/copilotEngine';
import {
  CopilotState,
  UseCopilotStateProps,
  UseCopilotStateReturn,
  CopilotContextValue,
  CopilotEvent
} from '../types/copilot';

/**
 * React hook for accessing Copilot functionality
 * Provides a clean interface for React components to interact with the Copilot engine
 */
export function useCopilot(props: UseCopilotStateProps): UseCopilotStateReturn {
  const [state, setState] = useState<CopilotState>(() => {
    const engine = new CopilotEngine(props.backendConfig, props.initialState);
    return engine.getState();
  });
  
  const engineRef = useRef<CopilotEngine | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);
  
  // Initialize the engine on first render
  useEffect(() => {
    if (!engineRef.current) {
      engineRef.current = new CopilotEngine(props.backendConfig, props.initialState);
      
      // Subscribe to state updates
      engineRef.current.subscribeToStateUpdates(setState);
      
      // Initialize the engine
      engineRef.current.initialize()
        .then(() => setIsInitialized(true))
        .catch(error => {
          console.error('Failed to initialize Copilot engine:', error);
          setIsInitialized(false);
        });
    }
    
    // Cleanup on unmount
    return () => {
      if (engineRef.current) {
        // Check if we're in a static export environment or offline
        const isStaticExport = typeof window === 'undefined' ||
          process.env.NEXT_PHASE === 'phase-production-build' ||
          (typeof window !== 'undefined' && !navigator.onLine);
        
        // Only flush telemetry data if not in static export and online
        if (!isStaticExport) {
          // Flush any pending telemetry data
          engineRef.current.flushTelemetry().catch(_error => {
            // Silently handle telemetry flush errors to avoid disrupting the application
            console.log('Telemetry flush failed (this is normal in development or offline environments)');
          });
        }
      }
    };
  }, [props.backendConfig, props.initialState]);
  
  // Memoize the hook interface to prevent unnecessary re-renders
  const hookInterface = engineRef.current?.createHookInterface();
  
  // Return a minimal interface if not initialized
  if (!isInitialized || !hookInterface) {
    // Return a minimal interface that handles the uninitialized state
    // For updateUIConfig, we'll allow it to work even when not initialized
    // to prevent errors during initial render
    return {
      state: state,
      sendMessage: async () => {
        throw new Error('Copilot engine is not initialized yet');
      },
      executeAction: async () => {
        throw new Error('Copilot engine is not initialized yet');
      },
      executeWorkflow: async () => {
        throw new Error('Copilot engine is not initialized yet');
      },
      openArtifact: async () => {
        throw new Error('Copilot engine is not initialized yet');
      },
      changePanel: async () => {
        throw new Error('Copilot engine is not initialized yet');
      },
      changeModality: async () => {
        throw new Error('Copilot engine is not initialized yet');
      },
      selectLNM: async () => {
        throw new Error('Copilot engine is not initialized yet');
      },
      togglePlugin: async () => {
        throw new Error('Copilot engine is not initialized yet');
      },
      updateUIConfig: async (config: Partial<CopilotState['uiConfig']>) => {
        // Allow updateUIConfig to work even when not initialized
        // by updating the local state directly
        setState(prevState => ({
          ...prevState,
          uiConfig: {
            ...prevState.uiConfig,
            ...config
          }
        }));
      },
      clearError: async () => {
        throw new Error('Copilot engine is not initialized yet');
      },
      retry: async () => {
        throw new Error('Copilot engine is not initialized yet');
      },
      dismissAction: async () => {
        throw new Error('Copilot engine is not initialized yet');
      },
      dismissWorkflow: async () => {
        throw new Error('Copilot engine is not initialized yet');
      },
      dismissArtifact: async () => {
        throw new Error('Copilot engine is not initialized yet');
      },
      refreshState: async () => {
        throw new Error('Copilot engine is not initialized yet');
      }
    };
  }
  
  return hookInterface;
}

/**
 * React context for Copilot
 * Allows components to access Copilot state and functions without prop drilling
 */
export const CopilotContext = React.createContext<CopilotContextValue | null>(null);

/**
 * Hook to access the Copilot context
 * Must be used within a CopilotProvider
 */
export function useCopilotContext(): CopilotContextValue {
  const context = React.useContext(CopilotContext);
  
  if (!context) {
    throw new Error('useCopilotContext must be used within a CopilotProvider');
  }
  
  return context;
}

/**
 * Provider component for Copilot context
 * Wraps components and provides access to Copilot state and functions
 */
export function CopilotProvider({ 
  children, 
  backendConfig, 
  initialState 
}: { 
  children: React.ReactNode;
  backendConfig: UseCopilotStateProps['backendConfig'];
  initialState?: UseCopilotStateProps['initialState'];
}) {
  const hookInterface = useCopilot({ backendConfig, initialState });
  
  return (
    React.createElement(CopilotContext.Provider, { value: hookInterface }, children)
  );
}

/**
 * Hook for accessing Copilot state
 * Returns the current state without any functions
 */
export function useCopilotState(): CopilotState {
  const { state } = useCopilotContext();
  return state;
}

/**
 * Hook for sending messages
 * Returns a function to send messages to the Copilot
 */
export function useCopilotSendMessage() {
  const { sendMessage } = useCopilotContext();
  return sendMessage;
}

/**
 * Hook for executing actions
 * Returns a function to execute actions
 */
export function useCopilotExecuteAction() {
  const { executeAction } = useCopilotContext();
  return executeAction;
}

/**
 * Hook for executing workflows
 * Returns a function to execute workflows
 */
export function useCopilotExecuteWorkflow() {
  const { executeWorkflow } = useCopilotContext();
  return executeWorkflow;
}

/**
 * Hook for opening artifacts
 * Returns a function to open artifacts
 */
export function useCopilotOpenArtifact() {
  const { openArtifact } = useCopilotContext();
  return openArtifact;
}

/**
 * Hook for changing the active panel
 * Returns a function to change the active panel
 */
export function useCopilotChangePanel() {
  const { changePanel } = useCopilotContext();
  return changePanel;
}

/**
 * Hook for changing the input modality
 * Returns a function to change the input modality
 */
export function useCopilotChangeModality() {
  const { changeModality } = useCopilotContext();
  return changeModality;
}

/**
 * Hook for selecting an LNM
 * Returns a function to select an LNM
 */
export function useCopilotSelectLNM() {
  const { selectLNM } = useCopilotContext();
  return selectLNM;
}

/**
 * Hook for toggling plugins
 * Returns a function to toggle plugins
 */
export function useCopilotTogglePlugin() {
  const { togglePlugin } = useCopilotContext();
  return togglePlugin;
}

/**
 * Hook for updating UI configuration
 * Returns a function to update UI configuration
 */
export function useCopilotUpdateUIConfig() {
  const { updateUIConfig } = useCopilotContext();
  return updateUIConfig;
}

/**
 * Hook for clearing errors
 * Returns a function to clear errors
 */
export function useCopilotClearError() {
  const { clearError } = useCopilotContext();
  return clearError;
}

/**
 * Hook for retrying failed messages
 * Returns a function to retry failed messages
 */
export function useCopilotRetry() {
  const { retry } = useCopilotContext();
  return retry;
}

/**
 * Hook for dismissing actions
 * Returns a function to dismiss actions
 */
export function useCopilotDismissAction() {
  const { dismissAction } = useCopilotContext();
  return dismissAction;
}

/**
 * Hook for dismissing workflows
 * Returns a function to dismiss workflows
 */
export function useCopilotDismissWorkflow() {
  const { dismissWorkflow } = useCopilotContext();
  return dismissWorkflow;
}

/**
 * Hook for dismissing artifacts
 * Returns a function to dismiss artifacts
 */
export function useCopilotDismissArtifact() {
  const { dismissArtifact } = useCopilotContext();
  return dismissArtifact;
}

/**
 * Hook for refreshing state
 * Returns a function to refresh state
 */
export function useCopilotRefreshState() {
  const { refreshState } = useCopilotContext();
  return refreshState;
}

/**
 * Hook for subscribing to Copilot events
 * Allows components to react to specific Copilot events
 */
export function useCopilotEvent(
  eventType: string,
  callback: (event: CopilotEvent) => void
) {
  const { state: _state } = useCopilotContext();
  
  useEffect(() => {
    if (!_state) return;
    
    // In a real implementation, we would subscribe to events from the engine
    // For now, we'll just call the callback immediately
    // This is a placeholder for the actual event subscription logic
    
    return () => {
      // Cleanup event subscription
    };
  }, [_state, eventType, callback]);
}

/**
 * Hook for accessing Copilot telemetry
 * Returns functions to record telemetry events and performance metrics
 */
export function useCopilotTelemetry() {
  const recordEvent = useCallback((eventName: string, properties?: Record<string, unknown>) => {
    // In a real implementation, this would record telemetry events
    console.log('Recording telemetry event:', eventName, properties);
  }, []);
  
  const recordMetric = useCallback((metricName: string, value: number, unit?: string) => {
    // In a real implementation, this would record performance metrics
    console.log('Recording performance metric:', metricName, value, unit);
  }, []);
  
  const recordError = useCallback((error: Error, context?: Record<string, unknown>) => {
    // In a real implementation, this would record errors
    console.error('Recording error:', error, context);
  }, []);
  
  return {
    recordEvent,
    recordMetric,
    recordError
  };
}

/**
 * Hook for defining Copilot actions
 * Allows components to define actions that can be executed by the Copilot
 */
export function useCopilotAction(
  name: string,
  description: string,
  handler: (params: Record<string, unknown>) => Promise<Record<string, unknown> | void>,
  dependencies?: React.DependencyList
) {
  const { state: _state } = useCopilotContext();
  
  useEffect(() => {
    if (!_state) return;
    
    // Register the action with the Copilot engine
    // In a real implementation, this would register the action with the backend
    console.log(`Registering action: ${name}`, { description, dependencies });
    
    return () => {
      // Cleanup - unregister the action
      console.log(`Unregistering action: ${name}`);
    };
  }, [_state, name, description, handler, dependencies]);
  
  return {
    name,
    description,
    execute: handler
  };
}

/**
 * Hook for providing readable context to the Copilot
 * Allows components to provide context that the Copilot can read
 */
export function useCopilotReadable(
  id: string,
  data: unknown,
  description?: string
) {
  const { state: _state } = useCopilotContext();
  
  useEffect(() => {
    if (!_state) return;
    
    // Provide the data to the Copilot engine
    // In a real implementation, this would send the data to the backend
    console.log(`Providing readable context: ${id}`, { data, description });
    
    return () => {
      // Cleanup - remove the context
      console.log(`Removing readable context: ${id}`);
    };
  }, [_state, id, data, description]);
  
  return {
    id,
    data,
    description
  };
}