# Path: ui_launchers/web_ui/src/components/chat/MessageBubble.tsx

'use client';

import React, { useState, useCallback, memo } from 'react';
import { motion } from 'framer-motion';
import { format } from 'date-fns';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Copy, 
  ThumbsUp, 
  ThumbsDown, 
  MoreHorizontal, 
  Bot, 
  User,
  RotateCcw,
  Trash2,
  Edit3
} from 'lucide-react';
import { ChatMessage } from '@/lib/types';
import { SanitizedMarkdown } from '@/components/security/SanitizedMarkdown';
import { RBACGuard } from '@/components/security/RBACGuard';
import { useScreenReader, createAriaLabel, createAriaDescribedBy, chatAriaPatterns } from '@/hooks/use-screen-reader';

interface MessageBubbleProps {
  message: ChatMessage;
  onAction?: (action: MessageAction) => void;
  isLast?: boolean;
  className?: string;
}

interface MessageAction {
  type: 'copy' | 'retry' | 'edit' | 'delete' | 'rate';
  payload?: any;
}

const MessageBubble: React.FC<MessageBubbleProps> = memo(({
  message,
  onAction,
  isLast = false,
  className = ''
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const [showActions, setShowActions] = useState(false);

  const isUser = message.role === 'user';
  const isError = message.status === 'error';
  const isGenerating = message.status === 'generating';
  
  // Screen reader support
  const { announce } = useScreenReader();

  // Handle action clicks
  const handleAction = useCallback((type: MessageAction['type'], payload?: any) => {
    onAction?.({ type, payload });
    
    // Announce action to screen readers
    const actionMessages = {
      copy: 'Message copied to clipboard',
      retry: 'Retrying message',
      edit: 'Editing message',
      delete: 'Message deleted',
      rate: payload?.rating === 'up' ? 'Message rated positively' : 'Message rated negatively'
    };
    
    if (actionMessages[type]) {
      announce(actionMessages[type], 'polite');
    }
  }, [onAction, announce]);

  // Get confidence percentage
  const confidencePercentage = message.metadata?.confidence 
    ? Math.round(message.metadata.confidence * 100)
    : null;

  // Animation variants
  const bubbleVariants = {
    initial: { opacity: 0, y: 20, scale: 0.95 },
    animate: {
      opacity: 1,
      y: 0,
      scale: 1,
      transition: { 
        type: "spring", 
        stiffness: 500, 
        damping: 30, 
        mass: 1 
      }
    },
    exit: { 
      opacity: 0, 
      y: -10, 
      scale: 0.95, 
      transition: { duration: 0.2 } 
    }
  };

  const actionVariants = {
    hidden: { opacity: 0, scale: 0.8, y: 5 },
    visible: {
      opacity: 1,
      scale: 1,
      y: 0,
      transition: { type: "spring", stiffness: 400, damping: 25 }
    }
  };

  // Create comprehensive ARIA labels
  const messageAriaLabel = createAriaLabel(
    `${isUser ? 'Your' : 'Assistant'} message`,
    {
      state: isError ? 'error' : isGenerating ? 'generating' : 'completed',
      description: `sent at ${format(message.timestamp, 'HH:mm')}`
    }
  );

  const contentId = `message-content-${message.id}`;
  const actionsId = `message-actions-${message.id}`;
  const metadataId = `message-metadata-${message.id}`;

  return (
    <motion.div
      variants={bubbleVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      className={`flex gap-3 group ${isUser ? 'flex-row-reverse' : 'flex-row'} ${className}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      role="article"
      aria-label={messageAriaLabel}
      aria-describedby={createAriaDescribedBy(
        contentId,
        !isUser && message.status === 'completed' ? metadataId : null,
        (isHovered || showActions) && !isUser ? actionsId : null
      )}
    >
      {/* Avatar */}
      <motion.div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center shadow-sm ${
          isUser
            ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white'
            : isError
            ? 'bg-gradient-to-br from-red-500 to-red-600 text-white'
            : 'bg-gradient-to-br from-emerald-500 to-emerald-600 text-white'
        }`}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        role="img"
        aria-label={`${isUser ? 'User' : 'Assistant'} avatar${isError ? ' (error state)' : ''}`}
      >
        {isUser ? <User className="h-4 w-4" aria-hidden="true" /> : <Bot className="h-4 w-4" aria-hidden="true" />}
      </motion.div>

      {/* Message Content */}
      <div className={`flex-1 max-w-[85%] md:max-w-[75%] ${isUser ? 'text-right' : 'text-left'}`}>
        <motion.div
          className={`inline-block p-4 rounded-2xl shadow-sm relative ${
            isUser
              ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white'
              : isError
              ? 'bg-gradient-to-br from-red-50 to-red-100 border border-red-200 text-red-900 dark:bg-red-900/20 dark:border-red-800 dark:text-red-100'
              : 'bg-white border border-gray-200 text-gray-900 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-100'
          }`}
          whileHover={{ 
            scale: 1.01, 
            boxShadow: "0 8px 25px rgba(0,0,0,0.1)" 
          }}
          transition={{ type: "spring", stiffness: 400, damping: 25 }}
        >
          {/* Message Content */}
          <div 
            id={contentId}
            className="whitespace-pre-wrap break-words leading-relaxed"
            {...(isGenerating ? chatAriaPatterns.streamingMessage : {})}
          >
            {isUser ? (
              message.content
            ) : (
              <SanitizedMarkdown 
                content={message.content}
                allowedTags={['p', 'br', 'strong', 'em', 'code', 'pre', 'ul', 'ol', 'li', 'blockquote']}
                linkTarget="_blank"
              />
            )}
          </div>

          {/* Generating indicator */}
          {isGenerating && (
            <div 
              className="mt-2 flex items-center gap-2 text-xs opacity-70"
              role="status"
              aria-live="polite"
              aria-label="Assistant is generating response"
            >
              <div className="flex gap-1" aria-hidden="true">
                {[0, 0.2, 0.4].map((delay) => (
                  <motion.div
                    key={delay}
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ repeat: Infinity, duration: 1.5, delay }}
                    className="w-1 h-1 bg-current rounded-full"
                  />
                ))}
              </div>
              <span>Generating...</span>
            </div>
          )}

          {/* Metadata for assistant messages */}
          {!isUser && message.status === 'completed' && (
            <div 
              id={metadataId}
              className="mt-3 pt-3 border-t border-gray-200/20"
              role="group"
              aria-label="Message metadata"
            >
              <div className="flex items-center gap-2 text-xs">
                {confidencePercentage !== null && (
                  <Badge
                    variant="secondary"
                    className="text-xs bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300"
                    aria-label={`Confidence level: ${confidencePercentage} percent`}
                  >
                    {confidencePercentage}% confidence
                  </Badge>
                )}
                
                {message.metadata?.model && (
                  <Badge 
                    variant="outline" 
                    className="text-xs"
                    aria-label={`Generated by model: ${message.metadata.model}`}
                  >
                    {message.metadata.model}
                  </Badge>
                )}

                {message.metadata?.latencyMs && (
                  <Badge 
                    variant="outline" 
                    className="text-xs"
                    aria-label={`Response time: ${message.metadata.latencyMs} milliseconds`}
                  >
                    {message.metadata.latencyMs}ms
                  </Badge>
                )}
              </div>
            </div>
          )}
        </motion.div>

        {/* Action Buttons */}
        {(isHovered || showActions) && !isUser && (
          <motion.div
            id={actionsId}
            variants={actionVariants}
            initial="hidden"
            animate="visible"
            exit="hidden"
            className="flex items-center gap-1 mt-2 text-xs text-gray-500"
            {...chatAriaPatterns.messageActions}
          >
            <span className="mr-2" aria-label={`Message sent at ${format(message.timestamp, 'HH:mm')}`}>
              {format(message.timestamp, 'HH:mm')}
            </span>

            <RBACGuard permission="chat.copy" fallback={null}>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
                onClick={() => handleAction('copy')}
                aria-label="Copy message to clipboard"
                title="Copy message"
              >
                <Copy className="h-3 w-3" aria-hidden="true" />
              </Button>
            </RBACGuard>

            {isError && (
              <RBACGuard permission="chat.retry" fallback={null}>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 w-6 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
                  onClick={() => handleAction('retry')}
                  aria-label="Retry generating this message"
                  title="Retry message"
                >
                  <RotateCcw className="h-3 w-3" aria-hidden="true" />
                </Button>
              </RBACGuard>
            )}

            <RBACGuard permission="chat.rate" fallback={null}>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
                onClick={() => handleAction('rate', { rating: 'up' })}
                aria-label="Rate this message as helpful"
                title="Rate up"
              >
                <ThumbsUp className="h-3 w-3" aria-hidden="true" />
              </Button>
            </RBACGuard>

            <RBACGuard permission="chat.rate" fallback={null}>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
                onClick={() => handleAction('rate', { rating: 'down' })}
                aria-label="Rate this message as not helpful"
                title="Rate down"
              >
                <ThumbsDown className="h-3 w-3" aria-hidden="true" />
              </Button>
            </RBACGuard>

            <RBACGuard permission="chat.edit" fallback={null}>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
                onClick={() => handleAction('edit')}
                aria-label="Edit this message"
                title="Edit message"
              >
                <Edit3 className="h-3 w-3" aria-hidden="true" />
              </Button>
            </RBACGuard>

            <RBACGuard permission="chat.delete" fallback={null}>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
                onClick={() => handleAction('delete')}
                aria-label="Delete this message"
                title="Delete message"
              >
                <Trash2 className="h-3 w-3" aria-hidden="true" />
              </Button>
            </RBACGuard>

            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
              onClick={() => setShowActions(!showActions)}
              aria-label={showActions ? "Hide additional actions" : "Show additional actions"}
              aria-expanded={showActions}
              title="More actions"
            >
              <MoreHorizontal className="h-3 w-3" aria-hidden="true" />
            </Button>
          </motion.div>
        )}

        {/* Timestamp for user messages */}
        {isUser && (
          <div 
            className="text-xs text-gray-500 mt-1"
            aria-label={`Message sent at ${format(message.timestamp, 'HH:mm')}`}
          >
            {format(message.timestamp, 'HH:mm')}
          </div>
        )}
      </div>
    </motion.div>
  );
});

MessageBubble.displayName = 'MessageBubble';

export { MessageBubble };
export default MessageBubble;