/**
 * Dynamic File Grid Components
 * 
 * These components dynamically load ag-grid dependencies to reduce initial bundle size.
 */

'use client';

import React, { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { Skeleton } from '@/components/ui/skeleton';

// Loading skeleton component
const FileGridSkeleton = ({ height = 400 }: { height?: number }) => (
  <div className="space-y-4" style={{ height }}>
    <div className="flex items-center justify-between">
      <Skeleton className="h-9 w-[220px]" />
      <div className="flex gap-2">
        <Skeleton className="h-9 w-20" />
        <Skeleton className="h-9 w-24" />
      </div>
    </div>
    <div className="space-y-2">
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className="flex items-center space-x-4 p-2 border rounded">
          <Skeleton className="h-4 w-4" />
          <Skeleton className="h-4 flex-1" />
          <Skeleton className="h-4 w-16" />
          <Skeleton className="h-4 w-20" />
        </div>
      ))}
    </div>
  </div>
);

// Dynamic imports for file grid components
export const DynamicFilePermissionManager = dynamic(
  () => import('./FilePermissionManager').then(mod => ({ default: mod.default })),
  {
    loading: () => <FileGridSkeleton />,
    ssr: false
  }
);

export const DynamicFileMetadataGrid = dynamic(
  () => import('./FileMetadataGrid').then(mod => ({ default: mod.default })),
  {
    loading: () => <FileGridSkeleton />,
    ssr: false
  }
);

// Wrapper component for dynamic file grids
interface DynamicFileGridProps {
  children: React.ReactNode;
  height?: number;
}

export const DynamicFileGrid: React.FC<DynamicFileGridProps> = ({
  children,
  height = 400
}) => {
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  // Don't render on server side to avoid hydration issues
  if (!isClient) {
    return <FileGridSkeleton height={height} />;
  }

  return <>{children}</>;
};

export default DynamicFileGrid;