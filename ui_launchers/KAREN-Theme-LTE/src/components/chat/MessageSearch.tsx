/**
 * Message Search Component - Search within conversations with advanced filtering
 */

import React, { useState, useEffect } from 'react';
import { Message, Conversation } from '../../types/conversation';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Input } from '../ui/input';
import { Checkbox } from '../ui/checkbox';
import { Separator } from '../ui/separator';
import { 
  Search,
  Filter,
  Calendar,
  User,
  Bot,
  MessageSquare,
  X,
  ChevronDown,
  ChevronRight,
  Clock,
  FileText
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { formatDistanceToNow } from 'date-fns';

interface MessageSearchProps {
  userId: string;
  onMessageSelect?: (message: Message) => void;
  className?: string;
}

interface SearchFilters {
  query: string;
  conversationIds: string[];
  dateRange: {
    start: string;
    end: string;
  };
  sender: 'all' | 'user' | 'assistant';
  hasAttachments: boolean;
  providers: string[];
}

interface SearchResult {
  message: Message;
  conversation: Conversation;
  highlights: string[];
  relevanceScore: number;
}

export const MessageSearch: React.FC<MessageSearchProps> = ({
  userId,
  onMessageSelect,
  className = ''
}) => {
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [expandedResults, setExpandedResults] = useState<Set<string>>(new Set());
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [searchHistory, setSearchHistory] = useState<string[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  
  const [filters, setFilters] = useState<SearchFilters>({
    query: '',
    conversationIds: [],
    dateRange: {
      start: '',
      end: ''
    },
    sender: 'all',
    hasAttachments: false,
    providers: []
  });

  // Mock data - in real implementation, this would fetch from API
  const mockConversations: Conversation[] = [
    {
      id: 'conv_1',
      title: 'Project Planning Discussion',
      userId: userId,
      createdAt: new Date(Date.now() - 86400000 * 5).toISOString(),
      updatedAt: new Date(Date.now() - 86400000 * 2).toISOString(),
      metadata: {
        provider: 'OpenAI',
        model: 'gpt-4',
        messageCount: 25,
        tags: ['work', 'planning']
      }
    },
    {
      id: 'conv_2',
      title: 'React Development Help',
      userId: userId,
      createdAt: new Date(Date.now() - 86400000 * 3).toISOString(),
      updatedAt: new Date(Date.now() - 86400000).toISOString(),
      metadata: {
        provider: 'Anthropic',
        model: 'claude-3',
        messageCount: 18,
        tags: ['development', 'react']
      }
    }
  ];

  useEffect(() => {
    // Load conversations for filtering
    setConversations(mockConversations);
    
    // Load search history from localStorage
    const savedHistory = localStorage.getItem('message-search-history');
    if (savedHistory) {
      setSearchHistory(JSON.parse(savedHistory));
    }
  }, [userId]);

  const performSearch = async () => {
    if (!filters.query.trim()) return;
    
    setLoading(true);
    
    // Save to search history
    const newHistory = [filters.query, ...searchHistory.filter(q => q !== filters.query)].slice(0, 10);
    setSearchHistory(newHistory);
    localStorage.setItem('message-search-history', JSON.stringify(newHistory));
    
    // Simulate API call
    setTimeout(() => {
      // Mock search results
      const mockResults: SearchResult[] = [
        {
          message: {
            id: 'msg_1',
            conversationId: 'conv_1',
            content: 'We need to plan the project timeline and milestones for the next quarter',
            role: 'user',
            timestamp: new Date(Date.now() - 86400000 * 2).toISOString(),
            metadata: {
              tokens: 15
            }
          },
          conversation: mockConversations[0]!,
          highlights: ['plan', 'project', 'timeline'],
          relevanceScore: 0.95
        },
        {
          message: {
            id: 'msg_2',
            conversationId: 'conv_2',
            content: 'For React development, I recommend using hooks for state management',
            role: 'assistant',
            timestamp: new Date(Date.now() - 86400000).toISOString(),
            metadata: {
              provider: 'Anthropic',
              model: 'claude-3',
              tokens: 18
            }
          },
          conversation: mockConversations[1]!,
          highlights: ['React', 'development', 'hooks'],
          relevanceScore: 0.88
        }
      ];
      
      setSearchResults(mockResults);
      setLoading(false);
    }, 800);
  };

  const handleSearchChange = (query: string) => {
    setFilters(prev => ({ ...prev, query }));
  };

  const handleFilterChange = (key: keyof SearchFilters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const toggleConversationFilter = (conversationId: string) => {
    setFilters(prev => ({
      ...prev,
      conversationIds: prev.conversationIds.includes(conversationId)
        ? prev.conversationIds.filter(id => id !== conversationId)
        : [...prev.conversationIds, conversationId]
    }));
  };

  const toggleProviderFilter = (provider: string) => {
    setFilters(prev => ({
      ...prev,
      providers: prev.providers.includes(provider)
        ? prev.providers.filter(p => p !== provider)
        : [...prev.providers, provider]
    }));
  };

  const toggleResultExpansion = (messageId: string) => {
    setExpandedResults(prev => {
      const newSet = new Set(prev);
      if (newSet.has(messageId)) {
        newSet.delete(messageId);
      } else {
        newSet.add(messageId);
      }
      return newSet;
    });
  };

  const clearFilters = () => {
    setFilters({
      query: filters.query,
      conversationIds: [],
      dateRange: { start: '', end: '' },
      sender: 'all',
      hasAttachments: false,
      providers: []
    });
  };

  const highlightText = (text: string, highlights: string[]) => {
    let highlightedText = text;
    highlights.forEach(highlight => {
      const regex = new RegExp(`(${highlight})`, 'gi');
      highlightedText = highlightedText.replace(regex, '<mark class="bg-yellow-200 px-1 rounded">$1</mark>');
    });
    return highlightedText;
  };

  const handleSearchFromHistory = (query: string) => {
    setFilters(prev => ({ ...prev, query }));
    performSearch();
  };

  return (
    <div className={cn('message-search', className)}>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Search className="h-5 w-5" />
            <span>Message Search</span>
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Search Input */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search messages..."
              value={filters.query}
              onChange={(e) => handleSearchChange(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && performSearch()}
              className="pl-10 pr-20"
            />
            <Button
              variant="ghost"
              size="sm"
              onClick={performSearch}
              disabled={!filters.query.trim() || loading}
              className="absolute right-1 top-1/2 transform -translate-y-1/2"
            >
              Search
            </Button>
          </div>

          {/* Search History */}
          {searchHistory.length > 0 && !filters.query && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-muted-foreground">Recent Searches</h4>
              <div className="flex flex-wrap gap-2">
                {searchHistory.map((query, index) => (
                  <Badge
                    key={index}
                    variant="outline"
                    className="cursor-pointer hover:bg-muted"
                    onClick={() => handleSearchFromHistory(query)}
                  >
                    <Clock className="h-3 w-3 mr-1" />
                    {query}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Advanced Filters Toggle */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
            className="w-full"
          >
            <Filter className="h-4 w-4 mr-2" />
            Advanced Filters
            {showAdvancedFilters ? (
              <ChevronDown className="h-4 w-4 ml-2" />
            ) : (
              <ChevronRight className="h-4 w-4 ml-2" />
            )}
          </Button>

          {/* Advanced Filters */}
          {showAdvancedFilters && (
            <div className="space-y-4 p-4 bg-muted rounded-lg">
              {/* Conversation Filter */}
              <div className="space-y-2">
                <h4 className="text-sm font-medium">Conversations</h4>
                <div className="space-y-2">
                  {conversations.map(conversation => (
                    <div key={conversation.id} className="flex items-center space-x-2">
                      <Checkbox
                        id={`conv-${conversation.id}`}
                        checked={filters.conversationIds.includes(conversation.id)}
                        onCheckedChange={() => toggleConversationFilter(conversation.id)}
                      />
                      <label
                        htmlFor={`conv-${conversation.id}`}
                        className="text-sm cursor-pointer flex-1"
                      >
                        {conversation.title}
                      </label>
                    </div>
                  ))}
                </div>
              </div>

              {/* Date Range Filter */}
              <div className="space-y-2">
                <h4 className="text-sm font-medium">Date Range</h4>
                <div className="flex space-x-2">
                  <Input
                    type="date"
                    placeholder="Start date"
                    value={filters.dateRange.start}
                    onChange={(e) => handleFilterChange('dateRange', { ...filters.dateRange, start: e.target.value })}
                  />
                  <Input
                    type="date"
                    placeholder="End date"
                    value={filters.dateRange.end}
                    onChange={(e) => handleFilterChange('dateRange', { ...filters.dateRange, end: e.target.value })}
                  />
                </div>
              </div>

              {/* Sender Filter */}
              <div className="space-y-2">
                <h4 className="text-sm font-medium">Sender</h4>
                <div className="flex space-x-4">
                  {['all', 'user', 'assistant'].map(sender => (
                    <div key={sender} className="flex items-center space-x-2">
                      <input
                        type="radio"
                        id={`sender-${sender}`}
                        name="sender"
                        checked={filters.sender === sender}
                        onChange={() => handleFilterChange('sender', sender)}
                      />
                      <label
                        htmlFor={`sender-${sender}`}
                        className="text-sm cursor-pointer"
                      >
                        {sender === 'all' ? 'All' : sender === 'user' ? 'User' : 'Assistant'}
                      </label>
                    </div>
                  ))}
                </div>
              </div>

              {/* Provider Filter */}
              <div className="space-y-2">
                <h4 className="text-sm font-medium">Providers</h4>
                <div className="flex flex-wrap gap-2">
                  {['OpenAI', 'Anthropic', 'Google', 'Local'].map(provider => (
                    <Badge
                      key={provider}
                      variant={filters.providers.includes(provider) ? 'default' : 'outline'}
                      className="cursor-pointer"
                      onClick={() => toggleProviderFilter(provider)}
                    >
                      {provider}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Clear Filters */}
              <Button variant="outline" size="sm" onClick={clearFilters}>
                <X className="h-4 w-4 mr-2" />
                Clear Filters
              </Button>
            </div>
          )}

          <Separator />

          {/* Search Results */}
          <div className="space-y-4">
            {loading && (
              <div className="flex justify-center py-8">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
                <p className="text-muted-foreground ml-2">Searching...</p>
              </div>
            )}

            {!loading && searchResults.length === 0 && filters.query && (
              <div className="text-center py-8 text-muted-foreground">
                <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No messages found matching your search criteria.</p>
              </div>
            )}

            {!loading && searchResults.length > 0 && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">
                    {searchResults.length} Results
                  </h3>
                  <Badge variant="outline">
                    Relevance: {searchResults[0] ? Math.round(searchResults[0].relevanceScore * 100) : 0}%
                  </Badge>
                </div>

                {searchResults.map((result) => (
                  <Card key={result.message.id} className="cursor-pointer hover:bg-muted/50">
                    <CardContent className="p-4">
                      <div className="space-y-3">
                        {/* Result Header */}
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            {result.message.role === 'user' ? (
                              <User className="h-4 w-4" />
                            ) : (
                              <Bot className="h-4 w-4" />
                            )}
                            <Badge variant="outline" className="text-xs">
                              {result.conversation.title}
                            </Badge>
                            {result.message.metadata?.provider && (
                              <Badge variant="secondary" className="text-xs">
                                {result.message.metadata.provider}
                              </Badge>
                            )}
                          </div>
                          <div className="flex items-center space-x-2">
                            <span className="text-xs text-muted-foreground">
                              {formatDistanceToNow(new Date(result.message.timestamp), { addSuffix: true })}
                            </span>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => toggleResultExpansion(result.message.id)}
                            >
                              {expandedResults.has(result.message.id) ? (
                                <ChevronDown className="h-4 w-4" />
                              ) : (
                                <ChevronRight className="h-4 w-4" />
                              )}
                            </Button>
                          </div>
                        </div>

                        {/* Message Content with Highlights */}
                        <div
                          className="text-sm"
                          dangerouslySetInnerHTML={{
                            __html: highlightText(result.message.content, result.highlights)
                          }}
                        />

                        {/* Expanded Details */}
                        {expandedResults.has(result.message.id) && (
                          <div className="pt-3 border-t space-y-2">
                            <div className="flex items-center justify-between text-xs text-muted-foreground">
                              <span>Message ID: {result.message.id}</span>
                              <span>Relevance: {Math.round(result.relevanceScore * 100)}%</span>
                            </div>
                            {result.message.metadata && (
                              <div className="text-xs text-muted-foreground space-y-1">
                                {result.message.metadata.tokens && (
                                  <div>Tokens: {result.message.metadata.tokens}</div>
                                )}
                                {result.message.metadata.model && (
                                  <div>Model: {result.message.metadata.model}</div>
                                )}
                              </div>
                            )}
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => onMessageSelect?.(result.message)}
                              className="w-full"
                            >
                              <FileText className="h-4 w-4 mr-2" />
                              View in Context
                            </Button>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};