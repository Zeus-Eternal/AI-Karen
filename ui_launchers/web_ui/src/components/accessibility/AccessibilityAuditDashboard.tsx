'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Alert, AlertDescription } from '../ui/alert';
import { 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  Info, 
  Play, 
  RefreshCw,
  Download,
  Eye,
  Keyboard,
  Volume2,
  Palette,
  Focus,
} from 'lucide-react';
import { useAccessibilityTesting } from '../../hooks/use-accessibility-testing';
import { cn } from '../../lib/utils';
import type { AccessibilityReport } from '../../lib/accessibility/accessibility-testing';

interface AccessibilityAuditDashboardProps {
  className?: string;
  autoRun?: boolean;
  showRecommendations?: boolean;
}

export function AccessibilityAuditDashboard({
  className,
  autoRun = false,
  showRecommendations = true,
}: AccessibilityAuditDashboardProps) {
  const containerRef = React.useRef<HTMLDivElement>(null);
  const [activeTab, setActiveTab] = useState('overview');
  
  const {
    report,
    isRunning,
    history,
    passes,
    score,
    runTest,
    runKeyboardTest,
    runScreenReaderTest,
    runColorContrastTest,
    runFullSuite,
  } = useAccessibilityTesting(containerRef, {
    autoTest: autoRun,
    testInterval: 30000,
    scoreThreshold: 80,
  });

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBadgeVariant = (score: number) => {
    if (score >= 90) return 'default';
    if (score >= 70) return 'secondary';
    return 'destructive';
  };

  const formatViolationImpact = (impact: string) => {
    const impactMap = {
      critical: { color: 'text-red-600', icon: XCircle },
      serious: { color: 'text-orange-600', icon: AlertTriangle },
      moderate: { color: 'text-yellow-600', icon: AlertTriangle },
      minor: { color: 'text-blue-600', icon: Info },
    };
    
    return impactMap[impact as keyof typeof impactMap] || impactMap.minor;
  };

  const exportReport = () => {
    if (!report) return;
    
    const reportData = {
      timestamp: new Date().toISOString(),
      score,
      passes,
      violations: report.violations,
      summary: report.summary,
      recommendations: report.recommendations,
    };
    
    const blob = new Blob([JSON.stringify(reportData, null, 2)], {
      type: 'application/json',
    });
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `accessibility-report-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div ref={containerRef} className={cn('space-y-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Accessibility Audit</h2>
          <p className="text-muted-foreground">
            Monitor and improve accessibility compliance
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => runTest('basic')}
            disabled={isRunning}
          >
            {isRunning ? (
              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Play className="h-4 w-4 mr-2" />
            )}
            Run Basic Test
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={runFullSuite}
            disabled={isRunning}
          >
            Run Full Suite
          </Button>
          
          {report && (
            <Button
              variant="outline"
              size="sm"
              onClick={exportReport}
            >
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
          )}
        </div>
      </div>

      {/* Score Overview */}
      {report && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Overall Score</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-2">
                <span className={cn('text-2xl font-bold', getScoreColor(score))}>
                  {score}
                </span>
                <Badge variant={getScoreBadgeVariant(score)}>
                  {passes ? 'PASS' : 'FAIL'}
                </Badge>
              </div>
              <Progress value={score} className="mt-2" />
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Violations</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-2">
                <span className="text-2xl font-bold text-red-600">
                  {report.summary.critical + report.summary.serious + report.summary.moderate + report.summary.minor}
                </span>
                <XCircle className="h-5 w-5 text-red-600" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Passes</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-2">
                <span className="text-2xl font-bold text-green-600">
                  {report.passed ? 'All' : '0'}
                </span>
                <CheckCircle className="h-5 w-5 text-green-600" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Test Duration</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-2">
                <span className="text-2xl font-bold">
                  {Math.round(report.testDuration)}ms
                </span>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Detailed Results */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="violations">Violations</TabsTrigger>
          <TabsTrigger value="keyboard">Keyboard</TabsTrigger>
          <TabsTrigger value="screen-reader">Screen Reader</TabsTrigger>
          <TabsTrigger value="contrast">Contrast</TabsTrigger>
        </TabsList>
        
        <TabsContent value="overview" className="space-y-4">
          {report ? (
            <div className="space-y-4">
              {/* Quick Actions */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Button
                  variant="outline"
                  className="h-auto p-4 flex flex-col items-center space-y-2"
                  onClick={runKeyboardTest}
                  disabled={isRunning}
                >
                  <Keyboard className="h-6 w-6" />
                  <span className="text-sm">Test Keyboard</span>
                </Button>
                
                <Button
                  variant="outline"
                  className="h-auto p-4 flex flex-col items-center space-y-2"
                  onClick={runScreenReaderTest}
                  disabled={isRunning}
                >
                  <Volume2 className="h-6 w-6" />
                  <span className="text-sm">Test Screen Reader</span>
                </Button>
                
                <Button
                  variant="outline"
                  className="h-auto p-4 flex flex-col items-center space-y-2"
                  onClick={runColorContrastTest}
                  disabled={isRunning}
                >
                  <Palette className="h-6 w-6" />
                  <span className="text-sm">Test Contrast</span>
                </Button>
                
                <Button
                  variant="outline"
                  className="h-auto p-4 flex flex-col items-center space-y-2"
                  onClick={() => runTest('comprehensive')}
                  disabled={isRunning}
                >
                  <Eye className="h-6 w-6" />
                  <span className="text-sm">Full Audit</span>
                </Button>
              </div>

              {/* Recommendations */}
              {showRecommendations && report.recommendations.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Recommendations</CardTitle>
                    <CardDescription>
                      Suggested improvements to enhance accessibility
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {report.recommendations.map((recommendation, index) => (
                        <Alert key={index}>
                          <Info className="h-4 w-4" />
                          <AlertDescription>{recommendation}</AlertDescription>
                        </Alert>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Eye className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Audit Results</h3>
                <p className="text-muted-foreground text-center mb-4">
                  Run an accessibility test to see detailed results and recommendations.
                </p>
                <Button onClick={() => runTest('basic')} disabled={isRunning}>
                  {isRunning ? (
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Play className="h-4 w-4 mr-2" />
                  )}
                  Run Basic Test
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>
        
        <TabsContent value="violations" className="space-y-4">
          {report && report.violations.length > 0 ? (
            <div className="space-y-4">
              {report.violations.map((violation, index) => {
                const { color, icon: Icon } = formatViolationImpact(violation.impact);
                
                return (
                  <Card key={index}>
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="flex items-center space-x-2">
                          <Icon className={cn('h-5 w-5', color)} />
                          <div>
                            <CardTitle className="text-base">
                              {violation.description}
                            </CardTitle>
                            <CardDescription>
                              Impact: {violation.impact} • {violation.elements.length} element(s) affected
                            </CardDescription>
                          </div>
                        </div>
                        <Badge variant="outline">{violation.impact}</Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div>
                          <h4 className="font-medium mb-2">How to fix:</h4>
                          <p className="text-sm text-muted-foreground">{violation.help}</p>
                        </div>
                        
                        <div>
                          <h4 className="font-medium mb-2">Affected elements:</h4>
                          <div className="space-y-2">
                            {violation.elements.slice(0, 3).map((element, elemIndex) => (
                              <div key={elemIndex} className="p-2 bg-muted rounded text-xs font-mono">
                                {Array.isArray(element.target) ? element.target.join(' ') : element.target}
                              </div>
                            ))}
                            {violation.elements.length > 3 && (
                              <p className="text-xs text-muted-foreground">
                                +{violation.elements.length - 3} more elements
                              </p>
                            )}
                          </div>
                        </div>
                        
                        <div>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => window.open(violation.helpUrl, '_blank')}
                          >
                            Learn More
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <CheckCircle className="h-12 w-12 text-green-600 mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Violations Found</h3>
                <p className="text-muted-foreground text-center">
                  Great job! No accessibility violations were detected.
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
        
        <TabsContent value="keyboard">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Keyboard className="h-5 w-5" />
                <span>Keyboard Accessibility</span>
              </CardTitle>
              <CardDescription>
                Test keyboard navigation and focus management
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button
                onClick={runKeyboardTest}
                disabled={isRunning}
                className="mb-4"
              >
                {isRunning ? (
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Keyboard className="h-4 w-4 mr-2" />
                )}
                Test Keyboard Navigation
              </Button>
              
              <div className="text-sm text-muted-foreground">
                <p>This test will check:</p>
                <ul className="list-disc list-inside mt-2 space-y-1">
                  <li>All interactive elements are keyboard accessible</li>
                  <li>Focus order is logical and predictable</li>
                  <li>Focus indicators are visible</li>
                  <li>Focus traps work correctly in modals</li>
                  <li>Skip links are properly implemented</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="screen-reader">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Volume2 className="h-5 w-5" />
                <span>Screen Reader Compatibility</span>
              </CardTitle>
              <CardDescription>
                Test screen reader accessibility and ARIA implementation
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button
                onClick={runScreenReaderTest}
                disabled={isRunning}
                className="mb-4"
              >
                {isRunning ? (
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Volume2 className="h-4 w-4 mr-2" />
                )}
                Test Screen Reader Support
              </Button>
              
              <div className="text-sm text-muted-foreground">
                <p>This test will check:</p>
                <ul className="list-disc list-inside mt-2 space-y-1">
                  <li>All form controls have proper labels</li>
                  <li>Images have appropriate alt text</li>
                  <li>ARIA attributes are used correctly</li>
                  <li>Landmark structure is properly implemented</li>
                  <li>Heading hierarchy is logical</li>
                  <li>Live regions work correctly</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="contrast">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Palette className="h-5 w-5" />
                <span>Color Contrast</span>
              </CardTitle>
              <CardDescription>
                Test color contrast ratios for WCAG compliance
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button
                onClick={runColorContrastTest}
                disabled={isRunning}
                className="mb-4"
              >
                {isRunning ? (
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Palette className="h-4 w-4 mr-2" />
                )}
                Test Color Contrast
              </Button>
              
              <div className="text-sm text-muted-foreground">
                <p>This test will check:</p>
                <ul className="list-disc list-inside mt-2 space-y-1">
                  <li>Text meets WCAG AA contrast requirements (4.5:1)</li>
                  <li>Large text meets minimum contrast (3:1)</li>
                  <li>Interactive elements have sufficient contrast</li>
                  <li>Focus indicators are clearly visible</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default AccessibilityAuditDashboard;