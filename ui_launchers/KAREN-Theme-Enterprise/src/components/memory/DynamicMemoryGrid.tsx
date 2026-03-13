/**
 * Dynamic Memory Grid Component
 * 
 * This component dynamically loads the MemoryGrid and ag-grid dependencies
 * to reduce initial bundle size for the memory page.
 */

'use client';

import React, { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { Skeleton } from '@/components/ui/skeleton';

// Types
export type MemoryType = "fact" | "preference" | "context";

export interface MemoryGridRow {
  id: string;
  content: string;
  type: MemoryType;
  confidence: number;
  last_accessed: string; // ISO
  relevance_score: number;
  semantic_cluster: string;
  relationships: string[];
  timestamp: number; // epoch ms
  user_id: string;
  session_id?: string;
  tenant_id?: string;
}

export interface DynamicMemoryGridProps {
  userId: string;
  tenantId?: string;
  onMemorySelect?: (memory: MemoryGridRow) => void;
  onMemoryEdit?: (memory: MemoryGridRow) => void;
  filters?: Record<string, unknown>;
  height?: number;
  className?: string;
}

// Loading skeleton component
const MemoryGridSkeleton = ({ height = 480 }: { height?: number }) => (
  <div className="space-y-4" style={{ height }}>
    <div className="flex items-center justify-between">
      <Skeleton className="h-9 w-[220px]" />
      <div className="flex gap-2">
        <Skeleton className="h-9 w-20" />
        <Skeleton className="h-9 w-24" />
      </div>
    </div>
    <div className="space-y-2">
      {Array.from({ length: 10 }).map((_, i) => (
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

// Dynamic import of MemoryGrid
const MemoryGrid = dynamic(
  () => import('./MemoryGrid').then(mod => ({ default: mod.default })),
  {
    loading: () => <MemoryGridSkeleton />,
    ssr: false
  }
);

// Main component
export const DynamicMemoryGrid: React.FC<DynamicMemoryGridProps> = ({
  userId,
  tenantId,
  onMemorySelect,
  onMemoryEdit,
  filters,
  height = 480,
  className,
}) => {
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  // Don't render on server side to avoid hydration issues
  if (!isClient) {
    return <MemoryGridSkeleton height={height} />;
  }

  return (
    <div className={className}>
      <MemoryGrid
        userId={userId}
        tenantId={tenantId}
        onMemorySelect={onMemorySelect}
        onMemoryEdit={onMemoryEdit}
        filters={filters}
        height={height}
      />
    </div>
  );
};

export default DynamicMemoryGrid;