import { useCallback, useEffect, useRef, useState, type RefObject } from 'react';
import { AccessibilityTestSuiteImpl, type AccessibilityTestSuite, type AccessibilityReport } from '../lib/accessibility/accessibility-testing';

export interface UseAccessibilityTestingOptions {
  /** Whether to run tests automatically */
  autoTest?: boolean;
  /** Interval for automatic testing (in ms) */
  testInterval?: number;
  /** Whether to test on component updates */
  testOnUpdate?: boolean;
  /** Minimum score threshold for passing */
  scoreThreshold?: number;
  /** Callback when test completes */
  onTestComplete?: (report: AccessibilityReport) => void;
  /** Callback when test fails */
  onTestFail?: (report: AccessibilityReport) => void;
}

export interface AccessibilityTestingState {
  /** Current test report */
  report: AccessibilityReport | null;
  /** Whether tests are currently running */
  isRunning: boolean;
  /** Test history */
  history: AccessibilityReport[];
  /** Last test timestamp */
  lastTested: Date | null;
  /** Whether the component passes accessibility tests */
  passes: boolean;
  /** Current accessibility score */
  score: number;
}

export function useAccessibilityTesting(
  elementRef: RefObject<HTMLElement>,
  options: UseAccessibilityTestingOptions = {}
) {
  const {
    autoTest = false,
    testInterval = 30000, // 30 seconds
    testOnUpdate = false,
    scoreThreshold = 80,
    onTestComplete,
    onTestFail,
  } = options;

  const [state, setState] = useState<AccessibilityTestingState>({
    report: null,
    isRunning: false,
    history: [],
    lastTested: null,
    passes: true,
    score: 100,
  });

  const testSuiteRef = useRef<AccessibilityTestSuite | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // Initialize test suite
  useEffect(() => {
    if (elementRef.current) {
      testSuiteRef.current = new AccessibilityTestSuiteImpl(elementRef.current);
    }
  }, [elementRef]);

  // Run accessibility test
  const runTest = useCallback(async (testType: 'basic' | 'comprehensive' = 'basic') => {
    if (!testSuiteRef.current || state.isRunning) return;
    setState(prev => ({ ...prev, isRunning: true }));
    try {
      const report = testType === 'comprehensive'
        ? await testSuiteRef.current.comprehensive()
        : await testSuiteRef.current.basic();

      const passes = report.passed && report.score >= scoreThreshold;
      setState(prev => ({
        ...prev,
        report,
        isRunning: false,
        history: [...prev.history.slice(-9), report], // Keep last 10 reports
        lastTested: new Date(),
        passes,
        score: report.score,
      }));

      // Trigger callbacks
      onTestComplete?.(report);
      if (!passes) {
        onTestFail?.(report);
      }

      return report;
    } catch (error) {
      setState(prev => ({ ...prev, isRunning: false }));
      console.error('Accessibility test failed:', error);
      throw error;
    }
  }, [state.isRunning, scoreThreshold, onTestComplete, onTestFail]);

  // Run keyboard accessibility test
  const runKeyboardTest = useCallback(async () => {
    if (!testSuiteRef.current || state.isRunning) return;
    setState(prev => ({ ...prev, isRunning: true }));
    try {
      const result = await testSuiteRef.current.keyboard();
      setState(prev => ({ ...prev, isRunning: false }));
      return result;
    } catch (error) {
      setState(prev => ({ ...prev, isRunning: false }));
      console.error('Keyboard accessibility test failed:', error);
      throw error;
    }
  }, [state.isRunning]);

  // Run screen reader test
  const runScreenReaderTest = useCallback(async () => {
    if (!testSuiteRef.current || state.isRunning) return;
    setState(prev => ({ ...prev, isRunning: true }));
    try {
      const result = await testSuiteRef.current.screenReader();
      setState(prev => ({ ...prev, isRunning: false }));
      return result;
    } catch (error) {
      setState(prev => ({ ...prev, isRunning: false }));
      console.error('Screen reader test failed:', error);
      throw error;
    }
  }, [state.isRunning]);

  // Run color contrast test
  const runColorContrastTest = useCallback(async () => {
    if (!testSuiteRef.current || state.isRunning) return;
    setState(prev => ({ ...prev, isRunning: true }));
    try {
      const result = await testSuiteRef.current.colorContrast();
      setState(prev => ({ ...prev, isRunning: false }));
      return result;
    } catch (error) {
      setState(prev => ({ ...prev, isRunning: false }));
      console.error('Color contrast test failed:', error);
      throw error;
    }
  }, [state.isRunning]);

  // Run comprehensive test suite
  const runFullSuite = useCallback(async () => {
    if (!testSuiteRef.current || state.isRunning) return;
    setState(prev => ({ ...prev, isRunning: true }));
    try {
      const [basic, keyboard, screenReader, colorContrast, focusManagement, aria] = await Promise.all([
        testSuiteRef.current.basic(),
        testSuiteRef.current.keyboard(),
        testSuiteRef.current.screenReader(),
        testSuiteRef.current.colorContrast(),
        testSuiteRef.current.focusManagement(),
        testSuiteRef.current.aria(),
      ]);

      const fullReport = {
        basic,
        keyboard,
        screenReader,
        colorContrast,
        focusManagement,
        aria,
        overallPassed: basic.passed && keyboard.passed && screenReader.passed && colorContrast.passed,
        overallScore: Math.round((basic.score + (keyboard.passed ? 100 : 0) + (screenReader.passed ? 100 : 0) + (colorContrast.passed ? 100 : 0)) / 4),
      };

      setState(prev => ({ ...prev, isRunning: false }));
      return fullReport;
    } catch (error) {
      setState(prev => ({ ...prev, isRunning: false }));
      console.error('Full accessibility test suite failed:', error);
      throw error;
    }
  }, [state.isRunning]);

  // Set up automatic testing
  useEffect(() => {
    if (autoTest && testSuiteRef.current) {
      intervalRef.current = setInterval(() => {
        runTest('basic');
      }, testInterval);

      // Run initial test
      runTest('basic');
      return () => {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
        }
      };
    }
  }, [autoTest, testInterval, runTest]);

  // Test on component updates
  useEffect(() => {
    if (testOnUpdate && testSuiteRef.current && !state.isRunning) {
      const timeoutId = setTimeout(() => {
        runTest('basic');
      }, 1000); // Debounce updates
      return () => clearTimeout(timeoutId);
    }
  }, [testOnUpdate, runTest, state.isRunning]);

  // Cleanup
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  return {
    ...state,
    runTest,
    runKeyboardTest,
    runScreenReaderTest,
    runColorContrastTest,
    runFullSuite,
  };
}

// Hook for monitoring accessibility in development
export function useAccessibilityMonitor(
  elementRef: React.RefObject<HTMLElement>,
  enabled: boolean = process.env.NODE_ENV === 'development'
) {
  const [violations, setViolations] = useState<string[]>([]);
  const [warnings, setWarnings] = useState<string[]>([]);
  const { report, runTest } = useAccessibilityTesting(elementRef, {
    autoTest: enabled,
    testInterval: 10000, // 10 seconds in development
    onTestComplete: (report) => {
      const newViolations = report.violations.map(v => v.description);
      const newWarnings = report.warnings.map(w => w.description);
      setViolations(newViolations);
      setWarnings(newWarnings);

      // Log to console in development
      if (enabled && (newViolations.length > 0 || newWarnings.length > 0)) {
        console.group('🔍 Accessibility Issues Detected');
        if (newViolations.length > 0) {
          console.warn('Violations:', newViolations);
        }
        if (newWarnings.length > 0) {
          console.warn('Warnings:', newWarnings);
        }
        console.groupEnd();
      }
    },
  });

  return {
    violations,
    warnings,
    report,
    runTest,
    hasIssues: violations.length > 0 || warnings.length > 0,
  };
}

// Hook for accessibility testing in tests
export function useAccessibilityTestRunner() {
  const runAccessibilityTest = useCallback(async (element: HTMLElement) => {
    const testSuite = new AccessibilityTestSuiteImpl(element);
    return await testSuite.basic();
  }, []);

  const runKeyboardTest = useCallback(async (element: HTMLElement) => {
    const testSuite = new AccessibilityTestSuiteImpl(element);
    return await testSuite.keyboard();
  }, []);

  const runScreenReaderTest = useCallback(async (element: HTMLElement) => {
    const testSuite = new AccessibilityTestSuiteImpl(element);
    return await testSuite.screenReader();
  }, []);

  const runColorContrastTest = useCallback(async (element: HTMLElement) => {
    const testSuite = new AccessibilityTestSuiteImpl(element);
    return await testSuite.colorContrast();
  }, []);

  return {
    runAccessibilityTest,
    runKeyboardTest,
    runScreenReaderTest,
    runColorContrastTest,
  };
}

export default useAccessibilityTesting;
