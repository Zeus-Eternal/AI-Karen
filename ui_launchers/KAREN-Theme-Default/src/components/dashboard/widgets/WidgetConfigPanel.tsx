// ui_launchers/KAREN-Theme-Default/src/components/dashboard/widgets/WidgetConfigPanel.tsx
"use client";

import React, { useCallback, useMemo, useEffect } from "react";
import { useForm, type FieldPath, type Resolver } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";

import {
  Select,
  SelectTrigger,
  SelectContent,
  SelectItem,
  SelectValue,
} from "@/components/ui/select";

import type { WidgetConfig, WidgetType } from "@/types/dashboard";

/* -------------------------------- Schemas ------------------------------- */

const baseWidgetSchema = z.object({
  title: z.string().min(1, "Title is required"),
  size: z.enum(["small", "medium", "large", "full"]),
  refreshInterval: z.number().min(1000).max(300000).optional(),
  enabled: z.boolean(),
  type: z.custom<WidgetType>(),
});

const metricWidgetSchema = baseWidgetSchema.extend({
  config: z.object({
    dataSource: z.string().min(1, "Data source is required"),
    metric: z.string().min(1, "Metric is required"),
    format: z.enum(["number", "percentage", "currency", "bytes"]).optional(),
    unit: z.string().optional(),
    thresholds: z
      .object({
        warning: z.number().optional(),
        critical: z.number().optional(),
      })
      .optional(),
    showTrend: z.boolean().default(true),
  }),
});

const statusWidgetSchema = baseWidgetSchema.extend({
  config: z.object({
    service: z.string().min(1, "Service is required"),
    endpoint: z.string().url("Must be a valid URL").optional(),
    checkInterval: z.number().min(5000).max(300000).default(30000),
    showDetails: z.boolean().default(true),
    showHistory: z.boolean().default(true),
  }),
});

const chartWidgetSchema = baseWidgetSchema.extend({
  config: z.object({
    dataSource: z.string().min(1, "Data source is required"),
    chartType: z.enum(["line", "bar", "area"]).default("line"),
    timeRange: z.enum(["1h", "6h", "24h", "7d", "30d"]).default("24h"),
    series: z.array(z.string()).min(1, "At least one series is required"),
    showLegend: z.boolean().default(true),
    enableZoom: z.boolean().default(true),
  }),
});

const logWidgetSchema = baseWidgetSchema.extend({
  config: z.object({
    logSource: z.string().min(1, "Log source is required"),
    levels: z.array(z.enum(["info", "warn", "error", "debug"])).default(["warn", "error"]),
    maxEntries: z.number().min(50).max(1000).default(200),
    autoScroll: z.boolean().default(true),
    showMetadata: z.boolean().default(false),
  }),
});

const getSchemaForType = (type: WidgetType) => {
  switch (type) {
    case "metric":
      return metricWidgetSchema;
    case "status":
      return statusWidgetSchema;
    case "chart":
      return chartWidgetSchema;
    case "log":
      return logWidgetSchema;
    default:
      return baseWidgetSchema;
  }
};

const toStringValue = (value: unknown) =>
  typeof value === "string" ? value : value == null ? "" : String(value);

const toStringArray = (value: unknown): string[] =>
  Array.isArray(value)
    ? value
    : typeof value === "string"
    ? value
        .split("\n")
        .map((entry) => entry.trim())
        .filter(Boolean)
    : [];

/* ---------------------------- Component ---------------------------- */

interface WidgetConfigPanelProps {
  isOpen: boolean;
  onClose: () => void;
  config: WidgetConfig;
  onSave: (config: WidgetConfig) => void;
  onPreview?: (config: WidgetConfig) => void;
}

type WidgetConfigFieldPath = FieldPath<WidgetConfig>;

export const WidgetConfigPanel: React.FC<WidgetConfigPanelProps> = ({
  isOpen,
  onClose,
  config,
  onSave,
  onPreview,
}) => {

  const schema = useMemo(() => getSchemaForType(config.type), [config.type]);
  const resolver = zodResolver(schema) as unknown as Resolver<WidgetConfig>;

  const form = useForm<WidgetConfig>({
    resolver,
    defaultValues: config,
    mode: "onChange",
  });

  const handleSave = useCallback(
    (data: WidgetConfig) => {
      onSave(data);
      onClose();
    },
    [onSave, onClose]
  );

  const handlePreview = useCallback(() => {
    const formData = form.getValues();
    onPreview?.(formData);
  }, [form, onPreview]);

  // Accessibility: ESC to close when open
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose?.();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  /* -------------------- Type-specific Fields --------------------- */

  const renderMetric = () => (
    <>
      <FormField
        control={form.control}
        name={"config.dataSource" as WidgetConfigFieldPath}
        render={({ field }) => (
          <FormItem>
            <FormLabel>Data Source</FormLabel>
            <Select value={toStringValue(field.value)} onValueChange={field.onChange}>
              <FormControl>
                <SelectTrigger>
                  <SelectValue placeholder="Select data source" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                <SelectItem value="system-metrics">System Metrics</SelectItem>
                <SelectItem value="application-metrics">Application Metrics</SelectItem>
                <SelectItem value="custom-metrics">Custom Metrics</SelectItem>
              </SelectContent>
            </Select>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name={"config.metric" as WidgetConfigFieldPath}
        render={({ field }) => (
          <FormItem>
            <FormLabel>Metric</FormLabel>
            <FormControl>
              <Input
                placeholder="e.g., cpu_usage, memory_usage"
                value={toStringValue(field.value)}
                onChange={(e) => field.onChange(e.target.value)}
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name={"config.format" as WidgetConfigFieldPath}
        render={({ field }) => (
          <FormItem>
            <FormLabel>Format</FormLabel>
            <Select value={toStringValue(field.value)} onValueChange={field.onChange}>
              <FormControl>
                <SelectTrigger>
                  <SelectValue placeholder="Select format" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                <SelectItem value="number">Number</SelectItem>
                <SelectItem value="percentage">Percentage</SelectItem>
                <SelectItem value="currency">Currency</SelectItem>
                <SelectItem value="bytes">Bytes</SelectItem>
              </SelectContent>
            </Select>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name={"config.unit" as WidgetConfigFieldPath}
        render={({ field }) => (
          <FormItem>
            <FormLabel>Unit (Optional)</FormLabel>
            <FormControl>
              <Input
                placeholder="e.g., ms, req/s"
                value={toStringValue(field.value)}
                onChange={(e) => field.onChange(e.target.value)}
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <div className="space-y-4">
        <FormLabel>Thresholds</FormLabel>
        <div className="grid grid-cols-2 gap-4">
          <FormField
            control={form.control}
            name={"config.thresholds.warning" as WidgetConfigFieldPath}
            render={({ field }) => (
              <FormItem>
                <FormLabel>Warning</FormLabel>
                <FormControl>
                  <Input
                    type="number"
                    placeholder="Warning threshold"
                    value={field.value != null ? String(field.value) : ""}
                    onChange={(e) =>
                      field.onChange(e.target.value ? Number(e.target.value) : undefined)
                    }
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name={"config.thresholds.critical" as WidgetConfigFieldPath}
            render={({ field }) => (
              <FormItem>
                <FormLabel>Critical</FormLabel>
                <FormControl>
                  <Input
                    type="number"
                    placeholder="Critical threshold"
                    value={field.value != null ? String(field.value) : ""}
                    onChange={(e) =>
                      field.onChange(e.target.value ? Number(e.target.value) : undefined)
                    }
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>
      </div>
      <FormField
        control={form.control}
        name={"config.showTrend" as WidgetConfigFieldPath}
        render={({ field }) => (
          <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
            <div className="space-y-0.5">
              <FormLabel className="text-base">Show Trend</FormLabel>
              <FormDescription>Display sparkline or trend indicator.</FormDescription>
            </div>
            <FormControl>
              <Switch checked={Boolean(field.value)} onCheckedChange={(value) => field.onChange(value)} />
            </FormControl>
          </FormItem>
        )}
      />
    </>
  );

  const renderStatus = () => (
    <>
      <FormField
        control={form.control}
        name={"config.service" as WidgetConfigFieldPath}
        render={({ field }) => (
          <FormItem>
            <FormLabel>Service</FormLabel>
            <Select value={toStringValue(field.value)} onValueChange={field.onChange}>
              <FormControl>
                <SelectTrigger>
                  <SelectValue placeholder="Select service" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                <SelectItem value="api-server">API Server</SelectItem>
                <SelectItem value="database">Database</SelectItem>
                <SelectItem value="cache">Cache</SelectItem>
                <SelectItem value="message-queue">Message Queue</SelectItem>
              </SelectContent>
            </Select>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name={"config.endpoint" as WidgetConfigFieldPath}
        render={({ field }) => (
          <FormItem>
            <FormLabel>Health Check Endpoint (Optional)</FormLabel>
            <FormControl>
              <Input
                placeholder="https://api.example.com/health"
                value={toStringValue(field.value)}
                onChange={(e) => field.onChange(e.target.value)}
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name={"config.checkInterval" as WidgetConfigFieldPath}
        render={({ field }) => (
          <FormItem>
            <FormLabel>Check Interval (ms)</FormLabel>
            <FormControl>
              <div className="space-y-2">
                {(() => {
                  const interval = typeof field.value === "number" ? field.value : 30000;
                  return (
                    <>
                      <Slider
                        min={5000}
                        max={300000}
                        step={5000}
                        value={[interval]}
                        onValueChange={(value) => field.onChange(value[0])}
                      />
                      <div className="text-sm text-muted-foreground">
                        {(interval / 1000).toFixed(0)} seconds
                      </div>
                    </>
                  );
                })()}
              </div>
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name={"config.showDetails" as WidgetConfigFieldPath}
        render={({ field }) => (
          <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
            <div className="space-y-0.5">
              <FormLabel className="text-base">Show Details</FormLabel>
            </div>
            <FormControl>
              <Switch checked={Boolean(field.value)} onCheckedChange={(value) => field.onChange(value)} />
            </FormControl>
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name={"config.showHistory" as WidgetConfigFieldPath}
        render={({ field }) => (
          <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
            <div className="space-y-0.5">
              <FormLabel className="text-base">Show History</FormLabel>
            </div>
            <FormControl>
              <Switch checked={Boolean(field.value)} onCheckedChange={(value) => field.onChange(value)} />
            </FormControl>
          </FormItem>
        )}
      />
    </>
  );

  const renderChart = () => (
    <>
      <FormField
        control={form.control}
        name={"config.dataSource" as WidgetConfigFieldPath}
        render={({ field }) => (
          <FormItem>
            <FormLabel>Data Source</FormLabel>
            <Select value={toStringValue(field.value)} onValueChange={field.onChange}>
              <FormControl>
                <SelectTrigger>
                  <SelectValue placeholder="Select data source" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                <SelectItem value="metrics-api">Metrics API</SelectItem>
                <SelectItem value="logs-api">Logs API</SelectItem>
                <SelectItem value="custom-api">Custom API</SelectItem>
              </SelectContent>
            </Select>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name={"config.chartType" as WidgetConfigFieldPath}
        render={({ field }) => (
          <FormItem>
            <FormLabel>Chart Type</FormLabel>
            <Select value={toStringValue(field.value)} onValueChange={field.onChange}>
              <FormControl>
                <SelectTrigger>
                  <SelectValue placeholder="Select chart type" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                <SelectItem value="line">Line</SelectItem>
                <SelectItem value="bar">Bar</SelectItem>
                <SelectItem value="area">Area</SelectItem>
              </SelectContent>
            </Select>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name={"config.timeRange" as WidgetConfigFieldPath}
        render={({ field }) => (
          <FormItem>
            <FormLabel>Time Range</FormLabel>
            <Select value={toStringValue(field.value)} onValueChange={field.onChange}>
              <FormControl>
                <SelectTrigger>
                  <SelectValue placeholder="Select time range" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                <SelectItem value="1h">Last Hour</SelectItem>
                <SelectItem value="6h">Last 6 Hours</SelectItem>
                <SelectItem value="24h">Last 24 Hours</SelectItem>
                <SelectItem value="7d">Last 7 Days</SelectItem>
                <SelectItem value="30d">Last 30 Days</SelectItem>
              </SelectContent>
            </Select>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name={"config.series" as WidgetConfigFieldPath}
        render={({ field }) => (
          <FormItem>
            <FormLabel>Data Series</FormLabel>
            <FormControl>
              {(() => {
                const seriesValue = toStringArray(field.value);
                return (
                  <Textarea
                    placeholder="Enter series names, one per line"
                    value={seriesValue.join("\n")}
                    onChange={(e) =>
                      field.onChange(
                        e.target.value
                          .split("\n")
                          .map((s) => s.trim())
                          .filter(Boolean)
                      )
                    }
                  />
                );
              })()}
            </FormControl>
            <FormDescription>Each line becomes a separate series.</FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name={"config.showLegend" as WidgetConfigFieldPath}
        render={({ field }) => (
          <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
            <div className="space-y-0.5">
              <FormLabel className="text-base">Show Legend</FormLabel>
            </div>
            <FormControl>
              <Switch checked={Boolean(field.value)} onCheckedChange={(value) => field.onChange(value)} />
            </FormControl>
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name={"config.enableZoom" as WidgetConfigFieldPath}
        render={({ field }) => (
          <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
            <div className="space-y-0.5">
              <FormLabel className="text-base">Enable Zoom</FormLabel>
            </div>
            <FormControl>
              <Switch checked={Boolean(field.value)} onCheckedChange={(value) => field.onChange(value)} />
            </FormControl>
          </FormItem>
        )}
      />
    </>
  );

  const renderLog = () => {
    const LEVELS = ["info", "warn", "error", "debug"] as const;
    return (
      <>
        <FormField
          control={form.control}
          name={"config.logSource" as WidgetConfigFieldPath}
          render={({ field }) => (
            <FormItem>
              <FormLabel>Log Source</FormLabel>
              <Select value={toStringValue(field.value)} onValueChange={field.onChange}>
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder="Select log source" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  <SelectItem value="application">Application Logs</SelectItem>
                  <SelectItem value="system">System Logs</SelectItem>
                  <SelectItem value="security">Security Logs</SelectItem>
                  <SelectItem value="audit">Audit Logs</SelectItem>
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name={"config.levels" as WidgetConfigFieldPath}
          render={({ field }) => (
            <FormItem>
              <FormLabel>Log Levels</FormLabel>
              <div className="flex flex-wrap gap-2">
                {LEVELS.map((level) => {
                  const selectedLevels = Array.isArray(field.value) ? field.value : [];
                  const active = selectedLevels.includes(level);
                  return (
                    <Badge
                      key={level}
                      variant={active ? "default" : "outline"}
                      className="cursor-pointer"
                      onClick={() => {
                        const set = new Set<string>(selectedLevels);
                        if (set.has(level)) set.delete(level);
                        else set.add(level);
                        field.onChange(Array.from(set));
                      }}
                    >
                      {level.toUpperCase()}
                    </Badge>
                  );
                })}
              </div>
              <FormDescription>Select one or more severity levels.</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name={"config.maxEntries" as WidgetConfigFieldPath}
          render={({ field }) => (
            <FormItem>
              <FormLabel>Max Entries</FormLabel>
              <FormControl>
                <div className="space-y-2">
                  {(() => {
                    const entries = typeof field.value === "number" ? field.value : 200;
                    return (
                      <>
                        <Slider
                          min={50}
                          max={1000}
                          step={50}
                          value={[entries]}
                          onValueChange={(value) => field.onChange(value[0])}
                        />
                        <div className="text-sm text-muted-foreground">{entries} entries</div>
                      </>
                    );
                  })()}
                </div>
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name={"config.autoScroll" as WidgetConfigFieldPath}
          render={({ field }) => (
            <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
              <div className="space-y-0.5">
                <FormLabel className="text-base">Auto Scroll</FormLabel>
              </div>
              <FormControl>
                <Switch checked={Boolean(field.value)} onCheckedChange={(value) => field.onChange(value)} />
              </FormControl>
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name={"config.showMetadata" as WidgetConfigFieldPath}
          render={({ field }) => (
            <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
              <div className="space-y-0.5">
                <FormLabel className="text-base">Show Metadata</FormLabel>
              </div>
              <FormControl>
                <Switch checked={Boolean(field.value)} onCheckedChange={(value) => field.onChange(value)} />
              </FormControl>
            </FormItem>
          )}
        />
      </>
    );
  };

  const renderTypeSpecificFields = () => {
    switch (config.type) {
      case "metric":
        return renderMetric();
      case "status":
        return renderStatus();
      case "chart":
        return renderChart();
      case "log":
        return renderLog();
      default:
        return null;
    }
  };

  /* -------------------------------- JSX ------------------------------- */

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Configure Widget</DialogTitle>
          <DialogDescription>
            Customize the settings for your <b>{config.type}</b> widget.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSave)} className="space-y-6">
            {/* Basic Settings */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium">Basic Settings</h3>

              <FormField
                control={form.control}
                name="title"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Title</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="Widget title"
                        value={toStringValue(field.value)}
                        onChange={(e) => field.onChange(e.target.value)}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="size"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Size</FormLabel>
                    <Select value={toStringValue(field.value)} onValueChange={field.onChange}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select size" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="small">Small (1x1)</SelectItem>
                        <SelectItem value="medium">Medium (2x1)</SelectItem>
                        <SelectItem value="large">Large (2x2)</SelectItem>
                        <SelectItem value="full">Full Width</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="refreshInterval"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Refresh Interval (ms)</FormLabel>
                    <FormControl>
              <div className="space-y-2">
                {(() => {
                  const refresh = typeof field.value === "number" ? field.value : 30000;
                  return (
                    <>
                      <Slider
                        min={1000}
                        max={300000}
                        step={1000}
                        value={[refresh]}
                        onValueChange={(value) => field.onChange(value[0])}
                      />
                      <div className="text-sm text-muted-foreground">
                        {(refresh / 1000).toFixed(0)} seconds
                      </div>
                    </>
                  );
                })()}
              </div>
            </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="enabled"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                    <div className="space-y-0.5">
                      <FormLabel className="text-base">Enabled</FormLabel>
                    </div>
                    <FormControl>
                      <Switch checked={Boolean(field.value)} onCheckedChange={(value) => field.onChange(value)} />
                    </FormControl>
                  </FormItem>
                )}
              />
            </div>

            <Separator />

            {/* Type-specific Settings */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium">Widget Settings</h3>
              {renderTypeSpecificFields()}
            </div>

            <DialogFooter className="gap-2">
              <Button type="button" variant="outline" onClick={onClose}>
                Cancel
              </Button>
              {onPreview && (
                <Button type="button" variant="outline" onClick={handlePreview}>
                  Preview
                </Button>
              )}
              <Button type="submit">Save</Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
};

export default WidgetConfigPanel;
