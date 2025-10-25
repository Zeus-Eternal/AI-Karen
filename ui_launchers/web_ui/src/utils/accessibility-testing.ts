/**
 * Accessibility Testing Utilities
 * 
 * Comprehensive utilities for testing accessibility in components and applications.
 * Includes automated testing helpers, manual testing guides, and validation functions.
 */

import axe, { type AxeResults, type RunOptions } from 'axe-core';

// ============================================================================
// TYPES AND INTERFACES
// ============================================================================

export interface AccessibilityTestOptions {
  /** Custom axe-core rules configuration */
  rules?: RunOptions['rules'];
  /** Tags to include in testing */
  tags?: string[];
  /** Elements to exclude from testing */
  exclude?: string[];
  /** Include only specific elements */
  include?: string[];
  /** Custom timeout for tests */
  timeout?: number;
  /** Enable detailed reporting */
  detailedReport?: boolean;
}

export interface AccessibilityReport {
  /** Test results from axe-core */
  results: AxeResults;
  /** Summary of violations */
  summary: {
    violations: number;
    passes: number;
    incomplete: number;
    inapplicable: number;
  };
  /** Detailed violation information */
  violations: AccessibilityViolation[];
  /** Performance metrics */
  performance: {
    duration: number;
    rulesRun: number;
  };
}

export interface AccessibilityViolation {
  /** Rule ID that was violated */
  id: string;
  /** Impact level of the violation */
  impact: 'minor' | 'moderate' | 'serious' | 'critical';
  /** Description of the violation */
  description: string;
  /** Help text for fixing the violation */
  help: string;
  /** URL to more information */
  helpUrl: string;
  /** Elements that have the violation */
  nodes: Array<{
    target: string[];
    html: string;
    failureSummary: string;
  }>;
}

export interface KeyboardTestResult {
  /** Whether all interactive elements are reachable */
  allReachable: boolean;
  /** Elements that are not keyboard accessible */
  unreachableElements: string[];
  /** Focus order issues */
  focusOrderIssues: string[];
  /** Missing focus indicators */
  missingFocusIndicators: string[];
}

export interface ScreenReaderTestResult {
  /** Whether all content has appropriate labels */
  hasLabels: boolean;
  /** Elements missing labels */
  missingLabels: string[];
  /** ARIA usage issues */
  ariaIssues: string[];
  /** Landmark structure issues */
  landmarkIssues: string[];
}

// ============================================================================
// AUTOMATED ACCESSIBILITY TESTING
// ============================================================================

/**
 * Run comprehensive accessibility tests on a DOM element
 */
export async function runAccessibilityTest(
  element: Element | Document = document,
  options: AccessibilityTestOptions = {}
): Promise<AccessibilityReport> {
  const startTime = performance.now();

  // Configure axe-core options
  const axeOptions: any = {
    rules: {
      // Default rule configuration
      'color-contrast': { enabled: true },
      'focus-order-semantics': { enabled: true },
      'keyboard-navigation': { enabled: true },
      'aria-valid-attr': { enabled: true },
      'aria-valid-attr-value': { enabled: true },
      'aria-roles': { enabled: true },
      'form-field-multiple-labels': { enabled: true },
      'heading-order': { enabled: true },
      'landmark-unique': { enabled: true },
      'link-name': { enabled: true },
      'list': { enabled: true },
      'listitem': { enabled: true },
      'page-has-heading-one': { enabled: true },
      'region': { enabled: true },
      'skip-link': { enabled: true },
      'tabindex': { enabled: true },
      ...options.rules,
    },
    timeout: options.timeout || 10000,
  };

  // Add tags if provided
  if (options.tags) {
    axeOptions.runOnly = {
      type: 'tag',
      values: options.tags,
    };
  } else {
    axeOptions.runOnly = {
      type: 'tag',
      values: ['wcag2a', 'wcag2aa', 'wcag21aa', 'best-practice'],
    };
  }

  // Add include/exclude selectors if provided
  if (options.include) {
    axeOptions.include = options.include;
  }
  if (options.exclude) {
    axeOptions.exclude = options.exclude;
  }

  try {
    // Run axe-core analysis
    const results = await axe.run(element as any, axeOptions) as unknown as AxeResults;
    const endTime = performance.now();

    // Process results
    const violations: AccessibilityViolation[] = results.violations.map((violation: any) => ({
      id: violation.id,
      impact: violation.impact as AccessibilityViolation['impact'],
      description: violation.description,
      help: violation.help,
      helpUrl: violation.helpUrl,
      nodes: violation.nodes.map((node: any) => ({
        target: node.target,
        html: node.html,
        failureSummary: node.failureSummary || '',
      })),
    }));

    const report: AccessibilityReport = {
      results,
      summary: {
        violations: results.violations.length,
        passes: results.passes.length,
        incomplete: results.incomplete.length,
        inapplicable: results.inapplicable.length,
      },
      violations,
      performance: {
        duration: endTime - startTime,
        rulesRun: Object.keys(axeOptions.rules || {}).length,
      },
    };

    return report;
  } catch (error) {
    throw new Error(`Accessibility test failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Test keyboard accessibility of interactive elements
 */
export function testKeyboardAccessibility(
  container: Element = document.body
): KeyboardTestResult {
  const interactiveSelectors = [
    'button',
    'a[href]',
    'input:not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    '[tabindex]:not([tabindex="-1"])',
    '[role="button"]',
    '[role="link"]',
    '[role="menuitem"]',
    '[role="tab"]',
  ];

  const interactiveElements = container.querySelectorAll(interactiveSelectors.join(', '));
  const unreachableElements: string[] = [];
  const focusOrderIssues: string[] = [];
  const missingFocusIndicators: string[] = [];

  interactiveElements.forEach((element, index) => {
    const htmlElement = element as HTMLElement;
    
    // Check if element is focusable
    const tabIndex = htmlElement.tabIndex;
    const isDisabled = htmlElement.hasAttribute('disabled') || 
                      htmlElement.getAttribute('aria-disabled') === 'true';
    
    if (tabIndex < 0 && !isDisabled) {
      unreachableElements.push(`${element.tagName.toLowerCase()}[${index}]`);
    }

    // Check focus order (simplified check)
    if (tabIndex > 0) {
      focusOrderIssues.push(`${element.tagName.toLowerCase()}[${index}] has positive tabindex`);
    }

    // Check for focus indicators (simplified check)
    const computedStyle = window.getComputedStyle(htmlElement, ':focus');
    const hasOutline = computedStyle.outline !== 'none' && computedStyle.outline !== '';
    const hasBoxShadow = computedStyle.boxShadow !== 'none';
    const hasCustomFocus = htmlElement.classList.contains('focus-visible') ||
                          htmlElement.classList.contains('focus');

    if (!hasOutline && !hasBoxShadow && !hasCustomFocus) {
      missingFocusIndicators.push(`${element.tagName.toLowerCase()}[${index}]`);
    }
  });

  return {
    allReachable: unreachableElements.length === 0,
    unreachableElements,
    focusOrderIssues,
    missingFocusIndicators,
  };
}

/**
 * Test screen reader accessibility
 */
export function testScreenReaderAccessibility(
  container: Element = document.body
): ScreenReaderTestResult {
  const missingLabels: string[] = [];
  const ariaIssues: string[] = [];
  const landmarkIssues: string[] = [];

  // Check form controls for labels
  const formControls = container.querySelectorAll('input, select, textarea');
  formControls.forEach((control, index) => {
    const htmlControl = control as HTMLElement;
    const id = htmlControl.id;
    const ariaLabel = htmlControl.getAttribute('aria-label');
    const ariaLabelledBy = htmlControl.getAttribute('aria-labelledby');
    const hasLabel = id && container.querySelector(`label[for="${id}"]`);

    if (!ariaLabel && !ariaLabelledBy && !hasLabel) {
      missingLabels.push(`${control.tagName.toLowerCase()}[${index}]`);
    }
  });

  // Check images for alt text
  const images = container.querySelectorAll('img');
  images.forEach((img, index) => {
    const altText = img.getAttribute('alt');
    const ariaLabel = img.getAttribute('aria-label');
    const role = img.getAttribute('role');

    if (!altText && !ariaLabel && role !== 'presentation' && role !== 'none') {
      missingLabels.push(`img[${index}]`);
    }
  });

  // Check ARIA usage
  const elementsWithAria = container.querySelectorAll('[aria-*]');
  elementsWithAria.forEach((element, index) => {
    const ariaAttributes = Array.from(element.attributes)
      .filter(attr => attr.name.startsWith('aria-'));

    ariaAttributes.forEach(attr => {
      // Basic ARIA validation (simplified)
      if (attr.name === 'aria-describedby' || attr.name === 'aria-labelledby') {
        const ids = attr.value.split(' ');
        ids.forEach(id => {
          if (!container.querySelector(`#${id}`)) {
            ariaIssues.push(`${element.tagName.toLowerCase()}[${index}] references non-existent ID: ${id}`);
          }
        });
      }
    });
  });

  // Check landmark structure
  const mainLandmarks = container.querySelectorAll('main, [role="main"]');
  
  if (mainLandmarks.length === 0) {
    landmarkIssues.push('No main landmark found');
  } else if (mainLandmarks.length > 1) {
    landmarkIssues.push('Multiple main landmarks found');
  }

  return {
    hasLabels: missingLabels.length === 0,
    missingLabels,
    ariaIssues,
    landmarkIssues,
  };
}

// ============================================================================
// ACCESSIBILITY VALIDATION HELPERS
// ============================================================================

/**
 * Validate color contrast ratio
 */
export function validateColorContrast(
  foreground: string,
  background: string,
  fontSize: number = 16,
  fontWeight: number = 400
): { ratio: number; passes: { aa: boolean; aaa: boolean } } {
  // Convert colors to RGB
  const fgRgb = hexToRgb(foreground);
  const bgRgb = hexToRgb(background);

  if (!fgRgb || !bgRgb) {
    throw new Error('Invalid color format');
  }

  // Calculate relative luminance
  const fgLuminance = getRelativeLuminance(fgRgb);
  const bgLuminance = getRelativeLuminance(bgRgb);

  // Calculate contrast ratio
  const ratio = (Math.max(fgLuminance, bgLuminance) + 0.05) / 
                (Math.min(fgLuminance, bgLuminance) + 0.05);

  // Determine if it's large text
  const isLargeText = fontSize >= 18 || (fontSize >= 14 && fontWeight >= 700);

  // WCAG requirements
  const aaRequirement = isLargeText ? 3 : 4.5;
  const aaaRequirement = isLargeText ? 4.5 : 7;

  return {
    ratio: Math.round(ratio * 100) / 100,
    passes: {
      aa: ratio >= aaRequirement,
      aaa: ratio >= aaaRequirement,
    },
  };
}

/**
 * Validate ARIA attributes
 */
export function validateAriaAttributes(element: Element): string[] {
  const issues: string[] = [];
  const ariaAttributes = Array.from(element.attributes)
    .filter(attr => attr.name.startsWith('aria-'));

  ariaAttributes.forEach(attr => {
    const name = attr.name;
    const value = attr.value;

    // Check for empty values
    if (!value.trim()) {
      issues.push(`${name} has empty value`);
      return;
    }

    // Validate specific ARIA attributes
    switch (name) {
      case 'aria-expanded':
      case 'aria-checked':
      case 'aria-selected':
      case 'aria-pressed':
      case 'aria-hidden':
        if (!['true', 'false'].includes(value)) {
          issues.push(`${name} must be "true" or "false"`);
        }
        break;

      case 'aria-level':
      case 'aria-setsize':
      case 'aria-posinset':
        if (!/^\d+$/.test(value) || parseInt(value) < 1) {
          issues.push(`${name} must be a positive integer`);
        }
        break;

      case 'aria-describedby':
      case 'aria-labelledby':
      case 'aria-controls':
        // Check if referenced IDs exist (simplified check)
        const ids = value.split(' ');
        ids.forEach(id => {
          if (id && !document.getElementById(id)) {
            issues.push(`${name} references non-existent ID: ${id}`);
          }
        });
        break;
    }
  });

  return issues;
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Convert hex color to RGB
 */
function hexToRgb(hex: string): { r: number; g: number; b: number } | null {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16),
  } : null;
}

/**
 * Calculate relative luminance
 */
function getRelativeLuminance({ r, g, b }: { r: number; g: number; b: number }): number {
  const [rs, gs, bs] = [r, g, b].map(c => {
    c = c / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });

  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
}

/**
 * Generate accessibility report summary
 */
export function generateAccessibilityReportSummary(report: AccessibilityReport): string {
  const { summary, violations, performance } = report;
  
  let reportText = `Accessibility Test Report\n`;
  reportText += `========================\n\n`;
  reportText += `Summary:\n`;
  reportText += `- Violations: ${summary.violations}\n`;
  reportText += `- Passes: ${summary.passes}\n`;
  reportText += `- Incomplete: ${summary.incomplete}\n`;
  reportText += `- Not Applicable: ${summary.inapplicable}\n`;
  reportText += `- Test Duration: ${Math.round(performance.duration)}ms\n\n`;

  if (violations.length > 0) {
    reportText += `Violations:\n`;
    violations.forEach((violation, index) => {
      reportText += `${index + 1}. ${violation.description} (${violation.impact})\n`;
      reportText += `   Help: ${violation.help}\n`;
      reportText += `   More info: ${violation.helpUrl}\n`;
      reportText += `   Affected elements: ${violation.nodes.length}\n\n`;
    });
  }

  return reportText;
}

/**
 * Create accessibility testing configuration for different scenarios
 */
export const accessibilityTestConfigs = {
  // Basic accessibility test
  basic: {
    tags: ['wcag2a', 'wcag2aa'],
    rules: {
      'color-contrast': { enabled: true },
      'keyboard-navigation': { enabled: true },
      'aria-valid-attr': { enabled: true },
    },
  },

  // Comprehensive accessibility test
  comprehensive: {
    tags: ['wcag2a', 'wcag2aa', 'wcag21aa', 'best-practice'],
    rules: {
      'color-contrast': { enabled: true },
      'focus-order-semantics': { enabled: true },
      'keyboard-navigation': { enabled: true },
      'aria-valid-attr': { enabled: true },
      'aria-valid-attr-value': { enabled: true },
      'form-field-multiple-labels': { enabled: true },
      'heading-order': { enabled: true },
      'landmark-unique': { enabled: true },
      'page-has-heading-one': { enabled: true },
    },
  },

  // Form-specific accessibility test
  forms: {
    tags: ['wcag2a', 'wcag2aa'],
    rules: {
      'label': { enabled: true },
      'form-field-multiple-labels': { enabled: true },
      'aria-valid-attr': { enabled: true },
      'aria-required-attr': { enabled: true },
    },
  },

  // Navigation-specific accessibility test
  navigation: {
    tags: ['wcag2a', 'wcag2aa'],
    rules: {
      'link-name': { enabled: true },
      'skip-link': { enabled: true },
      'landmark-unique': { enabled: true },
      'region': { enabled: true },
    },
  },
};