# Path: ui_launchers/web_ui/src/components/chat/MessageList.tsx

'use client';

import React, { useMemo, useCallback, useRef, useEffect, useState } from 'react';
import { VariableSizeList as List, ListChildComponentProps } from 'react-window';
import { motion, AnimatePresence } from 'framer-motion';
import { ChatMessage } from '@/lib/types';
import { MessageBubble } from './MessageBubble';
import { useTelemetry } from '@/hooks/use-telemetry';
import { usePerformanceMarks } from '@/hooks/use-performance-marks';
import { useScreenReader, chatAriaPatterns, createAriaLabel } from '@/hooks/use-screen-reader';

interface MessageListProps {
  messages: ChatMessage[];
  isLoading?: boolean;
  onMessageAction?: (messageId: string, action: MessageAction) => void;
  virtualizationThreshold?: number;
  className?: string;
  autoScroll?: boolean;
  smoothScrolling?: boolean;
}

interface MessageAction {
  type: 'copy' | 'retry' | 'edit' | 'delete' | 'rate';
  payload?: any;
}

const BASE_ITEM_HEIGHT = 80; // Base height per message
const OVERSCAN_COUNT = 3; // Number of items to render outside visible area
const SCROLL_DEBOUNCE_MS = 100;

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  isLoading = false,
  onMessageAction,
  virtualizationThreshold = 100,
  className = '',
  autoScroll = true,
  smoothScrolling = true
}) => {
  const listRef = useRef<List>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const scrollTimeoutRef = useRef<NodeJS.Timeout>();
  const itemHeightsRef = useRef<Map<number, number>>(new Map());
  const [isUserScrolling, setIsUserScrolling] = useState(false);
  const [containerHeight, setContainerHeight] = useState(400);
  
  const { track } = useTelemetry();
  const { markRender } = usePerformanceMarks();
  
  // Screen reader support
  const { announce, setStatus, clear } = useScreenReader({
    announceOnMount: messages.length > 0 ? `Conversation loaded with ${messages.length} messages` : undefined
  });

  // Track performance metrics
  useEffect(() => {
    markRender('message-list', messages.length);
  }, [messages.length, markRender]);

  // Announce new messages to screen readers
  useEffect(() => {
    if (messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      const isNewMessage = lastMessage && lastMessage.timestamp && 
        Date.now() - new Date(lastMessage.timestamp).getTime() < 5000; // Within last 5 seconds
      
      if (isNewMessage) {
        const messagePreview = lastMessage.content.length > 100 
          ? lastMessage.content.substring(0, 100) + '...'
          : lastMessage.content;
        
        announce(
          `New message from ${lastMessage.role}: ${messagePreview}`,
          lastMessage.role === 'assistant' ? 'polite' : 'assertive'
        );
      }
    }
  }, [messages, announce]);

  // Announce loading state changes
  useEffect(() => {
    if (isLoading) {
      setStatus('Loading messages...');
    } else {
      setStatus(`${messages.length} messages loaded`);
    }
  }, [isLoading, messages.length, setStatus]);

  // Update container height on resize
  useEffect(() => {
    const updateHeight = () => {
      if (containerRef.current) {
        setContainerHeight(containerRef.current.clientHeight);
      }
    };

    const resizeObserver = new ResizeObserver(updateHeight);
    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }

    return () => resizeObserver.disconnect();
  }, []);

  // Auto-scroll to bottom when new messages arrive (with smooth scrolling)
  useEffect(() => {
    if (messages.length > 0 && listRef.current && autoScroll && !isUserScrolling) {
      if (smoothScrolling) {
        // Smooth scroll to bottom
        const scrollToBottom = () => {
          listRef.current?.scrollToItem(messages.length - 1, 'end');
        };
        
        // Use requestAnimationFrame for smooth scrolling
        requestAnimationFrame(scrollToBottom);
      } else {
        listRef.current.scrollToItem(messages.length - 1, 'end');
      }
    }
  }, [messages.length, autoScroll, isUserScrolling, smoothScrolling]);

  // Handle scroll events to detect user scrolling
  const handleScroll = useCallback(() => {
    setIsUserScrolling(true);
    
    if (scrollTimeoutRef.current) {
      clearTimeout(scrollTimeoutRef.current);
    }
    
    scrollTimeoutRef.current = setTimeout(() => {
      setIsUserScrolling(false);
    }, SCROLL_DEBOUNCE_MS);
  }, []);

  // Handle message actions with telemetry
  const handleMessageAction = useCallback((messageId: string, action: MessageAction) => {
    track('message_action', {
      messageId,
      action: action.type,
      messageCount: messages.length
    });
    
    onMessageAction?.(messageId, action);
  }, [onMessageAction, track, messages.length]);

  // Calculate dynamic item height based on content
  const getItemHeight = useCallback((index: number) => {
    const cachedHeight = itemHeightsRef.current.get(index);
    if (cachedHeight) return cachedHeight;

    const message = messages[index];
    if (!message) return BASE_ITEM_HEIGHT;

    // Estimate height based on content length and type
    const contentLines = Math.ceil(message.content.length / 80); // ~80 chars per line
    const baseHeight = message.role === 'user' ? 60 : 80; // User messages are typically shorter
    const contentHeight = Math.max(1, contentLines) * 20; // ~20px per line
    const paddingHeight = 40; // Padding and margins
    
    const estimatedHeight = baseHeight + contentHeight + paddingHeight;
    
    // Cache the height
    itemHeightsRef.current.set(index, estimatedHeight);
    
    return estimatedHeight;
  }, [messages]);

  // Memoized message renderer for virtualization
  const MessageItem = useCallback(({ index, style }: ListChildComponentProps) => {
    const message = messages[index];
    if (!message) return null;

    const timestamp = message.timestamp ? new Date(message.timestamp).toLocaleTimeString() : 'Unknown time';
    const ariaProps = chatAriaPatterns.message(message.role, timestamp, index, messages.length);

    return (
      <div style={style}>
        <div 
          style={{ padding: '8px 16px' }}
          {...ariaProps}
          tabIndex={0}
          onFocus={() => {
            announce(`Focused on message ${index + 1} of ${messages.length} from ${message.role}`);
          }}
        >
          <MessageBubble
            message={message}
            onAction={(action) => handleMessageAction(message.id, action)}
            isLast={index === messages.length - 1}
          />
        </div>
      </div>
    );
  }, [messages, handleMessageAction, announce]);

  // Determine if virtualization should be used
  const shouldVirtualize = messages.length > virtualizationThreshold;

  // Memoized message list for non-virtualized rendering
  const messageElements = useMemo(() => {
    if (shouldVirtualize) return null;
    
    return messages.map((message, index) => {
      const timestamp = message.timestamp ? new Date(message.timestamp).toLocaleTimeString() : 'Unknown time';
      const ariaProps = chatAriaPatterns.message(message.role, timestamp, index, messages.length);
      
      return (
        <motion.div
          key={message.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.3, delay: index * 0.05 }}
          {...ariaProps}
          tabIndex={0}
          onFocus={() => {
            announce(`Focused on message ${index + 1} of ${messages.length} from ${message.role}`);
          }}
        >
          <MessageBubble
            message={message}
            onAction={(action) => handleMessageAction(message.id, action)}
            isLast={index === messages.length - 1}
          />
        </motion.div>
      );
    });
  }, [messages, shouldVirtualize, handleMessageAction, announce]);

  if (messages.length === 0) {
    return (
      <div 
        className={`flex items-center justify-center h-full ${className}`}
        role="region"
        aria-label="Empty conversation"
        aria-describedby="empty-state-description"
      >
        <div className="text-center text-muted-foreground">
          <div className="text-lg font-medium mb-2">No messages yet</div>
          <div id="empty-state-description" className="text-sm">
            Start a conversation to see messages here
          </div>
        </div>
      </div>
    );
  }

  // Cleanup scroll timeout on unmount
  useEffect(() => {
    return () => {
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, []);

  return (
    <div 
      ref={containerRef}
      className={`flex-1 overflow-hidden ${className}`}
      {...chatAriaPatterns.messageList}
      aria-describedby="message-list-description"
    >
      <div id="message-list-description" className="sr-only">
        Conversation with {messages.length} messages. Use arrow keys to navigate between messages.
        {isLoading && ' Loading additional messages.'}
      </div>
      {shouldVirtualize ? (
        <List
          ref={listRef}
          height={containerHeight}
          width="100%"
          itemCount={messages.length}
          itemSize={getItemHeight}
          overscanCount={OVERSCAN_COUNT}
          onScroll={handleScroll}
          className="scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-transparent"
          style={{
            scrollBehavior: smoothScrolling ? 'smooth' : 'auto'
          }}
          role="listbox"
          aria-label={`Message list with ${messages.length} messages`}
        >
          {MessageItem}
        </List>
      ) : (
        <div 
          className="space-y-4 p-4 overflow-y-auto h-full scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-transparent"
          onScroll={handleScroll}
          style={{
            scrollBehavior: smoothScrolling ? 'smooth' : 'auto'
          }}
        >
          <AnimatePresence mode="popLayout">
            {messageElements}
          </AnimatePresence>
          
          {isLoading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex items-center justify-center py-4"
              role="status"
              aria-live="polite"
              aria-label="Loading messages"
            >
              <div className="flex items-center gap-2 text-muted-foreground">
                <div 
                  className="animate-spin rounded-full h-4 w-4 border-b-2 border-current"
                  aria-hidden="true"
                />
                <span>Loading messages...</span>
              </div>
            </motion.div>
          )}
        </div>
      )}
    </div>
  );
};

export default MessageList;