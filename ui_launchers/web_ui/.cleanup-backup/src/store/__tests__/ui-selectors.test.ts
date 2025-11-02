import { describe, it, expect } from 'vitest';
import {
  selectSidebarState,
  selectRightPanelState,
  selectThemeState,
  selectAnimationState,
  selectPanelState,
  selectModalState,
  selectLoadingState,
  selectErrorState,
  selectLayoutState,
  selectPreferencesState,
} from '../ui-selectors';
import { UIStore } from '../ui-store';

// Mock store state
const createMockStore = (overrides: Partial<UIStore> = {}): UIStore => ({
  // State
  sidebarCollapsed: false,
  rightPanelView: 'dashboard',
  rightPanelCollapsed: false,
  theme: 'system',
  reducedMotion: false,
  panelStates: {
    'test-panel': { isOpen: true, size: 300, position: 'right' },
  },
  modals: {
    'test-modal': { isOpen: true, data: { id: 1 } },
  },
  loadingStates: {
    'test-loading': true,
  },
  errors: {
    'test-error': 'Test error message',
  },
  
  // Actions (mocked)
  toggleSidebar: () => {},
  setSidebarCollapsed: () => {},
  setRightPanelView: () => {},
  toggleRightPanel: () => {},
  setRightPanelCollapsed: () => {},
  setTheme: () => {},
  setReducedMotion: () => {},
  openPanel: () => {},
  closePanel: () => {},
  togglePanel: () => {},
  setPanelSize: () => {},
  openModal: () => {},
  closeModal: () => {},
  toggleModal: () => {},
  setLoading: () => {},
  setError: () => {},
  clearError: () => {},
  clearAllErrors: () => {},
  resetUIState: () => {},
  
  ...overrides,
});

describe('UI Selectors', () => {
  describe('selectSidebarState', () => {
    it('should select sidebar state and actions', () => {
      const mockStore = createMockStore({ sidebarCollapsed: true });
      const result = selectSidebarState(mockStore);
      
      expect(result.collapsed).toBe(true);
      expect(typeof result.toggle).toBe('function');
      expect(typeof result.setCollapsed).toBe('function');
    });
  });

  describe('selectRightPanelState', () => {
    it('should select right panel state and actions', () => {
      const mockStore = createMockStore({
        rightPanelView: 'settings',
        rightPanelCollapsed: true,
      });
      const result = selectRightPanelState(mockStore);
      
      expect(result.view).toBe('settings');
      expect(result.collapsed).toBe(true);
      expect(typeof result.setView).toBe('function');
      expect(typeof result.toggle).toBe('function');
      expect(typeof result.setCollapsed).toBe('function');
    });
  });

  describe('selectThemeState', () => {
    it('should select theme state and actions', () => {
      const mockStore = createMockStore({ theme: 'dark' });
      const result = selectThemeState(mockStore);
      
      expect(result.theme).toBe('dark');
      expect(typeof result.setTheme).toBe('function');
    });
  });

  describe('selectAnimationState', () => {
    it('should select animation state and actions', () => {
      const mockStore = createMockStore({ reducedMotion: true });
      const result = selectAnimationState(mockStore);
      
      expect(result.reducedMotion).toBe(true);
      expect(typeof result.setReducedMotion).toBe('function');
    });
  });

  describe('selectPanelState', () => {
    it('should select specific panel state and actions', () => {
      const mockStore = createMockStore();
      const selector = selectPanelState('test-panel');
      const result = selector(mockStore);
      
      expect(result.panel).toEqual({
        isOpen: true,
        size: 300,
        position: 'right',
      });
      expect(typeof result.openPanel).toBe('function');
      expect(typeof result.closePanel).toBe('function');
      expect(typeof result.togglePanel).toBe('function');
      expect(typeof result.setPanelSize).toBe('function');
    });

    it('should return default panel state for non-existent panel', () => {
      const mockStore = createMockStore();
      const selector = selectPanelState('non-existent-panel');
      const result = selector(mockStore);
      
      expect(result.panel).toEqual({ isOpen: false });
    });
  });

  describe('selectModalState', () => {
    it('should select specific modal state and actions', () => {
      const mockStore = createMockStore();
      const selector = selectModalState('test-modal');
      const result = selector(mockStore);
      
      expect(result.modal).toEqual({
        isOpen: true,
        data: { id: 1 },
      });
      expect(typeof result.openModal).toBe('function');
      expect(typeof result.closeModal).toBe('function');
      expect(typeof result.toggleModal).toBe('function');
    });

    it('should return default modal state for non-existent modal', () => {
      const mockStore = createMockStore();
      const selector = selectModalState('non-existent-modal');
      const result = selector(mockStore);
      
      expect(result.modal).toEqual({ isOpen: false });
    });
  });

  describe('selectLoadingState', () => {
    it('should select specific loading state and actions', () => {
      const mockStore = createMockStore();
      const selector = selectLoadingState('test-loading');
      const result = selector(mockStore);
      
      expect(result.loading).toBe(true);
      expect(typeof result.setLoading).toBe('function');
    });

    it('should return false for non-existent loading state', () => {
      const mockStore = createMockStore();
      const selector = selectLoadingState('non-existent-loading');
      const result = selector(mockStore);
      
      expect(result.loading).toBe(false);
    });
  });

  describe('selectErrorState', () => {
    it('should select specific error state and actions', () => {
      const mockStore = createMockStore();
      const selector = selectErrorState('test-error');
      const result = selector(mockStore);
      
      expect(result.error).toBe('Test error message');
      expect(typeof result.setError).toBe('function');
      expect(typeof result.clearError).toBe('function');
    });

    it('should return null for non-existent error state', () => {
      const mockStore = createMockStore();
      const selector = selectErrorState('non-existent-error');
      const result = selector(mockStore);
      
      expect(result.error).toBe(null);
    });
  });

  describe('selectLayoutState', () => {
    it('should select combined layout state', () => {
      const mockStore = createMockStore({
        sidebarCollapsed: true,
        rightPanelView: 'settings',
        rightPanelCollapsed: false,
      });
      const result = selectLayoutState(mockStore);
      
      expect(result.sidebar.collapsed).toBe(true);
      expect(result.rightPanel.view).toBe('settings');
      expect(result.rightPanel.collapsed).toBe(false);
      expect(typeof result.sidebar.toggle).toBe('function');
      expect(typeof result.rightPanel.setView).toBe('function');
    });
  });

  describe('selectPreferencesState', () => {
    it('should select combined preferences state', () => {
      const mockStore = createMockStore({
        theme: 'dark',
        reducedMotion: true,
      });
      const result = selectPreferencesState(mockStore);
      
      expect(result.theme).toBe('dark');
      expect(result.reducedMotion).toBe(true);
      expect(typeof result.setTheme).toBe('function');
      expect(typeof result.setReducedMotion).toBe('function');
    });
  });
});