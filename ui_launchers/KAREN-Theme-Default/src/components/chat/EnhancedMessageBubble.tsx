"use client";

import React, { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Copy,
  RefreshCw,
  ThumbsUp,
  ThumbsDown,
  User,
  Bot,
  Shield,
  Clock,
  Cpu,
  Zap,
  Check
} from 'lucide-react';
import { CodeBlock } from '@/components/ui/syntax-highlighter';
import { cn } from '@/lib/utils';

export interface MessageMetadata {
  confidence?: number;
  model?: string;
  latency?: number;
  tokens?: {
    prompt?: number;
    completion?: number;
    total?: number;
  };
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  type?: 'text' | 'code';
  language?: string;
  timestamp: Date;
  metadata?: MessageMetadata;
  status?: 'sending' | 'sent' | 'error';
  rating?: 'positive' | 'negative';
}

export interface EnhancedMessageBubbleProps {
  message: Message;
  onCopy?: (content: string) => void;
  onRegenerate?: (messageId: string) => void;
  onRate?: (messageId: string, rating: 'positive' | 'negative') => void;
  showMetadata?: boolean;
  className?: string;
}

export default function EnhancedMessageBubble({
  message,
  onCopy,
  onRegenerate,
  onRate,
  showMetadata = true,
  className,
}: EnhancedMessageBubbleProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (onCopy) {
      onCopy(message.content);
    } else {
      navigator.clipboard.writeText(message.content);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRegenerate = () => {
    if (onRegenerate) {
      onRegenerate(message.id);
    }
  };

  const handleRate = (rating: 'positive' | 'negative') => {
    if (onRate) {
      onRate(message.id, rating);
    }
  };

  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';
  const isCode = message.type === 'code';

  const getRoleIcon = () => {
    switch (message.role) {
      case 'user':
        return <User className="h-4 w-4" />;
      case 'assistant':
        return <Bot className="h-4 w-4" />;
      case 'system':
        return <Shield className="h-4 w-4" />;
      default:
        return null;
    }
  };

  const getRoleLabel = () => {
    switch (message.role) {
      case 'user':
        return 'You';
      case 'assistant':
        return 'Assistant';
      case 'system':
        return 'System';
      default:
        return message.role;
    }
  };

  const formatTimestamp = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <div
      className={cn(
        'flex w-full',
        isUser ? 'justify-end' : 'justify-start',
        className
      )}
    >
      <div className={cn('flex max-w-[80%] gap-3', isUser && 'flex-row-reverse')}>
        {/* Avatar */}
        <div
          className={cn(
            'flex h-8 w-8 shrink-0 items-center justify-center rounded-full',
            isUser && 'bg-blue-500 text-white',
            !isUser && !isSystem && 'bg-purple-500 text-white',
            isSystem && 'bg-gray-500 text-white'
          )}
        >
          {getRoleIcon()}
        </div>

        {/* Message Content */}
        <div className="flex flex-col gap-2 w-full">
          {/* Header */}
          <div className={cn('flex items-center gap-2', isUser && 'flex-row-reverse')}>
            <span className="text-sm font-medium">{getRoleLabel()}</span>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {formatTimestamp(message.timestamp)}
            </span>
            {message.status === 'sending' && (
              <Badge variant="outline" className="text-xs">
                Sending...
              </Badge>
            )}
            {message.status === 'error' && (
              <Badge variant="destructive" className="text-xs">
                Error
              </Badge>
            )}
          </div>

          {/* Message Bubble */}
          <Card
            className={cn(
              'relative px-4 py-3',
              isUser && 'bg-blue-500 text-white',
              !isUser && !isSystem && 'bg-gray-100 dark:bg-gray-800',
              isSystem && 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800'
            )}
          >
            {isCode && message.language ? (
              <CodeBlock
                language={message.language}
                showLineNumbers
              >
                {message.content}
              </CodeBlock>
            ) : (
              <div className="whitespace-pre-wrap break-words">
                {message.content}
              </div>
            )}

            {/* Metadata */}
            {showMetadata && message.metadata && !isUser && (
              <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700 flex flex-wrap gap-3 text-xs text-gray-600 dark:text-gray-400">
                {message.metadata.confidence !== undefined && (
                  <div className="flex items-center gap-1">
                    <Zap className="h-3 w-3" />
                    <span>Confidence: {Math.round(message.metadata.confidence * 100)}%</span>
                  </div>
                )}
                {message.metadata.model && (
                  <div className="flex items-center gap-1">
                    <Cpu className="h-3 w-3" />
                    <span>{message.metadata.model}</span>
                  </div>
                )}
                {message.metadata.latency !== undefined && (
                  <div className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    <span>{message.metadata.latency}ms</span>
                  </div>
                )}
                {message.metadata.tokens?.total && (
                  <div className="flex items-center gap-1">
                    <span>{message.metadata.tokens.total} tokens</span>
                  </div>
                )}
              </div>
            )}
          </Card>

          {/* Actions */}
          {!isUser && message.status !== 'sending' && (
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleCopy}
                className="h-7 px-2"
                title="Copy message"
              >
                {copied ? (
                  <>
                    <Check className="h-3 w-3 mr-1" />
                    <span className="text-xs">Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="h-3 w-3 mr-1" />
                    <span className="text-xs">Copy</span>
                  </>
                )}
              </Button>

              {onRegenerate && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleRegenerate}
                  className="h-7 px-2"
                  title="Regenerate response"
                >
                  <RefreshCw className="h-3 w-3 mr-1" />
                  <span className="text-xs">Regenerate</span>
                </Button>
              )}

              {onRate && (
                <>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleRate('positive')}
                    className={cn(
                      'h-7 px-2',
                      message.rating === 'positive' && 'text-green-600'
                    )}
                    title="Rate positive"
                  >
                    <ThumbsUp className="h-3 w-3" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleRate('negative')}
                    className={cn(
                      'h-7 px-2',
                      message.rating === 'negative' && 'text-red-600'
                    )}
                    title="Rate negative"
                  >
                    <ThumbsDown className="h-3 w-3" />
                  </Button>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Export commonly used types and the component
