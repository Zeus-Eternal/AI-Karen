// Lazy loading components and utilities
export {
  default as LazyComponent,
  LazyComponentErrorBoundary,
} from './lazy-component';
export { createLazyComponent, useLazyPreload } from './lazy-component-utils';

export { default as LazyImage } from './lazy-image';
export { useImagePreloader } from './use-image-preloader';

export { default as RouteLazyLoader } from './route-lazy-loader';
export { createLazyRoute, useRoutePreloader, withLazyLoading } from './route-lazy-loader-utils';

export {
  IntersectionObserverWrapper,
  LazyContent,
  VirtualizedList,
} from './intersection-observer';
export { default as useIntersectionObserver, useMultipleIntersectionObserver } from './use-intersection-observer';

// Re-export types
export type {
  LazyComponentProps,
  LazyLoadOptions,
  SimpleComponent,
} from './lazy-component.types';

export type {
  LazyImageProps
} from './lazy-image.types';

export type {
  RouteLazyLoaderProps,
  FallbackComponent,
  RouteErrorFallback,
} from './route-lazy-loader.types';

export type {
  IntersectionObserverWrapperProps,
  LazyContentProps,
  VirtualizedListProps,
  IntersectionObserverOptions,
  UseIntersectionObserverReturn,
} from './intersection-observer.types';
