'use client';

import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { AgCharts } from 'ag-charts-react';
import { AgChartOptions } from 'ag-charts-community';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { 
  Network, 
  Brain, 
  Filter, 
  ZoomIn, 
  ZoomOut, 
  RotateCcw,
  Settings,
  Eye,
  EyeOff,
  Maximize2
} from 'lucide-react';
import { useHooks } from '@/contexts/HookContext';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';

export interface MemoryNode {
  id: string;
  label: string;
  type: 'cluster' | 'memory';
  size?: number;
  confidence?: number;
  cluster?: string;
  color?: string;
  x?: number;
  y?: number;
}

export interface MemoryEdge {
  from: string;
  to: string;
  weight: number;
  type?: 'relationship' | 'cluster' | 'semantic';
}

export interface MemoryNetworkData {
  nodes: MemoryNode[];
  edges: MemoryEdge[];
  clusters: string[];
  totalMemories: number;
}

interface MemoryNetworkVisualizationProps {
  data?: MemoryNetworkData;
  onNodeClick?: (node: MemoryNode) => void;
  onEdgeClick?: (edge: MemoryEdge) => void;
  onRefresh?: () => Promise<void>;
  className?: string;
}

type LayoutType = 'force' | 'circular' | 'hierarchical' | 'grid';
type FilterType = 'all' | 'high-confidence' | 'recent' | 'cluster';

export const MemoryNetworkVisualization: React.FC<MemoryNetworkVisualizationProps> = ({
  data,
  onNodeClick,
  onEdgeClick,
  onRefresh,
  className = ''
}) => {
  const { user } = useAuth();
  const { triggerHooks, registerChartHook } = useHooks();
  const { toast } = useToast();
  
  const [layoutType, setLayoutType] = useState<LayoutType>('force');
  const [filterType, setFilterType] = useState<FilterType>('all');
  const [confidenceThreshold, setConfidenceThreshold] = useState([0.5]);
  const [selectedClusters, setSelectedClusters] = useState<string[]>([]);
  const [showLabels, setShowLabels] = useState(true);
  const [showEdges, setShowEdges] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(1);
  
  const chartRef = useRef<any>(null);

  // Process network data based on filters
  const processedData = useMemo(() => {
    if (!data) return { nodes: [], edges: [] };

    let filteredNodes = [...data.nodes];
    let filteredEdges = [...data.edges];

    // Apply confidence filter
    if (filterType === 'high-confidence') {
      filteredNodes = filteredNodes.filter(node => 
        node.type === 'cluster' || (node.confidence && node.confidence >= confidenceThreshold[0])
      );
    }

    // Apply cluster filter
    if (selectedClusters.length > 0) {
      filteredNodes = filteredNodes.filter(node =>
        node.type === 'cluster' ? selectedClusters.includes(node.label) :
        node.cluster ? selectedClusters.includes(node.cluster) : false
      );
    }

    // Filter edges based on remaining nodes
    const nodeIds = new Set(filteredNodes.map(node => node.id));
    filteredEdges = filteredEdges.filter(edge =>
      nodeIds.has(edge.from) && nodeIds.has(edge.to)
    );

    return { nodes: filteredNodes, edges: filteredEdges };
  }, [data, filterType, confidenceThreshold, selectedClusters]);

  // Generate chart data for AG-Charts network visualization
  const chartData = useMemo(() => {
    const { nodes, edges } = processedData;
    
    // Create scatter plot data for nodes
    const nodeData = nodes.map((node, index) => {
      // Calculate position based on layout type
      let x, y;
      
      switch (layoutType) {
        case 'circular':
          const angle = (index / nodes.length) * 2 * Math.PI;
          const radius = node.type === 'cluster' ? 150 : 100;
          x = Math.cos(angle) * radius;
          y = Math.sin(angle) * radius;
          break;
          
        case 'grid':
          const cols = Math.ceil(Math.sqrt(nodes.length));
          x = (index % cols) * 100;
          y = Math.floor(index / cols) * 100;
          break;
          
        case 'hierarchical':
          x = node.type === 'cluster' ? index * 200 : (index % 3) * 100;
          y = node.type === 'cluster' ? 0 : 150;
          break;
          
        default: // force layout
          x = node.x || Math.random() * 400;
          y = node.y || Math.random() * 400;
      }

      return {
        id: node.id,
        label: node.label,
        type: node.type,
        x,
        y,
        size: node.type === 'cluster' ? (node.size || 10) * 3 : 8,
        confidence: node.confidence || 1,
        cluster: node.cluster,
        color: node.color || (node.type === 'cluster' ? '#3b82f6' : '#10b981')
      };
    });

    return nodeData;
  }, [processedData, layoutType]);

  // Chart options for network visualization
  const chartOptions: AgChartOptions = useMemo(() => {
    return {
      data: chartData,
      theme: 'ag-default',
      background: { fill: 'transparent' },
      padding: { top: 20, right: 20, bottom: 20, left: 20 },
      title: {
        text: `Memory Network (${processedData.nodes.length} nodes, ${processedData.edges.length} connections)`,
        fontSize: 16
      },
      series: [
        {
          type: 'scatter',
          xKey: 'x',
          yKey: 'y',
          sizeKey: 'size',
          labelKey: showLabels ? 'label' : undefined,
          label: {
            enabled: showLabels,
            fontSize: 10,
            color: '#374151'
          },
          marker: {
            shape: 'circle',
            strokeWidth: 2,
            stroke: '#ffffff'
          },
          tooltip: {
            renderer: ({ datum }: any) => ({
              content: `
                <div class="p-2">
                  <div class="font-semibold">${datum.label}</div>
                  <div class="text-sm text-gray-600">Type: ${datum.type}</div>
                  ${datum.confidence ? `<div class="text-sm">Confidence: ${(datum.confidence * 100).toFixed(1)}%</div>` : ''}
                  ${datum.cluster ? `<div class="text-sm">Cluster: ${datum.cluster}</div>` : ''}
                </div>
              `
            })
          }
        } as any
      ],
      axes: [
        {
          type: 'number',
          position: 'bottom',
          title: { enabled: false },
          tick: { enabled: false },
          line: { enabled: false },
          label: { enabled: false }
        },
        {
          type: 'number',
          position: 'left',
          title: { enabled: false },
          tick: { enabled: false },
          line: { enabled: false },
          label: { enabled: false }
        }
      ],
      legend: { enabled: false }
    } as AgChartOptions;
  }, [chartData, processedData, showLabels]);

  // Register network visualization hooks
  useEffect(() => {
    const hookIds: string[] = [];

    hookIds.push(registerChartHook('memoryNetwork', 'dataLoad', async (params) => {
      console.log('Memory network data loaded:', params);
      return { success: true, nodeCount: processedData.nodes.length };
    }));

    hookIds.push(registerChartHook('memoryNetwork', 'nodeClick', async (params) => {
      console.log('Memory network node clicked:', params);
      return { success: true, clickedNode: params };
    }));

    return () => {
      // Cleanup hooks
    };
  }, [registerChartHook, processedData.nodes.length]);

  // Handle chart ready event
  useEffect(() => {
    if (chartRef.current && processedData.nodes.length > 0) {
      handleChartReady();
    }
  }, [chartRef.current, processedData.nodes.length, processedData.edges.length]);

  // Handle chart events
  const handleChartReady = useCallback(async () => {
    await triggerHooks('chart_memoryNetwork_dataLoad', {
      chartId: 'memoryNetwork',
      nodeCount: processedData.nodes.length,
      edgeCount: processedData.edges.length,
      layoutType,
      filterType
    }, { userId: user?.user_id });
  }, [triggerHooks, processedData, layoutType, filterType, user?.user_id]);

  const handleNodeClick = useCallback(async (event: any) => {
    const datum = event.datum;
    if (datum && onNodeClick) {
      const node: MemoryNode = {
        id: datum.id,
        label: datum.label,
        type: datum.type,
        confidence: datum.confidence,
        cluster: datum.cluster
      };
      onNodeClick(node);
      
      await triggerHooks('chart_memoryNetwork_nodeClick', {
        chartId: 'memoryNetwork',
        node: datum
      }, { userId: user?.user_id });
    }
  }, [onNodeClick, triggerHooks, user?.user_id]);

  const handleRefresh = useCallback(async () => {
    if (!onRefresh) return;
    
    try {
      await onRefresh();
      toast({
        title: 'Network Refreshed',
        description: 'Memory network data has been updated successfully.'
      });
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Refresh Failed',
        description: 'Failed to refresh network data. Please try again.'
      });
    }
  }, [onRefresh, toast]);

  const handleZoomIn = () => {
    setZoomLevel(prev => Math.min(prev * 1.2, 3));
  };

  const handleZoomOut = () => {
    setZoomLevel(prev => Math.max(prev / 1.2, 0.3));
  };

  const handleResetView = () => {
    setZoomLevel(1);
    setLayoutType('force');
  };

  const ClusterBadge = ({ cluster, isSelected, onClick }: {
    cluster: string;
    isSelected: boolean;
    onClick: () => void;
  }) => (
    <Badge
      variant={isSelected ? 'default' : 'outline'}
      className="cursor-pointer hover:bg-primary/20 transition-colors"
      onClick={onClick}
    >
      {cluster.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
    </Badge>
  );

  return (
    <Card className={`w-full ${isFullscreen ? 'fixed inset-0 z-50' : ''} ${className}`}>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold flex items-center gap-2">
            <Network className="h-5 w-5" />
            Memory Network Visualization
          </CardTitle>
          
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsFullscreen(!isFullscreen)}
            >
              <Maximize2 className="h-4 w-4" />
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>

        {/* Network Stats */}
        {data && (
          <div className="flex items-center gap-4 mt-4">
            <Badge variant="secondary">
              <Brain className="h-3 w-3 mr-1" />
              {data.totalMemories} Memories
            </Badge>
            <Badge variant="secondary">
              <Network className="h-3 w-3 mr-1" />
              {processedData.nodes.length} Nodes
            </Badge>
            <Badge variant="secondary">
              {processedData.edges.length} Connections
            </Badge>
            <Badge variant="secondary">
              {data.clusters.length} Clusters
            </Badge>
          </div>
        )}

        {/* Cluster Filter */}
        {data && data.clusters.length > 0 && (
          <div className="mt-4">
            <Label className="text-sm font-medium mb-2 block">Filter by Clusters:</Label>
            <div className="flex flex-wrap gap-2">
              {data.clusters.map(cluster => (
                <ClusterBadge
                  key={cluster}
                  cluster={cluster}
                  isSelected={selectedClusters.includes(cluster)}
                  onClick={() => {
                    setSelectedClusters(prev =>
                      prev.includes(cluster)
                        ? prev.filter(c => c !== cluster)
                        : [...prev, cluster]
                    );
                  }}
                />
              ))}
            </div>
          </div>
        )}

        {/* Controls */}
        <div className="flex items-center justify-between mt-4 p-4 bg-muted/50 rounded-lg">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Label htmlFor="layout-select" className="text-sm">Layout:</Label>
              <Select value={layoutType} onValueChange={(value) => setLayoutType(value as LayoutType)}>
                <SelectTrigger className="w-32" id="layout-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="force">Force</SelectItem>
                  <SelectItem value="circular">Circular</SelectItem>
                  <SelectItem value="hierarchical">Hierarchical</SelectItem>
                  <SelectItem value="grid">Grid</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center gap-2">
              <Label htmlFor="filter-select" className="text-sm">Filter:</Label>
              <Select value={filterType} onValueChange={(value) => setFilterType(value as FilterType)}>
                <SelectTrigger className="w-40" id="filter-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Memories</SelectItem>
                  <SelectItem value="high-confidence">High Confidence</SelectItem>
                  <SelectItem value="recent">Recent</SelectItem>
                  <SelectItem value="cluster">By Cluster</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Label htmlFor="confidence-slider" className="text-sm">Min Confidence:</Label>
              <div className="w-24">
                <Slider
                  id="confidence-slider"
                  value={confidenceThreshold}
                  onValueChange={setConfidenceThreshold}
                  max={1}
                  min={0}
                  step={0.1}
                  className="w-full"
                />
              </div>
              <span className="text-xs text-muted-foreground w-8">
                {Math.round(confidenceThreshold[0] * 100)}%
              </span>
            </div>

            <div className="flex items-center gap-2">
              <Switch
                id="show-labels"
                checked={showLabels}
                onCheckedChange={setShowLabels}
              />
              <Label htmlFor="show-labels" className="text-sm">Labels</Label>
            </div>

            <div className="flex items-center gap-2">
              <Switch
                id="show-edges"
                checked={showEdges}
                onCheckedChange={setShowEdges}
              />
              <Label htmlFor="show-edges" className="text-sm">Edges</Label>
            </div>
          </div>
        </div>

        {/* Zoom Controls */}
        <div className="flex items-center gap-2 mt-2">
          <Button variant="outline" size="sm" onClick={handleZoomOut}>
            <ZoomOut className="h-4 w-4" />
          </Button>
          <span className="text-sm text-muted-foreground px-2">
            {Math.round(zoomLevel * 100)}%
          </span>
          <Button variant="outline" size="sm" onClick={handleZoomIn}>
            <ZoomIn className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="sm" onClick={handleResetView}>
            <RotateCcw className="h-4 w-4 mr-2" />
            Reset
          </Button>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        <div 
          className={`w-full ${isFullscreen ? 'h-[calc(100vh-200px)]' : 'h-[600px]'}`}
          style={{ transform: `scale(${zoomLevel})`, transformOrigin: 'center center' }}
        >
          <AgCharts
            ref={chartRef}
            options={chartOptions}
          />
        </div>

        {/* Network Legend */}
        <div className="p-4 border-t bg-muted/30">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded-full bg-blue-500"></div>
                <span className="text-sm">Clusters</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded-full bg-green-500"></div>
                <span className="text-sm">Memories</span>
              </div>
            </div>
            
            <div className="text-sm text-muted-foreground">
              Click nodes to explore • Drag to pan • Scroll to zoom
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
