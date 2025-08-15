import React, { useState, memo, useMemo } from 'react';
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
import { useStableCallback, useStableMemo } from '../../utils/memoization';

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

// Memoized avatar component
const MessageAvatar = memo<{ isUser: boolean; isError: boolean }>(({ isUser, isError }) => {
  const avatarClasses = useMemo(() => {
    return `flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center shadow-sm ${
      isUser
        ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white'
        : isError
        ? 'bg-gradient-to-br from-red-500 to-red-600 text-white'
        : 'bg-gradient-to-br from-emerald-500 to-emerald-600 text-white'
    }`;
  }, [isUser, isError]);

  return (
    <motion.div
      className={avatarClasses}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
    >
      {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
    </motion.div>
  );
});

MessageAvatar.displayName = 'MessageAvatar';

// Memoized metadata component
const MessageMetadata = memo<{ 
  message: ChatMessage; 
  confidencePercentage: number | null; 
}>(({ message, confidencePercentage }) => {
  const shouldShowMetadata = message.role !== 'user' && message.status === 'completed';
  
  if (!shouldShowMetadata) return null;

  return (
    <div className="mt-3 pt-3 border-t border-gray-200/20">
      <div className="flex items-center gap-2 text-xs">
        {confidencePercentage !== null && (
          <Badge
            variant="secondary"
            className="text-xs bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300"
          >
            {confidencePercentage}% confidence
          </Badge>
        )}
        
        {message.metadata?.model && (
          <Badge variant="outline" className="text-xs">
            {message.metadata.model}
          </Badge>
        )}

        {message.metadata?.latencyMs && (
          <Badge variant="outline" className="text-xs">
            {message.metadata.latencyMs}ms
          </Badge>
        )}
      </div>
    </div>
  );
});

MessageMetadata.displayName = 'MessageMetadata';

// Memoized generating indicator
const GeneratingIndicator = memo(() => (
  <div className="mt-2 flex items-center gap-2 text-xs opacity-70">
    <div className="flex gap-1">
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
));

GeneratingIndicator.displayName = 'GeneratingIndicator';

// Memoized action buttons
const MessageActions = memo<{
  message: ChatMessage;
  onAction: (action: MessageAction) => void;
  isVisible: boolean;
}>(({ message, onAction, isVisible }) => {
  const isUser = message.role === 'user';
  const isError = message.status === 'error';
  
  const handleAction = useStableCallback((type: MessageAction['type'], payload?: any) => {
    onAction({ type, payload });
  }, [onAction]);

  const formattedTime = useStableMemo(() => {
    return format(message.timestamp, 'HH:mm');
  }, [message.timestamp]);

  if (!isVisible || isUser) {
    return isUser ? (
      <div className="text-xs text-gray-500 mt-1">
        {formattedTime}
      </div>
    ) : null;
  }

  const actionVariants = {
    hidden: { opacity: 0, scale: 0.8, y: 5 },
    visible: {
      opacity: 1,
      scale: 1,
      y: 0,
      transition: { type: "spring", stiffness: 400, damping: 25 }
    }
  };

  return (
    <motion.div
      variants={actionVariants}
      initial="hidden"
      animate="visible"
      exit="hidden"
      className="flex items-center gap-1 mt-2 text-xs text-gray-500"
    >
      <span className="mr-2">{formattedTime}</span>

      <RBACGuard permission="chat.copy" fallback={null}>
        <Button
          variant="ghost"
          size="sm"
          className="h-6 w-6 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
          onClick={() => handleAction('copy')}
          title="Copy message"
        >
          <Copy className="h-3 w-3" />
        </Button>
      </RBACGuard>

      {isError && (
        <RBACGuard permission="chat.retry" fallback={null}>
          <Button
            variant="ghost"
            size="sm"
            className="h-6 w-6 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
            onClick={() => handleAction('retry')}
            title="Retry message"
          >
            <RotateCcw className="h-3 w-3" />
          </Button>
        </RBACGuard>
      )}

      <RBACGuard permission="chat.rate" fallback={null}>
        <Button
          variant="ghost"
          size="sm"
          className="h-6 w-6 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
          onClick={() => handleAction('rate', { rating: 'up' })}
          title="Rate up"
        >
          <ThumbsUp className="h-3 w-3" />
        </Button>
      </RBACGuard>

      <RBACGuard permission="chat.rate" fallback={null}>
        <Button
          variant="ghost"
          size="sm"
          className="h-6 w-6 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
          onClick={() => handleAction('rate', { rating: 'down' })}
          title="Rate down"
        >
          <ThumbsDown className="h-3 w-3" />
        </Button>
      </RBACGuard>

      <RBACGuard permission="chat.edit" fallback={null}>
        <Button
          variant="ghost"
          size="sm"
          className="h-6 w-6 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
          onClick={() => handleAction('edit')}
          title="Edit message"
        >
          <Edit3 className="h-3 w-3" />
        </Button>
      </RBACGuard>

      <RBACGuard permission="chat.delete" fallback={null}>
        <Button
          variant="ghost"
          size="sm"
          className="h-6 w-6 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
          onClick={() => handleAction('delete')}
          title="Delete message"
        >
          <Trash2 className="h-3 w-3" />
        </Button>
      </RBACGuard>
    </motion.div>
  );
});

MessageActions.displayName = 'MessageActions';

// Main component with optimized memoization
const OptimizedMessageBubble: React.FC<MessageBubbleProps> = memo(({
  message,
  onAction,
  isLast = false,
  className = ''
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const [showActions, setShowActions] = useState(false);

  // Memoized derived values
  const messageState = useStableMemo(() => ({
    isUser: message.role === 'user',
    isError: message.status === 'error',
    isGenerating: message.status === 'generating',
    confidencePercentage: message.metadata?.confidence 
      ? Math.round(message.metadata.confidence * 100)
      : null
  }), [message.role, message.status, message.metadata?.confidence]);

  // Memoized CSS classes
  const containerClasses = useStableMemo(() => {
    return `flex gap-3 group ${messageState.isUser ? 'flex-row-reverse' : 'flex-row'} ${className}`;
  }, [messageState.isUser, className]);

  const contentWrapperClasses = useStableMemo(() => {
    return `flex-1 max-w-[85%] md:max-w-[75%] ${messageState.isUser ? 'text-right' : 'text-left'}`;
  }, [messageState.isUser]);

  const bubbleClasses = useStableMemo(() => {
    return `inline-block p-4 rounded-2xl shadow-sm relative ${
      messageState.isUser
        ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white'
        : messageState.isError
        ? 'bg-gradient-to-br from-red-50 to-red-100 border border-red-200 text-red-900 dark:bg-red-900/20 dark:border-red-800 dark:text-red-100'
        : 'bg-white border border-gray-200 text-gray-900 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-100'
    }`;
  }, [messageState.isUser, messageState.isError]);

  // Stable event handlers
  const handleMouseEnter = useStableCallback(() => setIsHovered(true), []);
  const handleMouseLeave = useStableCallback(() => setIsHovered(false), []);
  const handleActionCallback = useStableCallback((action: MessageAction) => {
    onAction?.(action);
  }, [onAction]);

  // Animation variants (memoized)
  const bubbleVariants = useStableMemo(() => ({
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
  }), []);

  return (
    <motion.div
      variants={bubbleVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      className={containerClasses}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {/* Avatar */}
      <MessageAvatar 
        isUser={messageState.isUser} 
        isError={messageState.isError} 
      />

      {/* Message Content */}
      <div className={contentWrapperClasses}>
        <motion.div
          className={bubbleClasses}
          whileHover={{ 
            scale: 1.01, 
            boxShadow: "0 8px 25px rgba(0,0,0,0.1)" 
          }}
          transition={{ type: "spring", stiffness: 400, damping: 25 }}
        >
          {/* Message Content */}
          <div className="whitespace-pre-wrap break-words leading-relaxed">
            {messageState.isUser ? (
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
          {messageState.isGenerating && <GeneratingIndicator />}

          {/* Metadata for assistant messages */}
          <MessageMetadata 
            message={message} 
            confidencePercentage={messageState.confidencePercentage} 
          />
        </motion.div>

        {/* Action Buttons */}
        <MessageActions
          message={message}
          onAction={handleActionCallback}
          isVisible={isHovered || showActions}
        />
      </div>
    </motion.div>
  );
}, (prevProps, nextProps) => {
  // Custom comparison function for better memoization
  return (
    prevProps.message.id === nextProps.message.id &&
    prevProps.message.content === nextProps.message.content &&
    prevProps.message.status === nextProps.message.status &&
    prevProps.message.timestamp.getTime() === nextProps.message.timestamp.getTime() &&
    prevProps.isLast === nextProps.isLast &&
    prevProps.className === nextProps.className &&
    prevProps.onAction === nextProps.onAction
  );
});

OptimizedMessageBubble.displayName = 'OptimizedMessageBubble';

export { OptimizedMessageBubble };
export default OptimizedMessageBubble;