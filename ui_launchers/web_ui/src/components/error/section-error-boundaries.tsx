'use client';

import React, { ReactNode } from 'react';
import { useEffect } from 'react';
import { ModernErrorBoundary } from './modern-error-boundary';
export { ModernErrorBoundary } from './modern-error-boundary';

interface SectionErrorBoundaryProps {
  children: ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  className?: string;
}

/**
 * Error boundary specifically for the sidebar section
 */
export function SidebarErrorBoundary({ children, onError, className }: SectionErrorBoundaryProps) {

  // Focus management for accessibility
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        // Handle escape key
        onClose?.();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  return (
    <ModernErrorBoundary
      section="sidebar"
      maxRetries={2}
      enableAutoRetry={true}
      retryDelay={1500}
      enableErrorReporting={true}
      onError={onError}
      className={className}
      fallback={(error, errorInfo, retry) => (
        <div className="p-4 border border-destructive/50 rounded-lg bg-destructive/5 sm:p-4 md:p-6">
          <div className="text-sm font-medium text-destructive mb-2 md:text-base lg:text-lg">
            Sidebar Error
          </div>
          <div className="text-xs text-muted-foreground mb-3 sm:text-sm md:text-base">
            The sidebar encountered an error. You can continue using other parts of the app.
          </div>
          <button
            onClick={retry}
            className="text-xs bg-destructive text-destructive-foreground px-2 py-1 rounded hover:bg-destructive/90 sm:text-sm md:text-base"
           aria-label="Button">
            Retry Sidebar
          </button>
        </div>
      )}
    >
      {children}
    </ModernErrorBoundary>
  );
}

/**
 * Error boundary specifically for the main content area
 */
export function MainContentErrorBoundary({ children, onError, className }: SectionErrorBoundaryProps) {
  return (
    <ModernErrorBoundary
      section="main-content"
      maxRetries={3}
      enableAutoRetry={true}
      retryDelay={2000}
      enableErrorReporting={true}
      showTechnicalDetails={false}
      onError={onError}
      className={className}
    >
      {children}
    </ModernErrorBoundary>
  );
}

/**
 * Error boundary specifically for the right panel
 */
export function RightPanelErrorBoundary({ children, onError, className }: SectionErrorBoundaryProps) {
  return (
    <ModernErrorBoundary
      section="right-panel"
      maxRetries={2}
      enableAutoRetry={true}
      retryDelay={1500}
      enableErrorReporting={true}
      onError={onError}
      className={className}
      fallback={(error, errorInfo, retry) => (
        <div className="h-full flex items-center justify-center p-4 sm:p-4 md:p-6">
          <div className="text-center space-y-3 max-w-sm">
            <div className="text-sm font-medium text-destructive md:text-base lg:text-lg">
              Right Panel Error
            </div>
            <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
              The right panel encountered an error. The main application is still functional.
            </div>
            <button
              onClick={retry}
              className="text-xs bg-primary text-primary-foreground px-3 py-1.5 rounded hover:bg-primary/90 sm:text-sm md:text-base"
             aria-label="Button">
              Retry Panel
            </button>
          </div>
        </div>
      )}
    >
      {children}
    </ModernErrorBoundary>
  );
}

/**
 * Error boundary specifically for chat components
 */
export function ChatErrorBoundary({ children, onError, className }: SectionErrorBoundaryProps) {
  return (
    <ModernErrorBoundary
      section="chat"
      maxRetries={3}
      enableAutoRetry={false} // Don't auto-retry chat to avoid message loss
      retryDelay={2000}
      enableErrorReporting={true}
      onError={onError}
      className={className}
      fallback={(error, errorInfo, retry) => (
        <div className="p-4 border border-destructive/50 rounded-lg bg-destructive/5 m-4 sm:p-4 md:p-6">
          <div className="text-sm font-medium text-destructive mb-2 md:text-base lg:text-lg">
            Chat Error
          </div>
          <div className="text-xs text-muted-foreground mb-3 sm:text-sm md:text-base">
            The chat interface encountered an error. Your conversation history is preserved.
          </div>
          <div className="flex gap-2">
            <button
              onClick={retry}
              className="text-xs bg-primary text-primary-foreground px-2 py-1 rounded hover:bg-primary/90 sm:text-sm md:text-base"
             aria-label="Button">
              Retry Chat
            </button>
            <button
              onClick={() = aria-label="Button"> window.location.reload()}
              className="text-xs bg-secondary text-secondary-foreground px-2 py-1 rounded hover:bg-secondary/90 sm:text-sm md:text-base"
            >
              Refresh Page
            </button>
          </div>
        </div>
      )}
    >
      {children}
    </ModernErrorBoundary>
  );
}

/**
 * Error boundary specifically for form components
 */
export function FormErrorBoundary({ children, onError, className }: SectionErrorBoundaryProps) {
  return (
    <ModernErrorBoundary
      section="form"
      maxRetries={2}
      enableAutoRetry={false} // Don't auto-retry forms to avoid data loss
      retryDelay={1000}
      enableErrorReporting={true}
      onError={onError}
      className={className}
      fallback={(error, errorInfo, retry) => (
        <div className="p-4 border border-destructive/50 rounded-lg bg-destructive/5 sm:p-4 md:p-6">
          <div className="text-sm font-medium text-destructive mb-2 md:text-base lg:text-lg">
            Form Error
          </div>
          <div className="text-xs text-muted-foreground mb-3 sm:text-sm md:text-base">
            The form encountered an error. Your input data may be preserved in your browser.
          </div>
          <button
            onClick={retry}
            className="text-xs bg-primary text-primary-foreground px-2 py-1 rounded hover:bg-primary/90 sm:text-sm md:text-base"
           aria-label="Button">
            Retry Form
          </button>
        </div>
      )}
    >
      {children}
    </ModernErrorBoundary>
  );
}

/**
 * Error boundary specifically for modal/dialog components
 */
export function ModalErrorBoundary({ children, onError, className }: SectionErrorBoundaryProps) {
  return (
    <ModernErrorBoundary
      section="modal"
      maxRetries={2}
      enableAutoRetry={true}
      retryDelay={1000}
      enableErrorReporting={true}
      onError={onError}
      className={className}
      fallback={(error, errorInfo, retry) => (
        <div className="p-6 text-center space-y-4 sm:p-4 md:p-6">
          <div className="text-sm font-medium text-destructive md:text-base lg:text-lg">
            Modal Error
          </div>
          <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
            This dialog encountered an error.
          </div>
          <div className="flex justify-center gap-2">
            <button
              onClick={retry}
              className="text-xs bg-primary text-primary-foreground px-3 py-1.5 rounded hover:bg-primary/90 sm:text-sm md:text-base"
             aria-label="Button">
              Retry
            </button>
            <button
              onClick={() = aria-label="Button"> {
                // Close modal by dispatching escape key event
                const escEvent = new KeyboardEvent('keydown', { key: 'Escape' });
                document.dispatchEvent(escEvent);
              }}
              className="text-xs bg-secondary text-secondary-foreground px-3 py-1.5 rounded hover:bg-secondary/90 sm:text-sm md:text-base"
            >
              Close
            </button>
          </div>
        </div>
      )}
    >
      {children}
    </ModernErrorBoundary>
  );
}

/**
 * Error boundary specifically for data visualization components
 */
export function ChartErrorBoundary({ children, onError, className }: SectionErrorBoundaryProps) {
  return (
    <ModernErrorBoundary
      section="chart"
      maxRetries={2}
      enableAutoRetry={true}
      retryDelay={1500}
      enableErrorReporting={true}
      onError={onError}
      className={className}
      fallback={(error, errorInfo, retry) => (
        <div className="h-64 flex items-center justify-center border border-dashed border-muted-foreground/25 rounded-lg">
          <div className="text-center space-y-3">
            <div className="text-sm font-medium text-muted-foreground md:text-base lg:text-lg">
              Chart Error
            </div>
            <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
              Unable to render chart data
            </div>
            <button
              onClick={retry}
              className="text-xs bg-primary text-primary-foreground px-3 py-1.5 rounded hover:bg-primary/90 sm:text-sm md:text-base"
             aria-label="Button">
              Retry Chart
            </button>
          </div>
        </div>
      )}
    >
      {children}
    </ModernErrorBoundary>
  );
}

/**
 * Error boundary specifically for widget components
 */
export function WidgetErrorBoundary({ children, onError, className }: SectionErrorBoundaryProps) {
  return (
    <ModernErrorBoundary
      section="widget"
      maxRetries={2}
      enableAutoRetry={true}
      retryDelay={1000}
      enableErrorReporting={true}
      onError={onError}
      className={className}
      fallback={(error, errorInfo, retry) => (
        <div className="p-4 border border-dashed border-muted-foreground/25 rounded-lg bg-muted/25 sm:p-4 md:p-6">
          <div className="text-center space-y-2">
            <div className="text-sm font-medium text-muted-foreground md:text-base lg:text-lg">
              Widget Error
            </div>
            <button
              onClick={retry}
              className="text-xs bg-primary text-primary-foreground px-2 py-1 rounded hover:bg-primary/90 sm:text-sm md:text-base"
             aria-label="Button">
              Retry
            </button>
          </div>
        </div>
      )}
    >
      {children}
    </ModernErrorBoundary>
  );
}
