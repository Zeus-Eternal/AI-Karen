"use client";

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Brain, Search, Trash2, Calendar } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface MemoryRow {
  id: string;
  content: string;
  timestamp: Date;
  category?: string;
  importance?: 'high' | 'medium' | 'low';
  tags?: string[];
}

export interface MemoryGridProps {
  memories?: MemoryRow[];
  onDelete?: (id: string) => void;
  onSearch?: (query: string) => void;
  className?: string;
}

export default function MemoryGrid({
  memories = [],
  onDelete,
  onSearch,
  className,
}: MemoryGridProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [localMemories] = useState<MemoryRow[]>(memories);

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchQuery(query);
    if (onSearch) {
      onSearch(query);
    }
  };

  const filteredMemories = localMemories.filter((memory) =>
    memory.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
    memory.tags?.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const getImportanceColor = (importance?: string) => {
    switch (importance) {
      case 'high': return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400';
      case 'medium': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400';
      case 'low': return 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400';
    }
  };

  const formatDate = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days} days ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className={cn('space-y-4', className)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain className="h-5 w-5 text-purple-600 dark:text-purple-400" />
          <h3 className="text-lg font-semibold">Memory Bank</h3>
          <Badge variant="secondary">{filteredMemories.length}</Badge>
        </div>

        <div className="relative w-64">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search memories..."
            value={searchQuery}
            onChange={handleSearch}
            className="pl-8"
          />
        </div>
      </div>

      {filteredMemories.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Brain className="h-12 w-12 text-gray-400 mb-4" />
            <p className="text-gray-600 dark:text-gray-400">
              {searchQuery ? 'No memories found' : 'No memories stored yet'}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {filteredMemories.map((memory) => (
            <Card key={memory.id} className="relative group hover:shadow-md transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1">
                    {memory.category && (
                      <Badge variant="outline" className="mb-2">
                        {memory.category}
                      </Badge>
                    )}
                    <CardDescription className="line-clamp-3">
                      {memory.content}
                    </CardDescription>
                  </div>
                  {onDelete && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onDelete(memory.id)}
                      className="opacity-0 group-hover:opacity-100 transition-opacity h-7 w-7 p-0"
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  )}
                </div>
              </CardHeader>

              <CardContent className="pt-0 space-y-2">
                {memory.tags && memory.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {memory.tags.map((tag, index) => (
                      <Badge key={index} variant="secondary" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                )}

                <div className="flex items-center justify-between text-xs text-gray-500">
                  <div className="flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    {formatDate(memory.timestamp)}
                  </div>
                  {memory.importance && (
                    <Badge
                      className={cn('text-xs', getImportanceColor(memory.importance))}
                    >
                      {memory.importance}
                    </Badge>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

export { MemoryGrid };
