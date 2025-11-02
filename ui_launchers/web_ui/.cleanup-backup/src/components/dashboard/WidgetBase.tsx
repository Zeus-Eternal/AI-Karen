'use client';

import React, { useState, useCallback } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  MoreVertical, 
  RefreshCw, 
  Settings, 
  X, 
  AlertTriangle,
  Loader2 
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { cn } from '@/lib/utils';
import type { WidgetProps, WidgetData } from '@/types/dashboard';

export interface WidgetBaseProps extends WidgetProps {
  children: React.ReactNode;
  loading?: boolean;
  error?: string;
  className?: string;
}

export const WidgetBase: React.FC<WidgetBaseProps> = ({
  config,
  data,
  children,
  loading = false,
  error,
  onConfigChange,
  onRefresh,
  onRemove,
  isEditing = false,
  className
}) => {
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = useCallback(async () => {
    if (onRefresh && !isRefreshing) {
      setIsRefreshing(true);
      try {
        await onRefresh();
      } finally {
        setIsRefreshing(false);
      }
    }
  }, [onRefresh, isRefreshing]);

  const handleConfigChange = useCallback(() => {
    // This would open a configuration modal/panel
    // For now, we'll just call the callback if provided
    if (onConfigChange) {
      // In a real implementation, this would open a config dialog
      console.log('Configure widget:', config.id);
    }
  }, [onConfigChange, config.id]);

  const handleRemove = useCallback(() => {
    if (onRemove && window.confirm('Are you sure you want to remove this widget?')) {
      onRemove();
    }
  }, [onRemove]);

  const getWidgetSizeClasses = (size: string) => {
    switch (size) {
      case 'small':
        return 'col-span-1 row-span-1 min-h-[200px]';
      case 'medium':
        return 'col-span-2 row-span-1 min-h-[200px]';
      case 'large':
        return 'col-span-2 row-span-2 min-h-[400px]';
      case 'full':
        return 'col-span-full row-span-2 min-h-[400px]';
      default:
        return 'col-span-1 row-span-1 min-h-[200px]';
    }
  };

  const renderContent = () => {
    if (error) {
      return (
        <div className="flex flex-col items-center justify-center h-full text-center p-4">
          <AlertTriangle className="h-8 w-8 text-destructive mb-2" />
          <p className="text-sm text-muted-foreground mb-2">Widget Error</p>
          <p className="text-xs text-muted-foreground">{error}</p>
          {onRefresh && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              className="mt-2"
            >
              <RefreshCw className="h-3 w-3 mr-1" />
              Retry
            </Button>
          )}
        </div>
      );
    }

    if (loading || isRefreshing) {
      return (
        <div className="flex items-center justify-center h-full">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      );
    }

    return children;
  };

  return (
    <Card 
      className={cn(
        'relative transition-all duration-200 hover:shadow-md',
        getWidgetSizeClasses(config.size),
        isEditing && 'ring-2 ring-[var(--component-button-default-ring)] ring-offset-2 ring-offset-[var(--component-button-default-ring-offset,var(--color-neutral-50))]',
        className
      )}
      data-widget-id={config.id}
    >
      {/* Widget Header */}
      <div className="flex items-center justify-between p-3 border-b">
        <h3 className="font-medium text-sm truncate">{config.title}</h3>
        
        <div className="flex items-center gap-1">
          {/* Refresh Button */}
          {onRefresh && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="h-6 w-6 p-0"
            >
              <RefreshCw className={cn(
                "h-3 w-3",
                isRefreshing && "animate-spin"
              )} />
            </Button>
          )}

          {/* Widget Menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0"
              >
                <MoreVertical className="h-3 w-3" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-40">
              {onRefresh && (
                <DropdownMenuItem onClick={handleRefresh} disabled={isRefreshing}>
                  <RefreshCw className="h-3 w-3 mr-2" />
                  Refresh
                </DropdownMenuItem>
              )}
              {onConfigChange && (
                <DropdownMenuItem onClick={handleConfigChange}>
                  <Settings className="h-3 w-3 mr-2" />
                  Configure
                </DropdownMenuItem>
              )}
              {(onRefresh || onConfigChange) && onRemove && (
                <DropdownMenuSeparator />
              )}
              {onRemove && (
                <DropdownMenuItem 
                  onClick={handleRemove}
                  className="text-destructive focus:text-destructive"
                >
                  <X className="h-3 w-3 mr-2" />
                  Remove
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Widget Content */}
      <div className="p-3 flex-1 overflow-hidden">
        {renderContent()}
      </div>

      {/* Last Updated Indicator */}
      {data?.lastUpdated && !loading && !error && (
        <div className="absolute bottom-1 right-1 text-xs text-muted-foreground">
          {new Date(data.lastUpdated).toLocaleTimeString()}
        </div>
      )}
    </Card>
  );
};

export default WidgetBase;