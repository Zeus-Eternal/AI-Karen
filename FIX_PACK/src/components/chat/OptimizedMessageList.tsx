import React, { memo, useMemo, useCallback, useRef, useEffect } from 'react';
import { FixedSizeList as List, ListChildComponentProps } from 'react-window';
import { ChatMessage } from '@/lib/types';
import { OptimizedMessageBubble } from './OptimizedMessageBubble';
import { useStableCallback, useStableMemo } from '../../utils/memoization';

interface MessageListProps {
  messages: ChatMessage[];
  onMessageAction?: (messageId: string, action: any) => void;
  height?: number;
  className?: string;
  virtualizationThreshold?: number;
  itemHeight?: number;
}

interface MessageAction {
  type: 'copy' | 'retry' | 'edit' | 'delete' | 'rate';
  payload?: any;
}

// Memoized message item for virtualization
const VirtualizedMessageItem = memo<ListChildComponentProps>(({ index, style, data }) => {
  const { messages, onMessageAction } = data;
  const message = messages[index];
  const isLast = index === messages.length - 1;

  const handleAction = useStableCallback((action: MessageAction) => {
    onMessageAction?.(message.id, action);
  }, [message.id, onMessageAction]);

  return (
    <div style={style}>
      <div className="px-4 py-2">
        <OptimizedMessageBubble
          message={message}
          onAction={handleAction}
          isLast={isLast}
        />
      </div>
    </div>
  );
});

VirtualizedMessageItem.displayName = 'VirtualizedMessageItem';

// Non-virtualized message list for smaller lists
const SimpleMessageList = memo<{
  messages: ChatMessage[];
  onMessageAction?: (messageId: string, action: any) => void;
  className?: string;
}>(({ messages, onMessageAction, className }) => {
  const handleMessageAction = useStableCallback((messageId: string, action: MessageAction) => {
    onMessageAction?.(messageId, action);
  }, [onMessageAction]);

  return (
    <div className={`space-y-4 ${className || ''}`}>
      {messages.map((message, index) => (
        <OptimizedMessageBubble
          key={message.id}
          message={message}
          onAction={(action) => handleMessageAction(message.id, action)}
          isLast={index === messages.length - 1}
        />
      ))}
    </div>
  );
});

SimpleMessageList.displayName = 'SimpleMessageList';

// Main optimized message list component
const OptimizedMessageList: React.FC<MessageListProps> = memo(({
  messages,
  onMessageAction,
  height = 600,
  className = '',
  virtualizationThreshold = 100,
  itemHeight = 120
}) => {
  const listRef = useRef<List>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Determine if virtualization should be used
  const shouldVirtualize = useStableMemo(() => {
    return messages.length > virtualizationThreshold;
  }, [messages.length, virtualizationThreshold]);

  // Memoized data for virtualized list
  const virtualizedData = useStableMemo(() => ({
    messages,
    onMessageAction
  }), [messages, onMessageAction]);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = useStableCallback(() => {
    if (shouldVirtualize && listRef.current) {
      listRef.current.scrollToItem(messages.length - 1, 'end');
    } else if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [shouldVirtualize, messages.length]);

  // Effect to scroll to bottom on new messages
  useEffect(() => {
    const lastMessage = messages[messages.length - 1];
    if (lastMessage && lastMessage.role === 'assistant') {
      // Small delay to ensure DOM is updated
      const timeoutId = setTimeout(scrollToBottom, 100);
      return () => clearTimeout(timeoutId);
    }
  }, [messages, scrollToBottom]);

  // Memoized container classes
  const containerClasses = useStableMemo(() => {
    return `message-list-container ${className}`;
  }, [className]);

  // Handle message actions with stable callback
  const handleMessageAction = useStableCallback((messageId: string, action: MessageAction) => {
    onMessageAction?.(messageId, action);
  }, [onMessageAction]);

  if (shouldVirtualize) {
    return (
      <div className={containerClasses} style={{ height }}>
        <List
          ref={listRef}
          height={height}
          itemCount={messages.length}
          itemSize={itemHeight}
          itemData={virtualizedData}
          overscanCount={5} // Render 5 extra items for smooth scrolling
          className="virtualized-message-list"
        >
          {VirtualizedMessageItem}
        </List>
      </div>
    );
  }

  return (
    <div 
      ref={containerRef}
      className={`${containerClasses} overflow-y-auto`}
      style={{ height }}
    >
      <SimpleMessageList
        messages={messages}
        onMessageAction={handleMessageAction}
        className="p-4"
      />
    </div>
  );
}, (prevProps, nextProps) => {
  // Custom comparison for better memoization
  if (prevProps.messages.length !== nextProps.messages.length) {
    return false;
  }

  // Check if any message has changed
  for (let i = 0; i < prevProps.messages.length; i++) {
    const prevMessage = prevProps.messages[i];
    const nextMessage = nextProps.messages[i];
    
    if (
      prevMessage.id !== nextMessage.id ||
      prevMessage.content !== nextMessage.content ||
      prevMessage.status !== nextMessage.status ||
      prevMessage.timestamp.getTime() !== nextMessage.timestamp.getTime()
    ) {
      return false;
    }
  }

  return (
    prevProps.height === nextProps.height &&
    prevProps.className === nextProps.className &&
    prevProps.virtualizationThreshold === nextProps.virtualizationThreshold &&
    prevProps.itemHeight === nextProps.itemHeight &&
    prevProps.onMessageAction === nextProps.onMessageAction
  );
});

OptimizedMessageList.displayName = 'OptimizedMessageList';

export { OptimizedMessageList };
export default OptimizedMessageList;