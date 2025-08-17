/**
 * AG-UI Memory Network Visualization Component
 * Displays memory relationships as an interactive network graph
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { AgChartsReact } from 'ag-charts-react';
import { AgChartOptions } from 'ag-charts-community';

interface MemoryNetworkNode {
  id: string;
  label: string;
  type: string;
  confidence: number;
  cluster: string;
  size: number;
  color: string;
}

interface MemoryNetworkEdge {
  source: string;
  target: string;
  weight: number;
  type: string;
  label: string;
}

interface MemoryNetworkData {
  nodes: MemoryNetworkNode[];
  edges: MemoryNetworkEdge[];
}

interface MemoryNetworkVisualizationProps {
  userId: string;
  tenantId?: string;
  maxNodes?: number;
  onNodeSelect?: (node: MemoryNetworkNode) => void;
  onNodeDoubleClick?: (node: MemoryNetworkNode) => void;
  height?: number;
  width?: number;
}

// Custom network chart component using AG-Charts
const NetworkChart: React.FC<{
  data: MemoryNetworkData;
  onNodeSelect?: (node: MemoryNetworkNode) => void;
  onNodeDoubleClick?: (node: MemoryNetworkNode) => void;
  height: number;
  width: number;
}> = ({ data, onNodeSelect, onNodeDoubleClick, height, width }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  // Simple force-directed layout calculation
  const calculateLayout = useCallback((nodes: MemoryNetworkNode[], edges: MemoryNetworkEdge[]) => {
    const positions = new Map<string, { x: number; y: number }>();
    
    // Initialize random positions
    nodes.forEach(node => {
      positions.set(node.id, {
        x: Math.random() * (width - 100) + 50,
        y: Math.random() * (height - 100) + 50
      });
    });

    // Simple force simulation (simplified)
    for (let iteration = 0; iteration < 50; iteration++) {
      const forces = new Map<string, { fx: number; fy: number }>();
      
      // Initialize forces
      nodes.forEach(node => {
        forces.set(node.id, { fx: 0, fy: 0 });
      });

      // Repulsion between all nodes
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const node1 = nodes[i];
          const node2 = nodes[j];
          const pos1 = positions.get(node1.id)!;
          const pos2 = positions.get(node2.id)!;
          
          const dx = pos1.x - pos2.x;
          const dy = pos1.y - pos2.y;
          const distance = Math.sqrt(dx * dx + dy * dy) || 1;
          
          const repulsion = 1000 / (distance * distance);
          const fx = (dx / distance) * repulsion;
          const fy = (dy / distance) * repulsion;
          
          const force1 = forces.get(node1.id)!;
          const force2 = forces.get(node2.id)!;
          
          force1.fx += fx;
          force1.fy += fy;
          force2.fx -= fx;
          force2.fy -= fy;
        }
      }

      // Attraction along edges
      edges.forEach(edge => {
        const pos1 = positions.get(edge.source);
        const pos2 = positions.get(edge.target);
        
        if (pos1 && pos2) {
          const dx = pos2.x - pos1.x;
          const dy = pos2.y - pos1.y;
          const distance = Math.sqrt(dx * dx + dy * dy) || 1;
          
          const attraction = distance * 0.01 * edge.weight;
          const fx = (dx / distance) * attraction;
          const fy = (dy / distance) * attraction;
          
          const force1 = forces.get(edge.source);
          const force2 = forces.get(edge.target);
          
          if (force1) {
            force1.fx += fx;
            force1.fy += fy;
          }
          if (force2) {
            force2.fx -= fx;
            force2.fy -= fy;
          }
        }
      });

      // Apply forces
      nodes.forEach(node => {
        const pos = positions.get(node.id)!;
        const force = forces.get(node.id)!;
        
        pos.x += force.fx * 0.1;
        pos.y += force.fy * 0.1;
        
        // Keep within bounds
        pos.x = Math.max(node.size, Math.min(width - node.size, pos.x));
        pos.y = Math.max(node.size, Math.min(height - node.size, pos.y));
      });
    }

    return positions;
  }, [width, height]);

  // Draw the network
  const drawNetwork = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    if (data.nodes.length === 0) {
      // Draw empty state
      ctx.fillStyle = '#666';
      ctx.font = '16px Arial';
      ctx.textAlign = 'center';
      ctx.fillText('No memory relationships to display', width / 2, height / 2);
      return;
    }

    const positions = calculateLayout(data.nodes, data.edges);

    // Draw edges first
    ctx.strokeStyle = '#ccc';
    ctx.lineWidth = 1;
    data.edges.forEach(edge => {
      const pos1 = positions.get(edge.source);
      const pos2 = positions.get(edge.target);
      
      if (pos1 && pos2) {
        ctx.beginPath();
        ctx.moveTo(pos1.x, pos1.y);
        ctx.lineTo(pos2.x, pos2.y);
        ctx.stroke();
        
        // Draw edge label
        const midX = (pos1.x + pos2.x) / 2;
        const midY = (pos1.y + pos2.y) / 2;
        ctx.fillStyle = '#999';
        ctx.font = '10px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(edge.label, midX, midY);
      }
    });

    // Draw nodes
    data.nodes.forEach(node => {
      const pos = positions.get(node.id);
      if (!pos) return;

      // Draw node circle
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, node.size, 0, 2 * Math.PI);
      ctx.fillStyle = selectedNode === node.id ? '#ff6b6b' : node.color;
      ctx.fill();
      
      // Draw node border
      ctx.strokeStyle = selectedNode === node.id ? '#ff0000' : '#333';
      ctx.lineWidth = selectedNode === node.id ? 3 : 1;
      ctx.stroke();

      // Draw node label
      ctx.fillStyle = '#333';
      ctx.font = '12px Arial';
      ctx.textAlign = 'center';
      ctx.fillText(node.label, pos.x, pos.y + node.size + 15);
      
      // Draw confidence indicator
      ctx.fillStyle = '#666';
      ctx.font = '10px Arial';
      ctx.fillText(`${Math.round(node.confidence * 100)}%`, pos.x, pos.y + node.size + 28);
    });
  }, [data, selectedNode, calculateLayout, width, height]);

  // Handle canvas clicks
  const handleCanvasClick = useCallback((event: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    const positions = calculateLayout(data.nodes, data.edges);
    
    // Find clicked node
    for (const node of data.nodes) {
      const pos = positions.get(node.id);
      if (!pos) continue;

      const distance = Math.sqrt((x - pos.x) ** 2 + (y - pos.y) ** 2);
      if (distance <= node.size) {
        setSelectedNode(node.id);
        if (onNodeSelect) {
          onNodeSelect(node);
        }
        return;
      }
    }

    // No node clicked, clear selection
    setSelectedNode(null);
  }, [data, calculateLayout, onNodeSelect]);

  const handleCanvasDoubleClick = useCallback((event: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    const positions = calculateLayout(data.nodes, data.edges);
    
    // Find double-clicked node
    for (const node of data.nodes) {
      const pos = positions.get(node.id);
      if (!pos) continue;

      const distance = Math.sqrt((x - pos.x) ** 2 + (y - pos.y) ** 2);
      if (distance <= node.size) {
        if (onNodeDoubleClick) {
          onNodeDoubleClick(node);
        }
        return;
      }
    }
  }, [data, calculateLayout, onNodeDoubleClick]);

  // Redraw when data changes
  useEffect(() => {
    drawNetwork();
  }, [drawNetwork]);

  return (
    <canvas
      ref={canvasRef}
      width={width}
      height={height}
      onClick={handleCanvasClick}
      onDoubleClick={handleCanvasDoubleClick}
      style={{ 
        border: '1px solid #ddd', 
        borderRadius: '4px',
        cursor: 'pointer'
      }}
    />
  );
};

export const MemoryNetworkVisualization: React.FC<MemoryNetworkVisualizationProps> = ({
  userId,
  tenantId,
  maxNodes = 50,
  onNodeSelect,
  onNodeDoubleClick,
  height = 500,
  width = 800
}) => {
  const [networkData, setNetworkData] = useState<MemoryNetworkData>({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCluster, setSelectedCluster] = useState<string | null>(null);

  // Fetch network data
  const fetchNetworkData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/memory/network', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          tenant_id: tenantId,
          max_nodes: maxNodes
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setNetworkData(data);
    } catch (err) {
      console.error('Error fetching network data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load network data');
    } finally {
      setLoading(false);
    }
  }, [userId, tenantId, maxNodes]);

  // Load data on mount
  useEffect(() => {
    fetchNetworkData();
  }, [fetchNetworkData]);

  // Filter data by cluster
  const filteredData = React.useMemo(() => {
    if (!networkData?.nodes || !networkData?.edges) return { nodes: [], edges: [] };
    if (!selectedCluster) return networkData;

    const filteredNodes = networkData.nodes.filter(node => node.cluster === selectedCluster);
    const nodeIds = new Set(filteredNodes.map(node => node.id));
    const filteredEdges = networkData.edges.filter(edge => 
      nodeIds.has(edge.source) && nodeIds.has(edge.target)
    );

    return { nodes: filteredNodes, edges: filteredEdges };
  }, [networkData, selectedCluster]);

  // Get unique clusters for filter
  const clusters = React.useMemo(() => {
    if (!networkData?.nodes) return [];
    const clusterSet = new Set(networkData.nodes.map(node => node.cluster));
    return Array.from(clusterSet).sort();
  }, [networkData?.nodes]);

  if (error) {
    return (
      <div className="network-error" style={{ 
        padding: '20px', 
        textAlign: 'center', 
        color: '#f44336',
        border: '1px solid #f44336',
        borderRadius: '4px',
        backgroundColor: '#ffebee'
      }}>
        <h3>Error Loading Network Data</h3>
        <p>{error}</p>
        <button 
          onClick={fetchNetworkData}
          style={{
            padding: '8px 16px',
            backgroundColor: '#f44336',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="memory-network-container">
      {/* Controls */}
      <div style={{ 
        marginBottom: '16px', 
        display: 'flex', 
        alignItems: 'center', 
        gap: '16px',
        padding: '12px',
        backgroundColor: '#f5f5f5',
        borderRadius: '4px'
      }}>
        <label style={{ fontWeight: 'bold' }}>Filter by Cluster:</label>
        <select
          value={selectedCluster || ''}
          onChange={(e) => setSelectedCluster(e.target.value || null)}
          style={{
            padding: '4px 8px',
            borderRadius: '4px',
            border: '1px solid #ccc'
          }}
        >
          <option value="">All Clusters</option>
          {clusters.map(cluster => (
            <option key={cluster} value={cluster}>
              {cluster.charAt(0).toUpperCase() + cluster.slice(1)}
            </option>
          ))}
        </select>
        
        <div style={{ marginLeft: 'auto', fontSize: '14px', color: '#666' }}>
          Nodes: {filteredData.nodes.length} | Edges: {filteredData.edges.length}
        </div>
        
        <button
          onClick={fetchNetworkData}
          disabled={loading}
          style={{
            padding: '6px 12px',
            backgroundColor: '#2196F3',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.6 : 1
          }}
        >
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      {/* Network Visualization */}
      <div style={{ position: 'relative' }}>
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
            Loading network visualization...
          </div>
        )}
        
        <NetworkChart
          data={filteredData}
          onNodeSelect={onNodeSelect}
          onNodeDoubleClick={onNodeDoubleClick}
          height={height}
          width={width}
        />
      </div>

      {/* Legend */}
      <div style={{ 
        marginTop: '16px', 
        padding: '12px',
        backgroundColor: '#f9f9f9',
        borderRadius: '4px',
        fontSize: '12px'
      }}>
        <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>Legend:</div>
        <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#FF6B6B' }} />
            <span>Technical</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#4ECDC4' }} />
            <span>Personal</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#45B7D1' }} />
            <span>Work</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#96CEB4' }} />
            <span>General</span>
          </div>
          <div style={{ marginLeft: '16px' }}>
            <span>Node size = confidence level</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MemoryNetworkVisualization;