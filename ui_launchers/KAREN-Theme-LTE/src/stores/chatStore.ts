/**
 * Chat Store
 * Zustand store for managing chat state and messages
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { ChatMessage } from '@/lib/types';

export interface ChatState {
  // Messages
  messages: ChatMessage[];
  isLoading: boolean;
  error?: string;
  
  // Input state
  inputValue: string;
  isRecording: boolean;
  
  // Conversation state
  conversationId: string | null;
  sessionId: string | null;
  userId: string | null;
  
  // Voice settings
  voiceEnabled: boolean;
  activeListenMode: boolean;
  
  // UI state
  showTimestamps: boolean;
  showMetadata: boolean;
  autoScroll: boolean;
  
  // Actions
  setMessages: (messages: ChatMessage[]) => void;
  addMessage: (message: ChatMessage) => void;
  updateMessage: (id: string, updates: Partial<ChatMessage>) => void;
  removeMessage: (id: string) => void;
  clearMessages: () => void;
  
  setLoading: (loading: boolean) => void;
  setError: (error?: string) => void;
  setInputValue: (value: string) => void;
  setRecording: (recording: boolean) => void;
  
  setConversationId: (id: string | null) => void;
  setSessionId: (id: string | null) => void;
  setUserId: (id: string | null) => void;
  
  setVoiceEnabled: (enabled: boolean) => void;
  setActiveListenMode: (enabled: boolean) => void;
  
  setShowTimestamps: (show: boolean) => void;
  setShowMetadata: (show: boolean) => void;
  setAutoScroll: (enabled: boolean) => void;
  
  // Complex actions
  sendMessage: (content: string) => Promise<void>;
  startRecording: () => void;
  stopRecording: () => void;
  toggleVoice: () => void;
  toggleActiveListen: () => void;
  resetChat: () => void;
  
  // API integration
  loadConversationHistory: (conversationId: string) => Promise<void>;
  retryFailedMessage: (messageId: string) => Promise<void>;
}

export const useChatStore = create<ChatState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        messages: [],
        isLoading: false,
        error: undefined,
        inputValue: '',
        isRecording: false,
        conversationId: null,
        sessionId: null,
        userId: null,
        voiceEnabled: true,
        activeListenMode: false,
        showTimestamps: true,
        showMetadata: true,
        autoScroll: true,

        // Basic setters
        setMessages: (messages) => set({ messages }),
        addMessage: (message) => set((state) => ({ 
          messages: [...state.messages, message] 
        })),
        updateMessage: (id, updates) => set((state) => ({
          messages: state.messages.map((msg) => 
            msg.id === id ? { ...msg, ...updates } : msg
          )
        })),
        removeMessage: (id) => set((state) => ({
          messages: state.messages.filter((msg) => msg.id !== id)
        })),
        clearMessages: () => set({ messages: [] }),

        setLoading: (loading) => set({ isLoading: loading }),
        setError: (error) => set({ error }),
        setInputValue: (value) => set({ inputValue: value }),
        setRecording: (recording) => set({ isRecording: recording }),

        setConversationId: (id) => set({ conversationId: id }),
        setSessionId: (id) => set({ sessionId: id }),
        setUserId: (id) => set({ userId: id }),

        setVoiceEnabled: (enabled) => set({ voiceEnabled: enabled }),
        setActiveListenMode: (enabled) => set({ activeListenMode: enabled }),

        setShowTimestamps: (show) => set({ showTimestamps: show }),
        setShowMetadata: (show) => set({ showMetadata: show }),
        setAutoScroll: (enabled) => set({ autoScroll: enabled }),

        // Complex actions
        sendMessage: async (content) => {
          const { conversationId, sessionId, userId } = get();
          
          if (!content.trim()) return;

          // Clear any previous errors
          set({ error: undefined });

          // Create user message
          const userMessage: ChatMessage = {
            id: `user-${Date.now()}`,
            role: 'user',
            content: content.trim(),
            timestamp: new Date(),
          };

          // Add user message immediately
          set((state) => ({
            messages: [...state.messages, userMessage],
            inputValue: '',
            isLoading: true,
          }));

          try {
            // Call real API
            const response = await fetch('/api/ai/chat', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                // Add API key if available
                ...(process.env.NEXT_PUBLIC_API_KEY && {
                  'Authorization': `Bearer ${process.env.NEXT_PUBLIC_API_KEY}`
                })
              },
              body: JSON.stringify({
                message: content,
                conversationId: conversationId || undefined,
                sessionId: sessionId || undefined,
                userId: userId || undefined,
                preferences: {
                  personalityTone: 'friendly',
                  personalityVerbosity: 'balanced',
                  memoryDepth: 'medium',
                  enableStreaming: false,
                }
              }),
            });

            if (!response.ok) {
              const errorData = await response.json();
              throw new Error(errorData.error || 'Failed to send message');
            }

            const data = await response.json();

            // Create assistant message
            const assistantMessage: ChatMessage = {
              id: data.messageId || `assistant-${Date.now()}`,
              role: 'assistant',
              content: data.message || 'Sorry, I could not process your request.',
              timestamp: new Date(),
              aiData: {
                confidence: data.metadata?.confidence,
                intent: data.metadata?.intent,
              },
              metadata: data.metadata || {}
            };

            // Add assistant message and update conversation ID
            set((state) => ({
              messages: [...state.messages, assistantMessage],
              isLoading: false,
              conversationId: data.conversationId || state.conversationId,
            }));

          } catch (error) {
            console.error('Failed to send message:', error);
            
            // Update user message with error
            set((state) => ({
              messages: state.messages.map((msg) =>
                msg.id === userMessage.id
                  ? { ...msg, content: `${msg.content} (Error: Failed to send)` }
                  : msg
              ),
              isLoading: false,
              error: error instanceof Error ? error.message : 'Unknown error occurred',
            }));
          }
        },

        loadConversationHistory: async (conversationId: string) => {
          try {
            set({ isLoading: true, error: undefined });
            
            const response = await fetch(`/api/ai/chat/history?conversationId=${conversationId}`, {
              method: 'GET',
              headers: {
                // Add API key if available
                ...(process.env.NEXT_PUBLIC_API_KEY && {
                  'Authorization': `Bearer ${process.env.NEXT_PUBLIC_API_KEY}`
                })
              }
            });

            if (!response.ok) {
              const errorData = await response.json();
              throw new Error(errorData.error || 'Failed to load conversation history');
            }

            const data = await response.json();
            
            set({
              messages: data.messages || [],
              conversationId: conversationId,
              isLoading: false,
            });
          } catch (error) {
            console.error('Failed to load conversation history:', error);
            set({
              isLoading: false,
              error: error instanceof Error ? error.message : 'Failed to load conversation history',
            });
          }
        },

        retryFailedMessage: async (messageId: string) => {
          const { messages } = get();
          const failedMessage = messages.find(msg => msg.id === messageId);
          
          if (!failedMessage || failedMessage.role !== 'user') {
            return;
          }

          try {
            set({ isLoading: true, error: undefined });
            
            // Retry sending message
            const response = await fetch('/api/ai/chat', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                // Add API key if available
                ...(process.env.NEXT_PUBLIC_API_KEY && {
                  'Authorization': `Bearer ${process.env.NEXT_PUBLIC_API_KEY}`
                })
              },
              body: JSON.stringify({
                message: failedMessage.content,
                conversationId: get().conversationId || undefined,
                sessionId: get().sessionId || undefined,
                userId: get().userId || undefined,
                preferences: {
                  personalityTone: 'friendly',
                  personalityVerbosity: 'balanced',
                  memoryDepth: 'medium',
                  enableStreaming: false,
                }
              }),
            });

            if (!response.ok) {
              const errorData = await response.json();
              throw new Error(errorData.error || 'Failed to retry message');
            }

            const data = await response.json();

            // Update failed message with success state
            set((state) => ({
              messages: state.messages.map((msg) =>
                msg.id === messageId
                  ? { ...msg, content: failedMessage.content } // Remove error suffix
                  : msg
              ),
              isLoading: false,
            }));

            // Add new assistant message
            const assistantMessage: ChatMessage = {
              id: data.messageId || `assistant-${Date.now()}`,
              role: 'assistant',
              content: data.message || 'Sorry, I could not process your request.',
              timestamp: new Date(),
              aiData: {
                confidence: data.metadata?.confidence,
                intent: data.metadata?.intent,
              },
              metadata: data.metadata || {}
            };

            set((state) => ({
              messages: [...state.messages, assistantMessage],
              conversationId: data.conversationId || state.conversationId,
            }));

          } catch (error) {
            console.error('Failed to retry message:', error);
            set({
              isLoading: false,
              error: error instanceof Error ? error.message : 'Failed to retry message',
            });
          }
        },

        startRecording: () => set({ isRecording: true }),
        stopRecording: () => set({ isRecording: false }),
        
        toggleVoice: () => set((state) => ({ 
          voiceEnabled: !state.voiceEnabled 
        })),
        
        toggleActiveListen: () => set((state) => ({ 
          activeListenMode: !state.activeListenMode 
        })),

        resetChat: () => set({
          messages: [],
          isLoading: false,
          error: undefined,
          inputValue: '',
          isRecording: false,
          conversationId: null,
          sessionId: null,
        }),
      }),
      {
        name: 'chat-store',
        partialize: (state) => ({
          voiceEnabled: state.voiceEnabled,
          activeListenMode: state.activeListenMode,
          showTimestamps: state.showTimestamps,
          showMetadata: state.showMetadata,
          autoScroll: state.autoScroll,
          userId: state.userId,
        }),
      }
    ),
    {
      name: 'chat-store',
    }
  )
);

// Selectors for common state combinations
export const useChatMessages = () => useChatStore((state) => state.messages);
export const useChatLoading = () => useChatStore((state) => state.isLoading);
export const useChatInput = () => useChatStore((state) => state.inputValue);
export const useChatRecording = () => useChatStore((state) => state.isRecording);
export const useChatError = () => useChatStore((state) => state.error);
export const useVoiceSettings = () => useChatStore((state) => ({
  voiceEnabled: state.voiceEnabled,
  activeListenMode: state.activeListenMode,
}));

// Action hooks
export const useChatActions = () => useChatStore((state) => ({
  sendMessage: state.sendMessage,
  clearMessages: state.clearMessages,
  startRecording: state.startRecording,
  stopRecording: state.stopRecording,
  toggleVoice: state.toggleVoice,
  toggleActiveListen: state.toggleActiveListen,
  resetChat: state.resetChat,
  loadConversationHistory: state.loadConversationHistory,
  retryFailedMessage: state.retryFailedMessage,
}));

// Utility functions
export const getMessageById = (id: string, messages: ChatMessage[]): ChatMessage | undefined => {
  return messages.find((msg) => msg.id === id);
};

export const getMessagesByRole = (role: ChatMessage['role'], messages: ChatMessage[]): ChatMessage[] => {
  return messages.filter((msg) => msg.role === role);
};

export const getLastMessage = (messages: ChatMessage[]): ChatMessage | undefined => {
  return messages[messages.length - 1];
};

export const getConversationStats = (messages: ChatMessage[]) => {
  const userMessages = getMessagesByRole('user', messages);
  const assistantMessages = getMessagesByRole('assistant', messages);
  
  return {
    totalMessages: messages.length,
    userMessages: userMessages.length,
    assistantMessages: assistantMessages.length,
    averageResponseTime: 0, // Calculate based on timestamps
  };
};