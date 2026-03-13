import React, { Suspense, ComponentType, LazyExoticComponent } from 'react';
import { Theme } from '../components/chat/types';

interface LoadingProps {
  theme?: Theme;
  size?: 'small' | 'medium' | 'large';
  message?: string;
}

/**
 * Default loading component to show while lazy-loaded components are being loaded
 */
export const LoadingComponent: React.FC<LoadingProps> = ({ 
  theme, 
  size = 'medium',
  message = 'Loading...' 
}) => {
  const sizeMap = {
    small: { width: '20px', height: '20px' },
    medium: { width: '40px', height: '40px' },
    large: { width: '60px', height: '60px' }
  };

  return (
    <div 
      className="copilot-loading-container"
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: theme?.spacing.md || '16px',
        color: theme?.colors.textSecondary || '#666',
        minHeight: '100px'
      }}
    >
      <div
        className="copilot-loading-spinner"
        style={{
          width: sizeMap[size].width,
          height: sizeMap[size].height,
          border: `3px solid ${theme?.colors.border || '#ddd'}`,
          borderTop: `3px solid ${theme?.colors.primary || '#007bff'}`,
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
          marginBottom: theme?.spacing.sm || '8px'
        }}
      />
      <span>{message}</span>
    </div>
  );
};

/**
 * Error component to show when lazy loading fails
 */
interface ErrorComponentProps {
  theme?: Theme;
  error?: Error;
  onRetry?: () => void;
}

export const ErrorComponent: React.FC<ErrorComponentProps> = ({ 
  theme, 
  error, 
  onRetry 
}) => {
  return (
    <div 
      className="copilot-error-container"
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: theme?.spacing.md || '16px',
        color: theme?.colors.error || '#dc3545',
        backgroundColor: `${theme?.colors.error || '#dc3545'}10`,
        borderRadius: theme?.borderRadius || '8px',
        border: `1px solid ${theme?.colors.error || '#dc3545'}`
      }}
    >
      <div style={{ fontSize: '2rem', marginBottom: theme?.spacing.sm || '8px' }}>⚠️</div>
      <h3 style={{ margin: 0, marginBottom: theme?.spacing.sm || '8px' }}>Error Loading Component</h3>
      <p style={{ margin: 0, textAlign: 'center' }}>
        {error?.message || 'Failed to load component'}
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          style={{
            marginTop: theme?.spacing.sm || '8px',
            padding: `${theme?.spacing.xs || '4px'} ${theme?.spacing.sm || '8px'}`,
            backgroundColor: theme?.colors.primary || '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: theme?.borderRadius || '4px',
            cursor: 'pointer'
          }}
        >
          Retry
        </button>
      )}
    </div>
  );
};

/**
 * Creates a lazy-loaded component with proper loading and error handling
 */
type ComponentWithTheme<T extends ComponentType<unknown>> = React.ComponentProps<T> & {
  theme?: Theme;
};

type PreloadableLazyComponent = {
  _payload?: {
    _result?: (() => unknown) | unknown;
  };
};

export function createLazyComponent<T extends ComponentType<unknown>>(
  importFn: () => Promise<{ default: T }>,
  fallback?: React.ComponentType<LoadingProps>,
  errorFallback?: React.ComponentType<ErrorComponentProps>
): LazyExoticComponent<T> {
  const LazyComponent = React.lazy(importFn);

  const WrappedComponent: React.FC<ComponentWithTheme<T>> = (props) => {
    const [retryCount, setRetryCount] = React.useState(0);
    const [hasError, setHasError] = React.useState(false);

    const handleRetry = () => {
      setRetryCount(prev => prev + 1);
      setHasError(false);
    };

    const ErrorFallback = errorFallback || ErrorComponent;

    return (
      <Suspense
        fallback={fallback ? React.createElement(fallback, { theme: props.theme }) : <LoadingComponent theme={props.theme} />}
      >
        {hasError ? (
          <ErrorFallback
            theme={props.theme}
            onRetry={handleRetry}
          />
        ) : (
          <LazyComponent key={retryCount} {...props} />
        )}
      </Suspense>
    );
  };

  return React.memo(WrappedComponent) as LazyExoticComponent<T>;
}

/**
 * Creates a lazy-loaded component with custom loading and error components
 */
export function createLazyComponentWithCustomFallbacks<T extends ComponentType<unknown>>(
  importFn: () => Promise<{ default: T }>,
  LoadingFallback: React.ComponentType<LoadingProps>,
  ErrorFallback: React.ComponentType<ErrorComponentProps>
): LazyExoticComponent<T> {
  return createLazyComponent(importFn, LoadingFallback, ErrorFallback);
}

/**
 * Utility to preload a component
 */
export function preloadComponent<T extends ComponentType<unknown>>(
  lazyComponent: LazyExoticComponent<T>
): void {
  const preloadableComponent = lazyComponent as LazyExoticComponent<T> & PreloadableLazyComponent;

  if (
    preloadableComponent._payload &&
    typeof preloadableComponent._payload._result === 'function'
  ) {
    preloadableComponent._payload._result();
  }
}

/**
 * Higher-order component for lazy loading with intersection observer
 */
export function withIntersectionObserver<T extends ComponentType<unknown>>(
  Component: LazyExoticComponent<T>,
  options?: IntersectionObserverInit
): React.FC<ComponentWithTheme<T>> {
  const ObservedComponent: React.FC<ComponentWithTheme<T>> = (props) => {
    const [isVisible, setIsVisible] = React.useState(false);
    const ref = React.useRef<HTMLDivElement>(null);
    
    React.useEffect(() => {
      const observer = new IntersectionObserver(([entry]) => {
        if (entry?.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      }, options || { rootMargin: '100px' });
      
      if (ref.current) {
        observer.observe(ref.current);
      }
      
      return () => {
        observer.disconnect();
      };
    }, [options]);
    
    return (
      <div ref={ref} style={{ display: 'contents' }}>
        {isVisible ? <Component {...props} /> : <LoadingComponent theme={props.theme} />}
      </div>
    );
  };
  
  return React.memo(ObservedComponent);
}

/**
 * Hook for lazy loading with intersection observer
 */
export function useIntersectionObserver(
  ref: React.RefObject<Element>,
  options?: IntersectionObserverInit
): boolean {
  const [isVisible, setIsVisible] = React.useState(false);
  
  React.useEffect(() => {
    const observer = new IntersectionObserver(([entry]) => {
      setIsVisible(entry?.isIntersecting ?? false);
    }, options || { rootMargin: '100px' });
    
    if (ref.current) {
      observer.observe(ref.current);
    }
    
    return () => {
      observer.disconnect();
    };
  }, [ref, options]);
  
  return isVisible;
}
