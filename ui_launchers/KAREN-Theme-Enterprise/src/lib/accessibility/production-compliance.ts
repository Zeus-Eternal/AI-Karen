/**
 * Accessibility Production Compliance
 * 
 * Ensures WCAG 2.1 AA compliance across all components
 * with automated testing and monitoring for production.
 */

import { useEffect, useState } from 'react';

// Accessibility compliance types
export interface AccessibilityIssue {
  id: string;
  type: 'error' | 'warning';
  rule: string;
  description: string;
  element: string;
  impact: 'critical' | 'serious' | 'moderate' | 'minor';
  helpUrl?: string;
  selector?: string;
}

export interface AccessibilityReport {
  timestamp: number;
  url: string;
  score: number;
  issues: AccessibilityIssue[];
  compliance: {
    wcagLevel: 'A' | 'AA' | 'AAA';
    passed: number;
    failed: number;
    total: number;
  };
}

export interface AccessibilityConfig {
  enableLiveMonitoring: boolean;
  enableAutoFixes: boolean;
  reportEndpoint?: string;
  wcagLevel: 'A' | 'AA' | 'AAA';
}

// WCAG 2.1 AA compliance rules
const WCAG_RULES = [
  {
    id: 'wcag-1-1-1',
    name: 'Non-text Content',
    description: 'All non-text content has a text alternative',
    test: (element: Element) => {
      if (element instanceof HTMLImageElement) {
        return element.alt !== null && element.alt !== '';
      }
      if (element instanceof HTMLCanvasElement) {
        return element.getAttribute('aria-label') !== null;
      }
      return true;
    },
    impact: 'critical' as const,
  },
  {
    id: 'wcag-1-3-1',
    name: 'Adaptable Content',
    description: 'Information and user interface components must be presentable in different ways',
    test: (element: Element) => {
      const hasAriaLabel = element.getAttribute('aria-label') !== null;
      const hasAriaLabelledBy = element.getAttribute('aria-labelledby') !== null;
      const hasTitle = element.getAttribute('title') !== null;
      return hasAriaLabel || hasAriaLabelledBy || hasTitle;
    },
    impact: 'serious' as const,
  },
  {
    id: 'wcag-2-1-1',
    name: 'Keyboard Accessible',
    description: 'All functionality must be available from a keyboard',
    test: (element: Element) => {
      if (element instanceof HTMLElement) {
        const tabIndex = element.tabIndex;
        const isFocusable = tabIndex >= 0 || 
                          element.tagName === 'A' ||
                          element.tagName === 'BUTTON' ||
                          element.tagName === 'INPUT' ||
                          element.tagName === 'TEXTAREA' ||
                          element.tagName === 'SELECT';
        return isFocusable || element.getAttribute('role') === 'presentation';
      }
      return true;
    },
    impact: 'critical' as const,
  },
  {
    id: 'wcag-2-4-1',
    name: 'Purpose of Links',
    description: 'The purpose of each link can be determined from the link text alone',
    test: (element: Element) => {
      if (element instanceof HTMLAnchorElement) {
        const hasText = element.textContent?.trim().length > 0;
        const ariaLabel = element.getAttribute('aria-label');
        const hasAriaLabel = ariaLabel && ariaLabel.trim().length > 0;
        return hasText || hasAriaLabel;
      }
      return true;
    },
    impact: 'serious' as const,
  },
  {
    id: 'wcag-3-1-1',
    name: 'Language of Page',
    description: 'The default human language of each web page can be programmatically determined',
    test: () => {
      const html = document.documentElement;
      return html.getAttribute('lang') !== null && html.getAttribute('lang') !== '';
    },
    impact: 'moderate' as const,
  },
  {
    id: 'wcag-3-2-1',
    name: 'On Focus',
    description: 'When any component receives focus, it does not initiate a change of context',
    test: (element: Element) => {
      if (element instanceof HTMLElement) {
        const hasOnFocus = element.getAttribute('onfocus') !== null;
        const hasOnClick = element.getAttribute('onclick') !== null;
        return !(hasOnFocus && hasOnClick);
      }
      return true;
    },
    impact: 'moderate' as const,
  },
  {
    id: 'wcag-4-1-2',
    name: 'Name, Role, Value',
    description: 'For all user interface components, the name and role can be programmatically determined',
    test: (element: Element) => {
      if (element instanceof HTMLElement) {
        const hasRole = element.getAttribute('role') !== null;
        const hasImplicitRole = ['button', 'link', 'navigation', 'main', 'header', 'footer']
          .includes(element.tagName.toLowerCase());
        return hasRole || hasImplicitRole;
      }
      return true;
    },
    impact: 'serious' as const,
  },
];

// Accessibility compliance checker class
export class AccessibilityComplianceChecker {
  private config: AccessibilityConfig;
  private issues: AccessibilityIssue[] = [];
  private isMonitoring = false;
  private observer?: MutationObserver;

  constructor(config: AccessibilityConfig = {
    enableLiveMonitoring: true,
    enableAutoFixes: true,
    wcagLevel: 'AA',
  }) {
    this.config = config;
  }

  // Start accessibility monitoring
  start(): void {
    if (this.isMonitoring) return;

    this.isMonitoring = true;
    console.log('🔍 Accessibility monitoring started');

    // Initial scan
    this.scanPage();

    // Setup live monitoring if enabled
    if (this.config.enableLiveMonitoring) {
      this.setupLiveMonitoring();
    }

    // Setup keyboard navigation monitoring
    this.setupKeyboardMonitoring();

    // Setup focus management
    this.setupFocusManagement();
  }

  // Stop accessibility monitoring
  stop(): void {
    if (!this.isMonitoring) return;

    this.isMonitoring = false;
    
    if (this.observer) {
      this.observer.disconnect();
      this.observer = undefined;
    }

    console.log('⏹️ Accessibility monitoring stopped');
  }

  // Scan entire page for accessibility issues
  scanPage(): AccessibilityIssue[] {
    this.issues = [];
    
    // Test WCAG rules
    WCAG_RULES.forEach(rule => {
      const elements = document.querySelectorAll('*');
      elements.forEach(element => {
        try {
          const passed = rule.test(element);
          if (!passed) {
            this.issues.push({
              id: `${rule.id}-${Date.now()}`,
              type: 'error',
              rule: rule.name,
              description: rule.description,
              element: element.tagName.toLowerCase(),
              impact: rule.impact,
              selector: this.getElementSelector(element),
              helpUrl: `https://www.w3.org/WAI/WCAG21/Techniques/${rule.id}`,
            });
          }
        } catch (error) {
          console.warn(`Error testing rule ${rule.name}:`, error);
        }
      });
    });

    // Test page-level rules
    this.testPageLevelRules();

    // Apply auto-fixes if enabled
    if (this.config.enableAutoFixes) {
      this.applyAutoFixes();
    }

    // Log results
    this.logResults();

    return [...this.issues];
  }

  // Setup live monitoring with MutationObserver
  private setupLiveMonitoring(): void {
    if (!window.MutationObserver) return;

    this.observer = new MutationObserver((mutations) => {
      let shouldRescan = false;

      mutations.forEach((mutation) => {
        if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
          shouldRescan = true;
        }
        if (mutation.type === 'attributes') {
          shouldRescan = true;
        }
      });

      if (shouldRescan) {
        // Debounce rescan
        setTimeout(() => this.scanPage(), 100);
      }
    });

    this.observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['aria-label', 'role', 'alt', 'title'],
    });
  }

  // Setup keyboard navigation monitoring
  private setupKeyboardMonitoring(): void {
    let lastFocusTime = 0;

    document.addEventListener('keydown', (event) => {
      const now = Date.now();
      
      // Track tab navigation
      if (event.key === 'Tab') {
        const timeSinceLastFocus = now - lastFocusTime;
        
        // Log tab navigation speed
        if (timeSinceLastFocus < 100) {
          console.warn('⚠️ Rapid tab navigation detected');
        }
        
        lastFocusTime = now;
      }

      // Check for keyboard traps
      if (event.key === 'Escape') {
        const activeElement = document.activeElement;
        if (activeElement && activeElement.getAttribute('data-keyboard-trap') === 'true') {
          console.warn('⚠️ Keyboard trap detected');
        }
      }
    });

    // Focus trap detection
    document.addEventListener('focusin', (event) => {
      const focusedElement = event.target as HTMLElement;
      const hasFocusTrap = focusedElement.getAttribute('data-keyboard-trap') === 'true';
      
      if (hasFocusTrap) {
        console.warn('⚠️ Element with focus trap received focus:', focusedElement);
      }
    }, true);
  }

  // Setup focus management
  private setupFocusManagement(): void {
    // Track focus order
    let focusHistory: Element[] = [];

    document.addEventListener('focusin', (event) => {
      const focusedElement = event.target as Element;
      focusHistory.push(focusedElement);

      // Keep only last 10 focus events
      if (focusHistory.length > 10) {
        focusHistory = focusHistory.slice(-10);
      }

      // Check for logical focus order
      if (focusHistory.length > 1) {
        const previousElement = focusHistory[focusHistory.length - 2];
        const currentElement = focusHistory[focusHistory.length - 1];

        if (!this.isLogicalFocusOrder(previousElement, currentElement)) {
          console.warn('⚠️ Illogical focus order detected');
        }
      }
    }, true);

    // Skip links detection
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Tab') {
        const skipLinks = document.querySelectorAll('[data-skip-link]');
        if (skipLinks.length > 0) {
          console.log('🔗 Skip links found:', skipLinks.length);
        }
      }
    });
  }

  // Test page-level accessibility rules
  private testPageLevelRules(): void {
    // Test page title
    const title = document.title;
    if (!title || title.trim().length === 0) {
      this.issues.push({
        id: 'page-title-missing',
        type: 'error',
        rule: 'Page Title',
        description: 'Page must have a descriptive title',
        element: 'title',
        impact: 'serious',
        helpUrl: 'https://www.w3.org/WAI/WCAG21/Techniques/techniques.html#H25',
      });
    }

    // Test heading structure
    const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
    const hasH1 = Array.from(headings).some(h => h.tagName === 'H1');
    
    if (!hasH1) {
      this.issues.push({
        id: 'missing-h1',
        type: 'warning',
        rule: 'Heading Structure',
        description: 'Page should have at least one H1 heading',
        element: 'h1',
        impact: 'moderate',
        helpUrl: 'https://www.w3.org/WAI/WCAG21/Techniques/techniques.html#H42',
      });
    }

    // Test for proper heading hierarchy
    let previousLevel = 0;
    headings.forEach((heading, index) => {
      const currentLevel = parseInt(heading.tagName.substring(1));
      
      if (currentLevel > previousLevel + 1 && index > 0) {
        this.issues.push({
          id: `heading-hierarchy-${index}`,
          type: 'warning',
          rule: 'Heading Hierarchy',
          description: 'Headings should not skip levels',
          element: heading.tagName.toLowerCase(),
          impact: 'moderate',
          selector: this.getElementSelector(heading),
        });
      }
      
      previousLevel = currentLevel;
    });
  }

  // Apply automatic fixes
  private applyAutoFixes(): void {
    // Add missing alt attributes to images
    const images = document.querySelectorAll('img:not([alt])');
    images.forEach(img => {
      img.setAttribute('alt', '');
      console.log('🔧 Added empty alt attribute to image');
    });

    // Add role to landmark elements
    const landmarks = {
      'header': 'banner',
      'nav': 'navigation',
      'main': 'main',
      'aside': 'complementary',
      'footer': 'contentinfo',
    };

    Object.entries(landmarks).forEach(([tag, role]) => {
      const elements = document.querySelectorAll(`${tag}:not([role])`);
      elements.forEach(element => {
        element.setAttribute('role', role);
        console.log(`🔧 Added role="${role}" to ${tag} element`);
      });
    });

    // Add skip links for keyboard navigation
    const main = document.querySelector('main');
    const firstFocusable = document.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
    
    if (main && firstFocusable && !document.querySelector('[data-skip-link]')) {
      const skipLink = document.createElement('a');
      skipLink.href = '#main';
      skipLink.textContent = 'Skip to main content';
      skipLink.setAttribute('data-skip-link', 'true');
      skipLink.className = 'sr-only focus:not-sr-only focus:outline-none focus:ring-2 focus:ring-blue-500 absolute top-4 left-4 z-50 bg-white px-4 py-2 rounded';
      
      document.body.insertBefore(skipLink, document.body.firstChild);
      console.log('🔧 Added skip link for keyboard navigation');
    }
  }

  // Check if focus order is logical
  private isLogicalFocusOrder(previous: Element, current: Element): boolean {
    // Simple heuristic: check if current element is below or to the right of previous
    const prevRect = previous.getBoundingClientRect();
    const currRect = current.getBoundingClientRect();
    
    return currRect.top >= prevRect.top || currRect.left >= prevRect.left;
  }

  // Get CSS selector for element
  private getElementSelector(element: Element): string {
    if (element.id) {
      return `#${element.id}`;
    }
    
    // Handle className safely - it could be a string, DOMTokenList, null, or undefined
    let classNameStr = '';
    if (element.className) {
      if (typeof element.className === 'string') {
        classNameStr = element.className;
      } else if ((element.className as any) instanceof DOMTokenList) {
        classNameStr = Array.from(element.className as DOMTokenList).join(' ');
      } else {
        // Convert any other type to string safely
        try {
          classNameStr = String(element.className);
        } catch (e) {
          console.warn('Unable to convert className to string:', e);
          classNameStr = '';
        }
      }
    }
    
    if (classNameStr) {
      const classes = classNameStr.split(' ').filter(c => c.trim());
      if (classes.length > 0) {
        return `${element.tagName.toLowerCase()}.${classes.join('.')}`;
      }
    }
    
    return element.tagName.toLowerCase();
  }

  // Log accessibility results
  private logResults(): void {
    const criticalIssues = this.issues.filter(i => i.impact === 'critical').length;
    const seriousIssues = this.issues.filter(i => i.impact === 'serious').length;
    const moderateIssues = this.issues.filter(i => i.impact === 'moderate').length;
    const minorIssues = this.issues.filter(i => i.impact === 'minor').length;

    console.group('🔍 Accessibility Scan Results');
    console.log(`Critical: ${criticalIssues}`);
    console.log(`Serious: ${seriousIssues}`);
    console.log(`Moderate: ${moderateIssues}`);
    console.log(`Minor: ${minorIssues}`);
    console.log(`Total: ${this.issues.length}`);
    
    if (this.issues.length > 0) {
      console.table(this.issues);
    }
    
    console.groupEnd();

    // Send report if endpoint is configured
    if (this.config.reportEndpoint) {
      this.sendReport();
    }
  }

  // Send accessibility report
  private async sendReport(): Promise<void> {
    if (!this.config.reportEndpoint) return;

    const report: AccessibilityReport = {
      timestamp: Date.now(),
      url: window.location.href,
      score: this.calculateScore(),
      issues: this.issues,
      compliance: {
        wcagLevel: this.config.wcagLevel,
        passed: this.issues.length === 0 ? 1 : 0,
        failed: this.issues.length,
        total: 1,
      },
    };

    try {
      await fetch(this.config.reportEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(report),
      });
      console.log('📊 Accessibility report sent');
    } catch (error) {
      console.error('❌ Failed to send accessibility report:', error);
    }
  }

  // Calculate accessibility score
  private calculateScore(): number {
    if (this.issues.length === 0) return 100;

    const weights = {
      critical: 4,
      serious: 3,
      moderate: 2,
      minor: 1,
    };

    const totalWeight = this.issues.reduce((sum, issue) => {
      return sum + weights[issue.impact];
    }, 0);

    const maxPossibleWeight = this.issues.length * 4; // All critical = worst case
    const score = Math.max(0, 100 - (totalWeight / maxPossibleWeight) * 100);

    return Math.round(score);
  }

  // Get current issues
  getIssues(): AccessibilityIssue[] {
    return [...this.issues];
  }

  // Get accessibility score
  getScore(): number {
    return this.calculateScore();
  }
}

// Singleton instance
let accessibilityChecker: AccessibilityComplianceChecker | null = null;

// Initialize accessibility monitoring
export function initAccessibilityMonitoring(config: Partial<AccessibilityConfig> = {}): AccessibilityComplianceChecker {
  if (!accessibilityChecker) {
    accessibilityChecker = new AccessibilityComplianceChecker({
      enableLiveMonitoring: config.enableLiveMonitoring ?? true,
      enableAutoFixes: config.enableAutoFixes ?? true,
      wcagLevel: config.wcagLevel ?? 'AA',
      reportEndpoint: config.reportEndpoint,
    });
  }

  // Start monitoring when DOM is ready
  if (document.readyState === 'complete') {
    accessibilityChecker.start();
  } else {
    window.addEventListener('load', () => {
      accessibilityChecker!.start();
    });
  }

  return accessibilityChecker;
}

// Get accessibility checker instance
export function getAccessibilityChecker(): AccessibilityComplianceChecker | null {
  return accessibilityChecker;
}

// Accessibility utility functions
export function announceToScreenReader(message: string, priority: 'polite' | 'assertive' = 'polite'): void {
  const announcement = document.createElement('div');
  announcement.setAttribute('aria-live', priority);
  announcement.setAttribute('aria-atomic', 'true');
  announcement.className = 'sr-only';
  announcement.textContent = message;

  document.body.appendChild(announcement);

  // Remove after announcement
  setTimeout(() => {
    document.body.removeChild(announcement);
  }, 1000);
}

export function trapFocus(container: Element): () => void {
  const focusableElements = container.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  ) as NodeListOf<HTMLElement>;

  const firstElement = focusableElements[0];
  const lastElement = focusableElements[focusableElements.length - 1];

  const handleKeyDown = (event: KeyboardEvent) => {
    if (event.key === 'Tab') {
      if (event.shiftKey) {
        if (document.activeElement === firstElement) {
          lastElement.focus();
          event.preventDefault();
        }
      } else {
        if (document.activeElement === lastElement) {
          firstElement.focus();
          event.preventDefault();
        }
      }
    }
  };

  container.addEventListener('keydown', handleKeyDown as EventListener);
  firstElement?.focus();

  // Return cleanup function
  return () => {
    container.removeEventListener('keydown', handleKeyDown as EventListener);
  };
}