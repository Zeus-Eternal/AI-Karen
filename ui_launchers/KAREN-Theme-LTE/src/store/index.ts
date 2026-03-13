/**
 * UI Store
 * Provides centralized UI state management
 */

import { create } from 'zustand';

export interface LoadingState {
  isLoading: boolean;
  message?: string;
  progress?: number;
}

export interface ErrorState {
  error: string | null;
  timestamp: Date | null;
  context?: Record<string, unknown>;
}

export interface UIState {
  loading: Record<string, LoadingState>;
  errors: Record<string, ErrorState>;
  globalLoading: LoadingState;
  globalError: ErrorState;
}

export interface UIActions {
  // Loading actions
  setLoading: (key: string, loading: Partial<LoadingState>) => void;
  setGlobalLoading: (loading: Partial<LoadingState>) => void;
  clearLoading: (key?: string) => void;
  clearAllLoading: () => void;
  
  // Error actions
  setError: (key: string, error: string | null, context?: Record<string, unknown>) => void;
  setGlobalError: (error: string | null, context?: Record<string, unknown>) => void;
  clearError: (key: string) => void;
  clearAllErrors: () => void;
}

export const useUIStore = create<UIState & UIActions>((set) => ({
  // Initial state
  loading: {},
  errors: {},
  globalLoading: {
    isLoading: false,
  },
  globalError: {
    error: null,
    timestamp: null,
  },

  // Loading actions
  setLoading: (key, loading) => set((state) => ({
    loading: {
      ...state.loading,
      [key]: {
        ...(state.loading[key] || { isLoading: false }),
        ...loading,
      },
    },
  })),

  setGlobalLoading: (loading) => set((state) => ({
    globalLoading: {
      ...state.globalLoading,
      ...loading,
    },
  })),

  clearLoading: (key) => set((state) => {
    if (key) {
      const newLoading = { ...state.loading };
      delete newLoading[key];
      return { loading: newLoading };
    }
    return { loading: {} };
  }),

  clearAllLoading: () => set({ loading: {} }),

  // Error actions
  setError: (key, error, context) => set((state) => ({
    errors: {
      ...state.errors,
      [key]: {
        error,
        timestamp: error ? new Date() : null,
        context,
      },
    },
  })),

  setGlobalError: (error, context) => set(() => ({
    globalError: {
      error,
      timestamp: error ? new Date() : null,
      context,
    },
  })),

  clearError: (key) => set((state) => {
    const newErrors = { ...state.errors };
    delete newErrors[key];
    return { errors: newErrors };
  }),

  clearAllErrors: () => set({ errors: {} }),
}));

// Selectors
export const selectLoadingState = (key: string) => (state: UIState) => state.loading[key] || { isLoading: false };
export const selectErrorState = (key: string) => (state: UIState) => state.errors[key] || { error: null, timestamp: null };
export const selectGlobalLoading = (state: UIState) => state.globalLoading;
export const selectGlobalError = (state: UIState) => state.globalError;

export type UseUIStoreReturn = ReturnType<typeof useUIStore>;