import React from 'react';
import { Bot, Loader2, Wifi, WifiOff } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface TypingIndicatorProps {
  isTyping: boolean;
  isConnected: boolean;
  typingUsers?: string[];
  estimatedTime?: number;
  showConnectionStatus?: boolean;
}

export const TypingIndicator: React.FC<TypingIndicatorProps> = ({
  isTyping,
  isConnected,
  typingUsers = [],
  estimatedTime,
  showConnectionStatus = true,
}) => {
  const TypingDots = () => (
    <div className="flex space-x-1">
      <div className="w-2 h-2 bg-current rounded-full animate-bounce sm:w-auto md:w-full" />
      <div className="w-2 h-2 bg-current rounded-full animate-bounce [animation-delay:0.1s] sm:w-auto md:w-full" />
      <div className="w-2 h-2 bg-current rounded-full animate-bounce [animation-delay:0.2s] sm:w-auto md:w-full" />
    </div>
  );

  const getTypingMessage = () => {
    if (typingUsers.length === 0) {
      return 'AI is thinking...';
    } else if (typingUsers.length === 1) {
      return `${typingUsers[0]} is typing...`;
    } else {
      return `${typingUsers.slice(0, -1).join(', ')} and ${typingUsers[typingUsers.length - 1]} are typing...`;
    }
  };

  if (!isTyping && !showConnectionStatus) {
    return null;
  }

  return (
    <div className="flex items-center justify-between p-3 border-t bg-muted/50 sm:p-4 md:p-6">
      {/* Typing Indicator */}
      {isTyping && (
        <div 
          className="flex items-center space-x-3"
          role="status" 
          aria-live="polite" 
          aria-label={getTypingMessage()}
        >
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center sm:w-auto md:w-full">
            <Bot className="h-4 w-4 text-primary sm:w-auto md:w-full" aria-hidden="true" />
          </div>
          <div className="flex items-center space-x-2">
            <TypingDots />
            <span className="text-sm text-muted-foreground md:text-base lg:text-lg">
              {getTypingMessage()}
            </span>
            {estimatedTime && (
              <Badge variant="secondary" className="text-xs sm:text-sm md:text-base">
                ~{estimatedTime}s
              </Badge>
            )}
          </div>
        </div>
      )}

      {/* Connection Status */}
      {showConnectionStatus && (
        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-1">
            {isConnected ? (
              <>
                <Wifi className="h-4 w-4 text-green-500 sm:w-auto md:w-full" aria-hidden="true" />
                <span className="text-xs text-green-600 dark:text-green-400 sm:text-sm md:text-base">
                  Connected
                </span>
              </>
            ) : (
              <>
                <WifiOff className="h-4 w-4 text-red-500 sm:w-auto md:w-full" aria-hidden="true" />
                <span className="text-xs text-red-600 dark:text-red-400 sm:text-sm md:text-base">
                  Disconnected
                </span>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default TypingIndicator;
