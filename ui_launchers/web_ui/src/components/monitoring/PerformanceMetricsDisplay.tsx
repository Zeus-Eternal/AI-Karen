/**
 * Performance metrics display component
 */

import React from 'react';
import { PerformanceMetrics } from './types';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';

interface PerformanceMetricsDisplayProps {
  metrics: PerformanceMetrics;
  className?: string;
  showTrends?: boolean;
}

export const PerformanceMetricsDisplay: React.FC<PerformanceMetricsDisplayProps> = ({
  metrics,
  className = '',
  showTrends = false
}) => {
  const formatTime = (time: number) => {
    if (time < 1000) {
      return `${Math.round(time)}ms`;
    }
    return `${(time / 1000).toFixed(2)}s`;
  };

  const formatThroughput = (throughput: number) => {
    if (throughput < 1) {
      return `${(throughput * 60).toFixed(1)}/min`;
    }
    return `${throughput.toFixed(1)}/sec`;
  };

  const getPerformanceStatus = (avgTime: number) => {
    if (avgTime < 1000) return { status: 'excellent', color: 'text-green-600', bg: 'bg-green-50' };
    if (avgTime < 3000) return { status: 'good', color: 'text-blue-600', bg: 'bg-blue-50' };
    if (avgTime < 5000) return { status: 'fair', color: 'text-yellow-600', bg: 'bg-yellow-50' };
    return { status: 'poor', color: 'text-red-600', bg: 'bg-red-50' };
  };

  const getErrorRateStatus = (errorRate: number) => {
    if (errorRate < 1) return { status: 'excellent', color: 'text-green-600' };
    if (errorRate < 5) return { status: 'good', color: 'text-yellow-600' };
    return { status: 'poor', color: 'text-red-600' };
  };

  const performanceStatus = getPerformanceStatus(metrics.averageResponseTime);
  const errorStatus = getErrorRateStatus(metrics.errorRate);

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between">
          <span className="text-lg font-semibold">Performance Metrics</span>
          <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
            {metrics.timeRange}
          </Badge>
        </CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Response Time Metrics */}
        <div className={`p-3 rounded-lg ${performanceStatus.bg}`}>
          <div className="flex justify-between items-center mb-2">
            <h4 className="font-medium text-sm md:text-base lg:text-lg">Response Times</h4>
            <Badge 
              variant={performanceStatus.status === 'excellent' ? 'default' : 'secondary'}
              className="text-xs capitalize sm:text-sm md:text-base"
            >
              {performanceStatus.status}
            </Badge>
          </div>
          
          <div className="grid grid-cols-3 gap-3 text-sm md:text-base lg:text-lg">
            <div className="text-center">
              <div className={`font-bold text-lg ${performanceStatus.color}`}>
                {formatTime(metrics.averageResponseTime)}
              </div>
              <div className="text-muted-foreground">Average</div>
            </div>
            <div className="text-center">
              <div className={`font-bold text-lg ${performanceStatus.color}`}>
                {formatTime(metrics.p95ResponseTime)}
              </div>
              <div className="text-muted-foreground">95th %ile</div>
            </div>
            <div className="text-center">
              <div className={`font-bold text-lg ${performanceStatus.color}`}>
                {formatTime(metrics.p99ResponseTime)}
              </div>
              <div className="text-muted-foreground">99th %ile</div>
            </div>
          </div>
        </div>

        {/* Request Volume and Error Rate */}
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 bg-blue-50 rounded-lg sm:p-4 md:p-6">
            <div className="text-center">
              <div className="font-bold text-2xl text-blue-600">
                {metrics.requestCount.toLocaleString()}
              </div>
              <div className="text-sm text-muted-foreground md:text-base lg:text-lg">Total Requests</div>
              <div className="text-xs text-blue-600 mt-1 sm:text-sm md:text-base">
                {formatThroughput(metrics.throughput)}
              </div>
            </div>
          </div>
          
          <div className={`p-3 rounded-lg ${
            metrics.errorRate < 1 ? 'bg-green-50' : 
            metrics.errorRate < 5 ? 'bg-yellow-50' : 
            'bg-red-50'
          }`}>
            <div className="text-center">
              <div className={`font-bold text-2xl ${errorStatus.color}`}>
                {metrics.errorRate.toFixed(1)}%
              </div>
              <div className="text-sm text-muted-foreground md:text-base lg:text-lg">Error Rate</div>
              <div className={`text-xs mt-1 ${errorStatus.color}`}>
                {errorStatus.status === 'excellent' ? 'Excellent' : 
                 errorStatus.status === 'good' ? 'Acceptable' : 'High'}
              </div>
            </div>
          </div>
        </div>

        {/* Performance Indicators */}
        <div className="space-y-2">
          <h4 className="font-medium text-sm md:text-base lg:text-lg">Performance Indicators</h4>
          
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm md:text-base lg:text-lg">
              <span>Response Time</span>
              <div className="flex items-center space-x-2">
                <div className="w-24 bg-gray-200 rounded-full h-2 sm:w-auto md:w-full">
                  <div 
                    className={`h-2 rounded-full ${
                      metrics.averageResponseTime < 1000 ? 'bg-green-500' :
                      metrics.averageResponseTime < 3000 ? 'bg-yellow-500' :
                      'bg-red-500'
                    }`}
                    style={{ 
                      width: `${Math.min((metrics.averageResponseTime / 5000) * 100, 100)}%` 
                    }}
                  />
                </div>
                <span className="text-xs text-muted-foreground sm:text-sm md:text-base">
                  {formatTime(metrics.averageResponseTime)}
                </span>
              </div>
            </div>
            
            <div className="flex items-center justify-between text-sm md:text-base lg:text-lg">
              <span>Error Rate</span>
              <div className="flex items-center space-x-2">
                <div className="w-24 bg-gray-200 rounded-full h-2 sm:w-auto md:w-full">
                  <div 
                    className={`h-2 rounded-full ${
                      metrics.errorRate < 1 ? 'bg-green-500' :
                      metrics.errorRate < 5 ? 'bg-yellow-500' :
                      'bg-red-500'
                    }`}
                    style={{ 
                      width: `${Math.min((metrics.errorRate / 10) * 100, 100)}%` 
                    }}
                  />
                </div>
                <span className="text-xs text-muted-foreground sm:text-sm md:text-base">
                  {metrics.errorRate.toFixed(1)}%
                </span>
              </div>
            </div>
            
            <div className="flex items-center justify-between text-sm md:text-base lg:text-lg">
              <span>Throughput</span>
              <div className="flex items-center space-x-2">
                <div className="w-24 bg-gray-200 rounded-full h-2 sm:w-auto md:w-full">
                  <div 
                    className="h-2 rounded-full bg-blue-500"
                    style={{ 
                      width: `${Math.min((metrics.throughput / 10) * 100, 100)}%` 
                    }}
                  />
                </div>
                <span className="text-xs text-muted-foreground sm:text-sm md:text-base">
                  {formatThroughput(metrics.throughput)}
                </span>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};