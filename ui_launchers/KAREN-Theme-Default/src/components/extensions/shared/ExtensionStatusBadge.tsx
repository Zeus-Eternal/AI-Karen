"use client";

import React from 'react';
import { Badge } from "@/components/ui/badge";
import { CheckCircle, XCircle, Clock, AlertCircle, Ban } from "lucide-react";

export interface ExtensionStatusBadgeProps {
  status: 'active' | 'inactive' | 'loading' | 'error' | 'disabled';
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
  className?: string;
}

const statusConfig = {
  active: {
    label: 'Active',
    variant: 'default' as const,
    icon: CheckCircle,
    className: 'bg-green-500 hover:bg-green-600 text-white',
  },
  inactive: {
    label: 'Inactive',
    variant: 'secondary' as const,
    icon: XCircle,
    className: 'bg-gray-500 hover:bg-gray-600 text-white',
  },
  loading: {
    label: 'Loading',
    variant: 'outline' as const,
    icon: Clock,
    className: 'bg-blue-500 hover:bg-blue-600 text-white',
  },
  error: {
    label: 'Error',
    variant: 'destructive' as const,
    icon: AlertCircle,
    className: 'bg-red-500 hover:bg-red-600 text-white',
  },
  disabled: {
    label: 'Disabled',
    variant: 'outline' as const,
    icon: Ban,
    className: 'bg-gray-300 hover:bg-gray-400 text-gray-700',
  },
};

const sizeConfig = {
  sm: 'text-xs px-1.5 py-0.5',
  md: 'text-sm px-2 py-1',
  lg: 'text-base px-3 py-1.5',
};

export default function ExtensionStatusBadge({
  status,
  size = 'sm',
  showIcon = true,
  className = '',
}: ExtensionStatusBadgeProps) {
  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <Badge
      variant={config.variant}
      className={`${config.className} ${sizeConfig[size]} ${className} flex items-center gap-1 w-fit`}
    >
      {showIcon && <Icon className="h-3 w-3" />}
      {config.label}
    </Badge>
  );
}

export { ExtensionStatusBadge };
export type { ExtensionStatusBadgeProps };
