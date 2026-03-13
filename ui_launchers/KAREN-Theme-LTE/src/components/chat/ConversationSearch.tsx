/**
 * Conversation Search Component - Search across conversations and messages
 */

import React, { useState, useEffect } from 'react';
import { Conversation, SearchFilters } from '../../types/conversation';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { 
  Search, 
  Filter, 
  Calendar, 
  Tag, 
  MessageSquare,
  User,
  Bot,
  Clock,
  ExternalLink
} from 'lucide-react';
import { cn } from '../../lib/utils';

interface ConversationSearchProps {
  userId: string;
  className?: string;
}

export const ConversationSearch: React.FC<ConversationSearchProps> = ({
  userId,
  className = ''
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('conversations');
  const [filters, setFilters] = useState<Partial<SearchFilters>>({});

  // Simple search implementation
  const handleSearch = () => {
    if (searchQuery.trim()) {
      console.log('Searching for:', searchQuery, 'with filters:', filters);
      // In a real implementation, this would call the search API
    }
  };

  const clearAllFilters = () => {
    setFilters({});
    setSearchQuery('');
  };

  const highlightText = (text: string, query: string) => {
    if (!query.trim()) return text;
    
    const regex = new RegExp(`(${query})`, 'gi');
    const parts = text.split(regex);
    
    return parts.map((part, index) => 
      regex.test(part) ? (
        <mark key={index} className="bg-yellow-200 dark:bg-yellow-800 px-1 rounded">
          {part}
        </mark>
      ) : part
    );
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className={cn('conversation-search', className)}>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Search className="h-5 w-5" />
            <span>Search Conversations</span>
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Search input */}
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search conversations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Simple filters */}
          <div className="mt-4 p-4 bg-muted rounded-lg">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium flex items-center space-x-2">
                <Filter className="h-4 w-4" />
                <span>Filters</span>
              </h3>
              <Button variant="ghost" size="sm" onClick={clearAllFilters}>
                Clear All
              </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* Tags filter */}
              <div className="space-y-2">
                <label className="text-sm font-medium flex items-center space-x-2">
                  <Tag className="h-4 w-4" />
                  <span>Tags</span>
                </label>
                <div className="flex flex-wrap gap-2">
                  {['work', 'personal', 'project', 'idea', 'research'].map(tag => (
                    <Badge
                      key={tag}
                      variant={filters.tags?.includes(tag) ? 'default' : 'outline'}
                      className="cursor-pointer"
                      onClick={() => {
                        const currentTags = filters.tags || [];
                        const newTags = currentTags.includes(tag)
                          ? currentTags.filter((t: string) => t !== tag)
                          : [...currentTags, tag];
                        setFilters(prev => ({ ...prev, tags: newTags }));
                      }}
                    >
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Search results */}
          <div className="mt-6">
            <div className="text-center py-8 text-muted-foreground">
              <Search className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Search functionality will be implemented with backend integration</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};