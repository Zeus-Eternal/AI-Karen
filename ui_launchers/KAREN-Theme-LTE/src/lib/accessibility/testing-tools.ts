/**
 * Accessibility Testing and Validation Tools
 * Comprehensive accessibility testing and validation for WCAG 2.1 AA compliance
 */

'use client';

import React, { useEffect, useCallback, useState, useRef } from 'react';
import { useAccessibility } from '@/contexts/AccessibilityContext';
import { wcagComplianceChecker, WCAGComplianceReport } from './wcag-compliance';
import { useAxeTesting, AccessibilityTest } from './axe-testing';

// Test result interface
export interface TestResult {
  id: string;
  name: string;
  status: 'pass' | 'fail' | 'warning' | 'review';
  description: string;
  impact: 'critical' | 'serious' | 'moderate' | 'minor';
  wcagCriteria: string[];
  element?: HTMLElement;
  recommendation?: string;
  timestamp: Date;
}

// Testing configuration
export interface TestingConfig {
  // Test scope
  includeComponentTests: boolean;
  includePageTests: boolean;
  includeContrastTests: boolean;
  includeKeyboardTests: boolean;
  includeScreenReaderTests: boolean;
  
  // Test filters
  excludeSelectors: string[];
  includeSelectors: string[];
  
  // WCAG level
  wcagLevel: 'A' | 'AA' | 'AAA';
  
  // Test options
  testColorContrast: boolean;
  testFocusManagement: boolean;
  testKeyboardNavigation: boolean;
  testARIA: boolean;
  testSemanticHTML: boolean;
  testImageAlt: boolean;
  testFormLabels: boolean;
  testLinkText: boolean;
  testHeadingOrder: boolean;
  testTableHeaders: boolean;
}

// Default testing configuration
const DEFAULT_TESTING_CONFIG: TestingConfig = {
  includeComponentTests: true,
  includePageTests: true,
  includeContrastTests: true,
  includeKeyboardTests: true,
  includeScreenReaderTests: true,
  excludeSelectors: [],
  includeSelectors: [],
  wcagLevel: 'AA',
  testColorContrast: true,
  testFocusManagement: true,
  testKeyboardNavigation: true,
  testARIA: true,
  testSemanticHTML: true,
  testImageAlt: true,
  testFormLabels: true,
  testLinkText: true,
  testHeadingOrder: true,
  testTableHeaders: true,
};

// Accessibility testing hook
export function useAccessibilityTesting(config: Partial<TestingConfig> = {}) {
  const { state, addViolation, updateComplianceScore } = useAccessibility();
  const { runFullTest, runQuickTest, testComponent } = useAxeTesting();
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [currentTest, setCurrentTest] = useState<string | null>(null);
  const [complianceReport, setComplianceReport] = useState<WCAGComplianceReport | null>(null);
  
  const testingConfig = { ...DEFAULT_TESTING_CONFIG, ...config };

  // Manual contrast checker
  const checkColorContrast = useCallback((element: HTMLElement): TestResult | null => {
    if (!testingConfig.testColorContrast) return null;

    const styles = window.getComputedStyle(element);
    const color = styles.color;
    const backgroundColor = styles.backgroundColor;
    
    // Skip transparent backgrounds
    if (backgroundColor === 'transparent' || backgroundColor === 'rgba(0, 0, 0, 0)') {
      return null;
    }
    
    // Convert RGB to hex for easier processing
    const rgbToHex = (rgb: string): string => {
      const match = rgb.match(/\d+/g);
      if (!match) return '#000000';
      
      const hex = match.slice(0, 3).map(x => {
        const hex = parseInt(x).toString(16);
        return hex.length === 1 ? '0' + hex : hex;
      });
      
      return '#' + hex.join('');
    };
    
    const foreground = rgbToHex(color);
    const background = rgbToHex(backgroundColor);
    
    // Calculate contrast ratio
    const getLuminance = (hex: string): number => {
      const rgb = parseInt(hex.slice(1), 16);
      const r = (rgb >> 16) & 0xff;
      const g = (rgb >> 8) & 0xff;
      const b = rgb & 0xff;
      
      const [rs, gs, bs] = [r, g, b].map(c => {
        c = c / 255;
        return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
      });
      
      return 0.2126 * (rs ?? 0) + 0.7152 * (gs ?? 0) + 0.0722 * (bs ?? 0);
    };
    
    const l1 = getLuminance(foreground);
    const l2 = getLuminance(background);
    const lighter = Math.max(l1, l2);
    const darker = Math.min(l1, l2);
    const ratio = (lighter + 0.05) / (darker + 0.05);
    
    // Check WCAG compliance
    const fontSize = parseFloat(styles.fontSize);
    const fontWeight = styles.fontWeight;
    const isLargeText = fontSize >= 18 || (fontSize >= 14 && fontWeight === 'bold' || fontWeight === '700');
    
    const requiredRatio = isLargeText ? 3.0 : 4.5;
    const passes = ratio >= requiredRatio;
    
    return {
      id: `contrast-${Date.now()}`,
      name: 'Color Contrast',
      status: passes ? 'pass' : 'fail',
      description: `Contrast ratio: ${ratio.toFixed(2)}:1 (required: ${requiredRatio}:1)`,
      impact: passes ? 'minor' : 'serious',
      wcagCriteria: ['1.4.3'],
      element,
      recommendation: passes ? undefined : 'Increase color contrast to meet WCAG AA standards',
      timestamp: new Date(),
    };
  }, [testingConfig.testColorContrast]);

  // Manual focus management test
  const testFocusManagement = useCallback((element: HTMLElement): TestResult | null => {
    if (!testingConfig.testFocusManagement) return null;

    const issues: string[] = [];
    
    // Check if element is focusable
    const isFocusable = element.matches(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"]), [contenteditable="true"]'
    );
    
    if (isFocusable) {
      // Check for focus indicator
      const focusStyles = window.getComputedStyle(element, ':focus');
      const hasFocusIndicator = 
        focusStyles.outline !== 'none' ||
        focusStyles.boxShadow !== 'none' ||
        focusStyles.border !== 'none';
      
      if (!hasFocusIndicator) {
        issues.push('No visible focus indicator');
      }
      
      // Check tabindex
      const tabindex = element.getAttribute('tabindex');
      if (tabindex && parseInt(tabindex) > 0) {
        issues.push('Positive tabindex value may disrupt logical tab order');
      }
    }
    
    if (issues.length === 0) return null;
    
    return {
      id: `focus-${Date.now()}`,
      name: 'Focus Management',
      status: 'fail',
      description: issues.join('; '),
      impact: 'serious',
      wcagCriteria: ['2.4.7'],
      element,
      recommendation: 'Add visible focus indicators and use proper tabindex values',
      timestamp: new Date(),
    };
  }, [testingConfig.testFocusManagement]);

  // Manual ARIA test
  const testARIA = useCallback((element: HTMLElement): TestResult | null => {
    if (!testingConfig.testARIA) return null;

    const issues: string[] = [];
    
    // Check for invalid ARIA attributes
    const role = element.getAttribute('role');
    if (role) {
      const validRoles = [
        'alert', 'alertdialog', 'application', 'article', 'banner', 'button', 'cell',
        'checkbox', 'columnheader', 'combobox', 'complementary', 'contentinfo',
        'definition', 'dialog', 'directory', 'document', 'feed', 'figure',
        'form', 'grid', 'gridcell', 'group', 'heading', 'img', 'link',
        'list', 'listbox', 'listitem', 'log', 'main', 'marquee', 'math',
        'menu', 'menubar', 'menuitem', 'menuitemcheckbox', 'menuitemradio',
        'navigation', 'none', 'note', 'option', 'presentation', 'progressbar',
        'radio', 'radiogroup', 'region', 'row', 'rowgroup', 'rowheader',
        'scrollbar', 'search', 'searchbox', 'separator', 'slider', 'spinbutton',
        'status', 'switch', 'tab', 'table', 'tablist', 'tabpanel', 'term',
        'textbox', 'timer', 'toolbar', 'tooltip', 'tree', 'treegrid', 'treeitem'
      ];
      
      if (!validRoles.includes(role)) {
        issues.push(`Invalid role: ${role}`);
      }
    }
    
    // Check for required ARIA attributes
    if (role === 'button' && !element.getAttribute('aria-label') && !element.getAttribute('aria-labelledby') && !element.textContent?.trim()) {
      issues.push('Button role requires accessible name');
    }
    
    if (role === 'img' && !element.getAttribute('aria-label') && !element.getAttribute('aria-labelledby')) {
      issues.push('Image role requires accessible name');
    }
    
    if (issues.length === 0) return null;
    
    return {
      id: `aria-${Date.now()}`,
      name: 'ARIA Attributes',
      status: 'fail',
      description: issues.join('; '),
      impact: 'serious',
      wcagCriteria: ['4.1.2'],
      element,
      recommendation: 'Fix invalid ARIA attributes and ensure proper labeling',
      timestamp: new Date(),
    };
  }, [testingConfig.testARIA]);

  // Manual semantic HTML test
  const testSemanticHTML = useCallback((element: HTMLElement): TestResult | null => {
    if (!testingConfig.testSemanticHTML) return null;

    const issues: string[] = [];
    const tagName = element.tagName.toLowerCase();
    
    // Check for proper heading structure
    if (tagName.startsWith('h')) {
      const level = parseInt(tagName.slice(1));
      if (isNaN(level) || level < 1 || level > 6) {
        issues.push(`Invalid heading level: ${tagName}`);
      }
    }
    
    // Check for proper use of semantic elements
    if (tagName === 'div' && element.getAttribute('role')) {
      const role = element.getAttribute('role');
      const semanticEquivalent = {
        'navigation': 'nav',
        'main': 'main',
        'complementary': 'aside',
        'banner': 'header',
        'contentinfo': 'footer',
        'region': 'section',
      };
      
      if (semanticEquivalent[role as keyof typeof semanticEquivalent]) {
        issues.push(`Use <${semanticEquivalent[role as keyof typeof semanticEquivalent]}> instead of div with role="${role}"`);
      }
    }
    
    // Check for table headers
    if (tagName === 'table') {
      const hasHeaders = element.querySelector('th, [scope]');
      if (!hasHeaders) {
        issues.push('Table lacks proper headers');
      }
    }
    
    if (issues.length === 0) return null;
    
    return {
      id: `semantic-${Date.now()}`,
      name: 'Semantic HTML',
      status: 'fail',
      description: issues.join('; '),
      impact: 'moderate',
      wcagCriteria: ['1.3.1'],
      element,
      recommendation: 'Use appropriate semantic HTML elements',
      timestamp: new Date(),
    };
  }, [testingConfig.testSemanticHTML]);

  // Run comprehensive accessibility test
  const runComprehensiveTest = useCallback(async (scope?: HTMLElement | string) => {
    setIsRunning(true);
    setCurrentTest('Running comprehensive accessibility test...');
    
    try {
      const results: TestResult[] = [];
      
      // Run axe-core tests
      if (testingConfig.includeComponentTests || testingConfig.includePageTests) {
        const axeResults = await runFullTest();
        axeResults.forEach((axeResult: AccessibilityTest) => {
          results.push({
            id: `axe-${Date.now()}-${Math.random()}`,
            name: axeResult.name,
            status: axeResult.status,
            description: axeResult.description,
            impact: axeResult.impact,
            wcagCriteria: axeResult.tags.filter((tag: any) => tag.match(/^\d\.\d+\.\d+$/)),
            recommendation: axeResult.violations[0]?.help,
            timestamp: new Date(),
          });
        });
      }
      
      // Run WCAG compliance test
      if (testingConfig.includePageTests) {
        const wcagReport = await wcagComplianceChecker.runComplianceTest();
        setComplianceReport(wcagReport);
        updateComplianceScore(wcagReport.overallScore);
        
        wcagReport.violations.forEach((violation: any) => {
          results.push({
            id: `wcag-${Date.now()}-${Math.random()}`,
            name: violation.id,
            status: 'fail',
            description: violation.description,
            impact: violation.impact,
            wcagCriteria: violation.wcagCriteria,
            recommendation: violation.help,
            timestamp: new Date(),
          });
        });
      }
      
      // Run manual tests on specified scope
      if (scope) {
        const elements = typeof scope === 'string' 
          ? document.querySelectorAll(scope) as NodeListOf<HTMLElement>
          : [scope];
        
        elements.forEach(element => {
          const contrastTest = checkColorContrast(element);
          if (contrastTest) results.push(contrastTest);
          
          const focusTest = testFocusManagement(element);
          if (focusTest) results.push(focusTest);
          
          const ariaTest = testARIA(element);
          if (ariaTest) results.push(ariaTest);
          
          const semanticTest = testSemanticHTML(element);
          if (semanticTest) results.push(semanticTest);
        });
      }
      
      setTestResults(results);
      
      // Add violations to global state
      results.filter(result => result.status === 'fail').forEach(result => {
        const accessibilityViolation: Omit<import('../../contexts/AccessibilityContext').AccessibilityViolation, 'timestamp'> = {
          message: result.description,
          priority: 'polite',
          type: result.name,
          severity: result.impact,
        };
        addViolation(accessibilityViolation);
      });
      
      return results;
    } catch (error) {
      console.error('Accessibility test failed:', error);
      return [];
    } finally {
      setIsRunning(false);
      setCurrentTest(null);
    }
  }, [
    testingConfig,
    runFullTest,
    checkColorContrast,
    testFocusManagement,
    testARIA,
    testSemanticHTML,
    addViolation,
    updateComplianceScore,
  ]);

  // Run quick test
  const runQuickAccessibilityTest = useCallback(async () => {
    setIsRunning(true);
    setCurrentTest('Running quick accessibility test...');
    
    try {
      const results: TestResult[] = [];
      
      // Run quick axe tests
      const axeResults = await runQuickTest();
      axeResults.forEach((axeResult: AccessibilityTest) => {
        results.push({
          id: `axe-quick-${Date.now()}-${Math.random()}`,
          name: axeResult.name,
          status: axeResult.status,
          description: axeResult.description,
          impact: axeResult.impact,
          wcagCriteria: axeResult.tags.filter((tag: any) => tag.match(/^\d\.\d+\.\d+$/)),
          recommendation: axeResult.violations[0]?.help,
          timestamp: new Date(),
        });
      });
      
      setTestResults(results);
      return results;
    } catch (error) {
      console.error('Quick accessibility test failed:', error);
      return [];
    } finally {
      setIsRunning(false);
      setCurrentTest(null);
    }
  }, [runQuickTest]);

  // Test specific component
  const testComponentAccessibility = useCallback(async (component: HTMLElement) => {
    setIsRunning(true);
    setCurrentTest('Testing component accessibility...');
    
    try {
      const results: TestResult[] = [];
      
      // Run axe test on component
      const axeResults = await testComponent(component);
      axeResults.forEach((axeResult: AccessibilityTest) => {
        results.push({
          id: `axe-component-${Date.now()}-${Math.random()}`,
          name: axeResult.name,
          status: axeResult.status,
          description: axeResult.description,
          impact: axeResult.impact,
          wcagCriteria: axeResult.tags.filter((tag: any) => tag.match(/^\d\.\d+\.\d+$/)),
          recommendation: axeResult.violations[0]?.help,
          element: component,
          timestamp: new Date(),
        });
      });
      
      // Run manual tests on component
      const contrastTest = checkColorContrast(component);
      if (contrastTest) results.push(contrastTest);
      
      const focusTest = testFocusManagement(component);
      if (focusTest) results.push(focusTest);
      
      const ariaTest = testARIA(component);
      if (ariaTest) results.push(ariaTest);
      
      const semanticTest = testSemanticHTML(component);
      if (semanticTest) results.push(semanticTest);
      
      setTestResults(results);
      return results;
    } catch (error) {
      console.error('Component accessibility test failed:', error);
      return [];
    } finally {
      setIsRunning(false);
      setCurrentTest(null);
    }
  }, [testComponent, checkColorContrast, testFocusManagement, testARIA, testSemanticHTML]);

  // Clear test results
  const clearResults = useCallback(() => {
    setTestResults([]);
    setComplianceReport(null);
  }, []);

  // Generate test report
  const generateReport = useCallback(() => {
    const passed = testResults.filter(r => r.status === 'pass').length;
    const failed = testResults.filter(r => r.status === 'fail').length;
    const warnings = testResults.filter(r => r.status === 'warning').length;
    const reviews = testResults.filter(r => r.status === 'review').length;
    
    const criticalIssues = testResults.filter(r => r.impact === 'critical').length;
    const seriousIssues = testResults.filter(r => r.impact === 'serious').length;
    const moderateIssues = testResults.filter(r => r.impact === 'moderate').length;
    const minorIssues = testResults.filter(r => r.impact === 'minor').length;
    
    return {
      summary: {
        total: testResults.length,
        passed,
        failed,
        warnings,
        reviews,
        criticalIssues,
        seriousIssues,
        moderateIssues,
        minorIssues,
        complianceScore: complianceReport?.overallScore || 0,
      },
      results: testResults,
      wcagReport: complianceReport,
      timestamp: new Date(),
    };
  }, [testResults, complianceReport]);

  return {
    testResults,
    isRunning,
    currentTest,
    complianceReport,
    runComprehensiveTest,
    runQuickAccessibilityTest,
    testComponentAccessibility,
    clearResults,
    generateReport,
  };
}

// Accessibility testing dashboard component
export interface AccessibilityTestingDashboardProps {
  className?: string;
}

export function AccessibilityTestingDashboard({ className = '' }: AccessibilityTestingDashboardProps) {
  const {
    testResults,
    isRunning,
    currentTest,
    complianceReport,
    runComprehensiveTest,
    runQuickAccessibilityTest,
    clearResults,
    generateReport,
  } = useAccessibilityTesting();

  const [showDetails, setShowDetails] = useState(false);
  const [filterStatus, setFilterStatus] = useState<'all' | 'pass' | 'fail' | 'warning' | 'review'>('all');
  const [filterImpact, setFilterImpact] = useState<'all' | 'critical' | 'serious' | 'moderate' | 'minor'>('all');

  const filteredResults = testResults.filter(result => {
    if (filterStatus !== 'all' && result.status !== filterStatus) return false;
    if (filterImpact !== 'all' && result.impact !== filterImpact) return false;
    return true;
  });

  const report = generateReport();

  return React.createElement('div', {
    className: `accessibility-testing-dashboard ${className}`,
    role: 'region',
    'aria-label': 'Accessibility testing dashboard',
  }, [
    // Header
    React.createElement('div', { key: 'header', className: 'dashboard-header' }, [
      React.createElement('h2', { key: 'title' }, 'Accessibility Testing Dashboard'),
      
      // Summary stats
      React.createElement('div', { key: 'summary', className: 'test-summary' }, [
        React.createElement('div', { key: 'total', className: 'summary-item' },
          React.createElement('span', { className: 'summary-label' }, 'Total Tests: '),
          React.createElement('span', { className: 'summary-value' }, report.summary.total)
        ),
        React.createElement('div', { key: 'passed', className: 'summary-item passed' },
          React.createElement('span', { className: 'summary-label' }, 'Passed: '),
          React.createElement('span', { className: 'summary-value' }, report.summary.passed)
        ),
        React.createElement('div', { key: 'failed', className: 'summary-item failed' },
          React.createElement('span', { className: 'summary-label' }, 'Failed: '),
          React.createElement('span', { className: 'summary-value' }, report.summary.failed)
        ),
        complianceReport && React.createElement('div', { key: 'score', className: 'summary-item score' },
          React.createElement('span', { className: 'summary-label' }, 'Compliance Score: '),
          React.createElement('span', { className: 'summary-value' }, `${complianceReport.overallScore}%`)
        ),
      ]),
    ]),
    
    // Controls
    React.createElement('div', { key: 'controls', className: 'test-controls' }, [
      React.createElement('button', {
        key: 'quick-test',
        onClick: runQuickAccessibilityTest,
        disabled: isRunning,
        className: 'test-button quick',
      }, 'Run Quick Test'),
      
      React.createElement('button', {
        key: 'comprehensive-test',
        onClick: () => runComprehensiveTest(),
        disabled: isRunning,
        className: 'test-button comprehensive',
      }, 'Run Comprehensive Test'),
      
      React.createElement('button', {
        key: 'clear-results',
        onClick: clearResults,
        disabled: isRunning,
        className: 'test-button clear',
      }, 'Clear Results'),
      
      React.createElement('button', {
        key: 'toggle-details',
        onClick: () => setShowDetails(!showDetails),
        className: 'test-button toggle',
        'aria-expanded': showDetails,
      }, showDetails ? 'Hide Details' : 'Show Details'),
    ]),
    
    // Current test status
    isRunning && React.createElement('div', {
      key: 'status',
      className: 'test-status',
      role: 'status',
      'aria-live': 'polite',
    }, [
      React.createElement('div', { className: 'status-indicator' }),
      React.createElement('span', { className: 'status-text' }, currentTest || 'Running tests...'),
    ]),
    
    // Filters
    showDetails && React.createElement('div', { key: 'filters', className: 'test-filters' }, [
      React.createElement('div', { key: 'status-filter', className: 'filter-group' },
        React.createElement('label', { htmlFor: 'status-filter' }, 'Filter by Status:'),
        React.createElement('select', {
          id: 'status-filter',
          value: filterStatus,
          onChange: (e: React.ChangeEvent<HTMLSelectElement>) => setFilterStatus(e.target.value as any),
        }, [
          React.createElement('option', { key: 'all', value: 'all' }, 'All'),
          React.createElement('option', { key: 'pass', value: 'pass' }, 'Pass'),
          React.createElement('option', { key: 'fail', value: 'fail' }, 'Fail'),
          React.createElement('option', { key: 'warning', value: 'warning' }, 'Warning'),
          React.createElement('option', { key: 'review', value: 'review' }, 'Review'),
        ])
      ),
      
      React.createElement('div', { key: 'impact-filter', className: 'filter-group' },
        React.createElement('label', { htmlFor: 'impact-filter' }, 'Filter by Impact:'),
        React.createElement('select', {
          id: 'impact-filter',
          value: filterImpact,
          onChange: (e: React.ChangeEvent<HTMLSelectElement>) => setFilterImpact(e.target.value as any),
        }, [
          React.createElement('option', { key: 'all', value: 'all' }, 'All'),
          React.createElement('option', { key: 'critical', value: 'critical' }, 'Critical'),
          React.createElement('option', { key: 'serious', value: 'serious' }, 'Serious'),
          React.createElement('option', { key: 'moderate', value: 'moderate' }, 'Moderate'),
          React.createElement('option', { key: 'minor', value: 'minor' }, 'Minor'),
        ])
      ),
    ]),
    
    // Test results
    showDetails && React.createElement('div', { key: 'results', className: 'test-results' }, [
      React.createElement('h3', { key: 'results-title' }, `Test Results (${filteredResults.length})`),
      
      filteredResults.length === 0 
        ? React.createElement('p', { key: 'no-results', className: 'no-results' }, 'No test results found')
        : React.createElement('ul', { key: 'results-list', className: 'results-list' },
          filteredResults.map(result =>
            React.createElement('li', {
              key: result.id,
              className: `result-item ${result.status} ${result.impact}`,
            }, [
              React.createElement('div', { key: 'header', className: 'result-header' }, [
                React.createElement('span', { key: 'name', className: 'result-name' }, result.name),
                React.createElement('span', { key: 'status', className: `result-status ${result.status}` }, result.status),
                React.createElement('span', { key: 'impact', className: `result-impact ${result.impact}` }, result.impact),
              ]),
              
              React.createElement('div', { key: 'description', className: 'result-description' }, result.description),
              
              result.wcagCriteria.length > 0 && React.createElement('div', {
                key: 'criteria',
                className: 'result-criteria',
              }, [
                React.createElement('span', { key: 'label' }, 'WCAG Criteria: '),
                React.createElement('span', { key: 'list' }, result.wcagCriteria.join(', ')),
              ]),
              
              result.recommendation && React.createElement('div', {
                key: 'recommendation',
                className: 'result-recommendation',
              }, [
                React.createElement('span', { key: 'label' }, 'Recommendation: '),
                React.createElement('span', { key: 'text' }, result.recommendation),
              ]),
            ])
          )
        ),
    ]),
  ]);
}
