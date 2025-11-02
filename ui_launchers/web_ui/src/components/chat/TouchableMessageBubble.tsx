import React, { useState, useCallback } from 'react';
import { useSwipeable } from 'react-swipeable';
import { Copy, ThumbsUp, ThumbsDown, MoreHorizontal, Reply } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { MessageBubble, MessageBubbleProps } from './MessageBubble';

import { } from '@/components/ui/dropdown-menu';

interface TouchableMessageBubbleProps extends MessageBubbleProps {
  onSwipeLeft?: (messageId: string) => void;
  onSwipeRight?: (messageId: string) => void;
  onCopy?: (content: string) => void;
  onReply?: (messageId: string) => void;
  onRate?: (messageId: string, rating: 'up' | 'down') => void;
  enableSwipeActions?: boolean;
}

export const TouchableMessageBubble: React.FC<TouchableMessageBubbleProps> = ({
  message,
  onSwipeLeft,
  onSwipeRight,
  onCopy,
  onReply,
  onRate,
  enableSwipeActions = true,
  ...props
}) => {
  const [showActions, setShowActions] = useState(false);
  const [swipeOffset, setSwipeOffset] = useState(0);

  const handleSwipeLeft = useCallback(() => {
    if (onSwipeLeft) {
      onSwipeLeft(message.id);
    } else if (message.role === 'assistant' && onReply) {
      onReply(message.id);
    }
  }, [onSwipeLeft, onReply, message.id, message.role]);

  const handleSwipeRight = useCallback(() => {
    if (onSwipeRight) {
      onSwipeRight(message.id);
    } else if (onCopy) {
      onCopy(message.content);
    }
  }, [onSwipeRight, onCopy, message.id, message.content]);

  const swipeHandlers = useSwipeable({
    onSwipedLeft: enableSwipeActions ? handleSwipeLeft : undefined,
    onSwipedRight: enableSwipeActions ? handleSwipeRight : undefined,
    onSwiping: (eventData) => {
      if (enableSwipeActions) {
        setSwipeOffset(eventData.deltaX);
      }
    },
    onSwiped: () => {
      setSwipeOffset(0);
    },
    trackMouse: false,
    trackTouch: true,
    preventScrollOnSwipe: false,
    delta: 50, // Minimum distance to trigger swipe

  const isUser = message.role === 'user';

  return (
    <div
      {...swipeHandlers}
      className="relative touch-pan-y"
      style={{
        transform: enableSwipeActions ? `translateX(${Math.max(-100, Math.min(100, swipeOffset))}px)` : undefined,
        transition: swipeOffset === 0 ? 'transform 0.2s ease-out' : 'none',
      }}
      onTouchStart={() => setShowActions(true)}
      onTouchEnd={() => setTimeout(() => setShowActions(false), 1000)}
    >
      {/* Swipe Action Hints */}
      {enableSwipeActions && Math.abs(swipeOffset) > 20 && (
        <div className="absolute inset-0 flex items-center justify-between pointer-events-none z-10">
          {swipeOffset > 20 && (
            <div className="flex items-center space-x-2 ml-4 text-blue-500">
              <Copy className="h-5 w-5 " />
              <span className="text-sm font-medium md:text-base lg:text-lg">Copy</span>
            </div>
          )}
          {swipeOffset < -20 && (
            <div className="flex items-center space-x-2 mr-4 text-green-500 ml-auto">
              <span className="text-sm font-medium md:text-base lg:text-lg">Reply</span>
              <Reply className="h-5 w-5 " />
            </div>
          )}
        </div>
      )}

      {/* Message Content */}
      <div className="relative">
        <MessageBubble message={message} {...props} />

        {/* Mobile Action Buttons */}
        {showActions && (
          <div className={`absolute top-2 ${isUser ? 'left-2' : 'right-2'} flex items-center space-x-1 z-20`}>
            {message.role === 'assistant' && (
              <>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0 bg-background/80 backdrop-blur-sm shadow-sm "
                  onClick={() => onRate?.(message.id, 'up')}
                  aria-label="Rate message positively"
                >
                  <ThumbsUp className="h-3 w-3 " />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0 bg-background/80 backdrop-blur-sm shadow-sm "
                  onClick={() => onRate?.(message.id, 'down')}
                  aria-label="Rate message negatively"
                >
                  <ThumbsDown className="h-3 w-3 " />
                </Button>
              </>
            )}

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0 bg-background/80 backdrop-blur-sm shadow-sm "
                  aria-label="More actions"
                >
                  <MoreHorizontal className="h-3 w-3 " />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align={isUser ? 'start' : 'end'}>
                <DropdownMenuItem onClick={() => onCopy?.(message.content)}>
                  <Copy className="h-4 w-4 mr-2 " />
                </DropdownMenuItem>
                {message.role === 'assistant' && (
                  <DropdownMenuItem onClick={() => onReply?.(message.id)}>
                    <Reply className="h-4 w-4 mr-2 " />
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        )}
      </div>

      {/* Swipe Instructions (show once) */}
      {enableSwipeActions && (
        <div className="sr-only" aria-live="polite">
        </div>
      )}
    </div>
  );
};

export default TouchableMessageBubble;
