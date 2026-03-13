"use client";

import type { ComponentType } from "react";

import ErrorProvider, { type ErrorProviderProps } from "./ErrorProvider";

export function withErrorProvider<P extends object>(
  Component: ComponentType<P>,
  providerProps?: Omit<ErrorProviderProps, "children">
): ComponentType<P> {
  const WrappedComponent = (props: P) => (
    <ErrorProvider {...providerProps}>
      <Component {...props} />
    </ErrorProvider>
  );

  WrappedComponent.displayName = `WithErrorProvider(${Component.displayName ?? Component.name ?? "Component"})`;

  return WrappedComponent;
}
