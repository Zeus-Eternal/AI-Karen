"use client";

import React from "react";

import { useFirstRunSetup } from "@/hooks/useFirstRunSetup";

import { SetupRouteGuard } from "./SetupRouteGuard";

export const useSetupRouteAccess = () => {
  const { isFirstRun, setupCompleted, isLoading } = useFirstRunSetup();

  return {
    canAccessSetup: !isLoading && isFirstRun && !setupCompleted,
    shouldRedirectToLogin: !isLoading && (!isFirstRun || setupCompleted),
    isCheckingAccess: isLoading,
  };
};

export function withSetupRouteGuard<P extends object>(Component: React.ComponentType<P>) {
  const WrappedComponent = (props: P) => (
    <SetupRouteGuard>
      <Component {...props} />
    </SetupRouteGuard>
  );

  WrappedComponent.displayName = `withSetupRouteGuard(${Component.displayName || Component.name || "Component"})`;

  return WrappedComponent;
}
