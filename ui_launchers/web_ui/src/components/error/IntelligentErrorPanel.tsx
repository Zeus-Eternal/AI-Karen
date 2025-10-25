'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { AlertTriangle, RefreshCw, ExternalLink, Clock, CheckCircle, XCircle, AlertCircle, Info } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { getApiClient } from '@/lib/api-client';
import { cn } from '@/lib/utils';

// Types based on the backend API
export interface ErrorAnalysisRequest {
  error_message: string;
  error_type?: string;
  status_code?: number;
  provider_name?: string;
  request_path?: string;
  user_context?: Record<string, any>;
  use_ai_analysis?: boolean;
}

export interface ErrorAnalysisResponse {
  title: string;
  summary: string;
  category: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  next_steps: string[];
  provider_health?: {
    name: string;
    status: 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
    success_rate: number;
    response_time: number;
    error_message?: string;
    last_check?: string;
  };
  contact_admin: boolean;
  retry_after?: number;
  help_url?: string;
  technical_details?: string;
  cached: boolean;
  response_time_ms: number;
}

export interface IntelligentErrorPanelProps {
  error: Error | string;
  errorType?: string;
  statusCode?: number;
  providerName?: string;
  requestPath?: string;
  userContext?: Record<string, any>;
  useAiAnalysis?: boolean;
  onRetry?: () => void;
  onDismiss?: () => void;
  className?: string;
  autoFetch?: boolean;
  showTechnicalDetails?: boolean;
  maxRetries?: number;
}

const getSeverityIcon = (severity: string) => {
  switch (severity) {
    case 'critical':
      return <XCircle className="h-5 w-5 text-red-500" />;
    case 'high':
      return <AlertTriangle className="h-5 w-5 text-orange-500" />;
    case 'medium':
      return <AlertCircle className="h-5 w-5 text-yellow-500" />;
    case 'low':
      return <Info className="h-5 w-5 text-blue-500" />;
    default:
      return <AlertCircle className="h-5 w-5 text-gray-500" />;
  }
};

const getSeverityColor = (severity: string) => {
  switch (severity) {
    case 'critical':
      return 'destructive';
    case 'high':
      return 'destructive';
    case 'medium':
      return 'default';
    case 'low':
      return 'secondary';
    default:
      return 'outline';
  }
};

const getProviderHealthIcon = (status: string) => {
  switch (status) {
    case 'healthy':
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    case 'degraded':
      return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
    case 'unhealthy':
      return <XCircle className="h-4 w-4 text-red-500" />;
    default:
      return <AlertCircle className="h-4 w-4 text-gray-500" />;
  }
};

export const IntelligentErrorPanel: React.FC<IntelligentErrorPanelProps> = ({
  error,
  errorType,
  statusCode,
  providerName,
  requestPath,
  userContext,
  useAiAnalysis = true,
  onRetry,
  onDismiss,
  className,
  autoFetch = true,
  showTechnicalDetails = false,
  maxRetries = 3,
}) => {
  const [analysis, setAnalysis] = useState<ErrorAnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const [showDetails, setShowDetails] = useState(showTechnicalDetails);

  const apiClient = getApiClient();

  const errorMessage = typeof error === 'string' ? error : error.message;

  const fetchAnalysis = useCallback(async () => {
    if (!errorMessage || isLoading) return;

    setIsLoading(true);
    setFetchError(null);

    try {
      const request: ErrorAnalysisRequest = {
        error_message: errorMessage,
        error_type: errorType,
        status_code: statusCode,
        provider_name: providerName,
        request_path: requestPath,
        user_context: userContext,
        use_ai_analysis: useAiAnalysis,
      };

      const response = await apiClient.post<ErrorAnalysisResponse>(
        '/api/error-response/analyze',
        request
      );

      setAnalysis(response.data);
    } catch (err: any) {
      console.error('Failed to fetch error analysis:', err);
      setFetchError(err.message || 'Failed to analyze error');
      
      // Create fallback analysis
      setAnalysis({
        title: 'Error Analysis Unavailable',
        summary: 'Unable to generate intelligent error response at this time.',
        category: 'system_error',
        severity: 'medium',
        next_steps: [
          'Try refreshing the page',
          'Check your internet connection',
          'Contact admin if the problem persists'
        ],
        contact_admin: true,
        cached: false,
        response_time_ms: 0,
      });
    } finally {
      setIsLoading(false);
    }
  }, [errorMessage, errorType, statusCode, providerName, requestPath, userContext, useAiAnalysis, apiClient, isLoading]);

  const handleRetry = useCallback(() => {
    if (retryCount < maxRetries) {
      setRetryCount(prev => prev + 1);
      onRetry?.();
    }
  }, [retryCount, maxRetries, onRetry]);

  const handleRefreshAnalysis = useCallback(() => {
    fetchAnalysis();
  }, [fetchAnalysis]);

  // Auto-fetch analysis on mount or when error changes
  useEffect(() => {
    if (autoFetch) {
      fetchAnalysis();
    }
  }, [autoFetch, fetchAnalysis]);

  // Loading state
  if (isLoading && !analysis) {
    return (
      <Card className={cn('w-full', className)}>
        <CardHeader>
          <div className="flex items-center space-x-2">
            <RefreshCw className="h-5 w-5 animate-spin text-blue-500" />
            <CardTitle className="text-lg">Analyzing Error...</CardTitle>
          </div>
          <CardDescription>
            Generating intelligent response and next steps
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <div className="space-y-2">
            <Skeleton className="h-3 w-1/2" />
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-full" />
          </div>
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (fetchError && !analysis) {
    return (
      <Alert variant="destructive" className={className}>
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>Analysis Failed</AlertTitle>
        <AlertDescription className="mt-2">
          <p>{fetchError}</p>
          <div className="flex gap-2 mt-3">
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefreshAnalysis}
              disabled={isLoading}
            >
              <RefreshCw className={cn("h-4 w-4 mr-2", isLoading && "animate-spin")} />
              Try Again
            </Button>
            {onDismiss && (
              <Button variant="ghost" size="sm" onClick={onDismiss}>
                Dismiss
              </Button>
            )}
          </div>
        </AlertDescription>
      </Alert>
    );
  }

  if (!analysis) {
    return null;
  }

  return (
    <Card className={cn('w-full border-l-4', {
      'border-l-red-500': analysis.severity === 'critical',
      'border-l-orange-500': analysis.severity === 'high',
      'border-l-yellow-500': analysis.severity === 'medium',
      'border-l-blue-500': analysis.severity === 'low',
    }, className)}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-3">
            {getSeverityIcon(analysis.severity)}
            <div>
              <CardTitle className="text-lg">{analysis.title}</CardTitle>
              <div className="flex items-center space-x-2 mt-1">
                <Badge variant={getSeverityColor(analysis.severity) as any}>
                  {analysis.severity.toUpperCase()}
                </Badge>
                {analysis.cached && (
                  <Badge variant="outline" className="text-xs">
                    <Clock className="h-3 w-3 mr-1" />
                    Cached
                  </Badge>
                )}
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRefreshAnalysis}
              disabled={isLoading}
              title="Refresh analysis"
            >
              <RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />
            </Button>
            {onDismiss && (
              <Button variant="ghost" size="sm" onClick={onDismiss}>
                ×
              </Button>
            )}
          </div>
        </div>
        <CardDescription className="text-base mt-2">
          {analysis.summary}
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Provider Health Status */}
        {analysis.provider_health && (
          <div className="bg-muted/50 rounded-lg p-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                {getProviderHealthIcon(analysis.provider_health.status)}
                <span className="font-medium text-sm">
                  {analysis.provider_health.name} Status
                </span>
              </div>
              <div className="text-right text-sm text-muted-foreground">
                <div>{analysis.provider_health.success_rate}% success rate</div>
                <div>{analysis.provider_health.response_time}ms avg</div>
              </div>
            </div>
            {analysis.provider_health.error_message && (
              <p className="text-sm text-muted-foreground mt-2">
                {analysis.provider_health.error_message}
              </p>
            )}
          </div>
        )}

        {/* Next Steps */}
        {analysis.next_steps.length > 0 && (
          <div>
            <h4 className="font-medium text-sm mb-2">Next Steps:</h4>
            <ol className="space-y-2">
              {analysis.next_steps.map((step, index) => (
                <li key={index} className="flex items-start space-x-2 text-sm">
                  <span className="flex-shrink-0 w-5 h-5 bg-primary/10 text-primary rounded-full flex items-center justify-center text-xs font-medium">
                    {index + 1}
                  </span>
                  <span>{step}</span>
                </li>
              ))}
            </ol>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-2 pt-2">
          {onRetry && retryCount < maxRetries && (
            <Button
              variant="default"
              size="sm"
              onClick={handleRetry}
              disabled={analysis.retry_after ? true : false}
            >
              {analysis.retry_after ? (
                <>
                  <Clock className="h-4 w-4 mr-2" />
                  Retry in {analysis.retry_after}s
                </>
              ) : (
                <>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Try Again {retryCount > 0 && `(${retryCount}/${maxRetries})`}
                </>
              )}
            </Button>
          )}

          {analysis.help_url && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.open(analysis.help_url, '_blank')}
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              Help
            </Button>
          )}

          {analysis.contact_admin && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                // This could open a support modal or mailto link
                const subject = encodeURIComponent(`Error: ${analysis.title}`);
                const body = encodeURIComponent(`Error Details:\n${analysis.summary}\n\nTechnical Details:\n${analysis.technical_details || errorMessage}`);
                window.open(`mailto:admin@example.com?subject=${subject}&body=${body}`, '_blank');
              }}
            >
              Contact Admin
            </Button>
          )}

          {analysis.technical_details && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowDetails(!showDetails)}
            >
              {showDetails ? 'Hide' : 'Show'} Details
            </Button>
          )}
        </div>

        {/* Technical Details */}
        {showDetails && analysis.technical_details && (
          <div className="bg-muted/30 rounded-lg p-3 border">
            <h4 className="font-medium text-sm mb-2">Technical Details:</h4>
            <pre className="text-xs text-muted-foreground whitespace-pre-wrap font-mono">
              {analysis.technical_details}
            </pre>
          </div>
        )}

        {/* Analysis Metadata */}
        <div className="flex justify-between items-center text-xs text-muted-foreground pt-2 border-t">
          <span>
            Analysis: {analysis.response_time_ms.toFixed(1)}ms
            {analysis.cached && ' (cached)'}
          </span>
          <span>Category: {analysis.category}</span>
        </div>
      </CardContent>
    </Card>
  );
};

export default IntelligentErrorPanel;