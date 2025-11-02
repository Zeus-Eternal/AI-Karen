'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LucideIcon } from 'lucide-react';
import { cva, type VariantProps } from 'class-variance-authority';

const metricCardVariants = cva(
  'transition-all duration-200 hover:shadow-lg',
  {
    variants: {
      variant: {
        default: 'bg-card',
        primary: 'bg-gradient-to-br from-blue-500/10 to-blue-600/10 border-blue-500/20',
        success: 'bg-gradient-to-br from-green-500/10 to-green-600/10 border-green-500/20',
        warning: 'bg-gradient-to-br from-yellow-500/10 to-yellow-600/10 border-yellow-500/20',
        error: 'bg-gradient-to-br from-red-500/10 to-red-600/10 border-red-500/20',
        glass: 'glass-card',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
);

const iconBackgroundVariants = cva(
  'rounded-full p-2.5 w-10 h-10 flex items-center justify-center transition-all duration-200',
  {
    variants: {
      variant: {
        default: 'bg-primary/10 text-primary',
        primary: 'bg-blue-500/20 text-blue-600 dark:text-blue-400',
        success: 'bg-green-500/20 text-green-600 dark:text-green-400',
        warning: 'bg-yellow-500/20 text-yellow-600 dark:text-yellow-400',
        error: 'bg-red-500/20 text-red-600 dark:text-red-400',
        glass: 'bg-white/20 dark:bg-black/20 backdrop-blur-sm text-primary',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
);

export interface MetricCardProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof metricCardVariants> {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: LucideIcon;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  loading?: boolean;
}

export function MetricCard({
  className,
  variant = 'default',
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  loading = false,
  ...props
}: MetricCardProps) {
  return (
    <Card
      className={cn(metricCardVariants({ variant }), className)}
      {...props}
    >
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {Icon && (
          <div className={cn(iconBackgroundVariants({ variant }))}>
            <Icon className="h-4 w-4" />
          </div>
        )}
      </CardHeader>
      <CardContent>
        <div className="space-y-1">
          {loading ? (
            <div className="h-8 w-24 animate-pulse rounded bg-muted" />
          ) : (
            <div className="text-2xl font-bold tabular-nums">{value}</div>
          )}

          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            {trend && (
              <span
                className={cn(
                  'inline-flex items-center gap-0.5 font-medium',
                  trend.isPositive
                    ? 'text-green-600 dark:text-green-400'
                    : 'text-red-600 dark:text-red-400'
                )}
              >
                {trend.isPositive ? '↑' : '↓'} {Math.abs(trend.value)}%
              </span>
            )}
            {subtitle && <span>{subtitle}</span>}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default MetricCard;
