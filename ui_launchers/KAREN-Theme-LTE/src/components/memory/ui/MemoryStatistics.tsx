"use client";

import React from 'react';
import { cn } from '@/lib/utils';
import { MemoryStatisticsProps, MemoryStatistics as MemoryStatisticsType } from '../types';

// Icon components
const Database = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
  </svg>
);

const HardDrive = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" />
  </svg>
);

const Activity = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
  </svg>
);

const Clock = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const TrendingUp = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
  </svg>
);

const Tag = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
  </svg>
);

const Folder = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
  </svg>
);

export function MemoryStatistics({
  statistics,
  className,
  showCharts = false,
  showDetails = false
}: MemoryStatisticsProps) {
  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat().format(num);
  };

  const getTrendIcon = (trend?: 'up' | 'down' | 'stable') => {
    if (!trend) return null;
    switch (trend) {
      case 'up':
        return <TrendingUp className="h-3 w-3 text-green-500" />;
      case 'down':
        return <TrendingUp className="h-3 w-3 text-red-500 rotate-180" />;
      case 'stable':
        return <div className="h-3 w-3 bg-gray-400 rounded-full" />;
      default:
        return null;
    }
  };

  if (showDetails) {
    return (
      <div className={cn("grid grid-cols-2 md:grid-cols-4 gap-4", className)}>
        <div className="flex items-center space-x-2">
          <Database className="h-4 w-4 text-muted-foreground" />
          <div>
            <p className="text-xs text-muted-foreground">Total Memories</p>
            <p className="text-sm font-medium">{formatNumber(statistics.total)}</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <HardDrive className="h-4 w-4 text-muted-foreground" />
          <div>
            <p className="text-xs text-muted-foreground">Storage Used</p>
            <p className="text-sm font-medium">{formatBytes(statistics.totalSize)}</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <Activity className="h-4 w-4 text-muted-foreground" />
          <div>
            <p className="text-xs text-muted-foreground">Active Memories</p>
            <p className="text-sm font-medium">{formatNumber(statistics.byStatus.active || 0)}</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <Clock className="h-4 w-4 text-muted-foreground" />
          <div>
            <p className="text-xs text-muted-foreground">Avg. Age</p>
            <p className="text-sm font-medium">{statistics.oldestMemory && statistics.newestMemory
              ? Math.round((statistics.newestMemory.getTime() - statistics.oldestMemory.getTime()) / (1000 * 60 * 60 * 24))
              : 0} days</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("space-y-6", className)}>
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-card rounded-lg border p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Database className="h-5 w-5 text-muted-foreground" />
              <h3 className="text-sm font-medium text-muted-foreground">Total Memories</h3>
            </div>
            {showCharts && <div className="h-3 w-3 bg-primary rounded-full animate-pulse" />}
          </div>
          <p className="text-2xl font-bold mt-2">{formatNumber(statistics.total)}</p>
          <p className="text-xs text-muted-foreground mt-1">
            {formatNumber(statistics.byStatus.active || 0)} active, {formatNumber(statistics.byStatus.archived || 0)} archived
          </p>
        </div>

        <div className="bg-card rounded-lg border p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <HardDrive className="h-5 w-5 text-muted-foreground" />
              <h3 className="text-sm font-medium text-muted-foreground">Storage Used</h3>
            </div>
            {showCharts && <div className="h-3 w-3 bg-primary rounded-full animate-pulse" />}
          </div>
          <p className="text-2xl font-bold mt-2">{formatBytes(statistics.totalSize)}</p>
          <p className="text-xs text-muted-foreground mt-1">
            Average: {formatBytes(statistics.averageSize)} per memory
          </p>
        </div>

        <div className="bg-card rounded-lg border p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Activity className="h-5 w-5 text-muted-foreground" />
              <h3 className="text-sm font-medium text-muted-foreground">Access Activity</h3>
            </div>
            {showCharts && <div className="h-3 w-3 bg-primary rounded-full animate-pulse" />}
          </div>
          <p className="text-2xl font-bold mt-2">{formatNumber(statistics.totalAccessCount)}</p>
          <p className="text-xs text-muted-foreground mt-1">
            {formatNumber(statistics.usageStats.memoriesAccessedThisWeek)} this week
          </p>
        </div>

        <div className="bg-card rounded-lg border p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Clock className="h-5 w-5 text-muted-foreground" />
              <h3 className="text-sm font-medium text-muted-foreground">Average Age</h3>
            </div>
            {showCharts && <div className="h-3 w-3 bg-primary rounded-full animate-pulse" />}
          </div>
          <p className="text-2xl font-bold mt-2">
            {statistics.oldestMemory && statistics.newestMemory
              ? Math.round((statistics.newestMemory.getTime() - statistics.oldestMemory.getTime()) / (1000 * 60 * 60 * 24))
              : 0} days
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            Average retention: {statistics.retentionStats.averageRetentionDays} days
          </p>
        </div>
      </div>

      {/* Memory Type Distribution */}
      <div className="bg-card rounded-lg border p-4">
        <h3 className="text-lg font-medium mb-4">Memory Type Distribution</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(statistics.byType).map(([type, count]) => (
            <div key={type} className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full bg-primary" />
                <span className="text-sm font-medium capitalize">{type}</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-sm text-muted-foreground">{formatNumber(count)}</span>
                <span className="text-xs text-muted-foreground">
                  ({Math.round((count / statistics.total) * 100)}%)
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Organization Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-card rounded-lg border p-4">
          <div className="flex items-center space-x-2 mb-4">
            <Tag className="h-5 w-5 text-muted-foreground" />
            <h3 className="text-lg font-medium">Tags</h3>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Total Tags</span>
              <span className="text-sm font-medium">-</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Most Used</span>
              <span className="text-sm font-medium">-</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Average per Memory</span>
              <span className="text-sm font-medium">-</span>
            </div>
          </div>
        </div>

        <div className="bg-card rounded-lg border p-4">
          <div className="flex items-center space-x-2 mb-4">
            <Folder className="h-5 w-5 text-muted-foreground" />
            <h3 className="text-lg font-medium">Folders</h3>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Total Folders</span>
              <span className="text-sm font-medium">-</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Most Populated</span>
              <span className="text-sm font-medium">-</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Average Depth</span>
              <span className="text-sm font-medium">-</span>
            </div>
          </div>
        </div>
      </div>

      {/* Storage Breakdown */}
      <div className="bg-card rounded-lg border p-4">
        <h3 className="text-lg font-medium mb-4">Storage Breakdown</h3>
        <div className="space-y-3">
          {Object.entries(statistics.storageStats.storageByType).map(([type, size]) => (
            <div key={type} className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full bg-primary" />
                <span className="text-sm font-medium capitalize">{type}</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-sm text-muted-foreground">{formatBytes(size)}</span>
                <span className="text-xs text-muted-foreground">
                  ({Math.round((size / statistics.totalSize) * 100)}%)
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default MemoryStatistics;