"use client";

import React from 'react';
import { Badge } from "@/components/ui/badge";
import { Activity, AlertTriangle, XOctagon, HelpCircle } from "lucide-react";

export type HealthState = 'green' | 'yellow' | 'red' | 'unknown';

export interface ExtensionHealthIndicatorProps {
  health: HealthState;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
  showLabel?: boolean;
  className?: string;
}

const healthConfig = {
  green: {
    label: 'Healthy',
    icon: Activity,
    className: 'bg-green-500 hover:bg-green-600 text-white',
    dotColor: 'bg-green-500',
  },
  yellow: {
    label: 'Warning',
    icon: AlertTriangle,
    className: 'bg-yellow-500 hover:bg-yellow-600 text-white',
    dotColor: 'bg-yellow-500',
  },
  red: {
    label: 'Critical',
    icon: XOctagon,
    className: 'bg-red-500 hover:bg-red-600 text-white',
    dotColor: 'bg-red-500',
  },
  unknown: {
    label: 'Unknown',
    icon: HelpCircle,
    className: 'bg-gray-400 hover:bg-gray-500 text-white',
    dotColor: 'bg-gray-400',
  },
};

const sizeConfig = {
  sm: {
    badge: 'text-xs px-1.5 py-0.5',
    icon: 'h-3 w-3',
    dot: 'h-2 w-2',
  },
  md: {
    badge: 'text-sm px-2 py-1',
    icon: 'h-4 w-4',
    dot: 'h-3 w-3',
  },
  lg: {
    badge: 'text-base px-3 py-1.5',
    icon: 'h-5 w-5',
    dot: 'h-4 w-4',
  },
};

export default function ExtensionHealthIndicator({
  health,
  size = 'sm',
  showIcon = true,
  showLabel = true,
  className = '',
}: ExtensionHealthIndicatorProps) {
  const config = healthConfig[health];
  const sizes = sizeConfig[size];
  const Icon = config.icon;

  // If only showing dot (no icon, no label)
  if (!showIcon && !showLabel) {
    return (
      <div
        className={`${sizes.dot} ${config.dotColor} rounded-full ${className}`}
        title={config.label}
      />
    );
  }

  return (
    <Badge
      variant="outline"
      className={`${config.className} ${sizes.badge} ${className} flex items-center gap-1 w-fit`}
    >
      {showIcon && <Icon className={sizes.icon} />}
      {showLabel && config.label}
    </Badge>
  );
}

export { ExtensionHealthIndicator };
export type { ExtensionHealthIndicatorProps, HealthState };
