"use client";

import React, { useState, useEffect, useMemo, useCallback } from "react";
import { AgGridReact } from "ag-grid-react";
import type {
  ColDef,
  GridReadyEvent,
  ICellRendererParams,
} from "ag-grid-community";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import {
  MousePointer,
  Eye,
  Activity,
  TrendingUp,
  Search as SearchIcon,
  CheckCircle,
  AlertCircle,
  Clock,
  Users,
  BarChart3,
  Download,
} from "lucide-react";
import { useHooks } from "@/hooks/use-hooks";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";
import { format, formatDistanceToNow } from "date-fns";

import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-alpine.css";

/* -------------------------------- Types ------------------------------- */

export interface UserEngagementRow {
  id: string;
  timestamp: string; // ISO
  userId: string;
  componentType: string;
  componentId: string;
  interactionType: string;
  duration: number; // ms
  success: boolean;
  errorMessage?: string;
  sessionId?: string;
  userAgent?: string;
  location?: string;
}

interface UserEngagementGridProps {
  data?: UserEngagementRow[];
  onRowSelect?: (row: UserEngagementRow) => void;
  onExport?: (data: UserEngagementRow[]) => Promise<void>;
  onRefresh?: () => Promise<void>;
  className?: string;
}

type FilterType = "all" | "success" | "error" | "recent" | "component";
type TimeRange = "1h" | "24h" | "7d" | "30d";

/* ------------------------- Cell Renderers (AG Grid) ------------------------- */

const ComponentTypeRenderer = (params: ICellRendererParams<UserEngagementRow>) => {
  const type = String(params.value ?? "");
  const icons: Record<string, string> = {
    chat: "💬",
    analytics: "📊",
    memory: "🧠",
    grid: "📋",
    chart: "📈",
    button: "🔘",
    form: "📝",
    modal: "🪟",
  };
  return (
    <div className="flex items-center gap-2">
      <span>{icons[type] ?? "🔧"}</span>
      <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
        {type || "unknown"}
      </Badge>
    </div>
  );
};

const InteractionTypeRenderer = (params: ICellRendererParams<UserEngagementRow>) => {
  const type = String(params.value ?? "");
  const variants = {
    click: "default",
    view: "secondary",
    hover: "outline",
    scroll: "outline",
    input: "default",
    submit: "default",
    error: "destructive",
  } as const;

  const iconMap: Record<string, JSX.Element> = {
    click: <MousePointer className="h-3 w-3" />,
    view: <Eye className="h-3 w-3" />,
    hover: <Activity className="h-3 w-3" />,
    scroll: <TrendingUp className="h-3 w-3" />,
    input: <SearchIcon className="h-3 w-3" />,
    submit: <CheckCircle className="h-3 w-3" />,
    error: <AlertCircle className="h-3 w-3" />,
  };

  return (
    <Badge
      variant={(variants as unknown)[type] ?? "outline"}
      className="text-xs flex items-center gap-1 sm:text-sm md:text-base"
    >
      {iconMap[type]}
      {type || "unknown"}
    </Badge>
  );
};

const DurationRenderer = (params: ICellRendererParams<UserEngagementRow>) => {
  const duration = Number(params.value ?? 0);
  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
    };
  const color =
    duration > 10000 ? "text-red-600" : duration > 5000 ? "text-yellow-600" : "text-green-600";

  return (
    <div className="flex items-center gap-2">
      <Clock className={`h-3 w-3 ${color}`} />
      <span className={`text-sm font-medium ${color}`}>{formatDuration(duration)}</span>
    </div>
  );
};

const SuccessRenderer = (params: ICellRendererParams<UserEngagementRow>) => {
  const success = Boolean(params.value);
  return (
    <div className="flex items-center gap-2">
      {success ? (
        <CheckCircle className="h-4 w-4 text-green-500" />
      ) : (
        <AlertCircle className="h-4 w-4 text-red-500" />
      )}
      <span className={`text-sm font-medium ${success ? "text-green-600" : "text-red-600"}`}>
        {success ? "Success" : "Error"}
      </span>
    </div>
  );
};

const TimestampRenderer = (params: ICellRendererParams<UserEngagementRow>) => {
  const raw = params.value as string | undefined;
  const ts = raw ? new Date(raw) : null;
  if (!ts || Number.isNaN(ts.getTime())) return <span>-</span>;
  return (
    <div className="text-sm md:text-base lg:text-lg">
      <div className="font-medium">{format(ts, "MMM dd, HH:mm:ss")}</div>
      <div className="text-muted-foreground text-xs sm:text-sm md:text-base">
        {formatDistanceToNow(ts, { addSuffix: true })}
      </div>
    </div>
  );
};

const UserRenderer = (params: ICellRendererParams<UserEngagementRow>) => {
  const userId = String(params.value ?? "");
  const shortId = userId ? userId.slice(0, 8) : "anonymous";
  return (
    <div className="flex items-center gap-2">
      <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center">
        <Users className="h-3 w-3" />
      </div>
      <span className="text-sm font-mono md:text-base lg:text-lg">{shortId}</span>
    </div>
  );
};

/* ------------------------------- Component ------------------------------- */

export const UserEngagementGrid: React.FC<UserEngagementGridProps> = ({
  data = [],
  onRowSelect,
  onExport,
  onRefresh,
  className = "",
}) => {
  const { user } = useAuth();
  const { triggerHooks, registerGridHook } = useHooks();
  const { toast } = useToast();

  const [searchText, setSearchText] = useState("");
  const [filterType, setFilterType] = useState<FilterType>("all");
  const [timeRange, setTimeRange] = useState<TimeRange>("24h");
  const [selectedRows, setSelectedRows] = useState<UserEngagementRow[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Generate sample data ONLY when no data prop is provided
  const engagementData: UserEngagementRow[] = useMemo(() => {
    if (data.length > 0) return data;

    const generated: UserEngagementRow[] = [];
    const components = ["chat", "analytics", "memory", "grid", "chart"];
    const interactions = ["click", "view", "hover", "input", "submit"];
    const users = ["user1", "user2", "user3", "user4"];

    for (let i = 0; i < 50; i++) {
      const ts = new Date(Date.now() - Math.random() * 24 * 60 * 60 * 1000);
      const componentType = components[Math.floor(Math.random() * components.length)];
      const interactionType = interactions[Math.floor(Math.random() * interactions.length)];
      const success = Math.random() > 0.1;

      generated.push({
        id: `engagement_${i}`,
        timestamp: ts.toISOString(),
        userId: users[Math.floor(Math.random() * users.length)],
        componentType,
        componentId: `${componentType}_${Math.floor(Math.random() * 100)}`,
        interactionType,
        duration: Math.floor(Math.random() * 15000) + 100,
        success,
        errorMessage: success ? undefined : "Component failed to load",
        sessionId: `session_${Math.floor(Math.random() * 10)}`,
        userAgent: "Mozilla/5.0 (Chrome)",
        location: "dashboard",
      });
    }

    return generated.sort(
      (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );
  }, [data]);

  // Column definitions
  const columnDefs: ColDef<UserEngagementRow>[] = useMemo(
    () => [
      {
        field: "timestamp",
        headerName: "Time",
        width: 180,
        sortable: true,
        filter: "agDateColumnFilter",
        cellRenderer: TimestampRenderer,
        sort: "desc",
      },
      {
        field: "userId",
        headerName: "User",
        width: 140,
        sortable: true,
        filter: "agTextColumnFilter",
        cellRenderer: UserRenderer,
      },
      {
        field: "componentType",
        headerName: "Component",
        width: 150,
        sortable: true,
        filter: "agSetColumnFilter",
        cellRenderer: ComponentTypeRenderer,
      },
      {
        field: "componentId",
        headerName: "Component ID",
        width: 160,
        sortable: true,
        filter: "agTextColumnFilter",
        cellStyle: { fontSize: "12px", fontFamily: "monospace" } as unknown,
      },
      {
        field: "interactionType",
        headerName: "Interaction",
        width: 140,
        sortable: true,
        filter: "agSetColumnFilter",
        cellRenderer: InteractionTypeRenderer,
      },
      {
        field: "duration",
        headerName: "Duration",
        width: 120,
        sortable: true,
        filter: "agNumberColumnFilter",
        cellRenderer: DurationRenderer,
      },
      {
        field: "success",
        headerName: "Status",
        width: 110,
        sortable: true,
        filter: "agSetColumnFilter",
        cellRenderer: SuccessRenderer,
      },
      {
        field: "errorMessage",
        headerName: "Error",
        width: 220,
        sortable: false,
        filter: "agTextColumnFilter",
        cellStyle: { color: "#ef4444", fontSize: "12px" } as unknown,
        valueFormatter: (p) => p.value ?? "-",
      },
      {
        field: "location",
        headerName: "Location",
        width: 140,
        sortable: true,
        filter: "agTextColumnFilter",
      },
    ],
    []
  );

  const defaultColDef = useMemo<ColDef<UserEngagementRow>>(
    () => ({
      resizable: true,
      sortable: true,
      filter: true,
      floatingFilter: true,
    }),
    []
  );

  // Filter + search + range
  const filteredData = useMemo(() => {
    let filtered = [...engagementData];

    // time window
    const now = Date.now();
    const rangeMs: Record<TimeRange, number> = {
      "1h": 60 * 60 * 1000,
      "24h": 24 * 60 * 60 * 1000,
      "7d": 7 * 24 * 60 * 60 * 1000,
      "30d": 30 * 24 * 60 * 60 * 1000,
    };
    const cutoff = now - rangeMs[timeRange];
    filtered = filtered.filter((r) => new Date(r.timestamp).getTime() > cutoff);

    // filter type
    if (filterType === "success") filtered = filtered.filter((r) => r.success);
    else if (filterType === "error") filtered = filtered.filter((r) => !r.success);
    else if (filterType === "recent") filtered = filtered.slice(0, 20);

    // search
    if (searchText.trim()) {
      const q = searchText.toLowerCase();
      filtered = filtered.filter(
        (r) =>
          r.userId.toLowerCase().includes(q) ||
          r.componentType.toLowerCase().includes(q) ||
          r.componentId.toLowerCase().includes(q) ||
          r.interactionType.toLowerCase().includes(q) ||
          (r.errorMessage && r.errorMessage.toLowerCase().includes(q))
      );
    }

    return filtered;
  }, [engagementData, searchText, filterType, timeRange]);

  // Grid hooks
  useEffect(() => {
    const ids: string[] = [];
    ids.push(
      registerGridHook("userEngagement", "dataLoad", async () => {
        return { success: true, rowCount: filteredData.length };
      })
    );
    ids.push(
      registerGridHook("userEngagement", "rowSelected", async (params) => {
        return { success: true, selectedRow: params.data };
      })
    );

    return () => {
      // If your hook context exposes an unregister, call it here.
      // Example: ids.forEach((id) => unregisterGridHook(id))
    };
  }, [registerGridHook, filteredData.length]);

  const onGridReady = useCallback(
    async (params: GridReadyEvent) => {
      await triggerHooks(
        "grid_userEngagement_dataLoad",
        {
          gridId: "userEngagement",
          api: params.api,
          rowCount: filteredData.length,
          filterType,
          timeRange,
        },
        { userId: user?.userId }
      );
    },
    [triggerHooks, filteredData.length, filterType, timeRange, user?.userId]
  );

  const onSelectionChanged = useCallback(
    async (event: Event) => {
      const selectedNodes = event.api.getSelectedNodes();
      const selectedData = selectedNodes.map((n: unknown) => n.data as UserEngagementRow);
      setSelectedRows(selectedData);

      if (selectedData.length > 0 && onRowSelect) {
        onRowSelect(selectedData[0]);
      }

      for (const row of selectedData) {
        await triggerHooks(
          "grid_userEngagement_rowSelected",
          { gridId: "userEngagement", data: row, api: event.api },
          { userId: user?.userId }
        );
      }
    },
    [triggerHooks, onRowSelect, user?.userId]
  );

  const handleExport = useCallback(async () => {
    if (!onExport) return;
    setIsLoading(true);
    try {
      await onExport(filteredData);
      toast({
        title: "Export Successful",
        description: `Exported ${filteredData.length} engagement records.`,
      });
    } catch (e) {
      toast({
        variant: "destructive",
        title: "Export Failed",
        description: "Failed to export engagement data. Please try again.",
      });
    } finally {
      setIsLoading(false);
    }
  }, [onExport, filteredData, toast]);

  const handleRefresh = useCallback(async () => {
    if (!onRefresh) return;
    setIsLoading(true);
    try {
      await onRefresh();
      toast({
        title: "Data Refreshed",
        description: "User engagement data has been updated.",
      });
    } catch (e) {
      toast({
        variant: "destructive",
        title: "Refresh Failed",
        description: "Failed to refresh engagement data. Please try again.",
      });
    } finally {
      setIsLoading(false);
    }
  }, [onRefresh, toast]);

  // Summary stats
  const summaryStats = useMemo(() => {
    if (filteredData.length === 0) return null;
    const total = filteredData.length;
    const successful = filteredData.filter((r) => r.success).length;
    const avgDuration = Math.round(
      filteredData.reduce((s, r) => s + r.duration, 0) / total
    );
    const uniqueUsers = new Set(filteredData.map((r) => r.userId)).size;

    const compCounts = filteredData.reduce<Record<string, number>>((acc, r) => {
      acc[r.componentType] = (acc[r.componentType] ?? 0) + 1;
      return acc;
    }, {});
    const topComponents = Object.entries(compCounts)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 3);

    return {
      totalInteractions: total,
      successRate: ((successful / total) * 100).toFixed(1),
      avgDuration,
      uniqueUsers,
      topComponents,
    };
  }, [filteredData]);

  return (
    <Card className={`w-full ${className}`}>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            User Engagement Analytics ({filteredData.length} records)
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleExport}
              disabled={isLoading || filteredData.length === 0}
              title="Export CSV/JSON"
            >
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={isLoading}
              title="Refresh data"
            >
              <Activity className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </div>
        </div>

        {/* Summary Statistics */}
        {summaryStats && (
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mt-4">
            <div className="p-3 bg-muted/50 rounded-lg sm:p-4 md:p-6">
              <div className="text-sm text-muted-foreground md:text-base lg:text-lg">
                Total Interactions
              </div>
              <div className="text-xl font-bold">{summaryStats.totalInteractions}</div>
            </div>
            <div className="p-3 bg-muted/50 rounded-lg sm:p-4 md:p-6">
              <div className="text-sm text-muted-foreground md:text-base lg:text-lg">
                Success Rate
              </div>
              <div className="text-xl font-bold text-green-600">
                {summaryStats.successRate}%
              </div>
            </div>
            <div className="p-3 bg-muted/50 rounded-lg sm:p-4 md:p-6">
              <div className="text-sm text-muted-foreground md:text-base lg:text-lg">
                Avg Duration
              </div>
              <div className="text-xl font-bold">{summaryStats.avgDuration}ms</div>
            </div>
            <div className="p-3 bg-muted/50 rounded-lg sm:p-4 md:p-6">
              <div className="text-sm text-muted-foreground md:text-base lg:text-lg">
                Unique Users
              </div>
              <div className="text-xl font-bold">{summaryStats.uniqueUsers}</div>
            </div>
            <div className="p-3 bg-muted/50 rounded-lg sm:p-4 md:p-6">
              <div className="text-sm text-muted-foreground md:text-base lg:text-lg">
                Top Component
              </div>
              <div className="text-lg font-bold">
                {summaryStats.topComponents[0]?.[0] ?? "N/A"}
              </div>
            </div>
          </div>
        )}

        {/* Filters and Search */}
        <div className="flex items-center gap-4 mt-4">
          <div className="relative flex-1 max-w-sm">
            <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search interactions..."
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              className="pl-10"
            />
          </div>

          <Select
            value={filterType}
            onValueChange={(v) => setFilterType(v as FilterType)}
          >
            <SelectTrigger className="w-44" aria-label="Filter interactions">
              <SelectValue placeholder="Filter" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Interactions</SelectItem>
              <SelectItem value="success">Successful Only</SelectItem>
              <SelectItem value="error">Errors Only</SelectItem>
              <SelectItem value="recent">Recent (20)</SelectItem>
            </SelectContent>
          </Select>

          <Select
            value={timeRange}
            onValueChange={(v) => setTimeRange(v as TimeRange)}
          >
            <SelectTrigger className="w-28" aria-label="Time range">
              <SelectValue placeholder="Range" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1h">1H</SelectItem>
              <SelectItem value="24h">24H</SelectItem>
              <SelectItem value="7d">7D</SelectItem>
              <SelectItem value="30d">30D</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {selectedRows.length > 0 && (
          <div className="flex items-center gap-2 mt-2">
            <Badge variant="secondary">{selectedRows.length} selected</Badge>
            <Button variant="outline" size="sm">Actions</Button>
          </div>
        )}
      </CardHeader>

      <CardContent className="p-0 sm:p-4 md:p-6">
        <div className="ag-theme-alpine h-[600px] w-full">
          <AgGridReact<UserEngagementRow>
            rowData={filteredData}
            columnDefs={columnDefs}
            defaultColDef={defaultColDef}
            onGridReady={onGridReady}
            onSelectionChanged={(e) => onSelectionChanged(e as unknown)}
            rowSelection="multiple"
            animateRows
            getRowId={(params) => params.data.id}
            pagination
            paginationPageSize={50}
            suppressRowClickSelection={false}
          />
        </div>
      </CardContent>
    </Card>
  );
};
