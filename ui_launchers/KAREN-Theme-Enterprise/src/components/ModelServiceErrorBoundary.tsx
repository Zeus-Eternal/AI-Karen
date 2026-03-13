'use client';

import React from 'react';
import { Alert, AlertDescription, AlertTitle } from './ui/alert';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { 
  Brain, 
  WifiOff, 
  RefreshCw, 
  AlertTriangle, 
  Settings,
  ExternalLink
} from 'lucide-react';

interface ModelServiceErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorType: 'distilbert' | 'network' | 'model-load' | 'unknown';
  retryCount: number;
}

interface ModelServiceErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<{ 
    error: Error; 
    retry: () => void; 
    errorType: string;
    retryCount: number;
  }>;
  onError?: (error: Error, errorType: string) => void;
  maxRetries?: number;
}

export class ModelServiceErrorBoundary extends React.Component<
  ModelServiceErrorBoundaryProps, 
  ModelServiceErrorBoundaryState
> {
  private retryTimeouts: NodeJS.Timeout[] = [];

  constructor(props: ModelServiceErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorType: 'unknown',
      retryCount: 0,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ModelServiceErrorBoundaryState> {
    // Categorize model service specific errors
    let errorType: 'distilbert' | 'network' | 'model-load' | 'unknown' = 'unknown';
    
    if (error.message.includes('DISTILBERT MODEL LOADING FAILED') ||
        error.message.includes('distilbert-base-uncased') ||
        error.message.includes('huggingface.co') && error.message.includes('offline mode')) {
      errorType = 'distilbert';
    } else if (error.message.includes('huggingface.co') ||
               error.message.includes('offline mode') ||
               error.message.includes("couldn't connect to")) {
      errorType = 'network';
    } else if (error.message.includes('model loading') ||
               error.message.includes('Failed to load model')) {
      errorType = 'model-load';
    }
    
    return {
      hasError: true,
      error,
      errorType,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    const { errorType } = this.state;
    
    // Log error with context
    console.error(`ModelServiceErrorBoundary caught ${errorType} error:`, error, errorInfo);
    
    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorType);
    }
    
    // In production, send to monitoring service
    if (process.env.NODE_ENV === 'production') {
      // This would integrate with your monitoring service
      console.warn('Model service error logged:', {
        errorType,
        message: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        timestamp: new Date().toISOString(),
      });
    }
  }

  componentWillUnmount() {
    // Clean up any pending retry timeouts
    this.retryTimeouts.forEach(timeout => clearTimeout(timeout));
  }

  private handleRetry = () => {
    const { maxRetries = 3 } = this.props;
    const { retryCount } = this.state;

    if (retryCount >= maxRetries) {
      console.warn('Max retries reached for model service');
      return;
    }

    // Clear any existing retry timeouts
    this.retryTimeouts.forEach(timeout => clearTimeout(timeout));
    this.retryTimeouts = [];

    // Exponential backoff for retries
    const delay = Math.min(2000 * Math.pow(2, retryCount), 15000);
    
    const timeout = setTimeout(() => {
      this.setState(prevState => ({
        hasError: false,
        error: null,
        errorType: 'unknown',
        retryCount: prevState.retryCount + 1,
      }));
    }, delay);

    this.retryTimeouts.push(timeout);
  };

  private handleReset = () => {
    this.retryTimeouts.forEach(timeout => clearTimeout(timeout));
    this.retryTimeouts = [];
    this.setState({
      hasError: false,
      error: null,
      errorType: 'unknown',
      retryCount: 0,
    });
  };

  private getErrorContent = () => {
    const { error, errorType, retryCount } = this.state;
    const { maxRetries = 3 } = this.props;

    switch (errorType) {
      case 'distilbert':
        return {
          icon: <Brain className="h-5 w-5" />,
          title: 'AI Model Unavailable',
          description: 'The DistilBERT AI model is currently unavailable in offline mode. This affects memory and advanced chat features.',
          actions: this.getDistilBERTActions(),
          help: [
            'Check your internet connection',
            'Try switching to online mode',
            'Some features will be limited until the model is available',
          ],
        };
      
      case 'network':
        return {
          icon: <WifiOff className="h-5 w-5" />,
          title: 'Network Connection Error',
          description: 'Unable to connect to the AI model service. Please check your internet connection.',
          actions: this.getNetworkActions(),
          help: [
            'Verify your internet connection',
            'Check if the service is running',
            'Try disabling VPN or proxy',
          ],
        };
      
      case 'model-load':
        return {
          icon: <AlertTriangle className="h-5 w-5" />,
          title: 'Model Loading Failed',
          description: 'The AI model failed to load properly. This may be due to insufficient resources or configuration issues.',
          actions: this.getModelLoadActions(),
          help: [
            'Check server resources',
            'Verify model configuration',
            'Try restarting the service',
          ],
        };
      
      default:
        return {
          icon: <AlertTriangle className="h-5 w-5" />,
          title: 'Model Service Error',
          description: error?.message || 'An unexpected error occurred in the model service.',
          actions: this.getDefaultActions(),
          help: [
            'Try refreshing the page',
            'Check the error details below',
            'Contact support if the issue persists',
          ],
        };
    }
  };

  private getDistilBERTActions = () => {
    const { retryCount } = this.state;
    const { maxRetries = 3 } = this.props;

    return (
      <div className="space-y-3">
        <div className="flex flex-col sm:flex-row gap-2">
          <Button 
            onClick={this.handleRetry} 
            className="flex-1"
            disabled={retryCount >= maxRetries}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            {retryCount > 0 ? `Retry (${retryCount}/${maxRetries})` : 'Try Reload'}
          </Button>
          
          <Button 
            onClick={this.handleReset} 
            variant="outline" 
            className="flex-1"
          >
            Reset
          </Button>
        </div>
        
        <div className="text-sm text-muted-foreground">
          <p className="font-medium mb-2">To resolve this issue:</p>
          <ul className="space-y-1 ml-4">
            <li>• Connect to the internet</li>
            <li>• Set TRANSFORMERS_OFFLINE=0</li>
            <li>• Or download models manually to ./models/transformers</li>
          </ul>
        </div>
        
        <Button 
          variant="ghost" 
          size="sm"
          className="w-full"
          onClick={() => window.open('https://huggingface.co/docs/transformers/installation#offline-mode', '_blank')}
        >
          <ExternalLink className="h-4 w-4 mr-2" />
          View Offline Mode Documentation
        </Button>
      </div>
    );
  };

  private getNetworkActions = () => {
    const { retryCount } = this.state;
    const { maxRetries = 3 } = this.props;

    return (
      <div className="space-y-3">
        <div className="flex flex-col sm:flex-row gap-2">
          <Button 
            onClick={this.handleRetry} 
            className="flex-1"
            disabled={retryCount >= maxRetries}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            {retryCount > 0 ? `Retry (${retryCount}/${maxRetries})` : 'Retry Connection'}
          </Button>
          
          <Button 
            onClick={this.handleReset} 
            variant="outline" 
            className="flex-1"
          >
            Reset
          </Button>
        </div>
      </div>
    );
  };

  private getModelLoadActions = () => {
    const { retryCount } = this.state;
    const { maxRetries = 3 } = this.props;

    return (
      <div className="space-y-3">
        <div className="flex flex-col sm:flex-row gap-2">
          <Button 
            onClick={this.handleRetry} 
            className="flex-1"
            disabled={retryCount >= maxRetries}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            {retryCount > 0 ? `Retry (${retryCount}/${maxRetries})` : 'Retry Loading'}
          </Button>
          
          <Button 
            onClick={this.handleReset} 
            variant="outline" 
            className="flex-1"
          >
            Reset
          </Button>
        </div>
      </div>
    );
  };

  private getDefaultActions = () => {
    const { retryCount } = this.state;
    const { maxRetries = 3 } = this.props;

    return (
      <div className="space-y-3">
        <div className="flex flex-col sm:flex-row gap-2">
          <Button 
            onClick={this.handleRetry} 
            className="flex-1"
            disabled={retryCount >= maxRetries}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            {retryCount > 0 ? `Retry (${retryCount}/${maxRetries})` : 'Try Again'}
          </Button>
          
          <Button 
            onClick={this.handleReset} 
            variant="outline" 
            className="flex-1"
          >
            Reset
          </Button>
        </div>
      </div>
    );
  };

  render() {
    if (this.state.hasError) {
      const { fallback: Fallback } = this.props;
      const { error, errorType, retryCount } = this.state;

      if (Fallback && error) {
        return <Fallback error={error} retry={this.handleRetry} errorType={errorType} retryCount={retryCount} />;
      }

      const errorContent = this.getErrorContent();

      return (
        <div className="min-h-[400px] flex items-center justify-center p-4">
          <div className="max-w-lg w-full space-y-4">
            <Alert className="border-orange-200 bg-orange-50 dark:border-orange-800 dark:bg-orange-950">
              {errorContent.icon}
              <AlertTitle className="flex items-center gap-2 text-orange-800 dark:text-orange-200">
                {errorContent.title}
                <Badge variant="outline" className="text-orange-600 border-orange-300 dark:text-orange-400 dark:border-orange-700">
                  {errorType}
                </Badge>
              </AlertTitle>
              <AlertDescription className="text-orange-700 dark:text-orange-300">
                {errorContent.description}
              </AlertDescription>
            </Alert>

            {errorContent.actions}

            {process.env.NODE_ENV === 'development' && error && (
              <details className="p-4 bg-gray-100 dark:bg-gray-800 rounded-lg text-sm">
                <summary className="cursor-pointer font-medium mb-2">Error Details (Development)</summary>
                <div className="space-y-2">
                  <div>
                    <strong>Error Type:</strong> {errorType}
                  </div>
                  <div>
                    <strong>Message:</strong> {error.message}
                  </div>
                  <div>
                    <strong>Retry Count:</strong> {retryCount}/{this.props.maxRetries || 3}
                  </div>
                  {error.stack && (
                    <div>
                      <strong>Stack Trace:</strong>
                      <pre className="mt-1 p-2 bg-red-50 dark:bg-red-900/20 rounded text-red-800 dark:text-red-400 text-xs overflow-auto max-h-32">
                        {error.stack}
                      </pre>
                    </div>
                  )}
                </div>
              </details>
            )}

            {retryCount >= (this.props.maxRetries || 3) && (
              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertTitle>Maximum retries reached</AlertTitle>
                <AlertDescription>
                  The service appears to be temporarily unavailable. Please check the troubleshooting steps above or contact support if the problem persists.
                </AlertDescription>
              </Alert>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ModelServiceErrorBoundary;