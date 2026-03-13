import React, { useState, useEffect, useRef, useCallback } from 'react';
import { MessageBubbleComponent } from './MessageBubbleComponent';
import { DataOptimizer } from '../../utils/memory-optimization';
import { useIntersectionObserver } from '../../hooks/useIntersectionObserver';

interface Theme {
  colors: {
    primary: string;
    secondary: string;
    background: string;
    surface: string;
    text: string;
    textSecondary: string;
    border: string;
    error: string;
    warning: string;
    success: string;
    info: string;
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    xxl: string;
  };
  typography: {
    fontFamily: string;
    fontSize: {
      xs: string;
      sm: string;
      base: string;
      lg: string;
      xl: string;
      xxl: string;
    };
    fontWeight: {
      light: number;
      normal: number;
      medium: number;
      semibold: number;
      bold: number;
    };
  };
  borderRadius: string;
  shadows: {
    sm: string;
    md: string;
    lg: string;
  };
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  aiData?: {
    keywords?: string[];
    knowledgeGraphInsights?: string;
    confidence?: number;
    reasoning?: string;
  };
  shouldAutoPlay?: boolean;
  attachments?: Array<{
    id: string;
    name: string;
    size: string;
    type: string;
    url?: string;
  }>;
}

interface VirtualizedMessageListProps {
  messages: ChatMessage[];
  theme: Theme;
  className?: string;
  onCopyMessage?: (messageId: string) => void;
  onRetryMessage?: (messageId: string) => void;
  onDeleteMessage?: (messageId: string) => void;
  showTimestamp?: boolean;
  showActions?: boolean;
  showAiData?: boolean;
  showConfidence?: boolean;
  showKeywords?: boolean;
  showReasoning?: boolean;
  highlightedMessageId?: string;
  pageSize?: number;
  initialPage?: number;
  loadMoreThreshold?: number;
  onLoadMore?: () => void;
  isLoadingMore?: boolean;
  estimatedItemHeight?: number;
  overscanCount?: number;
}

interface MessageItem {
  id: string;
  index: number;
  message: ChatMessage;
}

/**
 * Virtualized message list component for memory-efficient rendering of large chat histories
 */
export const VirtualizedMessageList: React.FC<VirtualizedMessageListProps> = ({
  messages,
  theme,
  className = '',
  onCopyMessage,
  onRetryMessage,
  onDeleteMessage,
  showTimestamp = true,
  showActions = true,
  showAiData = false,
  showConfidence = false,
  showKeywords = false,
  showReasoning = false,
  highlightedMessageId,
  pageSize = 50,
  initialPage = 1,
  loadMoreThreshold = 10,
  onLoadMore,
  isLoadingMore = false,
  estimatedItemHeight = 200,
  overscanCount = 5
}) => {
  const [currentPage, setCurrentPage] = useState(initialPage);
  const [visibleItems, setVisibleItems] = useState<MessageItem[]>([]);
  const [totalHeight, setTotalHeight] = useState(0);
  const [scrollTop, setScrollTop] = useState(0);
  const [isScrolling, setIsScrolling] = useState(false);
  
  const containerRef = useRef<HTMLDivElement>(null);
  const scrollTimeoutRef = useRef<number | null>(null);
  
  // Calculate total number of pages
  const totalPages = Math.ceil(messages.length / pageSize);
  
  // Calculate visible range based on scroll position
  const calculateVisibleRange = useCallback(() => {
    if (!containerRef.current) return { start: 0, end: pageSize };
    
    const containerHeight = containerRef.current.clientHeight;
    const startIndex = Math.floor(scrollTop / estimatedItemHeight);
    const endIndex = Math.min(
      startIndex + Math.ceil(containerHeight / estimatedItemHeight) + overscanCount * 2,
      messages.length - 1
    );
    
    return {
      start: Math.max(0, startIndex - overscanCount),
      end: endIndex
    };
  }, [scrollTop, estimatedItemHeight, messages.length, overscanCount]);
  
  // Update visible items based on scroll position
  useEffect(() => {
    const { start, end } = calculateVisibleRange();
    
    const newVisibleItems = messages
      .slice(start, end + 1)
      .map((message, index) => ({
        id: message.id,
        index: start + index,
        message
      }));
    
    setVisibleItems(newVisibleItems);
    setTotalHeight(messages.length * estimatedItemHeight);
  }, [messages, calculateVisibleRange, estimatedItemHeight]);
  
  // Handle scroll events
  const handleScroll = useCallback(() => {
    if (!containerRef.current) return;
    
    const newScrollTop = containerRef.current.scrollTop;
    setScrollTop(newScrollTop);
    
    // Set scrolling state
    setIsScrolling(true);
    
    // Clear previous timeout
    if (scrollTimeoutRef.current) {
      clearTimeout(scrollTimeoutRef.current);
    }
    
    // Set a timeout to detect when scrolling stops
    scrollTimeoutRef.current = window.setTimeout(() => {
      setIsScrolling(false);
    }, 150);
    
    // Check if we need to load more messages
    if (
      onLoadMore &&
      !isLoadingMore &&
      currentPage < totalPages &&
      newScrollTop + containerRef.current.clientHeight >= 
        containerRef.current.scrollHeight - loadMoreThreshold * estimatedItemHeight
    ) {
      onLoadMore();
      setCurrentPage(prev => prev + 1);
    }
  }, [onLoadMore, isLoadingMore, currentPage, totalPages, loadMoreThreshold, estimatedItemHeight]);
  
  // Scroll to highlighted message
  useEffect(() => {
    if (highlightedMessageId && containerRef.current) {
      const messageIndex = messages.findIndex(msg => msg.id === highlightedMessageId);
      if (messageIndex !== -1) {
        containerRef.current.scrollTop = messageIndex * estimatedItemHeight;
      }
    }
  }, [highlightedMessageId, messages, estimatedItemHeight]);
  
  // Clean up timeout on unmount
  useEffect(() => {
    return () => {
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, []);
  
  // Render a message item with intersection observer for lazy loading
  const renderMessageItem = (item: MessageItem) => {
    const isHighlighted = item.message.id === highlightedMessageId;
    
    return (
      <div
        key={item.id}
        className={`virtualized-message-item ${isHighlighted ? 'highlighted' : ''}`}
        style={{
          position: 'absolute',
          top: item.index * estimatedItemHeight,
          width: '100%',
          height: estimatedItemHeight,
          opacity: isScrolling ? 0.8 : 1,
          transition: 'opacity 0.2s ease'
        }}
      >
        <MessageBubbleComponent
          message={item.message}
          theme={theme}
          onCopyMessage={onCopyMessage}
          onRetryMessage={onRetryMessage}
          onDeleteMessage={onDeleteMessage}
          showTimestamp={showTimestamp}
          showActions={showActions}
          showAiData={showAiData}
          showConfidence={showConfidence}
          showKeywords={showKeywords}
          showReasoning={showReasoning}
          isHighlighted={isHighlighted}
          ariaPosInSet={item.index + 1}
          ariaSetSize={messages.length}
        />
      </div>
    );
  };
  
  return (
    <div
      ref={containerRef}
      className={`virtualized-message-list ${className}`}
      style={{
        height: '100%',
        overflowY: 'auto',
        position: 'relative'
      }}
      onScroll={DataOptimizer.throttle(handleScroll, 16)} // Throttle to ~60fps
      role="list"
      aria-label="Messages"
      tabIndex={0}
      onKeyDown={(e) => {
        // Keyboard navigation for the virtualized list
        if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
          e.preventDefault();
          const direction = e.key === 'ArrowDown' ? 1 : -1;
          const newIndex = Math.max(0, Math.min(messages.length - 1,
            (visibleItems[visibleItems.length - 1]?.index || 0) + direction));
          
          const newMessage = messages[newIndex];
          if (newMessage) {
            const messageElement = document.getElementById(`message-${newMessage.id}`);
            if (messageElement) {
              messageElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
              messageElement.focus();
            }
          }
        }
      }}
    >
      {/* Total height container */}
      <div
        className="virtualized-spacer"
        style={{
          height: totalHeight,
          position: 'relative'
        }}
        aria-hidden="true"
      >
        {/* Visible items */}
        {visibleItems.map(renderMessageItem)}
      </div>
      
      {/* Loading more indicator */}
      {isLoadingMore && (
        <div
          className="virtualized-loading-more"
          style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            padding: theme.spacing.md,
            textAlign: 'center',
            backgroundColor: theme.colors.surface,
            borderTop: `1px solid ${theme.colors.border}`
          }}
          role="status"
          aria-live="polite"
          aria-busy="true"
        >
          Loading more messages...
        </div>
      )}
      
      {/* Scroll to bottom button */}
      {currentPage < totalPages && (
        <button
          className="virtualized-scroll-to-bottom"
          onClick={() => {
            if (containerRef.current) {
              containerRef.current.scrollTop = containerRef.current.scrollHeight;
            }
          }}
          style={{
            position: 'absolute',
            bottom: theme.spacing.lg,
            right: theme.spacing.lg,
            padding: `${theme.spacing.sm} ${theme.spacing.md}`,
            backgroundColor: theme.colors.primary,
            color: theme.colors.text,
            border: 'none',
            borderRadius: '50%',
            width: '48px',
            height: '48px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            boxShadow: theme.shadows.md,
            zIndex: 10
          }}
          aria-label="Scroll to bottom"
          tabIndex={0}
        >
          ↓
        </button>
      )}
    </div>
  );
};

export default VirtualizedMessageList;