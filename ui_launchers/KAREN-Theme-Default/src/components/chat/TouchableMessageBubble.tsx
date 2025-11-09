// ui_launchers/KAREN-Theme-Default/src/components/chat/TouchableMessageBubble.tsx
"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import { useSwipeable } from "react-swipeable";
import {
  Copy,
  ThumbsUp,
  ThumbsDown,
  MoreHorizontal,
  Reply,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { MessageBubble, type MessageBubbleProps } from "./MessageBubble";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";

interface TouchableMessageBubbleProps extends MessageBubbleProps {
  onSwipeLeft?: (messageId: string) => void;
  onSwipeRight?: (messageId: string) => void;
  onCopy?: (content: string) => void;
  onReply?: (messageId: string) => void;
  onRate?: (messageId: string, rating: "up" | "down") => void;
  enableSwipeActions?: boolean;
  /** Desktop: show quick actions on hover (true by default) */
  hoverActions?: boolean;
  /** Milliseconds to keep mobile action tray visible after touch end */
  actionAutoHideMs?: number;
}

export const TouchableMessageBubble: React.FC<TouchableMessageBubbleProps> = ({
  message,
  onSwipeLeft,
  onSwipeRight,
  onCopy,
  onReply,
  onRate,
  enableSwipeActions = true,
  hoverActions = true,
  actionAutoHideMs = 1100,
  ...props
}) => {
  const [showActions, setShowActions] = useState(false);
  const [swipeOffset, setSwipeOffset] = useState(0);

  const isUser = message.role === "user";
  const autoHideTimer = useRef<number | null>(null);

  const clearAutoHide = () => {
    if (autoHideTimer.current) {
      window.clearTimeout(autoHideTimer.current);
      autoHideTimer.current = null;
    }
  };

  const scheduleAutoHide = () => {
    clearAutoHide();
    autoHideTimer.current = window.setTimeout(() => {
      setShowActions(false);
      autoHideTimer.current = null;
    }, actionAutoHideMs);
  };

  useEffect(() => {
    return () => clearAutoHide();
  }, []);

  const handleSwipeLeft = useCallback(() => {
    if (onSwipeLeft) {
      onSwipeLeft(message.id);
    } else if (message.role === "assistant" && onReply) {
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
    onSwiping: (evtData) => {
      if (enableSwipeActions) setSwipeOffset(evtData.deltaX);
    },
    onSwiped: () => setSwipeOffset(0),
    trackMouse: false,
    trackTouch: true,
    preventScrollOnSwipe: false,
    delta: 50, // Minimum pixels to trigger swipe
  });

  const handleTouchStart = () => {
    setShowActions(true);
    clearAutoHide();
  };

  const handleTouchEnd = () => {
    scheduleAutoHide();
  };

  const handleMouseEnter = () => {
    if (hoverActions) setShowActions(true);
  };

  const handleMouseLeave = () => {
    if (hoverActions) setShowActions(false);
  };

  return (
    <div
      {...swipeHandlers}
      className="relative touch-pan-y"
      style={{
        transform: enableSwipeActions
          ? `translateX(${Math.max(-100, Math.min(100, swipeOffset))}px)`
          : undefined,
        transition: swipeOffset === 0 ? "transform 0.2s ease-out" : "none",
      }}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      aria-label="Message with touch actions"
    >
      {/* Swipe Action Hints */}
      {enableSwipeActions && Math.abs(swipeOffset) > 20 && (
        <div className="absolute inset-0 flex items-center justify-between pointer-events-none z-10">
          {swipeOffset > 20 && (
            <div className="flex items-center space-x-2 ml-4 text-blue-500">
              <Copy className="h-5 w-5" />
              <span className="text-sm font-medium md:text-base lg:text-lg">
                Copy
              </span>
            </div>
          )}
          {swipeOffset < -20 && (
            <div className="flex items-center space-x-2 mr-4 text-green-500 ml-auto">
              <span className="text-sm font-medium md:text-base lg:text-lg">
                Reply
              </span>
              <Reply className="h-5 w-5" />
            </div>
          )}
        </div>
      )}

      {/* Message Content */}
      <div className="relative">
        <MessageBubble message={message} {...props} />

        {/* Quick Action Tray */}
        {showActions && (
          <div
            className={`absolute top-2 ${
              isUser ? "left-2" : "right-2"
            } flex items-center space-x-1 z-20`}
          >
            {message.role === "assistant" && (
              <>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0 bg-background/80 backdrop-blur-sm shadow-sm"
                  onClick={() => onRate?.(message.id, "up")}
                  aria-label="Rate message positively"
                  title="Thumbs up"
                >
                  <ThumbsUp className="h-3 w-3" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0 bg-background/80 backdrop-blur-sm shadow-sm"
                  onClick={() => onRate?.(message.id, "down")}
                  aria-label="Rate message negatively"
                  title="Thumbs down"
                >
                  <ThumbsDown className="h-3 w-3" />
                </Button>
              </>
            )}

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0 bg-background/80 backdrop-blur-sm shadow-sm"
                  aria-label="More actions"
                  title="More actions"
                >
                  <MoreHorizontal className="h-3 w-3" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align={isUser ? "start" : "end"}>
                <DropdownMenuItem onClick={() => onCopy?.(message.content)}>
                  <Copy className="h-4 w-4 mr-2" />
                  Copy
                </DropdownMenuItem>
                {message.role === "assistant" && (
                  <>
                    <DropdownMenuItem onClick={() => onReply?.(message.id)}>
                      <Reply className="h-4 w-4 mr-2" />
                      Reply
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={() => onRate?.(message.id, "up")}>
                      <ThumbsUp className="h-4 w-4 mr-2" />
                      Thumbs up
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={() => onRate?.(message.id, "down")}
                    >
                      <ThumbsDown className="h-4 w-4 mr-2" />
                      Thumbs down
                    </DropdownMenuItem>
                  </>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        )}
      </div>

      {/* One-time swipe instructions for screen readers */}
      {enableSwipeActions && (
        <div className="sr-only" aria-live="polite">
          Swipe right to copy, swipe left to reply.
        </div>
      )}
    </div>
  );
};

export default TouchableMessageBubble;
