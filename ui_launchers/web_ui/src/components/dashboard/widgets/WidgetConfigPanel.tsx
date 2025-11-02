
"use client";
import React, { useState, useCallback } from 'react';
import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import type { WidgetConfig, WidgetType } from '@/types/dashboard';

import { } from '@/components/ui/dialog';
import { } from '@/components/ui/form';

import { } from '@/components/ui/select';








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

const statusWidgetSchema = baseWidgetSchema.extend({
  config: z.object({
    service: z.string().min(1, 'Service is required'),
    endpoint: z.string().url('Must be a valid URL').optional(),
    checkInterval: z.number().min(5000).max(300000).default(30000),
    showDetails: z.boolean().default(true),
    showHistory: z.boolean().default(true),
  }),

const chartWidgetSchema = baseWidgetSchema.extend({
  config: z.object({
    dataSource: z.string().min(1, 'Data source is required'),
    chartType: z.enum(['line', 'bar', 'area']).default('line'),
    timeRange: z.enum(['1h', '6h', '24h', '7d', '30d']).default('24h'),
    series: z.array(z.string()).min(1, 'At least one series is required'),
    showLegend: z.boolean().default(true),
    enableZoom: z.boolean().default(true),
  }),

const logWidgetSchema = baseWidgetSchema.extend({
  config: z.object({
    logSource: z.string().min(1, 'Log source is required'),
    levels: z.array(z.enum(['', 'warn', 'error']),
    maxEntries: z.number().min(50).max(1000).default(200),
    autoScroll: z.boolean().default(true),
    showMetadata: z.boolean().default(false),
  }),

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
    resolver: zodResolver(schema) as any,
    defaultValues: config,

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

  // Focus management for accessibility
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        // Handle escape key
        onClose?.();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

        return (
          <>
            <FormField
              control={form.control}
              name="config.dataSource"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Data Source</FormLabel>
                  <select onValueChange={field.onChange} defaultValue={field.value} aria-label="Select option">
                    <FormControl>
                      <selectTrigger aria-label="Select option">
                        <selectValue placeholder="Select data source" />
                      </SelectTrigger>
                    </FormControl>
                    <selectContent aria-label="Select option">
                      <selectItem value="system-metrics" aria-label="Select option">System Metrics</SelectItem>
                      <selectItem value="application-metrics" aria-label="Select option">Application Metrics</SelectItem>
                      <selectItem value="custom-metrics" aria-label="Select option">Custom Metrics</SelectItem>
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
                    <input placeholder="e.g., cpu_usage, memory_usage" {...field} />
                  </FormControl>
                  <FormDescription>
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
                  <select onValueChange={field.onChange} defaultValue={field.value} aria-label="Select option">
                    <FormControl>
                      <selectTrigger aria-label="Select option">
                        <selectValue placeholder="Select format" />
                      </SelectTrigger>
                    </FormControl>
                    <selectContent aria-label="Select option">
                      <selectItem value="number" aria-label="Select option">Number</SelectItem>
                      <selectItem value="percentage" aria-label="Select option">Percentage</SelectItem>
                      <selectItem value="currency" aria-label="Select option">Currency</SelectItem>
                      <selectItem value="bytes" aria-label="Select option">Bytes</SelectItem>
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
                    <input placeholder="e.g., ms, req/s" {...field} />
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
                        <input 
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
                        <input 
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
                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4 sm:p-4 md:p-6">
                  <div className="space-y-0.5">
                    <FormLabel className="text-base">Show Trend</FormLabel>
                    <FormDescription>
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
                  <select onValueChange={field.onChange} defaultValue={field.value} aria-label="Select option">
                    <FormControl>
                      <selectTrigger aria-label="Select option">
                        <selectValue placeholder="Select service" />
                      </SelectTrigger>
                    </FormControl>
                    <selectContent aria-label="Select option">
                      <selectItem value="api-server" aria-label="Select option">API Server</SelectItem>
                      <selectItem value="database" aria-label="Select option">Database</SelectItem>
                      <selectItem value="cache" aria-label="Select option">Cache</SelectItem>
                      <selectItem value="message-queue" aria-label="Select option">Message Queue</SelectItem>
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
                    <input placeholder="https://api.example.com/health" {...field} />
                  </FormControl>
                  <FormDescription>
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
                      <div className="text-sm text-muted-foreground md:text-base lg:text-lg">
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
                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4 sm:p-4 md:p-6">
                  <div className="space-y-0.5">
                    <FormLabel className="text-base">Show Details</FormLabel>
                    <FormDescription>
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
                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4 sm:p-4 md:p-6">
                  <div className="space-y-0.5">
                    <FormLabel className="text-base">Show History</FormLabel>
                    <FormDescription>
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
                  <select onValueChange={field.onChange} defaultValue={field.value} aria-label="Select option">
                    <FormControl>
                      <selectTrigger aria-label="Select option">
                        <selectValue placeholder="Select data source" />
                      </SelectTrigger>
                    </FormControl>
                    <selectContent aria-label="Select option">
                      <selectItem value="metrics-api" aria-label="Select option">Metrics API</SelectItem>
                      <selectItem value="logs-api" aria-label="Select option">Logs API</SelectItem>
                      <selectItem value="custom-api" aria-label="Select option">Custom API</SelectItem>
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
                  <select onValueChange={field.onChange} defaultValue={field.value} aria-label="Select option">
                    <FormControl>
                      <selectTrigger aria-label="Select option">
                        <selectValue placeholder="Select chart type" />
                      </SelectTrigger>
                    </FormControl>
                    <selectContent aria-label="Select option">
                      <selectItem value="line" aria-label="Select option">Line Chart</SelectItem>
                      <selectItem value="bar" aria-label="Select option">Bar Chart</SelectItem>
                      <selectItem value="area" aria-label="Select option">Area Chart</SelectItem>
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
                  <select onValueChange={field.onChange} defaultValue={field.value} aria-label="Select option">
                    <FormControl>
                      <selectTrigger aria-label="Select option">
                        <selectValue placeholder="Select time range" />
                      </SelectTrigger>
                    </FormControl>
                    <selectContent aria-label="Select option">
                      <selectItem value="1h" aria-label="Select option">Last Hour</SelectItem>
                      <selectItem value="6h" aria-label="Select option">Last 6 Hours</SelectItem>
                      <selectItem value="24h" aria-label="Select option">Last 24 Hours</SelectItem>
                      <selectItem value="7d" aria-label="Select option">Last 7 Days</SelectItem>
                      <selectItem value="30d" aria-label="Select option">Last 30 Days</SelectItem>
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
                    <textarea
                      placeholder="Enter series names, one per line"
                      value={field.value?.join('\n') || ''}
                      onChange={(e) => field.onChange(e.target.value.split('\n').filter(Boolean))}
                    />
                  </FormControl>
                  <FormDescription>
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="config.showLegend"
              render={({ field }) => (
                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4 sm:p-4 md:p-6">
                  <div className="space-y-0.5">
                    <FormLabel className="text-base">Show Legend</FormLabel>
                    <FormDescription>
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
                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4 sm:p-4 md:p-6">
                  <div className="space-y-0.5">
                    <FormLabel className="text-base">Enable Zoom</FormLabel>
                    <FormDescription>
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
                  <select onValueChange={field.onChange} defaultValue={field.value} aria-label="Select option">
                    <FormControl>
                      <selectTrigger aria-label="Select option">
                        <selectValue placeholder="Select log source" />
                      </SelectTrigger>
                    </FormControl>
                    <selectContent aria-label="Select option">
                      <selectItem value="application" aria-label="Select option">Application Logs</SelectItem>
                      <selectItem value="system" aria-label="Select option">System Logs</SelectItem>
                      <selectItem value="security" aria-label="Select option">Security Logs</SelectItem>
                      <selectItem value="audit" aria-label="Select option">Audit Logs</SelectItem>
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
                    {['', 'warn', 'error'].map((level) => (
                      <Badge
                        key={level}
                        variant={field.value?.includes(level as any) ? 'default' : 'outline'}
                        className="cursor-pointer"
                        onClick={() => {
                          const currentLevels = field.value || [];
                          if (currentLevels.includes(level as any)) {
                            field.onChange(currentLevels.filter((l: any) => l !== level));
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
                      <div className="text-sm text-muted-foreground md:text-base lg:text-lg">
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
                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4 sm:p-4 md:p-6">
                  <div className="space-y-0.5">
                    <FormLabel className="text-base">Auto Scroll</FormLabel>
                    <FormDescription>
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
                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4 sm:p-4 md:p-6">
                  <div className="space-y-0.5">
                    <FormLabel className="text-base">Show Metadata</FormLabel>
                    <FormDescription>
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
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto ">
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
                    <select onValueChange={field.onChange} defaultValue={field.value} aria-label="Select option">
                      <FormControl>
                        <selectTrigger aria-label="Select option">
                          <selectValue placeholder="Select size" />
                        </SelectTrigger>
                      </FormControl>
                      <selectContent aria-label="Select option">
                        <selectItem value="small" aria-label="Select option">Small (1x1)</SelectItem>
                        <selectItem value="medium" aria-label="Select option">Medium (2x1)</SelectItem>
                        <selectItem value="large" aria-label="Select option">Large (2x2)</SelectItem>
                        <selectItem value="full" aria-label="Select option">Full Width</SelectItem>
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
                        <div className="text-sm text-muted-foreground md:text-base lg:text-lg">
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
                  <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4 sm:p-4 md:p-6">
                    <div className="space-y-0.5">
                      <FormLabel className="text-base">Enabled</FormLabel>
                      <FormDescription>
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
              <Button type="button" variant="outline" onClick={onClose} >
              </Button>
              {onPreview && (
                <Button type="button" variant="outline" onClick={handlePreview} >
                </Button>
              )}
              <button type="submit" aria-label="Submit form">
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
};
export default WidgetConfigPanel;
