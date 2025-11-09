/**
 * Enhanced App Store
 * 
 * Global state management with Zustand for theme, auth, and layout preferences.
 * Based on requirements: 12.2, 12.3
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import { subscribeWithSelector } from 'zustand/middleware';

// App State Types
export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  roles: string[];
  preferences: UserPreferences;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  density: 'compact' | 'comfortable' | 'spacious';
  language: string;
  timezone: string;
  notifications: {
    email: boolean;
    push: boolean;
    desktop: boolean;
  };
  accessibility: {
    reducedMotion: boolean;
    highContrast: boolean;
    screenReader: boolean;
  };
}

export interface LayoutState {
  sidebarOpen: boolean;
  sidebarCollapsed: boolean;
  rightPanelOpen: boolean;
  rightPanelView: string;
  headerHeight: number;
  footerVisible: boolean;
  breadcrumbsVisible: boolean;
}

export interface AppState {
  // Authentication state
  user: User | null;
  isAuthenticated: boolean;
  authLoading: boolean;
  authError: string | null;
  
  // Layout state
  layout: LayoutState;
  
  // Global loading states
  globalLoading: boolean;
  loadingStates: Record<string, boolean>;
  
  // Global error states
  errors: Record<string, string | null>;
  
  // Connection state
  isOnline: boolean;
  connectionQuality: 'good' | 'poor' | 'offline';
  
  // Feature flags
  features: Record<string, boolean>;
  
  // Notifications
  notifications: Array<{
    id: string;
    type: 'info' | 'success' | 'warning' | 'error';
    title: string;
    message: string;
    timestamp: Date;
    read: boolean;
    actions?: Array<{
      label: string;
      action: () => void;
    }>;
  }>;
}

export interface AppActions {
  // Authentication actions
  setUser: (user: User | null) => void;
  setAuthLoading: (loading: boolean) => void;
  setAuthError: (error: string | null) => void;
  login: (user: User) => void;
  logout: () => void;
  updateUserPreferences: (preferences: Partial<UserPreferences>) => void;
  
  // Layout actions
  setSidebarOpen: (open: boolean) => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setRightPanelOpen: (open: boolean) => void;
  setRightPanelView: (view: string) => void;
  setHeaderHeight: (height: number) => void;
  setFooterVisible: (visible: boolean) => void;
  setBreadcrumbsVisible: (visible: boolean) => void;
  toggleSidebar: () => void;
  toggleRightPanel: () => void;
  
  // Loading actions
  setGlobalLoading: (loading: boolean) => void;
  setLoading: (key: string, loading: boolean) => void;
  clearLoading: (key: string) => void;
  clearAllLoading: () => void;
  
  // Error actions
  setError: (key: string, error: string | null) => void;
  clearError: (key: string) => void;
  clearAllErrors: () => void;
  
  // Connection actions
  setOnline: (online: boolean) => void;
  setConnectionQuality: (quality: 'good' | 'poor' | 'offline') => void;
  
  // Feature flag actions
  setFeature: (feature: string, enabled: boolean) => void;
  toggleFeature: (feature: string) => void;
  
  // Notification actions
  addNotification: (notification: Omit<AppState['notifications'][0], 'id' | 'timestamp' | 'read'>) => void;
  markNotificationRead: (id: string) => void;
  removeNotification: (id: string) => void;
  clearAllNotifications: () => void;
  
  // Reset actions
  resetAppState: () => void;
}

export type AppStore = AppState & AppActions;

// Initial state
const initialState: AppState = {
  user: null,
  isAuthenticated: false,
  authLoading: false,
  authError: null,
  
  layout: {
    sidebarOpen: true,
    sidebarCollapsed: false,
    rightPanelOpen: false,
    rightPanelView: 'dashboard',
    headerHeight: 64,
    footerVisible: true,
    breadcrumbsVisible: true,
  },
  
  globalLoading: false,
  loadingStates: {},
  errors: {},
  
  isOnline: true,
  connectionQuality: 'good',
  
  features: {},
  notifications: [],
};

// Create the enhanced app store
export const useAppStore = create<AppStore>()(
  subscribeWithSelector(
    persist(
      immer((set, get) => ({
        ...initialState,
        
        // Authentication actions
        setUser: (user: User | null) => set((state) => {
          state.user = user;
          state.isAuthenticated = !!user;
        }),
        
        setAuthLoading: (loading: boolean) => set((state) => {
          state.authLoading = loading;
        }),
        
        setAuthError: (error: string | null) => set((state) => {
          state.authError = error;
        }),
        
        login: (user: User) => set((state) => {
          state.user = user;
          state.isAuthenticated = true;
          state.authLoading = false;
          state.authError = null;
        }),
        
        logout: () => set((state) => {
          state.user = null;
          state.isAuthenticated = false;
          state.authLoading = false;
          state.authError = null;
          // Clear sensitive data
          state.notifications = [];
          state.errors = {};
        }),
        
        updateUserPreferences: (preferences: Partial<UserPreferences>) => set((state) => {
          if (state.user) {
            state.user.preferences = { ...state.user.preferences, ...preferences };
          }
        }),
        
        // Layout actions
        setSidebarOpen: (open: boolean) => set((state) => {
          state.layout.sidebarOpen = open;
        }),
        
        setSidebarCollapsed: (collapsed: boolean) => set((state) => {
          state.layout.sidebarCollapsed = collapsed;
        }),
        
        setRightPanelOpen: (open: boolean) => set((state) => {
          state.layout.rightPanelOpen = open;
        }),
        
        setRightPanelView: (view: string) => set((state) => {
          state.layout.rightPanelView = view;
        }),
        
        setHeaderHeight: (height: number) => set((state) => {
          state.layout.headerHeight = height;
        }),
        
        setFooterVisible: (visible: boolean) => set((state) => {
          state.layout.footerVisible = visible;
        }),
        
        setBreadcrumbsVisible: (visible: boolean) => set((state) => {
          state.layout.breadcrumbsVisible = visible;
        }),
        
        toggleSidebar: () => set((state) => {
          state.layout.sidebarOpen = !state.layout.sidebarOpen;
        }),
        
        toggleRightPanel: () => set((state) => {
          state.layout.rightPanelOpen = !state.layout.rightPanelOpen;
        }),
        
        // Loading actions
        setGlobalLoading: (loading: boolean) => set((state) => {
          state.globalLoading = loading;
        }),
        
        setLoading: (key: string, loading: boolean) => set((state) => {
          if (loading) {
            state.loadingStates[key] = true;
          } else {
            delete state.loadingStates[key];
          }
        }),
        
        clearLoading: (key: string) => set((state) => {
          delete state.loadingStates[key];
        }),
        
        clearAllLoading: () => set((state) => {
          state.loadingStates = {};
          state.globalLoading = false;
        }),
        
        // Error actions
        setError: (key: string, error: string | null) => set((state) => {
          if (error) {
            state.errors[key] = error;
          } else {
            delete state.errors[key];
          }
        }),
        
        clearError: (key: string) => set((state) => {
          delete state.errors[key];
        }),
        
        clearAllErrors: () => set((state) => {
          state.errors = {};
        }),
        
        // Connection actions
        setOnline: (online: boolean) => set((state) => {
          state.isOnline = online;
          if (!online) {
            state.connectionQuality = 'offline';
          }
        }),
        
        setConnectionQuality: (quality: 'good' | 'poor' | 'offline') => set((state) => {
          state.connectionQuality = quality;
          state.isOnline = quality !== 'offline';
        }),
        
        // Feature flag actions
        setFeature: (feature: string, enabled: boolean) => set((state) => {
          state.features[feature] = enabled;
        }),
        
        toggleFeature: (feature: string) => set((state) => {
          state.features[feature] = !state.features[feature];
        }),
        
        // Notification actions
        addNotification: (notification) => set((state) => {
          const newNotification = {
            ...notification,
            id: `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            timestamp: new Date(),
            read: false,
          };
          state.notifications.unshift(newNotification);
          
          // Keep only the last 50 notifications
          if (state.notifications.length > 50) {
            state.notifications = state.notifications.slice(0, 50);
          }
        }),
        
        markNotificationRead: (id: string) => set((state) => {
          const notification = state.notifications.find(n => n.id === id);
          if (notification) {
            notification.read = true;
          }
        }),
        
        removeNotification: (id: string) => set((state) => {
          state.notifications = state.notifications.filter(n => n.id !== id);
        }),
        
        clearAllNotifications: () => set((state) => {
          state.notifications = [];
        }),
        
        // Reset actions
        resetAppState: () => set(() => ({ ...initialState })),
      })),
      {
        name: 'kari-app-store',
        storage: createJSONStorage(() => localStorage),
        // Only persist certain parts of the state
        partialize: (state) => ({
          user: state.user,
          isAuthenticated: state.isAuthenticated,
          layout: {
            sidebarCollapsed: state.layout.sidebarCollapsed,
            rightPanelView: state.layout.rightPanelView,
            footerVisible: state.layout.footerVisible,
            breadcrumbsVisible: state.layout.breadcrumbsVisible,
          },
          features: state.features,
        }),
        // Handle migration for state changes
        version: 1,
        migrate: (persistedState: any, version: number) => {
          if (version === 0) {
            // Migration from version 0 to 1
            return {
              ...persistedState,
              layout: {
                ...initialState.layout,
                ...persistedState.layout,
              },
            };
          }
          return persistedState;
        },
      }
    )
  )
);

// Selectors for common state access patterns
export const selectUser = (state: AppStore) => state.user;
export const selectIsAuthenticated = (state: AppStore) => state.isAuthenticated;
export const selectLayout = (state: AppStore) => state.layout;
export const selectTheme = (state: AppStore) => state.user?.preferences.theme || 'system';
export const selectDensity = (state: AppStore) => state.user?.preferences.density || 'comfortable';
export const selectIsLoading = (key: string) => (state: AppStore) => state.loadingStates[key] || false;
export const selectError = (key: string) => (state: AppStore) => state.errors[key] || null;
export const selectUnreadNotifications = (state: AppStore) => state.notifications.filter(n => !n.read);
export const selectFeature = (feature: string) => (state: AppStore) => state.features[feature] || false;