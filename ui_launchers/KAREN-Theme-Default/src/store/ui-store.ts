import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

// UI Store Types
export interface UIState {
  // Layout state
  sidebarCollapsed: boolean;
  rightPanelView: string;
  rightPanelCollapsed: boolean;
  
  // Theme state
  theme: 'light' | 'dark' | 'system';
  
  // Animation preferences
  reducedMotion: boolean;
  
  // Panel states
  panelStates: Record<string, {
    isOpen: boolean;
    size?: number;
    position?: 'left' | 'right' | 'top' | 'bottom';
  }>;
  
  // Modal states
  modals: Record<string, {
    isOpen: boolean;
    data?: unknown;
  }>;
  
  // Loading states
  loadingStates: Record<string, boolean>;
  
  // Error states
  errors: Record<string, string | null>;
}

export interface UIActions {
  // Layout actions
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setRightPanelView: (view: string) => void;
  toggleRightPanel: () => void;
  setRightPanelCollapsed: (collapsed: boolean) => void;
  
  // Theme actions
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  
  // Animation actions
  setReducedMotion: (reduced: boolean) => void;
  
  // Panel actions
  openPanel: (panelId: string, options?: { size?: number; position?: 'left' | 'right' | 'top' | 'bottom' }) => void;
  closePanel: (panelId: string) => void;
  togglePanel: (panelId: string) => void;
  setPanelSize: (panelId: string, size: number) => void;
  
  // Modal actions
  openModal: (modalId: string, data?: unknown) => void;
  closeModal: (modalId: string) => void;
  toggleModal: (modalId: string, data?: unknown) => void;
  
  // Loading actions
  setLoading: (key: string, loading: boolean) => void;
  
  // Error actions
  setError: (key: string, error: string | null) => void;
  clearError: (key: string) => void;
  clearAllErrors: () => void;
  
  // Reset actions
  resetUIState: () => void;
}

export type UIStore = UIState & UIActions;

// Initial state
const initialState: UIState = {
  sidebarCollapsed: false,
  rightPanelView: 'dashboard',
  rightPanelCollapsed: false,
  theme: 'system',
  reducedMotion: false,
  panelStates: {},
  modals: {},
  loadingStates: {},
  errors: {},
};

// Create the store with persistence and immer middleware
export const useUIStore = create<UIStore>()(
  persist(
    immer((set, _get) => ({
      ...initialState,
      
      // Layout actions
      toggleSidebar: () => set((state) => {
        state.sidebarCollapsed = !state.sidebarCollapsed;
      }),
      
      setSidebarCollapsed: (collapsed: boolean) => set((state) => {
        state.sidebarCollapsed = collapsed;
      }),
      
      setRightPanelView: (view: string) => set((state) => {
        state.rightPanelView = view;
      }),
      
      toggleRightPanel: () => set((state) => {
        state.rightPanelCollapsed = !state.rightPanelCollapsed;
      }),
      
      setRightPanelCollapsed: (collapsed: boolean) => set((state) => {
        state.rightPanelCollapsed = collapsed;
      }),
      
      // Theme actions
      setTheme: (theme: 'light' | 'dark' | 'system') => set((state) => {
        state.theme = theme;
      }),
      
      // Animation actions
      setReducedMotion: (reduced: boolean) => set((state) => {
        state.reducedMotion = reduced;
      }),
      
      // Panel actions
      openPanel: (panelId: string, options = {}) => set((state) => {
        state.panelStates[panelId] = {
          isOpen: true,
          size: options.size,
          position: options.position,
        };
      }),
      
      closePanel: (panelId: string) => set((state) => {
        if (state.panelStates[panelId]) {
          state.panelStates[panelId].isOpen = false;
        }
      }),
      
      togglePanel: (panelId: string) => set((state) => {
        if (state.panelStates[panelId]) {
          state.panelStates[panelId].isOpen = !state.panelStates[panelId].isOpen;
        } else {
          state.panelStates[panelId] = { isOpen: true };
        }
      }),
      
      setPanelSize: (panelId: string, size: number) => set((state) => {
        if (state.panelStates[panelId]) {
          state.panelStates[panelId].size = size;
        }
      }),
      
      // Modal actions
      openModal: (modalId: string, data?: unknown) => set((state) => {
        state.modals[modalId] = { isOpen: true, data };
      }),
      
      closeModal: (modalId: string) => set((state) => {
        if (state.modals[modalId]) {
          state.modals[modalId].isOpen = false;
          state.modals[modalId].data = undefined;
        }
      }),
      
      toggleModal: (modalId: string, data?: unknown) => set((state) => {
        if (state.modals[modalId]) {
          state.modals[modalId].isOpen = !state.modals[modalId].isOpen;
          if (state.modals[modalId].isOpen && data !== undefined) {
            state.modals[modalId].data = data;
          }
        } else {
          state.modals[modalId] = { isOpen: true, data };
        }
      }),
      
      // Loading actions
      setLoading: (key: string, loading: boolean) => set((state) => {
        state.loadingStates[key] = loading;
      }),
      
      // Error actions
      setError: (key: string, error: string | null) => set((state) => {
        state.errors[key] = error;
      }),
      
      clearError: (key: string) => set((state) => {
        delete state.errors[key];
      }),
      
      clearAllErrors: () => set((state) => {
        state.errors = {};
      }),
      
      // Reset actions
      resetUIState: () => set(() => ({ ...initialState })),
    })),
    {
      name: 'ui-store',
      storage: createJSONStorage(() => localStorage),
      // Only persist certain parts of the state
      partialize: (state) => ({
        sidebarCollapsed: state.sidebarCollapsed,
        rightPanelView: state.rightPanelView,
        rightPanelCollapsed: state.rightPanelCollapsed,
        theme: state.theme,
        reducedMotion: state.reducedMotion,
        panelStates: state.panelStates,
      }),
    }
  )
);
