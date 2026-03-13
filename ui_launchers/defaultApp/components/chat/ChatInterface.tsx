/**
 * ChatInterface Component
 * Main chat interface combining message list and input
 */

'use client'

import { useEffect } from 'react'
import { useChat } from '@/lib/hooks/useChat'
import { MessageList } from './MessageList'
import { MessageInput } from './MessageInput'
import { Loader2 } from 'lucide-react'

export function ChatInterface() {
  const {
    currentConversation,
    messages,
    isStreaming,
    isLoading,
    error,
    sendMessage,
    createConversation,
    stopStreaming,
  } = useChat()
  
  /**
   * Create a new conversation on mount if none exists
   */
  useEffect(() => {
    if (!currentConversation) {
      createConversation('New Chat')
    }
  }, [currentConversation, createConversation])
  
  /**
   * Handle sending a message
   */
  const handleSendMessage = async (content: string) => {
    if (!currentConversation) {
      const newConv = await createConversation()
      if (!newConv) return
    }
    
    // Send with streaming enabled
    await sendMessage(content, { stream: true })
  }
  
  return (
    <div className="flex flex-col h-screen bg-gray-100 dark:bg-gray-900">
      {/* Header */}
      <div className="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
              AI-Karen
            </h1>
            {currentConversation && (
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-0.5">
                {currentConversation.title}
              </p>
            )}
          </div>
          
          {isLoading && !currentConversation && (
            <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
              <Loader2 className="w-4 h-4 animate-spin" />
              Loading...
            </div>
          )}
        </div>
      </div>
      
      {/* Messages */}
      <MessageList messages={messages} isStreaming={isStreaming} />
      
      {/* Error display */}
      {error && (
        <div className="max-w-4xl mx-auto mb-4 mx-4">
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200 px-4 py-3 rounded-lg">
            <p className="text-sm font-medium">Error: {error}</p>
          </div>
        </div>
      )}
      
      {/* Input */}
      <MessageInput
        onSendMessage={handleSendMessage}
        onStop={stopStreaming}
        disabled={!currentConversation || isLoading}
        isStreaming={isStreaming}
      />
    </div>
  )
}
