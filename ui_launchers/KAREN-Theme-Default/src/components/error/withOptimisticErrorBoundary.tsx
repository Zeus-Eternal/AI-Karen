"use client";

import React from "react";

import OptimisticErrorBoundary, { type OptimisticErrorBoundaryProps } from "./optimistic-error-boundary";

export function withOptimisticErrorBoundary<P extends object>(
  Wrapped: React.ComponentType<P>,
  errorBoundaryProps?: Omit<OptimisticErrorBoundaryProps, "children">
) {
  const HOC = (props: P) => (
    <OptimisticErrorBoundary {...errorBoundaryProps}>
      <Wrapped {...props} />
    </OptimisticErrorBoundary>
  );

  HOC.displayName = `withOptimisticErrorBoundary(${Wrapped.displayName || Wrapped.name || "Component"})`;

  return HOC;
}

export default withOptimisticErrorBoundary;
