/**
 * Comprehensive Memory Interface Component (Production)
 * - Orchestrates Grid, Network, and Analytics views
 * - CopilotKit-enhanced editing (MemoryEditor)
 * - Safe fetch, explicit error surfacing
 * - Lazy-loaded charts & network viz
 * - Local refresh on save/delete without page reloads
 */

"use client";

import React, { useState, useCallback, useEffect, useMemo } from "react";
import dynamic from "next/dynamic";
import { v4 as uuidv4 } from "uuid";

import { ErrorBoundary } from "@/components/error-handling/ErrorBoundary";
import { CopilotKit } from "@copilotkit/react-core";
import MemoryGrid from "./MemoryGrid";
import MemoryEditor from "./MemoryEditor";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import type { AgChartOptions } from "ag-charts-community";

// Lazy-load heavy pieces
const MemoryNetworkVisualization = dynamic(
  () => import("./MemoryNetworkVisualization"),
  { ssr: false }
);
const AgCharts = dynamic(() => import("ag-charts-react").then((m) => m.AgCharts), {
  ssr: false,
});

/* ============================
 * Types
 * ========================== */
export type MemoryType = "fact" | "preference" | "context";

export interface MemoryGridRow {
  id: string;
  content: string;
  type: MemoryType;
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

export interface MemoryNetworkNode {
  id: string;
  label: string;
  type: string;
  confidence: number;
  cluster: string;
  size: number;
  color: string;
}

export interface MemoryAnalytics {
  total_memories: number;
  memories_by_type: Record<string, number>;
  memories_by_cluster: Record<string, number>;
  confidence_distribution: Array<{ range: string; count: number }>;
  access_patterns: Array<{ date: string; count: number }>;
  relationship_stats: Record<string, number>;
}

export interface MemoryInterfaceProps {
  userId: string;
  tenantId?: string;
  copilotApiKey?: string;
  height?: number;
}

export type ViewMode = "grid" | "network" | "analytics";

/* ============================
 * Utils
 * ========================== */
async function safeJsonPost<T = any>(url: string, payload: unknown): Promise<T> {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status}: ${text || res.statusText}`);
  }
  return res.json() as Promise<T>;
}

/* ============================
 * Component
 * ========================== */
export const MemoryInterface: React.FC<MemoryInterfaceProps> = ({
  userId,
  tenantId,
  copilotApiKey,
  height = 600,
}) => {
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [selectedMemory, setSelectedMemory] = useState<MemoryGridRow | null>(null);
  const [isEditorOpen, setIsEditorOpen] = useState(false);

  const [searchQuery, setSearchQuery] = useState("");
  const [filters, setFilters] = useState<Record<string, any>>({});

  const [analytics, setAnalytics] = useState<MemoryAnalytics | null>(null);
  const [isLoadingAnalytics, setIsLoadingAnalytics] = useState(false);

  const [error, setError] = useState<string | null>(null);
  const [gridKey, setGridKey] = useState<number>(0); // remount grid on save/delete

  // Unique instance ID (if you want to correlate logs)
  const componentInstanceId = useMemo(() => uuidv4(), []);

  /* ----- Analytics ----- */
  const fetchAnalytics = useCallback(async () => {
    try {
      setIsLoadingAnalytics(true);
      setError(null);
      const data = await safeJsonPost<MemoryAnalytics>("/api/memory/analytics", {
        user_id: userId,
        tenant_id: tenantId,
        timeframe_days: 30,
      });
      setAnalytics(data);
    } catch (err) {
      setError(
        (err as Error)?.message || "Failed to load analytics. Please try again later."
      );
      setAnalytics(null);
    } finally {
      setIsLoadingAnalytics(false);
    }
  }, [userId, tenantId]);

  useEffect(() => {
    if (viewMode === "analytics" && !analytics && !isLoadingAnalytics) {
      fetchAnalytics();
    }
  }, [viewMode, analytics, isLoadingAnalytics, fetchAnalytics]);

  /* ----- Selection / Editor ----- */
  const handleMemorySelect = useCallback((memory: MemoryGridRow) => {
    setSelectedMemory(memory);
  }, []);

  const handleMemoryEdit = useCallback((memory: MemoryGridRow) => {
    setSelectedMemory(memory);
    setIsEditorOpen(true);
  }, []);

  const handleEditorCancel = useCallback(() => {
    setIsEditorOpen(false);
    setSelectedMemory(null);
    setError(null);
  }, []);

  /* ----- Save/Delete ----- */
  const handleMemorySave = useCallback(
    async (updatedMemory: Partial<MemoryGridRow>) => {
      try {
        setError(null);
        if (!selectedMemory?.id && !updatedMemory.content) {
          throw new Error("Memory content is required");
        }
        await safeJsonPost("/api/memory/update", {
          user_id: userId,
          tenant_id: tenantId,
          memory_id: selectedMemory?.id || undefined,
          query: selectedMemory?.content || "",
          result: updatedMemory.content,
          metadata: {
            type: updatedMemory.type || "fact",
            confidence: updatedMemory.confidence ?? 0.8,
            semantic_cluster: updatedMemory.semantic_cluster || "default",
            updated_at: new Date().toISOString(),
          },
        });
        setIsEditorOpen(false);
        setSelectedMemory(null);
        // Trigger grid remount to refresh data
        setGridKey((k) => k + 1);
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Failed to save memory";
        setError(msg);
        throw err;
      }
    },
    [selectedMemory, userId, tenantId]
  );

  const handleMemoryDelete = useCallback(
    async (memoryId: string) => {
      try {
        setError(null);
        await safeJsonPost("/api/memory/delete", {
          user_id: userId,
          tenant_id: tenantId,
          memory_id: memoryId,
        });
        setIsEditorOpen(false);
        setSelectedMemory(null);
        setGridKey((k) => k + 1);
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Failed to delete memory";
        setError(msg);
        throw err;
      }
    },
    [userId, tenantId]
  );

  /* ----- Search ----- */
  const handleSearch = useCallback(async () => {
    if (!searchQuery.trim()) {
      // Clear search_results filter if present
      setFilters((prev) => {
        const next = { ...prev };
        delete next.search_results;
        return next;
      });
      return;
    }
    try {
      setError(null);
      const data = await safeJsonPost<{ results: any[] }>("/api/memory/search", {
        user_id: userId,
        tenant_id: tenantId,
        query: searchQuery,
        filters,
        limit: 50,
      });
      setFilters({ ...filters, search_results: data.results });
      setViewMode("grid");
      setGridKey((k) => k + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    }
  }, [searchQuery, filters, userId, tenantId]);

  /* ----- Create ----- */
  const handleCreateMemory = useCallback(() => {
    setSelectedMemory(null);
    setIsEditorOpen(true);
    setError(null);
  }, []);

  /* ----- Analytics charts (memoized) ----- */
  const analyticsCharts = useMemo<AgChartOptions[]>(() => {
    if (!analytics) return [];

    const charts: AgChartOptions[] = [];

    // Memory Types pie
    if (analytics.memories_by_type) {
      const typeData = Object.entries(analytics.memories_by_type).map(
        ([type, count]) => ({
          type: type.charAt(0).toUpperCase() + type.slice(1),
          count,
        })
      );
      charts.push({
        title: { text: "Memory Types Distribution" },
        data: typeData,
        series: [{ type: "pie", angleKey: "count", labelKey: "type" }],
      });
    }

    // Confidence distribution columns
    if (analytics.confidence_distribution) {
      charts.push({
        title: { text: "Confidence Score Distribution" },
        data: analytics.confidence_distribution,
        axes: [
          { type: "category", position: "bottom" },
          { type: "number", position: "left" },
        ],
        series: [{ type: "column", xKey: "range", yKey: "count" }],
      });
    }

    // Access patterns line
    if (analytics.access_patterns) {
      charts.push({
        title: { text: "Memory Access Patterns (Last 30 Days)" },
        data: analytics.access_patterns,
        axes: [
          { type: "time", position: "bottom", label: { format: "%b %d" } },
          { type: "number", position: "left" },
        ],
        series: [{ type: "line", xKey: "date", yKey: "count", marker: { enabled: true } }],
      });
    }

    return charts;
  }, [analytics]);

  /* ----- View Buttons style (inline minimal) ----- */
  const isActive = (mode: ViewMode) =>
    viewMode === mode ? "bg-primary text-primary-foreground border-primary" : "bg-background";

  /* ----- Render ----- */
  return (
    <ErrorBoundary fallback={<div>Something went wrong in MemoryInterface</div>}>
      <CopilotKit apiKey={copilotApiKey}>
        <div
          className="memory-interface relative flex flex-col"
          style={{ height: `${height}px` }}
          data-kari="memory-interface"
          data-instance={componentInstanceId}
        >
          {/* Error Toast */}
          {error && (
            <div className="absolute right-4 top-4 z-50 flex items-center gap-2 rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-800 shadow-sm">
              <span>{error}</span>
              <Button variant="ghost" size="icon" aria-label="Dismiss error" onClick={() => setError(null)}>
                ×
              </Button>
            </div>
          )}

          {/* Header */}
          <div className="flex flex-wrap items-center gap-3 border-b bg-muted/40 p-4">
            <h2 className="m-0 text-xl font-semibold">Memory Management</h2>

            <div className="ml-2 flex gap-2">
              <Button onClick={() => setViewMode("grid")} className={isActive("grid")}>
                Grid
              </Button>
              <Button onClick={() => setViewMode("network")} className={isActive("network")}>
                Network
              </Button>
              <Button onClick={() => setViewMode("analytics")} className={isActive("analytics")}>
                Analytics
              </Button>
            </div>

            <div className="ml-auto flex min-w-[300px] max-w-[500px] flex-1 items-center gap-2">
              <Input
                placeholder="Search memories…"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              />
              <Button onClick={handleSearch} disabled={!searchQuery.trim()}>
                Search
              </Button>
              <Button onClick={handleCreateMemory} variant="secondary">
                New Memory
              </Button>
            </div>
          </div>

          {/* Main */}
          <div className="flex-1 overflow-hidden p-4">
            {viewMode === "grid" && (
              <MemoryGrid
                key={gridKey}
                userId={userId}
                tenantId={tenantId}
                onMemorySelect={handleMemorySelect}
                onMemoryEdit={handleMemoryEdit}
                filters={filters}
                height={height - 120}
              />
            )}

            {viewMode === "network" && (
              <MemoryNetworkVisualization
                userId={userId}
                tenantId={tenantId}
                onNodeSelect={(node: MemoryNetworkNode) => {
                  // Optionally: set filters or focus based on node
                  void node;
                }}
                onNodeDoubleClick={(node: MemoryNetworkNode) => {
                  // Optional: open editor based on node mapping
                  console.log("Double clicked:", node);
                }}
                height={height - 120}
                width={undefined /* let component use container width */}
              />
            )}

            {viewMode === "analytics" && (
              <div style={{ height: height - 120, overflow: "auto" }}>
                {isLoadingAnalytics ? (
                  <div className="grid h-[200px] place-items-center text-muted-foreground">
                    Loading analytics…
                  </div>
                ) : analytics ? (
                  <div>
                    {/* Summary stats */}
                    <div className="mb-6 grid gap-4 [grid-template-columns:repeat(auto-fit,minmax(200px,1fr))]">
                      <div className="rounded-lg bg-muted/40 p-4 text-center">
                        <h3 className="mb-1 text-2xl font-bold text-primary">
                          {analytics.total_memories.toLocaleString()}
                        </h3>
                        <p className="m-0 text-sm text-muted-foreground">Total Memories</p>
                      </div>
                      <div className="rounded-lg bg-muted/40 p-4 text-center">
                        <h3 className="mb-1 text-2xl font-bold text-green-600">
                          {(analytics.relationship_stats?.connected_memories || 0).toLocaleString()}
                        </h3>
                        <p className="m-0 text-sm text-muted-foreground">Connected Memories</p>
                      </div>
                      <div className="rounded-lg bg-muted/40 p-4 text-center">
                        <h3 className="mb-1 text-2xl font-bold text-amber-600">
                          {Object.keys(analytics.memories_by_cluster || {}).length.toLocaleString()}
                        </h3>
                        <p className="m-0 text-sm text-muted-foreground">Clusters</p>
                      </div>
                    </div>

                    {/* Charts */}
                    <div className="grid gap-6 [grid-template-columns:repeat(auto-fit,minmax(380px,1fr))]">
                      {analyticsCharts.map((opts, i) => (
                        <div key={i} className="rounded-lg border bg-background p-4">
                          <h3 className="mb-4 text-base font-semibold">
                            {opts.title && typeof opts.title !== "string" ? opts.title.text : opts.title}
                          </h3>
                          <div className="h-[300px]">
                            <AgCharts options={opts as AgChartOptions} />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="grid h-[200px] place-items-center text-muted-foreground">
                    {error ? "Error loading analytics" : "No analytics data available"}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Editor */}
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
    </ErrorBoundary>
  );
};

export default MemoryInterface;
