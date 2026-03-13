/**
 * Dynamic AG-Grid Component Wrapper
 * 
 * This component dynamically loads ag-grid to reduce initial bundle size.
 * It provides a loading state while the library is being loaded.
 */

'use client';

import React, { useState, useEffect, forwardRef, useImperativeHandle } from 'react';
import dynamic from 'next/dynamic';

// Type definitions for the dynamic component
export interface DynamicAgGridProps {
  height?: number;
  className?: string;
  children?: React.ReactNode;
}

// Loading component
const AgGridLoadingFallback = ({ height = 400 }: { height?: number }) => (
  <div 
    className="flex items-center justify-center bg-muted/20 rounded-md border"
    style={{ height }}
  >
    <div className="text-center">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"></div>
      <p className="text-sm text-muted-foreground">Loading data grid...</p>
    </div>
  </div>
);

// Dynamic import wrapper for ag-grid styles
const loadAgGridStyles = async () => {
  if (typeof window !== 'undefined') {
    // Use require for CSS imports to avoid TypeScript issues
    if (typeof require !== 'undefined') {
      require('ag-grid-community/styles/ag-grid.css');
      require('ag-grid-community/styles/ag-theme-alpine.css');
    }
  }
};

// Main dynamic component
export const DynamicAgGrid = forwardRef<any, DynamicAgGridProps>(
  ({ height = 400, className, children }, ref) => {
    const [isLoaded, setIsLoaded] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
      const loadComponent = async () => {
        try {
          await loadAgGridStyles();
          setIsLoaded(true);
        } catch (err) {
          setError(err instanceof Error ? err.message : 'Failed to load grid component');
        }
      };

      // Only load on client side
      if (typeof window !== 'undefined') {
        loadComponent();
      }
    }, []);

    useImperativeHandle(ref, () => ({
      // Expose any methods needed by parent components
      refresh: () => {
        // Force re-render if needed
        setIsLoaded(false);
        setTimeout(() => setIsLoaded(true), 0);
      }
    }));

    if (error) {
      return (
        <div 
          className="flex items-center justify-center bg-destructive/10 rounded-md border border-destructive/20"
          style={{ height }}
        >
          <div className="text-center">
            <p className="text-sm text-destructive">Failed to load data grid</p>
            <button 
              onClick={() => window.location.reload()}
              className="mt-2 px-3 py-1 text-xs bg-destructive text-destructive-foreground rounded"
            >
              Retry
            </button>
          </div>
        </div>
      );
    }

    if (!isLoaded) {
      return <AgGridLoadingFallback height={height} />;
    }

    return (
      <div className={className} style={{ height }}>
        {children}
      </div>
    );
  }
);

DynamicAgGrid.displayName = 'DynamicAgGrid';

export default DynamicAgGrid;