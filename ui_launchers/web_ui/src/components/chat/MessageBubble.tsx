"use client";

import React from 'react';
import { Avatar } from '@/components/ui/avatar';
import { Card, CardContent } from '@/components/ui/card';
import { Bot, User } from 'lucide-react';

export interface MessageBubbleProps {
  message: {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp?: Date;
    metadata?: Record<string, any>;
  };
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  return (
    <div className={`flex items-start gap-3 my-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <Avatar className="h-10 w-10 self-start shrink-0 flex items-center justify-center bg-muted rounded-full">
          <Bot className="h-5 w-5 text-primary" />
        </Avatar>
      )}
      <Card className={`max-w-xl shadow-md rounded-xl ${isUser ? 'bg-primary text-primary-foreground' : 'bg-card'}`}>
        <CardContent className="p-3 md:p-4">
          <p className={`whitespace-pre-wrap text-sm md:text-base ${isSystem ? 'text-foreground' : ''}`}>
            {message.content}
          </p>
        </CardContent>
      </Card>
      {isUser && (
        <Avatar className="h-10 w-10 self-start shrink-0 flex items-center justify-center bg-muted rounded-full">
          <User className="h-5 w-5 text-secondary" />
        </Avatar>
      )}
    </div>
  );
}

export default MessageBubble;

