/**
 * Table Component - Simple table component
 */
import React from 'react';
import { cn } from '@/lib/utils';

export interface TableProps {
  className?: string;
  children?: React.ReactNode;
}

export const Table: React.FC<TableProps> = ({ className, children }) => {
  return (
    <div className={cn('w-full', className)}>
      {children}
    </div>
  );
};

export default Table;
