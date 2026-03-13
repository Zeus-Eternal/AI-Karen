import type React from 'react';

type SimpleComponent = React.ComponentType<Record<string, unknown>>;

export interface LazyComponentProps {
  fallback?: SimpleComponent;
  errorFallback?: React.ComponentType<{ error: Error; retry: () => void }>;
  children: React.ReactNode;
}

export interface LazyLoadOptions {
  fallback?: SimpleComponent;
  errorFallback?: React.ComponentType<{ error: Error; retry: () => void }>;
  delay?: number;
}

export type { SimpleComponent };
