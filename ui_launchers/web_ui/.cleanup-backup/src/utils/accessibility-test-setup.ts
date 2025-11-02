/**
 * Accessibility Test Setup and Configuration
 * 
 * This file provides setup utilities and configurations for accessibility testing
 * across the entire application.
 */

import React from 'react';
import { configure } from '@testing-library/react';
// Note: Using axe-core directly instead of jest-axe for Vitest compatibility
import axe from 'axe-core';

// Configure Testing Library for better accessibility testing
configure({
  // Use accessible queries by default
  defaultHidden: true,
  // Increase timeout for accessibility tests
  asyncUtilTimeout: 10000,
  // Configure better error messages
  getElementError: (message, container) => {
    const error = new Error(
      [
        message,
        'Here is the accessible tree:',
        require('@testing-library/dom').prettyDOM(container, undefined, {
          highlight: false,
          maxDepth: 3,
        }),
      ].join('\n\n')
    );
    error.name = 'TestingLibraryElementError';
    return error;
  },
});

// Note: toHaveNoViolations would be extended in test setup for Vitest

// Configure axe-core for consistent testing
// Note: Detailed configuration would be done in actual test files

// Accessibility test configurations for different scenarios
export const accessibilityConfigs = {
  // Basic accessibility test - essential rules only
  basic: {
    runOnly: {
      type: 'tag' as const,
      values: ['wcag2a'],
    },
  },
  
  // Standard accessibility test - WCAG 2.1 AA compliance
  standard: {
    runOnly: {
      type: 'tag' as const,
      values: ['wcag2a', 'wcag2aa'],
    },
  },
  
  // Comprehensive accessibility test - all rules and best practices
  comprehensive: {
    runOnly: {
      type: 'tag' as const,
      values: ['wcag2a', 'wcag2aa', 'wcag21aa', 'best-practice'],
    },
  },
  
  // Form-specific accessibility test
  forms: {
    runOnly: {
      type: 'tag' as const,
      values: ['wcag2a', 'wcag2aa'],
    },
  },
  
  // Navigation-specific accessibility test
  navigation: {
    runOnly: {
      type: 'tag' as const,
      values: ['wcag2a', 'wcag2aa'],
    },
  },
  
  // Color and visual accessibility test
  visual: {
    runOnly: {
      type: 'tag' as const,
      values: ['wcag2a', 'wcag2aa'],
    },
  },
};

// Helper function to create accessibility test wrapper
export const createAccessibilityTestWrapper = (options: {
  lang?: string;
  title?: string;
  skipLinks?: boolean;
} = {}) => {
  const { lang = 'en', title = 'Test Page', skipLinks = false } = options;
  
  return function AccessibilityTestWrapper({ children }: { children: React.ReactNode }) {
    return React.createElement('div', { lang },
      skipLinks && React.createElement('div', null,
        React.createElement('a', { 
          href: '#main-content', 
          className: 'sr-only focus:not-sr-only' 
        }, 'Skip to main content'),
        React.createElement('a', { 
          href: '#navigation', 
          className: 'sr-only focus:not-sr-only' 
        }, 'Skip to navigation')
      ),
      React.createElement('main', { 
        id: 'main-content', 
        role: 'main' 
      },
        React.createElement('h1', null, title),
        children
      )
    );
  };
};

// Helper function to run accessibility tests with consistent configuration
export const runAccessibilityTestSuite = async (
  container: Element,
  config: keyof typeof accessibilityConfigs = 'standard'
) => {
  const testConfig = accessibilityConfigs[config];
  
  try {
    const results = await axe.run(container as any, testConfig) as unknown as any;
    
    // Create detailed report
    const report = {
      passed: results.violations.length === 0,
      violations: results.violations,
      passes: results.passes,
      incomplete: results.incomplete,
      inapplicable: results.inapplicable,
      summary: {
        violations: results.violations.length,
        passes: results.passes.length,
        incomplete: results.incomplete.length,
        inapplicable: results.inapplicable.length,
      },
      config: config,
      timestamp: new Date().toISOString(),
    };
    
    return report;
  } catch (error) {
    throw new Error(`Accessibility test failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
};

// Helper function to validate specific accessibility patterns
export const validateAccessibilityPattern = {
  // Validate form accessibility
  form: (container: Element) => {
    const issues: string[] = [];
    
    // Check for form labels
    const inputs = container.querySelectorAll('input, select, textarea');
    inputs.forEach((input, index) => {
      const id = input.getAttribute('id');
      const ariaLabel = input.getAttribute('aria-label');
      const ariaLabelledBy = input.getAttribute('aria-labelledby');
      const hasLabel = id && container.querySelector(`label[for="${id}"]`);
      
      if (!ariaLabel && !ariaLabelledBy && !hasLabel) {
        issues.push(`Form control ${index + 1} is missing a label`);
      }
    });
    
    // Check for fieldsets with legends
    const fieldsets = container.querySelectorAll('fieldset');
    fieldsets.forEach((fieldset, index) => {
      const legend = fieldset.querySelector('legend');
      if (!legend) {
        issues.push(`Fieldset ${index + 1} is missing a legend`);
      }
    });
    
    return issues;
  },
  
  // Validate heading hierarchy
  headings: (container: Element) => {
    const issues: string[] = [];
    const headings = container.querySelectorAll('h1, h2, h3, h4, h5, h6');
    let previousLevel = 0;
    
    headings.forEach((heading, index) => {
      const level = parseInt(heading.tagName.charAt(1));
      
      if (index === 0 && level !== 1) {
        issues.push('First heading should be h1');
      }
      
      if (level > previousLevel + 1) {
        issues.push(`Heading level jumps from h${previousLevel} to h${level}`);
      }
      
      if (!heading.textContent?.trim()) {
        issues.push(`Heading ${index + 1} is empty`);
      }
      
      previousLevel = level;
    });
    
    return issues;
  },
  
  // Validate landmark structure
  landmarks: (container: Element) => {
    const issues: string[] = [];
    
    // Check for main landmark
    const mainLandmarks = container.querySelectorAll('main, [role="main"]');
    if (mainLandmarks.length === 0) {
      issues.push('No main landmark found');
    } else if (mainLandmarks.length > 1) {
      issues.push('Multiple main landmarks found');
    }
    
    // Check for navigation landmarks
    const navLandmarks = container.querySelectorAll('nav, [role="navigation"]');
    navLandmarks.forEach((nav, index) => {
      const ariaLabel = nav.getAttribute('aria-label');
      const ariaLabelledBy = nav.getAttribute('aria-labelledby');
      
      if (navLandmarks.length > 1 && !ariaLabel && !ariaLabelledBy) {
        issues.push(`Navigation landmark ${index + 1} needs aria-label or aria-labelledby`);
      }
    });
    
    return issues;
  },
  
  // Validate ARIA usage
  aria: (container: Element) => {
    const issues: string[] = [];
    
    // Check for ARIA references
    const elementsWithAriaRefs = container.querySelectorAll('[aria-describedby], [aria-labelledby], [aria-controls]');
    elementsWithAriaRefs.forEach((element, index) => {
      const describedBy = element.getAttribute('aria-describedby');
      const labelledBy = element.getAttribute('aria-labelledby');
      const controls = element.getAttribute('aria-controls');
      
      [describedBy, labelledBy, controls].forEach((attr) => {
        if (attr) {
          const ids = attr.split(' ');
          ids.forEach((id) => {
            if (id && !container.querySelector(`#${id}`)) {
              issues.push(`Element ${index + 1} references non-existent ID: ${id}`);
            }
          });
        }
      });
    });
    
    // Check for proper ARIA roles
    const elementsWithRoles = container.querySelectorAll('[role]');
    elementsWithRoles.forEach((element, index) => {
      const role = element.getAttribute('role');
      if (role && !isValidAriaRole(role)) {
        issues.push(`Element ${index + 1} has invalid ARIA role: ${role}`);
      }
    });
    
    return issues;
  },
};

// Helper function to validate ARIA roles (simplified)
function isValidAriaRole(role: string): boolean {
  const validRoles = [
    'alert', 'alertdialog', 'application', 'article', 'banner', 'button',
    'cell', 'checkbox', 'columnheader', 'combobox', 'complementary',
    'contentinfo', 'definition', 'dialog', 'directory', 'document',
    'feed', 'figure', 'form', 'grid', 'gridcell', 'group', 'heading',
    'img', 'link', 'list', 'listbox', 'listitem', 'log', 'main',
    'marquee', 'math', 'menu', 'menubar', 'menuitem', 'menuitemcheckbox',
    'menuitemradio', 'navigation', 'none', 'note', 'option', 'presentation',
    'progressbar', 'radio', 'radiogroup', 'region', 'row', 'rowgroup',
    'rowheader', 'scrollbar', 'search', 'searchbox', 'separator',
    'slider', 'spinbutton', 'status', 'switch', 'tab', 'table',
    'tablist', 'tabpanel', 'term', 'textbox', 'timer', 'toolbar',
    'tooltip', 'tree', 'treegrid', 'treeitem'
  ];
  
  return validRoles.includes(role);
}

// Export default configuration
export default {
  configs: accessibilityConfigs,
  createWrapper: createAccessibilityTestWrapper,
  runTestSuite: runAccessibilityTestSuite,
  validatePattern: validateAccessibilityPattern,
};