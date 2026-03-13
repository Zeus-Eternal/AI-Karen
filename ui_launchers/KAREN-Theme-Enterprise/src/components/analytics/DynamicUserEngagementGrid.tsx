/**
 * Dynamic User Engagement Grid Component
 * 
 * This component dynamically loads the UserEngagementGrid and ag-grid dependencies
 * to reduce initial bundle size.
 */

'use client';

import React, { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { Skeleton } from '@/components/ui/skeleton';

// Loading skeleton component
const UserEngagementGridSkeleton = ({ height = 400 }: { height?: number }) => (
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
          <Skeleton className="h-4 w-24" />
        </div>
      ))}
    </div>
  </div>
);

// Dynamic import of UserEngagementGrid
const UserEngagementGrid = dynamic(
  () => import('./UserEngagementGrid').then(mod => ({ default: mod.UserEngagementGrid })),
  {
    loading: () => <UserEngagementGridSkeleton />,
    ssr: false
  }
);

// Props interface (re-export from original component)
export interface DynamicUserEngagementGridProps {
  data?: any[];
  onRowSelect?: (row: any) => void;
  onExport?: (data: any[]) => Promise<void>;
  onRefresh?: () => Promise<void>;
  height?: number;
  className?: string;
}

// Main component
export const DynamicUserEngagementGrid: React.FC<DynamicUserEngagementGridProps> = ({
  data,
  onRowSelect,
  onExport,
  onRefresh,
  height = 400,
  className,
}) => {
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  // Don't render on server side to avoid hydration issues
  if (!isClient) {
    return <UserEngagementGridSkeleton height={height} />;
  }

  return (
    <div className={className}>
      <UserEngagementGrid
        data={data}
        onRowSelect={onRowSelect}
        onExport={onExport}
        onRefresh={onRefresh}
        className=""
      />
    </div>
  );
};

export default DynamicUserEngagementGrid;