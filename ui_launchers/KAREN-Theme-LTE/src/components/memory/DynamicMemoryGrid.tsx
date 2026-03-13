"use client";

import { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { 
  Download, 
  Trash2,
  RefreshCw,
  Brain,
  Clock,
  User,
  Calendar,
  Hash,
} from 'lucide-react';
import { cn } from '@/lib/utils';

// Memory data types
interface MemoryEntry {
  id: string;
  content: string;
  type: 'fact' | 'preference' | 'context' | 'conversation';
  category: string;
  tags: string[];
  confidence: number;
  importance: number;
  userId: string;
  userName: string;
  createdAt: string;
  updatedAt: string;
  accessCount: number;
  lastAccessed: string;
  metadata: {
    source?: string;
    context?: string;
    relatedIds?: string[];
  };
}

interface MemoryGridProps {
  className?: string;
}

type MemorySortBy = 'createdAt' | 'updatedAt' | 'importance' | 'confidence';
type MemorySortOrder = 'asc' | 'desc';

const isMemorySortBy = (value: string): value is MemorySortBy =>
  value === 'createdAt' || value === 'updatedAt' || value === 'importance' || value === 'confidence';

const isMemorySortOrder = (value: string): value is MemorySortOrder =>
  value === 'asc' || value === 'desc';

// Utility function for date formatting
function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

// Utility function for confidence color
function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.8) return 'bg-green-100 text-green-800';
  if (confidence >= 0.6) return 'bg-yellow-100 text-yellow-800';
  if (confidence >= 0.4) return 'bg-orange-100 text-orange-800';
  return 'bg-red-100 text-red-800';
}

// Utility function for importance color
function getImportanceColor(importance: number): string {
  if (importance >= 0.8) return 'bg-purple-100 text-purple-800';
  if (importance >= 0.6) return 'bg-blue-100 text-blue-800';
  if (importance >= 0.4) return 'bg-indigo-100 text-indigo-800';
  return 'bg-gray-100 text-gray-800';
}

// Utility function for type color
function getTypeColor(type: string): string {
  switch (type) {
    case 'fact': return 'bg-blue-100 text-blue-800';
    case 'preference': return 'bg-green-100 text-green-800';
    case 'context': return 'bg-purple-100 text-purple-800';
    case 'conversation': return 'bg-orange-100 text-orange-800';
    default: return 'bg-gray-100 text-gray-800';
  }
}

export default function DynamicMemoryGrid({ className }: MemoryGridProps) {
  const [memories, setMemories] = useState<MemoryEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedMemories, setSelectedMemories] = useState<string[]>([]);
  const [filterType, setFilterType] = useState<string>('all');
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [sortBy, setSortBy] = useState<MemorySortBy>('createdAt');
  const [sortOrder, setSortOrder] = useState<MemorySortOrder>('desc');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  // Mock data - replace with actual API call
  useEffect(() => {
    const mockMemories: MemoryEntry[] = [
      {
        id: '1',
        content: 'User prefers dark mode interface and larger font sizes for better readability',
        type: 'preference',
        category: 'ui-preferences',
        tags: ['ui', 'accessibility', 'dark-mode', 'fonts'],
        confidence: 0.95,
        importance: 0.8,
        userId: 'user-123',
        userName: 'John Doe',
        createdAt: new Date(Date.now() - 86400000).toISOString(),
        updatedAt: new Date(Date.now() - 3600000).toISOString(),
        accessCount: 15,
        lastAccessed: new Date(Date.now() - 1800000).toISOString(),
        metadata: {
          source: 'user-feedback',
          context: 'ui-settings-panel'
        }
      },
      {
        id: '2',
        content: 'User is working on a machine learning project with Python and TensorFlow',
        type: 'context',
        category: 'work-projects',
        tags: ['ml', 'python', 'tensorflow', 'project'],
        confidence: 0.88,
        importance: 0.9,
        userId: 'user-123',
        userName: 'John Doe',
        createdAt: new Date(Date.now() - 172800000).toISOString(),
        updatedAt: new Date(Date.now() - 86400000).toISOString(),
        accessCount: 8,
        lastAccessed: new Date(Date.now() - 7200000).toISOString(),
        metadata: {
          source: 'conversation',
          context: 'project-discussion'
        }
      },
      {
        id: '3',
        content: 'User has a meeting every Tuesday at 2 PM with the development team',
        type: 'fact',
        category: 'schedule',
        tags: ['meeting', 'tuesday', 'schedule', 'team'],
        confidence: 0.92,
        importance: 0.7,
        userId: 'user-123',
        userName: 'John Doe',
        createdAt: new Date(Date.now() - 259200000).toISOString(),
        updatedAt: new Date(Date.now() - 172800000).toISOString(),
        accessCount: 12,
        lastAccessed: new Date(Date.now() - 3600000).toISOString(),
        metadata: {
          source: 'calendar-integration',
          context: 'weekly-schedule'
        }
      },
      {
        id: '4',
        content: 'User discussed the implementation of a new authentication system with OAuth 2.0',
        type: 'conversation',
        category: 'development',
        tags: ['auth', 'oauth', 'security', 'implementation'],
        confidence: 0.85,
        importance: 0.85,
        userId: 'user-123',
        userName: 'John Doe',
        createdAt: new Date(Date.now() - 604800000).toISOString(),
        updatedAt: new Date(Date.now() - 86400000).toISOString(),
        accessCount: 6,
        lastAccessed: new Date(Date.now() - 10800000).toISOString(),
        metadata: {
          source: 'chat-history',
          context: 'technical-discussion'
        }
      },
      {
        id: '5',
        content: 'User prefers keyboard shortcuts over mouse interactions when possible',
        type: 'preference',
        category: 'interaction-preferences',
        tags: ['keyboard', 'shortcuts', 'accessibility', 'productivity'],
        confidence: 0.9,
        importance: 0.75,
        userId: 'user-123',
        userName: 'John Doe',
        createdAt: new Date(Date.now() - 432000000).toISOString(),
        updatedAt: new Date(Date.now() - 172800000).toISOString(),
        accessCount: 20,
        lastAccessed: new Date(Date.now() - 900000).toISOString(),
        metadata: {
          source: 'user-behavior-analysis',
          context: 'interaction-patterns'
        }
      }
    ];

    setMemories(mockMemories);
    setLoading(false);
  }, []);

  // Get unique categories
  const categories = useMemo(() => {
    const cats = new Set(memories.map(m => m.category));
    return Array.from(cats);
  }, [memories]);

  // Filter and sort memories
  const filteredMemories = useMemo(() => {
    let filtered = memories;

    // Apply search filter
    if (searchQuery) {
      filtered = filtered.filter(memory =>
        memory.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
        memory.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase())) ||
        memory.category.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Apply type filter
    if (filterType !== 'all') {
      filtered = filtered.filter(memory => memory.type === filterType);
    }

    // Apply category filter
    if (filterCategory !== 'all') {
      filtered = filtered.filter(memory => memory.category === filterCategory);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      const aValue = a[sortBy];
      const bValue = b[sortBy];
      
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortOrder === 'asc' 
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }
      
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortOrder === 'asc' ? aValue - bValue : bValue - aValue;
      }
      
      return 0;
    });

    return filtered;
  }, [memories, searchQuery, filterType, filterCategory, sortBy, sortOrder]);

  const handleRefresh = () => {
    setLoading(true);
    // Simulate refresh
    setTimeout(() => {
      // In real implementation, this would fetch fresh data
      setLoading(false);
    }, 1000);
  };

  const handleExport = () => {
    // In real implementation, this would export memory data
    const data = {
      memories: filteredMemories,
      exportedAt: new Date().toISOString(),
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `memory-data-${formatDate(new Date())}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleDeleteSelected = () => {
    // In real implementation, this would delete selected memories
    setMemories(memories.filter(m => !selectedMemories.includes(m.id)));
    setSelectedMemories([]);
  };

  const toggleMemorySelection = (memoryId: string) => {
    setSelectedMemories(prev =>
      prev.includes(memoryId)
        ? prev.filter(id => id !== memoryId)
        : [...prev, memoryId]
    );
  };

  const toggleAllSelection = () => {
    if (selectedMemories.length === filteredMemories.length) {
      setSelectedMemories([]);
    } else {
      setSelectedMemories(filteredMemories.map(m => m.id));
    }
  };

  return (
    <div className={cn("space-y-6", className)}>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            Dynamic Memory Grid
          </CardTitle>
          <CardDescription>
            Advanced memory management with search, filtering, and analytics
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Memory Controls */}
          <div className="flex flex-col gap-4 mb-6">
            <div className="flex gap-2">
              <Input
                placeholder="Search memories..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-1"
              />
              
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={loading}
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={handleExport}
              >
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
            </div>
            
            <div className="flex flex-wrap gap-2">
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="px-3 py-1 border border-border rounded-md text-sm"
              >
                <option value="all">All Types</option>
                <option value="fact">Facts</option>
                <option value="preference">Preferences</option>
                <option value="context">Context</option>
                <option value="conversation">Conversations</option>
              </select>
              
              <select
                value={filterCategory}
                onChange={(e) => setFilterCategory(e.target.value)}
                className="px-3 py-1 border border-border rounded-md text-sm"
              >
                <option value="all">All Categories</option>
                {categories.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
              
              <select
                value={`${sortBy}-${sortOrder}`}
                onChange={(e) => {
                  const [sort, order] = e.target.value.split('-');

                  if (isMemorySortBy(sort)) {
                    setSortBy(sort);
                  }

                  if (isMemorySortOrder(order)) {
                    setSortOrder(order);
                  }
                }}
                className="px-3 py-1 border border-border rounded-md text-sm"
              >
                <option value="createdAt-desc">Newest First</option>
                <option value="createdAt-asc">Oldest First</option>
                <option value="importance-desc">Most Important</option>
                <option value="importance-asc">Least Important</option>
                <option value="confidence-desc">Highest Confidence</option>
                <option value="confidence-asc">Lowest Confidence</option>
              </select>
              
              <div className="flex gap-1 ml-auto">
                <Button
                  variant={viewMode === 'grid' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setViewMode('grid')}
                >
                  Grid
                </Button>
                <Button
                  variant={viewMode === 'list' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setViewMode('list')}
                >
                  List
                </Button>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={toggleAllSelection}
                disabled={filteredMemories.length === 0}
              >
                {selectedMemories.length === filteredMemories.length ? 'Deselect All' : 'Select All'}
              </Button>
              
              {selectedMemories.length > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleDeleteSelected}
                  className="text-destructive"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete Selected ({selectedMemories.length})
                </Button>
              )}
              
              <Badge className="text-xs bg-secondary text-secondary-foreground">
                {filteredMemories.length} memories
              </Badge>
            </div>
          </div>

          {/* Memory Grid/List */}
          {viewMode === 'grid' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredMemories.map((memory) => (
                <Card 
                  key={memory.id} 
                  className={cn(
                    "cursor-pointer transition-all hover:shadow-md",
                    selectedMemories.includes(memory.id) && "ring-2 ring-primary"
                  )}
                  onClick={() => toggleMemorySelection(memory.id)}
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <Badge className={cn("text-xs", getTypeColor(memory.type))}>
                          {memory.type}
                        </Badge>
                        <Badge className="text-xs bg-secondary text-secondary-foreground">
                          {memory.category}
                        </Badge>
                      </div>
                      <input
                        type="checkbox"
                        checked={selectedMemories.includes(memory.id)}
                        onChange={() => toggleMemorySelection(memory.id)}
                        className="rounded"
                      />
                    </div>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <p className="text-sm mb-3 line-clamp-3">{memory.content}</p>
                    
                    <div className="flex flex-wrap gap-1 mb-3">
                      {memory.tags.slice(0, 3).map(tag => (
                        <Badge key={tag} className="text-xs border border-current">
                          {tag}
                        </Badge>
                      ))}
                      {memory.tags.length > 3 && (
                        <Badge className="text-xs border border-current">
                          +{memory.tags.length - 3}
                        </Badge>
                      )}
                    </div>
                    
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <div className="flex items-center gap-2">
                        <span className={cn("px-1 py-0.5 rounded", getConfidenceColor(memory.confidence))}>
                          {Math.round(memory.confidence * 100)}% confidence
                        </span>
                        <span className={cn("px-1 py-0.5 rounded", getImportanceColor(memory.importance))}>
                          {Math.round(memory.importance * 100)}% importance
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {formatDate(memory.createdAt)}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div className="space-y-2">
              {filteredMemories.map((memory) => (
                <Card 
                  key={memory.id} 
                  className={cn(
                    "cursor-pointer transition-all hover:shadow-md",
                    selectedMemories.includes(memory.id) && "ring-2 ring-primary"
                  )}
                  onClick={() => toggleMemorySelection(memory.id)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge className={cn("text-xs", getTypeColor(memory.type))}>
                            {memory.type}
                          </Badge>
                          <Badge className="text-xs bg-secondary text-secondary-foreground">
                            {memory.category}
                          </Badge>
                          <span className={cn("px-1 py-0.5 rounded text-xs", getConfidenceColor(memory.confidence))}>
                            {Math.round(memory.confidence * 100)}% confidence
                          </span>
                          <span className={cn("px-1 py-0.5 rounded text-xs", getImportanceColor(memory.importance))}>
                            {Math.round(memory.importance * 100)}% importance
                          </span>
                        </div>
                        
                        <p className="text-sm mb-2">{memory.content}</p>
                        
                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                          <div className="flex items-center gap-1">
                            <User className="h-3 w-3" />
                            {memory.userName}
                          </div>
                          <div className="flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            {formatDate(memory.createdAt)}
                          </div>
                          <div className="flex items-center gap-1">
                            <Hash className="h-3 w-3" />
                            {memory.accessCount} accesses
                          </div>
                        </div>
                      </div>
                      
                      <input
                        type="checkbox"
                        checked={selectedMemories.includes(memory.id)}
                        onChange={() => toggleMemorySelection(memory.id)}
                        className="rounded ml-4"
                      />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Empty State */}
          {filteredMemories.length === 0 && !loading && (
            <div className="text-center py-8">
              <Brain className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium">No memories found</h3>
              <p className="text-muted-foreground">
                {searchQuery 
                  ? `No memories matching "${searchQuery}"`
                  : 'No memories available'
                }
              </p>
              <Button onClick={handleRefresh} className="mt-4">
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh Data
              </Button>
            </div>
          )}

          {/* Loading State */}
          {loading && (
            <div className="text-center py-8">
              <RefreshCw className="h-8 w-8 mx-auto animate-spin text-muted-foreground" />
              <p className="text-muted-foreground mt-2">Loading memories...</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
