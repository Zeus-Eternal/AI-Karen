/**
 * Memory Network Graph Component
 * Interactive network visualization using D3.js for memory relationships
 */

import React, { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import * as d3 from 'd3';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { 
  ZoomIn, 
  ZoomOut, 
  RotateCcw, 
  Search, 
  Filter,
  Maximize2,
  Minimize2,
  Play,
  Pause,
  Settings
} from 'lucide-react';
import { getMemoryService } from '@/services/memoryService';
import type { 
  MemoryNetworkNode as BaseMemoryNetworkNode,
  MemoryNetworkEdge,
  MemoryNetworkData,
  MemoryCluster,
  NetworkStatistics,
  MemoryNetworkProps
} from '@/types/memory';

// Extend the base node type to be compatible with D3 simulation
type MemoryNetworkNode = BaseMemoryNetworkNode & d3.SimulationNodeDatum;

interface NetworkConfig {
  nodeSize: [number, number]; // [min, max]
  linkDistance: number;
  linkStrength: number;
  chargeStrength: number;
  clusterPadding: number;
  showLabels: boolean;
  showClusters: boolean;
  animationSpeed: number;
  colorScheme: 'default' | 'confidence' | 'type' | 'cluster';
}

interface TooltipData {
  node: MemoryNetworkNode;
  x: number;
  y: number;
}

interface FilterOptions {
  minConfidence: number;
  maxConfidence: number;
  selectedTypes: string[];
  selectedClusters: string[];
  minConnections: number;
  searchQuery: string;
}

export const MemoryNetworkGraph: React.FC<MemoryNetworkProps> = ({
  userId,
  tenantId,
  onNodeSelect,
  onNodeDoubleClick,
  onClusterSelect,
  height = 600,
  width = 800
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const simulationRef = useRef<d3.Simulation<MemoryNetworkNode, MemoryNetworkEdge> | null>(null);
  
  const [networkData, setNetworkData] = useState<MemoryNetworkData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<MemoryNetworkNode | null>(null);
  const [tooltip, setTooltip] = useState<TooltipData | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isPlaying, setIsPlaying] = useState(true);
  const [showControls, setShowControls] = useState(true);
  
  const [config, setConfig] = useState<NetworkConfig>({
    nodeSize: [5, 20],
    linkDistance: 50,
    linkStrength: 0.1,
    chargeStrength: -100,
    clusterPadding: 20,
    showLabels: true,
    showClusters: true,
    animationSpeed: 1,
    colorScheme: 'cluster'
  });

  const [filters, setFilters] = useState<FilterOptions>({
    minConfidence: 0,
    maxConfidence: 1,
    selectedTypes: [],
    selectedClusters: [],
    minConnections: 0,
    searchQuery: ''
  });

  const memoryService = useMemo(() => getMemoryService(), []);

  // Color scales for different visualization modes
  const colorScales = useMemo(() => ({
    default: d3.scaleOrdinal(d3.schemeCategory10),
    confidence: d3.scaleSequential(d3.interpolateViridis).domain([0, 1]),
    type: d3.scaleOrdinal(d3.schemeSet2),
    cluster: d3.scaleOrdinal(d3.schemeTableau10)
  }), []);

  // Load network data
  const loadNetworkData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Get memory stats to generate network data
      const stats = await memoryService.getMemoryStats(userId);
      
      // Generate mock network data based on memory stats
      const nodes: MemoryNetworkNode[] = [];
      const edges: MemoryNetworkEdge[] = [];
      const clusters: MemoryCluster[] = [];

      // Create nodes from memory data
      const nodeCount = Math.min(stats.totalMemories, 100); // Limit for performance
      for (let i = 0; i < nodeCount; i++) {
        const types = ['fact', 'preference', 'context'];
        const clusterNames = Object.keys(stats.memoriesByTag);
        const type = types[i % types.length];
        const cluster = clusterNames[i % clusterNames.length] || 'general';
        
        nodes.push({
          id: `node-${i}`,
          label: `Memory ${i + 1}`,
          content: `Sample memory content for node ${i + 1}`,
          type,
          confidence: 0.5 + Math.random() * 0.5,
          cluster,
          size: 5 + Math.random() * 15,
          color: colorScales.cluster(cluster),
          metadata: {
            created: new Date(Date.now() - Math.random() * 86400000 * 30),
            accessed: Math.floor(Math.random() * 100)
          },
          tags: [`tag-${i % 5}`, `category-${i % 3}`]
        });
      }

      // Create edges between related nodes
      const edgeCount = Math.floor(nodeCount * 1.5);
      const edgeSet = new Set<string>();
      
      for (let i = 0; i < edgeCount; i++) {
        const sourceIdx = Math.floor(Math.random() * nodeCount);
        const targetIdx = Math.floor(Math.random() * nodeCount);
        
        if (sourceIdx !== targetIdx) {
          const edgeId = `${sourceIdx}-${targetIdx}`;
          const reverseEdgeId = `${targetIdx}-${sourceIdx}`;
          
          if (!edgeSet.has(edgeId) && !edgeSet.has(reverseEdgeId)) {
            edgeSet.add(edgeId);
            
            const edgeTypes = ['semantic', 'temporal', 'explicit', 'inferred'];
            edges.push({
              id: edgeId,
              source: nodes[sourceIdx].id,
              target: nodes[targetIdx].id,
              weight: Math.random(),
              type: edgeTypes[Math.floor(Math.random() * edgeTypes.length)] as any,
              confidence: 0.3 + Math.random() * 0.7
            });
          }
        }
      }

      // Create clusters
      const clusterNames = [...new Set(nodes.map(n => n.cluster))];
      clusterNames.forEach((clusterName, index) => {
        const clusterNodes = nodes.filter(n => n.cluster === clusterName);
        clusters.push({
          id: `cluster-${index}`,
          name: clusterName,
          nodes: clusterNodes.map(n => n.id),
          centroid: { x: 0, y: 0 }, // Will be calculated during layout
          color: colorScales.cluster(clusterName),
          size: clusterNodes.length,
          density: clusterNodes.length / nodeCount,
          coherence: 0.7 + Math.random() * 0.3,
          topics: [`topic-${index}-1`, `topic-${index}-2`]
        });
      });

      // Calculate network statistics
      const statistics: NetworkStatistics = {
        nodeCount: nodes.length,
        edgeCount: edges.length,
        clusterCount: clusters.length,
        averageConnectivity: edges.length / nodes.length,
        networkDensity: (2 * edges.length) / (nodes.length * (nodes.length - 1)),
        modularity: 0.3 + Math.random() * 0.4,
        smallWorldCoefficient: 0.1 + Math.random() * 0.2
      };

      const networkData: MemoryNetworkData = {
        nodes,
        edges,
        clusters,
        statistics
      };

      setNetworkData(networkData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load network data';
      setError(errorMessage);
      console.error('Network data loading error:', err);
    } finally {
      setLoading(false);
    }
  }, [userId, memoryService, colorScales]);

  // Filter network data based on current filters
  const filteredData = useMemo(() => {
    if (!networkData) return null;

    let filteredNodes = networkData.nodes.filter(node => {
      // Confidence filter
      if (node.confidence < filters.minConfidence || node.confidence > filters.maxConfidence) {
        return false;
      }

      // Type filter
      if (filters.selectedTypes.length > 0 && !filters.selectedTypes.includes(node.type)) {
        return false;
      }

      // Cluster filter
      if (filters.selectedClusters.length > 0 && !filters.selectedClusters.includes(node.cluster)) {
        return false;
      }

      // Search filter
      if (filters.searchQuery) {
        const query = filters.searchQuery.toLowerCase();
        if (!node.label.toLowerCase().includes(query) && 
            !node.content.toLowerCase().includes(query) &&
            !node.tags.some(tag => tag.toLowerCase().includes(query))) {
          return false;
        }
      }

      return true;
    });

    // Filter edges to only include those between visible nodes
    const nodeIds = new Set(filteredNodes.map(n => n.id));
    const filteredEdges = networkData.edges.filter(edge => 
      nodeIds.has(edge.source as string) && nodeIds.has(edge.target as string)
    );

    // Apply minimum connections filter
    if (filters.minConnections > 0) {
      const connectionCounts = new Map<string, number>();
      filteredEdges.forEach(edge => {
        const source = edge.source as string;
        const target = edge.target as string;
        connectionCounts.set(source, (connectionCounts.get(source) || 0) + 1);
        connectionCounts.set(target, (connectionCounts.get(target) || 0) + 1);
      });

      filteredNodes = filteredNodes.filter(node => 
        (connectionCounts.get(node.id) || 0) >= filters.minConnections
      );
    }

    return {
      ...networkData,
      nodes: filteredNodes,
      edges: filteredEdges
    };
  }, [networkData, filters]);

  // Initialize and update D3 visualization
  const updateVisualization = useCallback(() => {
    if (!filteredData || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    const container = svg.select('.network-container');
    
    // Clear existing elements
    container.selectAll('*').remove();

    // Set up zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 10])
      .on('zoom', (event) => {
        container.attr('transform', event.transform);
      });

    svg.call(zoom);

    // Create simulation
    const simulation = d3.forceSimulation<MemoryNetworkNode>(filteredData.nodes)
      .force('link', d3.forceLink<MemoryNetworkNode, MemoryNetworkEdge>(filteredData.edges)
        .id(d => d.id)
        .distance(config.linkDistance)
        .strength(config.linkStrength))
      .force('charge', d3.forceManyBody().strength(config.chargeStrength))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(d => (d as MemoryNetworkNode).size + 2));

    simulationRef.current = simulation;

    // Create cluster backgrounds if enabled
    if (config.showClusters) {
      const clusterGroups = container.selectAll('.cluster')
        .data(filteredData.clusters)
        .enter()
        .append('g')
        .attr('class', 'cluster');

      clusterGroups.append('circle')
        .attr('class', 'cluster-background')
        .attr('r', d => Math.sqrt(d.size) * 20)
        .attr('fill', d => d.color)
        .attr('fill-opacity', 0.1)
        .attr('stroke', d => d.color)
        .attr('stroke-width', 2)
        .attr('stroke-dasharray', '5,5');
    }

    // Create links
    const links = container.selectAll('.link')
      .data(filteredData.edges)
      .enter()
      .append('line')
      .attr('class', 'link')
      .attr('stroke', d => {
        const colors = {
          semantic: '#2196F3',
          temporal: '#4CAF50',
          explicit: '#FF9800',
          inferred: '#9C27B0'
        };
        return colors[d.type] || '#999';
      })
      .attr('stroke-width', d => Math.sqrt(d.weight) * 2)
      .attr('stroke-opacity', d => d.confidence * 0.8);

    // Create nodes
    const nodes = container.selectAll('.node')
      .data(filteredData.nodes)
      .enter()
      .append('g')
      .attr('class', 'node')
      .style('cursor', 'pointer');

    // Node circles
    nodes.append('circle')
      .attr('r', d => d.size)
      .attr('fill', d => {
        switch (config.colorScheme) {
          case 'confidence':
            return colorScales.confidence(d.confidence);
          case 'type':
            return colorScales.type(d.type);
          case 'cluster':
            return colorScales.cluster(d.cluster);
          default:
            return colorScales.default(d.id);
        }
      })
      .attr('stroke', '#fff')
      .attr('stroke-width', 2);

    // Node labels
    if (config.showLabels) {
      nodes.append('text')
        .attr('class', 'node-label')
        .attr('dx', d => d.size + 5)
        .attr('dy', '.35em')
        .style('font-size', '10px')
        .style('fill', '#333')
        .text(d => d.label);
    }

    // Node interactions
    nodes
      .on('mouseover', (event, d) => {
        setTooltip({
          node: d,
          x: event.pageX,
          y: event.pageY
        });
        
        // Highlight connected nodes and edges
        const connectedNodeIds = new Set<string>();
        links
          .style('stroke-opacity', edge => {
            const sourceId = typeof edge.source === 'string' ? edge.source : (edge.source as MemoryNetworkNode).id;
            const targetId = typeof edge.target === 'string' ? edge.target : (edge.target as MemoryNetworkNode).id;
            
            if (sourceId === d.id || targetId === d.id) {
              connectedNodeIds.add(sourceId);
              connectedNodeIds.add(targetId);
              return 1;
            }
            return 0.1;
          });
        
        nodes.select('circle')
          .style('opacity', node => connectedNodeIds.has(node.id) || node.id === d.id ? 1 : 0.3);
      })
      .on('mouseout', () => {
        setTooltip(null);
        links.style('stroke-opacity', d => d.confidence * 0.8);
        nodes.select('circle').style('opacity', 1);
      })
      .on('click', (event, d) => {
        setSelectedNode(d);
        onNodeSelect?.(d);
      })
      .on('dblclick', (event, d) => {
        onNodeDoubleClick?.(d);
      });

    // Drag behavior
    const drag = d3.drag<SVGGElement, MemoryNetworkNode>()
      .on('start', (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      })
      .on('drag', (event, d) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on('end', (event, d) => {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      });

    nodes.call(drag);

    // Update positions on simulation tick
    simulation.on('tick', () => {
      links
        .attr('x1', d => {
          const source = d.source as any;
          return typeof source === 'object' ? source.x : 0;
        })
        .attr('y1', d => {
          const source = d.source as any;
          return typeof source === 'object' ? source.y : 0;
        })
        .attr('x2', d => {
          const target = d.target as any;
          return typeof target === 'object' ? target.x : 0;
        })
        .attr('y2', d => {
          const target = d.target as any;
          return typeof target === 'object' ? target.y : 0;
        });

      nodes.attr('transform', d => `translate(${(d as any).x || 0},${(d as any).y || 0})`);

      // Update cluster positions
      if (config.showClusters) {
        filteredData.clusters.forEach(cluster => {
          const clusterNodes = filteredData.nodes.filter(n => cluster.nodes.includes(n.id));
          if (clusterNodes.length > 0) {
            cluster.centroid.x = d3.mean(clusterNodes, n => (n as any).x || 0) || 0;
            cluster.centroid.y = d3.mean(clusterNodes, n => (n as any).y || 0) || 0;
          }
        });

        container.selectAll('.cluster circle')
          .attr('cx', d => (d as MemoryCluster).centroid.x)
          .attr('cy', d => (d as MemoryCluster).centroid.y);
      }
    });

    // Control simulation playback
    if (!isPlaying) {
      simulation.stop();
    }

  }, [filteredData, config, width, height, colorScales, isPlaying, onNodeSelect, onNodeDoubleClick]);

  // Load data on mount
  useEffect(() => {
    loadNetworkData();
  }, [loadNetworkData]);

  // Update visualization when data or config changes
  useEffect(() => {
    updateVisualization();
  }, [updateVisualization]);

  // Cleanup simulation on unmount
  useEffect(() => {
    return () => {
      if (simulationRef.current) {
        simulationRef.current.stop();
      }
    };
  }, []);

  // Control functions
  const handleZoomIn = useCallback(() => {
    if (svgRef.current) {
      d3.select(svgRef.current).transition().call(
        d3.zoom<SVGSVGElement, unknown>().scaleBy as any, 1.5
      );
    }
  }, []);

  const handleZoomOut = useCallback(() => {
    if (svgRef.current) {
      d3.select(svgRef.current).transition().call(
        d3.zoom<SVGSVGElement, unknown>().scaleBy as any, 1 / 1.5
      );
    }
  }, []);

  const handleReset = useCallback(() => {
    if (svgRef.current) {
      d3.select(svgRef.current).transition().call(
        d3.zoom<SVGSVGElement, unknown>().transform as any,
        d3.zoomIdentity
      );
    }
    if (simulationRef.current) {
      simulationRef.current.alpha(1).restart();
    }
  }, []);

  const togglePlayPause = useCallback(() => {
    setIsPlaying(prev => {
      const newPlaying = !prev;
      if (simulationRef.current) {
        if (newPlaying) {
          simulationRef.current.alpha(0.3).restart();
        } else {
          simulationRef.current.stop();
        }
      }
      return newPlaying;
    });
  }, []);

  const toggleFullscreen = useCallback(() => {
    setIsFullscreen(prev => !prev);
  }, []);

  if (error) {
    return (
      <Card className="p-6">
        <div className="text-center">
          <div className="text-red-600 mb-4">
            <Settings className="w-12 h-12 mx-auto mb-2" />
            <h3 className="text-lg font-semibold">Network Error</h3>
          </div>
          <p className="text-gray-600 mb-4">{error}</p>
          <Button onClick={loadNetworkData} variant="outline">
            Retry
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <div 
      ref={containerRef}
      className={`relative ${isFullscreen ? 'fixed inset-0 z-50 bg-white' : ''}`}
      style={{ height: `${height}px`, width: `${width}px` }}
    >
      {/* Controls */}
      {showControls && (
        <div className="absolute top-4 left-4 z-10 space-y-2">
          <Card className="p-2">
            <div className="flex space-x-1">
              <Button size="sm" variant="outline" onClick={handleZoomIn}>
                <ZoomIn className="w-4 h-4" />
              </Button>
              <Button size="sm" variant="outline" onClick={handleZoomOut}>
                <ZoomOut className="w-4 h-4" />
              </Button>
              <Button size="sm" variant="outline" onClick={handleReset}>
                <RotateCcw className="w-4 h-4" />
              </Button>
              <Button size="sm" variant="outline" onClick={togglePlayPause}>
                {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              </Button>
              <Button size="sm" variant="outline" onClick={toggleFullscreen}>
                {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
              </Button>
            </div>
          </Card>

          {/* Search and Filter */}
          <Card className="p-3 w-64">
            <div className="space-y-2">
              <div className="relative">
                <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  type="text"
                  placeholder="Search nodes..."
                  value={filters.searchQuery}
                  onChange={(e) => setFilters(prev => ({ ...prev, searchQuery: e.target.value }))}
                  className="pl-8 text-sm"
                />
              </div>
              
              <div className="flex items-center space-x-2">
                <label className="text-xs text-gray-600">Min Confidence:</label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={filters.minConfidence}
                  onChange={(e) => setFilters(prev => ({ 
                    ...prev, 
                    minConfidence: parseFloat(e.target.value) 
                  }))}
                  className="flex-1"
                />
                <span className="text-xs text-gray-600 w-8">
                  {filters.minConfidence.toFixed(1)}
                </span>
              </div>

              <div className="flex items-center space-x-2">
                <label className="text-xs text-gray-600">Color by:</label>
                <select
                  value={config.colorScheme}
                  onChange={(e) => setConfig(prev => ({ 
                    ...prev, 
                    colorScheme: e.target.value as any 
                  }))}
                  className="flex-1 text-xs border rounded px-1 py-1"
                >
                  <option value="cluster">Cluster</option>
                  <option value="type">Type</option>
                  <option value="confidence">Confidence</option>
                  <option value="default">Default</option>
                </select>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Statistics */}
      {networkData && (
        <div className="absolute top-4 right-4 z-10">
          <Card className="p-3">
            <div className="text-xs space-y-1">
              <div className="font-semibold">Network Statistics</div>
              <div>Nodes: {filteredData?.nodes.length || 0} / {networkData.statistics.nodeCount}</div>
              <div>Edges: {filteredData?.edges.length || 0} / {networkData.statistics.edgeCount}</div>
              <div>Clusters: {networkData.statistics.clusterCount}</div>
              <div>Density: {(networkData.statistics.networkDensity * 100).toFixed(1)}%</div>
            </div>
          </Card>
        </div>
      )}

      {/* Main SVG */}
      <svg
        ref={svgRef}
        width={width}
        height={height}
        className="border rounded"
        style={{ background: '#fafafa' }}
      >
        <defs>
          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="7"
            refX="9"
            refY="3.5"
            orient="auto"
          >
            <polygon
              points="0 0, 10 3.5, 0 7"
              fill="#999"
            />
          </marker>
        </defs>
        <g className="network-container" />
      </svg>

      {/* Loading overlay */}
      {loading && (
        <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
            <div className="text-sm text-gray-600">Loading network...</div>
          </div>
        </div>
      )}

      {/* Tooltip */}
      {tooltip && (
        <div
          className="absolute z-20 bg-black text-white text-xs rounded p-2 pointer-events-none max-w-xs"
          style={{
            left: tooltip.x + 10,
            top: tooltip.y - 10,
            transform: 'translateY(-100%)'
          }}
        >
          <div className="font-semibold">{tooltip.node.label}</div>
          <div className="text-gray-300">Type: {tooltip.node.type}</div>
          <div className="text-gray-300">Cluster: {tooltip.node.cluster}</div>
          <div className="text-gray-300">
            Confidence: {(tooltip.node.confidence * 100).toFixed(0)}%
          </div>
          <div className="text-gray-300 mt-1 line-clamp-2">
            {tooltip.node.content}
          </div>
          <div className="flex flex-wrap gap-1 mt-1">
            {tooltip.node.tags.slice(0, 3).map(tag => (
              <Badge key={tag} variant="secondary" className="text-xs">
                {tag}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Selected node details */}
      {selectedNode && (
        <div className="absolute bottom-4 left-4 z-10">
          <Card className="p-3 max-w-sm">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="font-semibold text-sm">{selectedNode.label}</h4>
                <button
                  onClick={() => setSelectedNode(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>
              <div className="text-xs text-gray-600">
                <div>Type: <Badge variant="outline" className="text-xs">{selectedNode.type}</Badge></div>
                <div>Cluster: <Badge variant="outline" className="text-xs">{selectedNode.cluster}</Badge></div>
                <div>Confidence: {(selectedNode.confidence * 100).toFixed(0)}%</div>
              </div>
              <div className="text-xs">
                {selectedNode.content}
              </div>
              <div className="flex flex-wrap gap-1">
                {selectedNode.tags.map(tag => (
                  <Badge key={tag} variant="secondary" className="text-xs">
                    {tag}
                  </Badge>
                ))}
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};

export default MemoryNetworkGraph;