/**
 * MessageInput Component
 * Auto-expanding textarea for sending messages
 */

'use client'

import { useState, useRef, useEffect, KeyboardEvent } from 'react'
import { Send, StopCircle } from 'lucide-react'

interface MessageInputProps {
  onSendMessage: (message: string) => void
  onStop?: () => void
  disabled?: boolean
  isStreaming?: boolean
  placeholder?: string
}

export function MessageInput({
  onSendMessage,
  onStop,
  disabled = false,
  isStreaming = false,
  placeholder = 'Type your message...',
}: MessageInputProps) {
  const [message, setMessage] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  
  /**
   * Auto-resize textarea based on content
   */
  useEffect(() => {
    const textarea = textareaRef.current
    if (!textarea) return
    
    textarea.style.height = 'auto'
    const newHeight = Math.min(textarea.scrollHeight, 200) // Max height of 200px
    textarea.style.height = `${newHeight}px`
  }, [message])
  
  /**
   * Handle keyboard shortcuts
   * - Enter: Send message
   * - Shift + Enter: New line
   */
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }
  
  /**
   * Send message or stop streaming
   */
  const handleSend = () => {
    if (isStreaming) {
      onStop?.()
      return
    }
    
    const trimmed = message.trim()
    if (!trimmed || disabled) return
    
    onSendMessage(trimmed)
    setMessage('')
    
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }
  
  return (
    <div className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
      <div className="max-w-4xl mx-auto flex items-end gap-3">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled || isStreaming}
            rows={1}
            className="w-full resize-none rounded-lg border border-gray-300 dark:border-gray-600 bg-transparent px-4 py-3 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:border-blue-500 dark:focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:focus:ring-blue-400/20 disabled:opacity-50 disabled:cursor-not-allowed"
            style={{ minHeight: '48px', maxHeight: '200px' }}
          />
        </div>
        
        <button
          onClick={handleSend}
          disabled={disabled || (!message.trim() && !isStreaming)}
          className={`
            flex items-center justify-center rounded-lg px-4 py-3 font-medium transition-colors
            ${
              isStreaming
                ? 'bg-red-500 hover:bg-red-600 text-white'
                : 'bg-blue-500 hover:bg-blue-600 text-white disabled:bg-gray-300 dark:disabled:bg-gray-700 disabled:text-gray-500 dark:disabled:text-gray-400'
            }
          `}
          aria-label={isStreaming ? 'Stop generation' : 'Send message'}
        >
          {isStreaming ? (
            <>
              <StopCircle className="w-5 h-5" />
              <span className="sr-only">Stop</span>
            </>
          ) : (
            <>
              <Send className="w-5 h-5" />
              <span className="sr-only">Send</span>
            </>
          )}
        </button>
      </div>
      
      <div className="max-w-4xl mx-auto mt-2 text-xs text-gray-500 dark:text-gray-400">
        Press <kbd className="px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 font-mono">Enter</kbd> to send, <kbd className="px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 font-mono">Shift + Enter</kbd> for new line
      </div>
    </div>
  )
}
