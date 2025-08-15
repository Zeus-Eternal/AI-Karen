import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { QueryProvider } from './QueryProvider';
import { StoreProvider } from './StoreProvider';

interface AppProviderProps {
  children: React.ReactNode;
}

/**
 * Main application provider that combines all state management and performance optimizations
 * 
 * Provider hierarchy:
 * 1. BrowserRouter - Routing context
 * 2. QueryProvider - React Query with error boundaries and suspense
 * 3. StoreProvider - Zustand stores with persistence and debugging
 * 4. Children - Application components
 */
export const AppProvider: React.FC<AppProviderProps> = ({ children }) => {
  return (
    <BrowserRouter>
      <QueryProvider>
        <StoreProvider>
          {children}
        </StoreProvider>
      </QueryProvider>
    </BrowserRouter>
  );
};

export default AppProvider;