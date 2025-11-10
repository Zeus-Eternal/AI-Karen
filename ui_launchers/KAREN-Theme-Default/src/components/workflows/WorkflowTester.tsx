
"use client";
import * as React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Alert, AlertDescription } from '@/components/ui/alert';

import { AlertCircle, CheckCircle, Clock, Download, Eye, Play, RotateCcw, Square } from 'lucide-react';

import { NodePort, WorkflowDefinition, WorkflowTestResult } from '@/types/workflows';

export interface WorkflowTesterProps {
  workflow: WorkflowDefinition;
  onTest?: (workflow: WorkflowDefinition, testData: Record<string, unknown>) => Promise<WorkflowTestResult>;
  className?: string;
}

interface TestInput {
  nodeId: string;
  inputId: string;
  name: string;
  type: NodePort['type'];
  value: unknown;
  required: boolean;
}

export function WorkflowTester({ workflow, onTest, className = '' }: WorkflowTesterProps) {
  const [testInputs, setTestInputs] = React.useState<Record<string, unknown>>({});
  const [testResult, setTestResult] = React.useState<WorkflowTestResult | null>(null);
  const [isRunning, setIsRunning] = React.useState(false);
  const [selectedStep, setSelectedStep] = React.useState<string | null>(null);

  // Extract input nodes and their required inputs
  const inputNodes = workflow.nodes.filter((node) =>
    node.type === 'input' ||
    (node.data.inputs && node.data.inputs.some((input) => input.required))
  );

  const testInputFields: TestInput[] = inputNodes.flatMap((node) =>
    (node.data.inputs ?? [])
      .filter((input) => input.required || node.type === 'input')
      .map((input) => {
        const key = `${node.id}.${input.id}`;
        const existingValue = testInputs[key] ?? (input.type === 'boolean' ? false : '');
        return {
          nodeId: node.id,
          inputId: input.id,
          name: `${node.data.label} - ${input.name}`,
          type: input.type,
          value: existingValue,
          required: input.required || node.type === 'input',
        };
      })
  );

  const handleInputChange = React.useCallback((nodeId: string, inputId: string, value: unknown) => {
    setTestInputs(prev => ({
      ...prev,
      [`${nodeId}.${inputId}`]: value
    }));
  }, []);

  const handleRunTest = React.useCallback(async () => {
    if (!onTest) return;

    setIsRunning(true);
    setTestResult(null);
    
    try {
      const result = await onTest(workflow, testInputs);
      setTestResult(result);
    } catch (error) {
      setTestResult({
        success: false,
        duration: 0,
        nodeResults: {},
        logs: [{
          id: 'error',
          timestamp: new Date(),
          level: 'error',
          message: error instanceof Error ? error.message : 'Unknown error occurred'
        }],
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      });
    } finally {
      setIsRunning(false);
    }
  }, [workflow, testInputs, onTest]);

  const handleStopTest = React.useCallback(() => {
    setIsRunning(false);
    // In a real implementation, this would cancel the running test
  }, []);

  const handleResetTest = React.useCallback(() => {
    setTestInputs({});
    setTestResult(null);
    setSelectedStep(null);
  }, []);

  const renderInputField = (input: TestInput) => {
    switch (input.type) {
      case 'string':
        return (
          <Textarea
            value={typeof input.value === 'string' ? input.value : String(input.value ?? '')}
            onChange={(event: React.ChangeEvent<HTMLTextAreaElement>) =>
              handleInputChange(input.nodeId, input.inputId, event.target.value)
            }
            placeholder={`Enter ${input.name.toLowerCase()}...`}
            className="min-h-[80px]"
          />
        );

      case 'number':
        return (
          <Input
            type="number"
            value={typeof input.value === 'number' ? input.value : Number(input.value) || 0}
            onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
              handleInputChange(input.nodeId, input.inputId, Number(event.target.value))
            }
            placeholder="0"
          />
        );

      case 'boolean':
        return (
          <select
            value={(Boolean(input.value)).toString()}
            onChange={(event: React.ChangeEvent<HTMLSelectElement>) =>
              handleInputChange(input.nodeId, input.inputId, event.target.value === 'true')
            }
            className="w-full p-2 border border-input rounded-md sm:p-4 md:p-6"
          >
            <option value="false">False</option>
            <option value="true">True</option>
          </select>
        );

      case 'object':
      case 'array':
        return (
          <Textarea
            value={typeof input.value === 'string' ? input.value : JSON.stringify(input.value, null, 2)}
            onChange={(event: React.ChangeEvent<HTMLTextAreaElement>) => {
              try {
                const parsed = JSON.parse(event.target.value);
                handleInputChange(input.nodeId, input.inputId, parsed);
              } catch {
                handleInputChange(input.nodeId, input.inputId, event.target.value);
              }
            }}
            placeholder={input.type === 'array' ? '[]' : '{}'}
            className="min-h-[100px] font-mono text-sm md:text-base lg:text-lg"
          />
        );

      default:
        return (
          <Input
            value={typeof input.value === 'string' ? input.value : String(input.value ?? '')}
            onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
              handleInputChange(input.nodeId, input.inputId, event.target.value)
            }
            placeholder={`Enter ${input.name.toLowerCase()}...`}
          />
        );
    }
  };

  const getLogLevelColor = (level: WorkflowTestResult['logs'][number]['level']) => {
    switch (level) {
      case 'error': return 'text-red-600 bg-red-50';
      case 'warn': return 'text-yellow-600 bg-yellow-50';
      case 'info': return 'text-blue-600 bg-blue-50';
      case 'debug': return 'text-gray-600 bg-gray-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const exportTestResults = React.useCallback(() => {
    if (!testResult) return;

    const exportData = {
      workflow: {
        id: workflow.id,
        name: workflow.name,
        version: workflow.version
      },
      testInputs,
      testResult,
      timestamp: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `workflow-test-${workflow.name}-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [workflow, testInputs, testResult]);

  return (
    <div className={`grid grid-cols-1 lg:grid-cols-2 gap-6 h-full ${className}`}>
      {/* Test Configuration */}
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleResetTest}
                  disabled={isRunning}
                 >
                  <RotateCcw className="h-4 w-4 mr-2 " />
                </Button>
                {isRunning ? (
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={handleStopTest}
                   >
                    <Square className="h-4 w-4 mr-2 " />
                  </Button>
                ) : (
                  <Button
                    size="sm"
                    onClick={handleRunTest}
                    disabled={!onTest}
                   aria-label="Button">
                    <Play className="h-4 w-4 mr-2 " />
                  </Button>
                )}
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {testInputFields.length === 0 ? (
              <Alert>
                <AlertCircle className="h-4 w-4 " />
                <AlertDescription>
                  No test inputs required. This workflow can be tested without input data.
                </AlertDescription>
              </Alert>
            ) : (
              <div className="space-y-4">
                {testInputFields.map((input) => (
                  <div key={`${input.nodeId}.${input.inputId}`} className="space-y-2">
                    <Label className="flex items-center gap-2">
                      {input.name}
                      <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                        {input.type}
                      </Badge>
                      {input.required && (
                        <span className="text-red-500 text-xs sm:text-sm md:text-base">*</span>
                      )}
                    </Label>
                    {renderInputField(input)}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Test Status */}
        {(isRunning || testResult) && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {isRunning ? (
                  <>
                    <Clock className="h-4 w-4 animate-spin " />
                    Running Test...
                  </>
                ) : testResult?.success ? (
                  <>
                    <CheckCircle className="h-4 w-4 text-green-600 " />
                  </>
                ) : (
                  <>
                    <AlertCircle className="h-4 w-4 text-red-600 " />
                  </>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {testResult && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm md:text-base lg:text-lg">
                    <span>Duration:</span>
                    <span>{testResult.duration}ms</span>
                  </div>
                  <div className="flex justify-between text-sm md:text-base lg:text-lg">
                    <span>Status:</span>
                    <Badge variant={testResult.success ? 'default' : 'destructive'}>
                      {testResult.success ? 'Success' : 'Failed'}
                    </Badge>
                  </div>
                  {testResult.error && (
                    <Alert variant="destructive">
                      <AlertCircle className="h-4 w-4 " />
                      <AlertDescription>{testResult.error}</AlertDescription>
                    </Alert>
                  )}
                  <div className="flex gap-2 pt-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={exportTestResults}
                     >
                      <Download className="h-4 w-4 mr-2 " />
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>

      {/* Test Results */}
      <div className="space-y-6">
        {/* Execution Logs */}
        {testResult && testResult.logs.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Execution Logs</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[300px]">
                <div className="space-y-2">
                  {testResult.logs.map((log, index) => (
                    <div
                      key={log.id || index}
                      className={`p-2 rounded text-sm ${getLogLevelColor(log.level)}`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                          {log.level.toUpperCase()}
                        </Badge>
                        <span className="text-xs opacity-75 sm:text-sm md:text-base">
                          {log.timestamp.toLocaleTimeString()}
                        </span>
                      </div>
                      <p>{log.message}</p>
                      {log.nodeId && (
                        <p className="text-xs opacity-75 mt-1 sm:text-sm md:text-base">Node: {log.nodeId}</p>
                      )}
                      {log.data && (
                        <details className="mt-2">
                          <summary className="text-xs cursor-pointer sm:text-sm md:text-base">View Data</summary>
                          <pre className="text-xs mt-1 p-2 bg-black/5 rounded overflow-auto sm:text-sm md:text-base">
                            {JSON.stringify(log.data, null, 2)}
                          </pre>
                        </details>
                      )}
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        )}

        {/* Node Results */}
        {testResult && Object.keys(testResult.nodeResults).length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Node Results</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[400px]">
                <div className="space-y-4">
                  {Object.entries(testResult.nodeResults).map(([nodeId, result]) => {
                    const node = workflow.nodes.find(n => n.id === nodeId);
                    return (
                      <div key={nodeId} className="border rounded p-3 sm:p-4 md:p-6">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-medium text-sm md:text-base lg:text-lg">
                            {node?.data.label || nodeId}
                          </h4>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setSelectedStep(selectedStep === nodeId ? null : nodeId)}
                          >
                            <Eye className="h-4 w-4 " />
                          </Button>
                        </div>
                        
                        {selectedStep === nodeId && (
                          <div className="mt-2 p-2 bg-muted rounded sm:p-4 md:p-6">
                            <pre className="text-xs overflow-auto sm:text-sm md:text-base">
                              {JSON.stringify(result, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        )}

        {/* No Results Message */}
        {!isRunning && !testResult && (
          <Card>
            <CardContent className="flex items-center justify-center h-[200px] text-muted-foreground">
              <div className="text-center">
                <Play className="h-8 w-8 mx-auto mb-2 opacity-50 " />
                <p>Run a test to see results here</p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}