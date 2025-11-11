/**
 * Dynamic Extension Router
 * 
 * Handles dynamic routing for extension pages and components
 */

"use client";

import React, { Suspense, useMemo } from 'react';
import { usePathname } from 'next/navigation';
import { ExtensionRoute } from './extension-integration';
import { useExtensionRoutes } from './hooks';
import { safeError, safeLog } from '../safe-console';
import { Button } from '@/components/ui/button';

export interface DynamicExtensionRouterProps {
  children?: React.ReactNode;
  fallback?: React.ComponentType;
}

/**
 * Dynamic router that renders extension components based on current path
 */
export function DynamicExtensionRouter({ children, fallback: Fallback }: DynamicExtensionRouterProps) {
  const pathname = usePathname();
  const routes = useExtensionRoutes();

  const matchedRoute = useMemo(() => {
    // Find the best matching route
    const exactMatches = routes.filter(route => route.exact && route.path === pathname);
    if (exactMatches.length > 0) {
      return exactMatches[0];
    }

    // Find prefix matches
    const prefixMatches = routes.filter(route => 
      !route.exact && pathname?.startsWith(route.path)
    ).sort((a, b) => b.path.length - a.path.length); // Longest match first

    return prefixMatches[0] || null;
  }, [pathname, routes]);

  if (matchedRoute) {
    safeLog(`DynamicExtensionRouter: Rendering extension route ${matchedRoute.path} for extension ${matchedRoute.extensionId}`);
    
    return (
      <Suspense fallback={<ExtensionLoadingFallback extensionId={matchedRoute.extensionId} />}>
        <ExtensionRouteRenderer route={matchedRoute} />
      </Suspense>
    );
  }

  // No extension route matched, render children or fallback
  if (children) {
    return <>{children}</>;
  }

  if (Fallback) {
    return <Fallback />;
  }

  return null;
}

/**
 * Renders an extension route with proper error boundaries
 */
function ExtensionRouteRenderer({ route }: { route: ExtensionRoute }) {
  const Component = route.component;
  if (!Component) {
    safeError(`DynamicExtensionRouter: Missing component for route ${route.path}`);
    return <ExtensionErrorFallback extensionId={route.extensionId} routePath={route.path} />;
  }

  return (
    <ExtensionErrorBoundary extensionId={route.extensionId} routePath={route.path}>
      <div className={`extension-route extension-${route.extensionId}`} data-extension-id={route.extensionId}>
        <Component />
      </div>
    </ExtensionErrorBoundary>
  );
}

/**
 * Loading fallback for extension routes
 */
function ExtensionLoadingFallback({ extensionId }: { extensionId: string }) {
  return (
    <div className="flex items-center justify-center min-h-[400px] bg-gray-50 rounded-lg">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading extension...</p>
        <p className="text-sm text-gray-500">{extensionId}</p>
      </div>
    </div>
  );
}

/**
 * Error boundary for extension routes
 */
interface ExtensionErrorBoundaryProps {
  children: React.ReactNode;
  extensionId: string;
  routePath: string;
}

interface ExtensionErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

class ExtensionErrorBoundary extends React.Component<
  ExtensionErrorBoundaryProps,
  ExtensionErrorBoundaryState
> {
  constructor(props: ExtensionErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    safeError(`ExtensionErrorBoundary: Extension ${this.props.extensionId} route ${this.props.routePath} crashed:`, {
      error,
      errorInfo,
      extensionId: this.props.extensionId,
      routePath: this.props.routePath
    });
  }

  render() {
    if (this.state.hasError) {
      return (
        <ExtensionErrorFallback 
          extensionId={this.props.extensionId} 
          error={this.state.error}
          routePath={this.props.routePath}
        />
      );
    }

    return this.props.children;
  }
}

/**
 * Error fallback for extension routes
 */
function ExtensionErrorFallback({ 
  extensionId, 
  error, 
  routePath 
}: { 
  extensionId: string; 
  error?: unknown;
  routePath?: string;
}) {
  const handleRetry = () => {
    window.location.reload();
  };

  return (
    <div className="flex items-center justify-center min-h-[400px] bg-red-50 rounded-lg border border-red-200">
      <div className="text-center max-w-md p-6">
        <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        </div>
        
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Extension Error</h3>
        <p className="text-gray-600 mb-4">
          The extension "{extensionId}" encountered an error and could not be loaded.
        </p>
        
        {routePath && (
          <p className="text-sm text-gray-500 mb-4">Route: {routePath}</p>
        )}
        
        {error != null && (
          <details className="text-left bg-gray-100 rounded p-3 mb-4">
            <summary className="cursor-pointer text-sm font-medium text-gray-700">
              View technical details
            </summary>
            <pre className="text-xs text-gray-600 mt-2 whitespace-pre-wrap">
              {String(error)}
            </pre>
          </details>
        )}

        <div className="flex gap-3 justify-center">
          <Button
            onClick={handleRetry}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Retry
          </Button>
          <Button
            onClick={() => window.history.back()}
            className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 transition-colors"
          >
            Go Back
          </Button>
        </div>
      </div>
    </div>
  );
}

/**
 * Hook to check if current path matches an extension route
 */
// eslint-disable-next-line react-refresh/only-export-components
export function useIsExtensionRoute() {
  const pathname = usePathname();
  const routes = useExtensionRoutes();

  return useMemo(() => {
    return routes.some(route => 
      route.exact ? route.path === pathname : pathname?.startsWith(route.path)
    );
  }, [pathname, routes]);
}

/**
 * Hook to get the current extension route
 */
// eslint-disable-next-line react-refresh/only-export-components
export function useCurrentExtensionRoute() {
  const pathname = usePathname();
  const routes = useExtensionRoutes();

  return useMemo(() => {
    const exactMatches = routes.filter(route => route.exact && route.path === pathname);
    if (exactMatches.length > 0) {
      return exactMatches[0];
    }

    const prefixMatches = routes.filter(route => 
      !route.exact && pathname?.startsWith(route.path)
    ).sort((a, b) => b.path.length - a.path.length);

    return prefixMatches[0] || null;
  }, [pathname, routes]);
}
