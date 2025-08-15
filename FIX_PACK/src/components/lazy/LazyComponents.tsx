import React, { lazy, Suspense } from 'react';
import { ErrorBoundary } from 'react-error-boundary';

// Loading fallback components
export const ComponentSkeleton: React.FC<{ className?: string }> = ({ className }) => (
  <div className={`animate-pulse ${className || ''}`}>
    <div className="bg-gray-200 dark:bg-gray-700 rounded-md h-4 w-3/4 mb-2"></div>
    <div className="bg-gray-200 dark:bg-gray-700 rounded-md h-4 w-1/2 mb-2"></div>
    <div className="bg-gray-200 dark:bg-gray-700 rounded-md h-4 w-5/6"></div>
  </div>
);

export const ModalSkeleton: React.FC = () => (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md animate-pulse">
      <div className="bg-gray-200 dark:bg-gray-700 rounded-md h-6 w-3/4 mb-4"></div>
      <div className="space-y-3">
        <div className="bg-gray-200 dark:bg-gray-700 rounded-md h-4 w-full"></div>
        <div className="bg-gray-200 dark:bg-gray-700 rounded-md h-4 w-5/6"></div>
        <div className="bg-gray-200 dark:bg-gray-700 rounded-md h-4 w-4/5"></div>
      </div>
      <div className="flex justify-end gap-2 mt-6">
        <div className="bg-gray-200 dark:bg-gray-700 rounded-md h-8 w-16"></div>
        <div className="bg-gray-200 dark:bg-gray-700 rounded-md h-8 w-20"></div>
      </div>
    </div>
  </div>
);

export const PanelSkeleton: React.FC = () => (
  <div className="w-full h-full p-4 animate-pulse">
    <div className="bg-gray-200 dark:bg-gray-700 rounded-md h-8 w-1/3 mb-6"></div>
    <div className="space-y-4">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="flex items-center space-x-3">
          <div className="bg-gray-200 dark:bg-gray-700 rounded-full h-10 w-10"></div>
          <div className="flex-1">
            <div className="bg-gray-200 dark:bg-gray-700 rounded-md h-4 w-3/4 mb-2"></div>
            <div className="bg-gray-200 dark:bg-gray-700 rounded-md h-3 w-1/2"></div>
          </div>
        </div>
      ))}
    </div>
  </div>
);

// Error fallback for lazy components
const LazyErrorFallback: React.FC<{ error: Error; resetErrorBoundary: () => void }> = ({
  error,
  resetErrorBoundary
}) => (
  <div className="p-4 border border-red-200 rounded-lg bg-red-50 dark:bg-red-900/20 dark:border-red-800">
    <h3 className="text-red-800 dark:text-red-200 font-medium mb-2">
      Failed to load component
    </h3>
    <p className="text-red-600 dark:text-red-300 text-sm mb-3">
      {error.message}
    </p>
    <button
      onClick={resetErrorBoundary}
      className="px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
    >
      Try again
    </button>
  </div>
);

// HOC for lazy loading with error boundary and suspense
export const withLazyLoading = <P extends object>(
  LazyComponent: React.LazyExoticComponent<React.ComponentType<P>>,
  fallback: React.ReactNode = <ComponentSkeleton />
) => {
  const WrappedComponent: React.FC<P> = (props) => (
    <ErrorBoundary
      FallbackComponent={LazyErrorFallback}
      onError={(error, errorInfo) => {
        console.error('Lazy component error:', error, errorInfo);
      }}
    >
      <Suspense fallback={fallback}>
        <LazyComponent {...props} />
      </Suspense>
    </ErrorBoundary>
  );

  WrappedComponent.displayName = `withLazyLoading(${LazyComponent.displayName || 'Component'})`;
  return WrappedComponent;
};

// Lazy-loaded components
export const LazySettingsModal = withLazyLoading(
  lazy(() => import('../modals/SettingsModal').then(module => ({ default: module.SettingsModal }))),
  <ModalSkeleton />
);

export const LazyUserProfileModal = withLazyLoading(
  lazy(() => import('../modals/UserProfileModal').then(module => ({ default: module.UserProfileModal }))),
  <ModalSkeleton />
);

export const LazyConversationHistoryPanel = withLazyLoading(
  lazy(() => import('../panels/ConversationHistoryPanel').then(module => ({ default: module.ConversationHistoryPanel }))),
  <PanelSkeleton />
);

export const LazyAnalyticsPanel = withLazyLoading(
  lazy(() => import('../panels/AnalyticsPanel').then(module => ({ default: module.AnalyticsPanel }))),
  <PanelSkeleton />
);

export const LazyVoiceInputModal = withLazyLoading(
  lazy(() => import('../modals/VoiceInputModal').then(module => ({ default: module.VoiceInputModal }))),
  <ModalSkeleton />
);

export const LazyFileUploadModal = withLazyLoading(
  lazy(() => import('../modals/FileUploadModal').then(module => ({ default: module.FileUploadModal }))),
  <ModalSkeleton />
);

export const LazyAdvancedSettingsPanel = withLazyLoading(
  lazy(() => import('../panels/AdvancedSettingsPanel').then(module => ({ default: module.AdvancedSettingsPanel }))),
  <PanelSkeleton />
);

// Route-level lazy components
export const LazyChatRoute = withLazyLoading(
  lazy(() => import('../../routes/ChatRoute').then(module => ({ default: module.ChatRoute }))),
  <div className="flex-1 flex items-center justify-center">
    <ComponentSkeleton className="w-full max-w-2xl" />
  </div>
);

export const LazySettingsRoute = withLazyLoading(
  lazy(() => import('../../routes/SettingsRoute').then(module => ({ default: module.SettingsRoute }))),
  <div className="flex-1 p-6">
    <PanelSkeleton />
  </div>
);

export const LazyAnalyticsRoute = withLazyLoading(
  lazy(() => import('../../routes/AnalyticsRoute').then(module => ({ default: module.AnalyticsRoute }))),
  <div className="flex-1 p-6">
    <PanelSkeleton />
  </div>
);

export const LazyHelpRoute = withLazyLoading(
  lazy(() => import('../../routes/HelpRoute').then(module => ({ default: module.HelpRoute }))),
  <div className="flex-1 p-6">
    <ComponentSkeleton className="w-full" />
  </div>
);