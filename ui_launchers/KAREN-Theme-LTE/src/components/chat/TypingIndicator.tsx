/**
 * Typing Indicator Component
 * Show when AI is responding
 */

import React from 'react';
import { cn } from '@/lib/utils';
import { Bot } from 'lucide-react';

export interface TypingIndicatorProps {
  className?: string;
  text?: string;
  showAvatar?: boolean;
}

export function TypingIndicator({
  className,
  text = 'KAREN is typing',
  showAvatar = true,
}: TypingIndicatorProps) {
  return (
    <div className={cn('flex gap-3 p-4', className)}>
      {showAvatar && (
        <div className="flex-shrink-0">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-600 to-pink-600 flex items-center justify-center">
            <Bot className="h-5 w-5 text-white" />
          </div>
        </div>
      )}
      
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <div className="text-xs font-medium px-2 py-1 rounded-full bg-purple-100 text-purple-700">
            KAREN
          </div>
          <div className="text-xs text-purple-400">{text}</div>
        </div>
        
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
          <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
          <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
        </div>
      </div>
    </div>
  );
}