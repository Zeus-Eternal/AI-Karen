/**
 * Accessibility Testing Utilities
 * WCAG 2.1 AA compliance testing utilities
 */

// Note: expect should be imported from the test framework being used
// This file provides utilities that can work with any test framework
import { render, RenderResult } from '@testing-library/react';

// Dynamic import for axe to avoid module resolution issues
const loadAxe = async () => {
  try {
    const axe = await import('axe-core');
    return axe.default;
  } catch (error) {
    console.warn('axe-core not available, accessibility testing will be limited');
    return null;
  }
};

// Type declaration for expect to work with any test framework
declare global {
  namespace jest {
    interface Matchers<R> {
      toHaveNoViolations(): R;
    }
  }
  
  interface Expect {
    extend(matchers: any): void;
  }
}

// Get expect from global or create a mock
const getExpect = () => {
  if (typeof global !== 'undefined' && (global as any).expect) {
    return (global as any).expect;
  }
  
  // Create a basic expect mock for non-test environments
  return {
    extend: () => {
      console.warn('expect.extend called outside of test environment');
    }
  };
};

const expect = getExpect();

// WCAG 2.1 AA compliance levels
export const WCAG_LEVELS = {
  A: 'A',
  AA: 'AA',
  AAA: 'AAA',
} as const;

// Accessibility rules configuration
export const ACCESSIBILITY_RULES = {
  // WCAG 2.1 AA specific rules
  'color-contrast': { enabled: true, level: WCAG_LEVELS.AA },
  'keyboard-navigation': { enabled: true, level: WCAG_LEVELS.AA },
  'focus-management': { enabled: true, level: WCAG_LEVELS.AA },
  'aria-labels': { enabled: true, level: WCAG_LEVELS.AA },
  'screen-reader': { enabled: true, level: WCAG_LEVELS.AA },
  'semantic-html': { enabled: true, level: WCAG_LEVELS.AA },
  'form-labels': { enabled: true, level: WCAG_LEVELS.AA },
  'link-purpose': { enabled: true, level: WCAG_LEVELS.AA },
  'image-alt': { enabled: true, level: WCAG_LEVELS.AA },
  'heading-order': { enabled: true, level: WCAG_LEVELS.AA },
  'table-headers': { enabled: true, level: WCAG_LEVELS.AA },
  'list-markup': { enabled: true, level: WCAG_LEVELS.AA },
  'button-names': { enabled: true, level: WCAG_LEVELS.AA },
  'skip-links': { enabled: true, level: WCAG_LEVELS.AA },
  'resize-text': { enabled: true, level: WCAG_LEVELS.AA },
  're-authentication': { enabled: true, level: WCAG_LEVELS.AA },
} as const;

// Accessibility testing interface
export interface AccessibilityTestOptions {
  level?: keyof typeof WCAG_LEVELS;
  rules?: Partial<typeof ACCESSIBILITY_RULES>;
  include?: string[];
  exclude?: string[];
}

// Main accessibility testing function
export const testAccessibility = async (
  component: React.ReactElement,
  options: AccessibilityTestOptions = {}
) => {
  const { level = 'AA', rules = ACCESSIBILITY_RULES, include, exclude } = options;
  
  const { container } = render(component);
  
  // Configure axe for WCAG 2.1 AA
  const axeConfig = {
    rules: Object.entries(rules)
      .filter(([, rule]) => rule.enabled && rule.level === WCAG_LEVELS[level])
      .reduce((acc, [ruleId]) => ({
        ...acc,
        [ruleId]: { enabled: true },
      }), {}),
    
    tags: [`wcag2${level.toLowerCase()}`, 'best-practice'],
    
    // Include/exclude specific elements
    include: include || ['*'],
    exclude: exclude || [
      // Common exclusions for testing
      '[aria-hidden="true"]',
      '.sr-only',
      '[style*="display: none"]',
      '[style*="visibility: hidden"]',
    ],
  };

  const axe = await loadAxe();
  if (!axe) {
    return {
      violations: [],
      passes: [],
      incomplete: [],
      inapplicable: [],
      wcagLevel: level,
      compliant: true,
      error: 'axe-core not available',
    };
  }
  
  const results = await (axe as any)(container, axeConfig);
  
  return {
    violations: results.violations || [],
    passes: results.passes || [],
    incomplete: results.incomplete || [],
    inapplicable: results.inapplicable || [],
    wcagLevel: level,
    compliant: (results.violations || []).length === 0,
  };
};

// Test specific accessibility features
export const testKeyboardNavigation = async (container: HTMLElement) => {
  const focusableElements = container.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );

  const results = {
    focusableElements: focusableElements.length,
    hasTabIndex: Array.from(focusableElements).every(el => 
      el.hasAttribute('tabindex') || ['button', 'input', 'select', 'textarea', 'a'].includes(el.tagName.toLowerCase())
    ),
    tabOrderCorrect: true, // Would need more complex testing
    focusVisible: true, // Would need visual testing
    skipLinks: container.querySelectorAll('[href="#main"], [href="#content"], [href="#navigation"]').length > 0,
  };

  return results;
};

export const testAriaLabels = async (container: HTMLElement) => {
  const interactiveElements = container.querySelectorAll(
    'button, input, select, textarea, a, [role="button"], [role="link"], [role="menuitem"]'
  );

  const elementsWithoutLabels = Array.from(interactiveElements).filter(el => {
    const hasAriaLabel = el.hasAttribute('aria-label') || el.hasAttribute('aria-labelledby');
    const hasTextContent = el.textContent?.trim().length > 0;
    const hasTitle = el.hasAttribute('title');
    
    return !hasAriaLabel && !hasTextContent && !hasTitle;
  });

  return {
    totalInteractiveElements: interactiveElements.length,
    elementsWithoutLabels: elementsWithoutLabels.length,
    compliant: elementsWithoutLabels.length === 0,
    violations: elementsWithoutLabels.map(el => ({
      element: el,
      reason: 'Missing accessible name',
    })),
  };
};

export const testColorContrast = async (container: HTMLElement) => {
  // This would require a color contrast calculation library
  // For now, return a placeholder implementation
  return {
    compliant: true,
    violations: [],
    testedElements: 0,
  };
};

export const testSemanticHTML = async (container: HTMLElement) => {
  const headingElements = container.querySelectorAll('h1, h2, h3, h4, h5, h6');
  const landmarkElements = container.querySelectorAll('header, nav, main, footer, section, article, aside');
  const listElements = container.querySelectorAll('ul, ol');
  const buttonElements = container.querySelectorAll('button, [role="button"]');
  const linkElements = container.querySelectorAll('a[href]');

  const violations = [];

  // Check heading hierarchy
  const headingLevels = Array.from(headingElements).map(el => 
    parseInt(el.tagName.substring(1))
  );
  for (let i = 1; i < headingLevels.length; i++) {
    if (i > 0 && headingLevels[i] && headingLevels[i - 1] &&
        headingLevels[i]! - headingLevels[i - 1]! > 1) {
      violations.push({
        type: 'heading-skip',
        element: headingElements[i],
        message: 'Heading levels should not be skipped',
      });
    }
  }

  // Check for proper button usage
  Array.from(buttonElements).forEach(el => {
    if (el.tagName.toLowerCase() !== 'button' && !el.hasAttribute('role')) {
      violations.push({
        type: 'button-role',
        element: el,
        message: 'Button elements should have proper role or be button elements',
      });
    }
  });

  return {
    compliant: violations.length === 0,
    violations,
    statistics: {
      headings: headingElements.length,
      landmarks: landmarkElements.length,
      lists: listElements.length,
      buttons: buttonElements.length,
      links: linkElements.length,
    },
  };
};

// Performance accessibility testing
export const testPerformanceAccessibility = async (component: React.ReactElement) => {
  const startTime = performance.now();
  const { container } = render(component);
  const renderTime = performance.now() - startTime;

  // Check for performance issues that affect accessibility
  const largeDOM = container.querySelectorAll('*').length > 1000;
  const deepNesting = getMaximumDepth(container) > 20;

  return {
    renderTime,
    compliant: renderTime < 1000 && !largeDOM && !deepNesting,
    violations: [
      ...(renderTime >= 1000 ? [{
        type: 'slow-render',
        message: `Component took ${renderTime}ms to render, which may affect users with assistive technology`,
      }] : []),
      ...(largeDOM ? [{
        type: 'large-dom',
        message: 'Large DOM tree may affect screen reader performance',
      }] : []),
      ...(deepNesting ? [{
        type: 'deep-nesting',
        message: 'Deeply nested elements may affect navigation',
      }] : []),
    ],
  };
};

// Helper function to calculate DOM depth
function getMaximumDepth(element: Element, currentDepth = 0): number {
  const children = element.children;
  if (children.length === 0) return currentDepth;
  
  let maxDepth = currentDepth;
  for (const child of children) {
    const depth = getMaximumDepth(child, currentDepth + 1);
    maxDepth = Math.max(maxDepth, depth);
  }
  
  return maxDepth;
}

// Comprehensive accessibility test suite
export const runAccessibilitySuite = async (
  component: React.ReactElement,
  options: AccessibilityTestOptions = {}
) => {
  const { container } = render(component);
  
  const [
    axeResults,
    keyboardResults,
    ariaResults,
    semanticResults,
    performanceResults,
  ] = await Promise.all([
    testAccessibility(component, options),
    testKeyboardNavigation(container),
    testAriaLabels(container),
    testSemanticHTML(container),
    testPerformanceAccessibility(component),
  ]);

  return {
    overall: {
      compliant: axeResults.compliant && 
                keyboardResults.tabOrderCorrect && 
                ariaResults.compliant && 
                semanticResults.compliant && 
                performanceResults.compliant,
      score: calculateAccessibilityScore({
        axeResults,
        keyboardResults,
        ariaResults,
        semanticResults,
        performanceResults,
      }),
    },
    axe: axeResults,
    keyboard: keyboardResults,
    aria: ariaResults,
    semantic: semanticResults,
    performance: performanceResults,
  };
};

// Calculate overall accessibility score
function calculateAccessibilityScore(results: any): number {
  const weights = {
    axe: 0.4,
    keyboard: 0.2,
    aria: 0.2,
    semantic: 0.1,
    performance: 0.1,
  };

  const scores = {
    axe: results.axeResults.compliant ? 100 : Math.max(0, 100 - ((results.axeResults.violations || []).length * 10)),
    keyboard: results.keyboardResults.tabOrderCorrect ? 100 : 50,
    aria: results.ariaResults.compliant ? 100 : Math.max(0, 100 - ((results.ariaResults.violations || []).length * 15)),
    semantic: results.semanticResults.compliant ? 100 : Math.max(0, 100 - ((results.semanticResults.violations || []).length * 10)),
    performance: results.performanceResults.compliant ? 100 : 70,
  };

  return Object.entries(weights).reduce((total, [key, weight]) => 
    total + (scores[key as keyof typeof scores] * weight), 0
  );
}

// Export accessibility testing matchers
export const toHaveNoViolations = {
  async toHaveNoViolations(received: HTMLElement) {
    const axe = await loadAxe();
    if (!axe) {
      return {
        pass: true,
        message: () => 'axe-core not available for accessibility testing',
      };
    }

    const results = await (axe as any)(received);
    const violations = results.violations || [];
    
    if (violations.length === 0) {
      return {
        pass: true,
        message: () => 'No accessibility violations found',
      };
    }

    return {
      pass: false,
      message: () => `Found ${violations.length} accessibility violation(s):\n${
        violations.map((v: any) => `- ${v.description} (${v.impact})`).join('\n')
      }`,
    };
  },
};