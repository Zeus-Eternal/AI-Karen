"use client";

import React from 'react';
import { Badge } from '@/components/ui/badge';
import { AgentCapability } from '../types';
import { cn } from '@/lib/utils';
import { badgeVariants } from '@/components/ui/badge';

interface AgentCapabilityBadgeProps {
  capability: AgentCapability;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
  className?: string;
}

export function AgentCapabilityBadge({
  capability,
  size = 'md',
  showIcon = true,
  className,
}: AgentCapabilityBadgeProps) {
  const getCapabilityIcon = (capability: AgentCapability) => {
    switch (capability) {
      case 'text-generation':
        return (
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2v-4a2 2 0 012-2h6a2 2 0 012 2v4a2 2 0 01-2 2h6a2 2 0 002 2v-4a2 2 0 00-2-2h-2z" />
          </svg>
        );
      case 'code-generation':
        return (
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-6-6-6 6m-6 0l6 6-6-6-6 6z" />
          </svg>
        );
      case 'data-analysis':
        return (
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        );
      case 'image-processing':
        return (
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 011.414-1.414L16 16m-4.586 4.586a2 2 0 01-1.414 1.414L4 16m4 4l4.586 4.586a2 2 0 001.414 1.414L16 16m4-4.586-4.586a2 2 0 00-1.414-1.414L4 16" />
          </svg>
        );
      case 'audio-processing':
        return (
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l-6 6v13m0 0a2 2 0 002 2h2a2 2 0 002-2m0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2z" />
          </svg>
        );
      case 'video-processing':
        return (
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 7.936l-3.553 6.051A1 1 0 0018 12.484L15 10z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.5 9.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'web-scraping':
        return (
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0zM13 8v4m-1 1h-2a1 1 0 00-1 1v4a1 1 0 001 1h2a1 1 0 001-1v-4z" />
          </svg>
        );
      case 'api-integration':
        return (
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l1.5-4.5m0 6L3 12" />
          </svg>
        );
      case 'database-query':
        return (
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 1.79 4 4h2c2.21 0 4-1.79 4V7M4 7h16M4 7v10c0 2.21 1.79 4 4h2c2.21 0 4-1.79 4V7M4 7h16" />
          </svg>
        );
      case 'file-processing':
        return (
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2v-4a2 2 0 012-2h6a2 2 0 012 2v4a2 2 0 01-2 2h6a2 2 0 002 2v-4a2 2 0 00-2-2h-2z" />
          </svg>
        );
      case 'natural-language-understanding':
        return (
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h4m-8 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'translation':
        return (
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m0 11.5a1.5 1.5 0 01-3 0V12m6-6v6.5a1.5 1.5 0 01-3 0V6" />
          </svg>
        );
      case 'summarization':
        return (
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2v-4a2 2 0 012-2h6a2 2 0 012 2v4a2 2 0 01-2 2h6a2 2 0 002 2v-4a2 2 0 00-2-2h-2z" />
          </svg>
        );
      case 'classification':
        return (
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h10M7 12h10m-7 5h10M5 7v10M9 17l-3-3m0 0l3 3" />
          </svg>
        );
      case 'recommendation':
        return (
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 11l3 3L22 4l-1 1-4-4-4-4H6a2 2 0 00-2 2v8a2 2 0 002 2h8l-3 3z" />
          </svg>
        );
      case 'automation':
        return (
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        );
      case 'monitoring':
        return (
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2z" />
          </svg>
        );
      case 'security-analysis':
        return (
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 22s8-4 8-4V8s0-4 8-4v10s-4 4-8 4z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 22s8-4 8-4V8s0-4 8-4v10s-4 4-8 4z" />
          </svg>
        );
      default:
        return (
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
    }
  };

  const formatCapabilityName = (capability: AgentCapability) => {
    return capability
      .split('-')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const sizeClasses = {
    sm: 'text-xs px-1.5 py-0.5',
    md: 'text-xs px-2 py-0.5',
    lg: 'text-sm px-2.5 py-1',
  };

  return (
    <div
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 text-foreground",
        sizeClasses[size],
        className
      )}
    >
      {showIcon && (
        <span className="flex-shrink-0">
          {getCapabilityIcon(capability)}
        </span>
      )}
      <span className="truncate">
        {formatCapabilityName(capability)}
      </span>
    </div>
  );
}