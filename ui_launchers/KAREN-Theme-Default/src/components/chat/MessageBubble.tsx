"use client";

import * as React from 'react';
import { Avatar } from '@/components/ui/avatar';
import { Card, CardContent } from '@/components/ui/card';
import { Bot, User } from 'lucide-react';

export interface MessageBubbleProps {
  message: {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp?: Date;
    metadata?: MessageMetadata;
  };
}

export interface MessageMetadata {
  provider?: string;
  model?: string;
  confidence?: number;
  kire?: {
    provider?: string;
    model?: string;
    confidence?: number;
  };
  kire_metadata?: Record<string, unknown>;
  [key: string]: unknown;
}

const MessageBubbleComponent = ({ message }: MessageBubbleProps) => {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';
  const metadata = message.metadata;
  const kireMeta = metadata?.kire;
  const provider =
    typeof kireMeta?.provider === 'string'
      ? kireMeta.provider
      : typeof metadata?.provider === 'string'
      ? metadata.provider
      : undefined;
  const model =
    typeof kireMeta?.model === 'string'
      ? kireMeta.model
      : typeof metadata?.model === 'string'
      ? metadata.model
      : undefined;
  const confidence =
    typeof kireMeta?.confidence === 'number'
      ? kireMeta.confidence
      : typeof metadata?.confidence === 'number'
      ? metadata.confidence
      : undefined;

  return (
    <div className={`flex items-start gap-3 my-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <Avatar className="h-10 w-10 self-start shrink-0 flex items-center justify-center bg-muted rounded-full ">
          <Bot className="h-5 w-5 text-primary " aria-hidden="true" />
        </Avatar>
      )}
      <Card className={`max-w-xl shadow-md rounded-xl ${isUser ? 'bg-primary text-primary-foreground' : 'bg-card'}`}>
        <CardContent className="p-3 md:p-4">
          <p className={`whitespace-pre-wrap text-sm md:text-base ${isSystem ? 'text-foreground' : ''}`}>
            {message.content}
          </p>
          {!isUser && (provider || model) && (
            <div className="mt-2 text-[11px] md:text-xs text-muted-foreground flex items-center gap-2">
              <span className="inline-flex items-center gap-1">
                <span className="opacity-70">Model:</span>
                <span className="font-medium">{provider ? `${provider}/` : ''}{model || 'any'}</span>
              </span>
              {typeof confidence === 'number' && (
                <span className="inline-flex items-center gap-1">
                  <span className="opacity-70">conf:</span>
                  <span>{(confidence * 100).toFixed(0)}%</span>
                </span>
              )}
            </div>
          )}
        </CardContent>
      </Card>
      {isUser && (
        <Avatar className="h-10 w-10 self-start shrink-0 flex items-center justify-center bg-muted rounded-full ">
          <User className="h-5 w-5 text-secondary " aria-hidden="true" />
        </Avatar>
      )}
    </div>
  );
};

// Memoize the component to prevent unnecessary re-renders
export const MessageBubble = React.memo(MessageBubbleComponent);

export default MessageBubble;
