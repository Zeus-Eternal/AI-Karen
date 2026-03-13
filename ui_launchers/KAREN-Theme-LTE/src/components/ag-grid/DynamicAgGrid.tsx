"use client";

import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Search,
  Filter,
  Plus,
  Download,
  Trash2,
  Edit,
  Eye,
  MoreHorizontal,
  RefreshCw,
  Settings,
  Maximize2,
  Grid3x3
} from 'lucide-react';
import { cn } from '@/lib/utils';

// Utility function for date formatting
function formatDate(date: Date): string {
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'UTC'
  });
}

// Mock AG Grid interface
interface GridColumn {
  field: string;
  headerName: string;
  headerTooltip?: string;
  width?: number;
  pinned?: boolean;
  sortable?: boolean;
  filter?: boolean;
  editable?: boolean;
  resizable?: boolean;
}

interface GridData {
  id: string;
  [key: string]: any;
}

interface AgGridProps {
  className?: string;
}

export default function DynamicAgGrid({ className }: AgGridProps) {
  const [gridData, setGridData] = useState<GridData[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRows, setSelectedRows] = useState<string[]>([]);
  const [columnConfig, setColumnConfig] = useState<GridColumn[]>([]);
  const [gridTheme, setGridTheme] = useState<'light' | 'dark'>('light');

  // Mock data - replace with actual API call
  useEffect(() => {
    const mockColumns: GridColumn[] = [
      {
        field: 'id',
        headerName: 'ID',
        width: 100,
        pinned: true,
        sortable: false,
      },
      {
        field: 'name',
        headerName: 'Name',
        width: 200,
        sortable: true,
        filter: true,
      },
      {
        field: 'type',
        headerName: 'Type',
        width: 120,
        filter: true,
      },
      {
        field: 'status',
        headerName: 'Status',
        width: 100,
        filter: true,
      },
      {
        field: 'created',
        headerName: 'Created',
        width: 150,
        sortable: true,
      },
      {
        field: 'updated',
        headerName: 'Updated',
        width: 150,
        sortable: true,
      },
      {
        field: 'size',
        headerName: 'Size',
        width: 100,
        sortable: true,
      },
      {
        field: 'owner',
        headerName: 'Owner',
        width: 120,
        filter: true,
      },
      {
        field: 'tags',
        headerName: 'Tags',
        width: 200,
        filter: true,
      },
    ];

    const mockData: GridData[] = [
      {
        id: '1',
        name: 'User Authentication System',
        type: 'security',
        status: 'active',
        created: new Date(Date.now() - 86400000).toISOString(),
        updated: new Date(Date.now() - 3600000).toISOString(),
        size: 'large',
        owner: 'security-team',
        tags: ['authentication', 'security', 'user-management'],
      },
      {
        id: '2',
        name: 'Performance Monitor',
        type: 'analytics',
        status: 'active',
        created: new Date(Date.now() - 172800000).toISOString(),
        updated: new Date(Date.now() - 86400000).toISOString(),
        size: 'medium',
        owner: 'analytics-team',
        tags: ['performance', 'monitoring', 'metrics'],
      },
      {
        id: '3',
        name: 'Chat Interface',
        type: 'communication',
        status: 'development',
        created: new Date(Date.now() - 259200000).toISOString(),
        updated: new Date(Date.now() - 172800000).toISOString(),
        size: 'small',
        owner: 'frontend-team',
        tags: ['chat', 'messaging', 'ui'],
      },
      {
        id: '4',
        name: 'Memory Management',
        type: 'data',
        status: 'active',
        created: new Date(Date.now() - 604800000).toISOString(),
        updated: new Date(Date.now() - 86400000).toISOString(),
        size: 'medium',
        owner: 'backend-team',
        tags: ['memory', 'data', 'storage'],
      },
      {
        id: '5',
        name: 'File Management',
        type: 'utility',
        status: 'planning',
        created: new Date(Date.now() - 432000000).toISOString(),
        updated: new Date(Date.now() - 172800000).toISOString(),
        size: 'large',
        owner: 'backend-team',
        tags: ['files', 'storage', 'management'],
      },
    ];

    setGridData(mockData);
    setColumnConfig(mockColumns);
    setLoading(false);
  }, []);

  // Filter data
  const filteredData = useMemo(() => {
    if (!searchQuery) return gridData;
    
    return gridData.filter(item =>
      Object.values(item).some(value =>
        String(value).toLowerCase().includes(searchQuery.toLowerCase())
      )
    );
  }, [gridData, searchQuery]);

  const gridRef = useRef<HTMLDivElement>(null);

  const handleRefresh = () => {
    setLoading(true);
    // Simulate refresh
    setTimeout(() => {
      // In real implementation, this would fetch fresh data
      setLoading(false);
    }, 1000);
  };

  const handleExport = () => {
    // In real implementation, this would export grid data
    const data = {
      columns: columnConfig,
      rows: filteredData,
      exportedAt: new Date().toISOString(),
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `grid-config-${formatDate(new Date())}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleRowSelection = (rows: string[]) => {
    setSelectedRows(rows);
  };

  const handleColumnConfig = () => {
    // In real implementation, this would open column configuration dialog
    alert('Column configuration dialog would open here');
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'development': return 'bg-yellow-100 text-yellow-800';
      case 'planning': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'security': return 'bg-red-100 text-red-800';
      case 'analytics': return 'bg-purple-100 text-purple-800';
      case 'communication': return 'bg-blue-100 text-blue-800';
      case 'data': return 'bg-green-100 text-green-800';
      case 'utility': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className={cn("space-y-6", className)}>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Grid3x3 className="h-5 w-5" />
            Dynamic AG Grid
          </CardTitle>
          <CardDescription>
            Advanced data grid with customizable columns and filtering
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Grid Controls */}
          <div className="flex flex-col gap-4 mb-6">
            <div className="flex gap-2">
              <Input
                placeholder="Search grid data..."
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
                onClick={handleColumnConfig}
              >
                <Settings className="h-4 w-4 mr-2" />
                Configure Columns
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
            
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setGridTheme(gridTheme === 'light' ? 'dark' : 'light')}
              >
                {gridTheme === 'light' ? '🌙' : '🌙'} Theme
              </Button>
              
              <Badge className="text-xs bg-secondary text-secondary-foreground">
                {filteredData.length} rows • {columnConfig.length} columns
              </Badge>
            </div>
          </div>

          {/* AG Grid */}
          <div 
            ref={gridRef}
            className="ag-theme-alpine dark:ag-theme-balham border border-border rounded-lg overflow-hidden"
            style={{ height: '600px' }}
          >
            {/* In a real implementation, this would use AG Grid library */}
            <div className="p-4">
              <div className="text-center py-8">
                <Grid3x3 className="h-8 w-8 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium">AG Grid Component</h3>
                <p className="text-muted-foreground mb-4">
                  Advanced data grid with sorting, filtering, and pagination
                </p>
                
                <div className="grid grid-cols-7 gap-2 text-sm">
                  {columnConfig.map((col, index) => (
                    <div key={index} className="font-medium p-2 bg-muted rounded">
                      {col.headerName}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Mock Grid Data Display */}
            <div className="p-4 space-y-2">
              {filteredData.map((row) => (
                <div key={row.id} className="border border-border rounded p-3 hover:bg-accent/50">
                  <div className="grid grid-cols-7 gap-2 text-sm">
                    {columnConfig.map((col, index) => (
                      <div key={index} className="p-2">
                        {row[col.field]}
                      </div>
                    ))}
                  </div>
                  
                  <div className="flex gap-2 mt-2">
                    <Badge
                      className={cn("text-xs", getTypeColor(row.type))}
                    >
                      {row.type}
                    </Badge>
                    
                    <Badge
                      className={cn("text-xs border border-current", getStatusColor(row.status))}
                    >
                      {row.status}
                    </Badge>
                    
                    <div className="text-xs text-muted-foreground">
                      Created: {formatDate(new Date(row.created))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Empty State */}
          {filteredData.length === 0 && !loading && (
            <div className="text-center py-8">
              <Grid3x3 className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium">No grid data found</h3>
              <p className="text-muted-foreground">
                {searchQuery 
                  ? `No data matching "${searchQuery}"`
                  : 'No grid data available'
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
              <p className="text-muted-foreground mt-2">Loading grid data...</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}