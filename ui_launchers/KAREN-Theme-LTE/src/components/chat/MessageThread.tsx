/**
 * Message Thread Component - Handle message threading and replies
 */

import React, { useState, useRef, useEffect } from 'react';
import { Message, Conversation } from '../../types/conversation';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Textarea } from '../ui/textarea';
import { Avatar, AvatarFallback, AvatarImage } from '../ui/avatar';
import { Separator } from '../ui/separator';
import { 
  Reply,
  Forward,
  MoreVertical,
  User,
  Bot,
  Send,
  Paperclip,
  Smile,
  ChevronDown,
  ChevronUp,
  MessageSquare,
  Clock
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { formatDistanceToNow } from 'date-fns';

interface MessageThreadProps {
  conversationId: string;
  userId: string;
  onMessageSend?: (content: string, replyTo?: string) => void;
  className?: string;
}

interface ThreadedMessage extends Message {
  replies: ThreadedMessage[];
  replyCount: number;
  isExpanded: boolean;
}

export const MessageThread: React.FC<MessageThreadProps> = ({
  conversationId,
  userId,
  onMessageSend,
  className = ''
}) => {
  const [messages, setMessages] = useState<ThreadedMessage[]>([]);
  const [replyingTo, setReplyingTo] = useState<string | null>(null);
  const [replyContent, setReplyContent] = useState('');
  const [expandedThreads, setExpandedThreads] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Mock data - in real implementation, this would fetch from API
  const mockMessages: ThreadedMessage[] = [
    {
      id: 'msg_1',
      conversationId: conversationId,
      content: 'I need help with implementing a new feature in my React application.',
      role: 'user',
      timestamp: new Date(Date.now() - 86400000 * 2).toISOString(),
      metadata: {
        tokens: 12
      },
      replies: [
        {
          id: 'msg_2',
          conversationId: conversationId,
          content: 'I\'d be happy to help! What specific feature are you working on?',
          role: 'assistant',
          timestamp: new Date(Date.now() - 86400000 * 2 + 60000).toISOString(),
          metadata: {
            provider: 'OpenAI',
            model: 'gpt-4',
            tokens: 14
          },
          replies: [],
          replyCount: 0,
          isExpanded: false
        }
      ],
      replyCount: 1,
      isExpanded: true
    },
    {
      id: 'msg_3',
      conversationId: conversationId,
      content: 'I\'m trying to implement real-time chat functionality with WebSocket. Can you guide me through the process?',
      role: 'user',
      timestamp: new Date(Date.now() - 86400000).toISOString(),
      metadata: {
        tokens: 18
      },
      replies: [
        {
          id: 'msg_4',
          conversationId: conversationId,
          content: 'Great choice! WebSocket is perfect for real-time chat. Here\'s a step-by-step approach:\n\n1. Set up WebSocket server\n2. Implement client-side WebSocket connection\n3. Handle message broadcasting\n4. Add user authentication\n5. Implement message history\n\nWould you like me to elaborate on any of these steps?',
          role: 'assistant',
          timestamp: new Date(Date.now() - 86400000 + 120000).toISOString(),
          metadata: {
            provider: 'OpenAI',
            model: 'gpt-4',
            tokens: 65
          },
          replies: [
            {
              id: 'msg_5',
              conversationId: conversationId,
              content: 'Yes, please focus on step 1 and 2. I\'m using Node.js for the backend.',
              role: 'user',
              timestamp: new Date(Date.now() - 86400000 + 180000).toISOString(),
              metadata: {
                tokens: 15
              },
              replies: [],
              replyCount: 0,
              isExpanded: false
            }
          ],
          replyCount: 1,
          isExpanded: true
        }
      ],
      replyCount: 2,
      isExpanded: true
    }
  ];

  useEffect(() => {
    loadMessages();
  }, [conversationId]);

  const loadMessages = async () => {
    setLoading(true);
    
    // Simulate API call
    setTimeout(() => {
      setMessages(mockMessages);
      setLoading(false);
    }, 800);
  };

  const toggleThreadExpansion = (messageId: string) => {
    setExpandedThreads(prev => {
      const newSet = new Set(prev);
      if (newSet.has(messageId)) {
        newSet.delete(messageId);
      } else {
        newSet.add(messageId);
      }
      return newSet;
    });

    // Update message expansion state
    setMessages(prev => prev.map(msg => {
      if (msg.id === messageId) {
        return { ...msg, isExpanded: !msg.isExpanded };
      }
      return msg;
    }));
  };

  const handleReply = (messageId: string) => {
    setReplyingTo(messageId);
    setReplyContent('');
    // Focus textarea after a short delay
    setTimeout(() => {
      textareaRef.current?.focus();
    }, 100);
  };

  const handleSendReply = () => {
    if (!replyContent.trim() || !replyingTo) return;

    // Create new reply message
    const newReply: ThreadedMessage = {
      id: `msg_${Date.now()}`,
      conversationId,
      content: replyContent,
      role: 'user',
      timestamp: new Date().toISOString(),
      metadata: {
        tokens: replyContent.split(' ').length
      },
      replies: [],
      replyCount: 0,
      isExpanded: false
    };

    // Add reply to the appropriate message
    setMessages(prev => prev.map(msg => {
      if (msg.id === replyingTo) {
        return {
          ...msg,
          replies: [...msg.replies, newReply],
          replyCount: msg.replyCount + 1
        };
      }
      // Also check nested replies
      if (msg.replies.length > 0) {
        return {
          ...msg,
          replies: msg.replies.map(reply => {
            if (reply.id === replyingTo) {
              return {
                ...reply,
                replies: [...reply.replies, newReply],
                replyCount: reply.replyCount + 1
              };
            }
            return reply;
          })
        };
      }
      return msg;
    }));

    // Reset reply form
    setReplyingTo(null);
    setReplyContent('');
    
    // Call parent handler if provided
    onMessageSend?.(replyContent, replyingTo);
  };

  const handleForward = (messageId: string) => {
    // In a real implementation, this would open a dialog to select a conversation
    console.log('Forward message:', messageId);
  };

  const MessageItem: React.FC<{ message: ThreadedMessage; depth?: number }> = ({ 
    message, 
    depth = 0 
  }) => {
    const isUser = message.role === 'user';
    const hasReplies = message.replies.length > 0;
    const isExpanded = expandedThreads.has(message.id) || message.isExpanded;

    return (
      <div className={cn('message-item', depth > 0 && 'ml-8 border-l-2 border-muted pl-4')}>
        <div className="flex gap-3 p-4 rounded-lg bg-card">
          {/* Avatar */}
          <Avatar className="h-8 w-8 mt-1">
            <AvatarFallback>
              {isUser ? (
                <User className="h-4 w-4" />
              ) : (
                <Bot className="h-4 w-4" />
              )}
            </AvatarFallback>
          </Avatar>

          {/* Message Content */}
          <div className="flex-1 space-y-2">
            {/* Message Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                {isUser ? (
                  <Badge variant="secondary">You</Badge>
                ) : (
                  <Badge variant="outline">
                    {message.metadata?.provider || 'Assistant'}
                  </Badge>
                )}
                <span className="text-xs text-muted-foreground">
                  {formatDistanceToNow(new Date(message.timestamp), { addSuffix: true })}
                </span>
              </div>
              
              <div className="flex items-center space-x-1">
                {hasReplies && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => toggleThreadExpansion(message.id)}
                    className="h-6 px-2"
                  >
                    <MessageSquare className="h-3 w-3 mr-1" />
                    {message.replyCount}
                    {isExpanded ? (
                      <ChevronUp className="h-3 w-3 ml-1" />
                    ) : (
                      <ChevronDown className="h-3 w-3 ml-1" />
                    )}
                  </Button>
                )}
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleReply(message.id)}
                  className="h-6 px-2"
                >
                  <Reply className="h-3 w-3" />
                </Button>
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleForward(message.id)}
                  className="h-6 px-2"
                >
                  <Forward className="h-3 w-3" />
                </Button>
                
                <Button variant="ghost" size="sm" className="h-6 px-2">
                  <MoreVertical className="h-3 w-3" />
                </Button>
              </div>
            </div>

            {/* Message Text */}
            <div className={cn(
              'text-sm p-3 rounded-lg',
              isUser ? 'bg-primary text-primary-foreground' : 'bg-muted'
            )}>
              {message.content}
            </div>

            {/* Message Metadata */}
            {message.metadata && (
              <div className="text-xs text-muted-foreground space-x-4">
                {message.metadata.tokens && (
                  <span>Tokens: {message.metadata.tokens}</span>
                )}
                {message.metadata.model && (
                  <span>Model: {message.metadata.model}</span>
                )}
                {message.metadata.provider && (
                  <span>Provider: {message.metadata.provider}</span>
                )}
              </div>
            )}

            {/* Reply Form */}
            {replyingTo === message.id && (
              <div className="mt-4 p-4 bg-muted rounded-lg space-y-3">
                <div className="flex items-center space-x-2 text-sm">
                  <Reply className="h-4 w-4" />
                  <span>Replying to message</span>
                </div>
                <Textarea
                  ref={textareaRef}
                  value={replyContent}
                  onChange={(e) => setReplyContent(e.target.value)}
                  placeholder="Type your reply..."
                  className="min-h-[80px]"
                />
                <div className="flex items-center justify-between">
                  <div className="flex space-x-2">
                    <Button variant="ghost" size="sm">
                      <Paperclip className="h-4 w-4 mr-2" />
                      Attach
                    </Button>
                    <Button variant="ghost" size="sm">
                      <Smile className="h-4 w-4 mr-2" />
                      Emoji
                    </Button>
                  </div>
                  <div className="flex space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setReplyingTo(null)}
                    >
                      Cancel
                    </Button>
                    <Button
                      size="sm"
                      onClick={handleSendReply}
                      disabled={!replyContent.trim()}
                    >
                      <Send className="h-4 w-4 mr-2" />
                      Send Reply
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Threaded Replies */}
        {hasReplies && isExpanded && (
          <div className="mt-4 space-y-4">
            {message.replies.map(reply => (
              <MessageItem key={reply.id} message={reply} depth={depth + 1} />
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={cn('message-thread', className)}>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <MessageSquare className="h-5 w-5" />
            <span>Message Threads</span>
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-4">
          {loading && (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
              <p className="text-muted-foreground ml-2">Loading messages...</p>
            </div>
          )}

          {!loading && messages.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No messages in this conversation yet.</p>
            </div>
          )}

          {!loading && messages.length > 0 && (
            <div className="space-y-4">
              {messages.map(message => (
                <MessageItem key={message.id} message={message} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};