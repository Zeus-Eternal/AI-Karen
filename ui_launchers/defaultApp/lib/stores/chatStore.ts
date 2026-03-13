/**
 * Chat Store using Zustand for client-side state management
 * Manages the current conversation, messages, and UI state
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Conversation, Message } from '@/types/chat'

interface ChatState {
  // Current state
  currentConversation: Conversation | null
  messages: Message[]
  isStreaming: boolean
  isLoading: boolean
  error: string | null
  
  // UI state
  isSidebarOpen: boolean
  isDarkMode: boolean
  
  // Actions
  setCurrentConversation: (conversation: Conversation | null) => void
  setMessages: (messages: Message[]) => void
  addMessage: (message: Message) => void
  updateMessage: (messageId: string, updates: Partial<Message>) => void
  removeMessage: (messageId: string) => void
  
  // Streaming actions
  setIsStreaming: (isStreaming: boolean) => void
  appendToLastMessage: (content: string) => void
  
  // Loading and error states
  setIsLoading: (isLoading: boolean) => void
  setError: (error: string | null) => void
  
  // UI actions
  toggleSidebar: () => void
  setSidebarOpen: (isOpen: boolean) => void
  toggleDarkMode: () => void
  
  // Cleanup
  clearCurrentConversation: () => void
  reset: () => void
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      // Initial state
      currentConversation: null,
      messages: [],
      isStreaming: false,
      isLoading: false,
      error: null,
      isSidebarOpen: true,
      isDarkMode: false,
      
      // Conversation actions
      setCurrentConversation: (conversation) => {
        set({ currentConversation: conversation, messages: [] })
      },
      
      setMessages: (messages) => {
        set({ messages })
      },
      
      addMessage: (message) => {
        set((state) => ({
          messages: [...state.messages, message],
        }))
      },
      
      updateMessage: (messageId, updates) => {
        set((state) => ({
          messages: state.messages.map((msg) =>
            msg.id === messageId ? { ...msg, ...updates } : msg
          ),
        }))
      },
      
      removeMessage: (messageId) => {
        set((state) => ({
          messages: state.messages.filter((msg) => msg.id !== messageId),
        }))
      },
      
      // Streaming actions
      setIsStreaming: (isStreaming) => {
        set({ isStreaming })
      },
      
      appendToLastMessage: (content) => {
        set((state) => {
          const messages = [...state.messages]
          const lastMessage = messages[messages.length - 1]
          
          if (lastMessage && lastMessage.role === 'assistant' && lastMessage.isStreaming) {
            lastMessage.content += content
            return { messages }
          }
          
          return state
        })
      },
      
      // Loading and error states
      setIsLoading: (isLoading) => {
        set({ isLoading })
      },
      
      setError: (error) => {
        set({ error })
      },
      
      // UI actions
      toggleSidebar: () => {
        set((state) => ({ isSidebarOpen: !state.isSidebarOpen }))
      },
      
      setSidebarOpen: (isOpen) => {
        set({ isSidebarOpen: isOpen })
      },
      
      toggleDarkMode: () => {
        set((state) => {
          const newDarkMode = !state.isDarkMode
          // Apply dark mode to document
          if (typeof window !== 'undefined') {
            if (newDarkMode) {
              document.documentElement.classList.add('dark')
            } else {
              document.documentElement.classList.remove('dark')
            }
          }
          return { isDarkMode: newDarkMode }
        })
      },
      
      // Cleanup
      clearCurrentConversation: () => {
        set({
          currentConversation: null,
          messages: [],
          isStreaming: false,
          error: null,
        })
      },
      
      reset: () => {
        set({
          currentConversation: null,
          messages: [],
          isStreaming: false,
          isLoading: false,
          error: null,
        })
      },
    }),
    {
      name: 'chat-storage',
      partialize: (state) => ({
        isSidebarOpen: state.isSidebarOpen,
        isDarkMode: state.isDarkMode,
      }),
    }
  )
)

// Selector hooks for optimized re-renders
export const useCurrentConversation = () => useChatStore((state) => state.currentConversation)
export const useMessages = () => useChatStore((state) => state.messages)
export const useIsStreaming = () => useChatStore((state) => state.isStreaming)
export const useIsLoading = () => useChatStore((state) => state.isLoading)
export const useChatError = () => useChatStore((state) => state.error)
export const useSidebarState = () => useChatStore((state) => state.isSidebarOpen)
export const useDarkMode = () => useChatStore((state) => state.isDarkMode)
