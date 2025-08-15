# Path: ui_launchers/web_ui/src/components/chat/MessageList.tsx

'use client';

import React, { useMemo, useCallback, useRef, useEffect } from 'react';
import { FixedSizeList as List } from 'react-window';
import { motion, AnimatePresence } from 'framer-motion';
import { ChatMessage } from '@/lib/types';
import { MessageBubble } from './MessageBubble';
import { useTelemetry } from '@/hooks/use-telemetry';
import { usePerformanceMarks } from '@/hooks/use-performance-marks';

interface MessageListProps {
  messages: ChatMessage[];
  isLoading?: boolean;
  onMessageAction?: (messageId: string, action: MessageAction) => void;
  virtualizationThreshold?: number;
  className?: string;
}

interface MessageAction {
  type: 'copy' | 'retry' | 'edit' | 'delete' | 'rate';
  payload?: any;
}

const ITEM_HEIGHT = 120; // Estimated height per message
const OVERSCAN_COUNT = 5; // Number of items to render outside visible area

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  isLoading = false,
  onMessageAction,
  virtualizationThreshold = 100,
  className = ''
}) => {
  const listRef = useRef<List>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const { track } = useTelemetry();
  const { markRender } = usePerformanceMarks();

  // Track performance metrics
  useEffect(() => {
    markRender('message-list', messages.length);
  }, [messages.length, markRender]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (messages.length > 0 && listRef.current) {
      listRef.current.scrollToItem(messages.length - 1, 'end');
    }
  }, [messages.length]);

  // Handle message actions with telemetry
  const handleMessageAction = useCallback((messageId: string, action: MessageAction) => {
    track('message_action', {
      messageId,
      action: action.type,
      messageCount: messages.length
    });
    
    onMessageAction?.(messageId, action);
  }, [onMessageAction, track, messages.length]);

  // Memoized message renderer for virtualization
  const MessageItem = useCallback(({ index, style }: { index: number; style: React.CSSProperties }) => {
    const message = messages[index];
    if (!message) return null;

    return (
      <div style={style}>
        <MessageBubble
          message={message}
          onAction={(action) => handleMessageAction(message.id, action)}
          isLast={index === messages.length - 1}
        />
      </div>
    );
  }, [messages, handleMessageAction]);

  // Determine if virtualization should be used
  const shouldVirtualize = messages.length > virtualizationThreshold;

  // Memoized message list for non-virtualized rendering
  const messageElements = useMemo(() => {
    if (shouldVirtualize) return null;
    
    return messages.map((message, index) => (
      <motion.div
        key={message.id}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        transition={{ duration: 0.3, delay: index * 0.05 }}
      >
        <MessageBubble
          message={message}
          onAction={(action) => handleMessageAction(message.id, action)}
          isLast={index === messages.length - 1}
        />
      </motion.div>
    ));
  }, [messages, shouldVirtualize, handleMessageAction]);

  if (messages.length === 0) {
    return (
      <div className={`flex items-center justify-center h-full ${className}`}>
        <div className="text-center text-muted-foreground">
          <div className="text-lg font-medium mb-2">No messages yet</div>
          <div className="text-sm">Start a conversation to see messages here</div>
        </div>
      </div>
    );
  }

  return (
    <div 
      ref={containerRef}
      className={`flex-1 overflow-hidden ${className}`}
      role="log"
      aria-label="Chat messages"
      aria-live="polite"
    >
      {shouldVirtualize ? (
        <List
          ref={listRef}
          height={containerRef.current?.clientHeight || 400}
          itemCount={messages.length}
          itemSize={ITEM_HEIGHT}
          overscanCount={OVERSCAN_COUNT}
          className="scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-transparent"
        >
          {MessageItem}
        </List>
      ) : (
        <div className="space-y-4 p-4 overflow-y-auto h-full scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-transparent">
          <AnimatePresence mode="popLayout">
            {messageElements}
          </AnimatePresence>
          
          {isLoading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex items-center justify-center py-4"
            >
              <div className="flex items-center gap-2 text-muted-foreground">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current" />
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