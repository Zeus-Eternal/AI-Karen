"use client";

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { AgGridReact } from 'ag-grid-react';
import type { ColDef, GridReadyEvent, ICellRendererParams, SelectionChangedEvent } from 'ag-grid-community';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Search, Filter, Download, RefreshCw } from 'lucide-react';
import { useHooks } from '@/hooks/use-hooks';
import { useAuth } from '@/hooks/use-auth';
import { format } from 'date-fns';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';
import { safeDebug } from '@/lib/safe-console';
import type { ConversationSummaryRow } from '@/types/chat-ui';

interface ConversationGridProps {
  conversations?: ConversationSummaryRow[];
  onConversationSelect?: (conversation: ConversationSummaryRow) => void;
  onRefresh?: () => Promise<void>;
  className?: string;
}

// Custom cell renderers for AG-Grid
const SentimentRenderer = (
  params: ICellRendererParams<ConversationSummaryRow, ConversationSummaryRow['sentiment']>
) => {
  const sentiment = params.value;
  const variant = sentiment === 'positive' ? 'default' :
                  sentiment === 'negative' ? 'destructive' : 'secondary';

  return (
    <Badge variant={variant} className="text-xs sm:text-sm md:text-base">
      {sentiment}
    </Badge>
  );
};

const TagsRenderer = (
  params: ICellRendererParams<ConversationSummaryRow, string[] | undefined>
) => {
  const tags = params.value ?? [];
  return (
    <div className="flex flex-wrap gap-1">
      {tags.slice(0, 2).map((tag, index) => (
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

const TimestampRenderer = (
  params: ICellRendererParams<ConversationSummaryRow, Date | undefined>
) => {
  const timestamp = params.value;
  return timestamp ? format(new Date(timestamp), 'MMM dd, HH:mm') : '';
};

const ParticipantsRenderer = (
  params: ICellRendererParams<ConversationSummaryRow, string[] | undefined>
) => {
  const participants = params.value ?? [];
  return participants.join(', ');
};

export const ConversationGrid: React.FC<ConversationGridProps> = ({
  conversations = [],
  onConversationSelect,
  onRefresh,
  className = ''
}) => {
  const { user } = useAuth();
  const { triggerHooks, registerGridHook } = useHooks();
  const [searchText, setSearchText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedRows, setSelectedRows] = useState<ConversationSummaryRow[]>([]);

  // Column definitions for AG-Grid
  const columnDefs: ColDef<ConversationSummaryRow>[] = useMemo(() => [
    {
      field: 'title',
      headerName: 'Conversation',
      flex: 2,
      sortable: true,
      filter: 'agTextColumnFilter',
      cellStyle: { fontWeight: '500' } as unknown
    },
    {
      field: 'lastMessage',
      headerName: 'Last Message',
      flex: 3,
      sortable: false,
      filter: 'agTextColumnFilter',
      cellStyle: { 
        whiteSpace: 'nowrap',
        overflow: 'hidden',
        textOverflow: 'ellipsis'
      } as unknown
    },
    {
      field: 'lastActivity',
      headerName: 'Last Activity',
      width: 140,
      sortable: true,
      filter: 'agDateColumnFilter',
      cellRenderer: TimestampRenderer,
      sort: 'desc'
    },
    {
      field: 'messageCount',
      headerName: 'Messages',
      width: 100,
      sortable: true,
      filter: 'agNumberColumnFilter',
      cellStyle: { textAlign: 'center' } as unknown
    },
    {
      field: 'participants',
      headerName: 'Participants',
      width: 150,
      sortable: false,
      filter: 'agTextColumnFilter',
      cellRenderer: ParticipantsRenderer
    },
    {
      field: 'sentiment',
      headerName: 'Sentiment',
      width: 120,
      sortable: true,
      filter: 'agSetColumnFilter',
      cellRenderer: SentimentRenderer
    },
    {
      field: 'tags',
      headerName: 'Tags',
      width: 150,
      sortable: false,
      filter: 'agTextColumnFilter',
      cellRenderer: TagsRenderer
    }
  ], []);

  // Default column properties
  const defaultColDef = useMemo(() => ({
    resizable: true,
    sortable: true,
    filter: true,
    floatingFilter: true
  }), []);

  // Grid options
  const gridOptions = useMemo(() => ({
    rowSelection: 'multiple' as const,
    suppressRowClickSelection: false,
    rowMultiSelectWithClick: true,
    animateRows: true,
    enableRangeSelection: true,
    suppressMenuHide: true,
    getRowId: (params: { data: ConversationSummaryRow }) => params.data.id
  }), []);

  // Register grid hooks on mount
  useEffect(() => {
    const hookIds: string[] = [];

    // Register data load hook
    hookIds.push(registerGridHook('conversations', 'dataLoad', async (params) => {
      safeDebug('Conversation grid data loaded:', params);
      return { success: true, rowCount: conversations.length };
    }));

    // Register row selection hook
    hookIds.push(registerGridHook('conversations', 'rowSelected', async (params) => {
      safeDebug('Conversation row selected:', params);
      if (onConversationSelect && params.data) {
        onConversationSelect(params.data);
      }
      return { success: true, selectedRow: params.data };
    }));

    return () => {
      // Cleanup hooks on unmount
      hookIds.forEach(id => {
        // Note: unregisterHook would be called here in a real implementation
      });
    };
  }, [registerGridHook, conversations.length, onConversationSelect]);

  // Handle grid ready event
  const onGridReady = useCallback(async (params: GridReadyEvent) => {
    await triggerHooks('grid_conversations_dataLoad', {
      gridId: 'conversations',
      api: params.api,
      rowCount: conversations.length
    }, { userId: user?.userId });
  }, [triggerHooks, conversations.length, user?.userId]);

  // Handle row selection
  const onSelectionChanged = useCallback(async (event: SelectionChangedEvent<ConversationSummaryRow>) => {
    const selectedNodes = event.api.getSelectedNodes();
    const selectedData = selectedNodes
      .map(node => node.data)
      .filter((row): row is ConversationSummaryRow => Boolean(row));
    setSelectedRows(selectedData);

    for (const rowData of selectedData) {
      await triggerHooks('grid_conversations_rowSelected', {
        gridId: 'conversations',
        data: rowData,
        api: event.api
      }, { userId: user?.userId });
    }
  }, [triggerHooks, user?.userId]);

  // Handle refresh
  const handleRefresh = useCallback(async () => {
    setIsLoading(true);
    try {
      if (onRefresh) {
        await onRefresh();
      }
    } finally {
      setIsLoading(false);
    }
  }, [onRefresh]);

  // Filter conversations based on search text
  const filteredConversations = useMemo(() => {
    if (!searchText) return conversations;

    const searchLower = searchText.toLowerCase();
    return conversations.filter(conv => {
      const titleMatch = conv.title?.toLowerCase().includes(searchLower);
      const lastMessageMatch = (conv.lastMessage?.toLowerCase() ?? '').includes(searchLower);
      const participantMatch = conv.participants?.some(participant => participant.toLowerCase().includes(searchLower));
      const tagMatch = conv.tags?.some(tag => tag.toLowerCase().includes(searchLower));

      return Boolean(titleMatch || lastMessageMatch || participantMatch || tagMatch);
    });
  }, [conversations, searchText]);

  return (
    <Card className={`w-full ${className}`}>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold">
            Conversations ({filteredConversations.length})
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={isLoading}
             >
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            </Button>
            <Button variant="outline" size="sm" >
              <Download className="h-4 w-4 mr-2 " />
            </Button>
          </div>
        </div>
        
        <div className="flex items-center gap-2 mt-4">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground " />
            <Input
              placeholder="Search conversations..."
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button variant="outline" size="sm" >
            <Filter className="h-4 w-4 mr-2 " />
          </Button>
        </div>

        {selectedRows.length > 0 && (
          <div className="flex items-center gap-2 mt-2">
            <Badge variant="secondary">
              {selectedRows.length} selected
            </Badge>
            <Button variant="outline" size="sm" >
            </Button>
          </div>
        )}
      </CardHeader>

      <CardContent className="p-0 sm:p-4 md:p-6">
        <div className="ag-theme-alpine h-[500px] w-full">
          <AgGridReact
            rowData={filteredConversations}
            columnDefs={columnDefs}
            defaultColDef={defaultColDef}
            gridOptions={gridOptions}
            onGridReady={onGridReady}
            onSelectionChanged={onSelectionChanged}
            suppressRowClickSelection={false}
            rowSelection="multiple"
            animateRows={true}
            enableRangeSelection={true}
            getRowId={(params) => params.data.id}
          />
        </div>
      </CardContent>
    </Card>
  );
};