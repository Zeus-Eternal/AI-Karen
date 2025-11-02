
"use client";
import React, { useState, useMemo } from 'react';
import { ErrorBoundary } from '@/components/error-handling/ErrorBoundary';
import { useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { format, formatDistanceToNow } from 'date-fns';
import { useToast } from '@/hooks/use-toast';

import { } from '@/components/ui/select';

import { } from '@/components/ui/dropdown-menu';

import { } from '@/components/ui/dialog';
import { } from 'lucide-react';



import { } from '@/types/enhanced-chat';

interface ConversationAnalytics {
  totalConversations: number;
  totalMessages: number;
  averageLength: number;
  topTopics: Array<{ topic: string; count: number }>;
  sentimentDistribution: {
    positive: number;
    neutral: number;
    negative: number;
  };
  complexityDistribution: {
    simple: number;
    medium: number;
    complex: number;
  };
  activityByDay: Array<{ date: string; count: number }>;
}

interface ConversationManagerProps {
  conversations: ConversationThread[];
  analytics?: ConversationAnalytics;
  onConversationSelect: (conversationId: string) => void;
  onConversationUpdate: (conversationId: string, updates: Partial<ConversationThread>) => void;
  onConversationDelete: (conversationId: string) => void;
  onConversationArchive: (conversationId: string) => void;
  onConversationExport: (conversationIds: string[]) => void;
  onConversationShare: (conversationId: string) => void;
  className?: string;
}

export const ConversationManager: React.FC<ConversationManagerProps> = ({
  conversations,
  analytics,
  onConversationSelect,
  onConversationUpdate,
  onConversationDelete,
  onConversationArchive,
  onConversationExport,
  onConversationShare,
  className = ''
}) => {
  const { toast } = useToast();
  
  // State
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'archived'>('all');
  const [topicFilter, setTopicFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'updated' | 'created' | 'messages' | 'title'>('updated');
  const [selectedConversations, setSelectedConversations] = useState<Set<string>>(new Set());
  const [showAnalytics, setShowAnalytics] = useState(false);

  // Get unique topics for filtering
  const availableTopics = useMemo(() => {
    const topics = new Set<string>();
    conversations.forEach(conv => {
      conv.metadata.tags.forEach(tag => topics.add(tag));
      if (conv.topic) topics.add(conv.topic);

    return Array.from(topics).sort();
  }, [conversations]);

  // Filter and sort conversations
  const filteredAndSortedConversations = useMemo(() => {
    let filtered = conversations.filter(conv => {
      const matchesSearch = searchQuery === '' ||
        conv.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        conv.topic.toLowerCase().includes(searchQuery.toLowerCase()) ||
        conv.metadata.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
      
      const matchesStatus = statusFilter === 'all' || conv.status === statusFilter;
      
      const matchesTopic = topicFilter === 'all' ||
        conv.topic === topicFilter ||
        conv.metadata.tags.includes(topicFilter);
      
      return matchesSearch && matchesStatus && matchesTopic;

    // Sort conversations
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'created':
          return b.createdAt.getTime() - a.createdAt.getTime();
        case 'messages':
          return b.metadata.messageCount - a.metadata.messageCount;
        case 'title':
          return a.title.localeCompare(b.title);
        case 'updated':
        default:
          return b.updatedAt.getTime() - a.updatedAt.getTime();
      }

    return filtered;
  }, [conversations, searchQuery, statusFilter, topicFilter, sortBy]);

  // Handle conversation selection
  const toggleConversationSelection = (conversationId: string) => {
    setSelectedConversations(prev => {
      const newSet = new Set(prev);
      if (newSet.has(conversationId)) {
        newSet.delete(conversationId);
      } else {
        newSet.add(conversationId);
      }
      return newSet;

  };

  // Handle bulk operations
  const handleBulkExport = () => {
    if (selectedConversations.size === 0) {
      toast({
        variant: 'destructive',
        title: 'No Selection',
        description: 'Please select conversations to export'

      return;
    }
    
    onConversationExport(Array.from(selectedConversations));
    setSelectedConversations(new Set());
  };

  const handleBulkArchive = () => {
    if (selectedConversations.size === 0) return;
    
    selectedConversations.forEach(id => onConversationArchive(id));
    setSelectedConversations(new Set());
    
    toast({
      title: 'Conversations Archived',
      description: `${selectedConversations.size} conversations have been archived`

  };

  // Get sentiment color
  const getSentimentColor = (sentiment: ThreadMetadata['sentiment']) => {
    switch (sentiment) {
      case 'positive':
        return 'text-green-600 bg-green-50';
      case 'negative':
        return 'text-red-600 bg-red-50';
      case 'neutral':
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  // Get complexity color
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

  // Render conversation item
  const renderConversationItem = (conversation: ConversationThread) => {
    const isSelected = selectedConversations.has(conversation.id);

  // Focus management for accessibility
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        // Handle escape key
        onClose?.();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

    
    return (
    <ErrorBoundary fallback={<div>Something went wrong in ConversationManager</div>}>
      <Card 
        key={conversation.id}
        className={`cursor-pointer transition-all hover:shadow-sm ${
          isSelected ? 'ring-2 ring-primary' : ''
        }`}
        onClick={() => onConversationSelect(conversation.id)}
      >
        <CardContent className="p-4 sm:p-4 md:p-6">
          <div className="flex items-start gap-3">
            {/* Selection Checkbox */}
            <input
              type="checkbox"
              checked={isSelected}
              onChange={(e) => {
                e.stopPropagation();
                toggleConversationSelection(conversation.id);
              }}
              className="mt-1"
            />

            {/* Conversation Content */}
            <div className="flex-1 min-w-0 ">
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1 min-w-0 ">
                  <h3 className="text-sm font-medium truncate md:text-base lg:text-lg">
                    {conversation.title}
                  </h3>
                  <p className="text-xs text-muted-foreground mt-1 sm:text-sm md:text-base">
                    {conversation.topic}
                  </p>
                </div>
                
                <DropdownMenu>
                  <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                    <Button variant="ghost" size="sm" className="h-6 w-6 p-0 " >
                      <MoreHorizontal className="h-3 w-3 " />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => onConversationShare(conversation.id)}>
                      <Share2 className="h-4 w-4 mr-2 " />
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => onConversationExport([conversation.id])}>
                      <Download className="h-4 w-4 mr-2 " />
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={() => onConversationArchive(conversation.id)}>
                      <Archive className="h-4 w-4 mr-2 " />
                      {conversation.status === 'archived' ? 'Unarchive' : 'Archive'}
                    </DropdownMenuItem>
                    <DropdownMenuItem 
                      onClick={() => onConversationDelete(conversation.id)}
                      className="text-destructive"
                    >
                      <Trash2 className="h-4 w-4 mr-2 " />
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>

              {/* Metadata */}
              <div className="flex items-center gap-2 mb-2">
                <Badge className={`text-xs ${getComplexityColor(conversation.metadata.complexity)}`}>
                  {conversation.metadata.complexity}
                </Badge>
                
                <div className={`px-2 py-1 rounded text-xs ${getSentimentColor(conversation.metadata.sentiment)}`}>
                  {conversation.metadata.sentiment}
                </div>
                
                <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                  {conversation.metadata.messageCount} messages
                </Badge>
              </div>

              {/* Tags */}
              {conversation.metadata.tags.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-2">
                  {conversation.metadata.tags.slice(0, 3).map(tag => (
                    <Badge key={tag} variant="secondary" className="text-xs sm:text-sm md:text-base">
                      {tag}
                    </Badge>
                  ))}
                  {conversation.metadata.tags.length > 3 && (
                    <Badge variant="secondary" className="text-xs sm:text-sm md:text-base">
                      +{conversation.metadata.tags.length - 3}
                    </Badge>
                  )}
                </div>
              )}

              {/* Summary */}
              {conversation.metadata.summary && (
                <p className="text-xs text-muted-foreground mb-2 line-clamp-2 sm:text-sm md:text-base">
                  {conversation.metadata.summary}
                </p>
              )}

              {/* Stats */}
              <div className="flex items-center justify-between text-xs text-muted-foreground sm:text-sm md:text-base">
                <div className="flex items-center gap-3">
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3 " />
                    {formatDistanceToNow(conversation.updatedAt, { addSuffix: true })}
                  </span>
                  
                  <span className="flex items-center gap-1">
                    <Users className="h-3 w-3 " />
                    {conversation.participants.length}
                  </span>
                </div>
                
                <div className="flex items-center gap-1">
                  <TrendingUp className="h-3 w-3 " />
                  <span>{Math.round(conversation.metadata.averageResponseTime)}ms</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  // Render analytics
  const renderAnalytics = () => {
    if (!analytics) return null;

    return (
      <div className="space-y-6">
        {/* Overview Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4 text-center sm:p-4 md:p-6">
              <div className="text-2xl font-bold text-primary">
                {analytics.totalConversations}
              </div>
              <div className="text-sm text-muted-foreground md:text-base lg:text-lg">
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4 text-center sm:p-4 md:p-6">
              <div className="text-2xl font-bold text-primary">
                {analytics.totalMessages}
              </div>
              <div className="text-sm text-muted-foreground md:text-base lg:text-lg">
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4 text-center sm:p-4 md:p-6">
              <div className="text-2xl font-bold text-primary">
                {Math.round(analytics.averageLength)}
              </div>
              <div className="text-sm text-muted-foreground md:text-base lg:text-lg">
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4 text-center sm:p-4 md:p-6">
              <div className="text-2xl font-bold text-primary">
                {analytics.topTopics.length}
              </div>
              <div className="text-sm text-muted-foreground md:text-base lg:text-lg">
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Top Topics */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm md:text-base lg:text-lg">Top Topics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {analytics.topTopics.slice(0, 5).map((topic, index) => (
                <div key={topic.topic} className="flex items-center justify-between">
                  <span className="text-sm md:text-base lg:text-lg">{topic.topic}</span>
                  <div className="flex items-center gap-2">
                    <div className="w-20 bg-muted rounded-full h-2 ">
                      <div 
                        className="bg-primary h-2 rounded-full"
                        style={{ 
                          width: `${(topic.count / analytics.topTopics[0].count) * 100}%` 
                        }}
                      />
                    </div>
                    <span className="text-xs text-muted-foreground w-8 ">
                      {topic.count}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Sentiment Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm md:text-base lg:text-lg">Sentiment Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-green-600 md:text-base lg:text-lg">Positive</span>
                <span className="text-sm font-medium md:text-base lg:text-lg">
                  {Math.round(analytics.sentimentDistribution.positive)}%
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 md:text-base lg:text-lg">Neutral</span>
                <span className="text-sm font-medium md:text-base lg:text-lg">
                  {Math.round(analytics.sentimentDistribution.neutral)}%
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-red-600 md:text-base lg:text-lg">Negative</span>
                <span className="text-sm font-medium md:text-base lg:text-lg">
                  {Math.round(analytics.sentimentDistribution.negative)}%
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  return (
    <Card className={`h-full flex flex-col ${className}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5 " />
          </CardTitle>
          
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
              {filteredAndSortedConversations.length} of {conversations.length}
            </Badge>
            
            {selectedConversations.size > 0 && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm" >
                    Actions ({selectedConversations.size})
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent>
                  <DropdownMenuItem onClick={handleBulkExport}>
                    <Download className="h-4 w-4 mr-2 " />
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={handleBulkArchive}>
                    <Archive className="h-4 w-4 mr-2 " />
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            )}
          </div>
        </div>

        {/* Filters */}
        <div className="space-y-3">
          <div className="relative">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground " />
            <input
              placeholder="Search conversations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 h-9"
            />
          </div>
          
          <div className="flex items-center gap-2 flex-wrap">
            <Filter className="h-4 w-4 text-muted-foreground " />
            
            <select value={statusFilter} onValueChange={(value) = aria-label="Select option"> setStatusFilter(value as any)}>
              <selectTrigger className="w-32 h-8 text-xs " aria-label="Select option">
                <selectValue />
              </SelectTrigger>
              <selectContent aria-label="Select option">
                <selectItem value="all" aria-label="Select option">All Status</SelectItem>
                <selectItem value="active" aria-label="Select option">Active</SelectItem>
                <selectItem value="archived" aria-label="Select option">Archived</SelectItem>
              </SelectContent>
            </Select>
            
            <select value={topicFilter} onValueChange={setTopicFilter} aria-label="Select option">
              <selectTrigger className="w-32 h-8 text-xs " aria-label="Select option">
                <selectValue />
              </SelectTrigger>
              <selectContent aria-label="Select option">
                <selectItem value="all" aria-label="Select option">All Topics</SelectItem>
                {availableTopics.map(topic => (
                  <selectItem key={topic} value={topic} aria-label="Select option">{topic}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            <select value={sortBy} onValueChange={(value) = aria-label="Select option"> setSortBy(value as any)}>
              <selectTrigger className="w-32 h-8 text-xs " aria-label="Select option">
                <selectValue />
              </SelectTrigger>
              <selectContent aria-label="Select option">
                <selectItem value="updated" aria-label="Select option">Last Updated</SelectItem>
                <selectItem value="created" aria-label="Select option">Created</SelectItem>
                <selectItem value="messages" aria-label="Select option">Message Count</SelectItem>
                <SelectItem value="title">Title</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex-1 p-0 sm:p-4 md:p-6">
        <Tabs defaultValue="conversations" className="h-full flex flex-col">
          <TabsList className="mx-4">
            <TabsTrigger value="conversations">
              Conversations ({filteredAndSortedConversations.length})
            </TabsTrigger>
            {analytics && (
              <TabsTrigger value="analytics">
                <BarChart3 className="h-4 w-4 mr-2 " />
              </TabsTrigger>
            )}
          </TabsList>

          <div className="flex-1 mt-4">
            <TabsContent value="conversations" className="h-full m-0">
              <ScrollArea className="h-full px-4">
                <div className="space-y-3 pb-4">
                  {filteredAndSortedConversations.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50 " />
                      <p className="text-sm md:text-base lg:text-lg">
                        {searchQuery || statusFilter !== 'all' || topicFilter !== 'all'
                          ? 'No conversations match your filters'
                          : 'No conversations yet'}
                      </p>
                    </div>
                  ) : (
                    filteredAndSortedConversations.map(renderConversationItem)
                  )}
                </div>
              </ScrollArea>
            </TabsContent>

            {analytics && (
              <TabsContent value="analytics" className="h-full m-0">
                <ScrollArea className="h-full px-4">
                  <div className="pb-4">
                    {renderAnalytics()}
                  </div>
                </ScrollArea>
              </TabsContent>
            )}
          </div>
        </Tabs>
      </CardContent>
    </Card>
    </ErrorBoundary>
  );
};

export default ConversationManager;