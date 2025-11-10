"use client";

import * as React from 'react';
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

import { 
  TestTube, 
  Clock, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  Play, 
  Activity, 
  Wifi, 
  Key, 
  Database, 
  Settings, 
  Zap 
} from 'lucide-react';
import { getKarenBackend } from '@/lib/karen-backend';

export interface TestResult {
  test_type: string;
  success: boolean;
  duration_ms: number;
  message: string;
  details?: Record<string, any>;
  timestamp: string;
}

export interface ValidationResult {
  connectivity: TestResult;
  authentication: TestResult;
  model_discovery: TestResult;
  capability_check: TestResult;
  performance_test: TestResult;
  overall_status: 'passed' | 'failed' | 'partial';
  recommendations: string[];
}

export interface ProviderTestingInterfaceProps {
  providerName: string;
  providerType: 'remote' | 'local' | 'hybrid';
  requiresApiKey: boolean;
  onTestComplete?: (result: ValidationResult) => void;
}

export function ProviderTestingInterface({
  providerName,
  providerType,
  requiresApiKey,
  onTestComplete
}: ProviderTestingInterfaceProps) {
  const [testing, setTesting] = useState(false);
  const [testResults, setTestResults] = useState<ValidationResult | null>(null);
  const [apiKey, setApiKey] = useState('');
  const [testPrompt, setTestPrompt] = useState('Hello, can you respond with a simple greeting?');
  const [activeTest, setActiveTest] = useState<string | null>(null);
  const { toast } = useToast();
  const backend = getKarenBackend();

  const runFullValidation = async () => {
    setTesting(true);
    setTestResults(null);
    try {
      const response = await backend.makeRequestPublic<ValidationResult>('/api/providers/validate-comprehensive', {
        method: 'POST',
        body: JSON.stringify({
          provider: providerName,
          api_key: requiresApiKey ? apiKey : undefined,
          test_prompt: testPrompt
        })
      });

      setTestResults(response);
      onTestComplete?.(response);
      toast({
        title: "Validation Complete",
        description: `Provider validation ${response.overall_status}`,
        variant: response.overall_status === 'failed' ? 'destructive' : 'default'
      });
    } catch (error) {
      toast({
        title: "Validation Failed",
        description: `Could not validate ${providerName}: ${(error as Error).message}`,
        variant: "destructive",
      });
    } finally {
      setTesting(false);
    }
  };

  const runIndividualTest = async (testType: string) => {
    setActiveTest(testType);
    try {
      const response = await backend.makeRequestPublic<TestResult>('/api/providers/test-individual', {
        method: 'POST',
        body: JSON.stringify({
          provider: providerName,
          test_type: testType,
          api_key: requiresApiKey ? apiKey : undefined,
          test_prompt: testPrompt
        })
      });

      // Update test results
      if (testResults) {
        const updatedResults = { ...testResults };
        (updatedResults as any)[testType] = response;
        setTestResults(updatedResults);
      }
      toast({
        title: `${testType} Test Complete`,
        description: response.success ? 'Test passed' : `Test failed: ${response.message}`,
        variant: response.success ? 'default' : 'destructive'
      });
    } catch (error) {
      toast({
        title: `${testType} Test Failed`,
        description: (error as Error).message,
        variant: "destructive",
      });
    } finally {
      setActiveTest(null);
    }
  };

  const getTestIcon = (result?: TestResult) => {
    if (!result) return <Clock className="h-4 w-4 text-gray-400" />;
    if (result.success) return <CheckCircle2 className="h-4 w-4 text-green-600" />;
    return <AlertCircle className="h-4 w-4 text-red-600" />;
  };

  const getTestBadge = (result?: TestResult) => {
    if (!result) return <Badge variant="outline">Not Run</Badge>;
    if (result.success) return <Badge variant="default" className="bg-green-100 text-green-800">Passed</Badge>;
    return <Badge variant="destructive">Failed</Badge>;
  };

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TestTube className="h-5 w-5" />
          Provider Testing & Validation
        </CardTitle>
        <CardDescription>
          Test connectivity, authentication, and capabilities for {providerName}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <Tabs defaultValue="quick" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="quick">Quick Test</TabsTrigger>
            <TabsTrigger value="detailed">Detailed Testing</TabsTrigger>
          </TabsList>
          
          <TabsContent value="quick" className="space-y-4">
            {/* API Key Input */}
            {requiresApiKey && (
              <div className="space-y-2">
                <Label htmlFor="api-key" className="flex items-center gap-2">
                  <Key className="h-4 w-4" />
                  API Key
                </Label>
                <Input
                  id="api-key"
                  type="password"
                  placeholder="Enter API key for testing..."
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                />
              </div>
            )}
            
            {/* Test Prompt */}
            <div className="space-y-2">
              <Label htmlFor="test-prompt">Test Prompt</Label>
              <Textarea
                id="test-prompt"
                placeholder="Enter a test prompt..."
                value={testPrompt}
                onChange={(e) => setTestPrompt(e.target.value)}
                rows={3}
              />
            </div>
            
            {/* Quick Test Button */}
            <Button
              onClick={runFullValidation}
              disabled={testing || (requiresApiKey && !apiKey.trim())}
              className="w-full"
            >
              {testing ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Running Validation...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  Run Quick Validation
                </>
              )}
            </Button>
            
            {/* Quick Results */}
            {testResults && (
              <Alert variant={testResults.overall_status === 'failed' ? 'destructive' : 'default'}>
                <Activity className="h-4 w-4" />
                <AlertTitle>Validation Results</AlertTitle>
                <AlertDescription>
                  <div className="space-y-2 mt-2">
                    <div className="flex items-center justify-between">
                      <span>Overall Status:</span>
                      <Badge variant={testResults.overall_status === 'passed' ? 'default' : 'destructive'}>
                        {testResults.overall_status}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div className="flex items-center gap-2">
                        {getTestIcon(testResults.connectivity)}
                        <span>Connectivity</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {getTestIcon(testResults.authentication)}
                        <span>Authentication</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {getTestIcon(testResults.model_discovery)}
                        <span>Model Discovery</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {getTestIcon(testResults.capability_check)}
                        <span>Capabilities</span>
                      </div>
                    </div>
                  </div>
                </AlertDescription>
              </Alert>
            )}
          </TabsContent>
          
          <TabsContent value="detailed" className="space-y-4">
            {/* Individual Test Controls */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Connectivity Test */}
              <Card>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Wifi className="h-4 w-4" />
                      <CardTitle className="text-sm">Connectivity</CardTitle>
                    </div>
                    {getTestBadge(testResults?.connectivity)}
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => runIndividualTest('connectivity')}
                    disabled={activeTest === 'connectivity'}
                    className="w-full"
                  >
                    {activeTest === 'connectivity' ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      'Test Connection'
                    )}
                  </Button>
                  {testResults?.connectivity && (
                    <div className="mt-2 text-xs text-muted-foreground">
                      <div>Duration: {formatDuration(testResults.connectivity.duration_ms)}</div>
                      <div>Message: {testResults.connectivity.message}</div>
                    </div>
                  )}
                </CardContent>
              </Card>
              
              {/* Authentication Test */}
              <Card>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Key className="h-4 w-4" />
                      <CardTitle className="text-sm">Authentication</CardTitle>
                    </div>
                    {getTestBadge(testResults?.authentication)}
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => runIndividualTest('authentication')}
                    disabled={activeTest === 'authentication' || (requiresApiKey && !apiKey.trim())}
                    className="w-full"
                  >
                    {activeTest === 'authentication' ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      'Test Auth'
                    )}
                  </Button>
                  {testResults?.authentication && (
                    <div className="mt-2 text-xs text-muted-foreground">
                      <div>Duration: {formatDuration(testResults.authentication.duration_ms)}</div>
                      <div>Message: {testResults.authentication.message}</div>
                    </div>
                  )}
                </CardContent>
              </Card>
              
              {/* Model Discovery Test */}
              <Card>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Database className="h-4 w-4" />
                      <CardTitle className="text-sm">Model Discovery</CardTitle>
                    </div>
                    {getTestBadge(testResults?.model_discovery)}
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => runIndividualTest('model_discovery')}
                    disabled={activeTest === 'model_discovery'}
                    className="w-full"
                  >
                    {activeTest === 'model_discovery' ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      'Discover Models'
                    )}
                  </Button>
                  {testResults?.model_discovery && (
                    <div className="mt-2 text-xs text-muted-foreground">
                      <div>Duration: {formatDuration(testResults.model_discovery.duration_ms)}</div>
                      <div>Models: {testResults.model_discovery.details?.model_count || 0}</div>
                    </div>
                  )}
                </CardContent>
              </Card>
              
              {/* Capability Check */}
              <Card>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Settings className="h-4 w-4" />
                      <CardTitle className="text-sm">Capabilities</CardTitle>
                    </div>
                    {getTestBadge(testResults?.capability_check)}
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => runIndividualTest('capability_check')}
                    disabled={activeTest === 'capability_check'}
                    className="w-full"
                  >
                    {activeTest === 'capability_check' ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      'Check Capabilities'
                    )}
                  </Button>
                  {testResults?.capability_check && (
                    <div className="mt-2 text-xs text-muted-foreground">
                      <div>Duration: {formatDuration(testResults.capability_check.duration_ms)}</div>
                      <div>Features: {Object.keys(testResults.capability_check.details?.capabilities || {}).length}</div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
            
            {/* Performance Test */}
            {testResults?.performance_test && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Zap className="h-4 w-4" />
                    Performance Test Results
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center">
                      <div className="text-lg font-semibold">
                        {formatDuration(testResults.performance_test.duration_ms)}
                      </div>
                      <div className="text-xs text-muted-foreground">Response Time</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-semibold">
                        {testResults.performance_test.details?.tokens_per_second || 0}
                      </div>
                      <div className="text-xs text-muted-foreground">Tokens/sec</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-semibold">
                        {testResults.performance_test.details?.total_tokens || 0}
                      </div>
                      <div className="text-xs text-muted-foreground">Total Tokens</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-semibold">
                        {testResults.performance_test.success ? 'Pass' : 'Fail'}
                      </div>
                      <div className="text-xs text-muted-foreground">Status</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
            
            {/* Recommendations */}
            {testResults?.recommendations && testResults.recommendations.length > 0 && (
              <Alert>
                <Activity className="h-4 w-4" />
                <AlertTitle>Recommendations</AlertTitle>
                <AlertDescription>
                  <ul className="list-disc list-inside space-y-1 mt-2">
                    {testResults.recommendations.map((rec, index) => (
                      <li key={index} className="text-sm">{rec}</li>
                    ))}
                  </ul>
                </AlertDescription>
              </Alert>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}

export default ProviderTestingInterface;