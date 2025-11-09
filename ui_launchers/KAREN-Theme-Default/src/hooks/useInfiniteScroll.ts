import { useEffect, useRef, useCallback } from 'react';

export interface UseInfiniteScrollOptions {
  hasNextPage: boolean;
  isLoading: boolean;
  onLoadMore: () => void;
  threshold?: number;
  rootMargin?: string;
}

export const useInfiniteScroll = ({
  hasNextPage,
  isLoading,
  onLoadMore,
  threshold = 0.1,
  rootMargin = '100px',
}: UseInfiniteScrollOptions) => {
  const loadMoreRef = useRef<HTMLDivElement | null>(null);

  const handleIntersection = useCallback(
    (entries: IntersectionObserverEntry[]) => {
      const [entry] = entries;
      if (entry.isIntersecting && hasNextPage && !isLoading) {
        onLoadMore();
      }
    },
    [hasNextPage, isLoading, onLoadMore]
  );

  useEffect(() => {
    const element = loadMoreRef.current;
    if (!element) return; // Ensure the element is present before observing

    const observer = new IntersectionObserver(handleIntersection, {
      threshold,
      rootMargin,
    });

    observer.observe(element);

    // Cleanup the observer on component unmount or when dependencies change
    return () => {
      observer.disconnect();
    };
  }, [handleIntersection, threshold, rootMargin]);

  return loadMoreRef;
};

export default useInfiniteScroll;
