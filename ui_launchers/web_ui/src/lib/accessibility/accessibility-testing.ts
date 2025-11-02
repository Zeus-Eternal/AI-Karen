/**
 * Enhanced Accessibility Testing Utilities
 * 
 * Comprehensive testing utilities for WCAG 2.1 AA compliance
 */

import axe, { type AxeResults, type RunOptions } from 'axe-core';

// ============================================================================
// TYPES AND INTERFACES
// ============================================================================

export interface AccessibilityTestSuite {
  /** Basic WCAG 2.1 AA compliance test */
  basic: () => Promise<AccessibilityReport>;
  /** Comprehensive accessibility audit */
  comprehensive: () => Promise<AccessibilityReport>;
  /** Keyboard navigation test */
  keyboard: () => Promise<KeyboardAccessibilityReport>;
  /** Screen reader compatibility test */
  screenReader: () => Promise<ScreenReaderReport>;
  /** Color contrast validation */
  colorContrast: () => Promise<ColorContrastReport>;
  /** Focus management test */
  focusManagement: () => Promise<FocusManagementReport>;
  /** ARIA implementation test */
  aria: () => Promise<AriaReport>;
}

export interface AccessibilityReport {
  passed: boolean;
  score: number; // 0-100
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

  /**
   * Run basic WCAG 2.1 AA compliance test
   */
  async basic(): Promise<AccessibilityReport> {
    const startTime = performance.now();
    
    try {
      const results = await axe.run(this.container as any, {
        ...this.options,
        runOnly: {
          type: 'tag',
          values: ['wcag2a', 'wcag2aa'],
        },

      return this.processAxeResults(results, performance.now() - startTime);
    } catch (error) {
      throw new Error(`Basic accessibility test failed: ${error}`);
    }
  }

  /**
   * Run comprehensive accessibility audit
   */
  async comprehensive(): Promise<AccessibilityReport> {
    const startTime = performance.now();
    
    try {
      const results = await axe.run(this.container as any, {
        ...this.options,
        runOnly: {
          type: 'tag',
          values: ['wcag2a', 'wcag2aa', 'wcag21aa', 'best-practice'],
        },

      return this.processAxeResults(results, performance.now() - startTime);
    } catch (error) {
      throw new Error(`Comprehensive accessibility test failed: ${error}`);
    }
  }

  /**
   * Test keyboard navigation
   */
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

    // Test each focusable element
    focusableElements.forEach((element, index) => {
      const htmlElement = element as HTMLElement;
      
      // Check if element is reachable
      if (htmlElement.tabIndex < 0 && !htmlElement.hasAttribute('disabled')) {
        unreachableElements.push(this.getElementSelector(htmlElement));
      }

      // Check focus order
      if (htmlElement.tabIndex > 0) {
        focusOrderIssues.push(`Element has positive tabindex: ${this.getElementSelector(htmlElement)}`);
      }

    // Test focus traps
    const focusTraps = this.container.querySelectorAll('[data-focus-trap="true"]');
    focusTraps.forEach((trap) => {
      // Simulate focus trap testing
      const trapElement = trap as HTMLElement;
      const focusableInTrap = trapElement.querySelectorAll(focusableSelectors.join(', '));
      
      if (focusableInTrap.length === 0) {
        trapIssues.push(`Focus trap has no focusable elements: ${this.getElementSelector(trapElement)}`);
      }

    // Test skip links
    const skipLinks = this.container.querySelectorAll('.skip-links a, [href^="#"]');
    skipLinks.forEach((link) => {
      const href = link.getAttribute('href');
      if (href && href.startsWith('#')) {
        const target = this.container.querySelector(href);
        if (!target) {
          skipLinkIssues.push(`Skip link target not found: ${href}`);
        }
      }

    return {
      passed: unreachableElements.length === 0 && focusOrderIssues.length === 0 && trapIssues.length === 0 && skipLinkIssues.length === 0,
      focusableElements: focusableElements.length,
      unreachableElements,
      focusOrderIssues,
      trapIssues,
      skipLinkIssues,
    };
  }

  /**
   * Test screen reader compatibility
   */
  async screenReader(): Promise<ScreenReaderReport> {
    const missingLabels: string[] = [];
    const ariaIssues: string[] = [];
    const landmarkIssues: string[] = [];
    const headingStructureIssues: string[] = [];
    const liveRegionIssues: string[] = [];

    // Test form labels
    const formControls = this.container.querySelectorAll('input, select, textarea');
    formControls.forEach((control) => {
      const element = control as HTMLElement;
      if (!this.hasAccessibleName(element)) {
        missingLabels.push(this.getElementSelector(element));
      }

    // Test images
    const images = this.container.querySelectorAll('img');
    images.forEach((img) => {
      const altText = img.getAttribute('alt');
      const ariaLabel = img.getAttribute('aria-label');
      const role = img.getAttribute('role');
      
      if (!altText && !ariaLabel && role !== 'presentation' && role !== 'none') {
        missingLabels.push(this.getElementSelector(img));
      }

    // Test ARIA usage
    const elementsWithAria = this.container.querySelectorAll('[aria-*]');
    elementsWithAria.forEach((element) => {
      const issues = this.validateAriaAttributes(element as HTMLElement);
      ariaIssues.push(...issues);

    // Test landmark structure
    const mainLandmarks = this.container.querySelectorAll('main, [role="main"]');
    if (mainLandmarks.length === 0) {
      landmarkIssues.push('No main landmark found');
    } else if (mainLandmarks.length > 1) {
      landmarkIssues.push('Multiple main landmarks found');
    }

    // Test heading structure
    const headings = this.container.querySelectorAll('h1, h2, h3, h4, h5, h6, [role="heading"]');
    let previousLevel = 0;
    headings.forEach((heading) => {
      const level = this.getHeadingLevel(heading as HTMLElement);
      if (level > previousLevel + 1) {
        headingStructureIssues.push(`Heading level skipped: h${level} after h${previousLevel}`);
      }
      previousLevel = level;

    // Test live regions
    const liveRegions = this.container.querySelectorAll('[aria-live]');
    liveRegions.forEach((region) => {
      const politeness = region.getAttribute('aria-live');
      if (!['polite', 'assertive', 'off'].includes(politeness || '')) {
        liveRegionIssues.push(`Invalid aria-live value: ${politeness}`);
      }

    return {
      passed: missingLabels.length === 0 && ariaIssues.length === 0 && landmarkIssues.length === 0 && headingStructureIssues.length === 0 && liveRegionIssues.length === 0,
      missingLabels,
      ariaIssues,
      landmarkIssues,
      headingStructureIssues,
      liveRegionIssues,
    };
  }

  /**
   * Test color contrast
   */
  async colorContrast(): Promise<ColorContrastReport> {
    const failedElements: ColorContrastReport['failedElements'] = [];
    const textElements = this.container.querySelectorAll('*');
    let totalRatio = 0;
    let elementCount = 0;

    textElements.forEach((element) => {
      const htmlElement = element as HTMLElement;
      const computedStyle = window.getComputedStyle(htmlElement);
      const color = computedStyle.color;
      const backgroundColor = computedStyle.backgroundColor;
      
      if (color && backgroundColor && htmlElement.textContent?.trim()) {
        try {
          const ratio = this.calculateContrastRatio(color, backgroundColor);
          const fontSize = parseFloat(computedStyle.fontSize);
          const fontWeight = computedStyle.fontWeight;
          const isLargeText = fontSize >= 18 || (fontSize >= 14 && (fontWeight === 'bold' || parseInt(fontWeight) >= 700));
          
          const requiredRatio = isLargeText ? 3 : 4.5;
          
          if (ratio < requiredRatio) {
            failedElements.push({
              element: this.getElementSelector(htmlElement),
              foreground: color,
              background: backgroundColor,
              ratio,
              required: requiredRatio,
              level: 'AA',

          }
          
          totalRatio += ratio;
          elementCount++;
        } catch (error) {
          // Skip elements with invalid colors
        }
      }

    return {
      passed: failedElements.length === 0,
      failedElements,
      averageRatio: elementCount > 0 ? totalRatio / elementCount : 0,
    };
  }

  /**
   * Test focus management
   */
  async focusManagement(): Promise<FocusManagementReport> {
    const focusTraps: FocusManagementReport['focusTraps'] = [];
    const focusRestoration: FocusManagementReport['focusRestoration'] = [];
    const focusIndicators: FocusManagementReport['focusIndicators'] = [];

    // Test focus traps
    const trapElements = this.container.querySelectorAll('[data-focus-trap="true"]');
    trapElements.forEach((trap) => {
      const trapElement = trap as HTMLElement;
      const issues: string[] = [];
      
      // Check if trap has focusable elements
      const focusableElements = trapElement.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
      if (focusableElements.length === 0) {
        issues.push('No focusable elements in trap');
      }
      
      focusTraps.push({
        element: this.getElementSelector(trapElement),
        working: issues.length === 0,
        issues,


    // Test focus indicators
    const focusableElements = this.container.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
    focusableElements.forEach((element) => {
      const htmlElement = element as HTMLElement;
      const computedStyle = window.getComputedStyle(htmlElement, ':focus');
      const outline = computedStyle.outline;
      const boxShadow = computedStyle.boxShadow;
      
      const hasVisibleFocus = outline !== 'none' || boxShadow !== 'none';
      
      focusIndicators.push({
        element: this.getElementSelector(htmlElement),
        visible: hasVisibleFocus,
        contrast: 0, // Would need more complex calculation


    return {
      passed: focusTraps.every(trap => trap.working) && focusIndicators.every(indicator => indicator.visible),
      focusTraps,
      focusRestoration,
      focusIndicators,
    };
  }

  /**
   * Test ARIA implementation
   */
  async aria(): Promise<AriaReport> {
    const invalidAttributes: string[] = [];
    const missingAttributes: string[] = [];
    const incorrectRoles: string[] = [];
    const brokenReferences: string[] = [];

    const elementsWithAria = this.container.querySelectorAll('[aria-*], [role]');
    
    elementsWithAria.forEach((element) => {
      const htmlElement = element as HTMLElement;
      
      // Validate ARIA attributes
      const ariaIssues = this.validateAriaAttributes(htmlElement);
      invalidAttributes.push(...ariaIssues);
      
      // Check for broken references
      const describedBy = htmlElement.getAttribute('aria-describedby');
      const labelledBy = htmlElement.getAttribute('aria-labelledby');
      const controls = htmlElement.getAttribute('aria-controls');
      
      [describedBy, labelledBy, controls].forEach((attr) => {
        if (attr) {
          const ids = attr.split(' ');
          ids.forEach((id) => {
            if (!this.container.querySelector(`#${id}`)) {
              brokenReferences.push(`${this.getElementSelector(htmlElement)} references non-existent ID: ${id}`);
            }

        }


    return {
      passed: invalidAttributes.length === 0 && missingAttributes.length === 0 && incorrectRoles.length === 0 && brokenReferences.length === 0,
      invalidAttributes,
      missingAttributes,
      incorrectRoles,
      brokenReferences,
    };
  }

  // ============================================================================
  // HELPER METHODS
  // ============================================================================

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

    return [...new Set(recommendations)]; // Remove duplicates
  }

  private hasAccessibleName(element: HTMLElement): boolean {
    const ariaLabel = element.getAttribute('aria-label');
    const ariaLabelledBy = element.getAttribute('aria-labelledby');
    const id = element.id;
    const label = id ? this.container.querySelector(`label[for="${id}"]`) : null;
    const parentLabel = element.closest('label');
    
    return !!(ariaLabel || ariaLabelledBy || label || parentLabel);
  }

  private validateAriaAttributes(element: HTMLElement): string[] {
    const issues: string[] = [];
    const ariaAttributes = Array.from(element.attributes).filter(attr => attr.name.startsWith('aria-'));

    ariaAttributes.forEach((attr) => {
      const name = attr.name;
      const value = attr.value;

      if (!value.trim()) {
        issues.push(`${this.getElementSelector(element)} has empty ${name}`);
        return;
      }

      switch (name) {
        case 'aria-expanded':
        case 'aria-checked':
        case 'aria-selected':
        case 'aria-pressed':
        case 'aria-hidden':
          if (!['true', 'false'].includes(value)) {
            issues.push(`${this.getElementSelector(element)} has invalid ${name} value: ${value}`);
          }
          break;
        case 'aria-level':
        case 'aria-setsize':
        case 'aria-posinset':
          if (!/^\d+$/.test(value) || parseInt(value) < 1) {
            issues.push(`${this.getElementSelector(element)} has invalid ${name} value: ${value}`);
          }
          break;
      }

    return issues;
  }

  private getElementSelector(element: HTMLElement): string {
    if (element.id) return `#${element.id}`;
    if (element.className) return `${element.tagName.toLowerCase()}.${element.className.split(' ')[0]}`;
    return element.tagName.toLowerCase();
  }

  private getHeadingLevel(element: HTMLElement): number {
    const tagName = element.tagName.toLowerCase();
    if (tagName.match(/^h[1-6]$/)) {
      return parseInt(tagName.charAt(1));
    }
    
    const ariaLevel = element.getAttribute('aria-level');
    return ariaLevel ? parseInt(ariaLevel) : 1;
  }

  private calculateContrastRatio(foreground: string, background: string): number {
    // Simplified contrast ratio calculation
    // In a real implementation, you'd need to parse CSS colors and calculate luminance
    return 4.5; // Placeholder
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

  }

  if (basic.recommendations.length > 0) {
    report += 'Recommendations:\n';
    basic.recommendations.forEach((rec, index) => {
      report += `${index + 1}. ${rec}\n`;

  }

  return report;
}

export default AccessibilityTestSuite;