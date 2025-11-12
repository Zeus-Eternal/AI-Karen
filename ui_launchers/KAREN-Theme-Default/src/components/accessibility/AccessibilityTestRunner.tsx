"use client";

import React, { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Textarea } from "../ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import { Alert, AlertDescription } from "../ui/alert";
import {
  Settings,
  Code,
  RefreshCw,
  Play,
  Copy,
  Download,
  FileText,
  CheckCircle,
  XCircle,
} from "lucide-react";
import { useAccessibilityTestRunner } from "../../hooks/use-accessibility-testing";
import { cn } from "../../lib/utils";

type TestType = "basic" | "keyboard" | "screenReader" | "colorContrast";

interface AxeViolation {
  id?: string;
  impact?: string;
  description?: string;
  help?: string;
  helpUrl?: string;
  nodes?: Array<Record<string, unknown>>;
  elements?: Array<unknown>;
}

interface AxeSummary {
  passes?: number;
  violations?: number;
  incomplete?: number;
  inapplicable?: number;
}

type AccessibilityTestResult = {
  passed?: boolean;
  score?: number;
  violations?: AxeViolation[];
  summary?: AxeSummary;
  error?: string;
  [key: string]: unknown;
} | null;

interface AccessibilityTestRunnerProps {
  className?: string;
}

export function AccessibilityTestRunner({ className }: AccessibilityTestRunnerProps) {
  const [testType, setTestType] = useState<TestType>("basic");
  const [customHtml, setCustomHtml] = useState<string>("");
  const [testResults, setTestResults] = useState<AccessibilityTestResult>(null);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<"html" | "results">("html");

  const { runAccessibilityTest, runKeyboardTest, runScreenReaderTest, runColorContrastTest } =
    useAccessibilityTestRunner();

  const sampleHtml = `<div>
  <h1>Sample Page</h1>
  <form>
    <label for="name">Name:</label>
    <input type="text" id="name" required aria-label="Name input">
    <label for="email">Email:</label>
    <input type="email" id="email" required aria-label="Email input">
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
</div>`.trim();

  const getTestTypeDescription = (): string => {
    switch (testType) {
      case "basic":
        return "Comprehensive WCAG 2.1 AA compliance test using axe-core.";
      case "keyboard":
        return "Tests keyboard navigation, focus management, and tab order.";
      case "screenReader":
        return "Tests screen reader compatibility, ARIA usage, and semantic structure.";
      case "colorContrast":
        return "Tests color contrast ratios for text and interactive elements.";
      default:
        return "Select a test type to see description.";
    }
  };

  const runTest = async () => {
    if (!customHtml.trim()) {
      setCustomHtml(sampleHtml);
      return;
    }
    setIsRunning(true);
    setTestResults(null);

    const container = document.createElement("div");
    try {
      container.setAttribute("data-axe-scope", "true");
      container.innerHTML = customHtml;
      document.body.appendChild(container);

      let results: AccessibilityTestResult;
      switch (testType) {
        case "basic":
          results = (await runAccessibilityTest(container)) as AccessibilityTestResult;
          break;
        case "keyboard":
          results = (await runKeyboardTest(container)) as AccessibilityTestResult;
          break;
        case "screenReader":
          results = (await runScreenReaderTest(container)) as AccessibilityTestResult;
          break;
        case "colorContrast":
          results = (await runColorContrastTest(container)) as AccessibilityTestResult;
          break;
        default:
          results = (await runAccessibilityTest(container)) as AccessibilityTestResult;
      }
      setTestResults(results);
      setActiveTab("results");
    } catch (error) {
      setTestResults({
        error: error instanceof Error ? error.message : "Test failed",
      });
      setActiveTab("results");
    } finally {
      if (container.parentNode) {
        document.body.removeChild(container);
      }
      setIsRunning(false);
    }
  };

  const copyResults = () => {
    if (!testResults) return;
    void navigator.clipboard.writeText(JSON.stringify(testResults, null, 2));
  };

  const downloadResults = () => {
    if (!testResults) return;
    const blob = new Blob([JSON.stringify(testResults, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `accessibility-test-${testType}-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const renderResults = () => {
    if (!testResults) return null;

    if (testResults.error) {
      return (
        <Alert variant="destructive">
          <div className="flex items-start">
            <XCircle className="h-4 w-4 mt-0.5" />
            <AlertDescription className="ml-2">{testResults.error}</AlertDescription>
          </div>
        </Alert>
      );
    }

    if (testType === "basic") {
      return (
        <div className="space-y-4">
          {/* Summary */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4 md:p-6">
                <div className="flex items-center space-x-2">
                  {testResults.passed ? (
                    <CheckCircle className="h-5 w-5 text-green-600" />
                  ) : (
                    <XCircle className="h-5 w-5 text-red-600" />
                  )}
                  <span className="font-medium">{testResults.passed ? "PASS" : "FAIL"}</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4 md:p-6">
                <div className="text-center">
                  <div className="text-2xl font-bold">{testResults.score || 0}</div>
                  <div className="text-sm text-muted-foreground">Score</div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4 md:p-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-600">
                    {testResults.violations?.length || 0}
                  </div>
                  <div className="text-sm text-muted-foreground">Violations</div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4 md:p-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {testResults.summary?.passes || 0}
                  </div>
                  <div className="text-sm text-muted-foreground">Passes</div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Violations */}
          {Array.isArray(testResults.violations) && testResults.violations.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Violations</CardTitle>
                <CardDescription>Issues detected by the audit with impacted elements.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {testResults.violations?.map((violation: AxeViolation, index: number) => (
                    <div key={index} className="border-l-4 border-l-red-500 pl-4">
                      <div className="flex items-center space-x-2 mb-1">
                        <Badge variant="destructive">{violation.impact ?? "unknown"}</Badge>
                        <span className="font-medium">{violation.description ?? violation.id}</span>
                      </div>
                      {violation.help && (
                        <p className="text-sm text-muted-foreground mb-2">{violation.help}</p>
                      )}
                      <div className="text-xs text-muted-foreground">
                        {violation.elements?.length || violation.nodes?.length || 0} element(s) affected
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

    // For other test types, show a simplified result block
    return (
      <Card>
        <CardHeader>
          <CardTitle>Test Results</CardTitle>
          <CardDescription>Raw output for deep inspection.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-2 mb-4">
            {testResults.passed ? (
              <CheckCircle className="h-5 w-5 text-green-600" />
            ) : (
              <XCircle className="h-5 w-5 text-red-600" />
            )}
            <span className="font-medium">
              {testResults.passed ? "Test Passed" : "Test Failed"}
            </span>
          </div>
          <pre className="bg-muted p-4 rounded text-sm overflow-auto max-h-96">
            {JSON.stringify(testResults, null, 2)}
          </pre>
        </CardContent>
      </Card>
    );
  };

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold">Accessibility Test Runner</h2>
        <p className="text-muted-foreground">
          Run on-demand audits for WCAG, keyboard navigation, screen reader semantics, and color contrast.
        </p>
      </div>

      {/* Test Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Settings className="h-5 w-5" />
            <span>Test Configuration</span>
          </CardTitle>
          <CardDescription>Select a test type and provide HTML to evaluate.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Test Type</label>
            <Select value={testType} onValueChange={(v: TestType) => setTestType(v)}>
              <SelectTrigger aria-label="Select test type">
                <SelectValue placeholder="Select a test" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="basic">Basic Accessibility Test</SelectItem>
                <SelectItem value="keyboard">Keyboard Navigation Test</SelectItem>
                <SelectItem value="screenReader">Screen Reader Test</SelectItem>
                <SelectItem value="colorContrast">Color Contrast Test</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-sm text-muted-foreground">{getTestTypeDescription()}</p>
          </div>
        </CardContent>
      </Card>

      {/* HTML Input + Results */}
      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "html" | "results")}>
        <TabsList>
          <TabsTrigger value="html">HTML Input</TabsTrigger>
          <TabsTrigger value="results">Test Results</TabsTrigger>
        </TabsList>

        <TabsContent value="html" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Code className="h-5 w-5" />
                <span>HTML to Test</span>
              </CardTitle>
              <CardDescription>Paste or type the HTML you want to audit.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                value={customHtml}
                onChange={(e) => setCustomHtml(e.target.value)}
                placeholder="Enter HTML to test..."
                className="min-h-[300px] font-mono text-sm"
                aria-label="HTML input"
              />
              <div className="flex items-center gap-2">
                <Button onClick={runTest} disabled={isRunning} className="flex-1" aria-label="Run accessibility test">
                  {isRunning ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : <Play className="h-4 w-4 mr-2" />}
                  Run {testType.charAt(0).toUpperCase() + testType.slice(1)} Test
                </Button>
                <Button variant="outline" onClick={() => setCustomHtml(sampleHtml)} aria-label="Load sample HTML">
                  Load Sample
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="results" className="space-y-4">
          {testResults ? (
            <div className="space-y-4">
              {/* Results Actions */}
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm" onClick={copyResults} aria-label="Copy results to clipboard">
                  <Copy className="h-4 w-4 mr-2" />
                  Copy
                </Button>
                <Button variant="outline" size="sm" onClick={downloadResults} aria-label="Download results JSON">
                  <Download className="h-4 w-4 mr-2" />
                  Download
                </Button>
              </div>

              {/* Results Display */}
              {renderResults()}
            </div>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <FileText className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Results Yet</h3>
                <p className="text-muted-foreground text-center mb-4">
                  Run a test to see the results here.
                </p>
                <Button onClick={() => setActiveTab("html")} aria-label="Go to HTML input">
                  Go to HTML
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
