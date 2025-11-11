/**
 * Accessibility Testing Components
 * Provides tools for testing and validating accessibility features
 */
import * as React from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { useScreenReaderAnnouncements } from './use-screen-reader-announcements';
export interface AccessibilityTestResult {
  /** Test name */
  name: string;
  /** Test description */
  description: string;
  /** Test result */
  passed: boolean;
  /** Error message if test failed */
  error?: string;
  /** Suggestions for improvement */
  suggestions?: string[];
}
export interface AccessibilityTestSuite {
  /** Suite name */
  name: string;
  /** Test results */
  results: AccessibilityTestResult[];
  /** Overall pass rate */
  passRate: number;
}
/**
 * AccessibilityTester - Component for running accessibility tests
 */
export interface AccessibilityTesterProps {
  /** Target element to test */
  target?: HTMLElement | null;
  /** Whether to run tests automatically */
  autoRun?: boolean;
  /** Callback when tests complete */
  onTestComplete?: (results: AccessibilityTestSuite) => void;
  /** Custom tests to run */
  customTests?: Array<(element: HTMLElement) => AccessibilityTestResult>;
}
export const AccessibilityTester: React.FC<AccessibilityTesterProps> = ({
  target,
  autoRun = false,
  onTestComplete,
  customTests = [],
}) => {
  const [testResults, setTestResults] = React.useState<AccessibilityTestSuite | null>(null);
  const [isRunning, setIsRunning] = React.useState(false);
  const { announce } = useScreenReaderAnnouncements();
  const runBasicTests = React.useCallback((element: HTMLElement): AccessibilityTestResult[] => {
    const results: AccessibilityTestResult[] = [];
    // Test 1: Check for proper heading hierarchy
    const headings = element.querySelectorAll('h1, h2, h3, h4, h5, h6');
    let headingHierarchyValid = true;
    let lastLevel = 0;
    headings.forEach((heading) => {
      const level = parseInt(heading.tagName.charAt(1));
      if (level > lastLevel + 1) {
        headingHierarchyValid = false;
      }
      lastLevel = level;
    });
    results.push({
      name: 'Heading Hierarchy',
      description: 'Checks if headings follow proper hierarchical order',
      passed: headingHierarchyValid,
      error: headingHierarchyValid ? undefined : 'Heading levels skip numbers in hierarchy',
      suggestions: headingHierarchyValid ? undefined : ['Use consecutive heading levels (h1, h2, h3, etc.)'],
    });

    // Test 2: Check for alt text on images
    const images = element.querySelectorAll('img');
    let imagesWithAlt = 0;
    images.forEach((img) => {
      if (img.hasAttribute('alt')) {
        imagesWithAlt++;
      }
    });
    const altTextPassed = images.length === 0 || imagesWithAlt === images.length;
    results.push({
      name: 'Image Alt Text',
      description: 'Checks if all images have alt text',
      passed: altTextPassed,
      error: altTextPassed ? undefined : `${images.length - imagesWithAlt} images missing alt text`,
      suggestions: altTextPassed ? undefined : ['Add alt attributes to all images', 'Use empty alt="" for decorative images'],
    });

    // Test 3: Check for proper form labels
    const inputs = element.querySelectorAll('input, select, textarea');
    let inputsWithLabels = 0;
    inputs.forEach((input) => {
      const hasLabel = input.hasAttribute('aria-label') ||
                     input.hasAttribute('aria-labelledby') ||
                     element.querySelector(`label[for="${input.id}"]`) !== null;
      if (hasLabel) {
        inputsWithLabels++;
      }
    });
    const labelsPassed = inputs.length === 0 || inputsWithLabels === inputs.length;
    results.push({
      name: 'Form Labels',
      description: 'Checks if all form inputs have proper labels',
      passed: labelsPassed,
      error: labelsPassed ? undefined : `${inputs.length - inputsWithLabels} inputs missing labels`,
      suggestions: labelsPassed ? undefined : ['Add labels to all form inputs', 'Use aria-label or aria-labelledby for inputs'],
    });

    // Test 4: Check for keyboard accessibility
    const interactiveElements = element.querySelectorAll('button, a, input, select, textarea, [tabindex]');
    let keyboardAccessible = 0;
    interactiveElements.forEach((el) => {
      const tabIndex = el.getAttribute('tabindex');
      if (tabIndex === null || parseInt(tabIndex) >= 0) {
        keyboardAccessible++;
      }
    });
    const keyboardPassed = interactiveElements.length === 0 || keyboardAccessible === interactiveElements.length;
    results.push({
      name: 'Keyboard Accessibility',
      description: 'Checks if interactive elements are keyboard accessible',
      passed: keyboardPassed,
      error: keyboardPassed ? undefined : `${interactiveElements.length - keyboardAccessible} elements not keyboard accessible`,
      suggestions: keyboardPassed ? undefined : ['Ensure all interactive elements have tabindex >= 0', 'Remove tabindex="-1" from interactive elements'],
    });

    // Test 5: Check for ARIA landmarks
    const landmarks = element.querySelectorAll('[role="banner"], [role="main"], [role="navigation"], [role="complementary"], [role="contentinfo"], header, main, nav, aside, footer');
    const landmarksPassed = landmarks.length > 0;
    results.push({
      name: 'ARIA Landmarks',
      description: 'Checks if page has proper landmark regions',
      passed: landmarksPassed,
      error: landmarksPassed ? undefined : 'No landmark regions found',
      suggestions: landmarksPassed ? undefined : ['Add semantic HTML elements (header, main, nav, aside, footer)', 'Use ARIA landmark roles'],
    });

    // Test 6: Check for color contrast (basic check)
    const elementsWithColor = element.querySelectorAll('*');
    let contrastIssues = 0;
    elementsWithColor.forEach((el) => {
      const styles = window.getComputedStyle(el);
      const color = styles.color;
      const backgroundColor = styles.backgroundColor;
      // This is a simplified check - in reality, you'd need a proper contrast ratio calculator
      if (color === backgroundColor) {
        contrastIssues++;
      }
    });
    const contrastPassed = contrastIssues === 0;
    results.push({
      name: 'Color Contrast',
      description: 'Basic check for color contrast issues',
      passed: contrastPassed,
      error: contrastPassed ? undefined : `${contrastIssues} potential contrast issues found`,
      suggestions: contrastPassed ? undefined : ['Ensure text has sufficient contrast with background', 'Use tools like WebAIM Contrast Checker'],
    });

    return results;
  }, []);
  const runTests = React.useCallback(async () => {
    if (!target || isRunning) return;
    setIsRunning(true);
    announce('Running accessibility tests', 'polite');
    try {
      const basicResults = runBasicTests(target);
      const customResults = customTests.map(test => test(target));
      const allResults = [...basicResults, ...customResults];
      const passedTests = allResults.filter(result => result.passed).length;
      const passRate = (passedTests / allResults.length) * 100;
      const testSuite: AccessibilityTestSuite = {
        name: 'Accessibility Test Suite',
        results: allResults,
        passRate,
      };
      setTestResults(testSuite);
      onTestComplete?.(testSuite);
      announce(`Accessibility tests completed. ${passedTests} of ${allResults.length} tests passed.`, 'polite');
    } catch (error) {
      announce('Accessibility tests failed to run', 'assertive');
    } finally {
      setIsRunning(false);
    }
  }, [target, isRunning, runBasicTests, customTests, onTestComplete, announce]);
  React.useEffect(() => {
    if (autoRun && target) {
      runTests();
    }
  }, [autoRun, target, runTests]);
  return (
    <div className="accessibility-tester">
      <div className="flex items-center gap-2 mb-4">
        <Button
          onClick={runTests}
          disabled={!target || isRunning}
          className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90 disabled:opacity-50"
          aria-label="Run accessibility tests"
        >
          {isRunning ? 'Running Tests...' : 'Run Accessibility Tests'}
        </Button>
        {testResults && (
          <span className={cn(
            'px-2 py-1 rounded text-sm font-medium',
            testResults.passRate === 100 ? 'bg-green-100 text-green-800' :
            testResults.passRate >= 80 ? 'bg-yellow-100 text-yellow-800' :
            'bg-red-100 text-red-800'
          )}>
            {testResults.passRate.toFixed(0)}% Pass Rate
          </span>
        )}
      </div>
      {testResults && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">Test Results</h3>
          <div className="space-y-2">
            {testResults.results.map((result, index) => (
              <div
                key={index}
                className={cn(
                  'p-3 rounded border',
                  result.passed ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'
                )}
              >
                <div className="flex items-center gap-2">
                  <span className={cn(
                    'w-4 h-4 rounded-full flex items-center justify-center text-xs font-bold',
                    result.passed ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
                  )}>
                    {result.passed ? '✓' : '✗'}
                  </span>
                  <h4 className="font-medium">{result.name}</h4>
                </div>
                <p className="text-sm text-gray-600 mt-1 md:text-base lg:text-lg">{result.description}</p>
                {result.error && (
                  <p className="text-sm text-red-600 mt-1 md:text-base lg:text-lg">Error: {result.error}</p>
                )}
                {result.suggestions && result.suggestions.length > 0 && (
                  <div className="mt-2">
                    <p className="text-sm font-medium md:text-base lg:text-lg">Suggestions:</p>
                    <ul className="text-sm text-gray-600 list-disc list-inside md:text-base lg:text-lg">
                      {result.suggestions.map((suggestion, i) => (
                        <li key={i}>{suggestion}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
/**
 * AccessibilityReport - Displays accessibility test results
 */
export interface AccessibilityReportProps {
  /** Test suite results */
  testSuite: AccessibilityTestSuite;
  /** Whether to show detailed results */
  detailed?: boolean;
}
export const AccessibilityReport: React.FC<AccessibilityReportProps> = ({
  testSuite,
  detailed = true,
}) => {
  const passedTests = testSuite.results.filter(result => result.passed).length;
  const failedTests = testSuite.results.length - passedTests;
  return (
    <div className="accessibility-report">
      <div className="mb-4">
        <h2 className="text-xl font-bold mb-2">{testSuite.name}</h2>
        <div className="flex items-center gap-4">
          <span className="text-green-600 font-medium">
            ✓ {passedTests} Passed
          </span>
          <span className="text-red-600 font-medium">
            ✗ {failedTests} Failed
          </span>
          <span className={cn(
            'px-2 py-1 rounded text-sm font-medium',
            testSuite.passRate === 100 ? 'bg-green-100 text-green-800' :
            testSuite.passRate >= 80 ? 'bg-yellow-100 text-yellow-800' :
            'bg-red-100 text-red-800'
          )}>
            {testSuite.passRate.toFixed(0)}% Pass Rate
          </span>
        </div>
      </div>
      {detailed && (
        <div className="space-y-3">
          {testSuite.results.map((result, index) => (
            <div
              key={index}
              className={cn(
                'p-3 rounded border',
                result.passed ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'
              )}
            >
              <div className="flex items-start gap-2">
                <span className={cn(
                  'w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold mt-0.5',
                  result.passed ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
                )}>
                  {result.passed ? '✓' : '✗'}
                </span>
                <div className="flex-1">
                  <h3 className="font-medium">{result.name}</h3>
                  <p className="text-sm text-gray-600 md:text-base lg:text-lg">{result.description}</p>
                  {result.error && (
                    <p className="text-sm text-red-600 mt-1 md:text-base lg:text-lg">
                      <strong>Issue:</strong> {result.error}
                    </p>
                  )}
                  {result.suggestions && result.suggestions.length > 0 && (
                    <div className="mt-2">
                      <p className="text-sm font-medium text-gray-700 md:text-base lg:text-lg">How to fix:</p>
                      <ul className="text-sm text-gray-600 list-disc list-inside ml-2 md:text-base lg:text-lg">
                        {result.suggestions.map((suggestion, i) => (
                          <li key={i}>{suggestion}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
export default AccessibilityTester;
