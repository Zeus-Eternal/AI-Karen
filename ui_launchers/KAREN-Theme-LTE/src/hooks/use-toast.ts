/**
 * Toast Hook
 * Provides toast notification functionality for React components
 */

import { useState, useCallback, useRef, useEffect } from 'react';

export interface Toast {
  id: string;
  title: string;
  message?: string;
  type: 'success' | 'error' | 'warning' | 'info';
  duration?: number;
  persistent?: boolean;
  action?: {
    label: string;
    onClick: () => void;
  };
  metadata?: Record<string, unknown>;
}

export interface ToastState {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
  clearToasts: () => void;
  updateToast: (id: string, updates: Partial<Toast>) => void;
}

// Type aliases for compatibility with index.ts exports
export type ToasterToast = Toast;
export type State = ToastState;

// Action types for reducer
export type ActionType = 'ADD_TOAST' | 'REMOVE_TOAST' | 'CLEAR_TOASTS' | 'UPDATE_TOAST';

export interface Action {
  type: ActionType;
  payload?: unknown;
}

// Reducer function for toast state management
export function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'ADD_TOAST':
      if (!action.payload || typeof action.payload !== 'object') return state;
      const toastPayload = action.payload as Toast;
      return {
        ...state,
        toasts: [...state.toasts, toastPayload]
      };
    case 'REMOVE_TOAST':
      if (typeof action.payload !== 'string') return state;
      return {
        ...state,
        toasts: state.toasts.filter(toast => toast.id !== action.payload)
      };
    case 'CLEAR_TOASTS':
      return {
        ...state,
        toasts: []
      };
    case 'UPDATE_TOAST':
      if (!action.payload || typeof action.payload !== 'object') return state;
      const updatePayload = action.payload as { id: string; updates: Partial<Toast> };
      return {
        ...state,
        toasts: state.toasts.map(toast =>
          toast.id === updatePayload.id
            ? { ...toast, ...updatePayload.updates }
          : toast
        )
      };
    default:
      return state;
  }
}

let toastIdCounter = 0;

export function useToast(): ToastState {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const toastTimeouts = useRef<Map<string, NodeJS.Timeout>>(new Map());

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
    
    // Clear timeout if exists
    const timeout = toastTimeouts.current.get(id);
    if (timeout) {
      clearTimeout(timeout);
      toastTimeouts.current.delete(id);
    }
  }, []);

  const addToast = useCallback((toast: Omit<Toast, 'id'>) => {
    const id = `toast-${++toastIdCounter}`;
    const newToast: Toast = { ...toast, id };
    
    setToasts(prev => [...prev, newToast]);
    
    // Auto-remove toast after duration
    if (toast.duration && toast.duration > 0 && !toast.persistent) {
      const timeout = setTimeout(() => {
        removeToast(id);
      }, toast.duration);
      
      toastTimeouts.current.set(id, timeout);
    }
    
    return id;
  }, [removeToast]);

  const clearToasts = useCallback(() => {
    setToasts([]);
    
    // Clear all timeouts
    toastTimeouts.current.forEach(timeout => clearTimeout(timeout));
    toastTimeouts.current.clear();
  }, []);

  const updateToast = useCallback((id: string, updates: Partial<Toast>) => {
    setToasts(prev => prev.map(toast => 
      toast.id === id ? { ...toast, ...updates } : toast
    ));
    
    // Handle duration changes
    if (updates.duration !== undefined) {
      const existingTimeout = toastTimeouts.current.get(id);
      if (existingTimeout) {
        clearTimeout(existingTimeout);
        toastTimeouts.current.delete(id);
      }
      
      if (updates.duration && updates.duration > 0) {
        const timeout = setTimeout(() => {
          removeToast(id);
        }, updates.duration);
        
        toastTimeouts.current.set(id, timeout);
      }
    }
  }, [removeToast]);

  // Cleanup timeouts on unmount
  useEffect(() => {
    const timeouts = toastTimeouts.current;
    return () => {
      timeouts.forEach(timeout => clearTimeout(timeout));
    };
  }, []);

  return {
    toasts,
    addToast,
    removeToast,
    clearToasts,
    updateToast
  };
}

export default useToast;
