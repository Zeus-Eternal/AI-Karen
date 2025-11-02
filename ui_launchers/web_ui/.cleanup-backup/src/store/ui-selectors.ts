import { UIStore } from './ui-store';

// Layout selectors
export const selectSidebarState = (state: UIStore) => ({
  collapsed: state.sidebarCollapsed,
  toggle: state.toggleSidebar,
  setCollapsed: state.setSidebarCollapsed,
});

export const selectRightPanelState = (state: UIStore) => ({
  view: state.rightPanelView,
  collapsed: state.rightPanelCollapsed,
  setView: state.setRightPanelView,
  toggle: state.toggleRightPanel,
  setCollapsed: state.setRightPanelCollapsed,
});

// Theme selectors
export const selectThemeState = (state: UIStore) => ({
  theme: state.theme,
  setTheme: state.setTheme,
});

// Animation selectors
export const selectAnimationState = (state: UIStore) => ({
  reducedMotion: state.reducedMotion,
  setReducedMotion: state.setReducedMotion,
});

// Panel selectors
export const selectPanelState = (panelId: string) => (state: UIStore) => ({
  panel: state.panelStates[panelId] || { isOpen: false },
  openPanel: (options?: { size?: number; position?: 'left' | 'right' | 'top' | 'bottom' }) => 
    state.openPanel(panelId, options),
  closePanel: () => state.closePanel(panelId),
  togglePanel: () => state.togglePanel(panelId),
  setPanelSize: (size: number) => state.setPanelSize(panelId, size),
});

// Modal selectors
export const selectModalState = (modalId: string) => (state: UIStore) => ({
  modal: state.modals[modalId] || { isOpen: false },
  openModal: (data?: any) => state.openModal(modalId, data),
  closeModal: () => state.closeModal(modalId),
  toggleModal: (data?: any) => state.toggleModal(modalId, data),
});

// Loading selectors
export const selectLoadingState = (key: string) => (state: UIStore) => ({
  loading: state.loadingStates[key] || false,
  setLoading: (loading: boolean) => state.setLoading(key, loading),
});

// Error selectors
export const selectErrorState = (key: string) => (state: UIStore) => ({
  error: state.errors[key] || null,
  setError: (error: string | null) => state.setError(key, error),
  clearError: () => state.clearError(key),
});

// Combined selectors for common use cases
export const selectLayoutState = (state: UIStore) => ({
  sidebar: {
    collapsed: state.sidebarCollapsed,
    toggle: state.toggleSidebar,
    setCollapsed: state.setSidebarCollapsed,
  },
  rightPanel: {
    view: state.rightPanelView,
    collapsed: state.rightPanelCollapsed,
    setView: state.setRightPanelView,
    toggle: state.toggleRightPanel,
    setCollapsed: state.setRightPanelCollapsed,
  },
});

export const selectPreferencesState = (state: UIStore) => ({
  theme: state.theme,
  reducedMotion: state.reducedMotion,
  setTheme: state.setTheme,
  setReducedMotion: state.setReducedMotion,
});

// Utility selectors
export const selectAllErrors = (state: UIStore) => state.errors;
export const selectAllLoadingStates = (state: UIStore) => state.loadingStates;
export const selectAllPanelStates = (state: UIStore) => state.panelStates;
export const selectAllModalStates = (state: UIStore) => state.modals;