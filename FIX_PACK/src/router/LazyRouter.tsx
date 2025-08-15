import React, { Suspense, useEffect } from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';
import { ErrorBoundary } from 'react-error-boundary';
import { createRouteConfig, preloadComponents, trackChunkLoad } from '../utils/codeSplitting';
import { ComponentSkeleton, PanelSkeleton } from '../components/lazy/LazyComponents';

// Route error fallback
const RouteErrorFallback: React.FC<{ error: Error; resetErrorBoundary: () => void }> = ({
  error,
  resetErrorBoundary
}) => (
  <div className="flex-1 flex items-center justify-center p-6">
    <div className="text-center max-w-md">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
        Failed to load page
      </h2>
      <p className="text-gray-600 dark:text-gray-400 mb-4">
        {error.message}
      </p>
      <button
        onClick={resetErrorBoundary}
        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
      >
        Try again
      </button>
    </div>
  </div>
);

// Route loading fallback
const RouteLoadingFallback: React.FC = () => (
  <div className="flex-1 flex items-center justify-center p-6">
    <ComponentSkeleton className="w-full max-w-2xl" />
  </div>
);

// Route configurations with lazy loading
const routeConfigs = createRouteConfig({
  '/': {
    importFn: () => import('../routes/ChatRoute'),
    preload: true,
    chunkName: 'chat-route',
  },
  '/chat': {
    importFn: () => import('../routes/ChatRoute'),
    preload: true,
    chunkName: 'chat-route',
  },
  '/chat/:conversationId': {
    importFn: () => import('../routes/ChatRoute'),
    preload: true,
    chunkName: 'chat-route',
  },
  '/settings': {
    importFn: () => import('../routes/SettingsRoute'),
    preload: false,
    chunkName: 'settings-route',
  },
  '/settings/:section': {
    importFn: () => import('../routes/SettingsRoute'),
    preload: false,
    chunkName: 'settings-route',
  },
  '/analytics': {
    importFn: () => import('../routes/AnalyticsRoute'),
    preload: false,
    chunkName: 'analytics-route',
  },
  '/help': {
    importFn: () => import('../routes/HelpRoute'),
    preload: false,
    chunkName: 'help-route',
  },
  '/profile': {
    importFn: () => import('../routes/ProfileRoute'),
    preload: false,
    chunkName: 'profile-route',
  },
});

// Preload critical routes
const preloadCriticalRoutes = async () => {
  const criticalRoutes = routeConfigs
    .filter(route => route.preload)
    .map(route => () => import('../routes/ChatRoute')); // Adjust imports as needed

  await preloadComponents(criticalRoutes);
};

// Route component with performance tracking
const TrackedRoute: React.FC<{
  component: React.LazyExoticComponent<React.ComponentType<any>>;
  chunkName?: string;
}> = ({ component: Component, chunkName }) => {
  useEffect(() => {
    if (chunkName) {
      const startTime = performance.now();
      
      // Track when component starts loading
      const loadPromise = Component._payload?._result || Promise.resolve();
      
      loadPromise.then(() => {
        trackChunkLoad(chunkName, startTime);
      }).catch((error: Error) => {
        console.error(`Failed to load chunk ${chunkName}:`, error);
      });
    }
  }, [Component, chunkName]);

  return <Component />;
};

// Main lazy router component
export const LazyRouter: React.FC = () => {
  const location = useLocation();

  // Preload critical routes on mount
  useEffect(() => {
    preloadCriticalRoutes().catch(error => {
      console.warn('Failed to preload critical routes:', error);
    });
  }, []);

  // Prefetch routes based on current location
  useEffect(() => {
    const currentPath = location.pathname;
    
    // Prefetch likely next routes based on current route
    if (currentPath === '/' || currentPath.startsWith('/chat')) {
      // User is in chat, likely to visit settings
      import('../routes/SettingsRoute').catch(() => {});
    } else if (currentPath.startsWith('/settings')) {
      // User is in settings, might go back to chat
      import('../routes/ChatRoute').catch(() => {});
    }
  }, [location.pathname]);

  return (
    <ErrorBoundary
      FallbackComponent={RouteErrorFallback}
      onError={(error, errorInfo) => {
        console.error('Route error:', error, errorInfo);
      }}
    >
      <Suspense fallback={<RouteLoadingFallback />}>
        <Routes>
          {routeConfigs.map((route) => (
            <Route
              key={route.path}
              path={route.path}
              element={
                <TrackedRoute
                  component={route.component}
                  chunkName={route.chunkName}
                />
              }
            />
          ))}
          
          {/* Catch-all route for 404 */}
          <Route
            path="*"
            element={
              <div className="flex-1 flex items-center justify-center p-6">
                <div className="text-center">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
                    Page not found
                  </h2>
                  <p className="text-gray-600 dark:text-gray-400">
                    The page you're looking for doesn't exist.
                  </p>
                </div>
              </div>
            }
          />
        </Routes>
      </Suspense>
    </ErrorBoundary>
  );
};

export default LazyRouter;