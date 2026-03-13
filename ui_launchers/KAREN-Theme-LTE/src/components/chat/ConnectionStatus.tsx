/**
 * Connection Status Component
 * Show WebSocket connection status
 */

import React from 'react';
import { cn } from '@/lib/utils';
import { ConnectionStatus as ConnectionStatusType } from '@/types/chat';
import { Badge } from '@/components/ui/badge';
import { 
  Wifi, 
  WifiOff, 
  AlertTriangle, 
  Loader2,
  CheckCircle,
  XCircle
} from 'lucide-react';

export interface ConnectionStatusProps {
  status: ConnectionStatusType;
  className?: string;
  showText?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export function ConnectionStatus({ 
  status, 
  className, 
  showText = true,
  size = 'md'
}: ConnectionStatusProps) {
  const getStatusIcon = () => {
    if (status.isConnecting) {
      return <Loader2 className="animate-spin" />;
    }
    
    if (status.isReconnecting) {
      return <Loader2 className="animate-spin" />;
    }
    
    if (status.isConnected) {
      return <CheckCircle />;
    }
    
    return <XCircle />;
  };

  const getStatusText = () => {
    if (status.isConnecting) return 'Connecting...';
    if (status.isReconnecting) return 'Reconnecting...';
    if (status.isConnected) return 'Connected';
    return 'Disconnected';
  };

  const getStatusColor = () => {
    if (status.isConnecting || status.isReconnecting) return 'orange';
    if (status.isConnected) return 'green';
    return 'red';
  };

  const getStatusBadge = () => {
    const color = getStatusColor();
    const text = getStatusText();
    
    return (
      <Badge 
        variant="outline" 
        className={cn(
          'border-current',
          color === 'green' && 'text-green-400 border-green-500/30 bg-green-500/10',
          color === 'orange' && 'text-orange-400 border-orange-500/30 bg-orange-500/10',
          color === 'red' && 'text-red-400 border-red-500/30 bg-red-500/10'
        )}
      >
        {text}
      </Badge>
    );
  };

  const getIconSize = () => {
    switch (size) {
      case 'sm': return 'h-4 w-4';
      case 'lg': return 'h-6 w-6';
      default: return 'h-5 w-5';
    }
  };

  const getTextColor = () => {
    const color = getStatusColor();
    return cn(
      color === 'green' && 'text-green-400',
      color === 'orange' && 'text-orange-400',
      color === 'red' && 'text-red-400'
    );
  };

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <div className={cn('flex items-center', getTextColor())}>
        <div className={getIconSize()}>
          {getStatusIcon()}
        </div>
        
        {showText && (
          <span className="text-sm font-medium">
            {getStatusText()}
          </span>
        )}
      </div>
      
      {/* Connection details */}
      {status.error && (
        <div className="flex items-center gap-1 text-red-400">
          <AlertTriangle className="h-4 w-4" />
          <span className="text-xs">
            {status.error}
          </span>
        </div>
      )}
      
      {/* Connection attempts indicator */}
      {status.connectionAttempts > 1 && (
        <div className="text-xs text-purple-400">
          Attempt {status.connectionAttempts}
        </div>
      )}
      
      {/* Last connected time */}
      {status.lastConnected && (
        <div className="text-xs text-purple-400">
          Last: {new Intl.DateTimeFormat('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
          }).format(status.lastConnected)}
        </div>
      )}
    </div>
  );
}

// Compact version for inline use
export function ConnectionStatusCompact({ 
  status, 
  className 
}: Omit<ConnectionStatusProps, 'showText' | 'size'>) {
  const isConnected = status.isConnected;
  
  return (
    <div className={cn('flex items-center gap-1', className)}>
      <div className={cn(
        'w-2 h-2 rounded-full',
        isConnected 
          ? 'bg-green-500' 
          : 'bg-red-500'
      )} />
      
      {!isConnected && (
        <span className="text-xs text-red-400">
          {status.error ? 'Error' : 'Offline'}
        </span>
      )}
    </div>
  );
}

// Badge version for headers
export function ConnectionStatusBadge({ 
  status, 
  className 
}: Omit<ConnectionStatusProps, 'showText' | 'size'>) {
  const getStatusBadge = () => {
    if (status.isConnecting) {
      return (
        <Badge variant="outline" className="text-orange-400 border-orange-500/30 bg-orange-500/10">
          Connecting
        </Badge>
      );
    }
    
    if (status.isReconnecting) {
      return (
        <Badge variant="outline" className="text-orange-400 border-orange-500/30 bg-orange-500/10">
          Reconnecting
        </Badge>
      );
    }
    
    if (status.isConnected) {
      return (
        <Badge variant="outline" className="text-green-400 border-green-500/30 bg-green-500/10">
          Connected
        </Badge>
      );
    }
    
    return (
      <Badge variant="outline" className="text-red-400 border-red-500/30 bg-red-500/10">
        Disconnected
      </Badge>
    );
  };

  return (
    <div className={cn('', className)}>
      {getStatusBadge()}
    </div>
  );
}