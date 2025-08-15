import { describe, it, expect, beforeEach } from 'vitest';
import { useUIStore, uiSelectors } from '../ui-store';

describe('UI Store', () => {
  beforeEach(() => {
    // Reset store before each test
    useUIStore.getState().resetUI();
  });

  describe('sidebar actions', () => {
    it('should toggle sidebar', () => {
      const store = useUIStore.getState();
      
      expect(store.isSidebarOpen).toBe(true);
      
      store.toggleSidebar();
      expect(useUIStore.getState().isSidebarOpen).toBe(false);
      
      store.toggleSidebar();
      expect(useUIStore.getState().isSidebarOpen).toBe(true);
    });

    it('should set sidebar open state', () => {
      const store = useUIStore.getState();
      
      store.setSidebarOpen(false);
      expect(useUIStore.getState().isSidebarOpen).toBe(false);
      
      store.setSidebarOpen(true);
      expect(useUIStore.getState().isSidebarOpen).toBe(true);
    });
  });

  describe('composer actions', () => {
    it('should toggle composer expansion', () => {
      const store = useUIStore.getState();
      
      expect(store.isComposerExpanded).toBe(false);
      
      store.toggleComposer();
      expect(useUIStore.getState().isComposerExpanded).toBe(true);
      
      store.toggleComposer();
      expect(useUIStore.getState().isComposerExpanded).toBe(false);
    });

    it('should set composer expanded state', () => {
      const store = useUIStore.getState();
      
      store.setComposerExpanded(true);
      expect(useUIStore.getState().isComposerExpanded).toBe(true);
      
      store.setComposerExpanded(false);
      expect(useUIStore.getState().isComposerExpanded).toBe(false);
    });
  });

  describe('conversation actions', () => {
    it('should set selected conversation', () => {
      const store = useUIStore.getState();
      
      store.setSelectedConversation('conv-1');
      expect(useUIStore.getState().selectedConversationId).toBe('conv-1');
      
      store.setSelectedConversation(null);
      expect(useUIStore.getState().selectedConversationId).toBe(null);
    });
  });

  describe('modal actions', () => {
    it('should open and close modals', () => {
      const store = useUIStore.getState();
      
      store.openModal('settings');
      expect(useUIStore.getState().activeModal).toBe('settings');
      
      store.closeModal();
      expect(useUIStore.getState().activeModal).toBe(null);
    });

    it('should toggle settings', () => {
      const store = useUIStore.getState();
      
      expect(store.isSettingsOpen).toBe(false);
      
      store.toggleSettings();
      expect(useUIStore.getState().isSettingsOpen).toBe(true);
      
      store.toggleSettings();
      expect(useUIStore.getState().isSettingsOpen).toBe(false);
    });
  });

  describe('theme actions', () => {
    it('should set theme', () => {
      const store = useUIStore.getState();
      
      store.setTheme('dark');
      expect(useUIStore.getState().theme).toBe('dark');
      
      store.setTheme('light');
      expect(useUIStore.getState().theme).toBe('light');
    });

    it('should set font size', () => {
      const store = useUIStore.getState();
      
      store.setFontSize('large');
      expect(useUIStore.getState().fontSize).toBe('large');
      
      store.setFontSize('small');
      expect(useUIStore.getState().fontSize).toBe('small');
    });
  });

  describe('streaming actions', () => {
    it('should set streaming state', () => {
      const store = useUIStore.getState();
      
      store.setStreaming(true, 'msg-1');
      expect(useUIStore.getState().isStreaming).toBe(true);
      expect(useUIStore.getState().streamingMessageId).toBe('msg-1');
      
      store.setStreaming(false);
      expect(useUIStore.getState().isStreaming).toBe(false);
      expect(useUIStore.getState().streamingMessageId).toBe(null);
    });
  });

  describe('error actions', () => {
    it('should set and clear errors', () => {
      const store = useUIStore.getState();
      
      store.setError('Test error');
      expect(useUIStore.getState().lastError).toBe('Test error');
      expect(useUIStore.getState().errorCount).toBe(1);
      
      store.clearError();
      expect(useUIStore.getState().lastError).toBe(null);
      expect(useUIStore.getState().errorCount).toBe(1); // Count persists
    });

    it('should increment error count', () => {
      const store = useUIStore.getState();
      
      store.incrementErrorCount();
      expect(useUIStore.getState().errorCount).toBe(1);
      
      store.incrementErrorCount();
      expect(useUIStore.getState().errorCount).toBe(2);
    });

    it('should reset error count', () => {
      const store = useUIStore.getState();
      
      store.incrementErrorCount();
      store.incrementErrorCount();
      expect(useUIStore.getState().errorCount).toBe(2);
      
      store.resetErrorCount();
      expect(useUIStore.getState().errorCount).toBe(0);
    });
  });

  describe('selectors', () => {
    it('should provide sidebar selector', () => {
      const store = useUIStore.getState();
      const sidebar = uiSelectors.sidebar(store);
      
      expect(sidebar.isOpen).toBe(true);
      expect(typeof sidebar.toggle).toBe('function');
      expect(typeof sidebar.setOpen).toBe('function');
    });

    it('should provide theme selector', () => {
      const store = useUIStore.getState();
      const theme = uiSelectors.theme(store);
      
      expect(theme.current).toBe('system');
      expect(theme.fontSize).toBe('medium');
      expect(typeof theme.setTheme).toBe('function');
      expect(typeof theme.setFontSize).toBe('function');
    });
  });

  describe('reset functionality', () => {
    it('should reset UI state', () => {
      const store = useUIStore.getState();
      
      // Modify some state
      store.setSidebarOpen(false);
      store.setTheme('dark');
      store.setError('Test error');
      
      // Reset
      store.resetUI();
      
      // Check that state is reset
      const newState = useUIStore.getState();
      expect(newState.isSidebarOpen).toBe(true);
      expect(newState.theme).toBe('system');
      expect(newState.lastError).toBe(null);
      expect(newState.errorCount).toBe(0);
    });
  });
});