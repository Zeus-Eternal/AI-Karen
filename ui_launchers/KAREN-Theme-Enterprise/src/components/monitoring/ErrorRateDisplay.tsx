/**
 * Error rate and error metrics display component
 */

import React, { useState } from 'react';
import { ErrorMetrics } from './types';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';

export interface ErrorRateDisplayProps {
  errorMetrics: ErrorMetrics;
  className?: string;
  showRecentErrors?: boolean;
}

export const ErrorRateDisplay: React.FC<ErrorRateDisplayProps> = ({
  errorMetrics,
  className = '',
  showRecentErrors = true
}) => {
  const [showDetails, setShowDetails] = useState(false);

  const getErrorRateStatus = (errorRate: number) => {
    if (errorRate < 1) return { status: 'low', color: 'text-green-600', bg: 'bg-green-50', variant: 'default' as const };
    if (errorRate < 5) return { status: 'medium', color: 'text-yellow-600', bg: 'bg-yellow-50', variant: 'secondary' as const };
    return { status: 'high', color: 'text-red-600', bg: 'bg-red-50', variant: 'destructive' as const };
  };

  const formatTimestamp = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    }).format(date);
  };

  const errorStatus = getErrorRateStatus(errorMetrics.errorRate);
  const sortedErrorTypes = Object.entries(errorMetrics.errorsByType)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5); // Show top 5 error types

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between">
          <span className="text-lg font-semibold">Error Metrics</span>
          <Badge variant={errorStatus.variant} className="text-xs sm:text-sm md:text-base">
            {errorStatus.status.toUpperCase()} RATE
          </Badge>
        </CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Error Rate Overview */}
        <div className={`p-4 rounded-lg ${errorStatus.bg}`}>
          <div className="text-center">
            <div className={`font-bold text-3xl ${errorStatus.color}`}>
              {errorMetrics.errorRate.toFixed(1)}%
            </div>
            <div className="text-sm text-muted-foreground mb-2 md:text-base lg:text-lg">Error Rate</div>
            <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
              {errorMetrics.totalErrors.toLocaleString()} total errors
            </div>
          </div>
        </div>

        {/* Error Types Breakdown */}
        {sortedErrorTypes.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="font-medium text-sm md:text-base lg:text-lg">Error Types</h4>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowDetails(!showDetails)}
                className="text-xs sm:text-sm md:text-base"
              >
                {showDetails ? 'Hide' : 'Show'} Details
              </Button>
            </div>
            
            <div className="space-y-2">
              {sortedErrorTypes.map(([errorType, count]) => {
                const percentage = (count / errorMetrics.totalErrors) * 100;
                return (
                  <div key={errorType} className="space-y-1">
                    <div className="flex justify-between items-center text-sm md:text-base lg:text-lg">
                      <span className="font-medium truncate" title={errorType}>
                        {errorType}
                      </span>
                      <div className="flex items-center space-x-2">
                        <span className="text-muted-foreground">
                          {count}
                        </span>
                        <span className="text-xs text-muted-foreground sm:text-sm md:text-base">
                          ({percentage.toFixed(1)}%)
                        </span>
                      </div>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-red-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Recent Errors */}
        {showRecentErrors && errorMetrics.recentErrors.length > 0 && (
          <div className="space-y-3">
            <h4 className="font-medium text-sm md:text-base lg:text-lg">Recent Errors</h4>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {errorMetrics.recentErrors.slice(0, 10).map((error, index) => (
                <div 
                  key={`${error.correlationId}-${index}`}
                  className="p-2 bg-red-50 rounded border-l-4 border-red-500 sm:p-4 md:p-6"
                >
                  <div className="flex justify-between items-start text-sm md:text-base lg:text-lg">
                    <div className="flex-1 min-w-0 ">
                      <div className="font-medium text-red-700 truncate" title={error.message}>
                        {error.message}
                      </div>
                      <div className="text-xs text-red-600 mt-1 sm:text-sm md:text-base">
                        Type: {error.type}
                      </div>
                      {showDetails && (
                        <div className="text-xs text-muted-foreground mt-1 font-mono sm:text-sm md:text-base">
                          ID: {error.correlationId}
                        </div>
                      )}
                    </div>
                    <div className="text-xs text-muted-foreground ml-2 flex-shrink-0 sm:text-sm md:text-base">
                      {formatTimestamp(error.timestamp)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
            
            {errorMetrics.recentErrors.length > 10 && (
              <div className="text-center">
                <Button variant="outline" size="sm" className="text-xs sm:text-sm md:text-base" >
                  View All Errors ({errorMetrics.recentErrors.length})
                </Button>
              </div>
            )}
          </div>
        )}

        {/* Error Rate Trend Indicator */}
        <div className="p-3 bg-gray-50 rounded-lg sm:p-4 md:p-6">
          <div className="flex items-center justify-between text-sm md:text-base lg:text-lg">
            <span className="text-muted-foreground">Status</span>
            <div className="flex items-center space-x-2">
              <div 
                className={`w-2 h-2 rounded-full ${
                  errorMetrics.errorRate < 1 ? 'bg-green-500' :
                  errorMetrics.errorRate < 5 ? 'bg-yellow-500' :
                  'bg-red-500'
                }`}
              />
              <span className={`font-medium ${errorStatus.color}`}>
                {errorMetrics.errorRate < 1 ? 'System Healthy' :
                 errorMetrics.errorRate < 5 ? 'Elevated Errors' :
                 'High Error Rate'}
              </span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};