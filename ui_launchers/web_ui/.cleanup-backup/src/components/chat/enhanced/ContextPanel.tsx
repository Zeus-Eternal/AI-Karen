'use client';

import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import {
  MessageSquare,
  Brain,
  Clock,
  Tag,
  Search,
  TrendingUp,
  Lightbulb,
  History,
  BookOpen,
  Users,
  Filter
} from 'lucide-react';
import { format, formatDistanceToNow } from 'date-fns';
import {
  ConversationContext,
  ConversationThread,
  MemoryReference,
  ContextSuggestion,
  UserPattern,
  ContextPanelProps
} from '@/types/enhanced-chat';

export const ContextPanel: React.FC<ContextPanelProps> = ({
  conversation,
  onThreadSelect,
  onMemorySelect,
  onSuggestionSelect,
  className = ''
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('threads');
  const [filterType, setFilterType] = useState<string>('all');

  // Filter and search logic
  const filteredThreads = useMemo(() => {
    return conversation.relatedThreads.filter(thread => {
      const matchesSearch = searchQuery === '' || 
        thread.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        thread.topic.toLowerCase().includes(searchQuery.toLowerCase());
      
      const matchesFilter = filterType === 'all' || 
        thread.status === filterType ||
        thread.metadata.complexity === filterType;
      
      return matchesSearch && matchesFilter;
    });
  }, [conversation.relatedThreads, searchQuery, filterType]);

  const filteredMemories = useMemo(() => {
    return conversation.memoryContext.relevantMemories.filter(memory => {
      const matchesSearch = searchQuery === '' ||
        memory.content.toLowerCase().includes(searchQuery.toLowerCase());
      
      const matchesFilter = filterType === 'all' || memory.type === filterType;
      
      return matchesSearch && matchesFilter;
    });
  }, [conversation.memoryContext.relevantMemories, searchQuery, filterType]);

  const topSuggestions = useMemo(() => {
    return conversation.currentThread.messages
      .flatMap(msg => msg.metadata?.suggestions || [])
      .sort((a, b) => b.confidence - a.confidence)
      .slice(0, 5);
  }, [conversation.currentThread.messages]);

  const renderThreadItem = (thread: ConversationThread) => (
    <div
      key={thread.id}
      className="p-3 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors"
      onClick={() => onThreadSelect(thread.id)}
    >
      <div className="flex items-start justify-between mb-2">
        <h4 className="font-medium text-sm truncate flex-1">{thread.title}</h4>
        <Badge variant="outline" className="text-xs ml-2">
          {thread.metadata.messageCount}
        </Badge>
      </div>
      
      <div className="flex items-center gap-2 mb-2">
        <Badge variant="secondary" className="text-xs">
          {thread.topic}
        </Badge>
        <Badge 
          variant={thread.metadata.complexity === 'complex' ? 'destructive' : 
                  thread.metadata.complexity === 'medium' ? 'default' : 'secondary'}
          className="text-xs"
        >
          {thread.metadata.complexity}
        </Badge>
      </div>
      
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span className="flex items-center gap-1">
          <Clock className="h-3 w-3" />
          {formatDistanceToNow(thread.updatedAt, { addSuffix: true })}
        </span>
        <span className="flex items-center gap-1">
          <TrendingUp className="h-3 w-3" />
          {Math.round(thread.metadata.sentiment === 'positive' ? 85 : 
                     thread.metadata.sentiment === 'negative' ? 35 : 60)}%
        </span>
      </div>
    </div>
  );

  const renderMemoryItem = (memory: MemoryReference) => (
    <div
      key={memory.id}
      className="p-3 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors"
      onClick={() => onMemorySelect(memory.id)}
    >
      <div className="flex items-start justify-between mb-2">
        <Badge variant="outline" className="text-xs">
          {memory.type}
        </Badge>
        <span className="text-xs text-muted-foreground">
          {Math.round(memory.relevance * 100)}% relevant
        </span>
      </div>
      
      <p className="text-sm text-muted-foreground mb-2 line-clamp-2">
        {memory.content}
      </p>
      
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>{format(memory.timestamp, 'MMM dd, yyyy')}</span>
        {memory.source && (
          <span className="flex items-center gap-1">
            <BookOpen className="h-3 w-3" />
            {memory.source}
          </span>
        )}
      </div>
    </div>
  );

  const renderSuggestionItem = (suggestion: ContextSuggestion) => (
    <Button
      key={suggestion.id}
      variant="ghost"
      size="sm"
      className="w-full justify-start h-auto p-3 text-left"
      onClick={() => onSuggestionSelect(suggestion)}
    >
      <div className="flex items-start gap-2 w-full">
        <Lightbulb className="h-4 w-4 mt-0.5 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium">{suggestion.text}</p>
          <div className="flex items-center gap-2 mt-1">
            <Badge variant="secondary" className="text-xs">
              {suggestion.type}
            </Badge>
            <span className="text-xs text-muted-foreground">
              {Math.round(suggestion.confidence * 100)}% confidence
            </span>
          </div>
        </div>
      </div>
    </Button>
  );

  const renderUserPattern = (pattern: UserPattern) => (
    <div key={`${pattern.type}-${pattern.pattern}`} className="p-2 border rounded">
      <div className="flex items-center justify-between mb-1">
        <Badge variant="outline" className="text-xs">
          {pattern.type}
        </Badge>
        <span className="text-xs text-muted-foreground">
          {Math.round(pattern.confidence * 100)}%
        </span>
      </div>
      <p className="text-sm">{pattern.pattern}</p>
      <p className="text-xs text-muted-foreground mt-1">
        Used {pattern.frequency} times • Last: {formatDistanceToNow(pattern.lastSeen, { addSuffix: true })}
      </p>
    </div>
  );

  return (
    <Card className={`h-full flex flex-col ${className}`}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Brain className="h-5 w-5" />
          Context
        </CardTitle>
        
        {/* Search and Filter */}
        <div className="space-y-2">
          <div className="relative">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search context..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 h-9"
            />
          </div>
          
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="text-sm border rounded px-2 py-1 bg-background"
            >
              <option value="all">All</option>
              <option value="active">Active</option>
              <option value="archived">Archived</option>
              <option value="simple">Simple</option>
              <option value="medium">Medium</option>
              <option value="complex">Complex</option>
            </select>
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex-1 p-0">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
          <TabsList className="grid w-full grid-cols-4 mx-4">
            <TabsTrigger value="threads" className="text-xs">
              <MessageSquare className="h-3 w-3 mr-1" />
              Threads
            </TabsTrigger>
            <TabsTrigger value="memory" className="text-xs">
              <Brain className="h-3 w-3 mr-1" />
              Memory
            </TabsTrigger>
            <TabsTrigger value="suggestions" className="text-xs">
              <Lightbulb className="h-3 w-3 mr-1" />
              Ideas
            </TabsTrigger>
            <TabsTrigger value="patterns" className="text-xs">
              <Users className="h-3 w-3 mr-1" />
              Patterns
            </TabsTrigger>
          </TabsList>

          <div className="flex-1 mt-4">
            <TabsContent value="threads" className="h-full m-0">
              <ScrollArea className="h-full px-4">
                <div className="space-y-3 pb-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium text-sm">Related Conversations</h3>
                    <Badge variant="secondary" className="text-xs">
                      {filteredThreads.length}
                    </Badge>
                  </div>
                  
                  {filteredThreads.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
                      <p className="text-sm">No related conversations found</p>
                    </div>
                  ) : (
                    filteredThreads.map(renderThreadItem)
                  )}
                </div>
              </ScrollArea>
            </TabsContent>

            <TabsContent value="memory" className="h-full m-0">
              <ScrollArea className="h-full px-4">
                <div className="space-y-3 pb-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium text-sm">Relevant Memories</h3>
                    <Badge variant="secondary" className="text-xs">
                      {filteredMemories.length}
                    </Badge>
                  </div>
                  
                  {/* Memory Stats */}
                  <div className="grid grid-cols-2 gap-2 mb-4">
                    <div className="p-2 bg-muted rounded text-center">
                      <div className="text-lg font-bold">
                        {conversation.memoryContext.memoryStats.totalMemories}
                      </div>
                      <div className="text-xs text-muted-foreground">Total</div>
                    </div>
                    <div className="p-2 bg-muted rounded text-center">
                      <div className="text-lg font-bold">
                        {Math.round(conversation.memoryContext.memoryStats.averageRelevance * 100)}%
                      </div>
                      <div className="text-xs text-muted-foreground">Avg Relevance</div>
                    </div>
                  </div>
                  
                  {filteredMemories.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <Brain className="h-8 w-8 mx-auto mb-2 opacity-50" />
                      <p className="text-sm">No relevant memories found</p>
                    </div>
                  ) : (
                    filteredMemories.map(renderMemoryItem)
                  )}
                </div>
              </ScrollArea>
            </TabsContent>

            <TabsContent value="suggestions" className="h-full m-0">
              <ScrollArea className="h-full px-4">
                <div className="space-y-3 pb-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium text-sm">Smart Suggestions</h3>
                    <Badge variant="secondary" className="text-xs">
                      {topSuggestions.length}
                    </Badge>
                  </div>
                  
                  {topSuggestions.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <Lightbulb className="h-8 w-8 mx-auto mb-2 opacity-50" />
                      <p className="text-sm">No suggestions available</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {topSuggestions.map(renderSuggestionItem)}
                    </div>
                  )}
                </div>
              </ScrollArea>
            </TabsContent>

            <TabsContent value="patterns" className="h-full m-0">
              <ScrollArea className="h-full px-4">
                <div className="space-y-3 pb-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium text-sm">User Patterns</h3>
                    <Badge variant="secondary" className="text-xs">
                      {conversation.userPatterns.length}
                    </Badge>
                  </div>
                  
                  {conversation.userPatterns.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <Users className="h-8 w-8 mx-auto mb-2 opacity-50" />
                      <p className="text-sm">No patterns detected yet</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {conversation.userPatterns.map(renderUserPattern)}
                    </div>
                  )}
                </div>
              </ScrollArea>
            </TabsContent>
          </div>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default ContextPanel;