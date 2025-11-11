"use client";

import React from 'react';

import {
  useIntersectionObserver,
  type IntersectionObserverOptions,
} from './use-intersection-observer';

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

export type {
  IntersectionObserverOptions,
  UseIntersectionObserverReturn,
} from './use-intersection-observer';

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

// Hook helpers are exported from use-intersection-observer.ts

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
