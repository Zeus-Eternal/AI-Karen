// ui_launchers/KAREN-Theme-Default/src/components/analytics/MemoryNetworkVisualization.tsx
"use client";

import React, { useState, useEffect, useMemo, useCallback, useRef } from "react";
import { AgCharts } from "ag-charts-react";
import type { AgChartOptions } from "ag-charts-community";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import {
  Network,
  Maximize2,
  RotateCcw,
  Brain,
  ZoomIn,
  ZoomOut,
} from "lucide-react";
import { useHooks } from "@/hooks/use-hooks";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";

export interface MemoryNode {
  id: string;
  label: string;
  type: "cluster" | "memory";
  size?: number;
  confidence?: number; // 0..1
  cluster?: string;
  color?: string;
  x?: number;
  y?: number;
}

export interface MemoryEdge {
  from: string;
  to: string;
  weight: number;
  type?: "relationship" | "cluster" | "semantic";
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
  onEdgeClick?: (edge: MemoryEdge) => void; // reserved (AG line segments are synthetic)
  onRefresh?: () => Promise<void>;
  className?: string;
}

type LayoutType = "force" | "circular" | "hierarchical" | "grid";
type FilterType = "all" | "high-confidence" | "recent" | "cluster";

// --- tiny deterministic hash for stable "force" placement (no RNG flicker)
function hashStr(s: string): number {
  let h = 2166136261 >>> 0;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619) >>> 0;
  }
  return h;
}
function hash01(s: string): number {
  return (hashStr(s) % 10000) / 10000;
}

export const MemoryNetworkVisualization: React.FC<MemoryNetworkVisualizationProps> = ({
  data,
  onNodeClick,
  onEdgeClick, // not used directly; kept for API parity
  onRefresh,
  className = "",
}) => {
  const { user } = useAuth();
  const { triggerHooks, registerChartHook } = useHooks();
  const { toast } = useToast();

  const [layoutType, setLayoutType] = useState<LayoutType>("force");
  const [filterType, setFilterType] = useState<FilterType>("all");
  const [confidenceThreshold, setConfidenceThreshold] = useState<number[]>([0.5]);
  const [selectedClusters, setSelectedClusters] = useState<string[]>([]);
  const [showLabels, setShowLabels] = useState(true);
  const [showEdges, setShowEdges] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(1);

  const chartRef = useRef<any>(null);

  // --- Process network data based on filters
  const processedData = useMemo(() => {
    if (!data) return { nodes: [] as MemoryNode[], edges: [] as MemoryEdge[] };

    let filteredNodes = [...data.nodes];
    let filteredEdges = [...data.edges];

    if (filterType === "high-confidence") {
      const thr = confidenceThreshold[0];
      filteredNodes = filteredNodes.filter(
        (n) => n.type === "cluster" || (typeof n.confidence === "number" && n.confidence >= thr),
      );
    }

    if (selectedClusters.length > 0) {
      filteredNodes = filteredNodes.filter((n) =>
        n.type === "cluster"
          ? selectedClusters.includes(n.label)
          : n.cluster
          ? selectedClusters.includes(n.cluster)
          : false,
      );
    }

    // Trim edges to kept nodes
    const nodeIds = new Set(filteredNodes.map((n) => n.id));
    filteredEdges = filteredEdges.filter((e) => nodeIds.has(e.from) && nodeIds.has(e.to));

    return { nodes: filteredNodes, edges: filteredEdges };
  }, [data, filterType, confidenceThreshold, selectedClusters]);

  // --- Layout calculation
  const laidOutNodes = useMemo(() => {
    const nodes = processedData.nodes;
    const len = Math.max(1, nodes.length);

    return nodes.map((node, index) => {
      let x = 0;
      let y = 0;

      switch (layoutType) {
        case "circular": {
          const angle = (index / len) * 2 * Math.PI;
          const radius = node.type === "cluster" ? 220 : 160;
          x = Math.cos(angle) * radius;
          y = Math.sin(angle) * radius;
          break;
        }
        case "grid": {
          const cols = Math.ceil(Math.sqrt(len));
          const cell = 120;
          x = (index % cols) * cell;
          y = Math.floor(index / cols) * cell;
          break;
        }
        case "hierarchical": {
          // Simple 2-level layout: clusters on top, memories below grouped by cluster
          const clusters = nodes.filter((n) => n.type === "cluster");
          const mems = nodes.filter((n) => n.type === "memory");
          if (node.type === "cluster") {
            const cIdx = clusters.findIndex((c) => c.id === node.id);
            x = (cIdx + 1) * 200;
            y = -40;
          } else {
            // group by cluster label
            const group = mems.filter((m) => m.cluster === node.cluster);
            const gIdx = group.findIndex((m) => m.id === node.id);
            const col = clusters.findIndex((c) => c.label === node.cluster);
            x = (col + 1) * 200 + (gIdx % 4) * 40 - 60;
            y = 120 + Math.floor(gIdx / 4) * 60;
          }
          break;
        }
        case "force":
        default: {
          // Deterministic pseudo-random placement for stability (no force sim dependency)
          const hx = hash01(node.id + "|x");
          const hy = hash01(node.id + "|y");
          const spread = node.type === "cluster" ? 260 : 220;
          x = (hx - 0.5) * 2 * spread;
          y = (hy - 0.5) * 2 * spread;
        }
      }

      return {
        id: node.id,
        label: node.label,
        type: node.type,
        x,
        y,
        size: node.type === "cluster" ? Math.max(10, (node.size || 10) * 2.4) : 8,
        confidence: typeof node.confidence === "number" ? node.confidence : 1,
        cluster: node.cluster,
        color: node.color || (node.type === "cluster" ? "#3b82f6" : "#10b981"),
      };
    });
  }, [processedData.nodes, layoutType]);

  // --- Build a NaN-broken polyline array so each edge renders as an independent segment
  const edgesPathData = useMemo(() => {
    if (!showEdges) return [] as { x: number; y: number }[];

    const byId = new Map(laidOutNodes.map((n) => [n.id, n]));
    const path: { x: number; y: number }[] = [];

    for (const e of processedData.edges) {
      const a = byId.get(e.from);
      const b = byId.get(e.to);
      if (!a || !b) continue;
      path.push({ x: a.x, y: a.y });
      path.push({ x: b.x, y: b.y });
      // NaN break so AGCharts doesn't connect to the next segment
      path.push({ x: Number.NaN, y: Number.NaN });
    }
    return path;
  }, [processedData.edges, laidOutNodes, showEdges]);

  // --- Chart options
  const chartOptions: AgChartOptions = useMemo(() => {
    const base: AgChartOptions = {
      theme: "ag-default",
      background: { fill: "transparent" },
      padding: { top: 12, right: 12, bottom: 12, left: 12 },
      title: {
        text: `Memory Network (${processedData.nodes.length} nodes, ${processedData.edges.length} connections)`,
        fontSize: 16,
      },
      axes: [
        {
          type: "number",
          position: "bottom",
          title: { enabled: false },
          tick: { enabled: false },
          line: { enabled: false },
          label: { enabled: false },
        },
        {
          type: "number",
          position: "left",
          title: { enabled: false },
          tick: { enabled: false },
          line: { enabled: false },
          label: { enabled: false },
        },
      ],
      legend: { enabled: false },
      series: [
        // edges (single NaN-broken polyline)
        ...(showEdges && edgesPathData.length
          ? ([
              {
                type: "line",
                data: edgesPathData,
                xKey: "x",
                yKey: "y",
                strokeWidth: 1,
                strokeOpacity: 0.25,
                marker: { enabled: false },
                tooltip: { enabled: false },
              } as unknown,
            ] as unknown[])
          : []),
        // nodes
        {
          type: "scatter",
          data: laidOutNodes,
          xKey: "x",
          yKey: "y",
          sizeKey: "size",
          labelKey: showLabels ? "label" : undefined,
          label: {
            enabled: showLabels,
            fontSize: 10,
            color: "#374151",
          },
          marker: {
            shape: "circle",
            strokeWidth: 2,
            stroke: "#ffffff",
            fillOpacity: 0.95,
            formatter: ({ datum }: unknown) => {
              return {
                fill: datum.color,
                size: datum.size,
              };
            },
          },
          tooltip: {
            renderer: ({ datum }: unknown) => ({
              content: `
                <div class="p-2">
                  <div class="font-semibold">${datum.label}</div>
                  <div class="text-sm text-gray-600">Type: ${datum.type}</div>
                  ${
                    typeof datum.confidence === "number"
                      ? `<div class="text-sm">Confidence: ${(datum.confidence * 100).toFixed(1)}%</div>`
                      : ""
                  }
                  ${datum.cluster ? `<div class="text-sm">Cluster: ${datum.cluster}</div>` : ""}
                </div>
              `,
            }),
          },
          listeners: {
            nodeClick: (event: Event) => {
              const d = event.datum;
              if (!d) return;
              const node: MemoryNode = {
                id: d.id,
                label: d.label,
                type: d.type,
                confidence: d.confidence,
                cluster: d.cluster,
              };
              onNodeClick?.(node);
              triggerHooks(
                "chart_memoryNetwork_nodeClick",
                { chartId: "memoryNetwork", node: d },
                { userId: user?.userId },
              );
            },
          },
        } as unknown,
      ],
    };

    return base;
  }, [
    laidOutNodes,
    processedData.nodes.length,
    processedData.edges.length,
    showLabels,
    showEdges,
    edgesPathData,
    onNodeClick,
    triggerHooks,
    user?.userId,
  ]);

  // --- Hooks (analytics/telemetry)
  useEffect(() => {
    const ids: string[] = [];
    ids.push(
      registerChartHook("memoryNetwork", "dataLoad", async () => {
        return { success: true, nodeCount: processedData.nodes.length, edgeCount: processedData.edges.length };
      }),
    );
    ids.push(
      registerChartHook("memoryNetwork", "nodeClick", async (params) => {
        return { success: true, clickedNode: params };
      }),
    );

    return () => {
      // If your HookContext supports deregistration, do it here.
      // (We keep it no-op for now to avoid leaking impl details.)
    };
  }, [registerChartHook, processedData.nodes.length, processedData.edges.length]);

  useEffect(() => {
    if (chartRef.current && processedData.nodes.length > 0) {
      handleChartReady();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chartRef.current, processedData.nodes.length, processedData.edges.length]);

  const handleChartReady = useCallback(async () => {
    await triggerHooks(
      "chart_memoryNetwork_dataLoad",
      {
        chartId: "memoryNetwork",
        nodeCount: processedData.nodes.length,
        edgeCount: processedData.edges.length,
        layoutType,
        filterType,
      },
      { userId: user?.userId },
    );
  }, [triggerHooks, processedData, layoutType, filterType, user?.userId]);

  const handleRefresh = useCallback(async () => {
    if (!onRefresh) return;
    try {
      await onRefresh();
      toast({
        title: "Network Refreshed",
        description: "Memory network data has been updated successfully.",
      });
      await handleChartReady();
    } catch (error: Error) {
      toast({
        variant: "destructive",
        title: "Refresh Failed",
        description: error?.message || "Failed to refresh network data. Please try again.",
      });
    }
  }, [onRefresh, toast, handleChartReady]);

  const handleZoomIn = () => setZoomLevel((prev) => Math.min(prev * 1.2, 3));
  const handleZoomOut = () => setZoomLevel((prev) => Math.max(prev / 1.2, 0.3));
  const handleResetView = () => {
    setZoomLevel(1);
    setLayoutType("force");
  };

  const ClusterBadge = ({
    cluster,
    isSelected,
    onClick,
  }: {
    cluster: string;
    isSelected: boolean;
    onClick: () => void;
  }) => (
    <Badge
      variant={isSelected ? "default" : "outline"}
      className="cursor-pointer hover:bg-primary/20 transition-colors"
      onClick={onClick}
    >
      {cluster.replace("_", " ").replace(/\b\w/g, (l) => l.toUpperCase())}
    </Badge>
  );

  return (
    <Card className={`w-full ${isFullscreen ? "fixed inset-0 z-50" : ""} ${className}`}>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold flex items-center gap-2">
            <Network className="h-5 w-5" />
            Memory Network
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => setIsFullscreen((v) => !v)}>
              <Maximize2 className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="sm" onClick={handleRefresh}>
              <RotateCcw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>

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
            <Badge variant="secondary">{processedData.edges.length} Connections</Badge>
            <Badge variant="secondary">{data.clusters.length} Clusters</Badge>
          </div>
        )}

        {data && data.clusters.length > 0 && (
          <div className="mt-4">
            <Label className="text-sm font-medium mb-2 block md:text-base lg:text-lg">Filter by Clusters:</Label>
            <div className="flex flex-wrap gap-2">
              {data.clusters.map((cluster) => (
                <ClusterBadge
                  key={cluster}
                  cluster={cluster}
                  isSelected={selectedClusters.includes(cluster)}
                  onClick={() =>
                    setSelectedClusters((prev) =>
                      prev.includes(cluster) ? prev.filter((c) => c !== cluster) : [...prev, cluster],
                    )
                  }
                />
              ))}
            </div>
          </div>
        )}

        {/* Controls */}
        <div className="flex items-center justify-between mt-4 p-4 bg-muted/50 rounded-lg sm:p-4 md:p-6">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <Label htmlFor="layout-select" className="text-sm md:text-base lg:text-lg">
                Layout:
              </Label>
              <Select value={layoutType} onValueChange={(v) => setLayoutType(v as LayoutType)}>
                <SelectTrigger id="layout-select" className="w-36">
                  <SelectValue placeholder="Layout" />
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
              <Label htmlFor="filter-select" className="text-sm md:text-base lg:text-lg">
                Filter:
              </Label>
              <Select value={filterType} onValueChange={(v) => setFilterType(v as FilterType)}>
                <SelectTrigger id="filter-select" className="w-44">
                  <SelectValue placeholder="Filter" />
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

          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <Label htmlFor="confidence-slider" className="text-sm md:text-base lg:text-lg">
                Min Confidence:
              </Label>
              <div className="w-28">
                <Slider
                  id="confidence-slider"
                  value={confidenceThreshold}
                  onValueChange={setConfidenceThreshold}
                  max={1}
                  min={0}
                  step={0.05}
                />
              </div>
              <span className="text-xs text-muted-foreground w-10 text-right">
                {Math.round(confidenceThreshold[0] * 100)}%
              </span>
            </div>

            <div className="flex items-center gap-2">
              <Switch id="show-labels" checked={showLabels} onCheckedChange={setShowLabels} />
              <Label htmlFor="show-labels" className="text-sm md:text-base lg:text-lg">
                Labels
              </Label>
            </div>

            <div className="flex items-center gap-2">
              <Switch id="show-edges" checked={showEdges} onCheckedChange={setShowEdges} />
              <Label htmlFor="show-edges" className="text-sm md:text-base lg:text-lg">
                Edges
              </Label>
            </div>
          </div>
        </div>

        {/* Zoom */}
        <div className="flex items-center gap-2 mt-2">
          <Button variant="outline" size="sm" onClick={handleZoomOut}>
            <ZoomOut className="h-4 w-4" />
          </Button>
          <span className="text-sm text-muted-foreground px-2 md:text-base lg:text-lg">
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

      <CardContent className="p-0 sm:p-4 md:p-6">
        <div
          className={`${isFullscreen ? "h-[calc(100vh-200px)]" : "h-[600px]"} w-full`}
          style={{ transform: `scale(${zoomLevel})`, transformOrigin: "center center" }}
        >
          <AgCharts ref={chartRef} options={chartOptions} />
        </div>

        {/* Legend */}
        <div className="p-4 border-t bg-muted/30 sm:p-4 md:p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded-full bg-blue-500" />
                <span className="text-sm md:text-base lg:text-lg">Clusters</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded-full bg-green-500" />
                <span className="text-sm md:text-base lg:text-lg">Memories</span>
              </div>
            </div>
            <div className="text-sm text-muted-foreground md:text-base lg:text-lg">
              Click nodes to explore • Drag to pan • Scroll to zoom
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
