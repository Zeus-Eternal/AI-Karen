'use client';

import React from 'react';
import { 
  CheckCircle, 
  AlertTriangle, 
  XCircle, 
  HelpCircle,
  Clock,
  Activity,
  Server,
  Wifi
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { WidgetBase } from '../WidgetBase';
import { Badge } from '@/components/ui/badge';
import type { WidgetProps, StatusData } from '@/types/dashboard';

interface StatusWidgetProps extends WidgetProps {
  data?: {
    id: string;
    data: StatusData;
    loading: boolean;
    error?: string;
    lastUpdated: Date;
  };
}

const getStatusConfig = (status: StatusData['status']) => {
  switch (status) {
    case 'healthy':
      return {
        icon: CheckCircle,
        color: 'text-green-600',
        bgColor: 'bg-green-50',
        badgeVariant: 'default' as const,
        badgeClass: 'bg-green-100 text-green-800 hover:bg-green-100',
        label: 'Healthy'
      };
    case 'warning':
      return {
        icon: AlertTriangle,
        color: 'text-yellow-600',
        bgColor: 'bg-yellow-50',
        badgeVariant: 'secondary' as const,
        badgeClass: 'bg-yellow-100 text-yellow-800 hover:bg-yellow-100',
        label: 'Warning'
      };
    case 'critical':
      return {
        icon: XCircle,
        color: 'text-red-600',
        bgColor: 'bg-red-50',
        badgeVariant: 'destructive' as const,
        badgeClass: 'bg-red-100 text-red-800 hover:bg-red-100',
        label: 'Critical'
      };
    case 'unknown':
    default:
      return {
        icon: HelpCircle,
        color: 'text-gray-600',
        bgColor: 'bg-gray-50',
        badgeVariant: 'outline' as const,
        badgeClass: 'bg-gray-100 text-gray-800 hover:bg-gray-100',
        label: 'Unknown'
      };
  }
};

const getDetailIcon = (key: string) => {
  const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
    uptime: Clock,
    cpu: Activity,
    memory: Server,
    network: Wifi,
    connections: Wifi,
    requests: Activity,
    errors: XCircle,
    latency: Clock,
  };

  const IconComponent = iconMap[key.toLowerCase()] || Activity;
  return IconComponent;
};

const formatDetailValue = (value: any): string => {
  if (typeof value === 'number') {
    // Format based on the value range
    if (value < 1) {
      return `${(value * 100).toFixed(1)}%`;
    } else if (value > 1000000) {
      return `${(value / 1000000).toFixed(1)}M`;
    } else if (value > 1000) {
      return `${(value / 1000).toFixed(1)}K`;
    }
    return value.toFixed(0);
  }
  
  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No';
  }
  
  return String(value);
};

export const StatusWidget: React.FC<StatusWidgetProps> = (props) => {
  const { data: widgetData } = props;
  
  if (!widgetData?.data) {
    return (
      <WidgetBase {...props}>
        <div className="flex items-center justify-center h-full text-muted-foreground">
          No status data available
        </div>
      </WidgetBase>
    );
  }

  const status = widgetData.data;
  const statusConfig = getStatusConfig(status.status);
  const StatusIcon = statusConfig.icon;

  return (
    <WidgetBase {...props}>
      <div className="flex flex-col h-full">
        {/* Main Status Display */}
        <div className="flex-1 flex flex-col justify-center">
          <div className="text-center mb-4">
            {/* Status Icon and Badge */}
            <div className="flex flex-col items-center gap-3">
              <div className={cn(
                "p-3 rounded-full",
                statusConfig.bgColor
              )}>
                <StatusIcon className={cn("h-8 w-8", statusConfig.color)} />
              </div>
              
              <Badge 
                variant={statusConfig.badgeVariant}
                className={cn("text-sm font-medium", statusConfig.badgeClass)}
              >
                {statusConfig.label}
              </Badge>
            </div>

            {/* Status Message */}
            <div className="mt-3">
              <p className="text-sm font-medium text-foreground mb-1">
                {status.message}
              </p>
              
              {/* Last Check Time */}
              <p className="text-xs text-muted-foreground">
                Last checked: {new Date(status.lastCheck).toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        {/* Status Details */}
        {status.details && Object.keys(status.details).length > 0 && (
          <div className="mt-4 pt-4 border-t">
            <div className="space-y-2">
              <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Details
              </h4>
              
              <div className="grid grid-cols-1 gap-2">
                {Object.entries(status.details).slice(0, 4).map(([key, value]) => {
                  const IconComponent = getDetailIcon(key);
                  
                  return (
                    <div key={key} className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <IconComponent className="h-3 w-3" />
                        <span className="capitalize">
                          {key.replace(/([A-Z])/g, ' $1').toLowerCase()}
                        </span>
                      </div>
                      <span className="font-medium text-foreground">
                        {formatDetailValue(value)}
                      </span>
                    </div>
                  );
                })}
              </div>

              {/* Show more indicator if there are additional details */}
              {Object.keys(status.details).length > 4 && (
                <div className="text-xs text-muted-foreground text-center pt-2">
                  +{Object.keys(status.details).length - 4} more details
                </div>
              )}
            </div>
          </div>
        )}

        {/* Status History Indicator */}
        <div className="mt-3 pt-2 border-t">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Status History</span>
            <div className="flex gap-1">
              {/* Mock status history - in real implementation, this would come from data */}
              {Array.from({ length: 10 }, (_, i) => (
                <div
                  key={i}
                  className={cn(
                    "w-2 h-2 rounded-full",
                    Math.random() > 0.8 ? 'bg-red-300' :
                    Math.random() > 0.9 ? 'bg-yellow-300' :
                    'bg-green-300'
                  )}
                  title={`${10 - i} periods ago`}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </WidgetBase>
  );
};

export default StatusWidget;