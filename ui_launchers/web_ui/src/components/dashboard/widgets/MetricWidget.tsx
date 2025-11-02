'use client';

import React from 'react';
import { TrendingUp, TrendingDown, Minus, AlertTriangle, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { WidgetBase } from '../WidgetBase';
import type { WidgetProps, MetricData } from '@/types/dashboard';

interface MetricWidgetProps extends WidgetProps {
  data?: {
    id: string;
    data: MetricData;
    loading: boolean;
    error?: string;
    lastUpdated: Date;
  };
}

const formatValue = (value: number, format?: string, unit?: string): string => {
  let formattedValue: string;

  switch (format) {
    case 'percentage':
      formattedValue = `${value.toFixed(1)}%`;
      break;
    case 'currency':
      formattedValue = new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
      }).format(value);
      break;
    case 'bytes':
      const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
      if (value === 0) return '0 B';
      const i = Math.floor(Math.log(value) / Math.log(1024));
      formattedValue = `${(value / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
      break;
    default:
      formattedValue = new Intl.NumberFormat('en-US').format(value);
  }

  return unit && format !== 'currency' && format !== 'bytes' && format !== 'percentage' 
    ? `${formattedValue} ${unit}` 
    : formattedValue;
};

const getTrendIcon = (direction: 'up' | 'down' | 'stable') => {
  switch (direction) {
    case 'up':
      return <TrendingUp className="h-4 w-4 sm:w-auto md:w-full" />;
    case 'down':
      return <TrendingDown className="h-4 w-4 sm:w-auto md:w-full" />;
    case 'stable':
    default:
      return <Minus className="h-4 w-4 sm:w-auto md:w-full" />;
  }
};

const getTrendColor = (direction: 'up' | 'down' | 'stable', isPositive: boolean = true) => {
  if (direction === 'stable') return 'text-muted-foreground';
  
  const isGoodTrend = (direction === 'up' && isPositive) || (direction === 'down' && !isPositive);
  return isGoodTrend ? 'text-green-600' : 'text-red-600';
};

const getThresholdStatus = (value: number, threshold?: { warning: number; critical: number }) => {
  if (!threshold) return null;
  
  if (value >= threshold.critical) {
    return { status: 'critical', color: 'text-red-600', bgColor: 'bg-red-50', icon: AlertCircle };
  } else if (value >= threshold.warning) {
    return { status: 'warning', color: 'text-yellow-600', bgColor: 'bg-yellow-50', icon: AlertTriangle };
  }
  
  return { status: 'normal', color: 'text-green-600', bgColor: 'bg-green-50', icon: null };
};

export const MetricWidget: React.FC<MetricWidgetProps> = (props) => {
  const { data: widgetData } = props;
  
  if (!widgetData?.data) {
    return (
      <WidgetBase {...props}>
        <div className="flex items-center justify-center h-full text-muted-foreground">
          No metric data available
        </div>
      </WidgetBase>
    );
  }

  const metric = widgetData.data;
  const thresholdStatus = getThresholdStatus(metric.value, metric.threshold);
  const ThresholdIcon = thresholdStatus?.icon;

  return (
    <WidgetBase {...props}>
      <div className="flex flex-col h-full">
        {/* Main Metric Display */}
        <div className="flex-1 flex flex-col justify-center">
          <div className="text-center">
            {/* Threshold Alert */}
            {thresholdStatus && thresholdStatus.status !== 'normal' && ThresholdIcon && (
              <div className={cn(
                "inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium mb-2",
                thresholdStatus.bgColor,
                thresholdStatus.color
              )}>
                <ThresholdIcon className="h-3 w-3 sm:w-auto md:w-full" />
                {thresholdStatus.status === 'critical' ? 'Critical' : 'Warning'}
              </div>
            )}

            {/* Value */}
            <div className={cn(
              "text-2xl font-bold mb-1",
              thresholdStatus?.status === 'critical' ? 'text-red-600' :
              thresholdStatus?.status === 'warning' ? 'text-yellow-600' :
              'text-foreground'
            )}>
              {formatValue(metric.value, metric.format, metric.unit)}
            </div>

            {/* Label */}
            <div className="text-sm text-muted-foreground mb-3 md:text-base lg:text-lg">
              {metric.label}
            </div>

            {/* Trend Indicator */}
            {metric.trend && (
              <div className={cn(
                "inline-flex items-center gap-1 text-sm font-medium",
                getTrendColor(metric.trend.direction, true)
              )}>
                {getTrendIcon(metric.trend.direction)}
                <span>
                  {metric.trend.percentage > 0 ? '+' : ''}
                  {metric.trend.percentage.toFixed(1)}%
                </span>
                <span className="text-muted-foreground text-xs sm:text-sm md:text-base">
                  vs last period
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Threshold Indicators */}
        {metric.threshold && (
          <div className="mt-4 pt-3 border-t">
            <div className="flex justify-between text-xs text-muted-foreground sm:text-sm md:text-base">
              <span>Thresholds:</span>
              <div className="flex gap-3">
                <span className="flex items-center gap-1">
                  <div className="w-2 h-2 rounded-full bg-yellow-500 sm:w-auto md:w-full"></div>
                  {formatValue(metric.threshold.warning, metric.format, metric.unit)}
                </span>
                <span className="flex items-center gap-1">
                  <div className="w-2 h-2 rounded-full bg-red-500 sm:w-auto md:w-full"></div>
                  {formatValue(metric.threshold.critical, metric.format, metric.unit)}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </WidgetBase>
  );
};

export default MetricWidget;