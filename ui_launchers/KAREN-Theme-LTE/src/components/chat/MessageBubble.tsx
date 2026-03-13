/**
 * Message Bubble Component
 * Individual message display with metadata
 */

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { ChatMessage, MessageStatus } from '@/types/chat';
import { Button } from '@/components/ui/button';
import { 
  Bookmark, 
  BookmarkCheck, 
  MoreHorizontal, 
  Copy, 
  RotateCcw, 
  ThumbsUp, 
  ThumbsDown,
  User,
  Bot,
  Paperclip,
  X
} from 'lucide-react';

export interface MessageBubbleProps {
  message: ChatMessage;
  className?: string;
  showAvatar?: boolean;
  showTimestamp?: boolean;
  showMetadata?: boolean;
  showReactions?: boolean;
  showActions?: boolean;
}

export function MessageBubble({
  message,
  className,
  showAvatar = true,
  showTimestamp = true,
  showMetadata = true,
  showReactions = true,
  showActions = true,
}: MessageBubbleProps) {
  const [showFullMessage, setShowFullMessage] = useState(false);
  const [isBookmarked, setIsBookmarked] = useState((message as any).isBookmarked || false);
  const [showActionsMenu, setShowActionsMenu] = useState(false);
  const [copied, setCopied] = useState(false);

  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';
  const isError = (message as any).status === MessageStatus.FAILED;
  const isSending = (message as any).status === MessageStatus.SENDING;
  const hasAttachments = (message as any).attachments && (message as any).attachments.length > 0;

  const handleBookmark = () => {
    setIsBookmarked(!isBookmarked);
    // In a real implementation, this would call the store
    // bookmarkMessage(message.id, !isBookmarked);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRetry = () => {
    // In a real implementation, this would call the store
    // retryMessage(message.id);
  };

  const formatTimestamp = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    }).format(date);
  };

  const truncateMessage = (text: string, maxLength: number) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  const getMessageStatusIcon = () => {
    if (isSending) {
      return <div className="w-2 h-2 border-2 border-purple-300 border-t-transparent animate-spin rounded-full" />;
    }
    
    if (isError) {
      return <X className="h-4 w-4 text-red-500" />;
    }
    
    return null;
  };

  return (
    <div
      className={cn(
        'group flex gap-3 p-4 rounded-lg transition-all duration-200',
        isUser 
          ? 'bg-purple-600/20 ml-auto max-w-3xl' 
          : 'bg-black/20 max-w-4xl',
        isError && 'border border-red-500/50 bg-red-500/10',
        className
      )}
    >
      {/* Avatar */}
      {showAvatar && (
        <div className="flex-shrink-0">
          <div
            className={cn(
              'w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium',
              isUser 
                ? 'bg-purple-500 text-white' 
                : 'bg-gradient-to-br from-purple-600 to-pink-600 text-white'
            )}
          >
            {isUser ? (
              <User className="h-5 w-5" />
            ) : (
              <Bot className="h-5 w-5" />
            )}
          </div>
        </div>
      )}

      {/* Message content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2 mb-1">
          {/* Role indicator */}
          <div className={cn(
            'text-xs font-medium px-2 py-1 rounded-full',
            isUser 
              ? 'bg-purple-700 text-purple-100' 
              : 'bg-purple-100 text-purple-700'
          )}>
            {isUser ? 'You' : 'KAREN'}
          </div>

          {/* Timestamp */}
          {showTimestamp && message.timestamp && (
            <div className="text-xs text-purple-400">
              {formatTimestamp(message.timestamp)}
            </div>
          )}
        </div>

        {/* Message text */}
        <div className="text-white mb-2">
          {isError ? (
            <div className="text-red-400">
              {message.content}
            </div>
          ) : showFullMessage || message.content.length <= 300 ? (
            <div className="whitespace-pre-wrap break-words">
              {message.content}
            </div>
          ) : (
            <div>
              <div className="whitespace-pre-wrap break-words">
                {truncateMessage(message.content, 300)}
              </div>
              {!showFullMessage && message.content.length > 300 && (
                <button
                  onClick={() => setShowFullMessage(true)}
                  className="text-purple-400 hover:text-purple-300 text-xs mt-1"
                >
                  Show more
                </button>
              )}
            </div>
          )}
        </div>

        {/* Attachments */}
        {hasAttachments && (
          <div className="flex flex-wrap gap-2 mt-2">
            {(message as any).attachments?.map((attachment: any) => (
              <div
                key={attachment.id}
                className="bg-white/10 border border-purple-500/30 rounded-lg p-3 flex items-center gap-2 max-w-xs"
              >
                {attachment.type === 'image' ? (
                  <img
                    src={attachment.url}
                    alt={attachment.name}
                    className="h-12 w-12 object-cover rounded"
                  />
                ) : (
                  <div className="flex items-center gap-2">
                    <Paperclip className="h-4 w-4 text-purple-400" />
                    <span className="text-xs text-purple-300 truncate max-w-[100px]">
                      {attachment.name}
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Message metadata */}
        {showMetadata && message.aiData && (
          <div className="text-xs text-purple-400 mt-2 border-t border-purple-500/20 pt-2">
            <div className="flex items-center gap-4">
              {(message as any).provider && (
                <div>
                  <span className="text-purple-300">Provider:</span>
                  <span className="text-white ml-1">{(message as any).provider}</span>
                </div>
              )}
              {(message as any).model && (
                <div>
                  <span className="text-purple-300">Model:</span>
                  <span className="text-white ml-1">{(message as any).model}</span>
                </div>
              )}
              {message.aiData.confidence && (
                <div>
                  <span className="text-purple-300">Confidence:</span>
                  <span className="text-white ml-1">
                    {Math.round(message.aiData.confidence * 100)}%
                  </span>
                </div>
              )}
              {(message as any).tokens && (
                <div>
                  <span className="text-purple-300">Tokens:</span>
                  <span className="text-white ml-1">
                    {(message as any).tokens.input} / {(message as any).tokens.output}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Reactions */}
        {showReactions && (message as any).reactions && (message as any).reactions.length > 0 && (
          <div className="flex items-center gap-1 mt-2">
            {(message as any).reactions.map((reaction: any) => (
              <div
                key={reaction.id}
                className="flex items-center bg-purple-500/30 rounded-full px-2 py-1 text-xs"
                title={`${reaction.userId} reacted with ${reaction.emoji}`}
              >
                {reaction.emoji}
                <span className="ml-1 text-purple-300">
                  {reaction.count > 1 ? reaction.count : ''}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Actions */}
        {showActions && !isSending && (
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleBookmark}
              className="text-purple-400 hover:text-purple-300 hover:bg-purple-500/10 p-1 rounded"
              title={isBookmarked ? 'Remove bookmark' : 'Add bookmark'}
            >
              {isBookmarked ? (
                <BookmarkCheck className="h-4 w-4" />
              ) : (
                <Bookmark className="h-4 w-4" />
              )}
            </Button>

            <Button
              variant="ghost"
              size="sm"
              onClick={handleCopy}
              className="text-purple-400 hover:text-purple-300 hover:bg-purple-500/10 p-1 rounded"
              title="Copy message"
            >
              {copied ? (
                <div className="text-green-400">
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L4.586 18.414a1 1 0 01.707-.293l-10-10 10.586a1 1 0 01.707.293L17 13a4 4 0 01-4.957-4.957L8.586 8.043a3 3 0 00-4.242 4.242L12 11.586a3 3 0 00-1.657-3.243l-1.242-1.242A3 3 0 00-4.243 4.242l1.242 1.242A3 3 0 001.657 3.243l1.242 1.242A3 3 0 004.242 4.242l1.242 1.242A3 3 0 004.957 4.957L17 11a4 4 0 01-4.957 4.957z" />
                  </svg>
                </div>
              ) : (
                <Copy className="h-4 w-4" />
              )}
            </Button>

            {isError && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleRetry}
                className="text-purple-400 hover:text-purple-300 hover:bg-purple-500/10 p-1 rounded"
                title="Retry message"
              >
                <RotateCcw className="h-4 w-4" />
              </Button>
            )}

            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowActionsMenu(!showActionsMenu)}
              className="text-purple-400 hover:text-purple-300 hover:bg-purple-500/10 p-1 rounded"
              title="More options"
            >
              <MoreHorizontal className="h-4 w-4" />
            </Button>

            {/* Actions menu */}
            {showActionsMenu && (
              <div className="absolute right-0 top-full mt-1 bg-black/90 backdrop-blur-md border border-purple-500/30 rounded-lg p-2 z-10 min-w-[150px]">
                <div className="flex flex-col gap-1">
                  <button className="text-left text-white hover:bg-purple-500/20 p-2 rounded text-sm w-full">
                    Edit
                  </button>
                  <button className="text-left text-white hover:bg-purple-500/20 p-2 rounded text-sm w-full">
                    Forward
                  </button>
                  <button className="text-left text-white hover:bg-purple-500/20 p-2 rounded text-sm w-full">
                    Delete
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}