/**
 * Lazy Loading Admin Components
 * 
 * Provides lazy-loaded components for admin interfaces to improve initial page load
 * performance and reduce bundle size.
 * 
 * Requirements: 7.3, 7.5
 */
"use client";

import React, { Suspense, lazy } from 'react';
import { ErrorBoundary } from 'react-error-boundary';
// Loading components
const LoadingSpinner = () => (
  <div className="flex items-center justify-center p-8 sm:p-4 md:p-6">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 "></div>
  </div>
);
const LoadingCard = ({ title }: { title: string }) => (
  <div className="bg-white shadow rounded-lg p-6 sm:p-4 md:p-6">
    <div className="animate-pulse">
      <div className="h-6 bg-gray-200 rounded w-1/3 mb-4 "></div>
      <div className="space-y-3">
        <div className="h-4 bg-gray-200 rounded"></div>
        <div className="h-4 bg-gray-200 rounded w-5/6 "></div>
        <div className="h-4 bg-gray-200 rounded w-4/6 "></div>
      </div>
    </div>
  </div>
);
const LoadingTable = () => (
  <div className="bg-white shadow rounded-lg">
    <div className="px-6 py-4 border-b border-gray-200">
      <div className="animate-pulse h-6 bg-gray-200 rounded w-1/4 "></div>
    </div>
    <div className="p-6 sm:p-4 md:p-6">
      <div className="animate-pulse space-y-4">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="flex space-x-4">
            <div className="h-4 bg-gray-200 rounded w-1/4 "></div>
            <div className="h-4 bg-gray-200 rounded w-1/6 "></div>
            <div className="h-4 bg-gray-200 rounded w-1/8 "></div>
            <div className="h-4 bg-gray-200 rounded w-1/6 "></div>
            <div className="h-4 bg-gray-200 rounded w-1/8 "></div>
          </div>
        ))}
      </div>
    </div>
  </div>
);
const LoadingDashboard = () => (
  <div className="space-y-6">
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="bg-white shadow rounded-lg p-6 sm:p-4 md:p-6">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-2/3 mb-2 "></div>
            <div className="h-8 bg-gray-200 rounded w-1/2 "></div>
          </div>
        </div>
      ))}
    </div>
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <LoadingCard title="Recent Activity" />
      <LoadingCard title="System Status" />
    </div>
  </div>
);
// Error fallback component
const ErrorFallback = ({ error, resetErrorBoundary }: { error: Error; resetErrorBoundary: () => void }) => (
  <div className="bg-red-50 border border-red-200 rounded-lg p-6 sm:p-4 md:p-6">
    <div className="flex items-center">
      <div className="flex-shrink-0">
        <svg className="h-5 w-5 text-red-400 " viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
        </svg>
      </div>
      <div className="ml-3">
        <h3 className="text-sm font-medium text-red-800 md:text-base lg:text-lg">
        </h3>
        <div className="mt-2 text-sm text-red-700 md:text-base lg:text-lg">
          <p>{error.message}</p>
        </div>
        <div className="mt-4">
          <button
            onClick={resetErrorBoundary}
            className="bg-red-100 px-3 py-2 rounded-md text-sm font-medium text-red-800 hover:bg-red-200 md:text-base lg:text-lg"
           aria-label="Button">
          </button>
        </div>
      </div>
    </div>
  </div>
);
// Lazy-loaded components
const LazyUserManagementTable = lazy(() => 
  import('./BulkUserOperations').then(module => ({ default: module.BulkUserOperations })) ); const LazyAuditLogViewer = lazy(() => import('./audit/AuditLogViewer') ); const LazySystemConfigurationPanel = lazy(() => import('./SystemConfigurationPanel') ); const LazySecuritySettingsPanel = lazy(() => import('./SecuritySettingsPanel') ); const LazyAdminManagementInterface = lazy(() => import('./AdminManagementInterface') ); // Wrapper components with error boundaries and loading states export const UserManagementTable = (props: any) => ( <ErrorBoundary FallbackComponent={ErrorFallback}> from "@/lib/placeholder";
    <Suspense fallback={<LoadingTable />}>
      <LazyUserManagementTable {...props} />
    </Suspense>
  </ErrorBoundary>
);
export const VirtualizedUserTable = (props: any) => (
  <ErrorBoundary FallbackComponent={ErrorFallback}>
    <Suspense fallback={<LoadingTable />}>
      <LazyVirtualizedUserTable {...props} />
    </Suspense>
  </ErrorBoundary>
);
export const AdminDashboard = (props: any) => (
  <ErrorBoundary FallbackComponent={ErrorFallback}>
    <Suspense fallback={<LoadingDashboard />}>
      <LazyAdminDashboard {...props} />
    </Suspense>
  </ErrorBoundary>
);
export const SuperAdminDashboard = (props: any) => (
  <ErrorBoundary FallbackComponent={ErrorFallback}>
    <Suspense fallback={<LoadingDashboard />}>
      <LazySuperAdminDashboard {...props} />
    </Suspense>
  </ErrorBoundary>
);
export const UserCreationForm = (props: any) => (
  <ErrorBoundary FallbackComponent={ErrorFallback}>
    <Suspense fallback={<LoadingCard title="User Creation Form" />}>
      <LazyUserCreationForm {...props} />
    </Suspense>
  </ErrorBoundary>
);
export const BulkUserOperations = (props: any) => (
  <ErrorBoundary FallbackComponent={ErrorFallback}>
    <Suspense fallback={<LoadingCard title="Bulk Operations" />}>
      <LazyBulkUserOperations {...props} />
    </Suspense>
  </ErrorBoundary>
);
export const AuditLogViewer = (props: any) => (
  <ErrorBoundary FallbackComponent={ErrorFallback}>
    <Suspense fallback={<LoadingTable />}>
      <LazyAuditLogViewer {...props} />
    </Suspense>
  </ErrorBoundary>
);
export const SystemConfigurationPanel = (props: any) => (
  <ErrorBoundary FallbackComponent={ErrorFallback}>
    <Suspense fallback={<LoadingCard title="System Configuration" />}>
      <LazySystemConfigurationPanel {...props} />
    </Suspense>
  </ErrorBoundary>
);
export const SecuritySettingsPanel = (props: any) => (
  <ErrorBoundary FallbackComponent={ErrorFallback}>
    <Suspense fallback={<LoadingCard title="Security Settings" />}>
      <LazySecuritySettingsPanel {...props} />
    </Suspense>
  </ErrorBoundary>
);
export const AdminManagementInterface = (props: any) => (
  <ErrorBoundary FallbackComponent={ErrorFallback}>
    <Suspense fallback={<LoadingCard title="Admin Management" />}>
      <LazyAdminManagementInterface {...props} />
    </Suspense>
  </ErrorBoundary>
);
// Higher-order component for lazy loading with custom loading state
export function withLazyLoading<T extends Record<string, any>>(
  Component: React.ComponentType<T>,
  LoadingComponent: React.ComponentType = LoadingSpinner
) {
  const LazyComponent = lazy(() => Promise.resolve({ default: Component }));
  return (props: T) => (
    <ErrorBoundary FallbackComponent={ErrorFallback}>
      <Suspense fallback={<LoadingComponent />}>
        <LazyComponent {...(props as any)} />
      </Suspense>
    </ErrorBoundary>
  );
}
// Preload functions for better UX
export const preloadAdminComponents = {
  userManagement: () => import('./UserManagementTable'),
  virtualizedTable: () => import('./VirtualizedUserTable'),
  adminDashboard: () => import('./AdminDashboard'),
  superAdminDashboard: () => import('./SuperAdminDashboard'),
  userCreation: () => import('./UserCreationForm'),
  bulkOperations: () => import('./BulkUserOperations'),
  auditLogs: () => import('./audit/AuditLogViewer'),
  systemConfig: () => import('./SystemConfigurationPanel'),
  securitySettings: () => import('./SecuritySettingsPanel'),
  adminManagement: () => import('./AdminManagementInterface'),
};
// Preload all admin components
export const preloadAllAdminComponents = () => {
  Object.values(preloadAdminComponents).forEach(preload => {
    preload().catch(error => {


};
// Component registry for dynamic loading
export const adminComponentRegistry = {
};
// Dynamic component loader
export function loadAdminComponent(componentName: keyof typeof adminComponentRegistry) {
  const Component = adminComponentRegistry[componentName];
  if (!Component) {
    throw new Error(`Admin component "${componentName}" not found`);
  }
  return Component;
}
// Performance monitoring hook for lazy components
export function useComponentLoadTime(componentName: string) {
  React.useEffect(() => {
    const startTime = performance.now();
    return () => {
      const endTime = performance.now();
      const loadTime = endTime - startTime;
      // Log component load time for performance monitoring
      console.debug(`Component ${componentName} loaded in ${loadTime.toFixed(2)}ms`);
      // Send to analytics if available
      if (typeof window !== 'undefined' && (window as any).gtag) {
        (window as any).gtag('event', 'component_load_time', {
          component_name: componentName,
          load_time: Math.round(loadTime),

      }
    };
  }, [componentName]);
}
// Bundle size analyzer helper
export const getComponentBundleInfo = () => {
  if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
    return {
      totalChunks: document.querySelectorAll('script[src*="chunk"]').length,
      loadedComponents: Object.keys(adminComponentRegistry),
      memoryUsage: (performance as any).memory ? {
        used: (performance as any).memory.usedJSHeapSize,
        total: (performance as any).memory.totalJSHeapSize,
        limit: (performance as any).memory.jsHeapSizeLimit,
      } : null,
    };
  }
  return null;
};
