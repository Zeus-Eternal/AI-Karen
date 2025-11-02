/**
 * Example Component Demonstrating Intelligent Error Panel Usage
 * 
 * Shows different ways to integrate the IntelligentErrorPanel component
 * and demonstrates various error scenarios and configurations.
 * 
 * Requirements: 3.2, 3.3, 3.7, 4.4
 */
import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { IntelligentErrorPanel } from './IntelligentErrorPanel';
import { withIntelligentError } from './withIntelligentError';
import { useIntelligentError, useIntelligentApiError } from '@/hooks/use-intelligent-error';
// Example error scenarios
const ERROR_SCENARIOS = {
  api_key_missing: {
    error: 'OpenAI API key not found',
    errorType: 'AuthenticationError',
    statusCode: 401,
    providerName: 'openai',
    description: 'Missing API key error'
  },
  rate_limit: {
    error: 'Rate limit exceeded for OpenAI API',
    errorType: 'RateLimitError',
    statusCode: 429,
    providerName: 'openai',
    description: 'Rate limiting error'
  },
  network_error: {
    error: 'Connection timeout while connecting to Anthropic',
    errorType: 'NetworkError',
    statusCode: 504,
    providerName: 'anthropic',
    description: 'Network connectivity error'
  },
  validation_error: {
    error: 'Invalid input: message cannot be empty',
    errorType: 'ValidationError',
    statusCode: 400,
    providerName: 'system',
    description: 'Input validation error'
  },
  system_error: {
    error: 'Database connection failed',
    errorType: 'DatabaseError',
    statusCode: 500,
    providerName: 'system',
    description: 'System/database error'
  }
};
/**
 * Basic usage example
 */
export const BasicErrorPanelExample: React.FC = () => {
  const [selectedScenario, setSelectedScenario] = useState<keyof typeof ERROR_SCENARIOS>('api_key_missing');
  const [showPanel, setShowPanel] = useState(false);
  const scenario = ERROR_SCENARIOS[selectedScenario];
  return (
    <Card className="w-full max-w-4xl ">
      <CardHeader>
        <CardTitle>Basic Intelligent Error Panel</CardTitle>
        <CardDescription>
          Select an error scenario to see how the intelligent error panel analyzes and provides guidance.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center space-x-4">
          <select
            value={selectedScenario}
            onValueChange={(value) = aria-label="Select option"> setSelectedScenario(value as keyof typeof ERROR_SCENARIOS)}
          >
            <selectTrigger className="w-64 " aria-label="Select option">
              <selectValue />
            </SelectTrigger>
            <selectContent aria-label="Select option">
              {Object.entries(ERROR_SCENARIOS).map(([key, scenario]) => (
                <selectItem key={key} value={key} aria-label="Select option">
                  {scenario.description}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button onClick={() => setShowPanel(true)}>
          </Button>
          {showPanel && (
            <Button variant="outline" onClick={() => setShowPanel(false)}>
            </Button>
          )}
        </div>
        {showPanel && (
          <IntelligentErrorPanel
            error={scenario.error}
            errorType={scenario.errorType}
            statusCode={scenario.statusCode}
            providerName={scenario.providerName}
            requestPath="/api/example"
            userContext={{ feature: 'example', userId: 'demo' }}
            onRetry={() => console.log('Retry clicked')}
            onDismiss={() => setShowPanel(false)}
            showTechnicalDetails={true}
          />
        )}
      </CardContent>
    </Card>
  );
};
/**
 * Hook usage example
 */
export const HookUsageExample: React.FC = () => {
  const intelligentError = useIntelligentError({
    onAnalysisComplete: (analysis) => {
    },
    onAnalysisError: (error) => {
    }

  const [selectedScenario, setSelectedScenario] = useState<keyof typeof ERROR_SCENARIOS>('api_key_missing');
  const triggerError = () => {
    const scenario = ERROR_SCENARIOS[selectedScenario];
    intelligentError.analyzeError(scenario.error, {
      error_type: scenario.errorType,
      status_code: scenario.statusCode,
      provider_name: scenario.providerName,
      request_path: '/api/hook-example',

  };
  return (
    <Card className="w-full max-w-4xl ">
      <CardHeader>
        <CardTitle>Hook Usage Example</CardTitle>
        <CardDescription>
          Demonstrates using the useIntelligentError hook for custom error handling.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center space-x-4">
          <select
            value={selectedScenario}
            onValueChange={(value) = aria-label="Select option"> setSelectedScenario(value as keyof typeof ERROR_SCENARIOS)}
          >
            <selectTrigger className="w-64 " aria-label="Select option">
              <selectValue />
            </SelectTrigger>
            <selectContent aria-label="Select option">
              {Object.entries(ERROR_SCENARIOS).map(([key, scenario]) => (
                <selectItem key={key} value={key} aria-label="Select option">
                  {scenario.description}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button onClick={triggerError} disabled={intelligentError.isAnalyzing} >
          </Button>
          {intelligentError.analysis && (
            <Button variant="outline" onClick={intelligentError.clearAnalysis} >
            </Button>
          )}
        </div>
        {intelligentError.isAnalyzing && (
          <div className="text-sm text-muted-foreground md:text-base lg:text-lg">
            Analyzing error...
          </div>
        )}
        {intelligentError.analysisError && (
          <div className="text-sm text-red-600 md:text-base lg:text-lg">
            Analysis failed: {intelligentError.analysisError}
            <Button
              variant="link"
              size="sm"
              onClick={intelligentError.retryAnalysis}
              className="ml-2"
             >
            </Button>
          </div>
        )}
        {intelligentError.analysis && (
          <div className="bg-muted/50 rounded-lg p-4 sm:p-4 md:p-6">
            <h4 className="font-medium mb-2">Analysis Result:</h4>
            <div className="space-y-2 text-sm md:text-base lg:text-lg">
              <div><strong>Title:</strong> {intelligentError.analysis.title}</div>
              <div><strong>Summary:</strong> {intelligentError.analysis.summary}</div>
              <div><strong>Severity:</strong> {intelligentError.analysis.severity}</div>
              <div><strong>Category:</strong> {intelligentError.analysis.category}</div>
              <div>
                <strong>Next Steps:</strong>
                <ul className="list-disc list-inside ml-4 mt-1">
                  {intelligentError.analysis.next_steps.map((step, index) => (
                    <li key={index}>{step}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
/**
 * API Error Hook Example
 */
export const ApiErrorExample: React.FC = () => {
  const apiError = useIntelligentApiError();
  const simulateApiError = () => {
    const mockApiError = {
      message: 'Request failed with status 500',
      status: 500,
      name: 'ApiError',
      isNetworkError: false,
      isCorsError: false,
      isTimeoutError: false,
      responseTime: 2500,
    };
    apiError.handleApiError(mockApiError, {
      endpoint: '/api/chat/completions',
      method: 'POST',
      provider: 'openai',

  };
  return (
    <Card className="w-full max-w-4xl ">
      <CardHeader>
        <CardTitle>API Error Hook Example</CardTitle>
        <CardDescription>
          Demonstrates automatic API error detection and analysis.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <Button onClick={simulateApiError} disabled={apiError.isAnalyzing} >
        </Button>
        {apiError.analysis && (
          <IntelligentErrorPanel
            error="API request failed"
            autoFetch={false}
            onDismiss={apiError.clearAnalysis}
          />
        )}
      </CardContent>
    </Card>
  );
};
/**
 * Component with automatic error detection using HOC
 */
const ProblematicComponent: React.FC<{ shouldError: boolean }> = ({ shouldError }) => {
  if (shouldError) {
    throw new Error('This component intentionally failed');
  }
  return (
    <div className="p-4 bg-green-50 rounded-lg border border-green-200 sm:p-4 md:p-6">
      <p className="text-green-800">Component is working correctly!</p>
    </div>
  );
};
const EnhancedProblematicComponent = withIntelligentError(ProblematicComponent, {
  position: 'top',
  replaceOnError: false,
  errorPanelProps: {
    showTechnicalDetails: true,
  },

export const HOCExample: React.FC = () => {
  const [shouldError, setShouldError] = useState(false);
  return (
    <Card className="w-full max-w-4xl ">
      <CardHeader>
        <CardTitle>Higher-Order Component Example</CardTitle>
        <CardDescription>
          Shows automatic error detection using the withIntelligentError HOC.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center space-x-4">
          <Button
            variant={shouldError ? "destructive" : "default"}
            onClick={() => setShouldError(!shouldError)}
          >
            {shouldError ? 'Fix Component' : 'Break Component'}
          </Button>
        </div>
        <EnhancedProblematicComponent shouldError={shouldError} />
      </CardContent>
    </Card>
  );
};
/**
 * Complete example showcasing all features
 */
export const IntelligentErrorExamples: React.FC = () => {
  return (
    <div className="space-y-8 p-6 sm:p-4 md:p-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">Intelligent Error Panel Examples</h1>
        <p className="text-muted-foreground">
          Comprehensive examples showing different ways to use the intelligent error handling system.
        </p>
      </div>
      <BasicErrorPanelExample />
      <HookUsageExample />
      <ApiErrorExample />
      <HOCExample />
    </div>
  );
};
export default IntelligentErrorExamples;
