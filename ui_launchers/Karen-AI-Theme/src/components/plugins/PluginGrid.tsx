import React from 'react';
import { PluginCard } from './PluginCard';
import { Plugin } from '@/types/plugin';
import { ChevronLeft, ChevronRight, Loader2, Package } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface PluginGridProps {
  plugins: Plugin[];
  loading: boolean;
  total?: number;
  page?: number;
  perPage?: number;
  totalPages?: number;
  hasNext?: boolean;
  hasPrev?: boolean;
  onPageChange?: (page: number) => void;
  onInstall?: (pluginId: string, version?: string) => void;
  onDetails?: (pluginId: string) => void;
  onDiscover?: (pluginId: string) => void;
  installingPlugins?: Set<string>;
  emptyMessage?: string;
  className?: string;
}

export function PluginGrid({
  plugins,
  loading,
  total = 0,
  page = 1,
  perPage = 20,
  totalPages = 0,
  hasNext = false,
  hasPrev = false,
  onPageChange,
  onInstall,
  onDetails,
  onDiscover,
  installingPlugins = new Set(),
  emptyMessage = 'No plugins found',
  className,
}: PluginGridProps) {
  const handleInstall = (pluginId: string, version?: string) => {
    if (onInstall) {
      onInstall(pluginId, version);
    }
  };

  const handleDetails = (pluginId: string) => {
    if (onDetails) {
      onDetails(pluginId);
    }
  };

  const handleDiscover = (pluginId: string) => {
    if (onDiscover) {
      onDiscover(pluginId);
    }
  };

  const startItem = total === 0 ? 0 : (page - 1) * perPage + 1;
  const endItem = Math.min(page * perPage, total);

  return (
    <div className={`flex flex-col gap-6 ${className}`}>
      {loading && plugins.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
          <p className="text-sm text-muted-foreground">Loading plugins...</p>
        </div>
      ) : plugins.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 border-2 border-dashed rounded-lg">
          <Package className="h-12 w-12 text-muted-foreground mb-4" />
          <p className="text-sm text-muted-foreground">{emptyMessage}</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {plugins.map((plugin) => (
              <PluginCard
                key={plugin.id}
                plugin={plugin}
                onInstall={onInstall && (() => handleInstall(plugin.id, plugin.version))}
                onDetails={onDetails && (() => handleDetails(plugin.id))}
                onDiscover={onDiscover && (() => handleDiscover(plugin.id))}
                loading={installingPlugins.has(plugin.id)}
              />
            ))}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between border-t pt-4">
              <div className="text-sm text-muted-foreground">
                Showing {startItem} to {endItem} of {total} plugins
              </div>

              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onPageChange?.(page - 1)}
                  disabled={!hasPrev}
                >
                  <ChevronLeft className="h-4 w-4 mr-1" />
                  Previous
                </Button>

                <div className="flex items-center gap-1">
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    let pageNum;
                    if (totalPages <= 5) {
                      pageNum = i + 1;
                    } else if (page <= 3) {
                      pageNum = i + 1;
                    } else if (page >= totalPages - 2) {
                      pageNum = totalPages - 4 + i;
                    } else {
                      pageNum = page - 2 + i;
                    }

                    return (
                      <Button
                        key={pageNum}
                        variant={page === pageNum ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => onPageChange?.(pageNum)}
                        className="h-8 w-8 p-0"
                      >
                        {pageNum}
                      </Button>
                    );
                  })}
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onPageChange?.(page + 1)}
                  disabled={!hasNext}
                >
                  Next
                  <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
