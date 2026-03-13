"use client";

import { useEffect, useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';
import { formatDate } from '@/lib/utils';
import { 
  Memory,
  MemoryActionPayload,
  MemoryManagementProps,
} from './types';
import { useMemoryStore, useMemoryActions } from './store/memoryStore';
import { MemoryCard } from './ui/MemoryCard';
import { MemoryDetails } from './ui/MemoryDetails';

// Button variant helper function
const getButtonVariant = (variant: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link") => {
  const variants = {
    default: "bg-primary text-primary-foreground hover:bg-primary/90",
    destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
    outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
    secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
    ghost: "hover:bg-accent hover:text-accent-foreground",
    link: "text-primary underline-offset-4 hover:underline",
  };
  return variants[variant];
};

// Icon components
const Grid = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 01-2 2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
  </svg>
);

const List = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
  </svg>
);

const Columns = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17V7m0 10a2 2 0 012-2h2a2 2 0 012 2v2m0 10a2 2 0 112-2h2a2 2 0 012 2v2m0 10a2 2 0 112-2h2a2 2 0 012 2v2" />
  </svg>
);

const Brain = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const Filter = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 01-.707.293V4z" />
  </svg>
);

const Settings = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 2.573 1.066c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v.01M12 12h.01M12 18h.01M7 12h.01M7 18h.01M12 6a1 1 0 110-2 1 1 0 010 2z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01" />
  </svg>
);

const RefreshCw = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.242 15.176l-2.546-2.546A7.007 7.007 0 001.418 0z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364l-5.858 5.858a1 1 0 01-1.414 1.414L12 20.778a1 1 0 01-.707-.293l-2.829-2.828a1 1 0 00-.293-.707L11.586 6.586a1 1 0 01-.414-1.414L4.172 4.172a1 1 0 01.586.414z" />
  </svg>
);

const Download = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2v-6a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>
);

const Trash2 = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
  </svg>
);

export function MemoryManagement({
  className,
  onMemorySelect,
  onMemoryAction,
  autoRefresh = false,
  refreshInterval = 30000,
  showStatistics = true,
  showOrganization = true,
  maxMemoryItems = 50,
}: MemoryManagementProps) {
  // Store hooks
  const memories = useMemoryStore((state) => state.memories);
  const selectedMemory = useMemoryStore((state) => state.selectedMemory);
  const isLoading = useMemoryStore((state) => state.isLoading);
  const error = useMemoryStore((state) => state.error);
  const statistics = useMemoryStore((state) => state.statistics);
  const showDetails = useMemoryStore((state) => state.showDetails);
  const showFilters = useMemoryStore((state) => state.showFilters);
  const viewMode = useMemoryStore((state) => state.viewMode);
  const selectedMemories = useMemoryStore((state) => state.selectedMemories);
  const currentPage = useMemoryStore((state) => state.currentPage);
  const pageSize = useMemoryStore((state) => state.pageSize);
  const total = useMemoryStore((state) => state.total);
  const hasMore = useMemoryStore((state) => state.hasMore);
  const searchQuery = useMemoryStore((state) => state.searchQuery);

  const {
    fetchMemories,
    executeMemoryAction,
    bulkDeleteMemories,
    bulkArchiveMemories,
    bulkExportMemories,
    searchMemories,
    clearSearch,
    clearFilters,
    disableRealTimeUpdates,
    fetchStatistics,
    fetchFolders,
    fetchCollections,
    fetchTags,
    fetchCategories,
    selectMemory,
    clearSelection,
    selectAll,
    setSelectedMemory,
    setShowDetails,
    setShowFilters,
    setViewMode,
    setCurrentPage,
    clearError,
  } = useMemoryActions();

  // Local state
  const [showImportExport, setShowImportExport] = useState(false);
  const [showCleanup, setShowCleanup] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  // Initialize data
  useEffect(() => {
    fetchMemories();
    fetchStatistics();
    fetchFolders();
    fetchCollections();
    fetchTags();
    fetchCategories();
    
    if (autoRefresh && typeof disableRealTimeUpdates === 'function') {
      // Real-time updates would be enabled here if the function was available
    }
    
    return () => {
      if (autoRefresh && typeof disableRealTimeUpdates === 'function') {
        disableRealTimeUpdates();
      }
    };
  }, [fetchMemories, fetchStatistics, fetchFolders, fetchCollections, fetchTags, fetchCategories, disableRealTimeUpdates, autoRefresh]);

  // Auto refresh
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchMemories();
      fetchStatistics();
      setLastRefresh(new Date());
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchMemories, fetchStatistics]);

  // Handle memory selection
  const handleMemorySelect = useCallback((memory: Memory) => {
    selectMemory(memory.id);
    setSelectedMemory(memory);
    setShowDetails(true);
    onMemorySelect?.(memory);
  }, [selectMemory, setSelectedMemory, setShowDetails, onMemorySelect]);

  // Handle memory action
  const handleMemoryAction = useCallback((payload: MemoryActionPayload) => {
    executeMemoryAction(payload);
    onMemoryAction?.(payload);
  }, [executeMemoryAction, onMemoryAction]);

  // Handle search
  const handleSearch = useCallback((query: string) => {
    if (query.trim()) {
      searchMemories(query);
    } else {
      clearSearch();
    }
  }, [searchMemories, clearSearch]);

  // Handle view mode change
  const handleViewModeChange = useCallback((mode: 'list' | 'grid' | 'kanban' | 'timeline') => {
    setViewMode(mode);
  }, [setViewMode]);

  // Handle page change
  const handlePageChange = useCallback((page: number) => {
    setCurrentPage(page);
  }, [setCurrentPage]);

  // Handle clear filters
  const handleClearFilters = useCallback(() => {
    clearFilters();
  }, [clearFilters]);

  // Handle refresh
  const handleRefresh = useCallback(() => {
    fetchMemories();
    fetchStatistics();
    setLastRefresh(new Date());
  }, [fetchMemories, fetchStatistics]);

  // Handle close details
  const handleCloseDetails = useCallback(() => {
    setShowDetails(false);
    setSelectedMemory(null);
  }, [setShowDetails, setSelectedMemory]);

  // Handle bulk actions
  const handleSelectAll = useCallback(() => {
    selectAll();
  }, [selectAll]);

  const handleClearSelection = useCallback(() => {
    clearSelection();
  }, [clearSelection]);

  const handleBulkDelete = useCallback(() => {
    if (selectedMemories.length > 0) {
      bulkDeleteMemories(selectedMemories);
    }
  }, [selectedMemories, bulkDeleteMemories]);

  const handleBulkArchive = useCallback(() => {
    if (selectedMemories.length > 0) {
      bulkArchiveMemories(selectedMemories);
    }
  }, [selectedMemories, bulkArchiveMemories]);

  const handleBulkExport = useCallback(() => {
    if (selectedMemories.length > 0) {
      bulkExportMemories(selectedMemories);
    }
  }, [selectedMemories, bulkExportMemories]);

  // Render memory based on view mode
  const renderMemory = (memory: Memory) => {
    switch (viewMode) {
      case 'grid':
        return (
          <div className="col-span-1">
            <MemoryCard
              memory={memory}
              onSelect={handleMemorySelect}
              onAction={handleMemoryAction}
              isSelected={selectedMemories.includes(memory.id)}
              showMetadata={true}
              compact={false}
            />
          </div>
        );
      case 'list':
        return (
          <div className="col-span-1">
            <MemoryCard
              memory={memory}
              onSelect={handleMemorySelect}
              onAction={handleMemoryAction}
              isSelected={selectedMemories.includes(memory.id)}
              showMetadata={true}
              compact={true}
            />
          </div>
        );
      case 'kanban':
        return (
          <div className="col-span-1">
            <MemoryCard
              memory={memory}
              onSelect={handleMemorySelect}
              onAction={handleMemoryAction}
              isSelected={selectedMemories.includes(memory.id)}
              showMetadata={false}
              compact={true}
            />
          </div>
        );
      case 'timeline':
        return (
          <div className="col-span-1">
            <MemoryCard
              memory={memory}
              onSelect={handleMemorySelect}
              onAction={handleMemoryAction}
              isSelected={selectedMemories.includes(memory.id)}
              showMetadata={true}
              compact={false}
            />
          </div>
        );
      default:
        return null;
    }
  };

  // Render kanban view
  const renderKanbanView = () => {
    const statusGroups = {
      active: memories.filter(m => m.status === 'active'),
      archived: memories.filter(m => m.status === 'archived'),
      deleted: memories.filter(m => m.status === 'deleted'),
      processing: memories.filter(m => m.status === 'processing'),
    };

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {Object.entries(statusGroups).map(([status, statusMemories]) => (
          <div key={status} className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold capitalize">{status}</h3>
              <Badge className="bg-secondary text-secondary-foreground">
                {statusMemories.length}
              </Badge>
            </div>
            <Separator />
            <div className="space-y-3 min-h-[200px]">
              {statusMemories.map(renderMemory)}
            </div>
          </div>
        ))}
      </div>
    );
  };

  // Render timeline view
  const renderTimelineView = () => {
    const sortedMemories = [...memories].sort((a, b) => 
      new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
    );

    return (
      <div className="space-y-4">
        {sortedMemories.map((memory) => (
          <div key={memory.id} className="flex gap-4">
            <div className="flex-shrink-0">
              <div className="w-4 h-4 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs font-medium">
                {memory.type.charAt(0).toUpperCase()}
              </div>
            </div>
            <div className="flex-1">
              <MemoryCard
                memory={memory}
                onSelect={handleMemorySelect}
                onAction={handleMemoryAction}
                isSelected={selectedMemories.includes(memory.id)}
                showMetadata={true}
                compact={false}
              />
            </div>
            <div className="flex-shrink-0 text-sm text-muted-foreground">
              {formatDate(memory.updatedAt)}
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5" />
              Memory Management
              {autoRefresh && (
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  <RefreshCw className="h-3 w-3" />
                  Auto-refresh
                </div>
              )}
              {lastRefresh && (
                <span className="text-xs text-muted-foreground">
                  Last: {lastRefresh.toLocaleTimeString('en-US', {
                    hour: '2-digit',
                    minute: '2-digit',
                    hour12: true,
                    timeZone: 'UTC'
                  })}
                </span>
              )}
            </CardTitle>
            
            <div className="flex items-center gap-2">
              {/* View Mode Toggle */}
              <div className="flex items-center border rounded-md">
                <button
                  className={cn(
                    "p-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
                    viewMode === 'list' ? "bg-background text-foreground" : "text-muted-foreground hover:text-accent-foreground"
                  )}
                  onClick={() => handleViewModeChange('list')}
                  title="List view"
                >
                  <List className="h-4 w-4" />
                </button>
                <button
                  className={cn(
                    "p-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
                    viewMode === 'grid' ? "bg-background text-foreground" : "text-muted-foreground hover:text-accent-foreground"
                  )}
                  onClick={() => handleViewModeChange('grid')}
                  title="Grid view"
                >
                  <Grid className="h-4 w-4" />
                </button>
                <button
                  className={cn(
                    "p-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
                    viewMode === 'kanban' ? "bg-background text-foreground" : "text-muted-foreground hover:text-accent-foreground"
                  )}
                  onClick={() => handleViewModeChange('kanban')}
                  title="Kanban view"
                >
                  <Columns className="h-4 w-4" />
                </button>
                <button
                  className={cn(
                    "p-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
                    viewMode === 'timeline' ? "bg-background text-foreground" : "text-muted-foreground hover:text-accent-foreground"
                  )}
                  onClick={() => handleViewModeChange('timeline')}
                  title="Timeline view"
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </button>
              </div>
              
              {/* Settings */}
              <button
                className={cn(
                  "p-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
                  showFilters ? "bg-background text-foreground" : "text-muted-foreground hover:text-accent-foreground"
                )}
                onClick={() => setShowFilters(!showFilters)}
                title="Toggle filters"
              >
                <Settings className="h-4 w-4" />
              </button>
              
              {/* Refresh */}
              <button
                className="p-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 text-muted-foreground hover:text-accent-foreground"
                onClick={handleRefresh}
                disabled={isLoading}
                title="Refresh memories"
              >
                <RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />
              </button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Quick Filters */}
      {total !== undefined && (
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Input
              placeholder="Search memories..."
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              className="w-64"
            />
            <div className="flex items-center gap-2">
              <button
                className={cn(
                  "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 px-3 gap-2",
                  getButtonVariant("outline")
                )}
                onClick={handleClearFilters}
              >
                <Filter className="h-4 w-4" />
                Clear Filters
              </button>
              <button
                className={cn(
                  "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 px-3 gap-2",
                  getButtonVariant("outline")
                )}
                onClick={() => setShowImportExport(true)}
              >
                <Download className="h-4 w-4" />
                Import/Export
              </button>
              <button
                className={cn(
                  "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 px-3 gap-2",
                  getButtonVariant("outline")
                )}
                onClick={() => setShowCleanup(true)}
              >
                <Trash2 className="h-4 w-4" />
                Cleanup
              </button>
            </div>
          </div>
          <div className="text-sm text-muted-foreground">
            {total} memories found
          </div>
        </div>
      )}

      {/* Filters */}
      {showFilters ? (
        <div className="p-4 border rounded-md bg-card">
          <h3 className="text-lg font-medium mb-4">Filters</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Filter functionality would be implemented here
          </p>
        </div>
      ) : null}

      {/* Statistics */}
      {showStatistics && statistics && (
        <div>
          {/* Statistics component would go here */}
        </div>
      )}

      {/* Organization */}
      {showOrganization && (
        <div>
          {/* Organization component would go here */}
        </div>
      )}

      {/* Bulk Actions */}
      {selectedMemories && selectedMemories.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Bulk Actions</CardTitle>
              <div className="flex items-center gap-2">
                <Badge className="bg-secondary text-secondary-foreground">
                  {selectedMemories.length} selected
                </Badge>
                <button
                  className={cn(
                    "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-8 px-3",
                    getButtonVariant("outline")
                  )}
                  onClick={handleSelectAll}
                >
                  Select All
                </button>
                <button
                  className={cn(
                    "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-8 px-3",
                    getButtonVariant("outline")
                  )}
                  onClick={handleClearSelection}
                >
                  Clear Selection
                </button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2">
              <button
                className={cn(
                  "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 px-3 gap-2",
                  getButtonVariant("outline")
                )}
                onClick={handleBulkArchive}
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                </svg>
                Archive Selected
              </button>
              <button
                className={cn(
                  "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 px-3 gap-2",
                  getButtonVariant("outline")
                )}
                onClick={handleBulkExport}
              >
                <Download className="h-4 w-4" />
                Export Selected
              </button>
              <button
                className={cn(
                  "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-9 px-3 gap-2",
                  getButtonVariant("destructive")
                )}
                onClick={handleBulkDelete}
              >
                <Trash2 className="h-4 w-4" />
                Delete Selected
              </button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Error Display */}
      {error && (
        <Card className="border-destructive">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-medium text-destructive">Error loading memories</h3>
                <p className="text-sm text-destructive/80 mt-1">{error}</p>
              </div>
              <button
                className={cn(
                  "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-8 px-3",
                  getButtonVariant("outline")
                )}
                onClick={clearError}
              >
                Dismiss
              </button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Memories */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: Math.min(6, maxMemoryItems) }).map((_, index) => (
            <Card key={index} className="h-full">
              <CardContent className="p-4">
                <div className="space-y-3">
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4"></div>
                  <div className="space-y-2">
                    <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
                    <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : memories.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center">
            <div className="space-y-3">
              <div className="w-16 h-16 mx-auto bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center">
                <Brain className="h-8 w-8 text-gray-400" />
              </div>
              <h3 className="text-lg font-medium">No memories found</h3>
              <p className="text-muted-foreground">
                {searchQuery 
                  ? `No memories matching "${searchQuery}"`
                  : 'No memories available'
                }
              </p>
              <button
                className={cn(
                  "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-9 px-3 gap-2"
                )}
                onClick={handleRefresh}
              >
                <RefreshCw className="h-4 w-4" />
                Refresh Data
              </button>
            </div>
          </CardContent>
        </Card>
      ) : viewMode === 'kanban' ? (
        renderKanbanView()
      ) : viewMode === 'timeline' ? (
        renderTimelineView()
      ) : (
        <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6' : 'space-y-4'}>
          {memories.slice(0, maxMemoryItems).map(renderMemory)}
        </div>
      )}

      {/* Pagination */}
      {total > pageSize && (
        <div className="flex items-center justify-between mt-6">
          <div className="text-sm text-muted-foreground">
            Showing {((currentPage - 1) * pageSize) + 1}-{Math.min(currentPage * pageSize, total)} of {total}
          </div>
          <div className="flex items-center gap-2">
            <button
              className={cn(
                "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-8 px-3",
                getButtonVariant("outline"),
                currentPage === 1 && "opacity-50 cursor-not-allowed"
              )}
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
            >
              Previous
            </button>
            <button
              className={cn(
                "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-8 px-3",
                getButtonVariant("outline"),
                !hasMore && "opacity-50 cursor-not-allowed"
              )}
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={!hasMore}
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* Memory Details Modal */}
      {showDetails && selectedMemory && (
        <MemoryDetails
          memory={selectedMemory}
          onClose={handleCloseDetails}
          onAction={handleMemoryAction}
          onEdit={(memory) => handleMemoryAction({ memoryId: memory.id, action: 'edit', data: memory })}
          showActions={true}
        />
      )}

      {/* Import/Export Modal */}
      {showImportExport && (
        <div className="p-4 border rounded-md bg-card">
          <h3 className="text-lg font-medium mb-4">Import/Export</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Import/Export functionality would be implemented here
          </p>
          <button
            className={cn(
              "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-9 px-3",
              getButtonVariant("default")
            )}
            onClick={() => setShowImportExport(false)}
          >
            Close
          </button>
        </div>
      )}

      {/* Cleanup Modal */}
      {showCleanup && (
        <div className="p-4 border rounded-md bg-card">
          <h3 className="text-lg font-medium mb-4">Cleanup</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Cleanup functionality would be implemented here
          </p>
          <button
            className={cn(
              "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-9 px-3",
              getButtonVariant("default")
            )}
            onClick={() => setShowCleanup(false)}
          >
            Close
          </button>
        </div>
      )}
    </div>
  );
}
