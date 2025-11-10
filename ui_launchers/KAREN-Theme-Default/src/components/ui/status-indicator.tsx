'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { cva, type VariantProps } from 'class-variance-authority';

const statusIndicatorVariants = cva(
  'inline-flex items-center gap-2 font-medium transition-all duration-200',
  {
    variants: {
      status: {
        online: 'text-green-700 dark:text-green-400',
        offline: 'text-gray-500 dark:text-gray-400',
        warning: 'text-yellow-700 dark:text-yellow-400',
        error: 'text-red-700 dark:text-red-400',
        loading: 'text-blue-700 dark:text-blue-400',
        success: 'text-green-700 dark:text-green-400',
      },
      size: {
        sm: 'text-xs',
        md: 'text-sm',
        lg: 'text-base',
      },
    },
    defaultVariants: {
      status: 'online',
      size: 'md',
    },
  }
);

type StatusVariant = NonNullable<VariantProps<typeof statusIndicatorVariants>['status']>;

const dotVariants = cva(
  'rounded-full transition-all duration-300',
  {
    variants: {
      status: {
        online: 'bg-green-500 shadow-[0_0_12px_rgba(34,197,94,0.6)]',
        offline: 'bg-gray-400',
        warning: 'bg-yellow-500 shadow-[0_0_12px_rgba(245,158,11,0.6)]',
        error: 'bg-red-500 shadow-[0_0_12px_rgba(239,68,68,0.6)]',
        loading: 'bg-blue-500 shadow-[0_0_12px_rgba(59,130,246,0.6)] animate-pulse',
        success: 'bg-green-500 shadow-[0_0_12px_rgba(34,197,94,0.6)]',
      },
      size: {
        sm: 'h-1.5 w-1.5',
        md: 'h-2 w-2',
        lg: 'h-2.5 w-2.5',
      },
      pulse: {
        true: 'animate-pulse',
        false: '',
      },
    },
    defaultVariants: {
      status: 'online',
      size: 'md',
      pulse: false,
    },
  }
);

export interface StatusIndicatorProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof statusIndicatorVariants> {
  label?: string;
  showDot?: boolean;
  pulse?: boolean;
}

const STATUS_LABELS: Record<StatusVariant, string> = {
  online: 'Online',
  offline: 'Offline',
  warning: 'Warning',
  error: 'Error',
  loading: 'Loading',
  success: 'Success',
};

export function StatusIndicator({
  className,
  status = 'online',
  size = 'md',
  label,
  showDot = true,
  pulse = false,
  ...props
}: StatusIndicatorProps) {
  const normalizedStatus: StatusVariant =
    status && status in STATUS_LABELS ? (status as StatusVariant) : 'online';

  return (
    <div
      className={cn(statusIndicatorVariants({ status: normalizedStatus, size }), className)}
      {...props}
    >
      {showDot && (
        <span className={cn(dotVariants({ status: normalizedStatus, size, pulse }))} />
      )}
      <span>{label ?? STATUS_LABELS[normalizedStatus]}</span>
    </div>
  );
}

export default StatusIndicator;
