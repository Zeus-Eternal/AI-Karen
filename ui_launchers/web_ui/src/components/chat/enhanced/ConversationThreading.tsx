import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import {
import { format, formatDistanceToNow } from 'date-fns';
'use client';








  MessageSquare,
  Plus,
  Search,
  Filter,
  Clock,
  Users,
  Tag,
  Archive,
  Trash2,
  MoreHorizontal,
  TrendingUp,
  Brain
} from 'lucide-react';

  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator
} from '@/components/ui/dropdown-menu';


  ConversationThread,
  ThreadMetadata,
  EnhancedChatMessage
} from '@/types/enhanced-chat';

interface ConversationThreadingProps {
  threads: ConversationThread[];
  activeThreadId?: string;
  onThreadSelect: (threadId: string) => void;
  onThreadCreate: (topic: string) => void;
  onThreadUpdate: (threadId: string, updates: Partial<ConversationThread>) => void;
  onThreadDelete: (threadId: string) => void;
  onThreadArchive: (threadId: string) => void;
  className?: string;
}

export const ConversationThreading: React.FC<ConversationThreadingProps> = ({
  threads,
  activeThreadId,
  onThreadSelect,
  onThreadCreate,
  onThreadUpdate,
  onThreadDelete,
  onThreadArchive,
  className = ''
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState<'all' | 'active' | 'archived'>('all');
  const [sortBy, setSortBy] = useState<'updated' | 'created' | 'messages'>('updated');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newThreadTopic, setNewThreadTopic] = useState('');

  // Filter and sort threads
  const filteredAndSortedThreads = useMemo(() => {
    let filtered = threads.filter(thread => {
      const matchesSearch = searchQuery === '' ||
        thread.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        thread.topic.toLowerCase().includes(searchQuery.toLowerCase()) ||
        thread.metadata.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
      
      const matchesFilter = filterStatus === 'all' || thread.status === filterStatus;
      
      return matchesSearch && matchesFilter;
    });

    // Sort threads
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'created':
          return b.createdAt.getTime() - a.createdAt.getTime();
        case 'messages':
          return b.metadata.messageCount - a.metadata.messageCount;
        case 'updated':
        default:
          return b.updatedAt.getTime() - a.updatedAt.getTime();
      }
    });

    return filtered;
  }, [threads, searchQuery, filterStatus, sortBy]);

  const handleCreateThread = () => {
    if (newThreadTopic.trim()) {
      onThreadCreate(newThreadTopic.trim());
      setNewThreadTopic('');
      setShowCreateForm(false);
    }
  };

  const getComplexityColor = (complexity: ThreadMetadata['complexity']) => {
    switch (complexity) {
      case 'simple':
        return 'bg-green-100 text-green-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'complex':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getSentimentColor = (sentiment: ThreadMetadata['sentiment']) => {
    switch (sentiment) {
      case 'positive':
        return 'text-green-600';
      case 'negative':
        return 'text-red-600';
      case 'neutral':
      default:
        return 'text-gray-600';
    }
  };

  const renderThreadItem = (thread: ConversationThread) => {
    const isActive = thread.id === activeThreadId;
    
    return (
      <div
        key={thread.id}
        className={`p-4 border rounded-lg cursor-pointer transition-all hover:shadow-sm ${
          isActive ? 'border-primary bg-primary/5' : 'hover:bg-muted/50'
        }`}
        onClick={() => onThreadSelect(thread.id)}
      >
        <div className="flex items-start justify-between mb-2">
          <div className="flex-1 min-w-0 sm:w-auto md:w-full">
            <h3 className="font-medium text-sm truncate md:text-base lg:text-lg">{thread.title}</h3>
            <p className="text-xs text-muted-foreground mt-1 sm:text-sm md:text-base">{thread.topic}</p>
          </div>
          
          <div className="flex items-center gap-2 ml-2">
            <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
              {thread.metadata.messageCount}
            </Badge>
            
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button variant="ghost" size="sm" className="h-6 w-6 p-0 sm:w-auto md:w-full" aria-label="Button">
                  <MoreHorizontal className="h-3 w-3 sm:w-auto md:w-full" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={(e) => {
                  e.stopPropagation();
                  onThreadArchive(thread.id);
                }}>
                  <Archive className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                  {thread.status === 'archived' ? 'Unarchive' : 'Archive'}
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem 
                  onClick={(e) => {
                    e.stopPropagation();
                    onThreadDelete(thread.id);
                  }}
                  className="text-destructive"
                >
                  <Trash2 className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {/* Thread metadata */}
        <div className="flex items-center gap-2 mb-2">
          <span className={`px-2 py-1 rounded-full text-xs ${getComplexityColor(thread.metadata.complexity)}`}>
            {thread.metadata.complexity}
          </span>
          
          <div className={`flex items-center gap-1 text-xs ${getSentimentColor(thread.metadata.sentiment)}`}>
            <TrendingUp className="h-3 w-3 sm:w-auto md:w-full" />
            {thread.metadata.sentiment}
          </div>
          
          {thread.metadata.tags.length > 0 && (
            <div className="flex items-center gap-1">
              <Tag className="h-3 w-3 text-muted-foreground sm:w-auto md:w-full" />
              <span className="text-xs text-muted-foreground sm:text-sm md:text-base">
                {thread.metadata.tags.slice(0, 2).join(', ')}
                {thread.metadata.tags.length > 2 && '...'}
              </span>
            </div>
          )}
        </div>

        {/* Thread summary if available */}
        {thread.metadata.summary && (
          <p className="text-xs text-muted-foreground mb-2 line-clamp-2 sm:text-sm md:text-base">
            {thread.metadata.summary}
          </p>
        )}

        {/* Thread stats */}
        <div className="flex items-center justify-between text-xs text-muted-foreground sm:text-sm md:text-base">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1">
              <Clock className="h-3 w-3 sm:w-auto md:w-full" />
              {formatDistanceToNow(thread.updatedAt, { addSuffix: true })}
            </span>
            
            <span className="flex items-center gap-1">
              <Users className="h-3 w-3 sm:w-auto md:w-full" />
              {thread.participants.length}
            </span>
          </div>
          
          <div className="flex items-center gap-1">
            <Brain className="h-3 w-3 sm:w-auto md:w-full" />
            <span>{Math.round(thread.metadata.averageResponseTime)}ms avg</span>
          </div>
        </div>
      </div>
    );
  };

  return (
    <Card className={`h-full flex flex-col ${className}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            <MessageSquare className="h-5 w-5 sm:w-auto md:w-full" />
            Conversations
          </CardTitle>
          
          <button
            size="sm"
            onClick={() = aria-label="Button"> setShowCreateForm(true)}
            className="h-8"
          >
            <Plus className="h-4 w-4 mr-1 sm:w-auto md:w-full" />
            New
          </Button>
        </div>

        {/* Create new thread form */}
        {showCreateForm && (
          <div className="space-y-2 p-3 border rounded-lg bg-muted/50 sm:p-4 md:p-6">
            <input
              placeholder="Enter conversation topic..."
              value={newThreadTopic}
              onChange={(e) = aria-label="Input"> setNewThreadTopic(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  handleCreateThread();
                } else if (e.key === 'Escape') {
                  setShowCreateForm(false);
                  setNewThreadTopic('');
                }
              }}
              autoFocus
            />
            <div className="flex gap-2">
              <button size="sm" onClick={handleCreateThread} aria-label="Button">
                Create
              </Button>
              <button 
                size="sm" 
                variant="outline" 
                onClick={() = aria-label="Button"> {
                  setShowCreateForm(false);
                  setNewThreadTopic('');
                }}
              >
                Cancel
              </Button>
            </div>
          </div>
        )}

        {/* Search and filters */}
        <div className="space-y-2">
          <div className="relative">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
            <input
              placeholder="Search conversations..."
              value={searchQuery}
              onChange={(e) = aria-label="Input"> setSearchQuery(e.target.value)}
              className="pl-8 h-9"
            />
          </div>
          
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
            
            <select
              value={filterStatus}
              onChange={(e) = aria-label="Select option"> setFilterStatus(e.target.value as any)}
              className="text-sm border rounded px-2 py-1 bg-background md:text-base lg:text-lg"
            >
              <option value="all">All</option>
              <option value="active">Active</option>
              <option value="archived">Archived</option>
            </select>
            
            <select
              value={sortBy}
              onChange={(e) = aria-label="Select option"> setSortBy(e.target.value as any)}
              className="text-sm border rounded px-2 py-1 bg-background md:text-base lg:text-lg"
            >
              <option value="updated">Last Updated</option>
              <option value="created">Created</option>
              <option value="messages">Message Count</option>
            </select>
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex-1 p-0 sm:p-4 md:p-6">
        <ScrollArea className="h-full px-4">
          <div className="space-y-3 pb-4">
            {filteredAndSortedThreads.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50 sm:w-auto md:w-full" />
                <p className="text-sm md:text-base lg:text-lg">
                  {searchQuery || filterStatus !== 'all' 
                    ? 'No conversations match your filters' 
                    : 'No conversations yet'}
                </p>
                {!searchQuery && filterStatus === 'all' && (
                  <button
                    variant="outline"
                    size="sm"
                    className="mt-2"
                    onClick={() = aria-label="Button"> setShowCreateForm(true)}
                  >
                    Start a conversation
                  </Button>
                )}
              </div>
            ) : (
              filteredAndSortedThreads.map(renderThreadItem)
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
};

export default ConversationThreading;