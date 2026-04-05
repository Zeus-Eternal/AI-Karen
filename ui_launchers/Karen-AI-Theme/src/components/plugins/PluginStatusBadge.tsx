import React from 'react';
import { CheckCircle2, XCircle, AlertTriangle, Clock, Download } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { PluginStatus } from '@/types/plugin';

interface PluginStatusBadgeProps {
  status: PluginStatus;
  showIcon?: boolean;
  className?: string;
}

const statusConfig = {
  installed: {
    label: 'Installed',
    icon: CheckCircle2,
    className: 'bg-green-500/10 text-green-600 dark:text-green-400 border-green-500/20',
  },
  available: {
    label: 'Available',
    icon: Download,
    className: 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20',
  },
  compatible: {
    label: 'Compatible',
    icon: Clock,
    className: 'bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 border-yellow-500/20',
  },
  incompatible: {
    label: 'Incompatible',
    icon: XCircle,
    className: 'bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20',
  },
};

export function PluginStatusBadge({ status, showIcon = true, className }: PluginStatusBadgeProps) {
  // Default to 'available' if status is undefined
  const safeStatus = status || 'available';
  const config = statusConfig[safeStatus];
  const Icon = config.icon;

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge variant="outline" className={`${config.className} ${className}`}>
            {showIcon && <Icon className="h-3 w-3 mr-1" />}
            {config.label}
          </Badge>
        </TooltipTrigger>
        <TooltipContent>
          <p>
            {safeStatus === 'installed' && 'Plugin is currently installed and active.'}
            {safeStatus === 'available' && 'Plugin is available for installation from the store.'}
            {safeStatus === 'compatible' && 'Plugin is compatible with your Karen AI version.'}
            {safeStatus === 'incompatible' && 'Plugin is not compatible with your current setup.'}
          </p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
