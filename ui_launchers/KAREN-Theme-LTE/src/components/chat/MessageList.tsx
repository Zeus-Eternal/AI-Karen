/**
 * Message List Component
 * Scrollable message display area with virtual scrolling
 */

import React, { useRef, useEffect, useCallback, useMemo, useState } from 'react';
import { cn } from '@/lib/utils';
import { ChatMessage } from '@/types/chat';
import { MessageBubble } from './MessageBubble';
import { TypingIndicator } from './TypingIndicator';
import { Button } from '@/components/ui/button';
import { ChevronDown, AlertCircle } from 'lucide-react';

export interface MessageListProps {
  messages: ChatMessage[];
  isLoading?: boolean;
  isTyping?: boolean;
  streamingContent?: string;
  error?: string | null;
  className?: string;
  onRetry?: () => void;
  autoScroll?: boolean;
  showAvatar?: boolean;
  showTimestamp?: boolean;
  showMetadata?: boolean;
  showReactions?: boolean;
  showActions?: boolean;
}

export function MessageList({
  messages,
  isLoading = false,
  isTyping = false,
  streamingContent,
  error,
  className,
  onRetry,
  autoScroll = true,
  showAvatar = true,
  showTimestamp = true,
  showMetadata = true,
  showReactions = true,
  showActions = true,
}: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [showScrollButton, setShowScrollButton] = useState(false);
  const [isAtBottom, setIsAtBottom] = useState(true);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = useCallback(() => {
    if (messagesEndRef.current && autoScroll) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [autoScroll]);

  // Check if user is at bottom of the message list
  const checkIfAtBottom = useCallback(() => {
    if (!containerRef.current) return;
    
    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    const threshold = 100; // pixels from bottom to consider "at bottom"
    const atBottom = scrollHeight - scrollTop - clientHeight < threshold;
    
    setIsAtBottom(atBottom);
    setShowScrollButton(!atBottom && scrollHeight > clientHeight);
  }, []);

  // Handle scroll events
  const handleScroll = useCallback(() => {
    checkIfAtBottom();
  }, [checkIfAtBottom]);

  // Scroll to bottom on new messages if user was already at bottom
  useEffect(() => {
    if (isAtBottom && autoScroll) {
      scrollToBottom();
    }
  }, [messages, isAtBottom, autoScroll, scrollToBottom]);

  // Initial scroll check
  useEffect(() => {
    checkIfAtBottom();
  }, [checkIfAtBottom]);

  // Group messages by date for better organization
  const groupedMessages = useMemo(() => {
    const groups: { [date: string]: ChatMessage[] } = {};
    
    messages.forEach(message => {
      const date = new Date(message.timestamp).toDateString();
      if (!groups[date]) {
        groups[date] = [];
      }
      groups[date].push(message);
    });
    
    return groups;
  }, [messages]);

  // Format date for group headers
  const formatDateHeader = (dateString: string) => {
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    } else {
      return new Intl.DateTimeFormat('en-US', {
        weekday: 'long',
        month: 'short',
        day: 'numeric'
      }).format(date);
    }
  };

  // Create a streaming message if content is provided
  const streamingMessage = useMemo(() => {
    if (!streamingContent) return null;
    
    return {
      id: 'streaming-message',
      role: 'assistant' as const,
      content: streamingContent,
      timestamp: new Date(),
      status: 'processing' as any,
    } as ChatMessage;
  }, [streamingContent]);

  return (
    <div
      ref={containerRef}
      onScroll={handleScroll}
      className={cn(
        'flex flex-col h-full overflow-y-auto bg-black/20 backdrop-blur-sm',
        className
      )}
    >
      {/* Messages */}
      <div className="flex-1 p-4 space-y-6">
        {Object.entries(groupedMessages).map(([date, dateMessages]) => (
          <div key={date} className="space-y-4">
            {/* Date header */}
            <div className="flex items-center justify-center">
              <div className="bg-purple-500/20 backdrop-blur-sm rounded-full px-3 py-1 text-xs text-purple-300 border border-purple-500/30">
                {formatDateHeader(date)}
              </div>
            </div>
            
            {/* Messages for this date */}
            <div className="space-y-4">
              {dateMessages.map((message, index) => (
                <MessageBubble
                  key={message.id}
                  message={message}
                  showAvatar={showAvatar}
                  showTimestamp={showTimestamp}
                  showMetadata={showMetadata}
                  showReactions={showReactions}
                  showActions={showActions}
                />
              ))}
            </div>
          </div>
        ))}
        
        {/* Streaming message */}
        {streamingMessage && (
          <MessageBubble
            message={streamingMessage}
            showAvatar={showAvatar}
            showTimestamp={false}
            showMetadata={false}
            showReactions={false}
            showActions={false}
          />
        )}
        
        {/* Typing indicator */}
        {isTyping && (
          <TypingIndicator />
        )}
        
        {/* Error message */}
        {error && (
          <div className="flex flex-col items-center justify-center p-6 bg-red-500/10 border border-red-500/30 rounded-lg">
            <AlertCircle className="h-8 w-8 text-red-400 mb-2" />
            <p className="text-red-400 text-center mb-4">{error}</p>
            {onRetry && (
              <Button
                onClick={onRetry}
                variant="outline"
                size="sm"
                className="border-red-500/30 text-red-400 hover:bg-red-500/10"
              >
                Retry
              </Button>
            )}
          </div>
        )}
        
        {/* Loading indicator */}
        {isLoading && (
          <div className="flex items-center justify-center p-6">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-purple-400 rounded-full animate-pulse"></div>
              <div className="w-2 h-2 bg-purple-400 rounded-full animate-pulse delay-75"></div>
              <div className="w-2 h-2 bg-purple-400 rounded-full animate-pulse delay-150"></div>
            </div>
          </div>
        )}
        
        {/* Scroll anchor */}
        <div ref={messagesEndRef} />
      </div>
      
      {/* Scroll to bottom button */}
      {showScrollButton && (
        <div className="absolute bottom-4 right-4 z-10">
          <Button
            onClick={scrollToBottom}
            size="icon"
            className="bg-purple-600 hover:bg-purple-700 text-white rounded-full shadow-lg border border-purple-500/30"
            aria-label="Scroll to bottom"
          >
            <ChevronDown className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  );
}