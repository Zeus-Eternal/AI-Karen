import type React from 'react';
import type {
  IntersectionObserverOptions,
  UseIntersectionObserverReturn,
} from './use-intersection-observer';

export interface IntersectionObserverWrapperProps {
  children: (isIntersecting: boolean, entry: IntersectionObserverEntry | null) => React.ReactNode;
  options?: IntersectionObserverOptions;
  as?: React.ElementType;
  className?: string;
}

export interface LazyContentProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  options?: IntersectionObserverOptions;
  className?: string;
  as?: React.ElementType;
}

export interface VirtualizedListProps<T> {
  items: T[];
  renderItem: (item: T, index: number, isVisible: boolean) => React.ReactNode;
  itemHeight?: number;
  containerHeight?: number;
  overscan?: number;
  className?: string;
}

export type { IntersectionObserverOptions, UseIntersectionObserverReturn };
