"use client";

import React from "react";

import ApiErrorBoundary, { type ApiErrorBoundaryProps } from "./ApiErrorBoundary";

export function withApiErrorBoundary<P extends object>(
  Wrapped: React.ComponentType<P>,
  errorBoundaryProps?: Omit<ApiErrorBoundaryProps, "children">
) {
  const WrappedComponent = (props: P) => (
    <ApiErrorBoundary {...errorBoundaryProps}>
      <Wrapped {...props} />
    </ApiErrorBoundary>
  );

  WrappedComponent.displayName = `withApiErrorBoundary(${Wrapped.displayName || Wrapped.name || "Component"})`;

  return WrappedComponent;
}

export default withApiErrorBoundary;
