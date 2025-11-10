/**
 * Progress Indicator Components
 * 
 * Progress indicators for bulk operations with cancellation support
 * and detailed progress information.
 * 
 * Requirements: 7.2, 7.5
 */

"use client";

import React from 'react';
import { X, CheckCircle, XCircle, AlertCircle, Loader2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export interface ProgressStep {
  id: string;
  label: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress?: number;
  error?: string;
  details?: string;
}

export interface BulkOperationProgress {
  operationId: string;
  operation: string;
  totalItems: number;
  processedItems: number;
  successfulItems: number;
  failedItems: number;
  status: 'running' | 'completed' | 'failed' | 'cancelled';
  startTime: Date;
  endTime?: Date;
  steps: ProgressStep[];
  errors: Array<{
    itemId: string;
    error: string;
    details?: string;
  }>;
  canCancel: boolean;
}

export interface ProgressIndicatorProps {
  progress: BulkOperationProgress;
  onCancel?: () => void;
  onClose?: () => void;
  className?: string;
  showDetails?: boolean;
}

export function ProgressIndicator({
  progress,
  onCancel,
  onClose,
  className = '',
  showDetails = true
}: ProgressIndicatorProps) {
  const [showErrorDetails, setShowErrorDetails] = React.useState(false);

  const overallProgress = progress.totalItems > 0
    ? Math.round((progress.processedItems / progress.totalItems) * 100)
    : 0;

  const isCompleted = progress.status === 'completed' || progress.status === 'failed' || progress.status === 'cancelled';
  const duration = progress.endTime
    ? Math.round((progress.endTime.getTime() - progress.startTime.getTime()) / 1000)
    : Math.round((Date.now() - progress.startTime.getTime()) / 1000);

  const getStatusIcon = (
    status: ProgressStep['status'] | BulkOperationProgress['status']
  ) => {
    switch (status) {
      case 'running':
        return <Loader2 className="h-5 w-5 animate-spin text-blue-600" />;
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-600" />;
      case 'cancelled':
        return <AlertCircle className="h-5 w-5 text-yellow-600" />;
      default:
        return <div className="h-5 w-5 rounded-full bg-gray-300" />;
    }
  };

  const getStatusColor = (
    status: ProgressStep['status'] | BulkOperationProgress['status']
  ) => {
    switch (status) {
      case 'running':
        return 'text-blue-600';
      case 'completed':
        return 'text-green-600';
      case 'failed':
        return 'text-red-600';
      case 'cancelled':
        return 'text-yellow-600';
      default:
        return 'text-gray-600';
    }
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  return (
    <div
      className={cn(
        'bg-white border border-gray-200 rounded-lg shadow-lg',
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 sm:p-4 md:p-6">
        <div className="flex items-center space-x-3">
          {getStatusIcon(progress.status)}
          <div>
            <h3 className="text-lg font-medium text-gray-900">
              {progress.operation}
            </h3>
            <p className="text-sm text-gray-600 md:text-base lg:text-lg">
              {progress.processedItems} of {progress.totalItems} items processed
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          {progress.canCancel && progress.status === 'running' && onCancel && (
            <Button
              type="button"
              onClick={onCancel}
              className="px-3 py-1 text-sm font-medium text-red-600 border border-red-300 rounded-md hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 md:text-base lg:text-lg"
              aria-label="Cancel operation"
            >
              Cancel
            </Button>
          )}

          {isCompleted && onClose && (
            <Button
              type="button"
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded"
              aria-label="Close progress indicator"
            >
              <X className="h-5 w-5" aria-hidden="true" />
              <span className="sr-only">Close</span>
            </Button>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="p-4 sm:p-4 md:p-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700 md:text-base lg:text-lg">
            Overall progress
          </span>
          <span className="text-sm text-gray-600 md:text-base lg:text-lg">
            {overallProgress}%
          </span>
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={cn(
              'h-2 rounded-full transition-all duration-300',
              progress.status === 'completed'
                ? 'bg-green-600'
                : progress.status === 'failed' || progress.status === 'cancelled'
                  ? 'bg-red-600'
                  : 'bg-blue-600'
            )}
            style={{ width: `${overallProgress}%` }}
            role="progressbar"
            aria-valuenow={overallProgress}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`Operation progress: ${overallProgress}%`}
          />
        </div>
      </div>

      {/* Statistics */}
      <div className="px-4 pb-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-green-600">
              {progress.successfulItems}
            </div>
            <div className="text-xs text-gray-600 sm:text-sm md:text-base">Successful</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-red-600">
              {progress.failedItems}
            </div>
            <div className="text-xs text-gray-600 sm:text-sm md:text-base">Failed</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-gray-600">
              {progress.totalItems - progress.processedItems}
            </div>
            <div className="text-xs text-gray-600 sm:text-sm md:text-base">Remaining</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-blue-600">
              {formatDuration(duration)}
            </div>
            <div className="text-xs text-gray-600 sm:text-sm md:text-base">Duration</div>
          </div>
        </div>
      </div>

      {/* Detailed Steps */}
      {showDetails && progress.steps.length > 0 && (
        <div className="border-t border-gray-200">
          <div className="p-4 sm:p-4 md:p-6">
            <h4 className="text-sm font-medium text-gray-900 mb-3 md:text-base lg:text-lg">
              Steps
            </h4>
            <div className="space-y-2">
              {progress.steps.map((step) => (
                <div key={step.id} className="flex items-center space-x-3">
                  {getStatusIcon(step.status)}
                  <div className="flex-1 min-w-0 ">
                    <div className="flex items-center justify-between">
                      <span className={`text-sm font-medium ${getStatusColor(step.status)}`}>
                        {step.label}
                      </span>
                      {step.progress !== undefined && (
                        <span className="text-xs text-gray-500 sm:text-sm md:text-base">
                          {step.progress}%
                        </span>
                      )}
                    </div>
                    {step.details && (
                      <p className="text-xs text-gray-600 mt-1 sm:text-sm md:text-base">
                        {step.details}
                      </p>
                    )}
                    {step.error && (
                      <p className="text-xs text-red-600 mt-1 sm:text-sm md:text-base">
                        {step.error}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Error Details */}
      {progress.errors.length > 0 && (
        <div className="border-t border-gray-200">
          <div className="p-4 sm:p-4 md:p-6">
            <Button
              type="button"
              onClick={() => setShowErrorDetails(!showErrorDetails)}
              className="flex items-center justify-between w-full text-left focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded"
            >
              <h4 className="text-sm font-medium text-red-600 md:text-base lg:text-lg">
                Errors ({progress.errors.length})
              </h4>
              <span className="text-red-600">
                {showErrorDetails ? '−' : '+'}
              </span>
            </Button>
            
            {showErrorDetails && (
              <div className="mt-3 space-y-2 max-h-40 overflow-y-auto">
                {progress.errors.map((error, index) => (
                  <div key={index} className="bg-red-50 border border-red-200 rounded-md p-3 sm:p-4 md:p-6">
                    <div className="text-sm font-medium text-red-800 md:text-base lg:text-lg">
                      Item: {error.itemId}
                    </div>
                    <div className="text-sm text-red-700 mt-1 md:text-base lg:text-lg">
                      {error.error}
                    </div>
                    {error.details && (
                      <div className="text-xs text-red-600 mt-1 sm:text-sm md:text-base">
                        {error.details}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Status Message */}
      {isCompleted && (
        <div className="border-t border-gray-200 p-4 sm:p-4 md:p-6">
          <div className={`text-sm font-medium ${getStatusColor(progress.status)}`}>
            {progress.status === 'completed' && 'Operation completed successfully'}
            {progress.status === 'failed' && 'Operation failed'}
            {progress.status === 'cancelled' && 'Operation was cancelled'}
          </div>
          {progress.status === 'completed' && progress.failedItems > 0 && (
            <div className="text-sm text-yellow-600 mt-1 md:text-base lg:text-lg">
              {progress.failedItems} item{progress.failedItems === 1 ? '' : 's'} failed to process
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export interface SimpleProgressBarProps {
  progress: number;
  label?: string;
  size?: 'sm' | 'md' | 'lg';
  color?: 'blue' | 'green' | 'red' | 'yellow';
  showPercentage?: boolean;
  className?: string;
}

export function SimpleProgressBar({
  progress,
  label,
  size = 'md',
  color = 'blue',
  showPercentage = true,
  className = ''
}: SimpleProgressBarProps) {
  const sizeClasses: Record<'sm' | 'md' | 'lg', string> = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3'
  };

  const colorClasses: Record<'blue' | 'green' | 'red' | 'yellow', string> = {
    blue: 'bg-blue-600',
    green: 'bg-green-600',
    red: 'bg-red-600',
    yellow: 'bg-yellow-600'
  };

  return (
    <div className={className}>
      {(label || showPercentage) && (
        <div className="flex items-center justify-between mb-2">
          {label && (
            <span className="text-sm font-medium text-gray-700 md:text-base lg:text-lg">
              {label}
            </span>
          )}
          {showPercentage && (
            <span className="text-sm text-gray-600 md:text-base lg:text-lg">
              {Math.round(progress)}%
            </span>
          )}
        </div>
      )}
      
      <div className={cn('w-full bg-gray-200 rounded-full', sizeClasses[size])}>
        <div
          className={cn(
            sizeClasses[size],
            'rounded-full transition-all duration-300',
            colorClasses[color]
          )}
          style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
          role="progressbar"
          aria-valuenow={progress}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={label ? `${label}: ${Math.round(progress)}%` : `Progress: ${Math.round(progress)}%`}
        />
      </div>
    </div>
  );
}

export default ProgressIndicator;