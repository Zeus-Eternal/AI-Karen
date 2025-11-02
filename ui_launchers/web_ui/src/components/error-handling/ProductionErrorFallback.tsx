/**
 * Production Error Fallback Component
 * 
 * Provides user-friendly error displays with recovery options
 * and intelligent fallback strategies for production environments.
 */
import React, { useState, useEffect } from 'react';
import { AlertTriangle, RefreshCw, Bug, Send, ChevronDown, ChevronUp } from 'lucide-react';
import { Button } from '../ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '../ui/collapsible';
import { ErrorFallbackProps } from './GlobalErrorBoundary';
export const ProductionErrorFallback: React.FC<ErrorFallbackProps> = ({
  error,
  errorInfo,
  errorReport,
  onRetry,
  onRecover,
  onReport,
  recoveryAttempts,
  maxRecoveryAttempts,
  fallbackMode,
  isRecovering
}) => {
  const [showDetails, setShowDetails] = useState(false);
  const [reportSent, setReportSent] = useState(false);
  const [autoRetryCountdown, setAutoRetryCountdown] = useState<number | null>(null);
  // Auto-retry logic for non-critical errors
  useEffect(() => {
    if (
      fallbackMode === 'full' && 
      recoveryAttempts < 2 && 
      !isRecovering &&
      errorReport?.severity !== 'critical'
    ) {
      setAutoRetryCountdown(5);
      const interval = setInterval(() => {
        setAutoRetryCountdown(prev => {
          if (prev === null || prev <= 1) {
            clearInterval(interval);
            onRecover();
            return null;
          }
          return prev - 1;
        });
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [fallbackMode, recoveryAttempts, isRecovering, errorReport?.severity, onRecover]);
  const handleSendReport = async () => {
    try {
      await onReport();
      setReportSent(true);
    } catch (error) {
    }
  };
  const getSeverityColor = (severity?: string) => {
    switch (severity) {
      case 'critical': return 'destructive';
      case 'high': return 'destructive';
      case 'medium': return 'secondary';
      case 'low': return 'outline';
      default: return 'secondary';
    }
  };
  const getSeverityIcon = (severity?: string) => {
    switch (severity) {
      case 'critical': return '🚨';
      case 'high': return '⚠️';
      case 'medium': return '⚡';
      case 'low': return 'ℹ️';
      default: return '❓';
    }
  };
  const renderMinimalFallback = () => (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <Card className="w-full max-w-md mx-4">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 w-12 h-12 rounded-full bg-destructive/10 flex items-center justify-center sm:w-auto md:w-full">
            <AlertTriangle className="w-6 h-6 text-destructive sm:w-auto md:w-full" />
          </div>
          <CardTitle className="text-xl">Application Error</CardTitle>
          <CardDescription>
            We're experiencing technical difficulties. Please try refreshing the page.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <button 
            onClick={() = aria-label="Button"> window.location.reload()} 
            className="w-full"
            size="lg"
          >
            <RefreshCw className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
            Refresh Page
          </Button>
          <div className="text-center">
            <button 
              variant="outline" 
              size="sm"
              onClick={handleSendReport}
              disabled={reportSent}
             aria-label="Button">
              <Send className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
              {reportSent ? 'Report Sent' : 'Send Error Report'}
            </Button>
          </div>
          {errorReport && (
            <div className="text-xs text-muted-foreground text-center sm:text-sm md:text-base">
              Error ID: {errorReport.id.split('-').pop()}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
  const renderDegradedFallback = () => (
    <div className="min-h-[400px] flex items-center justify-center p-4 sm:p-4 md:p-6">
      <Card className="w-full max-w-lg">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-destructive/10 flex items-center justify-center sm:w-auto md:w-full">
              <AlertTriangle className="w-5 h-5 text-destructive sm:w-auto md:w-full" />
            </div>
            <div>
              <CardTitle className="text-lg">Component Error</CardTitle>
              <CardDescription>
                This section is temporarily unavailable
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {errorReport && (
            <div className="flex items-center gap-2">
              <Badge variant={getSeverityColor(errorReport.severity)}>
                {getSeverityIcon(errorReport.severity)} {errorReport.severity?.toUpperCase()}
              </Badge>
              <Badge variant="outline">
                {errorReport.category?.toUpperCase()}
              </Badge>
            </div>
          )}
          {autoRetryCountdown && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 sm:p-4 md:p-6">
              <div className="flex items-center gap-2 text-blue-700">
                <RefreshCw className="w-4 h-4 animate-spin sm:w-auto md:w-full" />
                <span className="text-sm md:text-base lg:text-lg">
                  Auto-retry in {autoRetryCountdown} seconds...
                </span>
              </div>
            </div>
          )}
          <div className="flex gap-2">
            <button 
              onClick={onRetry} 
              disabled={isRecovering || autoRetryCountdown !== null}
              className="flex-1"
             aria-label="Button">
              {isRecovering ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin sm:w-auto md:w-full" />
                  Recovering...
                </>
              ) : (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
                  Try Again
                </>
              )}
            </Button>
            {recoveryAttempts < maxRecoveryAttempts && (
              <button 
                variant="outline" 
                onClick={onRecover}
                disabled={isRecovering || autoRetryCountdown !== null}
               aria-label="Button">
                Auto-Recover
              </Button>
            )}
          </div>
          <Collapsible open={showDetails} onOpenChange={setShowDetails}>
            <CollapsibleTrigger asChild>
              <button variant="ghost" size="sm" className="w-full" aria-label="Button">
                <Bug className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
                {showDetails ? 'Hide' : 'Show'} Details
                {showDetails ? (
                  <ChevronUp className="w-4 h-4 ml-2 sm:w-auto md:w-full" />
                ) : (
                  <ChevronDown className="w-4 h-4 ml-2 sm:w-auto md:w-full" />
                )}
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent className="space-y-2">
              <div className="bg-muted rounded-lg p-3 text-sm md:text-base lg:text-lg">
                <div className="font-medium mb-1">Error Message:</div>
                <div className="text-muted-foreground font-mono text-xs sm:text-sm md:text-base">
                  {error?.message || 'Unknown error'}
                </div>
              </div>
              {errorReport && (
                <div className="bg-muted rounded-lg p-3 text-sm md:text-base lg:text-lg">
                  <div className="font-medium mb-1">Error Details:</div>
                  <div className="space-y-1 text-xs text-muted-foreground sm:text-sm md:text-base">
                    <div>ID: {errorReport.id}</div>
                    <div>Time: {new Date(errorReport.timestamp).toLocaleString()}</div>
                    <div>Section: {errorReport.section}</div>
                    <div>Attempts: {recoveryAttempts}/{maxRecoveryAttempts}</div>
                  </div>
                </div>
              )}
              <button 
                variant="outline" 
                size="sm" 
                onClick={handleSendReport}
                disabled={reportSent}
                className="w-full"
               aria-label="Button">
                <Send className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
                {reportSent ? 'Report Sent' : 'Send Detailed Report'}
              </Button>
            </CollapsibleContent>
          </Collapsible>
        </CardContent>
      </Card>
    </div>
  );
  const renderFullFallback = () => (
    <div className="p-6 max-w-2xl mx-auto sm:w-auto md:w-full">
      <Card>
        <CardHeader>
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-full bg-destructive/10 flex items-center justify-center flex-shrink-0 sm:w-auto md:w-full">
              <AlertTriangle className="w-6 h-6 text-destructive sm:w-auto md:w-full" />
            </div>
            <div className="flex-1">
              <CardTitle className="text-xl mb-2">Something went wrong</CardTitle>
              <CardDescription className="text-base">
                We encountered an unexpected error. Our team has been notified and is working on a fix.
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {errorReport && (
            <div className="flex flex-wrap gap-2">
              <Badge variant={getSeverityColor(errorReport.severity)}>
                {getSeverityIcon(errorReport.severity)} {errorReport.severity?.toUpperCase()}
              </Badge>
              <Badge variant="outline">
                {errorReport.category?.toUpperCase()}
              </Badge>
              <Badge variant="secondary">
                Section: {errorReport.section}
              </Badge>
            </div>
          )}
          {autoRetryCountdown && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 sm:p-4 md:p-6">
              <div className="flex items-center gap-3">
                <RefreshCw className="w-5 h-5 text-blue-600 animate-spin sm:w-auto md:w-full" />
                <div>
                  <div className="font-medium text-blue-900">Automatic Recovery</div>
                  <div className="text-sm text-blue-700 md:text-base lg:text-lg">
                    Attempting to recover in {autoRetryCountdown} seconds...
                  </div>
                </div>
              </div>
            </div>
          )}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <button 
              onClick={onRetry} 
              disabled={isRecovering || autoRetryCountdown !== null}
              size="lg"
             aria-label="Button">
              {isRecovering ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin sm:w-auto md:w-full" />
                  Recovering...
                </>
              ) : (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
                  Try Again
                </>
              )}
            </Button>
            <button 
              variant="outline" 
              onClick={() = aria-label="Button"> window.location.reload()}
              size="lg"
            >
              Refresh Page
            </Button>
          </div>
          {recoveryAttempts < maxRecoveryAttempts && (
            <button 
              variant="secondary" 
              onClick={onRecover}
              disabled={isRecovering || autoRetryCountdown !== null}
              className="w-full"
             aria-label="Button">
              Attempt Smart Recovery
            </Button>
          )}
          <Collapsible open={showDetails} onOpenChange={setShowDetails}>
            <CollapsibleTrigger asChild>
              <button variant="ghost" className="w-full" aria-label="Button">
                <Bug className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
                {showDetails ? 'Hide' : 'Show'} Technical Details
                {showDetails ? (
                  <ChevronUp className="w-4 h-4 ml-2 sm:w-auto md:w-full" />
                ) : (
                  <ChevronDown className="w-4 h-4 ml-2 sm:w-auto md:w-full" />
                )}
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent className="space-y-4">
              <div className="bg-muted rounded-lg p-4 sm:p-4 md:p-6">
                <div className="font-medium mb-2">Error Information</div>
                <div className="space-y-2 text-sm md:text-base lg:text-lg">
                  <div>
                    <span className="font-medium">Message:</span>
                    <div className="font-mono text-xs bg-background p-2 rounded mt-1 sm:text-sm md:text-base">
                      {error?.message || 'Unknown error'}
                    </div>
                  </div>
                  {errorReport && (
                    <>
                      <div>
                        <span className="font-medium">Error ID:</span> {errorReport.id}
                      </div>
                      <div>
                        <span className="font-medium">Timestamp:</span> {new Date(errorReport.timestamp).toLocaleString()}
                      </div>
                      <div>
                        <span className="font-medium">Recovery Attempts:</span> {recoveryAttempts}/{maxRecoveryAttempts}
                      </div>
                      <div>
                        <span className="font-medium">Session ID:</span> {errorReport.sessionId}
                      </div>
                    </>
                  )}
                </div>
              </div>
              {error?.stack && (
                <div className="bg-muted rounded-lg p-4 sm:p-4 md:p-6">
                  <div className="font-medium mb-2">Stack Trace</div>
                  <pre className="text-xs font-mono bg-background p-2 rounded overflow-x-auto whitespace-pre-wrap sm:text-sm md:text-base">
                    {error.stack}
                  </pre>
                </div>
              )}
              <div className="flex gap-2">
                <button 
                  variant="outline" 
                  size="sm" 
                  onClick={handleSendReport}
                  disabled={reportSent}
                  className="flex-1"
                 aria-label="Button">
                  <Send className="w-4 h-4 mr-2 sm:w-auto md:w-full" />
                  {reportSent ? 'Report Sent' : 'Send Error Report'}
                </Button>
                <button 
                  variant="outline" 
                  size="sm"
                  onClick={() = aria-label="Button"> {
                    if (errorReport) {
                      navigator.clipboard.writeText(JSON.stringify(errorReport, null, 2));
                    }
                  }}
                >
                  Copy Details
                </Button>
              </div>
            </CollapsibleContent>
          </Collapsible>
        </CardContent>
      </Card>
    </div>
  );
  // Render based on fallback mode
  switch (fallbackMode) {
    case 'minimal':
      return renderMinimalFallback();
    case 'degraded':
      return renderDegradedFallback();
    case 'full':
    default:
      return renderFullFallback();
  }
};
export default ProductionErrorFallback;
