'use client';
import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { AgGridReact } from 'ag-grid-react';
import { ColDef, GridReadyEvent, CellValueChangedEvent, RowSelectedEvent } from 'ag-grid-community';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Search, Filter, Plus, Edit, Trash2, Brain, Network, Star } from 'lucide-react';
import { useHooks } from '@/contexts/HookContext';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';
import { format } from 'date-fns';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';
import { safeDebug } from '@/lib/safe-console';
export interface MemoryRow {
  id: string;
  content: string;
  type: 'fact' | 'preference' | 'context' | 'insight';
  confidence: number;
  lastAccessed: Date;
  relevanceScore: number;
  semanticCluster: string;
  relationships: string[];
  tags: string[];
  source: string;
  isStarred: boolean;
}
interface MemoryGridProps {
  memories?: MemoryRow[];
  onMemoryUpdate?: (memory: MemoryRow) => Promise<void>;
  onMemoryDelete?: (memoryId: string) => Promise<void>;
  onMemoryCreate?: (memory: Partial<MemoryRow>) => Promise<void>;
  className?: string;
}
// Custom cell renderers
const TypeRenderer = (params: any) => {
  const type = params.value;
  const variants = {
    fact: 'default',
    preference: 'secondary',
    context: 'outline',
    insight: 'destructive'
  } as const;
  return (
    <Badge variant={variants[type as keyof typeof variants]} className="text-xs sm:text-sm md:text-base">
      {type}
    </Badge>
  );
};
const ConfidenceRenderer = (params: any) => {
  const confidence = params.value;
  const percentage = Math.round(confidence * 100);
  const color = confidence > 0.8 ? 'text-green-600' : confidence > 0.5 ? 'text-yellow-600' : 'text-red-600';
  return (
    <div className="flex items-center gap-2">
      <div className={`w-2 h-2 rounded-full ${confidence > 0.8 ? 'bg-green-500' : confidence > 0.5 ? 'bg-yellow-500' : 'bg-red-500'}`} />
      <span className={`text-sm font-medium ${color}`}>{percentage}%</span>
    </div>
  );
};
const RelevanceRenderer = (params: any) => {
  const score = params.value;
  const stars = Math.round(score * 5);
  return (
    <div className="flex items-center">
      {[...Array(5)].map((_, i) => (
        <Star
          key={i}
          className={`h-3 w-3 ${i < stars ? 'text-yellow-400 fill-current' : 'text-gray-300'}`}
        />
      ))}
    </div>
  );
};
const TagsRenderer = (params: any) => {
  const tags = params.value || [];
  return (
    <div className="flex flex-wrap gap-1">
      {tags.slice(0, 2).map((tag: string, index: number) => (
        <Badge key={index} variant="outline" className="text-xs sm:text-sm md:text-base">
          {tag}
        </Badge>
      ))}
      {tags.length > 2 && (
        <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
          +{tags.length - 2}
        </Badge>
      )}
    </div>
  );
};
const ActionsRenderer = (params: any) => {
  const { onEdit, onDelete, onToggleStar } = params.context;
  const memory = params.data;
  return (
    <div className="flex items-center gap-1">
      <button
        variant="ghost"
        size="sm"
        onClick={() = aria-label="Button"> onToggleStar(memory)}
        className="h-6 w-6 p-0 sm:w-auto md:w-full"
      >
        <Star className={`h-3 w-3 ${memory.isStarred ? 'text-yellow-400 fill-current' : 'text-gray-400'}`} />
      </Button>
      <button
        variant="ghost"
        size="sm"
        onClick={() = aria-label="Button"> onEdit(memory)}
        className="h-6 w-6 p-0 sm:w-auto md:w-full"
      >
        <Edit className="h-3 w-3 sm:w-auto md:w-full" />
      </Button>
      <button
        variant="ghost"
        size="sm"
        onClick={() = aria-label="Button"> onDelete(memory.id)}
        className="h-6 w-6 p-0 text-destructive hover:text-destructive sm:w-auto md:w-full"
      >
        <Trash2 className="h-3 w-3 sm:w-auto md:w-full" />
      </Button>
    </div>
  );
};
export const MemoryGrid: React.FC<MemoryGridProps> = ({
  memories = [],
  onMemoryUpdate,
  onMemoryDelete,
  onMemoryCreate,
  className = ''
}) => {
  const { user } = useAuth();
  const { triggerHooks, registerGridHook } = useHooks();
  const { toast } = useToast();
  const [searchText, setSearchText] = useState('');
  const [selectedMemories, setSelectedMemories] = useState<MemoryRow[]>([]);
  const [editingMemory, setEditingMemory] = useState<MemoryRow | null>(null);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [newMemory, setNewMemory] = useState<Partial<MemoryRow>>({
    content: '',
    type: 'fact',
    tags: []
  });
  // Generate  if none provided
  const memoryData = useMemo(() => {
    if (memories.length > 0) return memories;
    return [
      {
        id: '1',
        content: 'User prefers TypeScript over JavaScript for new projects',
        type: 'preference' as const,
        confidence: 0.95,
        lastAccessed: new Date(Date.now() - 1000 * 60 * 30),
        relevanceScore: 0.9,
        semanticCluster: 'programming_preferences',
        relationships: ['2', '3'],
        tags: ['typescript', 'javascript', 'programming'],
        source: 'conversation',
        isStarred: true
      },
      {
        id: '2',
        content: 'User is working on a React project with Next.js',
        type: 'context' as const,
        confidence: 0.88,
        lastAccessed: new Date(Date.now() - 1000 * 60 * 60),
        relevanceScore: 0.85,
        semanticCluster: 'current_projects',
        relationships: ['1', '4'],
        tags: ['react', 'nextjs', 'project'],
        source: 'conversation',
        isStarred: false
      },
      {
        id: '3',
        content: 'User has experience with AG-Grid and data visualization',
        type: 'fact' as const,
        confidence: 0.92,
        lastAccessed: new Date(Date.now() - 1000 * 60 * 60 * 2),
        relevanceScore: 0.8,
        semanticCluster: 'technical_skills',
        relationships: ['1'],
        tags: ['ag-grid', 'data-visualization', 'skills'],
        source: 'conversation',
        isStarred: false
      },
      {
        id: '4',
        content: 'User tends to ask for code examples and practical implementations',
        type: 'insight' as const,
        confidence: 0.78,
        lastAccessed: new Date(Date.now() - 1000 * 60 * 60 * 4),
        relevanceScore: 0.75,
        semanticCluster: 'communication_style',
        relationships: ['2'],
        tags: ['learning-style', 'code-examples', 'practical'],
        source: 'ai_analysis',
        isStarred: true
      }
    ];
  }, [memories]);
  // Column definitions
  const columnDefs: ColDef[] = useMemo(() => [
    {
      field: 'content',
      headerName: 'Memory Content',
      flex: 3,
      sortable: true,
      filter: 'agTextColumnFilter',
      cellStyle: { 
        whiteSpace: 'normal',
        lineHeight: '1.4',
        paddingTop: '8px',
        paddingBottom: '8px'
      } as any,
      autoHeight: true
    },
    {
      field: 'type',
      headerName: 'Type',
      width: 100,
      sortable: true,
      filter: 'agSetColumnFilter',
      cellRenderer: TypeRenderer
    },
    {
      field: 'confidence',
      headerName: 'Confidence',
      width: 120,
      sortable: true,
      filter: 'agNumberColumnFilter',
      cellRenderer: ConfidenceRenderer
    },
    {
      field: 'relevanceScore',
      headerName: 'Relevance',
      width: 120,
      sortable: true,
      filter: 'agNumberColumnFilter',
      cellRenderer: RelevanceRenderer
    },
    {
      field: 'lastAccessed',
      headerName: 'Last Accessed',
      width: 140,
      sortable: true,
      filter: 'agDateColumnFilter',
      valueFormatter: (params) => format(new Date(params.value), 'MMM dd, HH:mm')
    },
    {
      field: 'semanticCluster',
      headerName: 'Cluster',
      width: 140,
      sortable: true,
      filter: 'agTextColumnFilter',
      cellStyle: { fontSize: '12px' } as any
    },
    {
      field: 'tags',
      headerName: 'Tags',
      width: 150,
      sortable: false,
      filter: 'agTextColumnFilter',
      cellRenderer: TagsRenderer
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 120,
      sortable: false,
      filter: false,
      cellRenderer: ActionsRenderer,
      cellRendererParams: {
        onEdit: (memory: MemoryRow) => setEditingMemory(memory),
        onDelete: handleDeleteMemory,
        onToggleStar: handleToggleStar
      }
    }
  ], []);
  // Default column properties
  const defaultColDef = useMemo(() => ({
    resizable: true,
    sortable: true,
    filter: true
  }), []);
  // Register grid hooks
  useEffect(() => {
    const hookIds: string[] = [];
    hookIds.push(registerGridHook('memories', 'dataLoad', async (params) => {
      safeDebug('Memory grid data loaded:', params);
      return { success: true, memoryCount: memoryData.length };
    }));
    hookIds.push(registerGridHook('memories', 'rowSelected', async (params) => {
      safeDebug('Memory row selected:', params);
      return { success: true, selectedMemory: params.data };
    }));
    return () => {
      // Cleanup hooks
    };
  }, [registerGridHook, memoryData.length]);
  // Handle grid events
  const onGridReady = useCallback(async (params: GridReadyEvent) => {
    await triggerHooks('grid_memories_dataLoad', {
      gridId: 'memories',
      api: params.api,
      memoryCount: memoryData.length
    }, { userId: user?.userId });
  }, [triggerHooks, memoryData.length, user?.userId]);
  const onSelectionChanged = useCallback(async (event: any) => {
    const selectedNodes = event.api.getSelectedNodes();
    const selectedData = selectedNodes.map((node: any) => node.data);
    setSelectedMemories(selectedData);
    for (const memory of selectedData) {
      await triggerHooks('grid_memories_rowSelected', {
        gridId: 'memories',
        data: memory,
        api: event.api
      }, { userId: user?.userId });
    }
  }, [triggerHooks, user?.userId]);
  // Memory management functions
  async function handleDeleteMemory(memoryId: string) {
    try {
      if (onMemoryDelete) {
        await onMemoryDelete(memoryId);
      }
      toast({
        title: 'Memory Deleted',
        description: 'The memory has been successfully deleted.'
      });
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Delete Failed',
        description: 'Failed to delete the memory. Please try again.'
      });
    }
  }
  async function handleToggleStar(memory: MemoryRow) {
    try {
      const updatedMemory = { ...memory, isStarred: !memory.isStarred };
      if (onMemoryUpdate) {
        await onMemoryUpdate(updatedMemory);
      }
      toast({
        title: memory.isStarred ? 'Memory Unstarred' : 'Memory Starred',
        description: `Memory has been ${memory.isStarred ? 'removed from' : 'added to'} favorites.`
      });
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Update Failed',
        description: 'Failed to update the memory. Please try again.'
      });
    }
  }
  const handleCreateMemory = async () => {
    try {
      if (onMemoryCreate && newMemory.content) {
        await onMemoryCreate({
          ...newMemory,
          confidence: 0.8,
          lastAccessed: new Date(),
          relevanceScore: 0.7,
          semanticCluster: 'user_created',
          relationships: [],
          source: 'manual',
          isStarred: false
        });
        setNewMemory({ content: '', type: 'fact', tags: [] });
        setIsCreateDialogOpen(false);
        toast({
          title: 'Memory Created',
          description: 'New memory has been successfully added.'
        });
      }
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Creation Failed',
        description: 'Failed to create the memory. Please try again.'
      });
    }
  };
  // Filter memories based on search
  const filteredMemories = useMemo(() => {
    if (!searchText) return memoryData;
    const searchLower = searchText.toLowerCase();
    return memoryData.filter(memory =>
      memory.content?.toLowerCase().includes(searchLower) ||
      memory.type?.toLowerCase().includes(searchLower) ||
      memory.semanticCluster?.toLowerCase().includes(searchLower) ||
      memory.tags?.some(tag => tag?.toLowerCase().includes(searchLower))
    );
  }, [memoryData, searchText]);
  return (
    <Card className={`w-full ${className}`}>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold flex items-center gap-2">
            <Brain className="h-5 w-5 sm:w-auto md:w-full" />
            Memory Management ({filteredMemories.length})
          </CardTitle>
          <div className="flex items-center gap-2">
            <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
              <DialogTrigger asChild>
                <button size="sm" aria-label="Button">
                  <Plus className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                  Add Memory
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Create New Memory</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium md:text-base lg:text-lg">Content</label>
                    <textarea
                      value={newMemory.content || ''}
                      onChange={(e) = aria-label="Textarea"> setNewMemory({ ...newMemory, content: e.target.value })}
                      placeholder="Enter memory content..."
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium md:text-base lg:text-lg">Type</label>
                    <select
                      value={newMemory.type || 'fact'}
                      onChange={(e) = aria-label="Select option"> setNewMemory({ ...newMemory, type: e.target.value as any })}
                      className="mt-1 w-full p-2 border rounded-md sm:p-4 md:p-6"
                    >
                      <option value="fact">Fact</option>
                      <option value="preference">Preference</option>
                      <option value="context">Context</option>
                      <option value="insight">Insight</option>
                    </select>
                  </div>
                  <div className="flex justify-end gap-2">
                    <button variant="outline" onClick={() = aria-label="Button"> setIsCreateDialogOpen(false)}>
                      Cancel
                    </Button>
                    <button onClick={handleCreateMemory} disabled={!newMemory.content} aria-label="Button">
                      Create Memory
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
            <button variant="outline" size="sm" aria-label="Button">
              <Network className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
              View Network
            </Button>
          </div>
        </div>
        <div className="flex items-center gap-2 mt-4">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
            <input
              placeholder="Search memories..."
              value={searchText}
              onChange={(e) = aria-label="Input"> setSearchText(e.target.value)}
              className="pl-10"
            />
          </div>
          <button variant="outline" size="sm" aria-label="Button">
            <Filter className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
            Filters
          </Button>
        </div>
        {selectedMemories.length > 0 && (
          <div className="flex items-center gap-2 mt-2">
            <Badge variant="secondary">
              {selectedMemories.length} selected
            </Badge>
            <button variant="outline" size="sm" aria-label="Button">
              Bulk Actions
            </Button>
          </div>
        )}
      </CardHeader>
      <CardContent className="p-0 sm:p-4 md:p-6">
        <div className="ag-theme-alpine h-[600px] w-full">
          <AgGridReact
            rowData={filteredMemories}
            columnDefs={columnDefs}
            defaultColDef={defaultColDef}
            onGridReady={onGridReady}
            onSelectionChanged={onSelectionChanged}
            rowSelection="multiple"
            animateRows={true}
            getRowId={(params) => params.data.id}
            context={{
              onEdit: setEditingMemory,
              onDelete: handleDeleteMemory,
              onToggleStar: handleToggleStar
            }}
          />
        </div>
      </CardContent>
    </Card>
  );
};
