import { useState, useCallback, useRef } from 'react';
import { useUIStore, selectLoadingState, selectErrorState } from '../store';

export interface OptimisticUpdateOptions<T> {
  // The key to use for loading and error states
  key: string;
  
  // Function to perform the actual update
  updateFn: () => Promise<T>;
  
  // Function to apply optimistic update
  optimisticUpdate?: () => void;
  
  // Function to revert optimistic update on error
  revertUpdate?: () => void;
  
  // Function to apply successful update
  onSuccess?: (result: T) => void;
  
  // Function to handle errors
  onError?: (error: Error) => void;
  
  // Retry configuration
  retryConfig?: {
    maxRetries: number;
    retryDelay: number;
    backoffMultiplier?: number;
  };
  
  // Whether to show loading states
  showLoading?: boolean;
}

export function useOptimisticUpdates<T = any>() {
  const [optimisticStates, setOptimisticStates] = useState<Record<string, any>>({});
  const retryCountRef = useRef<Record<string, number>>({});
  
  const performOptimisticUpdate = useCallback(async (options: OptimisticUpdateOptions<T>) => {
    const {
      key,
      updateFn,
      optimisticUpdate,
      revertUpdate,
      onSuccess,
      onError,
      retryConfig = { maxRetries: 3, retryDelay: 1000, backoffMultiplier: 2 },
      showLoading = true,
    } = options;
    
    const { setLoading, setError, clearError } = useUIStore.getState();
    
    // Clear any previous errors
    clearError(key);
    
    // Apply optimistic update immediately
    if (optimisticUpdate) {
      optimisticUpdate();
      setOptimisticStates(prev => ({ ...prev, [key]: true }));
    }
    
    // Show loading state if requested
    if (showLoading) {
      setLoading(key, true);
    }
    
    const attemptUpdate = async (retryCount = 0): Promise<T | null> => {
      try {
        const result = await updateFn();
        
        // Success - clear optimistic state and loading
        setOptimisticStates(prev => {
          const newState = { ...prev };
          delete newState[key];
          return newState;
        });
        
        if (showLoading) {
          setLoading(key, false);
        }
        
        // Reset retry count
        retryCountRef.current[key] = 0;
        
        // Apply successful update
        if (onSuccess) {
          onSuccess(result);
        }
        
        return result;
      } catch (error) {
        const errorObj = error instanceof Error ? error : new Error(String(error));
        
        // Check if we should retry
        if (retryCount < retryConfig.maxRetries) {
          const delay = retryConfig.retryDelay * Math.pow(retryConfig.backoffMultiplier || 2, retryCount);
          
          // Wait before retrying
          await new Promise(resolve => setTimeout(resolve, delay));
          
          // Increment retry count
          retryCountRef.current[key] = retryCount + 1;
          
          return attemptUpdate(retryCount + 1);
        }
        
        // Max retries reached - revert optimistic update
        if (revertUpdate) {
          revertUpdate();
        }
        
        setOptimisticStates(prev => {
          const newState = { ...prev };
          delete newState[key];
          return newState;
        });
        
        if (showLoading) {
          setLoading(key, false);
        }
        
        // Set error state
        setError(key, errorObj.message);
        
        // Call error handler
        if (onError) {
          onError(errorObj);
        }
        
        return null;
      }
    };
    
    return attemptUpdate();
  }, []);
  
  const isOptimistic = useCallback((key: string) => {
    return optimisticStates[key] || false;
  }, [optimisticStates]);
  
  const clearOptimisticState = useCallback((key: string) => {
    setOptimisticStates(prev => {
      const newState = { ...prev };
      delete newState[key];
      return newState;
    });
  }, []);
  
  return {
    performOptimisticUpdate,
    isOptimistic,
    clearOptimisticState,
    optimisticStates,
  };
}

// Hook for form submissions with optimistic updates
export function useOptimisticForm<TData = any, TResult = any>() {
  const { performOptimisticUpdate } = useOptimisticUpdates<TResult>();
  const [formData, setFormData] = useState<TData | null>(null);
  const [submittedData, setSubmittedData] = useState<TData | null>(null);
  
  const submitForm = useCallback(async (
    data: TData,
    submitFn: (data: TData) => Promise<TResult>,
    options?: Omit<OptimisticUpdateOptions<TResult>, 'updateFn' | 'optimisticUpdate' | 'revertUpdate'>
  ) => {
    const key = options?.key || 'form-submit';
    
    return performOptimisticUpdate({
      key,
      updateFn: () => submitFn(data),
      optimisticUpdate: () => {
        setFormData(data);
        setSubmittedData(data);
      },
      revertUpdate: () => {
        setSubmittedData(null);
      },
      onSuccess: (result) => {
        setFormData(null);
        options?.onSuccess?.(result);
      },
      ...options,
    });
  }, [performOptimisticUpdate]);
  
  const resetForm = useCallback(() => {
    setFormData(null);
    setSubmittedData(null);
  }, []);
  
  return {
    submitForm,
    resetForm,
    formData,
    submittedData,
    isSubmitting: submittedData !== null,
  };
}

// Hook for list operations with optimistic updates
export function useOptimisticList<TItem = any>(initialItems: TItem[] = []) {
  const [items, setItems] = useState<TItem[]>(initialItems);
  const [optimisticItems, setOptimisticItems] = useState<TItem[]>([]);
  const { performOptimisticUpdate } = useOptimisticUpdates();
  
  const addItem = useCallback(async (
    item: TItem,
    addFn: (item: TItem) => Promise<TItem>,
    options?: Omit<OptimisticUpdateOptions<TItem>, 'updateFn' | 'optimisticUpdate' | 'revertUpdate'>
  ) => {
    const key = options?.key || 'add-item';
    
    return performOptimisticUpdate({
      key,
      updateFn: () => addFn(item),
      optimisticUpdate: () => {
        setOptimisticItems(prev => [...prev, item]);
      },
      revertUpdate: () => {
        setOptimisticItems(prev => prev.filter(i => i !== item));
      },
      onSuccess: (result) => {
        setItems(prev => [...prev, result]);
        setOptimisticItems(prev => prev.filter(i => i !== item));
      },
      ...options,
    });
  }, [performOptimisticUpdate]);
  
  const removeItem = useCallback(async (
    item: TItem,
    removeFn: (item: TItem) => Promise<void>,
    options?: Omit<OptimisticUpdateOptions<void>, 'updateFn' | 'optimisticUpdate' | 'revertUpdate'>
  ) => {
    const key = options?.key || 'remove-item';
    
    return performOptimisticUpdate({
      key,
      updateFn: () => removeFn(item),
      optimisticUpdate: () => {
        setItems(prev => prev.filter(i => i !== item));
      },
      revertUpdate: () => {
        setItems(prev => [...prev, item]);
      },
      onSuccess: () => {
        // Item already removed optimistically
      },
      ...options,
    });
  }, [performOptimisticUpdate]);
  
  const updateItem = useCallback(async (
    oldItem: TItem,
    newItem: TItem,
    updateFn: (oldItem: TItem, newItem: TItem) => Promise<TItem>,
    options?: Omit<OptimisticUpdateOptions<TItem>, 'updateFn' | 'optimisticUpdate' | 'revertUpdate'>
  ) => {
    const key = options?.key || 'update-item';
    
    return performOptimisticUpdate({
      key,
      updateFn: () => updateFn(oldItem, newItem),
      optimisticUpdate: () => {
        setItems(prev => prev.map(i => i === oldItem ? newItem : i));
      },
      revertUpdate: () => {
        setItems(prev => prev.map(i => i === newItem ? oldItem : i));
      },
      onSuccess: (result) => {
        setItems(prev => prev.map(i => i === newItem ? result : i));
      },
      ...options,
    });
  }, [performOptimisticUpdate]);
  
  const allItems = [...items, ...optimisticItems];
  
  return {
    items: allItems,
    addItem,
    removeItem,
    updateItem,
    setItems,
  };
}