/**
 * Extension Integration Initializer
 * 
 * Ensures the extension integration service is properly initialized
 */

"use client";

import * as React from 'react';
import { useExtensionInitialization } from './use-extension-initialization';
import { safeError } from '../safe-console';

/**
 * Extension Integration Provider Component
 * 
 * Wraps children with extension integration initialization
 */
export function ExtensionIntegrationProvider({ children }: { children: React.ReactNode }) {
  const { initialized, error } = useExtensionInitialization();

  if (error) {
    safeError('ExtensionIntegrationProvider: Extension integration failed to initialize:', error);
    // Still render children even if extension integration fails
    return <>{children}</>;
  }

  if (!initialized) {
    // Extension integration is loading, but don't block the UI
    return <>{children}</>;
  }

  return <>{children}</>;
}
