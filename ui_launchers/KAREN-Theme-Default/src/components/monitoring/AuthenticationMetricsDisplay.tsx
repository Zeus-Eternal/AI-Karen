/**
 * Authentication metrics display component
 */

import React, { useState } from 'react';
import { AuthenticationMetrics } from './types';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';

interface AuthenticationMetricsDisplayProps {
  metrics: AuthenticationMetrics;
  className?: string;
  showRecentFailures?: boolean;
}

export const AuthenticationMetricsDisplay: React.FC<AuthenticationMetricsDisplayProps> = ({
  metrics,
  className = '',
  showRecentFailures = true
}) => {
  const [showDetails, setShowDetails] = useState(false);

  const getSuccessRateStatus = (successRate: number) => {
    if (successRate >= 95) return { status: 'excellent', color: 'text-green-600', bg: 'bg-green-50', variant: 'default' as const };
    if (successRate >= 85) return { status: 'good', color: 'text-blue-600', bg: 'bg-blue-50', variant: 'secondary' as const };
    if (successRate >= 70) return { status: 'fair', color: 'text-yellow-600', bg: 'bg-yellow-50', variant: 'secondary' as const };
    return { status: 'poor', color: 'text-red-600', bg: 'bg-red-50', variant: 'destructive' as const };
  };

  const formatAuthTime = (time: number) => {
    if (time < 1000) {
      return `${Math.round(time)}ms`;
    }
    return `${(time / 1000).toFixed(2)}s`;
  };

  const formatTimestamp = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    }).format(date);
  };

  const successRateStatus = getSuccessRateStatus(metrics.successRate);

  // Group recent failures by reason
  const failuresByReason = metrics.recentFailures.reduce((acc, failure) => {
    acc[failure.reason] = (acc[failure.reason] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const sortedFailureReasons = Object.entries(failuresByReason)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5);

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between">
          <span className="text-lg font-semibold">Authentication Metrics</span>
          <Badge variant={successRateStatus.variant} className="text-xs sm:text-sm md:text-base">
            {successRateStatus.status.toUpperCase()}
          </Badge>
        </CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Success Rate Overview */}
        <div className={`p-4 rounded-lg ${successRateStatus.bg}`}>
          <div className="text-center">
            <div className={`font-bold text-3xl ${successRateStatus.color}`}>
              {metrics.successRate.toFixed(1)}%
            </div>
            <div className="text-sm text-muted-foreground mb-2 md:text-base lg:text-lg">Success Rate</div>
            <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
              {metrics.totalAttempts.toLocaleString()} total attempts
            </div>
          </div>
        </div>

        {/* Authentication Stats Grid */}
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 bg-green-50 rounded-lg text-center sm:p-4 md:p-6">
            <div className="font-bold text-xl text-green-600">
              {metrics.successfulAttempts.toLocaleString()}
            </div>
            <div className="text-sm text-muted-foreground md:text-base lg:text-lg">Successful</div>
          </div>
          
          <div className="p-3 bg-red-50 rounded-lg text-center sm:p-4 md:p-6">
            <div className="font-bold text-xl text-red-600">
              {metrics.failedAttempts.toLocaleString()}
            </div>
            <div className="text-sm text-muted-foreground md:text-base lg:text-lg">Failed</div>
          </div>
        </div>

        {/* Average Auth Time */}
        <div className="p-3 bg-blue-50 rounded-lg sm:p-4 md:p-6">
          <div className="flex justify-between items-center">
            <span className="text-sm text-muted-foreground md:text-base lg:text-lg">Average Auth Time</span>
            <div className="text-right">
              <div className={`font-bold text-lg ${
                metrics.averageAuthTime < 1000 ? 'text-green-600' :
                metrics.averageAuthTime < 3000 ? 'text-yellow-600' :
                'text-red-600'
              }`}>
                {formatAuthTime(metrics.averageAuthTime)}
              </div>
              <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
                {metrics.averageAuthTime < 1000 ? 'Fast' :
                 metrics.averageAuthTime < 3000 ? 'Normal' :
                 'Slow'}
              </div>
            </div>
          </div>
        </div>

        {/* Failure Reasons */}
        {sortedFailureReasons.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="font-medium text-sm md:text-base lg:text-lg">Common Failure Reasons</h4>
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
              {sortedFailureReasons.map(([reason, count]) => {
                const percentage = (count / metrics.failedAttempts) * 100;
                return (
                  <div key={reason} className="space-y-1">
                    <div className="flex justify-between items-center text-sm md:text-base lg:text-lg">
                      <span className="font-medium truncate" title={reason}>
                        {reason}
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

        {/* Recent Failures */}
        {showRecentFailures && metrics.recentFailures.length > 0 && (
          <div className="space-y-3">
            <h4 className="font-medium text-sm md:text-base lg:text-lg">Recent Failures</h4>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {metrics.recentFailures.slice(0, 8).map((failure, index) => (
                <div 
                  key={`${failure.timestamp.getTime()}-${index}`}
                  className="p-2 bg-red-50 rounded border-l-4 border-red-500 sm:p-4 md:p-6"
                >
                  <div className="flex justify-between items-start text-sm md:text-base lg:text-lg">
                    <div className="flex-1 min-w-0 ">
                      <div className="font-medium text-red-700">
                        {failure.reason}
                      </div>
                      {showDetails && failure.email && (
                        <div className="text-xs text-red-600 mt-1 sm:text-sm md:text-base">
                          User: {failure.email}
                        </div>
                      )}
                    </div>
                    <div className="text-xs text-muted-foreground ml-2 flex-shrink-0 sm:text-sm md:text-base">
                      {formatTimestamp(failure.timestamp)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
            
            {metrics.recentFailures.length > 8 && (
              <div className="text-center">
                <Button variant="outline" size="sm" className="text-xs sm:text-sm md:text-base" >
                  View All Failures ({metrics.recentFailures.length})
                </Button>
              </div>
            )}
          </div>
        )}

        {/* Authentication Health Indicator */}
        <div className="p-3 bg-gray-50 rounded-lg sm:p-4 md:p-6">
          <div className="flex items-center justify-between text-sm md:text-base lg:text-lg">
            <span className="text-muted-foreground">Authentication Health</span>
            <div className="flex items-center space-x-2">
              <div 
                className={`w-2 h-2 rounded-full ${
                  metrics.successRate >= 95 ? 'bg-green-500' :
                  metrics.successRate >= 85 ? 'bg-blue-500' :
                  metrics.successRate >= 70 ? 'bg-yellow-500' :
                  'bg-red-500'
                }`}
              />
              <span className={`font-medium ${successRateStatus.color}`}>
                {metrics.successRate >= 95 ? 'Excellent' :
                 metrics.successRate >= 85 ? 'Good' :
                 metrics.successRate >= 70 ? 'Fair' :
                 'Needs Attention'}
              </span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};