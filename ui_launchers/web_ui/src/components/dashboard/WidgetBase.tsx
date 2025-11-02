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
        <div className="flex flex-col items-center justify-center h-full text-center p-4 sm:p-4 md:p-6">
          <AlertTriangle className="h-8 w-8 text-destructive mb-2 sm:w-auto md:w-full" />
          <p className="text-sm text-muted-foreground mb-2 md:text-base lg:text-lg">Widget Error</p>
          <p className="text-xs text-muted-foreground sm:text-sm md:text-base">{error}</p>
          {onRefresh && (
            <button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              className="mt-2"
             aria-label="Button">
              <RefreshCw className="h-3 w-3 mr-1 sm:w-auto md:w-full" />
              Retry
            </Button>
          )}
        </div>
      );
    }
    if (loading || isRefreshing) {
      return (
        <div className="flex items-center justify-center h-full">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground sm:w-auto md:w-full" />
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
      <div className="flex items-center justify-between p-3 border-b sm:p-4 md:p-6">
        <h3 className="font-medium text-sm truncate md:text-base lg:text-lg">{config.title}</h3>
        <div className="flex items-center gap-1">
          {/* Refresh Button */}
          {onRefresh && (
            <button
              variant="ghost"
              size="sm"
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="h-6 w-6 p-0 sm:w-auto md:w-full"
             aria-label="Button">
              <RefreshCw className={cn(
                "h-3 w-3",
                isRefreshing && "animate-spin"
              )} />
            </Button>
          )}
          {/* Widget Menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0 sm:w-auto md:w-full"
               aria-label="Button">
                <MoreVertical className="h-3 w-3 sm:w-auto md:w-full" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-40 sm:w-auto md:w-full">
              {onRefresh && (
                <DropdownMenuItem onClick={handleRefresh} disabled={isRefreshing}>
                  <RefreshCw className="h-3 w-3 mr-2 sm:w-auto md:w-full" />
                  Refresh
                </DropdownMenuItem>
              )}
              {onConfigChange && (
                <DropdownMenuItem onClick={handleConfigChange}>
                  <Settings className="h-3 w-3 mr-2 sm:w-auto md:w-full" />
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
                  <X className="h-3 w-3 mr-2 sm:w-auto md:w-full" />
                  Remove
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
      {/* Widget Content */}
      <div className="p-3 flex-1 overflow-hidden sm:p-4 md:p-6">
        {renderContent()}
      </div>
      {/* Last Updated Indicator */}
      {data?.lastUpdated && !loading && !error && (
        <div className="absolute bottom-1 right-1 text-xs text-muted-foreground sm:text-sm md:text-base">
          {new Date(data.lastUpdated).toLocaleTimeString()}
        </div>
      )}
    </Card>
  );
};
export default WidgetBase;
