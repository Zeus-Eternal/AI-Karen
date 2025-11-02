'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  ExternalLink,
  Database,
  Globe,
  FileText,
  MessageSquare,
  Brain,
  Star,
  Eye,
  Copy,
  Filter,
  Search
} from 'lucide-react';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { SourceAttribution as SourceAttributionType } from '@/types/enhanced-chat';

interface SourceAttributionProps {
  sources: SourceAttributionType[];
  onSourceClick?: (source: SourceAttributionType) => void;
  className?: string;
  compact?: boolean;
  showFilters?: boolean;
}

export const SourceAttribution: React.FC<SourceAttributionProps> = ({
  sources,
  onSourceClick,
  className = '',
  compact = false,
  showFilters = true
}) => {
  const { toast } = useToast();
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'relevance' | 'reliability' | 'title'>('relevance');

  // Get source icon
  const getSourceIcon = (type: SourceAttributionType['type']) => {
    switch (type) {
      case 'memory':
        return Brain;
      case 'knowledge_base':
        return Database;
      case 'web':
        return Globe;
      case 'document':
        return FileText;
      case 'conversation':
        return MessageSquare;
      default:
        return FileText;
    }
  };

  // Get source type color
  const getSourceTypeColor = (type: SourceAttributionType['type']) => {
    switch (type) {
      case 'memory':
        return 'bg-purple-100 text-purple-800';
      case 'knowledge_base':
        return 'bg-blue-100 text-blue-800';
      case 'web':
        return 'bg-green-100 text-green-800';
      case 'document':
        return 'bg-orange-100 text-orange-800';
      case 'conversation':
        return 'bg-pink-100 text-pink-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // Get reliability color
  const getReliabilityColor = (reliability: number) => {
    if (reliability >= 0.8) return 'text-green-600';
    if (reliability >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  // Filter and sort sources
  const filteredAndSortedSources = React.useMemo(() => {
    let filtered = sources.filter(source => {
      const matchesSearch = searchQuery === '' ||
        source.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (source.snippet && source.snippet.toLowerCase().includes(searchQuery.toLowerCase()));
      
      const matchesType = typeFilter === 'all' || source.type === typeFilter;
      
      return matchesSearch && matchesType;
    });

    // Sort sources
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'reliability':
          return b.reliability - a.reliability;
        case 'title':
          return a.title.localeCompare(b.title);
        case 'relevance':
        default:
          return b.relevance - a.relevance;
      }
    });

    return filtered;
  }, [sources, searchQuery, typeFilter, sortBy]);

  // Handle source click
  const handleSourceClick = (source: SourceAttributionType) => {
    if (onSourceClick) {
      onSourceClick(source);
    } else if (source.url) {
      window.open(source.url, '_blank');
    }
  };

  // Copy source information
  const copySourceInfo = async (source: SourceAttributionType) => {
    const info = `${source.title}\nType: ${source.type}\nReliability: ${Math.round(source.reliability * 100)}%\nRelevance: ${Math.round(source.relevance * 100)}%${source.url ? `\nURL: ${source.url}` : ''}${source.snippet ? `\nSnippet: ${source.snippet}` : ''}`;
    
    try {
      await navigator.clipboard.writeText(info);
      toast({
        title: 'Copied',
        description: 'Source information copied to clipboard'
      });
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Copy Failed',
        description: 'Failed to copy source information'
      });
    }
  };

  // Render compact version
  if (compact) {
    return (
      <div className={`flex flex-wrap gap-2 ${className}`}>
        {sources.slice(0, 3).map((source, index) => {
          const Icon = getSourceIcon(source.type);
          return (
            <TooltipProvider key={source.id}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-auto p-2"
                    onClick={() => handleSourceClick(source)}
                  >
                    <Icon className="h-3 w-3 mr-1" />
                    <span className="text-xs">{index + 1}</span>
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <div className="space-y-1">
                    <p className="font-medium">{source.title}</p>
                    <p className="text-xs">Type: {source.type}</p>
                    <p className="text-xs">Reliability: {Math.round(source.reliability * 100)}%</p>
                    <p className="text-xs">Relevance: {Math.round(source.relevance * 100)}%</p>
                  </div>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          );
        })}
        {sources.length > 3 && (
          <Badge variant="secondary" className="text-xs">
            +{sources.length - 3} more
          </Badge>
        )}
      </div>
    );
  }

  return (
    <Card className={`h-full flex flex-col ${className}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Source Attribution ({sources.length})
          </CardTitle>
          
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              Avg Reliability: {Math.round(sources.reduce((acc, s) => acc + s.reliability, 0) / sources.length * 100)}%
            </Badge>
          </div>
        </div>

        {/* Filters */}
        {showFilters && (
          <div className="space-y-3 mt-4">
            <div className="relative">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search sources..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 h-9"
              />
            </div>
            
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger className="w-32 h-8 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="memory">Memory</SelectItem>
                  <SelectItem value="knowledge_base">Knowledge Base</SelectItem>
                  <SelectItem value="web">Web</SelectItem>
                  <SelectItem value="document">Document</SelectItem>
                  <SelectItem value="conversation">Conversation</SelectItem>
                </SelectContent>
              </Select>
              
              <Select value={sortBy} onValueChange={(value) => setSortBy(value as any)}>
                <SelectTrigger className="w-32 h-8 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="relevance">Relevance</SelectItem>
                  <SelectItem value="reliability">Reliability</SelectItem>
                  <SelectItem value="title">Title</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        )}
      </CardHeader>

      <CardContent className="flex-1 p-0">
        <ScrollArea className="h-full px-4">
          <div className="space-y-3 pb-4">
            {filteredAndSortedSources.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Database className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">
                  {searchQuery || typeFilter !== 'all' 
                    ? 'No sources match your filters' 
                    : 'No sources available'}
                </p>
              </div>
            ) : (
              filteredAndSortedSources.map((source, index) => {
                const Icon = getSourceIcon(source.type);
                const typeColor = getSourceTypeColor(source.type);
                const reliabilityColor = getReliabilityColor(source.reliability);
                
                return (
                  <Card key={source.id} className="hover:shadow-sm transition-shadow">
                    <CardContent className="p-4">
                      <div className="flex items-start gap-3">
                        {/* Source Icon */}
                        <div className="flex-shrink-0 mt-1">
                          <Icon className="h-5 w-5 text-muted-foreground" />
                        </div>

                        {/* Source Content */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex-1 min-w-0">
                              <h3 className="text-sm font-medium truncate">
                                {source.title}
                              </h3>
                              <div className="flex items-center gap-2 mt-1">
                                <Badge className={`text-xs ${typeColor}`}>
                                  {source.type.replace('_', ' ')}
                                </Badge>
                                <span className="text-xs text-muted-foreground">
                                  Source #{index + 1}
                                </span>
                              </div>
                            </div>
                            
                            <div className="flex items-center gap-1 ml-2">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => copySourceInfo(source)}
                                className="h-6 w-6 p-0"
                              >
                                <Copy className="h-3 w-3" />
                              </Button>
                              
                              {source.url && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleSourceClick(source)}
                                  className="h-6 w-6 p-0"
                                >
                                  <ExternalLink className="h-3 w-3" />
                                </Button>
                              )}
                            </div>
                          </div>

                          {/* Source Snippet */}
                          {source.snippet && (
                            <p className="text-sm text-muted-foreground italic mb-3 line-clamp-2">
                              "{source.snippet}"
                            </p>
                          )}

                          {/* Source Metrics */}
                          <div className="flex items-center gap-4 text-xs">
                            <div className="flex items-center gap-1">
                              <Star className="h-3 w-3" />
                              <span className={`font-medium ${reliabilityColor}`}>
                                {Math.round(source.reliability * 100)}% reliable
                              </span>
                            </div>
                            
                            <div className="flex items-center gap-1">
                              <Eye className="h-3 w-3" />
                              <span className="font-medium">
                                {Math.round(source.relevance * 100)}% relevant
                              </span>
                            </div>
                          </div>

                          {/* Source URL */}
                          {source.url && (
                            <div className="mt-2">
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-auto p-0 text-xs text-primary hover:underline"
                                onClick={() => handleSourceClick(source)}
                              >
                                <ExternalLink className="h-3 w-3 mr-1" />
                                View Source
                              </Button>
                            </div>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
};

export default SourceAttribution;