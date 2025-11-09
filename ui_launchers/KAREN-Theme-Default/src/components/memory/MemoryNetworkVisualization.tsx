"use client";

/**
 * AG-UI Memory Network Visualization Component (Production)
 * Displays memory relationships as an interactive network graph (HTML Canvas)
 */

import React, { useState, useEffect, useCallback, useRef, useMemo } from "react";
import { Button } from "@/components/ui/button";

export interface MemoryNetworkNode {
  id: string;
  label: string;
  type: string;
  confidence: number; // 0..1
  cluster: string;
  size: number; // px radius
  color: string; // fallback color for node
}

export interface MemoryNetworkEdge {
  source: string;
  target: string;
  weight: number; // 0..1 preferred
  type: string;
  label: string;
}

export interface MemoryNetworkData {
  nodes: MemoryNetworkNode[];
  edges: MemoryNetworkEdge[];
}

export interface MemoryNetworkVisualizationProps {
  userId: string;
  tenantId?: string;
  maxNodes?: number;
  onNodeSelect?: (node: MemoryNetworkNode) => void;
  onNodeDoubleClick?: (node: MemoryNetworkNode) => void;
  height?: number;
  width?: number;
}

/** -------------------- Canvas Network -------------------- */

export type XY = { x: number; y: number };

const NetworkChart: React.FC<{
  data: MemoryNetworkData;
  onNodeSelect?: (node: MemoryNetworkNode) => void;
  onNodeDoubleClick?: (node: MemoryNetworkNode) => void;
  height: number;
  width: number;
}> = ({ data, onNodeSelect, onNodeDoubleClick, height, width }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  // Cache layout positions; recompute only when data/size changes
  const positionsRef = useRef<Map<string, XY>>(new Map());

  const PR = typeof window !== "undefined" ? window.devicePixelRatio || 1 : 1;

  // Deterministic-ish random for stable layout per dataset
  const seededRandom = (seedStr: string) => {
    let seed = 0;
    for (let i = 0; i < seedStr.length; i++) seed = (seed * 31 + seedStr.charCodeAt(i)) >>> 0;
    return () => {
      // xorshift32
      seed ^= seed << 13;
      seed ^= seed >>> 17;
      seed ^= seed << 5;
      // 0..1
      return ((seed >>> 0) % 1_000_000) / 1_000_000;
    };
  };

  const calculateLayout = useCallback(
    (nodes: MemoryNetworkNode[], edges: MemoryNetworkEdge[]): Map<string, XY> => {
      const positions = new Map<string, XY>();
      if (nodes.length === 0) return positions;

      const rand = seededRandom(JSON.stringify(nodes.map((n) => n.id)) + "|" + JSON.stringify(edges.map((e) => e.id)));

      // Initialize positions
      nodes.forEach((n) => {
        positions.set(n.id, {
          x: 50 + rand() * Math.max(1, width - 100),
          y: 50 + rand() * Math.max(1, height - 100),
        });
      });

      // Simple force simulation (bounded, few iterations)
      const ITER = Math.min(120, 30 + Math.floor(Math.sqrt(nodes.length) * 20));
      const REPULSION = 1800; // bigger => more spread
      const ATTR_K = 0.015; // spring strength (multiplied by edge.weight)
      const STEP = 0.12; // integrate

      for (let t = 0; t < ITER; t++) {
        const forces = new Map<string, { fx: number; fy: number }>();
        nodes.forEach((n) => forces.set(n.id, { fx: 0, fy: 0 }));

        // Node-node repulsion (O(N^2) but OK for <= few hundred)
        for (let i = 0; i < nodes.length; i++) {
          for (let j = i + 1; j < nodes.length; j++) {
            const a = nodes[i];
            const b = nodes[j];
            const pa = positions.get(a.id)!;
            const pb = positions.get(b.id)!;
            let dx = pa.x - pb.x;
            let dy = pa.y - pb.y;
            let dist = Math.hypot(dx, dy) || 1;
            const minDist = Math.max(a.size, b.size) + 6; // avoid overlap
            if (dist < 1) dist = 1;
            const rep = REPULSION / (dist * dist);
            const fx = (dx / dist) * rep;
            const fy = (dy / dist) * rep;
            const Fa = forces.get(a.id)!;
            const Fb = forces.get(b.id)!;
            Fa.fx += fx;
            Fa.fy += fy;
            Fb.fx -= fx;
            Fb.fy -= fy;

            // Gentle collision push-out if too close
            if (dist < minDist) {
              const push = (minDist - dist) * 0.5;
              const px = (dx / dist) * push;
              const py = (dy / dist) * push;
              Fa.fx += px;
              Fa.fy += py;
              Fb.fx -= px;
              Fb.fy -= py;
            }
          }
        }

        // Edge attraction
        for (const e of edges) {
          const p1 = positions.get(e.source);
          const p2 = positions.get(e.target);
          if (!p1 || !p2) continue;
          const dx = p2.x - p1.x;
          const dy = p2.y - p1.y;
          const dist = Math.hypot(dx, dy) || 1;
          const k = ATTR_K * Math.max(0.1, e.weight || 0.1);
          const fx = (dx / dist) * dist * k;
          const fy = (dy / dist) * dist * k;
          const F1 = forces.get(e.source)!;
          const F2 = forces.get(e.target)!;
          F1.fx += fx;
          F1.fy += fy;
          F2.fx -= fx;
          F2.fy -= fy;
        }

        // Integrate + keep inside bounds
        nodes.forEach((n) => {
          const p = positions.get(n.id)!;
          const F = forces.get(n.id)!;
          p.x = Math.max(n.size, Math.min(width - n.size, p.x + F.fx * STEP));
          p.y = Math.max(n.size, Math.min(height - n.size, p.y + F.fy * STEP));
        });
      }

      return positions;
    },
    [width, height]
  );

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const logicalW = width * PR;
    const logicalH = height * PR;

    // handle HiDPI
    canvas.width = logicalW;
    canvas.height = logicalH;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    ctx.setTransform(PR, 0, 0, PR, 0, 0);

    // Clear
    ctx.clearRect(0, 0, width, height);

    if (data.nodes.length === 0) {
      ctx.fillStyle = "#666";
      ctx.font = "16px system-ui, -apple-system, Segoe UI, Roboto, Arial";
      ctx.textAlign = "center";
      ctx.fillText("No memory relationships to display", width / 2, height / 2);
      return;
    }

    const positions = positionsRef.current;

    // Edges
    ctx.lineWidth = 1;
    data.edges.forEach((e) => {
      const p1 = positions.get(e.source);
      const p2 = positions.get(e.target);
      if (!p1 || !p2) return;
      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.strokeStyle = "rgba(0,0,0,0.15)";
      ctx.stroke();

      // edge label
      const midX = (p1.x + p2.x) / 2;
      const midY = (p1.y + p2.y) / 2;
      ctx.fillStyle = "#999";
      ctx.font = "10px system-ui, -apple-system, Segoe UI, Roboto, Arial";
      ctx.textAlign = "center";
      ctx.fillText(e.label, midX, midY);
    });

    // Nodes
    data.nodes.forEach((n) => {
      const p = positions.get(n.id);
      if (!p) return;

      // node fill/border
      ctx.beginPath();
      ctx.arc(p.x, p.y, n.size, 0, 2 * Math.PI);
      ctx.fillStyle = selectedNodeId === n.id ? "#ff6b6b" : n.color || "#45B7D1";
      ctx.fill();
      ctx.lineWidth = selectedNodeId === n.id ? 3 : 1;
      ctx.strokeStyle = selectedNodeId === n.id ? "#ff0000" : "#333";
      ctx.stroke();

      // label
      ctx.fillStyle = "#333";
      ctx.font = "12px system-ui, -apple-system, Segoe UI, Roboto, Arial";
      ctx.textAlign = "center";
      ctx.fillText(n.label, p.x, p.y + n.size + 14);

      // confidence
      ctx.fillStyle = "#666";
      ctx.font = "10px system-ui, -apple-system, Segoe UI, Roboto, Arial";
      ctx.fillText(`${Math.round(n.confidence * 100)}%`, p.x, p.y + n.size + 26);
    });
  }, [data, selectedNodeId, height, width, PR]);

  // Compute layout when data/size changes
  useEffect(() => {
    positionsRef.current = calculateLayout(data.nodes, data.edges);
    draw();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data, calculateLayout, height, width]);

  // Redraw on selection change
  useEffect(() => {
    draw();
  }, [selectedNodeId, draw]);

  // Hit-test utilities
  const getNodeAt = useCallback(
    (x: number, y: number): MemoryNetworkNode | null => {
      const pos = positionsRef.current;
      for (let i = data.nodes.length - 1; i >= 0; i--) {
        // iterate backwards to prioritize topmost node in draw order
        const n = data.nodes[i];
        const p = pos.get(n.id);
        if (!p) continue;
        const d = Math.hypot(x - p.x, y - p.y);
        if (d <= n.size) return n;
      }
      return null;
    },
    [data.nodes]
  );

  // Events
  const handleCanvasClick = useCallback(
    (event: React.MouseEvent<HTMLCanvasElement>) => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const rect = canvas.getBoundingClientRect();
      const x = (event.clientX - rect.left);
      const y = (event.clientY - rect.top);
      const node = getNodeAt(x, y);
      if (node) {
        setSelectedNodeId(node.id);
        onNodeSelect?.(node);
      } else {
        setSelectedNodeId(null);
      }
    },
    [getNodeAt, onNodeSelect]
  );

  const handleCanvasDoubleClick = useCallback(
    (event: React.MouseEvent<HTMLCanvasElement>) => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const rect = canvas.getBoundingClientRect();
      const x = (event.clientX - rect.left);
      const y = (event.clientY - rect.top);
      const node = getNodeAt(x, y);
      if (node) onNodeDoubleClick?.(node);
    },
    [getNodeAt, onNodeDoubleClick]
  );

  return (
    <canvas
      ref={canvasRef}
      width={width * PR}
      height={height * PR}
      onClick={handleCanvasClick}
      onDoubleClick={handleCanvasDoubleClick}
      style={{
        width,
        height,
        border: "1px solid #ddd",
        borderRadius: 8,
        cursor: "pointer",
        display: "block",
        background: "#fff",
      }}
    />
  );
};

/** -------------------- Container/Fetcher -------------------- */

export const MemoryNetworkVisualization: React.FC<MemoryNetworkVisualizationProps> = ({
  userId,
  tenantId,
  maxNodes = 50,
  onNodeSelect,
  onNodeDoubleClick,
  height = 500,
  width = 800,
}) => {
  const [networkData, setNetworkData] = useState<MemoryNetworkData>({
    nodes: [],
    edges: [],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCluster, setSelectedCluster] = useState<string | null>(null);

  const fetchNetworkData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch("/api/memory/network", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          tenant_id: tenantId,
          max_nodes: maxNodes,
        }),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data: MemoryNetworkData = await response.json();
      setNetworkData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load network data");
      setNetworkData({ nodes: [], edges: [] });
    } finally {
      setLoading(false);
    }
  }, [userId, tenantId, maxNodes]);

  useEffect(() => {
    fetchNetworkData();
  }, [fetchNetworkData]);

  const filteredData = useMemo<MemoryNetworkData>(() => {
    if (!selectedCluster) return networkData;
    const nodes = networkData.nodes.filter((n) => n.cluster === selectedCluster);
    const ids = new Set(nodes.map((n) => n.id));
    const edges = networkData.edges.filter((e) => ids.has(e.source) && ids.has(e.target));
    return { nodes, edges };
  }, [networkData, selectedCluster]);

  const clusters = useMemo(() => {
    const set = new Set(networkData.nodes.map((n) => n.cluster));
    return Array.from(set).sort();
  }, [networkData.nodes]);

  if (error) {
    return (
      <div
        className="network-error"
        style={{
          padding: 20,
          textAlign: "center",
          color: "#f44336",
          border: "1px solid #f44336",
          borderRadius: 8,
          backgroundColor: "#ffebee",
        }}
      >
        <h3>Error Loading Network Data</h3>
        <p style={{ marginBottom: 12 }}>{error}</p>
        <Button onClick={fetchNetworkData} aria-label="Retry">
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="memory-network-container">
      {/* Controls */}
      <div
        style={{
          marginBottom: 16,
          display: "flex",
          alignItems: "center",
          gap: 16,
          padding: 12,
          backgroundColor: "#f5f5f5",
          borderRadius: 8,
        }}
      >
        <label style={{ fontWeight: 600 }}>Filter by Cluster:</label>
        <select
          value={selectedCluster || ""}
          onChange={(e) => setSelectedCluster(e.target.value || null)}
          style={{
            padding: "6px 10px",
            borderRadius: 6,
            border: "1px solid #ccc",
          }}
        >
          <option value="">All Clusters</option>
          {clusters.map((c) => (
            <option key={c} value={c}>
              {c.charAt(0).toUpperCase() + c.slice(1)}
            </option>
          ))}
        </select>

        <div style={{ marginLeft: "auto", fontSize: 14, color: "#666" }}>
          Nodes: {filteredData.nodes.length} | Edges: {filteredData.edges.length}
        </div>

        <Button
          onClick={fetchNetworkData}
          disabled={loading}
          aria-label="Refresh"
          style={{ opacity: loading ? 0.7 : 1 }}
        >
          {loading ? "Loading..." : "Refresh"}
        </Button>
      </div>

      {/* Network */}
      <div style={{ position: "relative" }}>
        {loading && (
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              zIndex: 1,
              backgroundColor: "rgba(255,255,255,0.85)",
              borderRadius: 8,
            }}
          >
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
      <div
        style={{
          marginTop: 16,
          padding: 12,
          backgroundColor: "#f9f9f9",
          borderRadius: 8,
          fontSize: 12,
        }}
      >
        <div style={{ fontWeight: 600, marginBottom: 8 }}>Legend:</div>
        <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
          <LegendDot color="#FF6B6B" label="Technical" />
          <LegendDot color="#4ECDC4" label="Personal" />
          <LegendDot color="#45B7D1" label="Work" />
          <LegendDot color="#96CEB4" label="General" />
          <div style={{ marginLeft: 16 }}>Node size = confidence level</div>
        </div>
      </div>
    </div>
  );
};

const LegendDot: React.FC<{ color: string; label: string }> = ({ color, label }) => (
  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
    <div
      style={{
        width: 12,
        height: 12,
        borderRadius: "50%",
        backgroundColor: color,
        border: "1px solid rgba(0,0,0,0.2)",
      }}
    />
    <span>{label}</span>
  </div>
);

export default MemoryNetworkVisualization;
