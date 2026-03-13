/**
 * WCAG 2.1 AA Compliance Verification System
 * Comprehensive accessibility testing and compliance monitoring
 */

import { AxeResults, Result, NodeResult } from 'axe-core';
import { auditLogger } from '../audit-logger';

// WCAG 2.1 AA compliance requirements
export interface WCAGComplianceReport {
  timestamp: Date;
  overallScore: number;
  level: 'A' | 'AA' | 'AAA';
  violations: Violation[];
  passes: Pass[];
  incomplete: Incomplete[];
  recommendations: Recommendation[];
  metrics: ComplianceMetrics;
}

export interface Violation {
  id: string;
  impact: 'minor' | 'moderate' | 'serious' | 'critical';
  wcagCriteria: string[];
  description: string;
  help: string;
  helpUrl: string;
  nodes: NodeResult[];
  priority: number;
}

export interface Pass {
  ruleId: string;
  description: string;
  wcagCriteria: string[];
  nodes: NodeResult[];
}

export interface Incomplete {
  ruleId: string;
  description: string;
  wcagCriteria: string[];
  nodes: NodeResult[];
  reason: string;
}

export interface Recommendation {
  category: 'keyboard' | 'screen-reader' | 'color' | 'focus' | 'aria' | 'semantic' | 'media';
  priority: 'high' | 'medium' | 'low';
  description: string;
  implementation: string;
  wcagCriteria: string[];
}

export interface ComplianceMetrics {
  totalTests: number;
  passedTests: number;
  failedTests: number;
  incompleteTests: number;
  complianceScore: number;
  criticalIssues: number;
  seriousIssues: number;
  moderateIssues: number;
  minorIssues: number;
}

// Priority weights for violations
const VIOLATION_WEIGHTS = {
  critical: 4,
  serious: 3,
  moderate: 2,
  minor: 1,
};

// WCAG compliance checker class
export class WCAGComplianceChecker {
  private axe: unknown;
  private testResults: AxeResults | null = null;

  constructor() {
    this.initializeAxe();
  }

  private async initializeAxe() {
    if (typeof window !== 'undefined') {
      const axeModule = await import('axe-core');
      this.axe = (axeModule as { default?: unknown } & typeof axeModule).default || axeModule;
    }
  }

  /**
   * Run comprehensive WCAG 2.1 AA compliance test
   */
  async runComplianceTest(context?: string): Promise<WCAGComplianceReport> {
    try {
      // Run axe-core accessibility tests
      const results = await this.runAxeTests(context);
      
      // Analyze results for WCAG compliance
      const violations = this.analyzeViolations(results.violations);
      const passes = this.analyzePasses(results.passes);
      const incomplete = this.analyzeIncomplete(results.incomplete);
      
      // Calculate metrics
      const metrics = this.calculateMetrics(violations, passes, incomplete);
      
      // Generate recommendations
      const recommendations = this.generateRecommendations(violations, incomplete);
      
      // Determine compliance level
      const complianceLevel = this.determineComplianceLevel(metrics);
      
      const report: WCAGComplianceReport = {
        timestamp: new Date(),
        overallScore: metrics.complianceScore,
        level: complianceLevel,
        violations,
        passes,
        incomplete,
        recommendations,
        metrics,
      };

      // Log compliance check
      await auditLogger.log('INFO', 'accessibility_test_completed', {
        complianceLevel,
        score: metrics.complianceScore,
        violationsCount: violations.length,
        criticalIssues: metrics.criticalIssues,
      });

      return report;
    } catch (error) {
      console.error('WCAG compliance test failed:', error);
      throw new Error(`Compliance test failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Run axe-core accessibility tests
   */
  private async runAxeTests(context?: string): Promise<AxeResults> {
    if (!this.axe) {
      throw new Error('Axe-core not initialized');
    }

    const axe = this.axe as { run: (context?: string | Record<string, unknown>, options?: Record<string, unknown>) => Promise<AxeResults> };

    const options = {
      runOnly: {
        type: 'tag',
        values: ['wcag2aa', 'wcag21aa'],
      },
      reporter: 'v2',
      resultTypes: ['violations', 'passes', 'incomplete'],
    };

    if (context) {
      return await axe.run(context, options);
    } else {
      return await axe.run(options);
    }
  }

  /**
   * Analyze axe violations and map to WCAG criteria
   */
  private analyzeViolations(violations: Result[]): Violation[] {
    return violations.map(violation => {
      const wcagCriteria = this.mapRuleToWCAG(violation.id);
      const priority = this.calculatePriority(violation.impact || 'minor');

      return {
        id: violation.id,
        impact: (violation.impact || 'minor') as 'minor' | 'moderate' | 'serious' | 'critical',
        wcagCriteria,
        description: violation.description,
        help: violation.help,
        helpUrl: violation.helpUrl,
        nodes: violation.nodes,
        priority,
      };
    });
  }

  /**
   * Analyze passed tests
   */
  private analyzePasses(passes: Result[]): Pass[] {
    return passes.map(pass => ({
      ruleId: pass.id,
      description: pass.description,
      wcagCriteria: this.mapRuleToWCAG(pass.id),
      nodes: pass.nodes,
    }));
  }

  /**
   * Analyze incomplete tests
   */
  private analyzeIncomplete(incomplete: Result[]): Incomplete[] {
    return incomplete.map(item => ({
      ruleId: item.id,
      description: item.description,
      wcagCriteria: this.mapRuleToWCAG(item.id),
      nodes: item.nodes,
      reason: 'Requires manual testing or additional context',
    }));
  }

  /**
   * Map axe rules to WCAG criteria
   */
  private mapRuleToWCAG(ruleId: string): string[] {
    const ruleToWCAG: Record<string, string[]> = {
      'color-contrast': ['1.4.3'],
      'keyboard': ['2.1.1'],
      'focus-order-semantics': ['2.4.3'],
      'label': ['1.3.1', '3.3.2'],
      'link-name': ['2.4.4', '1.1.1'],
      'list': ['1.3.1'],
      'listitem': ['1.3.1'],
      'heading-order': ['1.3.1', '2.4.6'],
      'html-has-lang': ['3.1.1'],
      'page-has-heading-one': ['1.3.1', '2.4.6'],
      'frame-title': ['2.4.1', '4.1.2'],
      'image-alt': ['1.1.1'],
      'image-redundant-alt': ['1.1.1'],
      'input-button-name': ['1.3.1', '3.3.2'],
      'label-title-only': ['3.3.2'],
      'skip-link': ['2.4.1'],
      'tabindex': ['2.1.1', '2.4.3'],
      'aria-required-attr': ['4.1.2'],
      'aria-required-children': ['1.3.1'],
      'aria-required-parent': ['1.3.1'],
      'aria-roles': ['4.1.2'],
      'aria-valid-attr': ['4.1.2'],
      'aria-valid-attr-value': ['4.1.2'],
      'button-name': ['1.3.1', '3.3.2'],
      'bypass': ['2.4.1'],
      'document-title': ['2.4.2'],
      'duplicate-id': ['4.1.1'],
      'form-field-multiple-labels': ['3.3.2'],
      'header-present': ['1.3.1', '2.4.6'],
      'landmark-one-main': ['1.3.6', '2.4.1'],
      'landmark-roles': ['1.3.6', '2.4.1'],
      'meta-viewport': ['1.4.4'],
      'meta-viewport-large': ['1.4.4'],
      'object-alt': ['1.1.1'],
      'video-caption': ['1.2.2'],
      'definition-list': ['1.3.1'],
      'dlitem': ['1.3.1'],
      'region': ['1.3.6', '2.4.1'],
      'scope-attr-valid': ['1.3.1'],
      'server-side-image-map': ['2.1.1'],
      'table-headers': ['1.3.1'],
      'th-has-data-cells': ['1.3.1'],
      'td-headers-attr': ['1.3.1'],
      'aria-hidden-body': ['4.1.2'],
      'aria-hidden-focus': ['4.1.2'],
      'focus-visible-content': ['2.4.7'],
      'focus-trap': ['2.1.2'],
      'aria-input-field-name': ['1.3.1', '3.3.2'],
      'aria-toggle-field-name': ['1.3.1', '3.3.2'],
      'aria-textbox': ['4.1.2'],
      'aria-command-name': ['4.1.2'],
      'aria-meter': ['4.1.2'],
      'aria-progressbar-name': ['4.1.2'],
      'aria-scrollbar-name': ['4.1.2'],
      'aria-slider-name': ['4.1.2'],
      'aria-switch-name': ['4.1.2'],
      'aria-toggle-button-name': ['4.1.2'],
      'aria-treeitem-name': ['4.1.2'],
      'role-img-alt': ['1.1.1'],
      'role-link-name': ['2.4.4', '1.1.1'],
      'role-img': ['1.1.1'],
      'svg-img-alt': ['1.1.1'],
      'area-alt': ['1.1.1'],
      'image-map': ['1.1.1'],
      'map-name': ['1.3.1'],
      'no-autoplay-audio': ['1.4.2'],
      'avoid-inline-styles': ['1.3.2'],
      'css-contrast': ['1.4.3'],
      'css-letter-spacing': ['1.4.12'],
      'css-line-height': ['1.4.12'],
      'css-text-spacing': ['1.4.12'],
      'css-word-spacing': ['1.4.12'],
      'has-lang': ['3.1.1'],
      'html-lang-valid': ['3.1.1'],
      'landmark-no-duplicate-banner': ['1.3.6', '2.4.1'],
      'landmark-no-duplicate-contentinfo': ['1.3.6', '2.4.1'],
      'no-autoplay-audio-updated': ['1.4.2'],
      'p-as-heading': ['1.3.1', '2.4.6'],
      'presentation-role-conflict': ['1.3.1'],
      'scrollable-region-focusable': ['2.1.1'],
      'select-name': ['1.3.1', '3.3.2'],
      'target-size': ['2.5.5'],
      'title-only': ['2.4.2'],
      'video-description': ['1.2.5'],
      'video-title': ['1.2.1'],
      'accesskeys': ['2.1.1'],
      'aria-allowed-attr': ['4.1.2'],
      'blink': ['2.3.1'],
      'checkboxgroup': ['1.3.1', '3.3.2'],
      'empty-heading': ['1.3.1', '2.4.6'],
      'empty-table-header': ['1.3.1'],
      'frame-tested': ['4.1.2'],
      'hidden-content': ['4.1.2'],
      'image-button-alt': ['1.1.1'],
      'label-content-name-mismatch': ['3.3.2'],
      'landmark-banner-is-top-level': ['1.3.6', '2.4.1'],
      'landmark-contentinfo-is-top-level': ['1.3.6', '2.4.1'],
      'landmark-main-is-top-level': ['1.3.6', '2.4.1'],
      'link-in-text-block': ['1.4.1'],
      'meta-refresh': ['2.2.1'],
      'nested-interactive': ['1.3.1'],
      'radiogroup': ['1.3.1', '3.3.2'],
    };

    return ruleToWCAG[ruleId] || [];
  }

  /**
   * Calculate priority for violations
   */
  private calculatePriority(impact: string): number {
    return VIOLATION_WEIGHTS[impact as keyof typeof VIOLATION_WEIGHTS] || 1;
  }

  /**
   * Calculate compliance metrics
   */
  private calculateMetrics(
    violations: Violation[],
    passes: Pass[],
    incomplete: Incomplete[]
  ): ComplianceMetrics {
    const totalTests = violations.length + passes.length + incomplete.length;
    const passedTests = passes.length;
    const failedTests = violations.length;
    const incompleteTests = incomplete.length;

    // Calculate weighted compliance score
    let weightedViolations = 0;
    violations.forEach(violation => {
      weightedViolations += VIOLATION_WEIGHTS[violation.impact] * violation.priority;
    });

    const maxPossibleScore = totalTests * 4; // Maximum weight is 4 (critical)
    const complianceScore = Math.max(0, 100 - (weightedViolations / maxPossibleScore) * 100);

    // Count issues by severity
    const criticalIssues = violations.filter(v => v.impact === 'critical').length;
    const seriousIssues = violations.filter(v => v.impact === 'serious').length;
    const moderateIssues = violations.filter(v => v.impact === 'moderate').length;
    const minorIssues = violations.filter(v => v.impact === 'minor').length;

    return {
      totalTests,
      passedTests,
      failedTests,
      incompleteTests,
      complianceScore: Math.round(complianceScore * 100) / 100,
      criticalIssues,
      seriousIssues,
      moderateIssues,
      minorIssues,
    };
  }

  /**
   * Generate accessibility recommendations
   */
  private generateRecommendations(violations: Violation[], incomplete: Incomplete[]): Recommendation[] {
    const recommendations: Recommendation[] = [];

    // Analyze violations and generate specific recommendations
    violations.forEach(violation => {
      const recommendation = this.generateViolationRecommendation(violation);
      if (recommendation) {
        recommendations.push(recommendation);
      }
    });

    // Generate recommendations for incomplete tests
    incomplete.forEach(item => {
      const recommendation = this.generateIncompleteRecommendation(item);
      if (recommendation) {
        recommendations.push(recommendation);
      }
    });

    // Sort by priority
    recommendations.sort((a, b) => {
      const priorityOrder = { high: 3, medium: 2, low: 1 };
      return priorityOrder[b.priority] - priorityOrder[a.priority];
    });

    return recommendations;
  }

  /**
   * Generate recommendation for specific violation
   */
  private generateViolationRecommendation(violation: Violation): Recommendation | null {
    const recommendationMap: Record<string, Recommendation> = {
      'color-contrast': {
        category: 'color',
        priority: 'high',
        description: 'Ensure text has sufficient color contrast',
        implementation: 'Increase color contrast to meet WCAG AA standards (4.5:1 for normal text, 3:1 for large text)',
        wcagCriteria: ['1.4.3'],
      },
      'keyboard': {
        category: 'keyboard',
        priority: 'high',
        description: 'Ensure all interactive elements are keyboard accessible',
        implementation: 'Add keyboard event handlers and ensure proper focus management',
        wcagCriteria: ['2.1.1'],
      },
      'image-alt': {
        category: 'semantic',
        priority: 'high',
        description: 'Provide alternative text for images',
        implementation: 'Add descriptive alt attributes to all meaningful images',
        wcagCriteria: ['1.1.1'],
      },
      'label': {
        category: 'semantic',
        priority: 'high',
        description: 'Ensure form inputs have proper labels',
        implementation: 'Add label elements or aria-label attributes to form inputs',
        wcagCriteria: ['1.3.1', '3.3.2'],
      },
      'focus-order-semantics': {
        category: 'focus',
        priority: 'medium',
        description: 'Ensure logical focus order',
        implementation: 'Structure content with proper semantic HTML and tabindex management',
        wcagCriteria: ['2.4.3'],
      },
      'aria-required-attr': {
        category: 'aria',
        priority: 'high',
        description: 'Add required ARIA attributes',
        implementation: 'Include all required ARIA attributes for the role being used',
        wcagCriteria: ['4.1.2'],
      },
      'heading-order': {
        category: 'semantic',
        priority: 'medium',
        description: 'Maintain proper heading hierarchy',
        implementation: 'Use heading levels sequentially without skipping levels',
        wcagCriteria: ['1.3.1', '2.4.6'],
      },
      'link-name': {
        category: 'semantic',
        priority: 'medium',
        description: 'Provide descriptive link text',
        implementation: 'Ensure links have meaningful text that describes their destination',
        wcagCriteria: ['2.4.4', '1.1.1'],
      },
    };

    return recommendationMap[violation.id] || null;
  }

  /**
   * Generate recommendation for incomplete test
   */
  private generateIncompleteRecommendation(item: Incomplete): Recommendation | null {
    const incompleteMap: Record<string, Recommendation> = {
      'color-contrast': {
        category: 'color',
        priority: 'medium',
        description: 'Verify color contrast manually',
        implementation: 'Use color contrast checker tools to verify text meets WCAG standards',
        wcagCriteria: ['1.4.3'],
      },
      'video-caption': {
        category: 'media',
        priority: 'high',
        description: 'Add captions to videos',
        implementation: 'Provide synchronized captions for all video content',
        wcagCriteria: ['1.2.2'],
      },
      'audio-description': {
        category: 'media',
        priority: 'medium',
        description: 'Add audio descriptions to videos',
        implementation: 'Provide audio descriptions for important visual content in videos',
        wcagCriteria: ['1.2.5'],
      },
    };

    return incompleteMap[item.ruleId] || null;
  }

  /**
   * Determine WCAG compliance level
   */
  private determineComplianceLevel(metrics: ComplianceMetrics): 'A' | 'AA' | 'AAA' {
    if (metrics.complianceScore >= 95 && metrics.criticalIssues === 0 && metrics.seriousIssues === 0) {
      return 'AA';
    } else if (metrics.complianceScore >= 85 && metrics.criticalIssues === 0) {
      return 'A';
    } else {
      return 'A'; // Default to A level for non-compliant sites
    }
  }

  /**
   * Generate compliance report summary
   */
  generateSummary(report: WCAGComplianceReport): string {
    const { level, overallScore, metrics } = report;
    
    let summary = `WCAG ${level} Compliance Score: ${overallScore}%\n\n`;
    summary += `Test Results:\n`;
    summary += `- Total Tests: ${metrics.totalTests}\n`;
    summary += `- Passed: ${metrics.passedTests}\n`;
    summary += `- Failed: ${metrics.failedTests}\n`;
    summary += `- Incomplete: ${metrics.incompleteTests}\n\n`;
    
    summary += `Issues by Severity:\n`;
    summary += `- Critical: ${metrics.criticalIssues}\n`;
    summary += `- Serious: ${metrics.seriousIssues}\n`;
    summary += `- Moderate: ${metrics.moderateIssues}\n`;
    summary += `- Minor: ${metrics.minorIssues}\n\n`;
    
    if (report.recommendations.length > 0) {
      summary += `Top Recommendations:\n`;
      report.recommendations.slice(0, 5).forEach((rec, index) => {
        summary += `${index + 1}. [${rec.priority.toUpperCase()}] ${rec.description}\n`;
      });
    }
    
    return summary;
  }

  /**
   * Export report to JSON
   */
  exportReport(report: WCAGComplianceReport): string {
    return JSON.stringify(report, null, 2);
  }

  /**
   * Export report to CSV
   */
  exportToCSV(report: WCAGComplianceReport): string {
    const headers = ['Type', 'Rule ID', 'Impact', 'WCAG Criteria', 'Description', 'Help URL'];
    const rows = [headers.join(',')];
    
    // Add violations
    report.violations.forEach(violation => {
      const row = [
        'Violation',
        violation.id,
        violation.impact,
        violation.wcagCriteria.join(';'),
        `"${violation.description}"`,
        violation.helpUrl,
      ];
      rows.push(row.join(','));
    });
    
    // Add incomplete
    report.incomplete.forEach(item => {
      const row = [
        'Incomplete',
        item.ruleId,
        'N/A',
        item.wcagCriteria.join(';'),
        `"${item.description}"`,
        'N/A',
      ];
      rows.push(row.join(','));
    });
    
    return rows.join('\n');
  }
}

// Singleton instance
export const wcagComplianceChecker = new WCAGComplianceChecker();

// Convenience function for running compliance tests
export async function runWCAGComplianceTest(context?: string): Promise<WCAGComplianceReport> {
  return await wcagComplianceChecker.runComplianceTest(context);
}