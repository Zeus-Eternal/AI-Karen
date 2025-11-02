/**
 * Connection status indicator component
 */

import React from 'react';
import { ConnectionStatus } from './types';
import { Badge } from '../ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface ConnectionStatusIndicatorProps {
  status: ConnectionStatus;
  title: string;
  showDetails?: boolean;
  className?: string;
}

export const ConnectionStatusIndicator: React.FC<ConnectionStatusIndicatorProps> = ({
  status,
  title,
  showDetails = false,
  className = ''
}) => {
  const getStatusColor = (status: ConnectionStatus['status']) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-500';
      case 'degraded':
        return 'bg-yellow-500';
      case 'failed':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusText = (status: ConnectionStatus['status']) => {
    switch (status) {
      case 'healthy':
        return 'Healthy';
      case 'degraded':
        return 'Degraded';
      case 'failed':
        return 'Failed';
      default:
        return 'Unknown';
    }
  };

  const formatResponseTime = (time: number) => {
    if (time < 1000) {
      return `${Math.round(time)}ms`;
    }
    return `${(time / 1000).toFixed(2)}s`;
  };

  const formatLastCheck = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    if (diff < 60000) {
      return 'Just now';
    } else if (diff < 3600000) {
      return `${Math.floor(diff / 60000)}m ago`;
    } else {
      return `${Math.floor(diff / 3600000)}h ago`;
    }
  };

  const successRate = status.successCount + status.errorCount > 0 
    ? (status.successCount / (status.successCount + status.errorCount)) * 100 
    : 0;

  return (
    <Card className={`${className}`}>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between text-sm font-medium md:text-base lg:text-lg">
          <span>{title}</span>
          <div className="flex items-center space-x-2">
            <div 
              className={`w-3 h-3 rounded-full ${getStatusColor(status.status)}`}
              title={`Status: ${getStatusText(status.status)}`}
            />
            <Badge 
              variant={status.status === 'healthy' ? 'default' : 'destructive'}
              className="text-xs sm:text-sm md:text-base"
            >
              {getStatusText(status.status)}
            </Badge>
          </div>
        </CardTitle>
      </CardHeader>
      
      <CardContent className="pt-0">
        <div className="space-y-2">
          <div className="flex justify-between items-center text-sm md:text-base lg:text-lg">
            <span className="text-muted-foreground">Response Time:</span>
            <span className={`font-medium ${
              status.responseTime > 5000 ? 'text-red-600' : 
              status.responseTime > 2000 ? 'text-yellow-600' : 
              'text-green-600'
            }`}>
              {formatResponseTime(status.responseTime)}
            </span>
          </div>
          
          <div className="flex justify-between items-center text-sm md:text-base lg:text-lg">
            <span className="text-muted-foreground">Last Check:</span>
            <span className="font-medium">
              {formatLastCheck(status.lastCheck)}
            </span>
          </div>

          {showDetails && (
            <>
              <div className="flex justify-between items-center text-sm md:text-base lg:text-lg">
                <span className="text-muted-foreground">Success Rate:</span>
                <span className={`font-medium ${
                  successRate >= 95 ? 'text-green-600' : 
                  successRate >= 80 ? 'text-yellow-600' : 
                  'text-red-600'
                }`}>
                  {successRate.toFixed(1)}%
                </span>
              </div>
              
              <div className="flex justify-between items-center text-sm md:text-base lg:text-lg">
                <span className="text-muted-foreground">Endpoint:</span>
                <span className="font-mono text-xs truncate max-w-32 " title={status.endpoint}>
                  {status.endpoint}
                </span>
              </div>
              
              <div className="grid grid-cols-2 gap-2 text-xs sm:text-sm md:text-base">
                <div className="text-center p-2 bg-green-50 rounded sm:p-4 md:p-6">
                  <div className="font-medium text-green-700">{status.successCount}</div>
                  <div className="text-green-600">Success</div>
                </div>
                <div className="text-center p-2 bg-red-50 rounded sm:p-4 md:p-6">
                  <div className="font-medium text-red-700">{status.errorCount}</div>
                  <div className="text-red-600">Errors</div>
                </div>
              </div>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
};