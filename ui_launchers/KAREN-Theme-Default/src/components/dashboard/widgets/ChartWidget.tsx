// ui_launchers/KAREN-Theme-Default/src/components/dashboard/widgets/ChartWidget.tsx
"use client";

import React, { useMemo, useCallback, useRef } from "react";
import { AgCharts } from "ag-charts-react";
import type { AgChartOptions } from "ag-charts-community";
import { WidgetBase } from "../WidgetBase";
import { Button } from "@/components/ui/button";

import {
  TrendingUp,
  BarChart3,
  Activity,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Download,
} from "lucide-react";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";

import type { WidgetProps, ChartData } from "@/types/dashboard";

interface ChartWidgetProps extends WidgetProps {
  data?: {
    id: string;
    data: ChartData;
    loading: boolean;
    error?: string;
    lastUpdated: Date;
  };
}

const getChartTypeIcon = (type: string) => {
  switch (type) {
    case "line":
      return <TrendingUp className="h-3 w-3" />;
    case "bar":
      return <BarChart3 className="h-3 w-3" />;
    case "area":
      return <Activity className="h-3 w-3" />;
    default:
      return <TrendingUp className="h-3 w-3" />;
  }
};

export const ChartWidget: React.FC<ChartWidgetProps> = (props) => {
  const { data: widgetData } = props;

  // Keep a ref to the latest options in case you want to wire programmatic actions later
  const optionsRef = useRef<AgChartOptions | null>(null);

  const chartOptions = useMemo<AgChartOptions>(() => {
    if (!widgetData?.data) {
      const opts: AgChartOptions = { data: [], series: [] };
      optionsRef.current = opts;
      return opts;
    }

    const chartData = widgetData.data;

    // Build a unified data table where each row contains x and each series' y value
    const baseSeries = chartData.series?.[0];
    const transformedData =
      baseSeries?.data.map((pt) => {
        const xIsTime = chartData.xAxis?.type === "time";
        const xValue = xIsTime ? new Date(pt.x) : pt.x;

        const yValues = (chartData.series || []).reduce(
          (acc, s) => {
            const match = s.data.find((d) =>
              chartData.xAxis?.type === "time"
                ? new Date(d.x).getTime() === new Date(pt.x).getTime()
                : d.x === pt.x
            );
            acc[s.name] = typeof match?.y === "number" ? match.y : 0;
            return acc;
          },
          {} as Record<string, number>
        );

        return { x: xValue, ...yValues };
      }) ?? [];

    // Build AG Charts series config from our ChartData series
    const series = (chartData.series || []).map((s) => {
      const base = {
        xKey: "x",
        yKey: s.name,
        yName: s.name,
      };
      switch (s.type) {
        case "bar":
          return {
            ...base,
            type: "bar" as const,
          };
        case "area":
          return {
            ...base,
            type: "area" as const,
            fillOpacity: 0.3,
          };
        case "line":
        default:
          return {
            ...base,
            type: "line" as const,
            marker: {
              enabled: transformedData.length <= 50,
            },
          };
      }
    });

    const xAxisType =
      chartData.xAxis?.type === "time"
        ? "time"
        : chartData.xAxis?.type === "number"
        ? "number"
        : "category";

    const opts: AgChartOptions = {
      data: transformedData,
      series,
      axes: [
        {
          type: xAxisType as any,
          position: "bottom",
          title: { text: chartData.xAxis?.label || "" },
          ...(xAxisType === "time" && {
            tick: { count: 10 },
            label: { format: "%H:%M" },
          }),
        } as any,
        {
          type: "number",
          position: "left",
          title: { text: chartData.yAxis?.label || "" },
          ...(chartData.yAxis?.min !== undefined && { min: chartData.yAxis.min }),
          ...(chartData.yAxis?.max !== undefined && { max: chartData.yAxis.max }),
        },
      ],
      legend: {
        enabled: (chartData.series?.length || 0) > 1,
        position: "bottom",
      },
      tooltip: { enabled: true },
      zoom: { enabled: true, axes: "x" },
      animation: { enabled: true },
      theme: {
        baseTheme: "ag-default",
        palette: {
          fills: ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"],
          strokes: ["#2563eb", "#059669", "#d97706", "#dc2626", "#7c3aed", "#0891b2"],
        },
      },
    };

    optionsRef.current = opts;
    return opts;
  }, [widgetData?.data]);

  /* ---------- Controls (graceful fallbacks) ---------- */
  const handleExport = useCallback((format: "png" | "svg" | "pdf") => {
    // AG Charts programmatic export is enterprise-only; keep graceful placeholder.
    // Wire to server/client export pipeline here if licensed/enabled.
    // eslint-disable-next-line no-console
    console.info(`[ChartWidget] Export requested: ${format}`);
  }, []);

  const handleZoomIn = useCallback(() => {
    // Requires chart instance API; provide a safe placeholder for now.
    // eslint-disable-next-line no-console
    console.info("[ChartWidget] Zoom In");
  }, []);

  const handleZoomOut = useCallback(() => {
    // eslint-disable-next-line no-console
    console.info("[ChartWidget] Zoom Out");
  }, []);

  const handleResetZoom = useCallback(() => {
    // eslint-disable-next-line no-console
    console.info("[ChartWidget] Reset Zoom");
  }, []);

  const handleChangeChartType = useCallback((type: "line" | "bar" | "area") => {
    // In a future enhancement, you can lift state up and regenerate `chartOptions.series`.
    // eslint-disable-next-line no-console
    console.info("[ChartWidget] Change type ->", type);
  }, []);

  /* ---------- Empty / Error / Loading states ---------- */
  if (!widgetData?.data) {
    return (
      <WidgetBase {...props}>
        <div className="flex items-center justify-center h-full text-muted-foreground">
          No data
        </div>
      </WidgetBase>
    );
  }

  if (widgetData.loading) {
    return (
      <WidgetBase {...props}>
        <div className="flex items-center justify-center h-full text-muted-foreground">
          Loading chart…
        </div>
      </WidgetBase>
    );
  }

  if (widgetData.error) {
    return (
      <WidgetBase {...props}>
        <div className="flex items-center justify-center h-full text-red-600">
          {widgetData.error}
        </div>
      </WidgetBase>
    );
  }

  /* ---------- Render ---------- */
  return (
    <WidgetBase {...props} className="relative">
      {/* Chart Controls */}
      <div className="absolute top-2 right-2 z-10 flex gap-1">
        {/* Chart Type Selector */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              aria-label="Change chart type"
              className="h-6 w-6 p-0 bg-background/80 backdrop-blur-sm"
            >
              {getChartTypeIcon(widgetData.data.series[0]?.type || "line")}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-36">
            <DropdownMenuItem onClick={() => handleChangeChartType("line")}>
              <TrendingUp className="h-3 w-3 mr-2" />
              Line
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleChangeChartType("bar")}>
              <BarChart3 className="h-3 w-3 mr-2" />
              Bar
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleChangeChartType("area")}>
              <Activity className="h-3 w-3 mr-2" />
              Area
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Zoom Controls */}
        <Button
          variant="ghost"
          size="sm"
          onClick={handleZoomIn}
          aria-label="Zoom in"
          className="h-6 w-6 p-0 bg-background/80 backdrop-blur-sm"
        >
          <ZoomIn className="h-3 w-3" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleZoomOut}
          aria-label="Zoom out"
          className="h-6 w-6 p-0 bg-background/80 backdrop-blur-sm"
        >
          <ZoomOut className="h-3 w-3" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleResetZoom}
          aria-label="Reset zoom"
          className="h-6 w-6 p-0 bg-background/80 backdrop-blur-sm"
        >
          <RotateCcw className="h-3 w-3" />
        </Button>

        {/* Export Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              aria-label="Export chart"
              className="h-6 w-6 p-0 bg-background/80 backdrop-blur-sm"
            >
              <Download className="h-3 w-3" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-36">
            <DropdownMenuItem onClick={() => handleExport("png")}>
              PNG
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleExport("svg")}>
              SVG
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => handleExport("pdf")}>
              PDF
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Chart Container */}
      <div className="h-full w-full pt-8">
        <AgCharts options={chartOptions} />
      </div>

      {/* Chart Summary */}
      {widgetData.data.series.length > 0 && (
        <div className="absolute bottom-2 left-2 right-2 bg-background/80 backdrop-blur-sm rounded px-2 py-1">
          <div className="flex items-center justify-between text-xs text-muted-foreground sm:text-sm md:text-base">
            <span>
              {widgetData.data.series.length} series,{" "}
              {widgetData.data.series[0]?.data.length || 0} points
            </span>
            <span>
              {widgetData.data.xAxis?.type === "time" ? "Time Series" : "Data Series"}
            </span>
          </div>
        </div>
      )}
    </WidgetBase>
  );
};

export default ChartWidget;
