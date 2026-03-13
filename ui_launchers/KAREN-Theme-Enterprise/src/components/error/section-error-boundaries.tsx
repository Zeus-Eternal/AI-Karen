"use client";

import React, { ReactNode } from "react";
import type { ErrorInfo } from "react";
import { Button } from "@/components/ui/button";
import { ModernErrorBoundary } from "./modern-error-boundary";

interface SectionErrorBoundaryProps {
  children: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  className?: string;
}

/**
 * Error boundary specifically for the sidebar section
 */
export function SidebarErrorBoundary({
  children,
  onError,
  className,
}: SectionErrorBoundaryProps) {
  return (
    <ModernErrorBoundary
      section="sidebar"
      maxRetries={2}
      enableAutoRetry
      retryDelay={1500}
      enableErrorReporting
      onError={onError}
      className={className}
      fallback={(error, _errorInfo, retry) => (
        <div className="p-4 border border-destructive/50 rounded-lg bg-destructive/5 sm:p-4 md:p-6">
          <div className="text-sm font-medium text-destructive mb-2 md:text-base lg:text-lg">
            Sidebar crashed
          </div>
          <div className="text-xs text-muted-foreground mb-3 sm:text-sm md:text-base">
            The sidebar encountered an error. You can continue using other parts of the app.
          </div>
          <Button
            onClick={retry}
            className="text-xs bg-destructive text-destructive-foreground px-2 py-1 rounded hover:bg-destructive/90 sm:text-sm md:text-base"
            aria-label="Retry loading sidebar"
          >
            Retry
          </Button>
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
export function MainContentErrorBoundary({
  children,
  onError,
  className,
}: SectionErrorBoundaryProps) {
  return (
    <ModernErrorBoundary
      section="main-content"
      maxRetries={3}
      enableAutoRetry
      retryDelay={2000}
      enableErrorReporting
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
export function RightPanelErrorBoundary({
  children,
  onError,
  className,
}: SectionErrorBoundaryProps) {
  return (
    <ModernErrorBoundary
      section="right-panel"
      maxRetries={2}
      enableAutoRetry
      retryDelay={1500}
      enableErrorReporting
      onError={onError}
      className={className}
      fallback={(error, _errorInfo, retry) => (
        <div className="h-full flex items-center justify-center p-4 sm:p-4 md:p-6">
          <div className="text-center space-y-3 max-w-sm">
            <div className="text-sm font-medium text-destructive md:text-base lg:text-lg">
              Right panel crashed
            </div>
            <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
              The right panel encountered an error. The main application is still functional.
            </div>
            <Button
              onClick={retry}
              className="text-xs bg-primary text-primary-foreground px-3 py-1.5 rounded hover:bg-primary/90 sm:text-sm md:text-base"
              aria-label="Retry loading right panel"
            >
              Retry
            </Button>
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
export function ChatErrorBoundary({
  children,
  onError,
  className,
}: SectionErrorBoundaryProps) {
  return (
    <ModernErrorBoundary
      section="chat"
      maxRetries={3}
      enableAutoRetry={false} // Don't auto-retry chat to avoid message loss
      retryDelay={2000}
      enableErrorReporting
      onError={onError}
      className={className}
      fallback={(error, _errorInfo, retry) => (
        <div className="p-4 border border-destructive/50 rounded-lg bg-destructive/5 m-4 sm:p-4 md:p-6">
          <div className="text-sm font-medium text-destructive mb-2 md:text-base lg:text-lg">
            Chat crashed
          </div>
          <div className="text-xs text-muted-foreground mb-3 sm:text-sm md:text-base">
            The chat interface encountered an error. Your conversation history is preserved.
          </div>
          <div className="flex gap-2">
            <Button
              onClick={retry}
              className="text-xs bg-primary text-primary-foreground px-2 py-1 rounded hover:bg-primary/90 sm:text-sm md:text-base"
              aria-label="Retry chat"
            >
              Retry
            </Button>
            <Button
              onClick={() => window.location.reload()}
              className="text-xs bg-secondary text-secondary-foreground px-2 py-1 rounded hover:bg-secondary/90 sm:text-sm md:text-base"
              aria-label="Reload page"
            >
              Reload
            </Button>
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
export function FormErrorBoundary({
  children,
  onError,
  className,
}: SectionErrorBoundaryProps) {
  return (
    <ModernErrorBoundary
      section="form"
      maxRetries={2}
      enableAutoRetry={false} // Don't auto-retry forms to avoid data loss
      retryDelay={1000}
      enableErrorReporting
      onError={onError}
      className={className}
      fallback={(error, _errorInfo, retry) => (
        <div className="p-4 border border-destructive/50 rounded-lg bg-destructive/5 sm:p-4 md:p-6">
          <div className="text-sm font-medium text-destructive mb-2 md:text-base lg:text-lg">
            Form crashed
          </div>
          <div className="text-xs text-muted-foreground mb-3 sm:text-sm md:text-base">
            The form encountered an error. Your input may be preserved locally.
          </div>
          <Button
            onClick={retry}
            className="text-xs bg-primary text-primary-foreground px-2 py-1 rounded hover:bg-primary/90 sm:text-sm md:text-base"
            aria-label="Retry form"
          >
            Retry
          </Button>
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
export function ModalErrorBoundary({
  children,
  onError,
  className,
}: SectionErrorBoundaryProps) {
  return (
    <ModernErrorBoundary
      section="modal"
      maxRetries={2}
      enableAutoRetry
      retryDelay={1000}
      enableErrorReporting
      onError={onError}
      className={className}
      fallback={(error, _errorInfo, retry) => (
        <div className="p-6 text-center space-y-4 sm:p-4 md:p-6">
          <div className="text-sm font-medium text-destructive md:text-base lg:text-lg">
            Dialog crashed
          </div>
          <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
            This dialog encountered an error.
          </div>
          <div className="flex justify-center gap-2">
            <Button
              onClick={retry}
              className="text-xs bg-primary text-primary-foreground px-3 py-1.5 rounded hover:bg-primary/90 sm:text-sm md:text-base"
              aria-label="Retry dialog"
            >
              Retry
            </Button>
            <Button
              onClick={() => {
                const escEvent = new KeyboardEvent("keydown", { key: "Escape" });
                document.dispatchEvent(escEvent);
              }}
              className="text-xs bg-secondary text-secondary-foreground px-3 py-1.5 rounded hover:bg-secondary/90 sm:text-sm md:text-base"
              aria-label="Close dialog"
            >
              Close
            </Button>
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
export function ChartErrorBoundary({
  children,
  onError,
  className,
}: SectionErrorBoundaryProps) {
  return (
    <ModernErrorBoundary
      section="chart"
      maxRetries={2}
      enableAutoRetry
      retryDelay={1500}
      enableErrorReporting
      onError={onError}
      className={className}
      fallback={(error, _errorInfo, retry) => (
        <div className="h-64 flex items-center justify-center border border-dashed border-muted-foreground/25 rounded-lg">
          <div className="text-center space-y-3">
            <div className="text-sm font-medium text-muted-foreground md:text-base lg:text-lg">
              Chart crashed
            </div>
            <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
              We couldn’t render this visualization.
            </div>
            <Button
              onClick={retry}
              className="text-xs bg-primary text-primary-foreground px-3 py-1.5 rounded hover:bg-primary/90 sm:text-sm md:text-base"
              aria-label="Retry chart"
            >
              Retry
            </Button>
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
export function WidgetErrorBoundary({
  children,
  onError,
  className,
}: SectionErrorBoundaryProps) {
  return (
    <ModernErrorBoundary
      section="widget"
      maxRetries={2}
      enableAutoRetry
      retryDelay={1000}
      enableErrorReporting
      onError={onError}
      className={className}
      fallback={(error, _errorInfo, retry) => (
        <div className="p-4 border border-dashed border-muted-foreground/25 rounded-lg bg-muted/25 sm:p-4 md:p-6">
          <div className="text-center space-y-2">
            <div className="text-sm font-medium text-muted-foreground md:text-base lg:text-lg">
              Widget crashed
            </div>
            <Button
              onClick={retry}
              className="text-xs bg-primary text-primary-foreground px-2 py-1 rounded hover:bg-primary/90 sm:text-sm md:text-base"
              aria-label="Retry widget"
            >
              Retry
            </Button>
          </div>
        </div>
      )}
    >
      {children}
    </ModernErrorBoundary>
  );
}
