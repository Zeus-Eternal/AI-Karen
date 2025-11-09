/**
 * AG-UI Memory Grid Component (Production)
 * - Strong typing for row data & renderers
 * - Clean fetch with error handling
 * - Column formatters (confidence, type chips, relationships)
 * - Sensible defaults: pagination, sizing, selection
 * - Quick filter & CSV export (optional toolbar)
 * - Works with shadcn/ui Button; replace if using another UI kit
 */

"use client";

import React, { useState, useEffect, useCallback, useMemo, useRef } from "react";
import {
  AgGridReact
} from "ag-grid-react";
import type {
  ColDef,
  GridReadyEvent,
  FilterChangedEvent,
  ICellRendererParams,
  CsvExportParams,
  ValueFormatterParams,
  ColGroupDef,
} from "ag-grid-community";

import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-alpine.css";

import { Button } from "@/components/ui/button"; // swap if needed
import { cn } from "@/lib/utils";

export type MemoryType = "fact" | "preference" | "context";

export interface MemoryGridRow {
  id: string;
  content: string;
  type: MemoryType;
  confidence: number;
  last_accessed: string; // ISO
  relevance_score: number;
  semantic_cluster: string;
  relationships: string[];
  timestamp: number; // epoch ms
  user_id: string;
  session_id?: string;
  tenant_id?: string;
}

export interface MemoryGridProps {
  userId: string;
  tenantId?: string;
  onMemorySelect?: (memory: MemoryGridRow) => void;
  onMemoryEdit?: (memory: MemoryGridRow) => void;
  filters?: Record<string, unknown>;
  height?: number;
  className?: string;
}

/* ---------------------------
 * Utility: safe JSON POST
 * ------------------------- */
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

/* ---------------------------
 * Cell Renderers
 * ------------------------- */

const ConfidenceCellRenderer: React.FC<ICellRendererParams<MemoryGridRow, number>> = (params) => {
  const confidence = Math.max(0, Math.min(1, params.value ?? 0));
  const percentage = Math.round(confidence * 100);
  const color = confidence > 0.8 ? "#4CAF50" : confidence > 0.6 ? "#FF9800" : "#F44336";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <div
        aria-label={`Confidence ${percentage}%`}
        style={{
          width: 72,
          height: 8,
          backgroundColor: "#e0e0e0",
          borderRadius: 4,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${percentage}%`,
            height: "100%",
            backgroundColor: color,
            transition: "width 0.3s ease",
          }}
        />
      </div>
      <span style={{ fontSize: 12, color: "#666" }}>{percentage}%</span>
    </div>
  );
};

const TypeCellRenderer: React.FC<ICellRendererParams<MemoryGridRow, MemoryType>> = (params) => {
  const type = params.value ?? "context";
  const colors: Record<MemoryType, string> = {
    fact: "#2196F3",
    preference: "#9C27B0",
    context: "#FF9800",
  };
  return (
    <span
      style={{
        padding: "4px 8px",
        borderRadius: 12,
        backgroundColor: colors[type],
        color: "white",
        fontSize: 11,
        fontWeight: 700,
      }}
    >
      {type.toUpperCase()}
    </span>
  );
};

const RelationshipsCellRenderer: React.FC<ICellRendererParams<MemoryGridRow, string[]>> = (params) => {
  const relationships = Array.isArray(params.value) ? params.value : [];
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
      <span style={{ fontSize: 12, color: "#666" }}>
        {relationships.length} connection{relationships.length === 1 ? "" : "s"}
      </span>
      {relationships.length > 0 && (
        <div
          aria-hidden
          style={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            backgroundColor: "#4CAF50",
          }}
        />
      )}
    </div>
  );
};

const ContentCellRenderer: React.FC<ICellRendererParams<MemoryGridRow, string>> = (params) => {
  const content = params.value ?? "";
  const [expanded, setExpanded] = useState(false);

  if (content.length <= 140) return <span>{content}</span>;

  return (
    <div>
      <span>{expanded ? content : `${content.substring(0, 140)}…`}</span>
      <Button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="ml-2 h-6 px-2 text-[10px]"
        variant="outline"
      >
        {expanded ? "Less" : "More"}
      </Button>
    </div>
  );
};

/* ---------------------------
 * Main Component
 * ------------------------- */

export const MemoryGrid: React.FC<MemoryGridProps> = ({
  userId,
  tenantId,
  onMemorySelect,
  onMemoryEdit,
  filters,
  height = 480,
  className,
}) => {
  const gridRef = useRef<AgGridReact<MemoryGridRow>>(null);

  const [rowData, setRowData] = useState<MemoryGridRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [quickFilter, setQuickFilter] = useState("");

  /* ----- Column Defs ----- */
  const columnDefs = useMemo<(ColDef<MemoryGridRow> | ColGroupDef<MemoryGridRow>)[]>(
    () => [
      {
        headerName: "Content",
        field: "content",
        flex: 2,
        minWidth: 220,
        cellRenderer: ContentCellRenderer,
        filter: "agTextColumnFilter",
        sortable: true,
        resizable: true,
        tooltipField: "content",
      },
      {
        headerName: "Type",
        field: "type",
        width: 120,
        cellRenderer: TypeCellRenderer,
        filter: "agSetColumnFilter",
        sortable: true,
      },
      {
        headerName: "Confidence",
        field: "confidence",
        width: 150,
        cellRenderer: ConfidenceCellRenderer,
        filter: "agNumberColumnFilter",
        sortable: true,
        valueFormatter: (p: ValueFormatterParams<MemoryGridRow, number>) =>
          `${Math.round((p.value ?? 0) * 100)}%`,
      },
      {
        headerName: "Cluster",
        field: "semantic_cluster",
        width: 140,
        filter: "agSetColumnFilter",
        sortable: true,
        cellStyle: { textTransform: "capitalize" },
      },
      {
        headerName: "Relationships",
        field: "relationships",
        width: 160,
        cellRenderer: RelationshipsCellRenderer,
        sortable: true,
        comparator: (a?: string[], b?: string[]) => (a?.length ?? 0) - (b?.length ?? 0),
      },
      {
        headerName: "Last Accessed",
        field: "last_accessed",
        width: 180,
        filter: "agDateColumnFilter",
        sortable: true,
        comparator: (a?: string, b?: string) =>
          new Date(a ?? 0).getTime() - new Date(b ?? 0).getTime(),
        valueFormatter: (params: ValueFormatterParams<MemoryGridRow, string>) => {
          if (!params.value) return "";
          const d = new Date(params.value);
          const date = d.toLocaleDateString();
          const time = d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
          return `${date} ${time}`;
        },
      },
      {
        headerName: "Relevance",
        field: "relevance_score",
        width: 130,
        filter: "agNumberColumnFilter",
        sortable: true,
        valueFormatter: (p: ValueFormatterParams<MemoryGridRow, number>) =>
          `${Math.round((p.value ?? 0) * 100)}%`,
      },
    ],
    []
  );

  const defaultColDef = useMemo<ColDef<MemoryGridRow>>(
    () => ({
      sortable: true,
      filter: true,
      resizable: true,
      minWidth: 90,
    }),
    []
  );

  /* ----- Data Load ----- */
  const fetchMemoryData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await safeJsonPost<{ memories?: MemoryGridRow[] }>(
        "/api/memory/grid",
        {
          user_id: userId,
          tenant_id: tenantId,
          filters: filters || {},
        }
      );
      setRowData(Array.isArray(data.memories) ? data.memories : []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load memory data");
    } finally {
      setLoading(false);
    }
  }, [userId, tenantId, filters]);

  useEffect(() => {
    fetchMemoryData();
  }, [fetchMemoryData]);

  /* ----- Grid Events ----- */
  const onGridReady = (params: GridReadyEvent<MemoryGridRow>) => {
    params.api.setGridOption("domLayout", "normal");
    params.api.sizeColumnsToFit({
      defaultMinWidth: 90,
      columnLimits: [{ key: "content", minWidth: 220 }],
    });
  };

  const onFilterChanged = (event: FilterChangedEvent<MemoryGridRow>) => {
    // hook for analytics/telemetry
    const model = event.api.getFilterModel();
    // console.debug("Filters changed:", model);
  };

  const onRowClicked = (event: { data: MemoryGridRow }) => {
    onMemorySelect?.(event.data);
  };

  const onRowDoubleClicked = (event: { data: MemoryGridRow }) => {
    onMemoryEdit?.(event.data);
  };

  /* ----- Grid Options ----- */
  const gridOptions = useMemo(
    () => ({
      pagination: true,
      paginationPageSize: 50,
      rowSelection: "single" as const,
      animateRows: true,
      enableRangeSelection: true,
      suppressRowClickSelection: false,
      rowHeight: 64,
      headerHeight: 44,
      getRowId: (p: { data: MemoryGridRow }) => p.data.id,
      overlayLoadingTemplate:
        '<span class="ag-overlay-loading-center">Loading memory data…</span>',
      overlayNoRowsTemplate:
        '<span class="ag-overlay-no-rows-center">No memories found</span>',
    }),
    []
  );

  /* ----- Toolbar Actions ----- */
  const handleExportCsv = () => {
    const api = gridRef.current?.api;
    if (!api) return;
    const params: CsvExportParams = {
      fileName: `memories_${new Date().toISOString().slice(0, 19)}.csv`,
      processCellCallback: (p) => {
        // flatten arrays for CSV
        if (Array.isArray(p.value)) return p.value.join(" | ");
        if (typeof p.value === "number" && p.column.getColId() === "confidence") {
          return `${Math.round(p.value * 100)}%`;
        }
        if (typeof p.value === "number" && p.column.getColId() === "relevance_score") {
          return `${Math.round(p.value * 100)}%`;
        }
        return p.value ?? "";
      },
    };
    api.exportDataAsCsv(params);
  };

  const handleQuickFilter = (v: string) => {
    setQuickFilter(v);
    gridRef.current?.api.setGridOption("quickFilterText", v);
  };

  /* ----- Error State ----- */
  if (error) {
    return (
      <div
        className="memory-grid-error"
        style={{
          padding: 20,
          textAlign: "center",
          color: "#f44336",
          border: "1px solid #f44336",
          borderRadius: 8,
          backgroundColor: "#ffebee",
        }}
        role="alert"
      >
        <h3 className="mb-2 text-lg font-semibold">Error Loading Memory Data</h3>
        <p className="mb-3 text-sm">{error}</p>
        <Button onClick={fetchMemoryData} variant="destructive">
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className={cn("relative", className)} style={{ height }}>
      {/* Toolbar */}
      <div className="mb-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <input
            aria-label="Search memories"
            placeholder="Quick search…"
            value={quickFilter}
            onChange={(e) => handleQuickFilter(e.target.value)}
            className="h-9 w-[220px] rounded-md border bg-background px-3 text-sm"
          />
          <Button variant="outline" onClick={fetchMemoryData}>
            Refresh
          </Button>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" onClick={handleExportCsv}>
            Export CSV
          </Button>
        </div>
      </div>

      {/* Loading overlay */}
      {loading && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "grid",
            placeItems: "center",
            zIndex: 5,
            background: "rgba(255,255,255,0.6)",
          }}
          aria-busy="true"
        >
          Loading memory data…
        </div>
      )}

      {/* Grid */}
      <div className="ag-theme-alpine h-full w-full rounded-md border">
        <AgGridReact<MemoryGridRow>
          ref={gridRef}
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
          tooltipShowDelay={400}
        />
      </div>
    </div>
  );
};

export default MemoryGrid;
