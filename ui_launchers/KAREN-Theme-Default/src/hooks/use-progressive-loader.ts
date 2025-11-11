import { useCallback, useEffect, useState } from "react";

import type { ProgressiveLoaderProps } from "@/components/ui/progressive-loader";

type UseProgressiveLoaderOptions = {
  initialBatchSize?: number;
  batchSize?: number;
};

type ProgressiveLoaderResult<T> = {
  items: T[];
  loading: boolean;
  error: Error | null;
  hasMore: boolean;
  total: number;
  loadMore: () => void;
  reset: () => void;
};

export function useProgressiveLoader<T>(
  loadData: ProgressiveLoaderProps<T>["loadData"],
  options: UseProgressiveLoaderOptions = {}
): ProgressiveLoaderResult<T> {
  const [items, setItems] = useState<T[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [hasMore, setHasMore] = useState(true);
  const [total, setTotal] = useState(0);

  const { initialBatchSize = 20, batchSize = 10 } = options;

  const loadItems = useCallback(
    async (offset: number, limit: number) => {
      if (loading) {
        return;
      }

      try {
        setLoading(true);
        setError(null);

        const result = await loadData(offset, limit);

        setItems(prev =>
          offset === 0 ? result.items : [...prev, ...result.items]
        );
        setTotal(result.total);
        setHasMore(result.hasMore);
      } catch (err) {
        const resolvedError =
          err instanceof Error ? err : new Error("Failed to load items");
        setError(resolvedError);
      } finally {
        setLoading(false);
      }
    },
    [loadData, loading]
  );

  const loadMore = useCallback(() => {
    if (!hasMore || loading) {
      return;
    }

    loadItems(items.length, batchSize);
  }, [batchSize, hasMore, items.length, loadItems, loading]);

  const reset = useCallback(() => {
    setItems([]);
    setError(null);
    setHasMore(true);
    setTotal(0);
    loadItems(0, initialBatchSize);
  }, [initialBatchSize, loadItems]);

  useEffect(() => {
    loadItems(0, initialBatchSize);
  }, [initialBatchSize, loadItems]);

  return {
    items,
    loading,
    error,
    hasMore,
    total,
    loadMore,
    reset,
  };
}
