'use client';

import React from 'react';
import { Bot, User } from 'lucide-react';
import { MetaBar } from './MetaBar';

export interface ChatBubbleProps {
  role: 'user' | 'assistant' | 'system';
  content: React.ReactNode;
  meta?: React.ComponentProps<typeof MetaBar>;
}

export const ChatBubble: React.FC<ChatBubbleProps> = ({ role, content, meta }) => {
  const isUser = role === 'user';
  const shouldShowMeta = role === 'assistant' && meta && Object.keys(meta).length > 0;

  return (
    <div className={`flex gap-3 mb-4 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser ? 'bg-primary text-primary-foreground' : 'bg-muted'
        }`}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>
      <div className={`flex-1 max-w-[80%] ${isUser ? 'text-right' : 'text-left'}`}>
        <div
          className={`inline-block p-3 rounded-lg ${
            isUser ? 'bg-primary text-primary-foreground' : 'bg-muted border'
          }`}
        >
          {typeof content === 'string' ? (
            <p className="whitespace-pre-wrap">{content}</p>
          ) : (
            content
          )}
        </div>
        {shouldShowMeta && <MetaBar {...meta} />}
      </div>
    </div>
  );
};

export default ChatBubble;
