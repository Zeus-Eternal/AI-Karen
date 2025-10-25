'use client';

import React, { ReactNode } from 'react';
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
        <div className="p-4 border border-destructive/50 rounded-lg bg-destructive/5">
          <div className="text-sm font-medium text-destructive mb-2">
            Sidebar Error
          </div>
          <div className="text-xs text-muted-foreground mb-3">
            The sidebar encountered an error. You can continue using other parts of the app.
          </div>
          <button
            onClick={retry}
            className="text-xs bg-destructive text-destructive-foreground px-2 py-1 rounded hover:bg-destructive/90"
          >
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
        <div className="h-full flex items-center justify-center p-4">
          <div className="text-center space-y-3 max-w-sm">
            <div className="text-sm font-medium text-destructive">
              Right Panel Error
            </div>
            <div className="text-xs text-muted-foreground">
              The right panel encountered an error. The main application is still functional.
            </div>
            <button
              onClick={retry}
              className="text-xs bg-primary text-primary-foreground px-3 py-1.5 rounded hover:bg-primary/90"
            >
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
        <div className="p-4 border border-destructive/50 rounded-lg bg-destructive/5 m-4">
          <div className="text-sm font-medium text-destructive mb-2">
            Chat Error
          </div>
          <div className="text-xs text-muted-foreground mb-3">
            The chat interface encountered an error. Your conversation history is preserved.
          </div>
          <div className="flex gap-2">
            <button
              onClick={retry}
              className="text-xs bg-primary text-primary-foreground px-2 py-1 rounded hover:bg-primary/90"
            >
              Retry Chat
            </button>
            <button
              onClick={() => window.location.reload()}
              className="text-xs bg-secondary text-secondary-foreground px-2 py-1 rounded hover:bg-secondary/90"
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
        <div className="p-4 border border-destructive/50 rounded-lg bg-destructive/5">
          <div className="text-sm font-medium text-destructive mb-2">
            Form Error
          </div>
          <div className="text-xs text-muted-foreground mb-3">
            The form encountered an error. Your input data may be preserved in your browser.
          </div>
          <button
            onClick={retry}
            className="text-xs bg-primary text-primary-foreground px-2 py-1 rounded hover:bg-primary/90"
          >
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
        <div className="p-6 text-center space-y-4">
          <div className="text-sm font-medium text-destructive">
            Modal Error
          </div>
          <div className="text-xs text-muted-foreground">
            This dialog encountered an error.
          </div>
          <div className="flex justify-center gap-2">
            <button
              onClick={retry}
              className="text-xs bg-primary text-primary-foreground px-3 py-1.5 rounded hover:bg-primary/90"
            >
              Retry
            </button>
            <button
              onClick={() => {
                // Close modal by dispatching escape key event
                const escEvent = new KeyboardEvent('keydown', { key: 'Escape' });
                document.dispatchEvent(escEvent);
              }}
              className="text-xs bg-secondary text-secondary-foreground px-3 py-1.5 rounded hover:bg-secondary/90"
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
            <div className="text-sm font-medium text-muted-foreground">
              Chart Error
            </div>
            <div className="text-xs text-muted-foreground">
              Unable to render chart data
            </div>
            <button
              onClick={retry}
              className="text-xs bg-primary text-primary-foreground px-3 py-1.5 rounded hover:bg-primary/90"
            >
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
        <div className="p-4 border border-dashed border-muted-foreground/25 rounded-lg bg-muted/25">
          <div className="text-center space-y-2">
            <div className="text-sm font-medium text-muted-foreground">
              Widget Error
            </div>
            <button
              onClick={retry}
              className="text-xs bg-primary text-primary-foreground px-2 py-1 rounded hover:bg-primary/90"
            >
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
