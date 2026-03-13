/**
 * Custom React hook for chat functionality
 * Handles message sending, streaming, and conversation management
 */

import { useCallback, useEffect, useRef } from 'react'
import { v4 as uuidv4 } from 'uuid'
import { useChatStore } from '@/lib/stores/chatStore'
import apiClient from '@/lib/api/client'
import type { Message, Conversation } from '@/types/chat'

export function useChat() {
  const {
    currentConversation,
    messages,
    isStreaming,
    isLoading,
    error,
    setCurrentConversation,
    setMessages,
    addMessage,
    updateMessage,
    setIsStreaming,
    setIsLoading,
    setError,
  } = useChatStore()
  
  const abortControllerRef = useRef<AbortController | null>(null)
  
  /**
   * Load messages for the current conversation
   */
  const loadMessages = useCallback(async () => {
    if (!currentConversation) return
    
    try {
      setIsLoading(true)
      setError(null)
      
      const response = await apiClient.getMessages(currentConversation.id)
      const data = await response.json()
      
      setMessages(data.messages || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load messages')
      console.error('Error loading messages:', err)
    } finally {
      setIsLoading(false)
    }
  }, [currentConversation, setIsLoading, setError, setMessages])
  
  /**
   * Send a message and optionally stream the response
   */
  const sendMessage = useCallback(async (
    content: string,
    options?: {
      stream?: boolean
      agentId?: string
      executionMode?: 'native' | 'langgraph' | 'deepagents' | 'auto'
    }
  ) => {
    if (!currentConversation) {
      setError('No active conversation')
      return
    }
    
    if (!content.trim()) {
      setError('Message cannot be empty')
      return
    }
    
    try {
      setIsLoading(true)
      setError(null)
      
      // Cancel any ongoing request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
      abortControllerRef.current = new AbortController()
      
      // Create user message
      const userMessage: Message = {
        id: uuidv4(),
        conversationId: currentConversation.id,
        role: 'user',
        content: content.trim(),
        timestamp: new Date().toISOString(),
      }
      addMessage(userMessage)
      
      // Create placeholder for assistant message
      const assistantMessage: Message = {
        id: uuidv4(),
        conversationId: currentConversation.id,
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
        isStreaming: options?.stream || false,
      }
      addMessage(assistantMessage)
      
      if (options?.stream) {
        // Stream the response
        setIsStreaming(true)
        
        await apiClient.streamMessage(
          currentConversation.id,
          content,
          {
            agentId: options?.agentId,
            executionMode: options?.executionMode,
            onChunk: (chunk) => {
              updateMessage(assistantMessage.id, {
                content: (messages.find(m => m.id === assistantMessage.id)?.content || '') + chunk,
              })
            },
            onMetadata: (metadata) => {
              updateMessage(assistantMessage.id, {
                metadata,
              })
            },
            onError: (errorMsg) => {
              setError(errorMsg)
              updateMessage(assistantMessage.id, {
                content: `Error: ${errorMsg}`,
                isStreaming: false,
              })
            },
            onDone: () => {
              setIsStreaming(false)
              updateMessage(assistantMessage.id, {
                isStreaming: false,
              })
            },
          }
        )
      } else {
        // Non-streaming request
        const response = await apiClient.sendMessage(
          currentConversation.id,
          content,
          {
            agentId: options?.agentId,
            executionMode: options?.executionMode,
          }
        )
        
        const data = await response.json()
        
        updateMessage(assistantMessage.id, {
          content: data.response || '',
          metadata: data.metadata,
        })
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message')
      console.error('Error sending message:', err)
    } finally {
      setIsLoading(false)
    }
  }, [currentConversation, addMessage, updateMessage, setIsLoading, setError, setIsStreaming, messages])
  
  /**
   * Create a new conversation
   */
  const createConversation = useCallback(async (title?: string) => {
    try {
      setIsLoading(true)
      setError(null)
      
      const response = await apiClient.createConversation(title)
      const conversation: Conversation = await response.json()
      
      setCurrentConversation(conversation)
      setMessages([])
      
      return conversation
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create conversation')
      console.error('Error creating conversation:', err)
      return null
    } finally {
      setIsLoading(false)
    }
  }, [setCurrentConversation, setMessages, setIsLoading, setError])
  
  /**
   * Select an existing conversation
   */
  const selectConversation = useCallback(async (conversation: Conversation) => {
    setCurrentConversation(conversation)
    // Messages will be loaded by the useEffect
  }, [setCurrentConversation])
  
  /**
   * Update conversation title
   */
  const updateConversation = useCallback(async (conversationId: string, updates: { title?: string }) => {
    try {
      const response = await apiClient.updateConversation(conversationId, updates)
      const updated: Conversation = await response.json()
      
      if (currentConversation?.id === conversationId) {
        setCurrentConversation(updated)
      }
      
      return updated
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update conversation')
      console.error('Error updating conversation:', err)
      return null
    }
  }, [currentConversation, setCurrentConversation, setError])
  
  /**
   * Delete a conversation
   */
  const deleteConversation = useCallback(async (conversationId: string) => {
    try {
      await apiClient.deleteConversation(conversationId)
      
      if (currentConversation?.id === conversationId) {
        clearCurrentConversation()
      }
      
      return true
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete conversation')
      console.error('Error deleting conversation:', err)
      return false
    }
  }, [currentConversation, setError])
  
  /**
   * Clear the current conversation
   */
  const clearCurrentConversation = useCallback(() => {
    setCurrentConversation(null)
    setMessages([])
    setError(null)
  }, [setCurrentConversation, setMessages, setError])
  
  /**
   * Stop streaming response
   */
  const stopStreaming = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
    setIsStreaming(false)
  }, [setIsStreaming])
  
  // Load messages when conversation changes
  useEffect(() => {
    if (currentConversation) {
      loadMessages()
    }
  }, [currentConversation?.id, loadMessages])
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])
  
  return {
    // State
    currentConversation,
    messages,
    isStreaming,
    isLoading,
    error,
    
    // Actions
    sendMessage,
    createConversation,
    selectConversation,
    updateConversation,
    deleteConversation,
    clearCurrentConversation,
    stopStreaming,
    loadMessages,
  }
}
