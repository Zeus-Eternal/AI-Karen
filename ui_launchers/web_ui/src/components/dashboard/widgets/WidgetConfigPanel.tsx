'use client';

import React, { useState, useCallback } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import type { WidgetConfig, WidgetType } from '@/types/dashboard';

interface WidgetConfigPanelProps {
  isOpen: boolean;
  onClose: () => void;
  config: WidgetConfig;
  onSave: (config: WidgetConfig) => void;
  onPreview?: (config: WidgetConfig) => void;
}

// Base schema for all widgets
const baseWidgetSchema = z.object({
  title: z.string().min(1, 'Title is required'),
  size: z.enum(['small', 'medium', 'large', 'full']),
  refreshInterval: z.number().min(1000).max(300000).optional(),
  enabled: z.boolean(),
});

// Widget-specific schemas
const metricWidgetSchema = baseWidgetSchema.extend({
  config: z.object({
    dataSource: z.string().min(1, 'Data source is required'),
    metric: z.string().min(1, 'Metric is required'),
    format: z.enum(['number', 'percentage', 'currency', 'bytes']).optional(),
    unit: z.string().optional(),
    thresholds: z.object({
      warning: z.number().optional(),
      critical: z.number().optional(),
    }).optional(),
    showTrend: z.boolean().default(true),
  }),
});

const statusWidgetSchema = baseWidgetSchema.extend({
  config: z.object({
    service: z.string().min(1, 'Service is required'),
    endpoint: z.string().url('Must be a valid URL').optional(),
    checkInterval: z.number().min(5000).max(300000).default(30000),
    showDetails: z.boolean().default(true),
    showHistory: z.boolean().default(true),
  }),
});

const chartWidgetSchema = baseWidgetSchema.extend({
  config: z.object({
    dataSource: z.string().min(1, 'Data source is required'),
    chartType: z.enum(['line', 'bar', 'area']).default('line'),
    timeRange: z.enum(['1h', '6h', '24h', '7d', '30d']).default('24h'),
    series: z.array(z.string()).min(1, 'At least one series is required'),
    showLegend: z.boolean().default(true),
    enableZoom: z.boolean().default(true),
  }),
});

const logWidgetSchema = baseWidgetSchema.extend({
  config: z.object({
    logSource: z.string().min(1, 'Log source is required'),
    levels: z.array(z.enum(['debug', 'info', 'warn', 'error'])).default(['info', 'warn', 'error']),
    maxEntries: z.number().min(50).max(1000).default(200),
    autoScroll: z.boolean().default(true),
    showMetadata: z.boolean().default(false),
  }),
});

const getSchemaForType = (type: WidgetType) => {
  switch (type) {
    case 'metric':
      return metricWidgetSchema;
    case 'status':
      return statusWidgetSchema;
    case 'chart':
      return chartWidgetSchema;
    case 'log':
      return logWidgetSchema;
    default:
      return baseWidgetSchema;
  }
};

export const WidgetConfigPanel: React.FC<WidgetConfigPanelProps> = ({
  isOpen,
  onClose,
  config,
  onSave,
  onPreview,
}) => {
  const [isPreviewMode, setIsPreviewMode] = useState(false);
  
  const schema = getSchemaForType(config.type);
  
  const form = useForm<WidgetConfig>({
    resolver: zodResolver(schema),
    defaultValues: config,
  });

  const handleSave = useCallback((data: WidgetConfig) => {
    onSave(data);
    onClose();
  }, [onSave, onClose]);

  const handlePreview = useCallback(() => {
    const formData = form.getValues();
    if (onPreview) {
      onPreview(formData);
      setIsPreviewMode(true);
    }
  }, [form, onPreview]);

  const renderTypeSpecificFields = () => {
    switch (config.type) {
      case 'metric':
        return (
          <>
            <FormField
              control={form.control}
              name="config.dataSource"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Data Source</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
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
              name="config.metric"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Metric</FormLabel>
                  <FormControl>
                    <Input placeholder="e.g., cpu_usage, memory_usage" {...field} />
                  </FormControl>
                  <FormDescription>
                    The specific metric to display
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="config.format"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Format</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
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
              name="config.unit"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Unit (Optional)</FormLabel>
                  <FormControl>
                    <Input placeholder="e.g., ms, req/s" {...field} />
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
                  name="config.thresholds.warning"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Warning</FormLabel>
                      <FormControl>
                        <Input 
                          type="number" 
                          placeholder="Warning threshold"
                          {...field}
                          onChange={(e) => field.onChange(e.target.value ? Number(e.target.value) : undefined)}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="config.thresholds.critical"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Critical</FormLabel>
                      <FormControl>
                        <Input 
                          type="number" 
                          placeholder="Critical threshold"
                          {...field}
                          onChange={(e) => field.onChange(e.target.value ? Number(e.target.value) : undefined)}
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
              name="config.showTrend"
              render={({ field }) => (
                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                  <div className="space-y-0.5">
                    <FormLabel className="text-base">Show Trend</FormLabel>
                    <FormDescription>
                      Display trend indicators and percentage changes
                    </FormDescription>
                  </div>
                  <FormControl>
                    <Switch
                      checked={field.value}
                      onCheckedChange={field.onChange}
                    />
                  </FormControl>
                </FormItem>
              )}
            />
          </>
        );

      case 'status':
        return (
          <>
            <FormField
              control={form.control}
              name="config.service"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Service</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
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
              name="config.endpoint"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Health Check Endpoint (Optional)</FormLabel>
                  <FormControl>
                    <Input placeholder="https://api.example.com/health" {...field} />
                  </FormControl>
                  <FormDescription>
                    Custom endpoint for health checks
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="config.checkInterval"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Check Interval (ms)</FormLabel>
                  <FormControl>
                    <div className="space-y-2">
                      <Slider
                        min={5000}
                        max={300000}
                        step={5000}
                        value={[field.value]}
                        onValueChange={(value) => field.onChange(value[0])}
                      />
                      <div className="text-sm text-muted-foreground">
                        {(field.value / 1000).toFixed(0)} seconds
                      </div>
                    </div>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="config.showDetails"
              render={({ field }) => (
                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                  <div className="space-y-0.5">
                    <FormLabel className="text-base">Show Details</FormLabel>
                    <FormDescription>
                      Display additional service details
                    </FormDescription>
                  </div>
                  <FormControl>
                    <Switch
                      checked={field.value}
                      onCheckedChange={field.onChange}
                    />
                  </FormControl>
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="config.showHistory"
              render={({ field }) => (
                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                  <div className="space-y-0.5">
                    <FormLabel className="text-base">Show History</FormLabel>
                    <FormDescription>
                      Display status history indicators
                    </FormDescription>
                  </div>
                  <FormControl>
                    <Switch
                      checked={field.value}
                      onCheckedChange={field.onChange}
                    />
                  </FormControl>
                </FormItem>
              )}
            />
          </>
        );

      case 'chart':
        return (
          <>
            <FormField
              control={form.control}
              name="config.dataSource"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Data Source</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
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
              name="config.chartType"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Chart Type</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select chart type" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="line">Line Chart</SelectItem>
                      <SelectItem value="bar">Bar Chart</SelectItem>
                      <SelectItem value="area">Area Chart</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="config.timeRange"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Time Range</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
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
              name="config.series"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Data Series</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Enter series names, one per line"
                      value={field.value?.join('\n') || ''}
                      onChange={(e) => field.onChange(e.target.value.split('\n').filter(Boolean))}
                    />
                  </FormControl>
                  <FormDescription>
                    Enter each data series on a new line
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="config.showLegend"
              render={({ field }) => (
                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                  <div className="space-y-0.5">
                    <FormLabel className="text-base">Show Legend</FormLabel>
                    <FormDescription>
                      Display chart legend
                    </FormDescription>
                  </div>
                  <FormControl>
                    <Switch
                      checked={field.value}
                      onCheckedChange={field.onChange}
                    />
                  </FormControl>
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="config.enableZoom"
              render={({ field }) => (
                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                  <div className="space-y-0.5">
                    <FormLabel className="text-base">Enable Zoom</FormLabel>
                    <FormDescription>
                      Allow zooming and panning
                    </FormDescription>
                  </div>
                  <FormControl>
                    <Switch
                      checked={field.value}
                      onCheckedChange={field.onChange}
                    />
                  </FormControl>
                </FormItem>
              )}
            />
          </>
        );

      case 'log':
        return (
          <>
            <FormField
              control={form.control}
              name="config.logSource"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Log Source</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
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
              name="config.levels"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Log Levels</FormLabel>
                  <div className="flex flex-wrap gap-2">
                    {['debug', 'info', 'warn', 'error'].map((level) => (
                      <Badge
                        key={level}
                        variant={field.value?.includes(level as any) ? 'default' : 'outline'}
                        className="cursor-pointer"
                        onClick={() => {
                          const currentLevels = field.value || [];
                          if (currentLevels.includes(level as any)) {
                            field.onChange(currentLevels.filter(l => l !== level));
                          } else {
                            field.onChange([...currentLevels, level]);
                          }
                        }}
                      >
                        {level.toUpperCase()}
                      </Badge>
                    ))}
                  </div>
                  <FormDescription>
                    Click to toggle log levels
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="config.maxEntries"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Max Entries</FormLabel>
                  <FormControl>
                    <div className="space-y-2">
                      <Slider
                        min={50}
                        max={1000}
                        step={50}
                        value={[field.value]}
                        onValueChange={(value) => field.onChange(value[0])}
                      />
                      <div className="text-sm text-muted-foreground">
                        {field.value} entries
                      </div>
                    </div>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="config.autoScroll"
              render={({ field }) => (
                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                  <div className="space-y-0.5">
                    <FormLabel className="text-base">Auto Scroll</FormLabel>
                    <FormDescription>
                      Automatically scroll to new entries
                    </FormDescription>
                  </div>
                  <FormControl>
                    <Switch
                      checked={field.value}
                      onCheckedChange={field.onChange}
                    />
                  </FormControl>
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="config.showMetadata"
              render={({ field }) => (
                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                  <div className="space-y-0.5">
                    <FormLabel className="text-base">Show Metadata</FormLabel>
                    <FormDescription>
                      Display additional log metadata
                    </FormDescription>
                  </div>
                  <FormControl>
                    <Switch
                      checked={field.value}
                      onCheckedChange={field.onChange}
                    />
                  </FormControl>
                </FormItem>
              )}
            />
          </>
        );

      default:
        return null;
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Configure Widget</DialogTitle>
          <DialogDescription>
            Customize the settings for your {config.type} widget.
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
                      <Input placeholder="Widget title" {...field} />
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
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
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
                        <Slider
                          min={1000}
                          max={300000}
                          step={1000}
                          value={[field.value || 30000]}
                          onValueChange={(value) => field.onChange(value[0])}
                        />
                        <div className="text-sm text-muted-foreground">
                          {((field.value || 30000) / 1000).toFixed(0)} seconds
                        </div>
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
                      <FormDescription>
                        Enable or disable this widget
                      </FormDescription>
                    </div>
                    <FormControl>
                      <Switch
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
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
              <Button type="submit">
                Save Changes
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
};

export default WidgetConfigPanel;