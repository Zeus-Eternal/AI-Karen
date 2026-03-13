"use client";

import React from 'react';
import { AgentPerformanceMetrics } from '../types';
import { cn } from '@/lib/utils';

interface AgentPerformanceMetricsProps {
  metrics: AgentPerformanceMetrics;
  compact?: boolean;
  showDetails?: boolean;
  className?: string;
}

function AgentPerformanceMetricsComponent({
  metrics,
  compact = false,
  showDetails = false,
  className,
}: AgentPerformanceMetricsProps) {
  const {
    averageResponseTime,
    successRate,
    totalTasks,
    completedTasks,
    failedTasks,
    averageTaskDuration,
    uptime,
    lastUpdated,
    resourceUsage,
  } = metrics;

  const formatResponseTime = (ms: number) => {
    if (ms < 1000) {
      return `${ms}ms`;
    } else if (ms < 60000) {
      return `${(ms / 1000).toFixed(1)}s`;
    } else {
      return `${(ms / 60000).toFixed(1)}m`;
    }
  };

  const formatDuration = (ms: number) => {
    if (ms < 1000) {
      return `${ms}ms`;
    } else if (ms < 60000) {
      return `${(ms / 1000).toFixed(1)}s`;
    } else {
      return `${(ms / 60000).toFixed(1)}m`;
    }
  };

  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  const getStatusColor = (value: number, isHigherBetter = true) => {
    if (isHigherBetter) {
      if (value >= 95) return 'text-green-600';
      if (value >= 90) return 'text-green-500';
      if (value >= 80) return 'text-yellow-600';
      if (value >= 70) return 'text-orange-600';
      return 'text-red-600';
    } else {
      if (value <= 5) return 'text-green-600';
      if (value <= 10) return 'text-green-500';
      if (value <= 30) return 'text-yellow-600';
      if (value <= 100) return 'text-orange-600';
      return 'text-red-600';
    }
  };

  const getProgressBarColor = (value: number) => {
    if (value >= 95) return 'bg-green-500';
    if (value >= 90) return 'bg-green-400';
    if (value >= 80) return 'bg-yellow-500';
    if (value >= 70) return 'bg-orange-500';
    return 'bg-red-500';
  };

  if (compact) {
    return (
      <div className={cn("flex items-center gap-2 text-xs", className)}>
        <div className="flex items-center gap-1">
          <svg className="w-3 h-3 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          <span className={getStatusColor(averageResponseTime, false)}>
            {formatResponseTime(averageResponseTime)}
          </span>
        </div>
        
        <div className="flex items-center gap-1">
          <svg className="w-3 h-3 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a2 2 0 11-3 0 1.5 1.5 0 013 0z" />
          </svg>
          <span className={getStatusColor(successRate, true)}>
            {formatPercentage(successRate)}
          </span>
        </div>
        
        <div className="flex items-center gap-1">
          <svg className="w-3 h-3 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="text-muted-foreground">
            {uptime.toFixed(1)}%
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("space-y-3", className)}>
      {/* Response Time */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <svg className="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          <span className="text-sm font-medium">Avg Response Time</span>
        </div>
        <div className="text-right">
          <div className={cn("text-lg font-semibold", getStatusColor(averageResponseTime, false))}>
            {formatResponseTime(averageResponseTime)}
          </div>
          <div className="text-xs text-muted-foreground">
            Lower is better
          </div>
        </div>
      </div>

      {/* Success Rate */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <svg className="w-4 h-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a2 2 0 11-3 0 1.5 1.5 0 013 0z" />
          </svg>
          <span className="text-sm font-medium">Success Rate</span>
        </div>
        <div className="text-right">
          <div className={cn("text-lg font-semibold", getStatusColor(successRate, true))}>
            {formatPercentage(successRate)}
          </div>
          <div className="text-xs text-muted-foreground">
            Higher is better
          </div>
        </div>
      </div>

      {/* Progress Bar for Success Rate */}
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div 
          className={cn("h-2 rounded-full transition-all duration-300", getProgressBarColor(successRate))}
          style={{ width: `${successRate}%` }}
        />
      </div>

      {/* Task Statistics */}
      <div className="grid grid-cols-3 gap-4">
        <div className="text-center">
          <div className="text-2xl font-bold text-primary">
            {totalTasks.toLocaleString()}
          </div>
          <div className="text-sm text-muted-foreground">Total Tasks</div>
        </div>
        
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">
            {completedTasks.toLocaleString()}
          </div>
          <div className="text-sm text-muted-foreground">Completed</div>
        </div>
        
        <div className="text-center">
          <div className="text-2xl font-bold text-red-600">
            {failedTasks.toLocaleString()}
          </div>
          <div className="text-sm text-muted-foreground">Failed</div>
        </div>
      </div>

      {/* Average Task Duration */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <svg className="w-4 h-4 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="text-sm font-medium">Avg Task Duration</span>
        </div>
        <div className="text-right">
          <div className="text-lg font-semibold text-muted-foreground">
            {formatDuration(averageTaskDuration)}
          </div>
        </div>
      </div>

      {/* Uptime */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <svg className="w-4 h-4 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a2 2 0 11-3 0 1.5 1.5 0 013 0z" />
          </svg>
          <span className="text-sm font-medium">Uptime</span>
        </div>
        <div className="text-right">
          <div className={cn("text-lg font-semibold", getStatusColor(uptime, true))}>
            {formatPercentage(uptime)}
          </div>
          <div className="text-xs text-muted-foreground">
            Higher is better
          </div>
        </div>
      </div>

      {/* Resource Usage */}
      {showDetails && resourceUsage && (
        <div className="space-y-3">
          <div className="text-sm font-medium mb-2">Resource Usage</div>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-lg font-semibold text-orange-600">
                {resourceUsage.cpu.toFixed(1)}%
              </div>
              <div className="text-sm text-muted-foreground">CPU</div>
            </div>
            
            <div className="text-center">
              <div className="text-lg font-semibold text-blue-600">
                {resourceUsage.memory.toFixed(0)} MB
              </div>
              <div className="text-sm text-muted-foreground">Memory</div>
            </div>
            
            <div className="text-center">
              <div className="text-lg font-semibold text-purple-600">
                {resourceUsage.network.toFixed(1)} MB/s
              </div>
              <div className="text-sm text-muted-foreground">Network</div>
            </div>
          </div>
        </div>
      )}

      {/* Last Updated */}
      <div className="text-xs text-muted-foreground text-right">
        Last updated: {lastUpdated.toLocaleString()}
      </div>
    </div>
  );
}

export { AgentPerformanceMetricsComponent as AgentPerformanceMetrics };