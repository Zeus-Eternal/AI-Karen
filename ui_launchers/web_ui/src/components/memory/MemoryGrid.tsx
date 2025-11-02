/**
 * AG-UI Memory Grid Component
 * Displays memory data in an interactive grid with filtering and sorting
 */
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { AgGridReact } from 'ag-grid-react';
import { ColDef, GridReadyEvent, FilterChangedEvent } from 'ag-grid-community';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';
interface MemoryGridRow {
  id: string;
  content: string;
  type: 'fact' | 'preference' | 'context';
  confidence: number;
  last_accessed: string;
  relevance_score: number;
  semantic_cluster: string;
  relationships: string[];
  timestamp: number;
  user_id: string;
  session_id?: string;
  tenant_id?: string;
}
interface MemoryGridProps {
  userId: string;
  tenantId?: string;
  onMemorySelect?: (memory: MemoryGridRow) => void;
  onMemoryEdit?: (memory: MemoryGridRow) => void;
  filters?: Record<string, any>;
  height?: number;
}
// Custom cell renderers
const ConfidenceCellRenderer = (params: any) => {
  const confidence = params.value;
  const percentage = Math.round(confidence * 100);
  const color = confidence > 0.8 ? '#4CAF50' : confidence > 0.6 ? '#FF9800' : '#F44336';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <div 
        style={{
          width: '60px',
          height: '8px',
          backgroundColor: '#e0e0e0',
          borderRadius: '4px',
          overflow: 'hidden'
        }}
      >
        <div 
          style={{
            width: `${percentage}%`,
            height: '100%',
            backgroundColor: color,
            transition: 'width 0.3s ease'
          }}
        />
      </div>
      <span style={{ fontSize: '12px', color: '#666' }}>{percentage}%</span>
    </div>
  );
};
const TypeCellRenderer = (params: any) => {
  const type = params.value;
  const colors = {
    fact: '#2196F3',
    preference: '#9C27B0',
    context: '#FF9800'
  };
  return (
    <span 
      style={{
        padding: '4px 8px',
        borderRadius: '12px',
        backgroundColor: colors[type as keyof typeof colors] || '#666',
        color: 'white',
        fontSize: '11px',
        fontWeight: 'bold'
      }}
    >
      {type.toUpperCase()}
    </span>
  );
};
const RelationshipsCellRenderer = (params: any) => {
  const relationships = params.value || [];
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
      <span style={{ fontSize: '12px', color: '#666' }}>
        {relationships.length} connections
      </span>
      {relationships.length > 0 && (
        <div 
          style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: '#4CAF50'
          }}
        />
      )}
    </div>
  );
};
const ContentCellRenderer = (params: any) => {
  const content = params.value;
  const [expanded, setExpanded] = useState(false);
  if (content.length <= 100) {
    return <span>{content}</span>;
  }
  return (
    <div>
      <span>{expanded ? content : `${content.substring(0, 100)}...`}</span>
      <button
        onClick={() = aria-label="Button"> setExpanded(!expanded)}
        style={{
          marginLeft: '8px',
          padding: '2px 6px',
          fontSize: '10px',
          border: '1px solid #ccc',
          borderRadius: '4px',
          backgroundColor: 'transparent',
          cursor: 'pointer'
        }}
      >
        {expanded ? 'Less' : 'More'}
      </button>
    </div>
  );
};
export const MemoryGrid: React.FC<MemoryGridProps> = ({
  userId,
  tenantId,
  onMemorySelect,
  onMemoryEdit,
  filters,
  height = 400
}) => {
  const [rowData, setRowData] = useState<MemoryGridRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Column definitions for AG-Grid
  const columnDefs: ColDef[] = useMemo(() => [
    {
      headerName: 'Content',
      field: 'content',
      flex: 2,
      cellRenderer: ContentCellRenderer,
      filter: 'agTextColumnFilter',
      sortable: true,
      resizable: true
    },
    {
      headerName: 'Type',
      field: 'type',
      width: 100,
      cellRenderer: TypeCellRenderer,
      filter: 'agSetColumnFilter',
      sortable: true
    },
    {
      headerName: 'Confidence',
      field: 'confidence',
      width: 120,
      cellRenderer: ConfidenceCellRenderer,
      filter: 'agNumberColumnFilter',
      sortable: true
    },
    {
      headerName: 'Cluster',
      field: 'semantic_cluster',
      width: 100,
      filter: 'agSetColumnFilter',
      sortable: true,
      cellStyle: { textTransform: 'capitalize' }
    },
    {
      headerName: 'Relationships',
      field: 'relationships',
      width: 120,
      cellRenderer: RelationshipsCellRenderer,
      sortable: true,
      comparator: (a: string[], b: string[]) => a.length - b.length
    },
    {
      headerName: 'Last Accessed',
      field: 'last_accessed',
      width: 140,
      filter: 'agDateColumnFilter',
      sortable: true,
      valueFormatter: (params) => {
        const date = new Date(params.value);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      }
    },
    {
      headerName: 'Relevance',
      field: 'relevance_score',
      width: 100,
      filter: 'agNumberColumnFilter',
      sortable: true,
      valueFormatter: (params) => `${Math.round(params.value * 100)}%`
    }
  ], []);
  // Default column properties
  const defaultColDef = useMemo(() => ({
    sortable: true,
    filter: true,
    resizable: true,
    minWidth: 80
  }), []);
  // Fetch memory data
  const fetchMemoryData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch('/api/memory/grid', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          tenant_id: tenantId,
          filters: filters || {}
        })
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setRowData(data.memories || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load memory data');
    } finally {
      setLoading(false);
    }
  }, [userId, tenantId, filters]);
  // Load data on mount and when dependencies change
  useEffect(() => {
    fetchMemoryData();
  }, [fetchMemoryData]);
  // Handle grid events
  const onGridReady = (params: GridReadyEvent) => {
    params.api.sizeColumnsToFit();
  };
  const onFilterChanged = (event: FilterChangedEvent) => {
    // Optional: Handle filter changes for analytics
    console.log('Filters changed:', event.api.getFilterModel());
  };
  const onRowClicked = (event: any) => {
    if (onMemorySelect) {
      onMemorySelect(event.data);
    }
  };
  const onRowDoubleClicked = (event: any) => {
    if (onMemoryEdit) {
      onMemoryEdit(event.data);
    }
  };
  // Grid options
  const gridOptions = {
    pagination: true,
    paginationPageSize: 50,
    rowSelection: 'single' as const,
    animateRows: true,
    enableRangeSelection: true,
    suppressRowClickSelection: false,
    rowHeight: 60,
    headerHeight: 40
  };
  if (error) {
    return (
      <div className="memory-grid-error" style={{ 
        padding: '20px', 
        textAlign: 'center', 
        color: '#f44336',
        border: '1px solid #f44336',
        borderRadius: '4px',
        backgroundColor: '#ffebee'
      }}>
        <h3>Error Loading Memory Data</h3>
        <p>{error}</p>
        <button 
          onClick={fetchMemoryData}
          style={{
            padding: '8px 16px',
            backgroundColor: '#f44336',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
         aria-label="Button">
          Retry
        </button>
      </div>
    );
  }
  return (
    <div className="memory-grid-container" style={{ height: `${height}px` }}>
      {loading && (
        <div style={{ 
          position: 'absolute', 
          top: '50%', 
          left: '50%', 
          transform: 'translate(-50%, -50%)',
          zIndex: 1000,
          backgroundColor: 'rgba(255, 255, 255, 0.9)',
          padding: '20px',
          borderRadius: '4px'
        }}>
          Loading memory data...
        </div>
      )}
      <div className="ag-theme-alpine" style={{ height: '100%', width: '100%' }}>
        <AgGridReact
          rowData={rowData}
          columnDefs={columnDefs}
          defaultColDef={defaultColDef}
          gridOptions={gridOptions}
          onGridReady={onGridReady}
          onFilterChanged={onFilterChanged}
          onRowClicked={onRowClicked}
          onRowDoubleClicked={onRowDoubleClicked}
          suppressMenuHide={true}
          enableCellTextSelection={true}
        />
      </div>
    </div>
  );
};
export default MemoryGrid;
