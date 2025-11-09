"use client";

import React, { useEffect, useRef, useState, useCallback } from 'react';

export interface IntersectionObserverOptions {
  threshold?: number | number[];
  rootMargin?: string;
  root?: Element | null;
  triggerOnce?: boolean;
  skip?: boolean;
}

export interface UseIntersectionObserverReturn {
  ref: React.RefObject<HTMLElement>;
  isIntersecting: boolean;
  entry: IntersectionObserverEntry | null;
}

// Hook for intersection observer
export function useIntersectionObserver(
  options: IntersectionObserverOptions = {}
): UseIntersectionObserverReturn {
  const {
    threshold = 0,
    rootMargin = '0px',
    root = null,
    triggerOnce = false,
    skip = false,
  } = options;

  const [entry, setEntry] = useState<IntersectionObserverEntry | null>(null);
  const [isIntersecting, setIsIntersecting] = useState(false);
  const elementRef = useRef<HTMLElement>(null);
  const observerRef = useRef<IntersectionObserver | null>(null);

  useEffect(() => {
    const element = elementRef.current;
    
    if (!element || skip) return;

    // Disconnect previous observer
    if (observerRef.current) {
      observerRef.current.disconnect();
    }

    observerRef.current = new IntersectionObserver(
      ([entry]) => {
        setEntry(entry);
        setIsIntersecting(entry.isIntersecting);

        // If triggerOnce is true, disconnect after first intersection
        if (entry.isIntersecting && triggerOnce && observerRef.current) {
          observerRef.current.disconnect();
        }
      },
      {
        threshold,
        rootMargin,
        root,
      }
    );

    observerRef.current.observe(element);

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [threshold, rootMargin, root, triggerOnce, skip]);

  return {
    ref: elementRef,
    isIntersecting,
    entry,
  };
}

// Component wrapper for intersection observer
export interface IntersectionObserverWrapperProps {
  children: (isIntersecting: boolean, entry: IntersectionObserverEntry | null) => React.ReactNode;
  options?: IntersectionObserverOptions;
  as?: React.ElementType;
  className?: string;
}

export const IntersectionObserverWrapper: React.FC<IntersectionObserverWrapperProps> = ({
  children,
  options = {},
  as: Component = 'div',
  className,
}) => {
  const { ref, isIntersecting, entry } = useIntersectionObserver(options);

  return (
    <Component ref={ref} className={className}>
      {children(isIntersecting, entry)}
    </Component>
  );
};

// Lazy content component that renders children only when in view
export interface LazyContentProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  options?: IntersectionObserverOptions;
  className?: string;
  as?: React.ElementType;
}

export const LazyContent: React.FC<LazyContentProps> = ({
  children,
  fallback = null,
  options = { triggerOnce: true },
  className,
  as: Component = 'div',
}) => {
  const { ref, isIntersecting } = useIntersectionObserver(options);

  return (
    <Component ref={ref} className={className}>
      {isIntersecting ? children : fallback}
    </Component>
  );
};

// Hook for multiple intersection observers
export function useMultipleIntersectionObserver(
  elements: (HTMLElement | null)[],
  options: IntersectionObserverOptions = {}
) {
  const [entries, setEntries] = useState<Map<HTMLElement, IntersectionObserverEntry>>(new Map());
  const observerRef = useRef<IntersectionObserver | null>(null);

  const updateEntry = useCallback((entry: IntersectionObserverEntry) => {
    setEntries(prev => new Map(prev.set(entry.target as HTMLElement, entry)));
  }, []);

  useEffect(() => {
    const validElements = elements.filter((el): el is HTMLElement => el !== null);
    
    if (validElements.length === 0) return;

    observerRef.current = new IntersectionObserver(
      (entries) => {
        entries.forEach(updateEntry);
      },
      options
    );

    validElements.forEach(element => {
      observerRef.current?.observe(element);
    });

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [elements, options, updateEntry]);

  const isIntersecting = useCallback(
    (element: HTMLElement | null) => {
      if (!element) return false;
      return entries.get(element)?.isIntersecting ?? false;
    },
    [entries]
  );

  const getEntry = useCallback(
    (element: HTMLElement | null) => {
      if (!element) return null;
      return entries.get(element) ?? null;
    },
    [entries]
  );

  return {
    isIntersecting,
    getEntry,
    entries: Array.from(entries.values()),
  };
}

// Virtualized list component using intersection observer
export interface VirtualizedListProps<T> {
  items: T[];
  renderItem: (item: T, index: number, isVisible: boolean) => React.ReactNode;
  itemHeight?: number;
  containerHeight?: number;
  overscan?: number;
  className?: string;
}

export function VirtualizedList<T>({
  items,
  renderItem,
  itemHeight = 50,
  containerHeight = 400,
  overscan = 5,
  className,
}: VirtualizedListProps<T>) {
  const [visibleRange, setVisibleRange] = useState({ start: 0, end: 0 });
  const containerRef = useRef<HTMLDivElement>(null);
  const itemRefs = useRef<Map<number, HTMLElement>>(new Map());

  // Calculate visible items based on scroll position
  const handleScroll = useCallback(() => {
    if (!containerRef.current) return;

    const scrollTop = containerRef.current.scrollTop;
    const start = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
    const end = Math.min(
      items.length - 1,
      Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
    );

    setVisibleRange({ start, end });
  }, [itemHeight, containerHeight, overscan, items.length]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    container.addEventListener('scroll', handleScroll);
    handleScroll(); // Initial calculation

    return () => {
      container.removeEventListener('scroll', handleScroll);
    };
  }, [handleScroll]);

  const totalHeight = items.length * itemHeight;

  return (
    <div
      ref={containerRef}
      className={`overflow-auto ${className}`}
      style={{ height: containerHeight }}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        {items.slice(visibleRange.start, visibleRange.end + 1).map((item, index) => {
          const actualIndex = visibleRange.start + index;
          const isVisible = actualIndex >= visibleRange.start && actualIndex <= visibleRange.end;
          
          return (
            <div
              key={actualIndex}
              style={{
                position: 'absolute',
                top: actualIndex * itemHeight,
                height: itemHeight,
                width: '100%',
              }}
              ref={(el) => {
                if (el) {
                  itemRefs.current.set(actualIndex, el);
                } else {
                  itemRefs.current.delete(actualIndex);
                }
              }}
            >
              {renderItem(item, actualIndex, isVisible)}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default useIntersectionObserver;