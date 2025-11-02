"use client";

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Textarea } from '../ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Alert, AlertDescription } from '../ui/alert';

import { } from 'lucide-react';
import { useAccessibilityTestRunner } from '../../hooks/use-accessibility-testing';
import { cn } from '../../lib/utils';
interface AccessibilityTestRunnerProps {
  className?: string;
}
export function AccessibilityTestRunner({ className }: AccessibilityTestRunnerProps) {
  const [testType, setTestType] = useState<'basic' | 'keyboard' | 'screenReader' | 'colorContrast'>('basic');
  const [customHtml, setCustomHtml] = useState('');
  const [testResults, setTestResults] = useState<any>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [activeTab, setActiveTab] = useState('html');
  const {
    runAccessibilityTest,
    runKeyboardTest,
    runScreenReaderTest,
    runColorContrastTest,
  } = useAccessibilityTestRunner();
  const sampleHtml = `<div>
  <h1>Sample Page</h1>
  <form>
    <label for="name">Name:</label>
    <input type="text" id="name" required aria-label="Input">
    <label for="email">Email:</label>
    <input type="email" id="email" required aria-label="Input">
    <button type="submit" aria-label="Submit form">Submit</button>
  </form>
  <img src="example.jpg" alt="Example image">
  <nav aria-label="Main navigation">
    <ul>
      <li><a href="#home">Home</a></li>
      <li><a href="#about">About</a></li>
      <li><a href="#contact">Contact</a></li>
    </ul>
  </nav>
</div>`;
  const runTest = async () => {
    if (!customHtml.trim()) {
      setCustomHtml(sampleHtml);
      return;
    }
    setIsRunning(true);
    setTestResults(null);
    try {
      // Create a temporary container with the HTML
      const container = document.createElement('div');
      container.innerHTML = customHtml;
      document.body.appendChild(container);
      let results;
      switch (testType) {
        case 'basic':
          results = await runAccessibilityTest(container);
          break;
        case 'keyboard':
          results = await runKeyboardTest(container);
          break;
        case 'screenReader':
          results = await runScreenReaderTest(container);
          break;
        case 'colorContrast':
          results = await runColorContrastTest(container);
          break;
        default:
          results = await runAccessibilityTest(container);
      }
      setTestResults(results);
      // Clean up
      document.body.removeChild(container);
    } catch (error) {
      setTestResults({
        error: error instanceof Error ? error.message : 'Test failed',

    } finally {
      setIsRunning(false);
    }
  };
  const copyResults = () => {
    if (testResults) {
      navigator.clipboard.writeText(JSON.stringify(testResults, null, 2));
    }
  };
  const downloadResults = () => {
    if (testResults) {
      const blob = new Blob([JSON.stringify(testResults, null, 2)], {
        type: 'application/json',

      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `accessibility-test-${testType}-${Date.now()}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  };
  const getTestTypeDescription = () => {
    switch (testType) {
      case 'basic':
        return 'Comprehensive WCAG 2.1 AA compliance test using axe-core';
      case 'keyboard':
        return 'Test keyboard navigation, focus management, and tab order';
      case 'screenReader':
        return 'Test screen reader compatibility, ARIA usage, and semantic structure';
      case 'colorContrast':
        return 'Test color contrast ratios for text and interactive elements';
      default:
        return 'Select a test type to see description';
    }
  };
  const renderResults = () => {
    if (!testResults) return null;
    if (testResults.error) {
      return (
        <Alert variant="destructive">
          <XCircle className="h-4 w-4 " />
          <AlertDescription>{testResults.error}</AlertDescription>
        </Alert>
      );
    }
    if (testType === 'basic') {
      return (
        <div className="space-y-4">
          {/* Summary */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4 sm:p-4 md:p-6">
                <div className="flex items-center space-x-2">
                  {testResults.passed ? (
                    <CheckCircle className="h-5 w-5 text-green-600 " />
                  ) : (
                    <XCircle className="h-5 w-5 text-red-600 " />
                  )}
                  <span className="font-medium">
                    {testResults.passed ? 'PASS' : 'FAIL'}
                  </span>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 sm:p-4 md:p-6">
                <div className="text-center">
                  <div className="text-2xl font-bold">{testResults.score || 0}</div>
                  <div className="text-sm text-muted-foreground md:text-base lg:text-lg">Score</div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 sm:p-4 md:p-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-600">
                    {testResults.violations?.length || 0}
                  </div>
                  <div className="text-sm text-muted-foreground md:text-base lg:text-lg">Violations</div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 sm:p-4 md:p-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {testResults.summary?.passes || 0}
                  </div>
                  <div className="text-sm text-muted-foreground md:text-base lg:text-lg">Passes</div>
                </div>
              </CardContent>
            </Card>
          </div>
          {/* Violations */}
          {testResults.violations && testResults.violations.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Violations</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {testResults.violations.map((violation: any, index: number) => (
                    <div key={index} className="border-l-4 border-l-red-500 pl-4">
                      <div className="flex items-center space-x-2 mb-1">
                        <Badge variant="destructive">{violation.impact}</Badge>
                        <span className="font-medium">{violation.description}</span>
                      </div>
                      <p className="text-sm text-muted-foreground mb-2 md:text-base lg:text-lg">
                        {violation.help}
                      </p>
                      <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
                        {violation.elements?.length || 0} element(s) affected
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      );
    }
    // For other test types, show a simplified result
    return (
      <Card>
        <CardHeader>
          <CardTitle>Test Results</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-2 mb-4">
            {testResults.passed ? (
              <CheckCircle className="h-5 w-5 text-green-600 " />
            ) : (
              <XCircle className="h-5 w-5 text-red-600 " />
            )}
            <span className="font-medium">
              {testResults.passed ? 'Test Passed' : 'Test Failed'}
            </span>
          </div>
          <pre className="bg-muted p-4 rounded text-sm overflow-auto max-h-96 md:text-base lg:text-lg">
            {JSON.stringify(testResults, null, 2)}
          </pre>
        </CardContent>
      </Card>
    );
  };
  return (
    <div className={cn('space-y-6', className)}>
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold">Accessibility Test Runner</h2>
        <p className="text-muted-foreground">
        </p>
      </div>
      {/* Test Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Settings className="h-5 w-5 " />
            <span>Test Configuration</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium md:text-base lg:text-lg">Test Type</label>
            <select value={testType} onValueChange={(value: any) = aria-label="Select option"> setTestType(value)}>
              <selectTrigger aria-label="Select option">
                <selectValue />
              </SelectTrigger>
              <selectContent aria-label="Select option">
                <selectItem value="basic" aria-label="Select option">Basic Accessibility Test</SelectItem>
                <selectItem value="keyboard" aria-label="Select option">Keyboard Navigation Test</SelectItem>
                <selectItem value="screenReader" aria-label="Select option">Screen Reader Test</SelectItem>
                <selectItem value="colorContrast" aria-label="Select option">Color Contrast Test</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
              {getTestTypeDescription()}
            </p>
          </div>
        </CardContent>
      </Card>
      {/* HTML Input */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="html">HTML Input</TabsTrigger>
          <TabsTrigger value="results">Test Results</TabsTrigger>
        </TabsList>
        <TabsContent value="html" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Code className="h-5 w-5 " />
                <span>HTML to Test</span>
              </CardTitle>
              <CardDescription>
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <textarea
                value={customHtml}
                onChange={(e) => setCustomHtml(e.target.value)}
                placeholder="Enter HTML to test..."
                className="min-h-[300px] font-mono text-sm md:text-base lg:text-lg"
              />
              <div className="flex items-center space-x-2">
                <button
                  onClick={runTest}
                  disabled={isRunning}
                  className="flex-1"
                 aria-label="Button">
                  {isRunning ? (
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin " />
                  ) : (
                    <Play className="h-4 w-4 mr-2 " />
                  )}
                  Run {testType.charAt(0).toUpperCase() + testType.slice(1)} Test
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setCustomHtml(sampleHtml)}
                >
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="results" className="space-y-4">
          {testResults ? (
            <div className="space-y-4">
              {/* Results Actions */}
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={copyResults}
                 >
                  <Copy className="h-4 w-4 mr-2 " />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={downloadResults}
                 >
                  <Download className="h-4 w-4 mr-2 " />
                </Button>
              </div>
              {/* Results Display */}
              {renderResults()}
            </div>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <FileText className="h-12 w-12 text-muted-foreground mb-4 " />
                <h3 className="text-lg font-semibold mb-2">No Results Yet</h3>
                <p className="text-muted-foreground text-center mb-4">
                  Run a test to see the results here.
                </p>
                <Button onClick={() => setActiveTab('html')}>
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
export default AccessibilityTestRunner;
