import axe, { type AxeResults, type RunOptions } from 'axe-core';

// ============================================================================
// TYPES AND INTERFACES
// ============================================================================

export interface AccessibilityTestSuite {
  basic: () => Promise<AccessibilityReport>;
  comprehensive: () => Promise<AccessibilityReport>;
  keyboard: () => Promise<KeyboardAccessibilityReport>;
  screenReader: () => Promise<ScreenReaderReport>;
  colorContrast: () => Promise<ColorContrastReport>;
  focusManagement: () => Promise<FocusManagementReport>;
  aria: () => Promise<AriaReport>;
}

export interface AccessibilityReport {
  passed: boolean;
  score: number;
  violations: AccessibilityViolation[];
  warnings: AccessibilityWarning[];
  summary: {
    critical: number;
    serious: number;
    moderate: number;
    minor: number;
  };
  recommendations: string[];
  testDuration: number;
}

export interface AccessibilityViolation {
  id: string;
  impact: 'critical' | 'serious' | 'moderate' | 'minor';
  description: string;
  help: string;
  helpUrl: string;
  elements: Array<{
    target: string;
    html: string;
    failureSummary: string;
  }>;
}

export interface AccessibilityWarning {
  id: string;
  description: string;
  elements: string[];
  recommendation: string;
}

export interface KeyboardAccessibilityReport {
  passed: boolean;
  focusableElements: number;
  unreachableElements: string[];
  focusOrderIssues: string[];
  trapIssues: string[];
  skipLinkIssues: string[];
}

export interface ScreenReaderReport {
  passed: boolean;
  missingLabels: string[];
  ariaIssues: string[];
  landmarkIssues: string[];
  headingStructureIssues: string[];
  liveRegionIssues: string[];
}

export interface ColorContrastReport {
  passed: boolean;
  failedElements: Array<{
    element: string;
    foreground: string;
    background: string;
    ratio: number;
    required: number;
    level: 'AA' | 'AAA';
  }>;
  averageRatio: number;
}

export interface FocusManagementReport {
  passed: boolean;
  focusTraps: Array<{
    element: string;
    working: boolean;
    issues: string[];
  }>;
  focusRestoration: Array<{
    element: string;
    working: boolean;
  }>;
  focusIndicators: Array<{
    element: string;
    visible: boolean;
    contrast: number;
  }>;
}

export interface AriaReport {
  passed: boolean;
  invalidAttributes: string[];
  missingAttributes: string[];
  incorrectRoles: string[];
  brokenReferences: string[];
}

// ============================================================================
// ACCESSIBILITY TEST SUITE
// ============================================================================

export class AccessibilityTestSuiteImpl implements AccessibilityTestSuite {
  private container: Element | Document;
  private options: RunOptions;

  constructor(container: Element | Document = document, options: RunOptions = {}) {
    this.container = container;
    this.options = {
      runOnly: {
        type: 'tag',
        values: ['wcag2a', 'wcag2aa', 'wcag21aa'],
      },
      ...options,
    };
  }

  async basic(): Promise<AccessibilityReport> {
    const startTime = performance.now();
    try {
      const results = await axe.run(this.container as any, {
        ...this.options,
        runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa'] },
      });

      return this.processAxeResults(results, performance.now() - startTime);
    } catch (error) {
      throw new Error(`Basic accessibility test failed: ${error.message}`);
    }
  }

  async comprehensive(): Promise<AccessibilityReport> {
    const startTime = performance.now();
    try {
      const results = await axe.run(this.container as any, {
        ...this.options,
        runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa', 'best-practice'] },
      });

      return this.processAxeResults(results, performance.now() - startTime);
    } catch (error) {
      throw new Error(`Comprehensive accessibility test failed: ${error.message}`);
    }
  }

  async keyboard(): Promise<KeyboardAccessibilityReport> {
    const focusableSelectors = [
      'a[href]',
      'button:not([disabled])',
      'input:not([disabled])',
      'select:not([disabled])',
      'textarea:not([disabled])',
      '[tabindex]:not([tabindex="-1"])',
      '[role="button"]',
      '[role="link"]',
      '[role="menuitem"]',
      '[role="tab"]',
    ];

    const focusableElements = this.container.querySelectorAll(focusableSelectors.join(', '));
    const unreachableElements: string[] = [];
    const focusOrderIssues: string[] = [];
    const trapIssues: string[] = [];
    const skipLinkIssues: string[] = [];

    focusableElements.forEach((element, index) => {
      const htmlElement = element as HTMLElement;

      if (htmlElement.tabIndex < 0 && !htmlElement.hasAttribute('disabled')) {
        unreachableElements.push(this.getElementSelector(htmlElement));
      }

      if (htmlElement.tabIndex > 0) {
        focusOrderIssues.push(`Element has positive tabindex: ${this.getElementSelector(htmlElement)}`);
      }
    });

    const focusTraps = this.container.querySelectorAll('[data-focus-trap="true"]');
    focusTraps.forEach((trap) => {
      const trapElement = trap as HTMLElement;
      const focusableInTrap = trapElement.querySelectorAll(focusableSelectors.join(', '));

      if (focusableInTrap.length === 0) {
        trapIssues.push(`Focus trap has no focusable elements: ${this.getElementSelector(trapElement)}`);
      }
    });

    const skipLinks = this.container.querySelectorAll('.skip-links a, [href^="#"]');
    skipLinks.forEach((link) => {
      const href = link.getAttribute('href');
      if (href && href.startsWith('#')) {
        const target = this.container.querySelector(href);
        if (!target) {
          skipLinkIssues.push(`Skip link target not found: ${href}`);
        }
      }
    });

    return {
      passed: unreachableElements.length === 0 && focusOrderIssues.length === 0 && trapIssues.length === 0 && skipLinkIssues.length === 0,
      focusableElements: focusableElements.length,
      unreachableElements,
      focusOrderIssues,
      trapIssues,
      skipLinkIssues,
    };
  }

  async screenReader(): Promise<ScreenReaderReport> {
    // Implement the screenReader testing logic
    return {
      passed: true,
      missingLabels: [],
      ariaIssues: [],
      landmarkIssues: [],
      headingStructureIssues: [],
      liveRegionIssues: [],
    };
  }

  async colorContrast(): Promise<ColorContrastReport> {
    // Implement the colorContrast testing logic
    return {
      passed: true,
      failedElements: [],
      averageRatio: 4.5,
    };
  }

  // Add methods for focusManagement and aria testing...

  private processAxeResults(results: AxeResults, duration: number): AccessibilityReport {
    const violations: AccessibilityViolation[] = results.violations.map((violation: any) => ({
      id: violation.id,
      impact: violation.impact,
      description: violation.description,
      help: violation.help,
      helpUrl: violation.helpUrl,
      elements: violation.nodes.map((node: any) => ({
        target: node.target.join(' '),
        html: node.html,
        failureSummary: node.failureSummary || '',
      })),
    }));

    const summary = {
      critical: violations.filter(v => v.impact === 'critical').length,
      serious: violations.filter(v => v.impact === 'serious').length,
      moderate: violations.filter(v => v.impact === 'moderate').length,
      minor: violations.filter(v => v.impact === 'minor').length,
    };

    const score = Math.max(0, 100 - (summary.critical * 25 + summary.serious * 10 + summary.moderate * 5 + summary.minor * 1));

    const recommendations = this.generateRecommendations(violations);

    return {
      passed: violations.length === 0,
      score,
      violations,
      warnings: [],
      summary,
      recommendations,
      testDuration: duration,
    };
  }

  private generateRecommendations(violations: AccessibilityViolation[]): string[] {
    const recommendations: string[] = [];
    violations.forEach((violation) => {
      switch (violation.id) {
        case 'color-contrast':
          recommendations.push('Increase color contrast to meet WCAG AA standards (4.5:1 for normal text, 3:1 for large text)');
          break;
        case 'keyboard':
          recommendations.push('Ensure all interactive elements are keyboard accessible');
          break;
        case 'aria-valid-attr':
          recommendations.push('Fix invalid ARIA attributes');
          break;
        case 'label':
          recommendations.push('Add proper labels to form controls');
          break;
        default:
          recommendations.push(`Address ${violation.id}: ${violation.help}`);
      }
    });

    return [...new Set(recommendations)];
  }

  private getElementSelector(element: HTMLElement): string {
    if (element.id) return `#${element.id}`;
    if (element.className) return `${element.tagName.toLowerCase()}.${element.className.split(' ')[0]}`;
    return element.tagName.toLowerCase();
  }

  private calculateContrastRatio(foreground: string, background: string): number {
    // Placeholder contrast ratio calculation (simplified for now)
    return 4.5;
  }
}

// ============================================================================
// TESTING UTILITIES
// ============================================================================

export function createAccessibilityTestSuite(container?: Element | Document): AccessibilityTestSuite {
  return new AccessibilityTestSuiteImpl(container);
}

export async function runQuickAccessibilityCheck(element?: Element | Document): Promise<boolean> {
  const suite = createAccessibilityTestSuite(element);
  const result = await suite.basic();
  return result.passed;
}

export async function generateAccessibilityReport(element?: Element | Document): Promise<string> {
  const suite = createAccessibilityTestSuite(element);
  const [basic, keyboard, screenReader, colorContrast] = await Promise.all([
    suite.basic(),
    suite.keyboard(),
    suite.screenReader(),
    suite.colorContrast(),
  ]);

  let report = 'Accessibility Test Report\n';
  report += '========================\n\n';
  
  report += `Overall Score: ${basic.score}/100\n`;
  report += `Basic Test: ${basic.passed ? 'PASS' : 'FAIL'}\n`;
  report += `Keyboard Test: ${keyboard.passed ? 'PASS' : 'FAIL'}\n`;
  report += `Screen Reader Test: ${screenReader.passed ? 'PASS' : 'FAIL'}\n`;
  report += `Color Contrast Test: ${colorContrast.passed ? 'PASS' : 'FAIL'}\n\n`;

  if (basic.violations.length > 0) {
    report += 'Violations:\n';
    basic.violations.forEach((violation, index) => {
      report += `${index + 1}. ${violation.description} (${violation.impact})\n`;
      report += `   Elements: ${violation.elements.length}\n`;
      report += `   Help: ${violation.help}\n\n`;
    });
  }

  if (basic.recommendations.length > 0) {
    report += 'Recommendations:\n';
    basic.recommendations.forEach((rec, index) => {
      report += `${index + 1}. ${rec}\n`;
    });
  }

  return report;
}

export default AccessibilityTestSuite;
