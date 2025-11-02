"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import { Loader2, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface ProgressiveLoaderProps<T> {
  /**
   * Function that loads data progressively
   * @param offset - Starting index for loading
   * @param limit - Number of items to load
   * @returns Promise with loaded items and total count
   */
  loadData: (offset: number, limit: number) => Promise<{
    items: T[];
    total: number;
    hasMore: boolean;
  }>;
  
  /**
   * Function to render each item
   */
  renderItem: (item: T, index: number) => React.ReactNode;
  
  /**
   * Function to render loading placeholder
   */
  renderPlaceholder?: (index: number) => React.ReactNode;
  
  /**
   * Initial number of items to load
   */
  initialBatchSize?: number;
  
  /**
   * Number of items to load in subsequent batches
   */
  batchSize?: number;
  
  /**
   * Whether to load more items automatically when scrolling
   */
  autoLoad?: boolean;
  
  /**
   * Threshold for triggering auto-load (pixels from bottom)
   */
  autoLoadThreshold?: number;
  
  /**
   * Custom loading component
   */
  loadingComponent?: React.ReactNode;
  
  /**
   * Custom error component
   */
  errorComponent?: (error: Error, retry: () => void) => React.ReactNode;
  
  /**
   * Container className
   */
  className?: string;
  
  /**
   * Whether to show load more button
   */
  showLoadMoreButton?: boolean;
  
  /**
   * Load more button text
   */
  loadMoreText?: string;
  
  /**
   * Callback when items are loaded
   */
  onItemsLoaded?: (items: T[], total: number) => void;
  
  /**
   * Callback when loading state changes
   */
  onLoadingChange?: (loading: boolean) => void;
  
  /**
   * Callback when error occurs
   */
  onError?: (error: Error) => void;
}

export function ProgressiveLoader<T>({
  loadData,
  renderItem,
  renderPlaceholder,
  initialBatchSize = 20,
  batchSize = 10,
  autoLoad = false,
  autoLoadThreshold = 200,
  loadingComponent,
  errorComponent,
  className,
  showLoadMoreButton = true,
  loadMoreText = "Load More",
  onItemsLoaded,
  onLoadingChange,
  onError,
}: ProgressiveLoaderProps<T>) {
  const [items, setItems] = useState<T[]>([]);
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [hasMore, setHasMore] = useState(true);
  const [total, setTotal] = useState(0);
  const [loadedCount, setLoadedCount] = useState(0);

  // Update loading state callback
  useEffect(() => {
    onLoadingChange?.(loading || initialLoading);
  }, [loading, initialLoading, onLoadingChange]);

  // Load data function
  const loadItems = useCallback(
    async (offset: number, limit: number, isInitial = false) => {
      if (loading) return;

      try {
        setLoading(true);
        setError(null);

        const result = await loadData(offset, limit);
        
        setItems(prev => offset === 0 ? result.items : [...prev, ...result.items]);
        setTotal(result.total);
        setHasMore(result.hasMore);
        setLoadedCount(prev => offset === 0 ? result.items.length : prev + result.items.length);

        onItemsLoaded?.(result.items, result.total);
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Failed to load items');
        setError(error);
        onError?.(error);
      } finally {
        setLoading(false);
        if (isInitial) {
          setInitialLoading(false);
        }
      }
    },
    [loadData, loading, onItemsLoaded, onError]
  );

  // Initial load
  useEffect(() => {
    loadItems(0, initialBatchSize, true);
  }, [loadItems, initialBatchSize]);

  // Load more function
  const loadMore = useCallback(() => {
    if (!hasMore || loading) return;
    loadItems(loadedCount, batchSize);
  }, [hasMore, loading, loadedCount, batchSize, loadItems]);

  // Retry function
  const retry = useCallback(() => {
    if (items.length === 0) {
      setInitialLoading(true);
      loadItems(0, initialBatchSize, true);
    } else {
      loadMore();
    }
  }, [items.length, initialBatchSize, loadItems, loadMore]);

  // Auto-load on scroll
  useEffect(() => {
    if (!autoLoad || !hasMore || loading) return;

    const handleScroll = () => {
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      const scrollHeight = document.documentElement.scrollHeight;
      const clientHeight = window.innerHeight;

      if (scrollTop + clientHeight >= scrollHeight - autoLoadThreshold) {
        loadMore();
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [autoLoad, hasMore, loading, autoLoadThreshold, loadMore]);

  // Memoized placeholders
  const placeholders = useMemo(() => {
    if (!renderPlaceholder || !loading || items.length > 0) return null;
    
    return Array.from({ length: Math.min(initialBatchSize, 5) }, (_, index) => (
      <div key={`placeholder-${index}`}>
        {renderPlaceholder(index)}
      </div>
    ));
  }, [renderPlaceholder, loading, items.length, initialBatchSize]);

  // Default loading component
  const defaultLoadingComponent = (
    <div className="flex items-center justify-center py-4">
      <Loader2 className="h-4 w-4 animate-spin mr-2 " />
      <span className="text-sm text-muted-foreground md:text-base lg:text-lg">Loading...</span>
    </div>
  );

  // Default error component
  const defaultErrorComponent = (error: Error, retry: () => void) => (
    <div className="flex flex-col items-center justify-center py-8 text-center">
      <AlertCircle className="h-8 w-8 text-red-500 mb-2 " />
      <p className="text-sm text-red-600 mb-4 md:text-base lg:text-lg">{error.message}</p>
      <button
        onClick={retry}
        className="px-4 py-2 bg-red-100 text-red-700 rounded-md hover:bg-red-200 transition-colors"
       aria-label="Button">
      </button>
    </div>
  );

  // Render error state
  if (error && items.length === 0) {
    return (
      <div className={cn("w-full", className)}>
        {errorComponent ? errorComponent(error, retry) : defaultErrorComponent(error, retry)}
      </div>
    );
  }

  // Render initial loading state
  if (initialLoading && items.length === 0) {
    return (
      <div className={cn("w-full", className)}>
        {placeholders || loadingComponent || defaultLoadingComponent}
      </div>
    );
  }

  return (
    <div className={cn("w-full", className)}>
      {/* Render items */}
      {items.map((item, index) => (
        <div key={index}>
          {renderItem(item, index)}
        </div>
      ))}

      {/* Loading more indicator */}
      {loading && items.length > 0 && (
        <div className="py-4">
          {loadingComponent || defaultLoadingComponent}
        </div>
      )}

      {/* Load more button */}
      {!autoLoad && hasMore && !loading && showLoadMoreButton && (
        <div className="flex justify-center py-4">
          <button
            onClick={loadMore}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
           aria-label="Button">
            {loadMoreText}
          </button>
        </div>
      )}

      {/* Progress indicator */}
      {total > 0 && (
        <div className="text-xs text-muted-foreground text-center py-2 sm:text-sm md:text-base">
          Showing {loadedCount} of {total} items
          {hasMore && ` (${Math.round((loadedCount / total) * 100)}% loaded)`}
        </div>
      )}

      {/* No more items indicator */}
      {!hasMore && items.length > 0 && (
        <div className="text-xs text-muted-foreground text-center py-2 sm:text-sm md:text-base">
        </div>
      )}
    </div>
  );
}

// Hook for using progressive loader with custom logic
export function useProgressiveLoader<T>(
  loadData: ProgressiveLoaderProps<T>['loadData'],
  options: {
    initialBatchSize?: number;
    batchSize?: number;
    autoLoad?: boolean;
  } = {}
) {
  const [items, setItems] = useState<T[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [hasMore, setHasMore] = useState(true);
  const [total, setTotal] = useState(0);

  const {
    initialBatchSize = 20,
    batchSize = 10,
    autoLoad = false
  } = options;

  const loadItems = useCallback(
    async (offset: number, limit: number) => {
      if (loading) return;

      try {
        setLoading(true);
        setError(null);

        const result = await loadData(offset, limit);
        
        setItems(prev => offset === 0 ? result.items : [...prev, ...result.items]);
        setTotal(result.total);
        setHasMore(result.hasMore);
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Failed to load items');
        setError(error);
      } finally {
        setLoading(false);
      }
    },
    [loadData, loading]
  );

  const loadMore = useCallback(() => {
    if (!hasMore || loading) return;
    loadItems(items.length, batchSize);
  }, [hasMore, loading, items.length, batchSize, loadItems]);

  const reset = useCallback(() => {
    setItems([]);
    setError(null);
    setHasMore(true);
    setTotal(0);
    loadItems(0, initialBatchSize);
  }, [loadItems, initialBatchSize]);

  // Initial load
  useEffect(() => {
    loadItems(0, initialBatchSize);
  }, [loadItems, initialBatchSize]);

  return {
    items,
    loading,
    error,
    hasMore,
    total,
    loadMore,
    reset
  };
}