"use client";

import React from "react";

import GlobalErrorBoundary, { type GlobalErrorBoundaryProps } from "./GlobalErrorBoundary";

export function withGlobalErrorBoundary<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  errorBoundaryProps?: Omit<GlobalErrorBoundaryProps, "children">
) {
  const WithGlobalErrorBoundaryComponent = (props: P) => (
    <GlobalErrorBoundary {...(errorBoundaryProps as GlobalErrorBoundaryProps)}>
      <WrappedComponent {...props} />
    </GlobalErrorBoundary>
  );

  WithGlobalErrorBoundaryComponent.displayName = `withGlobalErrorBoundary(${
    WrappedComponent.displayName || WrappedComponent.name || "Component"
  })`;

  return WithGlobalErrorBoundaryComponent;
}

export default withGlobalErrorBoundary;
