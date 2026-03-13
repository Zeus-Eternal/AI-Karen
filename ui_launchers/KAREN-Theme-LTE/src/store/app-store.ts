/**
 * Application Store
 * 
 * Centralized state management for the application
 * Using Zustand for state management
 */

import { create } from 'zustand';

export interface AppNotification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
  timestamp: Date;
  actions?: Array<{
    label: string;
    action: () => void;
  }>;
}

export interface LoadingState {
  isLoading: boolean;
  message?: string;
  progress?: number;
}

export interface ConnectionState {
  quality: 'excellent' | 'good' | 'fair' | 'poor' | 'offline';
  speed?: number;
  latency?: number;
}

export interface AppState {
  // Loading states
  loading: LoadingState;
  globalLoading: LoadingState;
  
  // Notifications
  notifications: AppNotification[];
  
  // Connection state
  connectionQuality: ConnectionState;
  
  // User session
  isAuthenticated: boolean;
  user: {
    id?: string;
    email?: string;
    name?: string;
    avatar?: string;
    preferences?: Record<string, unknown>;
  } | null;
  
  // Error state
  error: string | null;
}

export interface AppActions {
  // Loading actions
  setLoading: (loading: Partial<LoadingState>) => void;
  setGlobalLoading: (loading: Partial<LoadingState>) => void;
  clearLoading: () => void;
  
  // Notification actions
  addNotification: (notification: Omit<AppNotification, 'id' | 'timestamp'>) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
  
  // Connection actions
  setConnectionQuality: (quality: Partial<ConnectionState>) => void;
  
  // Auth actions
  setUser: (user: AppState['user']) => void;
  logout: () => void;
  
  // Error actions
  setError: (error: string | Error) => void;
  clearError: (key?: string) => void;
}

export const useAppStore = create<AppState & AppActions>((set, get) => ({
  // Initial state
  loading: {
    isLoading: false,
  },
  globalLoading: {
    isLoading: false,
  },
  notifications: [],
  connectionQuality: {
    quality: 'excellent',
  },
  isAuthenticated: false,
  user: null,
  error: null,

  // Loading actions
  setLoading: (loading) => set((state) => ({
    loading: { ...state.loading, ...loading }
  })),
  
  setGlobalLoading: (loading) => set((state) => ({
    globalLoading: { ...state.globalLoading, ...loading }
  })),
  
  clearLoading: () => set({
    loading: { isLoading: false },
    globalLoading: { isLoading: false }
  }),

  // Notification actions
  addNotification: (notification) => {
    const id = Math.random().toString(36).substr(2, 9);
    const timestamp = new Date();
    
    set((state) => ({
      notifications: [...state.notifications, { ...notification, id, timestamp }]
    }));

    // Auto-remove notification after duration
    const duration = notification.duration ?? 5000;
    if (duration > 0) {
      setTimeout(() => {
        get().removeNotification(id);
      }, duration);
    }
  },
  
  removeNotification: (id) => set((state) => ({
    notifications: state.notifications.filter(n => n.id !== id)
  })),
  
  clearNotifications: () => set({ notifications: [] }),

  // Connection actions
  setConnectionQuality: (quality) => set((state) => ({
    connectionQuality: { ...state.connectionQuality, ...quality }
  })),

  // Auth actions
  setUser: (user) => set({
    user,
    isAuthenticated: !!user
  }),
  
  logout: () => set({
    user: null,
    isAuthenticated: false,
    notifications: [],
    error: null
  }),

  // Error actions
  setError: (error) => set({ error: typeof error === 'string' ? error : error.message }),
  clearError: () => set({ error: null })
}));

export type UseAppStoreReturn = ReturnType<typeof useAppStore>;