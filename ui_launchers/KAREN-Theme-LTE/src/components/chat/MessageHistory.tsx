/**
 * Message History Component - Display complete message history for conversations
 */

import React, { useState, useEffect, useRef } from 'react';
import { Message, Conversation } from '../../types/conversation';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Input } from '../ui/input';
import { ScrollArea } from '../ui/scroll-area';
import { Separator } from '../ui/separator';
import { Avatar, AvatarFallback, AvatarImage } from '../ui/avatar';
import { 
  Search,
  Filter,
  Calendar,
  User,
  Bot,
  MessageSquare,
  Reply,
  Forward,
  Download,
  MoreVertical,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { formatDistanceToNow } from 'date-fns';

interface MessageHistoryProps {
  conversationId: string;
  userId: string;
  className?: string;
}

interface MessageGroup {
  date: string;
  messages: Message[];
}

export const MessageHistory: React.FC<MessageHistoryProps> = ({
  conversationId,
  userId,
  className = ''
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedMessages, setExpandedMessages] = useState<Set<string>>(new Set());
  const [showFilters, setShowFilters] = useState(false);
  const [dateFilter, setDateFilter] = useState<string>('');
  const [senderFilter, setSenderFilter] = useState<string>('all');
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  // Mock data - in real implementation, this would fetch from API
  const mockMessages: Message[] = [
    {
      id: 'msg_1',
      conversationId: conversationId,
      content: 'Hello! How can I help you today?',
      role: 'assistant',
      timestamp: new Date(Date.now() - 86400000 * 2).toISOString(), // 2 days ago
      metadata: {
        provider: 'OpenAI',
        model: 'gpt-4',
        tokens: 25,
        processingTime: 1.2
      }
    },
    {
      id: 'msg_2',
      conversationId: conversationId,
      content: 'I need help with my project. Can you provide some guidance?',
      role: 'user',
      timestamp: new Date(Date.now() - 86400000 * 2 + 60000).toISOString(), // 2 days ago + 1 min
      metadata: {
        tokens: 18
      }
    },
    {
      id: 'msg_3',
      conversationId: conversationId,
      content: 'Of course! I\'d be happy to help with your project. What specific area do you need guidance on? Are you looking for technical advice, project planning, or something else?',
      role: 'assistant',
      timestamp: new Date(Date.now() - 86400000 * 2 + 120000).toISOString(), // 2 days ago + 2 min
      metadata: {
        provider: 'OpenAI',
        model: 'gpt-4',
        tokens: 42,
        processingTime: 1.8
      }
    },
    {
      id: 'msg_4',
      conversationId: conversationId,
      content: 'I\'m working on a React application and need help with state management.',
      role: 'user',
      timestamp: new Date(Date.now() - 86400000 + 3600000).toISOString(), // 1 day ago + 1 hour
      metadata: {
        tokens: 16
      }
    },
    {
      id: 'msg_5',
      conversationId: conversationId,
      content: 'Great! React state management is a crucial topic. There are several approaches you can take:\n\n1. **Local State**: Use useState for component-specific state\n2. **Context API**: For sharing state between components\n3. **State Libraries**: Redux, MobX, or Zustand for complex applications\n\nWhich approach interests you most, or would you like me to explain all of them?',
      role: 'assistant',
      timestamp: new Date(Date.now() - 86400000 + 3660000).toISOString(), // 1 day ago + 1 hour 1 min
      metadata: {
        provider: 'OpenAI',
        model: 'gpt-4',
        tokens: 78,
        processingTime: 2.5
      }
    }
  ];

  useEffect(() => {
    loadMessages();
  }, [conversationId, page, searchQuery, dateFilter, senderFilter]);

  const loadMessages = async () => {
    setLoading(true);
    
    // Simulate API call
    setTimeout(() => {
      // In real implementation, this would fetch from the API
      if (page === 1) {
        setMessages(mockMessages);
      } else {
        // Append more messages for pagination
        setMessages(prev => [...prev, ...mockMessages]);
      }
      
      setLoading(false);
      // Simulate no more pages after 3
      setHasMore(page < 3);
    }, 800);
  };

  const groupMessagesByDate = (messages: Message[]): MessageGroup[] => {
    const groups: { [key: string]: Message[] } = {};
    
    messages.forEach(message => {
      const date = new Date(message.timestamp).toDateString();
      if (!groups[date]) {
        groups[date] = [];
      }
      groups[date].push(message);
    });

    return Object.entries(groups).map(([date, msgs]) => ({
      date,
      messages: msgs
    }));
  };

  const toggleMessageExpansion = (messageId: string) => {
    setExpandedMessages(prev => {
      const newSet = new Set(prev);
      if (newSet.has(messageId)) {
        newSet.delete(messageId);
      } else {
        newSet.add(messageId);
      }
      return newSet;
    });
  };

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    setPage(1);
  };

  const handleFilterChange = (filterType: 'date' | 'sender', value: string) => {
    if (filterType === 'date') {
      setDateFilter(value);
    } else {
      setSenderFilter(value);
    }
    setPage(1);
  };

  const loadMore = () => {
    if (!loading && hasMore) {
      setPage(prev => prev + 1);
    }
  };

  const formatMessageContent = (content: string) => {
    // Simple markdown-like formatting
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code class="bg-muted px-1 py-0.5 rounded text-sm">$1</code>')
      .replace(/\n/g, '<br />');
  };

  const messageGroups = groupMessagesByDate(messages);

  return (
    <div className={cn('message-history', className)}>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <MessageSquare className="h-5 w-5" />
              <span>Message History</span>
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowFilters(!showFilters)}
              >
                <Filter className="h-4 w-4 mr-2" />
                Filters
              </Button>
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
            </div>
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Search Bar */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search messages..."
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Filters */}
          {showFilters && (
            <div className="flex flex-wrap gap-4 p-4 bg-muted rounded-lg">
              <div className="flex items-center space-x-2">
                <Calendar className="h-4 w-4" />
                <Input
                  type="date"
                  placeholder="Filter by date"
                  value={dateFilter}
                  onChange={(e) => handleFilterChange('date', e.target.value)}
                  className="w-auto"
                />
              </div>
              <div className="flex items-center space-x-2">
                <User className="h-4 w-4" />
                <select
                  value={senderFilter}
                  onChange={(e) => handleFilterChange('sender', e.target.value)}
                  className="px-3 py-2 border rounded-md bg-background"
                >
                  <option value="all">All Senders</option>
                  <option value="user">User</option>
                  <option value="assistant">Assistant</option>
                </select>
              </div>
            </div>
          )}

          {/* Message List */}
          <ScrollArea ref={scrollAreaRef} className="h-[600px] pr-4">
            <div className="space-y-6">
              {messageGroups.map((group, groupIndex) => (
                <div key={group.date}>
                  {/* Date Separator */}
                  <div className="flex items-center justify-center my-4">
                    <Separator className="flex-1" />
                    <Badge variant="outline" className="mx-2">
                      {group.date === new Date().toDateString() ? 'Today' : 
                       group.date === new Date(Date.now() - 86400000).toDateString() ? 'Yesterday' :
                       group.date}
                    </Badge>
                    <Separator className="flex-1" />
                  </div>

                  {/* Messages for this date */}
                  <div className="space-y-4">
                    {group.messages.map((message) => (
                      <div
                        key={message.id}
                        className={cn(
                          'flex gap-3 p-4 rounded-lg transition-colors hover:bg-muted/50',
                          message.role === 'user' ? 'justify-end' : 'justify-start'
                        )}
                      >
                        {message.role === 'assistant' && (
                          <Avatar className="h-8 w-8 mt-1">
                            <AvatarFallback>
                              <Bot className="h-4 w-4" />
                            </AvatarFallback>
                          </Avatar>
                        )}

                        <div className={cn(
                          'max-w-[70%] space-y-2',
                          message.role === 'user' ? 'items-end' : 'items-start'
                        )}>
                          {/* Message Header */}
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-2">
                              {message.role === 'user' ? (
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
                            
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => toggleMessageExpansion(message.id)}
                            >
                              {expandedMessages.has(message.id) ? (
                                <ChevronUp className="h-4 w-4" />
                              ) : (
                                <ChevronDown className="h-4 w-4" />
                              )}
                            </Button>
                          </div>

                          {/* Message Content */}
                          <div
                            className={cn(
                              'p-3 rounded-lg',
                              message.role === 'user' 
                                ? 'bg-primary text-primary-foreground' 
                                : 'bg-muted'
                            )}
                          >
                            <div
                              dangerouslySetInnerHTML={{ __html: formatMessageContent(message.content) }}
                              className={cn(
                                'text-sm',
                                message.role === 'user' ? 'text-primary-foreground' : 'text-foreground'
                              )}
                            />
                          </div>

                          {/* Expanded Metadata */}
                          {expandedMessages.has(message.id) && message.metadata && (
                            <div className="p-3 bg-muted/50 rounded-lg text-xs space-y-1">
                              {message.metadata.provider && (
                                <div>Provider: {message.metadata.provider}</div>
                              )}
                              {message.metadata.model && (
                                <div>Model: {message.metadata.model}</div>
                              )}
                              {message.metadata.tokens && (
                                <div>Tokens: {message.metadata.tokens}</div>
                              )}
                              {(typeof message.metadata.processingTime === 'number') && (
                                <div>Processing Time: {message.metadata.processingTime as number}s</div>
                              )}
                            </div>
                          )}

                          {/* Message Actions */}
                          <div className="flex items-center space-x-2">
                            <Button variant="ghost" size="sm">
                              <Reply className="h-4 w-4 mr-1" />
                              Reply
                            </Button>
                            <Button variant="ghost" size="sm">
                              <Forward className="h-4 w-4 mr-1" />
                              Forward
                            </Button>
                            <Button variant="ghost" size="sm">
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>

                        {message.role === 'user' && (
                          <Avatar className="h-8 w-8 mt-1">
                            <AvatarFallback>
                              <User className="h-4 w-4" />
                            </AvatarFallback>
                          </Avatar>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {/* Load More */}
            {hasMore && (
              <div className="flex justify-center mt-6">
                <Button
                  variant="outline"
                  onClick={loadMore}
                  disabled={loading}
                >
                  {loading ? 'Loading...' : 'Load More Messages'}
                </Button>
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
};
