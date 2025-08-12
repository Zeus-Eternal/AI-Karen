/**
 * React Hook for Action Registry System
 * 
 * Features:
 * - Easy integration with React components
 * - State management for action results
 * - Event handling for action events
 * - Loading states and error handling
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useToast } from '@/hooks/use-toast';
import { 
  getActionRegistry, 
  type SuggestedAction, 
  type ActionResult, 
  type ActionHandler 
} from '@/services/actionMapper';

interface UseActionRegistryOptions {
  autoToast?: boolean;
  onActionComplete?: (action: string, result: ActionResult) => void;
  onActionError?: (action: string, error: string) => void;
}

interface UseActionRegistryReturn {
  // Action execution
  performAction: (type: string, params?: Record<string, any>) => Promise<ActionResult>;
  performActions: (actions: SuggestedAction[]) => Promise<ActionResult[]>;
  performSuggestedAction: (action: SuggestedAction) => Promise<ActionResult>;
  
  // Action suggestions
  getSuggestions: (context: string, userIntent?: string) => SuggestedAction[];
  
  // Handler management
  registerHandler: (handler: ActionHandler) => void;
  unregisterHandler: (type: string) => void;
  getHandlers: () => ActionHandler[];
  
  // State
  isLoading: boolean;
  lastResult: ActionResult | null;
  error: string | null;
  
  // Event handling
  addEventListener: (eventName: string, listener: (event: CustomEvent) => void) => void;
  removeEventListener: (eventName: string, listener: (event: CustomEvent) => void) => void;
}

export function useActionRegistry(options: UseActionRegistryOptions = {}): UseActionRegistryReturn {
  const { autoToast = true, onActionComplete, onActionError } = options;
  const { toast } = useToast();
  const registry = getActionRegistry();
  
  // State
  const [isLoading, setIsLoading] = useState(false);
  const [lastResult, setLastResult] = useState<ActionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // Refs for stable callbacks
  const onActionCompleteRef = useRef(onActionComplete);
  const onActionErrorRef = useRef(onActionError);
  
  // Update refs when callbacks change
  useEffect(() => {
    onActionCompleteRef.current = onActionComplete;
    onActionErrorRef.current = onActionError;
  }, [onActionComplete, onActionError]);

  // Perform single action
  const performAction = useCallback(async (
    type: string, 
    params: Record<string, any> = {}
  ): Promise<ActionResult> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await registry.performAction(type, params);
      setLastResult(result);
      
      if (result.success) {
        if (autoToast && result.message) {
          toast({
            title: 'Action Completed',
            description: result.message,
            duration: 3000
          });
        }
        
        onActionCompleteRef.current?.(type, result);
      } else {
        const errorMessage = result.error || 'Action failed';
        setError(errorMessage);
        
        if (autoToast) {
          toast({
            variant: 'destructive',
            title: 'Action Failed',
            description: errorMessage,
            duration: 5000
          });
        }
        
        onActionErrorRef.current?.(type, errorMessage);
      }
      
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      
      if (autoToast) {
        toast({
          variant: 'destructive',
          title: 'Action Error',
          description: errorMessage,
          duration: 5000
        });
      }
      
      onActionErrorRef.current?.(type, errorMessage);
      
      return { success: false, error: errorMessage };
    } finally {
      setIsLoading(false);
    }
  }, [registry, autoToast, toast]);

  // Perform multiple actions
  const performActions = useCallback(async (
    actions: SuggestedAction[]
  ): Promise<ActionResult[]> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const results = await registry.performActions(actions);
      
      const successCount = results.filter(r => r.success).length;
      const failureCount = results.length - successCount;
      
      if (autoToast) {
        if (failureCount === 0) {
          toast({
            title: 'All Actions Completed',
            description: `Successfully completed ${successCount} actions`,
            duration: 3000
          });
        } else if (successCount > 0) {
          toast({
            title: 'Partial Success',
            description: `${successCount} actions completed, ${failureCount} failed`,
            duration: 4000
          });
        } else {
          toast({
            variant: 'destructive',
            title: 'All Actions Failed',
            description: `${failureCount} actions failed`,
            duration: 5000
          });
        }
      }
      
      return results;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      
      if (autoToast) {
        toast({
          variant: 'destructive',
          title: 'Actions Error',
          description: errorMessage,
          duration: 5000
        });
      }
      
      return [];
    } finally {
      setIsLoading(false);
    }
  }, [registry, autoToast, toast]);

  // Perform suggested action
  const performSuggestedAction = useCallback(async (
    action: SuggestedAction
  ): Promise<ActionResult> => {
    return performAction(action.type, action.params || {});
  }, [performAction]);

  // Get action suggestions
  const getSuggestions = useCallback((
    context: string, 
    userIntent?: string
  ): SuggestedAction[] => {
    return registry.getSuggestedActions(context, userIntent);
  }, [registry]);

  // Register handler
  const registerHandler = useCallback((handler: ActionHandler): void => {
    registry.registerHandler(handler);
  }, [registry]);

  // Unregister handler
  const unregisterHandler = useCallback((type: string): void => {
    registry.unregisterHandler(type);
  }, [registry]);

  // Get handlers
  const getHandlers = useCallback((): ActionHandler[] => {
    return registry.getHandlers();
  }, [registry]);

  // Add event listener
  const addEventListener = useCallback((
    eventName: string, 
    listener: (event: CustomEvent) => void
  ): void => {
    registry.addEventListener(eventName, listener);
  }, [registry]);

  // Remove event listener
  const removeEventListener = useCallback((
    eventName: string, 
    listener: (event: CustomEvent) => void
  ): void => {
    registry.removeEventListener(eventName, listener);
  }, [registry]);

  return {
    // Action execution
    performAction,
    performActions,
    performSuggestedAction,
    
    // Action suggestions
    getSuggestions,
    
    // Handler management
    registerHandler,
    unregisterHandler,
    getHandlers,
    
    // State
    isLoading,
    lastResult,
    error,
    
    // Event handling
    addEventListener,
    removeEventListener
  };
}

/**
 * Hook for listening to specific action events
 */
export function useActionEvents(
  eventName: string,
  handler: (event: CustomEvent) => void,
  deps: React.DependencyList = []
): void {
  const { addEventListener, removeEventListener } = useActionRegistry({ autoToast: false });
  
  useEffect(() => {
    addEventListener(eventName, handler);
    
    return () => {
      removeEventListener(eventName, handler);
    };
  }, [eventName, handler, addEventListener, removeEventListener, ...deps]);
}

/**
 * Hook for getting action suggestions based on context
 */
export function useActionSuggestions(
  context: string,
  userIntent?: string
): {
  suggestions: SuggestedAction[];
  performSuggestion: (action: SuggestedAction) => Promise<ActionResult>;
  isLoading: boolean;
} {
  const { getSuggestions, performSuggestedAction, isLoading } = useActionRegistry();
  
  const suggestions = getSuggestions(context, userIntent);
  
  return {
    suggestions,
    performSuggestion: performSuggestedAction,
    isLoading
  };
}

// Export types
export type {
  UseActionRegistryOptions,
  UseActionRegistryReturn
};