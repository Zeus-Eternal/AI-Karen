import { create } from 'zustand';
import { devtools, persist, subscribeWithSelector } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

// UI State Types
export interface UIState {
  // Chat interface state
  isSidebarOpen: boolean;
  isComposerExpanded: boolean;
  selectedConversationId: string | null;
  
  // Modal and overlay state
  activeModal: string | null;
  isSettingsOpen: boolean;
  
  // Theme and appearance
  theme: 'light' | 'dark' | 'system';
  fontSize: 'small' | 'medium' | 'large';
  
  // Layout preferences
  chatLayout: 'default' | 'compact' | 'comfortable';
  showTimestamps: boolean;
  showAvatars: boolean;
  
  // Streaming state
  isStreaming: boolean;
  streamingMessageId: string | null;
  
  // Error state
  lastError: string | null;
  errorCount: number;
}

// UI Actions
export interface UIActions {
  // Sidebar actions
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  
  // Composer actions
  toggleComposer: () => void;
  setComposerExpanded: (expanded: boolean) => void;
  
  // Conversation actions
  setSelectedConversation: (id: string | null) => void;
  
  // Modal actions
  openModal: (modalId: string) => void;
  closeModal: () => void;
  toggleSettings: () => void;
  
  // Theme actions
  setTheme: (theme: UIState['theme']) => void;
  setFontSize: (size: UIState['fontSize']) => void;
  
  // Layout actions
  setChatLayout: (layout: UIState['chatLayout']) => void;
  toggleTimestamps: () => void;
  toggleAvatars: () => void;
  
  // Streaming actions
  setStreaming: (isStreaming: boolean, messageId?: string) => void;
  
  // Error actions
  setError: (error: string | null) => void;
  clearError: () => void;
  incrementErrorCount: () => void;
  resetErrorCount: () => void;
  
  // Reset actions
  resetUI: () => void;
}

// Initial state
const initialState: UIState = {
  isSidebarOpen: true,
  isComposerExpanded: false,
  selectedConversationId: null,
  activeModal: null,
  isSettingsOpen: false,
  theme: 'system',
  fontSize: 'medium',
  chatLayout: 'default',
  showTimestamps: true,
  showAvatars: true,
  isStreaming: false,
  streamingMessageId: null,
  lastError: null,
  errorCount: 0,
};

// Create the UI store with persistence and devtools
export const useUIStore = create<UIState & UIActions>()(
  devtools(
    persist(
      subscribeWithSelector(
        immer((set, get) => ({
          ...initialState,

          // Sidebar actions
          toggleSidebar: () =>
            set((state) => {
              state.isSidebarOpen = !state.isSidebarOpen;
            }),

          setSidebarOpen: (open: boolean) =>
            set((state) => {
              state.isSidebarOpen = open;
            }),

          // Composer actions
          toggleComposer: () =>
            set((state) => {
              state.isComposerExpanded = !state.isComposerExpanded;
            }),

          setComposerExpanded: (expanded: boolean) =>
            set((state) => {
              state.isComposerExpanded = expanded;
            }),

          // Conversation actions
          setSelectedConversation: (id: string | null) =>
            set((state) => {
              state.selectedConversationId = id;
            }),

          // Modal actions
          openModal: (modalId: string) =>
            set((state) => {
              state.activeModal = modalId;
            }),

          closeModal: () =>
            set((state) => {
              state.activeModal = null;
            }),

          toggleSettings: () =>
            set((state) => {
              state.isSettingsOpen = !state.isSettingsOpen;
            }),

          // Theme actions
          setTheme: (theme: UIState['theme']) =>
            set((state) => {
              state.theme = theme;
            }),

          setFontSize: (size: UIState['fontSize']) =>
            set((state) => {
              state.fontSize = size;
            }),

          // Layout actions
          setChatLayout: (layout: UIState['chatLayout']) =>
            set((state) => {
              state.chatLayout = layout;
            }),

          toggleTimestamps: () =>
            set((state) => {
              state.showTimestamps = !state.showTimestamps;
            }),

          toggleAvatars: () =>
            set((state) => {
              state.showAvatars = !state.showAvatars;
            }),

          // Streaming actions
          setStreaming: (isStreaming: boolean, messageId?: string) =>
            set((state) => {
              state.isStreaming = isStreaming;
              state.streamingMessageId = messageId || null;
            }),

          // Error actions
          setError: (error: string | null) =>
            set((state) => {
              state.lastError = error;
              if (error) {
                state.errorCount += 1;
              }
            }),

          clearError: () =>
            set((state) => {
              state.lastError = null;
            }),

          incrementErrorCount: () =>
            set((state) => {
              state.errorCount += 1;
            }),

          resetErrorCount: () =>
            set((state) => {
              state.errorCount = 0;
            }),

          // Reset actions
          resetUI: () =>
            set((state) => {
              Object.assign(state, initialState);
            }),
        }))
      ),
      {
        name: 'ui-store',
        // Only persist certain UI preferences
        partialize: (state) => ({
          theme: state.theme,
          fontSize: state.fontSize,
          chatLayout: state.chatLayout,
          showTimestamps: state.showTimestamps,
          showAvatars: state.showAvatars,
          isSidebarOpen: state.isSidebarOpen,
        }),
      }
    ),
    {
      name: 'UI Store',
    }
  )
);

// Selectors for optimized subscriptions
export const uiSelectors = {
  sidebar: (state: UIState & UIActions) => ({
    isOpen: state.isSidebarOpen,
    toggle: state.toggleSidebar,
    setOpen: state.setSidebarOpen,
  }),
  
  composer: (state: UIState & UIActions) => ({
    isExpanded: state.isComposerExpanded,
    toggle: state.toggleComposer,
    setExpanded: state.setComposerExpanded,
  }),
  
  conversation: (state: UIState & UIActions) => ({
    selectedId: state.selectedConversationId,
    setSelected: state.setSelectedConversation,
  }),
  
  theme: (state: UIState & UIActions) => ({
    current: state.theme,
    fontSize: state.fontSize,
    setTheme: state.setTheme,
    setFontSize: state.setFontSize,
  }),
  
  streaming: (state: UIState & UIActions) => ({
    isStreaming: state.isStreaming,
    messageId: state.streamingMessageId,
    setStreaming: state.setStreaming,
  }),
  
  error: (state: UIState & UIActions) => ({
    lastError: state.lastError,
    errorCount: state.errorCount,
    setError: state.setError,
    clearError: state.clearError,
    incrementCount: state.incrementErrorCount,
    resetCount: state.resetErrorCount,
  }),
};