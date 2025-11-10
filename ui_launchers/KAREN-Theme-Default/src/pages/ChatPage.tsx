import { useState, useRef, useEffect } from 'react'
import { Send, Loader2 } from 'lucide-react'
import { useMutation } from '@tanstack/react-query'
import { useChatStore } from '../stores/chatStore'
import { chatAPI } from '../lib/api'
import { cn, formatDate } from '../lib/utils'
import { useToast } from '@/hooks/use-toast'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export default function ChatPage() {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { toast } = useToast()

  const {
    conversations,
    currentConversationId,
    addMessage,
    createConversation,
  } = useChatStore()

  const currentConversation = conversations.find(c => c.id === currentConversationId)

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [currentConversation?.messages])

  // Create initial conversation
  useEffect(() => {
    if (conversations.length === 0) {
      createConversation()
    }
  }, [conversations.length, createConversation])

  const sendMessageMutation = useMutation({
    mutationFn: chatAPI.sendMessage,
    onSuccess: (data) => {
      if (currentConversationId) {
        addMessage(currentConversationId, {
          role: 'assistant',
          content: data.response,
          metadata: data.metadata,
        })
      }
    },
    onError: (error: any) => {
      toast({
        title: 'Failed to send message',
        description: error.response?.data?.detail || error.message,
        variant: 'destructive',
      })
    },
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || !currentConversationId) return

    const userMessage = input.trim()
    setInput('')

    // Add user message
    addMessage(currentConversationId, {
      role: 'user',
      content: userMessage,
    })

    // Send to API
    sendMessageMutation.mutate({
      message: userMessage,
      conversation_id: currentConversationId,
    })
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="h-16 border-b border-border px-6 flex items-center">
        <h2 className="text-xl font-semibold">
          {currentConversation?.title || 'New Conversation'}
        </h2>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
        {currentConversation?.messages?.map((message) => (
          <div
            key={message.id}
            className={cn(
              'flex',
              message.role === 'user' ? 'justify-end' : 'justify-start'
            )}
          >
            <div
              className={cn(
                'message-bubble',
                message.role === 'user' ? 'message-user' : 'message-ai'
              )}
            >
              {message.role === 'assistant' ? (
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  className="prose prose-sm dark:prose-invert max-w-none"
                >
                  {message.content}
                </ReactMarkdown>
              ) : (
                <p>{message.content}</p>
              )}
              <span className="text-xs opacity-70 mt-2 block">
                {formatDate(message.timestamp)}
              </span>
            </div>
          </div>
        ))}

        {sendMessageMutation.isPending && (
          <div className="flex justify-start">
            <div className="message-bubble message-ai">
              <Loader2 className="w-5 h-5 animate-spin" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form
        onSubmit={handleSubmit}
        className="border-t border-border px-6 py-4"
      >
        <div className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            className="flex-1 px-4 py-3 rounded-lg bg-background border border-input focus:outline-none focus:ring-2 focus:ring-ring"
            disabled={sendMessageMutation.isPending}
          />
          <button
            type="submit"
            disabled={!input.trim() || sendMessageMutation.isPending}
            className="px-6 py-3 bg-karen-primary text-white rounded-lg hover:bg-karen-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {sendMessageMutation.isPending ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
      </form>
    </div>
  )
}
