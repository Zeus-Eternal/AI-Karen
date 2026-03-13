"use client";

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { MemoryCleanupProps, MemoryCleanupResult } from '../types';

// Icon components
const Trash2 = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
  </svg>
);

const Clock = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const AlertTriangle = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 15.5c-.77.833.192 2.5 1.732 2.5z" />
  </svg>
);

const Copy = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2H6a2 2 0 00-2 2v8a2 2 0 002 2z" />
  </svg>
);

const TrendingDown = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
  </svg>
);

const Check = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
  </svg>
);

const AlertCircle = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

export function MemoryCleanup({ onCleanup, className }: MemoryCleanupProps) {
  const [isProcessing, setIsProcessing] = useState(false);
  const [cleanupResult, setCleanupResult] = useState<MemoryCleanupResult | null>(null);
  const [isDryRun, setIsDryRun] = useState(true);
  
  // Cleanup options
  const [expired, setExpired] = useState(true);
  const [duplicates, setDuplicates] = useState(false);
  const [lowConfidence, setLowConfidence] = useState(false);
  const [lowImportance, setLowImportance] = useState(false);
  const [minConfidence, setMinConfidence] = useState(0.3);
  const [minImportance, setMinImportance] = useState(0.3);
  const [olderThan, setOlderThan] = useState(() => {
    const date = new Date();
    date.setFullYear(date.getFullYear() - 1);
    return date.toISOString().split('T')[0];
  });

  const handleCleanup = async () => {
    setIsProcessing(true);
    setCleanupResult(null);
    
    try {
      const options = {
        expired,
        duplicates,
        lowConfidence,
        lowImportance,
        minConfidence,
        minImportance,
        olderThan: new Date(olderThan || ''),
        dryRun: isDryRun,
        batchSize: 100
      };
      
      const result = await onCleanup(options);
      setCleanupResult(result);
    } catch (error) {
      setCleanupResult({
        deletedCount: 0,
        archivedCount: 0,
        errors: [error instanceof Error ? error.message : 'Unknown error occurred'],
        duplicatesFound: 0,
        spaceFreed: 0,
        duration: 0
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const clearResult = () => {
    setCleanupResult(null);
  };

  const formatDateForDisplay = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      timeZone: 'UTC'
    });
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDuration = (milliseconds: number) => {
    const seconds = Math.floor(milliseconds / 1000);
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ${seconds % 60}s`;
    const hours = Math.floor(minutes / 60);
    return `${hours}h ${minutes % 60}m`;
  };

  return (
    <div className={cn("bg-card rounded-lg border", className)}>
      {/* Header */}
      <div className="border-b p-4">
        <div className="flex items-center gap-3">
          <Trash2 className="h-5 w-5 text-muted-foreground" />
          <h2 className="text-lg font-semibold">Memory Cleanup</h2>
        </div>
        <p className="text-sm text-muted-foreground mt-1">
          Remove old, duplicate, or low-quality memories to optimize storage and performance
        </p>
      </div>

      {/* Content */}
      <div className="p-6 space-y-6">
        {/* Cleanup options */}
        <div className="space-y-4">
          <h3 className="font-medium">Cleanup Criteria</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="expired"
                  checked={expired}
                  onChange={(e) => setExpired(e.target.checked)}
                  className="rounded"
                />
                <label htmlFor="expired" className="text-sm font-medium flex items-center gap-2">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  Expired memories
                </label>
              </div>
              
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="duplicates"
                  checked={duplicates}
                  onChange={(e) => setDuplicates(e.target.checked)}
                  className="rounded"
                />
                <label htmlFor="duplicates" className="text-sm font-medium flex items-center gap-2">
                  <Copy className="h-4 w-4 text-muted-foreground" />
                  Duplicate memories
                </label>
              </div>
              
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="lowConfidence"
                  checked={lowConfidence}
                  onChange={(e) => setLowConfidence(e.target.checked)}
                  className="rounded"
                />
                <label htmlFor="lowConfidence" className="text-sm font-medium flex items-center gap-2">
                  <TrendingDown className="h-4 w-4 text-muted-foreground" />
                  Low confidence memories
                </label>
              </div>
              
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="lowImportance"
                  checked={lowImportance}
                  onChange={(e) => setLowImportance(e.target.checked)}
                  className="rounded"
                />
                <label htmlFor="lowImportance" className="text-sm font-medium flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-muted-foreground" />
                  Low importance memories
                </label>
              </div>
            </div>
            
            <div className="space-y-3">
              {lowConfidence && (
                <div>
                  <label className="text-sm font-medium">Minimum confidence</label>
                  <div className="flex items-center gap-2 mt-1">
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={minConfidence}
                      onChange={(e) => setMinConfidence(parseFloat(e.target.value))}
                      className="flex-1"
                    />
                    <span className="text-sm text-muted-foreground w-12 text-right">
                      {(minConfidence * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              )}
              
              {lowImportance && (
                <div>
                  <label className="text-sm font-medium">Minimum importance</label>
                  <div className="flex items-center gap-2 mt-1">
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={minImportance}
                      onChange={(e) => setMinImportance(parseFloat(e.target.value))}
                      className="flex-1"
                    />
                    <span className="text-sm text-muted-foreground w-12 text-right">
                      {(minImportance * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              )}
              
              <div>
                <label className="text-sm font-medium">Older than</label>
                <input
                  type="date"
                  value={olderThan}
                  onChange={(e) => setOlderThan(e.target.value)}
                  className="w-full mt-1 px-3 py-2 text-sm bg-background border rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  {olderThan && formatDateForDisplay(olderThan)}
                </p>
              </div>
              
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="dryRun"
                  checked={isDryRun}
                  onChange={(e) => setIsDryRun(e.target.checked)}
                  className="rounded"
                />
                <label htmlFor="dryRun" className="text-sm font-medium">
                  Dry run (preview only)
                </label>
              </div>
            </div>
          </div>
        </div>

        {/* Result notification */}
        {cleanupResult && (
          <div className={cn(
            "p-4 rounded-md",
            cleanupResult.errors.length === 0
              ? "bg-green-50 text-green-800 border border-green-200"
              : "bg-red-50 text-red-800 border border-red-200"
          )}>
            <div className="flex items-start gap-3">
              {cleanupResult.errors.length === 0 ? (
                <Check className="h-5 w-5 mt-0.5 flex-shrink-0" />
              ) : (
                <AlertCircle className="h-5 w-5 mt-0.5 flex-shrink-0" />
              )}
              <div className="flex-1">
                <p className="font-medium">
                  {isDryRun ? 'Cleanup Preview' : 'Cleanup Completed'}
                </p>
                <div className="mt-2 space-y-1 text-sm">
                  {cleanupResult.deletedCount > 0 && (
                    <p>Memories to delete: {cleanupResult.deletedCount}</p>
                  )}
                  {cleanupResult.archivedCount > 0 && (
                    <p>Memories to archive: {cleanupResult.archivedCount}</p>
                  )}
                  {cleanupResult.duplicatesFound > 0 && (
                    <p>Duplicates found: {cleanupResult.duplicatesFound}</p>
                  )}
                  {cleanupResult.spaceFreed > 0 && (
                    <p>Space to be freed: {formatBytes(cleanupResult.spaceFreed)}</p>
                  )}
                  <p>Processing time: {formatDuration(cleanupResult.duration)}</p>
                  {cleanupResult.errors.length > 0 && (
                    <div className="mt-2">
                      <p className="font-medium">Errors:</p>
                      <ul className="list-disc list-inside">
                        {cleanupResult.errors.map((error, index) => (
                          <li key={index} className="text-sm">{error}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
              <button
                className="ml-2 opacity-70 hover:opacity-100"
                onClick={clearResult}
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        )}

        {/* Action buttons */}
        <div className="flex justify-center gap-3">
          {isDryRun && cleanupResult && cleanupResult.errors.length === 0 && (
            <button
              className={cn(
                "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-destructive text-destructive-foreground hover:bg-destructive/90 px-6 py-2 gap-2",
                isProcessing && "opacity-50 cursor-not-allowed"
              )}
              onClick={() => {
                setIsDryRun(false);
                setCleanupResult(null);
              }}
              disabled={isProcessing}
            >
              <Trash2 className="h-4 w-4" />
              Execute Cleanup
            </button>
          )}
          
          <button
            className={cn(
              "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 px-6 py-2 gap-2",
              isProcessing && "opacity-50 cursor-not-allowed"
            )}
            onClick={handleCleanup}
            disabled={isProcessing || (!expired && !duplicates && !lowConfidence && !lowImportance)}
          >
            {isProcessing ? 'Processing...' : (
              <>
                {isDryRun ? (
                  <>
                    <AlertCircle className="h-4 w-4" />
                    Preview Cleanup
                  </>
                ) : (
                  <>
                    <Trash2 className="h-4 w-4" />
                    Start Cleanup
                  </>
                )}
              </>
            )}
          </button>
        </div>

        {/* Warning */}
        {!isDryRun && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
              <div>
                <p className="font-medium text-yellow-800">Warning</p>
                <p className="text-sm text-yellow-700 mt-1">
                  This action will permanently delete the selected memories. This cannot be undone. 
                  Consider running a dry run first to preview what will be affected.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default MemoryCleanup;