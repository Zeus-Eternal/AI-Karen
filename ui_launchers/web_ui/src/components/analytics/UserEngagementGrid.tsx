'use client';

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { AgGridReact } from 'ag-grid-react';
import { ColDef, GridReadyEvent, CellValueChangedEvent, RowSelectedEvent } from 'ag-grid-community';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Search, 
  Filter, 
  Download, 
  Users, 
  Activity, 
  Clock, 
  MousePointer,
  Eye,
  AlertCircle,
  CheckCircle,
  TrendingUp,
  BarChart3
} from 'lucide-react';
import { useHooks } from '@/contexts/HookContext';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';
import { format, formatDistanceToNow } from 'date-fns';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';

export interface UserEngagementRow {
  id: string;
  timestamp: string;
  userId: string;
  componentType: string;
  componentId: string;
  interactionType: string;
  duration: number;
  success: boolean;
  errorMessage?: string;
  sessionId?: string;
  userAgent?: string;
  location?: string;
}

interface UserEngagementGridProps {
  data?: UserEngagementRow[];
  onRowSelect?: (row: UserEngagementRow) => void;
  onExport?: (data: UserEngagementRow[]) => Promise<void>;
  onRefresh?: () => Promise<void>;
  className?: string;
}

type FilterType = 'all' | 'success' | 'error' | 'recent' | 'component';
type TimeRange = '1h' | '24h' | '7d' | '30d';

// Custom cell renderers
const ComponentTypeRenderer = (params: any) => {
  const type = params.value;
  const icons = {
    'chat': '💬',
    'analytics': '📊',
    'memory': '🧠',
    'grid': '📋',
    'chart': '📈',
    'button': '🔘',
    'form': '📝',
    'modal': '🪟'
  };
  
  return (
    <div className="flex items-center gap-2">
      <span>{icons[type as keyof typeof icons] || '🔧'}</span>
      <Badge variant="outline" className="text-xs">
        {type}
      </Badge>
    </div>
  );
};

const InteractionTypeRenderer = (params: any) => {
  const type = params.value;
  const variants = {
    'click': 'default',
    'view': 'secondary',
    'hover': 'outline',
    'scroll': 'outline',
    'input': 'default',
    'submit': 'default',
    'error': 'destructive'
  } as const;
  
  const icons = {
    'click': <MousePointer className="h-3 w-3" />,
    'view': <Eye className="h-3 w-3" />,
    'hover': <Activity className="h-3 w-3" />,
    'scroll': <TrendingUp className="h-3 w-3" />,
    'input': <Search className="h-3 w-3" />,
    'submit': <CheckCircle className="h-3 w-3" />,
    'error': <AlertCircle className="h-3 w-3" />
  };
  
  return (
    <Badge variant={variants[type as keyof typeof variants] || 'outline'} className="text-xs flex items-center gap-1">
      {icons[type as keyof typeof icons]}
      {type}
    </Badge>
  );
};

const DurationRenderer = (params: any) => {
  const duration = params.value;
  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  };
  
  const color = duration > 10000 ? 'text-red-600' : duration > 5000 ? 'text-yellow-600' : 'text-green-600';
  
  return (
    <div className="flex items-center gap-2">
      <Clock className={`h-3 w-3 ${color}`} />
      <span className={`text-sm font-medium ${color}`}>
        {formatDuration(duration)}
      </span>
    </div>
  );
};

const SuccessRenderer = (params: any) => {
  const success = params.value;
  return (
    <div className="flex items-center gap-2">
      {success ? (
        <CheckCircle className="h-4 w-4 text-green-500" />
      ) : (
        <AlertCircle className="h-4 w-4 text-red-500" />
      )}
      <span className={`text-sm font-medium ${success ? 'text-green-600' : 'text-red-600'}`}>
        {success ? 'Success' : 'Error'}
      </span>
    </div>
  );
};

const TimestampRenderer = (params: any) => {
  const timestamp = new Date(params.value);
  return (
    <div className="text-sm">
      <div className="font-medium">{format(timestamp, 'MMM dd, HH:mm:ss')}</div>
      <div className="text-muted-foreground text-xs">
        {formatDistanceToNow(timestamp, { addSuffix: true })}
      </div>
    </div>
  );
};

const UserRenderer = (params: any) => {
  const userId = params.value;
  const shortId = userId ? userId.substring(0, 8) : 'anonymous';
  
  return (
    <div className="flex items-center gap-2">
      <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center">
        <Users className="h-3 w-3" />
      </div>
      <span className="text-sm font-mono">{shortId}</span>
    </div>
  );
};

export const UserEngagementGrid: React.FC<UserEngagementGridProps> = ({
  data = [],
  onRowSelect,
  onExport,
  onRefresh,
  className = ''
}) => {
  const { user } = useAuth();
  const { triggerHooks, registerGridHook } = useHooks();
  const { toast } = useToast();
  
  const [searchText, setSearchText] = useState('');
  const [filterType, setFilterType] = useState<FilterType>('all');
  const [timeRange, setTimeRange] = useState<TimeRange>('24h');
  const [selectedRows, setSelectedRows] = useState<UserEngagementRow[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Generate sample data if none provided
  const engagementData = useMemo(() => {
    if (data.length > 0) return data;
    
    const sampleData: UserEngagementRow[] = [];
    const components = ['chat', 'analytics', 'memory', 'grid', 'chart'];
    const interactions = ['click', 'view', 'hover', 'input', 'submit'];
    const users = ['user1', 'user2', 'user3', 'user4'];
    
    for (let i = 0; i < 50; i++) {
      const timestamp = new Date(Date.now() - Math.random() * 24 * 60 * 60 * 1000);
      const componentType = components[Math.floor(Math.random() * components.length)];
      const interactionType = interactions[Math.floor(Math.random() * interactions.length)];
      const success = Math.random() > 0.1; // 90% success rate
      
      sampleData.push({
        id: `engagement_${i}`,
        timestamp: timestamp.toISOString(),
        userId: users[Math.floor(Math.random() * users.length)],
        componentType,
        componentId: `${componentType}_${Math.floor(Math.random() * 100)}`,
        interactionType,
        duration: Math.floor(Math.random() * 15000) + 100,
        success,
        errorMessage: success ? undefined : 'Component failed to load',
        sessionId: `session_${Math.floor(Math.random() * 10)}`,
        userAgent: 'Mozilla/5.0 (Chrome)',
        location: 'dashboard'
      });
    }
    
    return sampleData.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  }, [data]);

  // Column definitions
  const columnDefs: ColDef[] = useMemo(() => [
    {
      field: 'timestamp',
      headerName: 'Time',
      width: 180,
      sortable: true,
      filter: 'agDateColumnFilter',
      cellRenderer: TimestampRenderer,
      sort: 'desc'
    },
    {
      field: 'userId',
      headerName: 'User',
      width: 120,
      sortable: true,
      filter: 'agTextColumnFilter',
      cellRenderer: UserRenderer
    },
    {
      field: 'componentType',
      headerName: 'Component',
      width: 140,
      sortable: true,
      filter: 'agSetColumnFilter',
      cellRenderer: ComponentTypeRenderer
    },
    {
      field: 'componentId',
      headerName: 'Component ID',
      width: 150,
      sortable: true,
      filter: 'agTextColumnFilter',
      cellStyle: { fontSize: '12px', fontFamily: 'monospace' } as any
    },
    {
      field: 'interactionType',
      headerName: 'Interaction',
      width: 120,
      sortable: true,
      filter: 'agSetColumnFilter',
      cellRenderer: InteractionTypeRenderer
    },
    {
      field: 'duration',
      headerName: 'Duration',
      width: 120,
      sortable: true,
      filter: 'agNumberColumnFilter',
      cellRenderer: DurationRenderer
    },
    {
      field: 'success',
      headerName: 'Status',
      width: 100,
      sortable: true,
      filter: 'agSetColumnFilter',
      cellRenderer: SuccessRenderer
    },
    {
      field: 'errorMessage',
      headerName: 'Error',
      width: 200,
      sortable: false,
      filter: 'agTextColumnFilter',
      cellStyle: { color: '#ef4444', fontSize: '12px' } as any,
      valueFormatter: (params) => params.value || '-'
    },
    {
      field: 'location',
      headerName: 'Location',
      width: 120,
      sortable: true,
      filter: 'agTextColumnFilter'
    }
  ], []);

  // Default column properties
  const defaultColDef = useMemo(() => ({
    resizable: true,
    sortable: true,
    filter: true,
    floatingFilter: true
  }), []);

  // Filter data based on search and filters
  const filteredData = useMemo(() => {
    let filtered = [...engagementData];
    
    // Apply time range filter
    const now = new Date();
    const timeRangeMs = {
      '1h': 60 * 60 * 1000,
      '24h': 24 * 60 * 60 * 1000,
      '7d': 7 * 24 * 60 * 60 * 1000,
      '30d': 30 * 24 * 60 * 60 * 1000
    };
    
    const cutoff = new Date(now.getTime() - timeRangeMs[timeRange]);
    filtered = filtered.filter(row => new Date(row.timestamp) > cutoff);
    
    // Apply filter type
    switch (filterType) {
      case 'success':
        filtered = filtered.filter(row => row.success);
        break;
      case 'error':
        filtered = filtered.filter(row => !row.success);
        break;
      case 'recent':
        filtered = filtered.slice(0, 20);
        break;
    }
    
    // Apply search filter
    if (searchText) {
      const searchLower = searchText.toLowerCase();
      filtered = filtered.filter(row =>
        row.userId.toLowerCase().includes(searchLower) ||
        row.componentType.toLowerCase().includes(searchLower) ||
        row.componentId.toLowerCase().includes(searchLower) ||
        row.interactionType.toLowerCase().includes(searchLower) ||
        (row.errorMessage && row.errorMessage.toLowerCase().includes(searchLower))
      );
    }
    
    return filtered;
  }, [engagementData, searchText, filterType, timeRange]);

  // Register grid hooks
  useEffect(() => {
    const hookIds: string[] = [];

    hookIds.push(registerGridHook('userEngagement', 'dataLoad', async (params) => {
      console.log('User engagement grid data loaded:', params);
      return { success: true, rowCount: filteredData.length };
    }));

    hookIds.push(registerGridHook('userEngagement', 'rowSelected', async (params) => {
      console.log('User engagement row selected:', params);
      return { success: true, selectedRow: params.data };
    }));

    return () => {
      // Cleanup hooks
    };
  }, [registerGridHook, filteredData.length]);

  // Handle grid events
  const onGridReady = useCallback(async (params: GridReadyEvent) => {
    await triggerHooks('grid_userEngagement_dataLoad', {
      gridId: 'userEngagement',
      api: params.api,
      rowCount: filteredData.length,
      filterType,
      timeRange
    }, { userId: user?.user_id });
  }, [triggerHooks, filteredData.length, filterType, timeRange, user?.user_id]);

  const onSelectionChanged = useCallback(async (event: any) => {
    const selectedNodes = event.api.getSelectedNodes();
    const selectedData = selectedNodes.map((node: any) => node.data);
    setSelectedRows(selectedData);

    if (selectedData.length > 0 && onRowSelect) {
      onRowSelect(selectedData[0]);
    }

    for (const row of selectedData) {
      await triggerHooks('grid_userEngagement_rowSelected', {
        gridId: 'userEngagement',
        data: row,
        api: event.api
      }, { userId: user?.user_id });
    }
  }, [triggerHooks, onRowSelect, user?.user_id]);

  // Handle export
  const handleExport = useCallback(async () => {
    if (!onExport) return;
    
    setIsLoading(true);
    try {
      await onExport(filteredData);
      toast({
        title: 'Export Successful',
        description: `Exported ${filteredData.length} engagement records.`
      });
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Export Failed',
        description: 'Failed to export engagement data. Please try again.'
      });
    } finally {
      setIsLoading(false);
    }
  }, [onExport, filteredData, toast]);

  // Handle refresh
  const handleRefresh = useCallback(async () => {
    if (!onRefresh) return;
    
    setIsLoading(true);
    try {
      await onRefresh();
      toast({
        title: 'Data Refreshed',
        description: 'User engagement data has been updated.'
      });
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Refresh Failed',
        description: 'Failed to refresh engagement data. Please try again.'
      });
    } finally {
      setIsLoading(false);
    }
  }, [onRefresh, toast]);

  // Calculate summary statistics
  const summaryStats = useMemo(() => {
    if (filteredData.length === 0) return null;

    const totalInteractions = filteredData.length;
    const successfulInteractions = filteredData.filter(row => row.success).length;
    const avgDuration = filteredData.reduce((sum, row) => sum + row.duration, 0) / totalInteractions;
    const uniqueUsers = new Set(filteredData.map(row => row.userId)).size;
    const topComponents = Object.entries(
      filteredData.reduce((acc, row) => {
        acc[row.componentType] = (acc[row.componentType] || 0) + 1;
        return acc;
      }, {} as Record<string, number>)
    ).sort(([,a], [,b]) => b - a).slice(0, 3);

    return {
      totalInteractions,
      successRate: (successfulInteractions / totalInteractions * 100).toFixed(1),
      avgDuration: Math.round(avgDuration),
      uniqueUsers,
      topComponents
    };
  }, [filteredData]);

  return (
    <Card className={`w-full ${className}`}>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            User Engagement Analytics ({filteredData.length} records)
          </CardTitle>
          
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleExport}
              disabled={isLoading || filteredData.length === 0}
            >
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={isLoading}
            >
              <Activity className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </div>

        {/* Summary Statistics */}
        {summaryStats && (
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mt-4">
            <div className="p-3 bg-muted/50 rounded-lg">
              <div className="text-sm text-muted-foreground">Total Interactions</div>
              <div className="text-xl font-bold">{summaryStats.totalInteractions}</div>
            </div>
            <div className="p-3 bg-muted/50 rounded-lg">
              <div className="text-sm text-muted-foreground">Success Rate</div>
              <div className="text-xl font-bold text-green-600">{summaryStats.successRate}%</div>
            </div>
            <div className="p-3 bg-muted/50 rounded-lg">
              <div className="text-sm text-muted-foreground">Avg Duration</div>
              <div className="text-xl font-bold">{summaryStats.avgDuration}ms</div>
            </div>
            <div className="p-3 bg-muted/50 rounded-lg">
              <div className="text-sm text-muted-foreground">Unique Users</div>
              <div className="text-xl font-bold">{summaryStats.uniqueUsers}</div>
            </div>
            <div className="p-3 bg-muted/50 rounded-lg">
              <div className="text-sm text-muted-foreground">Top Component</div>
              <div className="text-lg font-bold">
                {summaryStats.topComponents[0]?.[0] || 'N/A'}
              </div>
            </div>
          </div>
        )}

        {/* Filters and Search */}
        <div className="flex items-center gap-4 mt-4">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search interactions..."
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              className="pl-10"
            />
          </div>
          
          <Select value={filterType} onValueChange={(value) => setFilterType(value as FilterType)}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Interactions</SelectItem>
              <SelectItem value="success">Successful Only</SelectItem>
              <SelectItem value="error">Errors Only</SelectItem>
              <SelectItem value="recent">Recent (20)</SelectItem>
            </SelectContent>
          </Select>
          
          <Select value={timeRange} onValueChange={(value) => setTimeRange(value as TimeRange)}>
            <SelectTrigger className="w-24">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1h">1H</SelectItem>
              <SelectItem value="24h">24H</SelectItem>
              <SelectItem value="7d">7D</SelectItem>
              <SelectItem value="30d">30D</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {selectedRows.length > 0 && (
          <div className="flex items-center gap-2 mt-2">
            <Badge variant="secondary">
              {selectedRows.length} selected
            </Badge>
            <Button variant="outline" size="sm">
              Analyze Selected
            </Button>
          </div>
        )}
      </CardHeader>

      <CardContent className="p-0">
        <div className="ag-theme-alpine h-[600px] w-full">
          <AgGridReact
            rowData={filteredData}
            columnDefs={columnDefs}
            defaultColDef={defaultColDef}
            onGridReady={onGridReady}
            onSelectionChanged={onSelectionChanged}
            rowSelection="multiple"
            animateRows={true}
            getRowId={(params) => params.data.id}
            pagination={true}
            paginationPageSize={50}
            suppressRowClickSelection={false}
          />
        </div>
      </CardContent>
    </Card>
  );
};