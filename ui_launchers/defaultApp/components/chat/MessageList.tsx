/**
 * MessageList Component
 * Displays messages with markdown rendering and code syntax highlighting
 */

'use client'

import { useEffect, useRef } from 'react'
import { User, Bot } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import type { Message } from '@/types/chat'

interface MessageListProps {
  messages: Message[]
  isStreaming?: boolean
}

export function MessageList({ messages, isStreaming = false }: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  /**
   * Auto-scroll to bottom when new messages arrive
   */
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isStreaming])
  
  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center max-w-md">
          <Bot className="w-16 h-16 mx-auto text-gray-400 dark:text-gray-600 mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
            Start a conversation
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            Send a message to begin chatting with AI-Karen
          </p>
        </div>
      </div>
    )
  }
  
  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-4xl mx-auto">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        {isStreaming && (
          <div className="flex gap-4 p-6">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="font-semibold text-gray-900 dark:text-gray-100">AI-Karen</span>
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                  <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse delay-100" />
                  <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse delay-200" />
                </div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>
  )
}

/**
 * Individual message bubble component
 */
function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user'
  
  return (
    <div className={`flex gap-4 p-6 ${isUser ? 'bg-gray-50 dark:bg-gray-800/50' : ''}`}>
      <div className="flex-shrink-0">
        {isUser ? (
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center">
            <User className="w-5 h-5 text-white" />
          </div>
        ) : (
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
            <Bot className="w-5 h-5 text-white" />
          </div>
        )}
      </div>
      
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-semibold text-gray-900 dark:text-gray-100">
            {isUser ? 'You' : 'AI-Karen'}
          </span>
          <span className="text-xs text-gray-500 dark:text-gray-400">
            {new Date(message.timestamp).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </span>
        </div>
        
        <div className="prose prose-gray dark:prose-invert max-w-none">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              code({ className, children, ...props }: any) {
                const match = /language-(\w+)/.exec(className || '')
                const language = match ? match[1] : ''
                const inline = !className
                
                return !inline && language ? (
                  <div className="relative group">
                    <SyntaxHighlighter
                      style={oneDark}
                      language={language}
                      PreTag="div"
                      className="rounded-lg"
                      {...props}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                    <button
                      onClick={() => navigator.clipboard.writeText(String(children))}
                      className="absolute top-2 right-2 px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600 text-white rounded opacity-0 group-hover:opacity-100 transition-opacity"
                      aria-label="Copy code"
                    >
                      Copy
                    </button>
                  </div>
                ) : (
                  <code
                    className="px-1.5 py-0.5 rounded bg-gray-200 dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-sm"
                    {...props}
                  >
                    {children}
                  </code>
                )
              },
              p({ children }) {
                return <p className="mb-4 last:mb-0">{children}</p>
              },
              ul({ children }) {
                return <ul className="list-disc list-inside mb-4">{children}</ul>
              },
              ol({ children }) {
                return <ol className="list-decimal list-inside mb-4">{children}</ol>
              },
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>
        
        {message.metadata?.attachments && message.metadata.attachments.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {message.metadata.attachments.map((attachment) => (
              <div
                key={attachment.id}
                className="flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-200 dark:bg-gray-800 text-sm"
              >
                <span className="font-medium">{attachment.name}</span>
                <span className="text-gray-500 dark:text-gray-400">
                  ({(attachment.size / 1024).toFixed(1)} KB)
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
