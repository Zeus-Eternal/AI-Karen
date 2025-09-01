/**
 * Comprehensive Memory Interface Component
 * Combines AG-UI grid, network visualization, and CopilotKit-enhanced editing
 */

import React, { useState, useCallback, useEffect, useMemo } from 'react';
import { CopilotKit } from '@copilotkit/react-core';
import dynamic from 'next/dynamic';
import MemoryGrid from './MemoryGrid';
// Lazy-load the network visualization and charts only when needed
const MemoryNetworkVisualization = dynamic(() => import('./MemoryNetworkVisualization'), { ssr: false });
import MemoryEditor from './MemoryEditor';
const AgCharts = dynamic(() => import('ag-charts-react').then(m => m.AgCharts), { ssr: false });
import { AgChartOptions } from 'ag-charts-community';
import { v4 as uuidv4 } from 'uuid';

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

interface MemoryNetworkNode {
  id: string;
  label: string;
  type: string;
  confidence: number;
  cluster: string;
  size: number;
  color: string;
}

interface MemoryAnalytics {
  total_memories: number;
  memories_by_type: Record<string, number>;
  memories_by_cluster: Record<string, number>;
  confidence_distribution: Array<{ range: string; count: number }>;
  access_patterns: Array<{ date: string; count: number }>;
  relationship_stats: Record<string, number>;
}

interface MemoryInterfaceProps {
  userId: string;
  tenantId?: string;
  copilotApiKey?: string;
  height?: number;
}

type ViewMode = 'grid' | 'network' | 'analytics';

export const MemoryInterface: React.FC<MemoryInterfaceProps> = ({
  userId,
  tenantId,
  copilotApiKey,
  height = 600
}) => {
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [selectedMemory, setSelectedMemory] = useState<MemoryGridRow | null>(null);
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<Record<string, any>>({});
  const [analytics, setAnalytics] = useState<MemoryAnalytics | null>(null);
  const [isLoadingAnalytics, setIsLoadingAnalytics] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Generate a unique component instance ID for error tracking
  const componentInstanceId = useMemo(() => uuidv4(), []);

  // Fetch analytics data with proper error handling
  const fetchAnalytics = useCallback(async () => {
    try {
      setIsLoadingAnalytics(true);
      setError(null);
      
      const response = await fetch('/api/memory/analytics', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          tenant_id: tenantId,
          timeframe_days: 30
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setAnalytics(data);
    } catch (err) {
      console.error(`Error fetching analytics [${componentInstanceId}]:`, err);
      setError('Failed to load analytics. Please try again later.');
      setAnalytics(null);
    } finally {
      setIsLoadingAnalytics(false);
    }
  }, [userId, tenantId, componentInstanceId]);

  // Load analytics when switching to analytics view
  useEffect(() => {
    if (viewMode === 'analytics' && !analytics && !isLoadingAnalytics) {
      fetchAnalytics();
    }
  }, [viewMode, analytics, isLoadingAnalytics, fetchAnalytics]);

  // Handle memory selection
  const handleMemorySelect = useCallback((memory: MemoryGridRow) => {
    setSelectedMemory(memory);
  }, []);

  // Handle memory editing
  const handleMemoryEdit = useCallback((memory: MemoryGridRow) => {
    setSelectedMemory(memory);
    setIsEditorOpen(true);
  }, []);

  // Handle memory save with error handling
  const handleMemorySave = useCallback(async (updatedMemory: Partial<MemoryGridRow>) => {
    try {
      setError(null);
      
      if (!selectedMemory?.id && !updatedMemory.content) {
        throw new Error('Memory content is required');
      }

      const response = await fetch('/api/memory/update', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          tenant_id: tenantId,
          memory_id: selectedMemory?.id || undefined,
          query: selectedMemory?.content || '',
          result: updatedMemory.content,
          metadata: {
            type: updatedMemory.type || 'fact',
            confidence: updatedMemory.confidence || 0.8,
            semantic_cluster: updatedMemory.semantic_cluster || 'default',
            updated_at: new Date().toISOString()
          }
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to save memory: ${response.statusText}`);
      }

      setIsEditorOpen(false);
      setSelectedMemory(null);
      // In a real app, you would update local state instead of reloading
      window.location.reload();
    } catch (err) {
      console.error(`Error saving memory [${componentInstanceId}]:`, err);
      setError(err instanceof Error ? err.message : 'Failed to save memory');
      throw err;
    }
  }, [selectedMemory, userId, tenantId, componentInstanceId]);

  // Handle memory deletion with error handling
  const handleMemoryDelete = useCallback(async (memoryId: string) => {
    try {
      setError(null);
      
      // In a real implementation, you'd have a proper delete endpoint
      const response = await fetch('/api/memory/delete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          tenant_id: tenantId,
          memory_id: memoryId
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to delete memory: ${response.statusText}`);
      }

      setIsEditorOpen(false);
      setSelectedMemory(null);
      // In a real app, you would update local state instead of reloading
      window.location.reload();
    } catch (err) {
      console.error(`Error deleting memory [${componentInstanceId}]:`, err);
      setError(err instanceof Error ? err.message : 'Failed to delete memory');
      throw err;
    }
  }, [userId, tenantId, componentInstanceId]);

  // Handle editor cancel
  const handleEditorCancel = useCallback(() => {
    setIsEditorOpen(false);
    setSelectedMemory(null);
    setError(null);
  }, []);

  // Handle node selection in network view
  const handleNodeSelect = useCallback((node: MemoryNetworkNode) => {
    console.log('Selected node:', node);
    // You could show node details or switch to grid view with filters
  }, []);

  // Handle search with error handling
  const handleSearch = useCallback(async () => {
    if (!searchQuery.trim()) {
      setFilters(prev => {
        const newFilters = {...prev};
        delete newFilters.search_results;
        return newFilters;
      });
      return;
    }

    try {
      setError(null);
      
      const response = await fetch('/api/memory/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          tenant_id: tenantId,
          query: searchQuery,
          filters: filters,
          limit: 50
        })
      });

      if (!response.ok) {
        throw new Error(`Search failed: ${response.statusText}`);
      }

      const data = await response.json();
      setFilters({ ...filters, search_results: data.results });
      setViewMode('grid');
    } catch (err) {
      console.error(`Error searching memories [${componentInstanceId}]:`, err);
      setError(err instanceof Error ? err.message : 'Search failed');
    }
  }, [searchQuery, filters, userId, tenantId, componentInstanceId]);

  // Create new memory
  const handleCreateMemory = useCallback(() => {
    setSelectedMemory(null);
    setIsEditorOpen(true);
    setError(null);
  }, []);

  // Analytics chart configurations using useMemo for performance
  const analyticsCharts = useMemo(() => {
    if (!analytics) return [];

    const charts = [];

    // Memory types pie chart
    if (analytics.memories_by_type) {
      const typeData = Object.entries(analytics.memories_by_type).map(([type, count]) => ({
        type: type.charAt(0).toUpperCase() + type.slice(1),
        count
      }));

      charts.push({
        title: 'Memory Types Distribution',
        data: typeData,
        series: [{
          type: 'pie',
          angleKey: 'count',
          labelKey: 'type',
          label: {
            enabled: true,
          },
        }],
      });
    }

    // Confidence distribution bar chart
    if (analytics.confidence_distribution) {
      charts.push({
        title: 'Confidence Score Distribution',
        data: analytics.confidence_distribution,
        axes: [
          {
            type: 'category',
            position: 'bottom',
          },
          {
            type: 'number',
            position: 'left',
          },
        ],
        series: [{
          type: 'column',
          xKey: 'range',
          yKey: 'count',
        }],
      });
    }

    // Access patterns line chart
    if (analytics.access_patterns) {
      charts.push({
        title: 'Memory Access Patterns (Last 30 Days)',
        data: analytics.access_patterns,
        axes: [
          {
            type: 'time',
            position: 'bottom',
            label: {
              format: '%b %d',
            },
          },
          {
            type: 'number',
            position: 'left',
          },
        ],
        series: [{
          type: 'line',
          xKey: 'date',
          yKey: 'count',
          marker: {
            enabled: true,
          },
        }],
      });
    }

    return charts;
  }, [analytics]);

  // View mode button styles
  const viewModeButtonStyles = useMemo(() => ({
    base: {
      padding: '8px 16px',
      border: '1px solid #ddd',
      borderRadius: '4px',
      cursor: 'pointer',
      transition: 'all 0.2s ease',
    },
    active: {
      backgroundColor: '#2196F3',
      color: '#fff',
      borderColor: '#2196F3',
    },
    inactive: {
      backgroundColor: '#fff',
      color: '#333',
      borderColor: '#ddd',
    }
  }), []);

  return (
    <CopilotKit>
      <div className="memory-interface" style={{ 
        height: `${height}px`, 
        display: 'flex', 
        flexDirection: 'column',
        position: 'relative',
      }}>
        {/* Error display */}
        {error && (
          <div style={{
            position: 'absolute',
            top: '16px',
            right: '16px',
            padding: '12px 16px',
            backgroundColor: '#ffebee',
            color: '#c62828',
            borderRadius: '4px',
            border: '1px solid #ef9a9a',
            zIndex: 1000,
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}>
            <span>{error}</span>
            <button 
              onClick={() => setError(null)}
              style={{
                background: 'none',
                border: 'none',
                color: '#c62828',
                cursor: 'pointer',
                fontSize: '16px',
              }}
            >
              ×
            </button>
          </div>
        )}

        {/* Header with controls */}
        <div style={{ 
          padding: '16px', 
          borderBottom: '1px solid #ddd',
          backgroundColor: '#f8f9fa',
          display: 'flex',
          alignItems: 'center',
          gap: '16px',
          flexWrap: 'wrap'
        }}>
          <h2 style={{ margin: 0, color: '#333' }}>Memory Management</h2>
          
          {/* View mode selector */}
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => setViewMode('grid')}
              style={{
                ...viewModeButtonStyles.base,
                ...(viewMode === 'grid' ? viewModeButtonStyles.active : viewModeButtonStyles.inactive)
              }}
            >
              Grid View
            </button>
            <button
              onClick={() => setViewMode('network')}
              style={{
                ...viewModeButtonStyles.base,
                ...(viewMode === 'network' ? viewModeButtonStyles.active : viewModeButtonStyles.inactive)
              }}
            >
              Network View
            </button>
            <button
              onClick={() => setViewMode('analytics')}
              style={{
                ...viewModeButtonStyles.base,
                ...(viewMode === 'analytics' ? viewModeButtonStyles.active : viewModeButtonStyles.inactive)
              }}
            >
              Analytics
            </button>
          </div>

          {/* Search and action buttons */}
          <div style={{ 
            display: 'flex', 
            gap: '8px', 
            marginLeft: 'auto',
            flexWrap: 'wrap',
            justifyContent: 'flex-end',
            flexGrow: 1,
            minWidth: '300px'
          }}>
            <div style={{ display: 'flex', gap: '8px', flexGrow: 1, maxWidth: '400px' }}>
              <input
                type="text"
                placeholder="Search memories..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                style={{
                  padding: '8px 12px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  flexGrow: 1,
                  minWidth: '120px'
                }}
              />
              <button
                onClick={handleSearch}
                disabled={!searchQuery.trim()}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#4CAF50',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: searchQuery.trim() ? 'pointer' : 'not-allowed',
                  opacity: searchQuery.trim() ? 1 : 0.6,
                  whiteSpace: 'nowrap'
                }}
              >
                Search
              </button>
            </div>
            <button
              onClick={handleCreateMemory}
              style={{
                padding: '8px 16px',
                backgroundColor: '#FF9800',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                whiteSpace: 'nowrap'
              }}
            >
              New Memory
            </button>
          </div>
        </div>

        {/* Main content area */}
        <div style={{ flex: 1, overflow: 'hidden', padding: '16px' }}>
          {viewMode === 'grid' && (
            <MemoryGrid
              userId={userId}
              tenantId={tenantId}
              onMemorySelect={handleMemorySelect}
              onMemoryEdit={handleMemoryEdit}
              filters={filters}
              height={height - 120}
            />
          )}

          {viewMode === 'network' && (
            <MemoryNetworkVisualization
              userId={userId}
              tenantId={tenantId}
              onNodeSelect={handleNodeSelect}
              onNodeDoubleClick={(node) => console.log('Double clicked:', node)}
              height={height - 120}
              width={window.innerWidth - 64}
            />
          )}

          {viewMode === 'analytics' && (
            <div style={{ height: height - 120, overflow: 'auto' }}>
              {isLoadingAnalytics ? (
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center', 
                  height: '200px',
                  color: '#666'
                }}>
                  Loading analytics...
                </div>
              ) : analytics ? (
                <div>
                  {/* Summary stats */}
                  <div style={{ 
                    display: 'grid', 
                    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
                    gap: '16px',
                    marginBottom: '24px'
                  }}>
                    <div style={{ 
                      padding: '16px', 
                      backgroundColor: '#f8f9fa', 
                      borderRadius: '8px',
                      textAlign: 'center'
                    }}>
                      <h3 style={{ margin: '0 0 8px 0', color: '#2196F3' }}>
                        {analytics.total_memories.toLocaleString()}
                      </h3>
                      <p style={{ margin: 0, color: '#666' }}>Total Memories</p>
                    </div>
                    <div style={{ 
                      padding: '16px', 
                      backgroundColor: '#f8f9fa', 
                      borderRadius: '8px',
                      textAlign: 'center'
                    }}>
                      <h3 style={{ margin: '0 0 8px 0', color: '#4CAF50' }}>
                        {(analytics.relationship_stats.connected_memories || 0).toLocaleString()}
                      </h3>
                      <p style={{ margin: 0, color: '#666' }}>Connected Memories</p>
                    </div>
                    <div style={{ 
                      padding: '16px', 
                      backgroundColor: '#f8f9fa', 
                      borderRadius: '8px',
                      textAlign: 'center'
                    }}>
                      <h3 style={{ margin: '0 0 8px 0', color: '#FF9800' }}>
                        {Object.keys(analytics.memories_by_cluster).length.toLocaleString()}
                      </h3>
                      <p style={{ margin: 0, color: '#666' }}>Clusters</p>
                    </div>
                  </div>

                  {/* Charts */}
                  <div style={{ 
                    display: 'grid', 
                    gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', 
                    gap: '24px'
                  }}>
                    {analyticsCharts.map((chartConfig, index) => (
                      <div key={index} style={{ 
                        backgroundColor: 'white', 
                        borderRadius: '8px', 
                        padding: '16px',
                        border: '1px solid #ddd'
                      }}>
                        <h3 style={{ marginTop: 0, marginBottom: '16px' }}>
                          {chartConfig.title}
                        </h3>
                        <div style={{ height: '300px' }}>
                          <AgCharts options={chartConfig as AgChartOptions} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center', 
                  height: '200px',
                  color: '#666'
                }}>
                  {error ? 'Error loading analytics' : 'No analytics data available'}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Memory Editor Modal */}
        <MemoryEditor
          memory={selectedMemory}
          onSave={handleMemorySave}
          onCancel={handleEditorCancel}
          onDelete={handleMemoryDelete}
          isOpen={isEditorOpen}
          userId={userId}
          tenantId={tenantId}
        />
      </div>
    </CopilotKit>
  );
};

export default MemoryInterface;
