"use client";

import React, { ReactNode } from 'react';
import { AuthProvider } from './AuthContext';
import { HookProvider } from './HookContext';

export interface AppProvidersProps {
  children: ReactNode;
}

/**
 * Combined provider that wraps all existing context providers
 * without duplication. This maintains the existing AuthProvider
 * while adding the new HookProvider for AG-UI integration.
 */
export const AppProviders: React.FC<AppProvidersProps> = ({ children }) => {
  return (
    <AuthProvider>
      <HookProvider>
        {children}
      </HookProvider>
    </AuthProvider>
  );
};