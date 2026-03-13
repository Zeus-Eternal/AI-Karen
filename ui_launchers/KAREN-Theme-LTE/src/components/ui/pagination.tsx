/**
 * Pagination Component - Reusable pagination component
 */

import React from 'react';
import { cn } from '../../lib/utils';
import { Button } from './button';

export interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  hasNext?: boolean;
  hasPrev?: boolean;
  onNext?: () => void;
  onPrev?: () => void;
  className?: string;
}

export const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  onPageChange,
  hasNext = false,
  hasPrev = false,
  onNext,
  onPrev,
  className = '',
}) => {
  const handlePageChange = (page: number) => {
    onPageChange(page);
  };

  const renderPageNumbers = () => {
    const pages = [];
    const maxVisible = 5;
    
    let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let endPage = Math.min(totalPages, startPage + maxVisible - 1);
    
    if (endPage - startPage < maxVisible) {
      const additionalPages = Math.max(0, maxVisible - (endPage - startPage + 1));
      startPage = Math.max(1, startPage - additionalPages / 2);
      endPage = Math.min(totalPages, endPage + additionalPages / 2);
    }
    
    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }
    
    return pages;
  };

  return (
    <div className={cn('flex items-center justify-center space-x-2', className)}>
      {/* Previous button */}
      <Button
        onClick={onPrev}
        disabled={!hasPrev}
        variant="outline"
        size="sm"
      >
        Previous
      </Button>
      
      {/* Page numbers */}
      <div className="flex space-x-1">
        {renderPageNumbers().map(page => (
          <button
            key={page}
            onClick={() => handlePageChange(page)}
            className={cn(
              'px-3 py-1 text-sm font-medium rounded-md transition-colors',
              page === currentPage
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'text-gray-700 bg-white hover:bg-gray-50 border border-gray-300'
            )}
          >
            {page}
          </button>
        ))}
      </div>
      
      {/* Next button */}
      <Button
        onClick={onNext}
        disabled={!hasNext}
        variant="outline"
        size="sm"
      >
        Next
      </Button>
      
      {/* Page info */}
      <div className="text-sm text-gray-600 dark:text-gray-400">
        Page {currentPage} of {totalPages}
      </div>
    </div>
  );
};