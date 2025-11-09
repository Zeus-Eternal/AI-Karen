/**
 * Memory Network Graph Component (Production)
 * Interactive network visualization using D3.js for memory relationships
 */

"use client";

import React, {
  useEffect,
  useRef,
  useState,
  useCallback,
  useMemo,
} from "react";
import * as d3 from "d3";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Pause,
  Play,
  Minimize2,
  Maximize2,
  Search,
  Settings,
} from "lucide-react";

import { getMemoryService } from "@/services/memoryService";
import type {
  MemoryNetworkNode as BaseMemoryNetworkNode,
  MemoryNetworkEdge,
  MemoryNetworkData,
  MemoryCluster,
  NetworkStatistics,
  MemoryNetworkProps,
} from "@/types/memory";

// Extend the base node type to be compatible with D3 simulation
export type MemoryNetworkNode = BaseMemoryNetworkNode & d3.SimulationNodeDatum;

export interface NetworkConfig {
  nodeSize: [number, number]; // [min, max]
  linkDistance: number;
  linkStrength: number;
  chargeStrength: number;
  clusterPadding: number;
  showLabels: boolean;
  showClusters: boolean;
  animationSpeed: number;
  colorScheme: "default" | "confidence" | "type" | "cluster";
}

export interface TooltipData {
  node: MemoryNetworkNode;
  x: number;
  y: number;
}

export interface FilterOptions {
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
  width = 800,
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const simulationRef =
    useRef<d3.Simulation<MemoryNetworkNode, MemoryNetworkEdge> | null>(null);

  const [networkData, setNetworkData] = useState<MemoryNetworkData | null>(
    null
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<MemoryNetworkNode | null>(
    null
  );
  const [tooltip, setTooltip] = useState<TooltipData | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isPlaying, setIsPlaying] = useState(true);
  const [showControls, setShowControls] = useState(true);

  const [config, setConfig] = useState<NetworkConfig>({
    nodeSize: [5, 20],
    linkDistance: 60,
    linkStrength: 0.12,
    chargeStrength: -140,
    clusterPadding: 20,
    showLabels: true,
    showClusters: true,
    animationSpeed: 1,
    colorScheme: "cluster",
  });

  const [filters, setFilters] = useState<FilterOptions>({
    minConfidence: 0,
    maxConfidence: 1,
    selectedTypes: [],
    selectedClusters: [],
    minConnections: 0,
    searchQuery: "",
  });

  const memoryService = useMemo(() => getMemoryService(), []);

  // Color scales for different visualization modes
  const colorScales = useMemo(
    () => ({
      // index -> color
      default: d3.scaleOrdinal<string, string>(d3.schemeCategory10),
      // 0..1 -> color
      confidence: d3.scaleSequential(d3.interpolateViridis).domain([0, 1]),
      // type -> color
      type: d3.scaleOrdinal<string, string>(d3.schemeSet2),
      // cluster -> color
      cluster: d3.scaleOrdinal<string, string>(d3.schemeTableau10),
    }),
    []
  );

  /** Load network data (mocked from stats; wire your real endpoint later) */
  const loadNetworkData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const stats = await memoryService.getMemoryStats(userId, tenantId);

      const nodes: MemoryNetworkNode[] = [];
      const edges: MemoryNetworkEdge[] = [];
      const clusters: MemoryCluster[] = [];

      // create nodes
      const nodeCount = Math.max(5, Math.min(stats.totalMemories ?? 50, 120));
      const types = ["fact", "preference", "context"] as const;
      const clusterKeys = Object.keys(stats.memoriesByTag ?? {});
      const safeCluster = (i: number) =>
        clusterKeys.length > 0 ? clusterKeys[i % clusterKeys.length] : "general";

      for (let i = 0; i < nodeCount; i++) {
        const type = types[i % types.length];
        const cluster = safeCluster(i);
        const size =
          config.nodeSize[0] +
          Math.random() * (config.nodeSize[1] - config.nodeSize[0]);

        const node: MemoryNetworkNode = {
          id: `node-${i}`,
          label: `Memory ${i + 1}`,
          content: `Sample memory content for node ${i + 1}`,
          type,
          confidence: 0.5 + Math.random() * 0.5,
          cluster,
          size,
          color: colorScales.cluster(cluster),
          metadata: {
            created: new Date(Date.now() - Math.random() * 86400000 * 30),
            accessed: Math.floor(Math.random() * 100),
          },
          tags: [`tag-${i % 5}`, `category-${i % 3}`],
        };
        nodes.push(node);
      }

      // edges
      const edgeCount = Math.floor(nodeCount * 1.5);
      const seen = new Set<string>();
      const edgeTypes = ["semantic", "temporal", "explicit", "inferred"] as const;

      for (let i = 0; i < edgeCount; i++) {
        const a = Math.floor(Math.random() * nodeCount);
        const b = Math.floor(Math.random() * nodeCount);
        if (a === b) continue;

        const key = a < b ? `${a}-${b}` : `${b}-${a}`;
        if (seen.has(key)) continue;
        seen.add(key);

        const e: MemoryNetworkEdge = {
          id: key,
          source: nodes[a].id,
          target: nodes[b].id,
          weight: Math.random(),
          type: edgeTypes[Math.floor(Math.random() * edgeTypes.length)] as any,
          confidence: 0.3 + Math.random() * 0.7,
        };
        edges.push(e);
      }

      // clusters
      const clusterNames = [...new Set(nodes.map((n) => n.cluster))];
      clusterNames.forEach((name, idx) => {
        const clusterNodes = nodes.filter((n) => n.cluster === name);
        const cl: MemoryCluster = {
          id: `cluster-${idx}`,
          name,
          nodes: clusterNodes.map((n) => n.id),
          centroid: { x: 0, y: 0 },
          color: colorScales.cluster(name),
          size: clusterNodes.length,
          density: clusterNodes.length / nodeCount,
          coherence: 0.7 + Math.random() * 0.3,
          topics: [`topic-${idx}-1`, `topic-${idx}-2`],
        };
        clusters.push(cl);
      });

      const statistics: NetworkStatistics = {
        nodeCount: nodes.length,
        edgeCount: edges.length,
        clusterCount: clusters.length,
        averageConnectivity: edges.length / Math.max(1, nodes.length),
        networkDensity:
          (2 * edges.length) / (nodes.length * Math.max(1, nodes.length - 1)),
        modularity: 0.3 + Math.random() * 0.4,
        smallWorldCoefficient: 0.1 + Math.random() * 0.2,
      };

      setNetworkData({ nodes, edges, clusters, statistics });
    } catch (err) {
      const msg =
        err instanceof Error ? err.message : "Failed to load network data";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [userId, tenantId, memoryService, colorScales, config.nodeSize]);

  /** Filter data for rendering */
  const filteredData = useMemo(() => {
    if (!networkData) return null;

    let nodes = networkData.nodes.filter((node) => {
      // confidence
      if (
        node.confidence < filters.minConfidence ||
        node.confidence > filters.maxConfidence
      )
        return false;

      // type
      if (
        filters.selectedTypes.length > 0 &&
        !filters.selectedTypes.includes(node.type)
      )
        return false;

      // cluster
      if (
        filters.selectedClusters.length > 0 &&
        !filters.selectedClusters.includes(node.cluster)
      )
        return false;

      // search
      if (filters.searchQuery) {
        const q = filters.searchQuery.toLowerCase();
        const hit =
          node.label.toLowerCase().includes(q) ||
          node.content.toLowerCase().includes(q) ||
          (node.tags || []).some((t) => t.toLowerCase().includes(q));
        if (!hit) return false;
      }
      return true;
    });

    const nodeIds = new Set(nodes.map((n) => n.id));
    let edges = networkData.edges.filter(
      (e) =>
        nodeIds.has(e.source as string) && nodeIds.has(e.target as string)
    );

    if (filters.minConnections > 0) {
      const counts = new Map<string, number>();
      edges.forEach((e) => {
        const s = e.source as string;
        const t = e.target as string;
        counts.set(s, (counts.get(s) || 0) + 1);
        counts.set(t, (counts.get(t) || 0) + 1);
      });
      nodes = nodes.filter(
        (n) => (counts.get(n.id) || 0) >= filters.minConnections
      );

      // recompute edges using reduced nodes set
      const reduced = new Set(nodes.map((n) => n.id));
      edges = edges.filter(
        (e) => reduced.has(e.source as string) && reduced.has(e.target as string)
      );
    }

    // pass through clusters unchanged (optional: recalc)
    return { ...networkData, nodes, edges };
  }, [networkData, filters]);

  /** Main D3 renderer */
  const updateVisualization = useCallback(() => {
    if (!filteredData || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    const container = svg.select<SVGGElement>(".network-container");
    container.selectAll("*").remove();

    // Zoom
    const zoomBehavior = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 10])
      .on("zoom", (event) => {
        container.attr("transform", event.transform.toString());
      });

    svg.call(zoomBehavior as any);

    // Simulation
    const sim = d3
      .forceSimulation<MemoryNetworkNode>(filteredData.nodes)
      .force(
        "link",
        d3
          .forceLink<MemoryNetworkNode, MemoryNetworkEdge>(filteredData.edges)
          .id((d) => d.id)
          .distance(config.linkDistance)
          .strength(config.linkStrength)
      )
      .force("charge", d3.forceManyBody().strength(config.chargeStrength))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force(
        "collision",
        d3
          .forceCollide<MemoryNetworkNode>()
          .radius((d) => (d as MemoryNetworkNode).size + 2)
      );

    simulationRef.current = sim;

    // Clusters (background circles)
    if (config.showClusters && filteredData.clusters) {
      const clusterGroups = container
        .selectAll<SVGGElement, MemoryCluster>(".cluster")
        .data(filteredData.clusters)
        .enter()
        .append("g")
        .attr("class", "cluster");

      clusterGroups
        .append("circle")
        .attr("class", "cluster-background")
        .attr("r", (d) => Math.sqrt(Math.max(1, d.size)) * 20)
        .attr("fill", (d) => d.color)
        .attr("fill-opacity", 0.1)
        .attr("stroke", (d) => d.color)
        .attr("stroke-width", 2)
        .attr("stroke-dasharray", "5,5");
    }

    // Links
    const links = container
      .selectAll<SVGLineElement, MemoryNetworkEdge>(".link")
      .data(filteredData.edges)
      .enter()
      .append("line")
      .attr("class", "link")
      .attr("stroke", (d) => {
        const colors: Record<string, string> = {
          semantic: "#2196F3",
          temporal: "#4CAF50",
          explicit: "#FF9800",
          inferred: "#9C27B0",
        };
        return colors[d.type] || "#999";
      })
      .attr("stroke-width", (d) => Math.max(1, Math.sqrt(d.weight) * 2))
      .attr("stroke-opacity", (d) => Math.max(0.15, d.confidence * 0.85));

    // Nodes
    const nodeGroups = container
      .selectAll<SVGGElement, MemoryNetworkNode>(".node")
      .data(filteredData.nodes)
      .enter()
      .append("g")
      .attr("class", "node")
      .style("cursor", "pointer");

    // Circles
    nodeGroups
      .append("circle")
      .attr("r", (d) => d.size)
      .attr("fill", (d) => {
        switch (config.colorScheme) {
          case "confidence":
            return colorScales.confidence(d.confidence);
          case "type":
            return colorScales.type(d.type);
          case "cluster":
            return colorScales.cluster(d.cluster);
          default:
            return colorScales.default(d.id);
        }
      })
      .attr("stroke", "#fff")
      .attr("stroke-width", 2);

    // Labels
    if (config.showLabels) {
      nodeGroups
        .append("text")
        .attr("class", "node-label")
        .attr("dx", (d) => d.size + 5)
        .attr("dy", ".35em")
        .style("fontSize", "10px")
        .style("fill", "#333")
        .text((d) => d.label);
    }

    // Hover + tooltip + highlight
    nodeGroups
      .on("mouseover", (event, d) => {
        // tooltip relative to container
        const rect = containerRef.current?.getBoundingClientRect();
        const x = (event as MouseEvent).clientX - (rect?.left ?? 0);
        const y = (event as MouseEvent).clientY - (rect?.top ?? 0);

        setTooltip({ node: d, x, y });

        const connected = new Set<string>();
        links.style("stroke-opacity", (edge) => {
          const sid =
            typeof edge.source === "string"
              ? edge.source
              : (edge.source as MemoryNetworkNode).id;
          const tid =
            typeof edge.target === "string"
              ? edge.target
              : (edge.target as MemoryNetworkNode).id;
          if (sid === d.id || tid === d.id) {
            connected.add(sid);
            connected.add(tid);
            return 1;
          }
          return 0.1;
        });

        nodeGroups.select("circle").style("opacity", (n) => {
          const id = (n as MemoryNetworkNode).id;
          return connected.has(id) || id === d.id ? 1 : 0.3;
        });
      })
      .on("mouseout", () => {
        setTooltip(null);
        links.style("stroke-opacity", (edge) =>
          Math.max(0.15, edge.confidence * 0.85)
        );
        nodeGroups.select("circle").style("opacity", 1);
      })
      .on("click", (_, d) => {
        setSelectedNode(d);
        onNodeSelect?.(d);
      })
      .on("dblclick", (_, d) => {
        onNodeDoubleClick?.(d);
      });

    // Drag
    const drag = d3
      .drag<SVGGElement, MemoryNetworkNode>()
      .on("start", (event, d) => {
        if (!event.active) sim.alphaTarget(0.3).restart();
        d.fx = d.x ?? 0;
        d.fy = d.y ?? 0;
      })
      .on("drag", (event, d) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on("end", (event, d) => {
        if (!event.active) sim.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      });

    nodeGroups.call(drag as any);

    // Tick
    sim.on("tick", () => {
      links
        .attr("x1", (d) =>
          typeof d.source === "object" ? (d.source as any).x ?? 0 : 0
        )
        .attr("y1", (d) =>
          typeof d.source === "object" ? (d.source as any).y ?? 0 : 0
        )
        .attr("x2", (d) =>
          typeof d.target === "object" ? (d.target as any).x ?? 0 : 0
        )
        .attr("y2", (d) =>
          typeof d.target === "object" ? (d.target as any).y ?? 0 : 0
        );

      nodeGroups.attr(
        "transform",
        (d) => `translate(${(d as any).x || 0}, ${(d as any).y || 0})`
      );

      // cluster centroids
      if (config.showClusters && filteredData.clusters) {
        filteredData.clusters.forEach((cluster) => {
          const cNodes = filteredData.nodes.filter((n) =>
            cluster.nodes.includes(n.id)
          );
          if (cNodes.length > 0) {
            cluster.centroid.x =
              d3.mean(cNodes, (n: any) => n.x || 0) ?? cluster.centroid.x;
            cluster.centroid.y =
              d3.mean(cNodes, (n: any) => n.y || 0) ?? cluster.centroid.y;
          }
        });

        container
          .selectAll<SVGCircleElement, MemoryCluster>(".cluster-background")
          .attr("cx", (d) => d.centroid.x)
          .attr("cy", (d) => d.centroid.y)
          .on("click", (_, d) => onClusterSelect?.(d));
      }
    });

    if (!isPlaying) sim.stop();
  }, [
    filteredData,
    config,
    width,
    height,
    colorScales,
    isPlaying,
    onNodeSelect,
    onNodeDoubleClick,
    onClusterSelect,
  ]);

  // Load on mount
  useEffect(() => {
    loadNetworkData();
  }, [loadNetworkData]);

  // Refresh render on data/config changes
  useEffect(() => {
    updateVisualization();
  }, [updateVisualization]);

  // Cleanup
  useEffect(() => {
    return () => {
      simulationRef.current?.stop();
    };
  }, []);

  // Controls
  const handleZoomIn = useCallback(() => {
    if (svgRef.current) {
      d3.select(svgRef.current)
        .transition()
        .call((d3.zoom<SVGSVGElement, unknown>().scaleBy as any), 1.5);
    }
  }, []);

  const handleZoomOut = useCallback(() => {
    if (svgRef.current) {
      d3.select(svgRef.current)
        .transition()
        .call((d3.zoom<SVGSVGElement, unknown>().scaleBy as any), 1 / 1.5);
    }
  }, []);

  const handleReset = useCallback(() => {
    if (svgRef.current) {
      d3.select(svgRef.current)
        .transition()
        .call(
          (d3.zoom<SVGSVGElement, unknown>().transform as any),
          d3.zoomIdentity
        );
    }
    simulationRef.current?.alpha(1).restart();
  }, []);

  const togglePlayPause = useCallback(() => {
    setIsPlaying((prev) => {
      const next = !prev;
      if (simulationRef.current) {
        if (next) simulationRef.current.alpha(0.3).restart();
        else simulationRef.current.stop();
      }
      return next;
    });
  }, []);

  const toggleFullscreen = useCallback(() => {
    setIsFullscreen((prev) => !prev);
  }, []);

  if (error) {
    return (
      <Card className="p-6 sm:p-4 md:p-6">
        <div className="text-center">
          <div className="mb-4 text-red-600">
            <Settings className="mx-auto mb-2 h-12 w-12" />
            <h3 className="text-lg font-semibold">Network Error</h3>
          </div>
          <p className="mb-4 text-gray-600">{error}</p>
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
      className={`relative ${isFullscreen ? "fixed inset-0 z-50 bg-white" : ""}`}
      style={{ height: `${height}px`, width: `${width}px` }}
      data-kari="memory-network-graph"
    >
      {/* Controls */}
      {showControls && (
        <div className="absolute left-4 top-4 z-10 space-y-2">
          <Card className="p-2">
            <div className="flex space-x-1">
              <Button size="sm" variant="outline" onClick={handleZoomIn} title="Zoom in">
                <ZoomIn className="h-4 w-4" />
              </Button>
              <Button size="sm" variant="outline" onClick={handleZoomOut} title="Zoom out">
                <ZoomOut className="h-4 w-4" />
              </Button>
              <Button size="sm" variant="outline" onClick={handleReset} title="Reset view">
                <RotateCcw className="h-4 w-4" />
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={togglePlayPause}
                title={isPlaying ? "Pause layout" : "Resume layout"}
              >
                {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={toggleFullscreen}
                title={isFullscreen ? "Exit fullscreen" : "Fullscreen"}
              >
                {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
              </Button>
            </div>
          </Card>

          {/* Search + filter */}
          <Card className="w-64 p-3">
            <div className="space-y-2">
              <div className="relative">
                <Search className="absolute left-2 top-1/2 h-4 w-4 -translate-y-1/2 transform text-gray-400" />
                <Input
                  placeholder="Search nodes..."
                  value={filters.searchQuery}
                  onChange={(e) =>
                    setFilters((p) => ({ ...p, searchQuery: e.target.value }))
                  }
                  className="pl-8"
                />
              </div>

              <div className="flex items-center space-x-2">
                <label className="text-xs text-gray-600">Min Confidence:</label>
                <input
                  type="range"
                  min={0}
                  max={1}
                  step={0.1}
                  value={filters.minConfidence}
                  onChange={(e) =>
                    setFilters((p) => ({
                      ...p,
                      minConfidence: parseFloat(e.target.value),
                    }))
                  }
                  className="flex-1"
                />
                <span className="w-8 text-xs text-gray-600">
                  {filters.minConfidence.toFixed(1)}
                </span>
              </div>

              <div className="flex items-center space-x-2">
                <label className="text-xs text-gray-600">Color by:</label>
                <select
                  value={config.colorScheme}
                  onChange={(e) =>
                    setConfig((p) => ({
                      ...p,
                      colorScheme: e.target.value as NetworkConfig["colorScheme"],
                    }))
                  }
                  className="rounded border px-1 py-1 text-xs"
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
        <div className="absolute right-4 top-4 z-10">
          <Card className="p-3">
            <div className="space-y-1 text-xs">
              <div className="font-semibold">Network Statistics</div>
              <div>
                Nodes: {filteredData?.nodes.length || 0} / {networkData.statistics.nodeCount}
              </div>
              <div>
                Edges: {filteredData?.edges.length || 0} / {networkData.statistics.edgeCount}
              </div>
              <div>Clusters: {networkData.statistics.clusterCount}</div>
              <div>
                Density: {(networkData.statistics.networkDensity * 100).toFixed(1)}%
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* SVG */}
      <svg
        ref={svgRef}
        width={width}
        height={height}
        className="rounded border"
        style={{ background: "#fafafa" }}
      >
        <defs>
          <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
            <polygon points="0 0, 10 3.5, 0 7" fill="#999" />
          </marker>
        </defs>
        <g className="network-container" />
      </svg>

      {/* Loading */}
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-white/75">
          <div className="text-center">
            <div className="mx-auto mb-2 h-8 w-8 animate-spin rounded-full border-b-2 border-blue-500" />
            <div className="text-sm text-gray-600">Loading network...</div>
          </div>
        </div>
      )}

      {/* Tooltip */}
      {tooltip && (
        <div
          className="pointer-events-none absolute z-20 max-w-xs rounded bg-black p-2 text-xs text-white"
          style={{
            left: tooltip.x + 10,
            top: tooltip.y - 10,
            transform: "translateY(-100%)",
          }}
          role="tooltip"
        >
          <div className="font-semibold">{tooltip.node.label}</div>
          <div className="text-gray-300">Type: {tooltip.node.type}</div>
          <div className="text-gray-300">Cluster: {tooltip.node.cluster}</div>
          <div className="text-gray-300">
            Confidence: {(tooltip.node.confidence * 100).toFixed(0)}%
          </div>
          <div className="mt-1 line-clamp-2 text-gray-300">
            {tooltip.node.content}
          </div>
          <div className="mt-1 flex flex-wrap gap-1">
            {tooltip.node.tags.slice(0, 3).map((tag) => (
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
          <Card className="max-w-sm p-3">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-semibold">{selectedNode.label}</h4>
                <Button
                  onClick={() => setSelectedNode(null)}
                  className="text-gray-400 hover:text-gray-600"
                  variant="ghost"
                  size="sm"
                >
                  ×
                </Button>
              </div>
              <div className="text-xs text-gray-600">
                <div>
                  Type:{" "}
                  <Badge variant="outline" className="text-xs">
                    {selectedNode.type}
                  </Badge>
                </div>
                <div>
                  Cluster:{" "}
                  <Badge variant="outline" className="text-xs">
                    {selectedNode.cluster}
                  </Badge>
                </div>
                <div>Confidence: {(selectedNode.confidence * 100).toFixed(0)}%</div>
              </div>
              <div className="text-xs">{selectedNode.content}</div>
              <div className="flex flex-wrap gap-1">
                {selectedNode.tags.map((tag) => (
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
