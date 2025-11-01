/**
 * Accessibility User Testing Tool
 * 
 * Provides tools for accessibility validation with assistive technology simulation,
 * user testing scenarios, and accessibility evaluation workflows.
 */

'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Eye, 
  EyeOff, 
  Keyboard, 
  Volume2, 
  VolumeX, 
  MousePointer, 
  Smartphone,
  Monitor,
  Tablet,
  Play,
  Pause,
  RotateCcw,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Info,
  Download,
  Upload,
  Settings,
  User,
  Clock,
  Target
} from 'lucide-react';

// Types for testing scenarios and results
interface TestingScenario {
  id: string;
  name: string;
  description: string;
  category: 'keyboard' | 'screen-reader' | 'visual' | 'cognitive' | 'motor';
  difficulty: 'easy' | 'medium' | 'hard';
  estimatedTime: number; // in minutes
  instructions: string[];
  successCriteria: string[];
  commonIssues: string[];
}

interface TestResult {
  scenarioId: string;
  userId: string;
  startTime: Date;
  endTime?: Date;
  status: 'not-started' | 'in-progress' | 'completed' | 'failed';
  success: boolean;
  timeSpent: number; // in seconds
  issues: TestIssue[];
  feedback: string;
  assistiveTechnology?: string;
  deviceType: string;
  browserInfo: string;
}

interface TestIssue {
  id: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  category: string;
  description: string;
  location: string;
  reproduction: string;
  suggestion: string;
}

interface SimulationSettings {
  visualImpairment: {
    enabled: boolean;
    type: 'none' | 'low-vision' | 'color-blind' | 'blind';
    severity: number; // 0-100
  };
  motorImpairment: {
    enabled: boolean;
    type: 'none' | 'limited-mobility' | 'tremor' | 'one-hand';
    keyboardOnly: boolean;
  };
  cognitiveImpairment: {
    enabled: boolean;
    type: 'none' | 'attention' | 'memory' | 'processing';
    reducedMotion: boolean;
  };
  screenReader: {
    enabled: boolean;
    type: 'nvda' | 'jaws' | 'voiceover' | 'talkback';
    speechRate: number; // 0-100
    verbosity: 'low' | 'medium' | 'high';
  };
}

interface AccessibilityUserTestingToolProps {
  className?: string;
  onTestComplete?: (result: TestResult) => void;
  onIssueReported?: (issue: TestIssue) => void;
}

export function AccessibilityUserTestingTool({ 
  className, 
  onTestComplete, 
  onIssueReported 
}: AccessibilityUserTestingToolProps) {
  const [currentScenario, setCurrentScenario] = useState<TestingScenario | null>(null);
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [simulationSettings, setSimulationSettings] = useState<SimulationSettings>({
    visualImpairment: { enabled: false, type: 'none', severity: 0 },
    motorImpairment: { enabled: false, type: 'none', keyboardOnly: false },
    cognitiveImpairment: { enabled: false, type: 'none', reducedMotion: false },
    screenReader: { enabled: false, type: 'nvda', speechRate: 50, verbosity: 'medium' }
  });
  const [currentTest, setCurrentTest] = useState<TestResult | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [newIssue, setNewIssue] = useState<Partial<TestIssue>>({});
  const [showIssueForm, setShowIssueForm] = useState(false);

  const timerRef = useRef<NodeJS.Timeout>();
  const startTimeRef = useRef<Date>();

  // Predefined testing scenarios
  const testingScenarios: TestingScenario[] = [
    {
      id: 'keyboard-navigation',
      name: 'Keyboard Navigation',
      description: 'Navigate the entire interface using only keyboard',
      category: 'keyboard',
      difficulty: 'easy',
      estimatedTime: 10,
      instructions: [
        'Disconnect or ignore your mouse/trackpad',
        'Use Tab to navigate forward through interactive elements',
        'Use Shift+Tab to navigate backward',
        'Use Enter or Space to activate buttons',
        'Use arrow keys for menus and complex widgets',
        'Try to complete a common user task'
      ],
      successCriteria: [
        'All interactive elements are reachable via keyboard',
        'Focus indicators are clearly visible',
        'Tab order is logical and intuitive',
        'No keyboard traps exist',
        'All functionality is accessible via keyboard'
      ],
      commonIssues: [
        'Missing focus indicators',
        'Illogical tab order',
        'Keyboard traps in modals or widgets',
        'Inaccessible dropdown menus',
        'Missing keyboard shortcuts'
      ]
    },
    {
      id: 'screen-reader-navigation',
      name: 'Screen Reader Navigation',
      description: 'Navigate using screen reader software',
      category: 'screen-reader',
      difficulty: 'medium',
      estimatedTime: 15,
      instructions: [
        'Turn on screen reader (NVDA, JAWS, VoiceOver, etc.)',
        'Close your eyes or turn off monitor',
        'Navigate using screen reader commands',
        'Listen to how content is announced',
        'Try to complete a user task using only audio feedback'
      ],
      successCriteria: [
        'All content is announced clearly',
        'Headings create logical structure',
        'Form controls have proper labels',
        'Images have meaningful alt text',
        'Dynamic content changes are announced'
      ],
      commonIssues: [
        'Missing or poor alt text',
        'Unlabeled form controls',
        'Poor heading structure',
        'Missing live regions',
        'Confusing link text'
      ]
    },
    {
      id: 'visual-impairment-simulation',
      name: 'Visual Impairment Simulation',
      description: 'Test with simulated visual impairments',
      category: 'visual',
      difficulty: 'medium',
      estimatedTime: 12,
      instructions: [
        'Enable visual impairment simulation',
        'Try different types: low vision, color blindness, etc.',
        'Increase browser zoom to 200%',
        'Test in high contrast mode',
        'Navigate and complete tasks with impaired vision'
      ],
      successCriteria: [
        'Content is readable at high zoom levels',
        'Color is not the only way to convey information',
        'Sufficient color contrast exists',
        'Text and UI elements remain usable',
        'High contrast mode works properly'
      ],
      commonIssues: [
        'Poor color contrast',
        'Information conveyed by color alone',
        'Text becomes unreadable when zoomed',
        'UI elements overlap at high zoom',
        'Poor high contrast support'
      ]
    },
    {
      id: 'motor-impairment-simulation',
      name: 'Motor Impairment Simulation',
      description: 'Test with simulated motor impairments',
      category: 'motor',
      difficulty: 'hard',
      estimatedTime: 15,
      instructions: [
        'Enable motor impairment simulation',
        'Try using only one hand',
        'Simulate tremor or limited precision',
        'Use keyboard-only navigation',
        'Test with larger touch targets on mobile'
      ],
      successCriteria: [
        'All functionality works with one hand',
        'Touch targets are large enough (44px minimum)',
        'No precise mouse movements required',
        'Keyboard alternatives exist for all actions',
        'Drag and drop has keyboard alternatives'
      ],
      commonIssues: [
        'Small touch targets',
        'Required precise mouse movements',
        'No keyboard alternatives for drag/drop',
        'Time-sensitive interactions',
        'Complex gesture requirements'
      ]
    },
    {
      id: 'cognitive-load-test',
      name: 'Cognitive Load Test',
      description: 'Test cognitive accessibility and usability',
      category: 'cognitive',
      difficulty: 'medium',
      estimatedTime: 20,
      instructions: [
        'Enable reduced motion preferences',
        'Test with distractions (background noise, etc.)',
        'Try to complete complex multi-step tasks',
        'Look for clear instructions and feedback',
        'Test error recovery and help systems'
      ],
      successCriteria: [
        'Clear, simple language is used',
        'Instructions are easy to follow',
        'Error messages are helpful',
        'Progress indicators show task completion',
        'Help and documentation are accessible'
      ],
      commonIssues: [
        'Complex or jargon-heavy language',
        'Unclear instructions',
        'Poor error messages',
        'Overwhelming interfaces',
        'Missing progress indicators'
      ]
    }
  ];

  // Start a test scenario
  const startTest = (scenario: TestingScenario) => {
    const testResult: TestResult = {
      scenarioId: scenario.id,
      userId: 'current-user', // In real app, get from auth
      startTime: new Date(),
      status: 'in-progress',
      success: false,
      timeSpent: 0,
      issues: [],
      feedback: '',
      deviceType: getDeviceType(),
      browserInfo: getBrowserInfo()
    };

    setCurrentScenario(scenario);
    setCurrentTest(testResult);
    setIsRecording(true);
    startTimeRef.current = new Date();

    // Start timer
    timerRef.current = setInterval(() => {
      if (startTimeRef.current) {
        const elapsed = Math.floor((Date.now() - startTimeRef.current.getTime()) / 1000);
        setCurrentTest(prev => prev ? { ...prev, timeSpent: elapsed } : null);
      }
    }, 1000);
  };

  // Complete current test
  const completeTest = (success: boolean, feedback: string = '') => {
    if (!currentTest || !currentScenario) return;

    const completedTest: TestResult = {
      ...currentTest,
      endTime: new Date(),
      status: success ? 'completed' : 'failed',
      success,
      feedback,
      assistiveTechnology: simulationSettings.screenReader.enabled 
        ? simulationSettings.screenReader.type 
        : undefined
    };

    setTestResults(prev => [...prev, completedTest]);
    setCurrentTest(null);
    setCurrentScenario(null);
    setIsRecording(false);

    if (timerRef.current) {
      clearInterval(timerRef.current);
    }

    onTestComplete?.(completedTest);
  };

  // Report an issue during testing
  const reportIssue = (issue: Partial<TestIssue>) => {
    const fullIssue: TestIssue = {
      id: Date.now().toString(),
      severity: issue.severity || 'medium',
      category: issue.category || 'general',
      description: issue.description || '',
      location: issue.location || window.location.pathname,
      reproduction: issue.reproduction || '',
      suggestion: issue.suggestion || ''
    };

    if (currentTest) {
      setCurrentTest(prev => prev ? {
        ...prev,
        issues: [...prev.issues, fullIssue]
      } : null);
    }

    onIssueReported?.(fullIssue);
    setNewIssue({});
    setShowIssueForm(false);
  };

  // Apply simulation settings
  const applySimulation = () => {
    const body = document.body;
    
    // Visual impairment simulation
    if (simulationSettings.visualImpairment.enabled) {
      body.classList.add('visual-impairment-simulation');
      body.setAttribute('data-visual-type', simulationSettings.visualImpairment.type);
      body.style.setProperty('--visual-severity', simulationSettings.visualImpairment.severity.toString());
    } else {
      body.classList.remove('visual-impairment-simulation');
    }

    // Motor impairment simulation
    if (simulationSettings.motorImpairment.enabled) {
      body.classList.add('motor-impairment-simulation');
      body.setAttribute('data-motor-type', simulationSettings.motorImpairment.type);
    } else {
      body.classList.remove('motor-impairment-simulation');
    }

    // Cognitive impairment simulation
    if (simulationSettings.cognitiveImpairment.enabled) {
      body.classList.add('cognitive-impairment-simulation');
      if (simulationSettings.cognitiveImpairment.reducedMotion) {
        body.style.setProperty('--motion-preference', 'reduce');
      }
    } else {
      body.classList.remove('cognitive-impairment-simulation');
    }
  };

  // Helper functions
  const getDeviceType = (): string => {
    const width = window.innerWidth;
    if (width < 768) return 'mobile';
    if (width < 1024) return 'tablet';
    return 'desktop';
  };

  const getBrowserInfo = (): string => {
    return navigator.userAgent;
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'destructive';
      case 'high': return 'destructive';
      case 'medium': return 'secondary';
      case 'low': return 'outline';
      default: return 'outline';
    }
  };

  // Apply simulation settings when they change
  useEffect(() => {
    applySimulation();
  }, [simulationSettings]);

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Accessibility User Testing</h1>
          <p className="text-muted-foreground">
            Test your application with simulated assistive technologies and accessibility scenarios
          </p>
        </div>
        <div className="flex gap-2">
          {isRecording && (
            <Badge variant="destructive" className="animate-pulse">
              <div className="w-2 h-2 bg-red-500 rounded-full mr-2" />
              Recording
            </Badge>
          )}
          <Button
            onClick={() => setShowIssueForm(true)}
            variant="outline"
            disabled={!isRecording}
          >
            <AlertTriangle className="h-4 w-4 mr-2" />
            Report Issue
          </Button>
        </div>
      </div>

      {/* Current Test Status */}
      {currentTest && currentScenario && (
        <Alert>
          <Play className="h-4 w-4" />
          <AlertTitle>Test in Progress: {currentScenario.name}</AlertTitle>
          <AlertDescription>
            <div className="flex items-center gap-4 mt-2">
              <span>Time: {formatTime(currentTest.timeSpent)}</span>
              <span>Issues: {currentTest.issues.length}</span>
              <div className="flex gap-2 ml-auto">
                <Button
                  size="sm"
                  onClick={() => completeTest(true, 'Test completed successfully')}
                  variant="outline"
                >
                  <CheckCircle className="h-4 w-4 mr-1" />
                  Pass
                </Button>
                <Button
                  size="sm"
                  onClick={() => completeTest(false, 'Test failed or abandoned')}
                  variant="outline"
                >
                  <XCircle className="h-4 w-4 mr-1" />
                  Fail
                </Button>
              </div>
            </div>
          </AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="scenarios" className="space-y-4">
        <TabsList>
          <TabsTrigger value="scenarios">Test Scenarios</TabsTrigger>
          <TabsTrigger value="simulation">Simulation Settings</TabsTrigger>
          <TabsTrigger value="results">Test Results</TabsTrigger>
          <TabsTrigger value="issues">Issues</TabsTrigger>
        </TabsList>

        <TabsContent value="scenarios" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {testingScenarios.map((scenario) => (
              <Card key={scenario.id} className="relative">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{scenario.name}</CardTitle>
                    <Badge variant={
                      scenario.difficulty === 'easy' ? 'outline' :
                      scenario.difficulty === 'medium' ? 'secondary' : 'destructive'
                    }>
                      {scenario.difficulty}
                    </Badge>
                  </div>
                  <CardDescription>{scenario.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Clock className="h-4 w-4" />
                      <span>~{scenario.estimatedTime} minutes</span>
                    </div>
                    
                    <div className="space-y-2">
                      <h4 className="font-medium text-sm">Instructions:</h4>
                      <ul className="text-xs space-y-1">
                        {scenario.instructions.slice(0, 3).map((instruction, index) => (
                          <li key={index} className="flex items-start gap-2">
                            <span className="text-muted-foreground">•</span>
                            <span>{instruction}</span>
                          </li>
                        ))}
                        {scenario.instructions.length > 3 && (
                          <li className="text-muted-foreground">
                            +{scenario.instructions.length - 3} more steps...
                          </li>
                        )}
                      </ul>
                    </div>

                    <Button
                      onClick={() => startTest(scenario)}
                      disabled={isRecording}
                      className="w-full"
                    >
                      <Play className="h-4 w-4 mr-2" />
                      Start Test
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="simulation" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Visual Impairment Simulation */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Eye className="h-5 w-5" />
                  Visual Impairment
                </CardTitle>
                <CardDescription>
                  Simulate various visual impairments and conditions
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="visual-enabled"
                    checked={simulationSettings.visualImpairment.enabled}
                    onCheckedChange={(checked) =>
                      setSimulationSettings(prev => ({
                        ...prev,
                        visualImpairment: { ...prev.visualImpairment, enabled: !!checked }
                      }))
                    }
                  />
                  <Label htmlFor="visual-enabled">Enable visual impairment simulation</Label>
                </div>

                {simulationSettings.visualImpairment.enabled && (
                  <div className="space-y-3">
                    <div>
                      <Label htmlFor="visual-type">Impairment Type</Label>
                      <Select
                        value={simulationSettings.visualImpairment.type}
                        onValueChange={(value: any) =>
                          setSimulationSettings(prev => ({
                            ...prev,
                            visualImpairment: { ...prev.visualImpairment, type: value }
                          }))
                        }
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="low-vision">Low Vision</SelectItem>
                          <SelectItem value="color-blind">Color Blindness</SelectItem>
                          <SelectItem value="blind">Blindness</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label htmlFor="visual-severity">
                        Severity: {simulationSettings.visualImpairment.severity}%
                      </Label>
                      <input
                        type="range"
                        id="visual-severity"
                        min="0"
                        max="100"
                        value={simulationSettings.visualImpairment.severity}
                        onChange={(e) =>
                          setSimulationSettings(prev => ({
                            ...prev,
                            visualImpairment: { ...prev.visualImpairment, severity: parseInt(e.target.value) }
                          }))
                        }
                        className="w-full"
                      />
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Motor Impairment Simulation */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MousePointer className="h-5 w-5" />
                  Motor Impairment
                </CardTitle>
                <CardDescription>
                  Simulate motor disabilities and limited mobility
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="motor-enabled"
                    checked={simulationSettings.motorImpairment.enabled}
                    onCheckedChange={(checked) =>
                      setSimulationSettings(prev => ({
                        ...prev,
                        motorImpairment: { ...prev.motorImpairment, enabled: !!checked }
                      }))
                    }
                  />
                  <Label htmlFor="motor-enabled">Enable motor impairment simulation</Label>
                </div>

                {simulationSettings.motorImpairment.enabled && (
                  <div className="space-y-3">
                    <div>
                      <Label htmlFor="motor-type">Impairment Type</Label>
                      <Select
                        value={simulationSettings.motorImpairment.type}
                        onValueChange={(value: any) =>
                          setSimulationSettings(prev => ({
                            ...prev,
                            motorImpairment: { ...prev.motorImpairment, type: value }
                          }))
                        }
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="limited-mobility">Limited Mobility</SelectItem>
                          <SelectItem value="tremor">Tremor</SelectItem>
                          <SelectItem value="one-hand">One Hand Use</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="keyboard-only"
                        checked={simulationSettings.motorImpairment.keyboardOnly}
                        onCheckedChange={(checked) =>
                          setSimulationSettings(prev => ({
                            ...prev,
                            motorImpairment: { ...prev.motorImpairment, keyboardOnly: !!checked }
                          }))
                        }
                      />
                      <Label htmlFor="keyboard-only">Keyboard only navigation</Label>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Screen Reader Simulation */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Volume2 className="h-5 w-5" />
                  Screen Reader
                </CardTitle>
                <CardDescription>
                  Simulate screen reader behavior and announcements
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="sr-enabled"
                    checked={simulationSettings.screenReader.enabled}
                    onCheckedChange={(checked) =>
                      setSimulationSettings(prev => ({
                        ...prev,
                        screenReader: { ...prev.screenReader, enabled: !!checked }
                      }))
                    }
                  />
                  <Label htmlFor="sr-enabled">Enable screen reader simulation</Label>
                </div>

                {simulationSettings.screenReader.enabled && (
                  <div className="space-y-3">
                    <div>
                      <Label htmlFor="sr-type">Screen Reader Type</Label>
                      <Select
                        value={simulationSettings.screenReader.type}
                        onValueChange={(value: any) =>
                          setSimulationSettings(prev => ({
                            ...prev,
                            screenReader: { ...prev.screenReader, type: value }
                          }))
                        }
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="nvda">NVDA</SelectItem>
                          <SelectItem value="jaws">JAWS</SelectItem>
                          <SelectItem value="voiceover">VoiceOver</SelectItem>
                          <SelectItem value="talkback">TalkBack</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label htmlFor="speech-rate">
                        Speech Rate: {simulationSettings.screenReader.speechRate}%
                      </Label>
                      <input
                        type="range"
                        id="speech-rate"
                        min="0"
                        max="100"
                        value={simulationSettings.screenReader.speechRate}
                        onChange={(e) =>
                          setSimulationSettings(prev => ({
                            ...prev,
                            screenReader: { ...prev.screenReader, speechRate: parseInt(e.target.value) }
                          }))
                        }
                        className="w-full"
                      />
                    </div>

                    <div>
                      <Label htmlFor="verbosity">Verbosity Level</Label>
                      <Select
                        value={simulationSettings.screenReader.verbosity}
                        onValueChange={(value: any) =>
                          setSimulationSettings(prev => ({
                            ...prev,
                            screenReader: { ...prev.screenReader, verbosity: value }
                          }))
                        }
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="low">Low</SelectItem>
                          <SelectItem value="medium">Medium</SelectItem>
                          <SelectItem value="high">High</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Cognitive Impairment Simulation */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <User className="h-5 w-5" />
                  Cognitive Impairment
                </CardTitle>
                <CardDescription>
                  Simulate cognitive disabilities and processing differences
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="cognitive-enabled"
                    checked={simulationSettings.cognitiveImpairment.enabled}
                    onCheckedChange={(checked) =>
                      setSimulationSettings(prev => ({
                        ...prev,
                        cognitiveImpairment: { ...prev.cognitiveImpairment, enabled: !!checked }
                      }))
                    }
                  />
                  <Label htmlFor="cognitive-enabled">Enable cognitive impairment simulation</Label>
                </div>

                {simulationSettings.cognitiveImpairment.enabled && (
                  <div className="space-y-3">
                    <div>
                      <Label htmlFor="cognitive-type">Impairment Type</Label>
                      <Select
                        value={simulationSettings.cognitiveImpairment.type}
                        onValueChange={(value: any) =>
                          setSimulationSettings(prev => ({
                            ...prev,
                            cognitiveImpairment: { ...prev.cognitiveImpairment, type: value }
                          }))
                        }
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="attention">Attention Deficit</SelectItem>
                          <SelectItem value="memory">Memory Issues</SelectItem>
                          <SelectItem value="processing">Processing Difficulties</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="reduced-motion"
                        checked={simulationSettings.cognitiveImpairment.reducedMotion}
                        onCheckedChange={(checked) =>
                          setSimulationSettings(prev => ({
                            ...prev,
                            cognitiveImpairment: { ...prev.cognitiveImpairment, reducedMotion: !!checked }
                          }))
                        }
                      />
                      <Label htmlFor="reduced-motion">Prefer reduced motion</Label>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="results" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Test Results</h3>
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Export Results
            </Button>
          </div>

          {testResults.length === 0 ? (
            <Card>
              <CardContent className="flex items-center justify-center h-32">
                <div className="text-center text-muted-foreground">
                  <Target className="h-12 w-12 mx-auto mb-2" />
                  <p>No test results yet</p>
                  <p className="text-sm">Complete some test scenarios to see results here</p>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {testResults.map((result, index) => {
                const scenario = testingScenarios.find(s => s.id === result.scenarioId);
                return (
                  <Card key={index}>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-lg">
                          {scenario?.name || result.scenarioId}
                        </CardTitle>
                        <div className="flex items-center gap-2">
                          <Badge variant={result.success ? 'default' : 'destructive'}>
                            {result.success ? 'Passed' : 'Failed'}
                          </Badge>
                          <Badge variant="outline">
                            {formatTime(result.timeSpent)}
                          </Badge>
                        </div>
                      </div>
                      <CardDescription>
                        Completed on {result.endTime?.toLocaleDateString()} at {result.endTime?.toLocaleTimeString()}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <span className="text-muted-foreground">Device:</span>
                            <p className="font-medium">{result.deviceType}</p>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Issues Found:</span>
                            <p className="font-medium">{result.issues.length}</p>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Assistive Tech:</span>
                            <p className="font-medium">{result.assistiveTechnology || 'None'}</p>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Time Spent:</span>
                            <p className="font-medium">{formatTime(result.timeSpent)}</p>
                          </div>
                        </div>

                        {result.feedback && (
                          <div>
                            <span className="text-muted-foreground text-sm">Feedback:</span>
                            <p className="text-sm mt-1">{result.feedback}</p>
                          </div>
                        )}

                        {result.issues.length > 0 && (
                          <div>
                            <span className="text-muted-foreground text-sm">Issues:</span>
                            <div className="mt-2 space-y-2">
                              {result.issues.map((issue, issueIndex) => (
                                <div key={issueIndex} className="flex items-start gap-2 text-sm">
                                  <Badge variant={getSeverityColor(issue.severity)} className="text-xs">
                                    {issue.severity}
                                  </Badge>
                                  <span>{issue.description}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>

        <TabsContent value="issues" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Reported Issues</h3>
            <Button
              onClick={() => setShowIssueForm(true)}
              variant="outline"
              size="sm"
            >
              <AlertTriangle className="h-4 w-4 mr-2" />
              Report New Issue
            </Button>
          </div>

          <ScrollArea className="h-96">
            <div className="space-y-4">
              {testResults.flatMap(result => result.issues).map((issue, index) => (
                <Card key={index}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-base">{issue.description}</CardTitle>
                      <Badge variant={getSeverityColor(issue.severity)}>
                        {issue.severity}
                      </Badge>
                    </div>
                    <CardDescription>
                      {issue.category} • {issue.location}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm">
                      {issue.reproduction && (
                        <div>
                          <span className="font-medium">Reproduction:</span>
                          <p className="text-muted-foreground">{issue.reproduction}</p>
                        </div>
                      )}
                      {issue.suggestion && (
                        <div>
                          <span className="font-medium">Suggestion:</span>
                          <p className="text-muted-foreground">{issue.suggestion}</p>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </ScrollArea>
        </TabsContent>
      </Tabs>

      {/* Issue Reporting Modal */}
      {showIssueForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md mx-4">
            <CardHeader>
              <CardTitle>Report Accessibility Issue</CardTitle>
              <CardDescription>
                Describe the accessibility issue you encountered
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="issue-severity">Severity</Label>
                <Select
                  value={newIssue.severity || 'medium'}
                  onValueChange={(value: any) => setNewIssue(prev => ({ ...prev, severity: value }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="low">Low</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                    <SelectItem value="critical">Critical</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="issue-category">Category</Label>
                <Input
                  id="issue-category"
                  value={newIssue.category || ''}
                  onChange={(e) => setNewIssue(prev => ({ ...prev, category: e.target.value }))}
                  placeholder="e.g., keyboard navigation, screen reader, visual"
                />
              </div>

              <div>
                <Label htmlFor="issue-description">Description</Label>
                <Textarea
                  id="issue-description"
                  value={newIssue.description || ''}
                  onChange={(e) => setNewIssue(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Describe the accessibility issue..."
                  rows={3}
                />
              </div>

              <div>
                <Label htmlFor="issue-reproduction">How to Reproduce</Label>
                <Textarea
                  id="issue-reproduction"
                  value={newIssue.reproduction || ''}
                  onChange={(e) => setNewIssue(prev => ({ ...prev, reproduction: e.target.value }))}
                  placeholder="Steps to reproduce the issue..."
                  rows={2}
                />
              </div>

              <div>
                <Label htmlFor="issue-suggestion">Suggested Fix</Label>
                <Textarea
                  id="issue-suggestion"
                  value={newIssue.suggestion || ''}
                  onChange={(e) => setNewIssue(prev => ({ ...prev, suggestion: e.target.value }))}
                  placeholder="How could this be fixed?"
                  rows={2}
                />
              </div>

              <div className="flex gap-2 pt-4">
                <Button
                  onClick={() => reportIssue(newIssue)}
                  disabled={!newIssue.description}
                  className="flex-1"
                >
                  Report Issue
                </Button>
                <Button
                  onClick={() => {
                    setShowIssueForm(false);
                    setNewIssue({});
                  }}
                  variant="outline"
                  className="flex-1"
                >
                  Cancel
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

export default AccessibilityUserTestingTool;