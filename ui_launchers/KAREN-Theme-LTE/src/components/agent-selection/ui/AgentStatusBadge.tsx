"use client";

import React from 'react';
import { Badge, badgeVariants } from '@/components/ui/badge';
import { AgentStatus } from '../types';
import { cn } from '@/lib/utils';
import { VariantProps } from 'class-variance-authority';

interface AgentStatusBadgeProps {
  status: AgentStatus;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
  showLabel?: boolean;
  className?: string;
}

export function AgentStatusBadge({
  status,
  size = 'md',
  showIcon = true,
  showLabel = true,
  className,
}: AgentStatusBadgeProps) {
  const getStatusConfig = (status: AgentStatus) => {
    switch (status) {
      case 'available':
        return {
          label: 'Available',
          color: 'default',
          icon: (
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a2 2 0 002-2h-2a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2v-6a2 2 0 00-2-2h-2z" />
            </svg>
          ),
        };
      case 'busy':
        return {
          label: 'Busy',
          color: 'secondary',
          icon: (
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          ),
        };
      case 'maintenance':
        return {
          label: 'Maintenance',
          color: 'outline',
          icon: (
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c-.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-1.756.426-1.756 2.924 0 3.35a1.724 1.724 0 001.066-2.573c.94-1.543.826-3.31 2.37-2.37.996.609 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          ),
        };
      case 'offline':
        return {
          label: 'Offline',
          color: 'outline',
          icon: (
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636l-3.536-3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l3.536-3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
          ),
        };
      case 'error':
        return {
          label: 'Error',
          color: 'destructive',
          icon: (
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          ),
        };
      default:
        return {
          label: status,
          color: 'outline',
          icon: null,
        };
    }
  };

  const config = getStatusConfig(status);
  
  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-xs px-2.5 py-0.5',
    lg: 'text-sm px-3 py-1',
  };

  return (
    <Badge
      variant={config.color as VariantProps<typeof badgeVariants>['variant']}
      className={cn(
        "inline-flex items-center gap-1",
        sizeClasses[size],
        className
      )}
    >
      {showIcon && config.icon && (
        <span className="flex-shrink-0">
          {config.icon}
        </span>
      )}
      {showLabel && (
        <span>{config.label}</span>
      )}
    </Badge>
  );
}