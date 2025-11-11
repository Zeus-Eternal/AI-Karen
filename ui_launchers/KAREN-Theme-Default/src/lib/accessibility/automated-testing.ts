// ui_launchers/KAREN-Theme-Default/src/lib/accessibility/automated-testing.ts
import * as axe from 'axe-core';
import { AxeResults, RunOptions, RuleObject } from 'axe-core';
import { Page } from '@playwright/test';

// Configuration for different testing scenarios
export interface AccessibilityTestConfig {
  rules?: RuleObject;
  tags?: string[];
  exclude?: string[];
  include?: string[];
  timeout?: number;
  reporter?: 'json' | 'html' | 'junit' | 'sarif';
  outputPath?: string;
  thresholds?: {
    critical?: number;
    serious?: number;
    moderate?: number;
    minor?: number;
  };
}

// Test result interfaces
export interface AccessibilityTestResult {
  url: string;
  timestamp: string;
  testConfig: AccessibilityTestConfig;
  axeResults: AxeResults;
  summary: {
    violations: number;
    passes: number;
    incomplete: number;
    inapplicable: number;
  };
  violationsByImpact: {
    critical: number;
    serious: number;
    moderate: number;
    minor: number;
  };
  complianceScore: number;
  passed: boolean;
}

export interface AccessibilityRegressionResult {
  current: AccessibilityTestResult;
  baseline?: AccessibilityTestResult;
  regressions: Array<{
    ruleId: string;
    description: string;
    impact: string;
    newViolations: number;
    previousViolations: number;
  }>;
  improvements: Array<{
    ruleId: string;
    description: string;
    impact: string;
    fixedViolations: number;
  }>;
  hasRegressions: boolean;
}

// Predefined test configurations
export const AccessibilityTestConfigs = {
  // Basic WCAG 2.0 A compliance
  wcag2a: {
    tags: ['wcag2a'],
    timeout: 30000,
    thresholds: {
      critical: 0,
      serious: 0,
      moderate: 5,
      minor: 10
    }
  } as AccessibilityTestConfig,
  
  // WCAG 2.1 AA compliance (recommended)
  wcag2aa: {
    tags: ['wcag2a', 'wcag2aa'],
    timeout: 45000,
    thresholds: {
      critical: 0,
      serious: 0,
      moderate: 3,
      minor: 8
    }
  } as AccessibilityTestConfig,
  
  // WCAG 2.1 AAA compliance (strict)
  wcag2aaa: {
    tags: ['wcag2a', 'wcag2aa', 'wcag2aaa'],
    timeout: 60000,
    thresholds: {
      critical: 0,
      serious: 0,
      moderate: 0,
      minor: 3
    }
  } as AccessibilityTestConfig,
  
  // Best practices and experimental rules
  comprehensive: {
    tags: ['wcag2a', 'wcag2aa', 'wcag21aa', 'best-practice'],
    timeout: 60000,
    thresholds: {
      critical: 0,
      serious: 2,
      moderate: 5,
      minor: 10
    }
  } as AccessibilityTestConfig,

  // Form-specific testing
  forms: {
    tags: ['wcag2a', 'wcag2aa'],
    rules: {
      'label': { enabled: true },
      'label-title-only': { enabled: true },
      'form-field-multiple-labels': { enabled: true },
      'select-name': { enabled: true },
      'input-button-name': { enabled: true },
      'input-image-alt': { enabled: true }
    },
    timeout: 30000
  } as AccessibilityTestConfig,

  // Navigation and interaction testing
  navigation: {
    tags: ['wcag2a', 'wcag2aa'],
    rules: {
      'focus-order-semantics': { enabled: true },
      'tabindex': { enabled: true },
      'keyboard': { enabled: true },
      'skip-link': { enabled: true },
      'landmark-one-main': { enabled: true },
      'landmark-complementary-is-top-level': { enabled: true }
    },
    timeout: 30000
  } as AccessibilityTestConfig,

  // Color and visual testing
  visual: {
    tags: ['wcag2a', 'wcag2aa'],
    rules: {
      'color-contrast': { enabled: true },
      'color-contrast-enhanced': { enabled: true },
      'link-in-text-block': { enabled: true },
      'focus-order-semantics': { enabled: true }
    },
    timeout: 30000
  } as AccessibilityTestConfig
};

/**
 * Automated Accessibility Tester Class
 */
export class AutomatedAccessibilityTester {
  private baselineResults: Map<string, AccessibilityTestResult> = new Map();
  private testHistory: AccessibilityTestResult[] = [];
  
  constructor(private defaultConfig: AccessibilityTestConfig = AccessibilityTestConfigs.wcag2aa) {}

  /**
   * Run accessibility test on a DOM element or document
   */
  async testElement(
    element: Element | Document,
    config: AccessibilityTestConfig = this.defaultConfig
  ): Promise<AccessibilityTestResult> {
    try {
      // Configure axe-core
      const runOptions: RunOptions = {
        runOnly: {
          type: 'tag',
          values: config.tags || ['wcag2a', 'wcag2aa']
        },
        rules: config.rules || {}
      };
      
      if (config.include) {
        (runOptions as unknown).include = config.include;
      }
      
      if (config.exclude) {
        (runOptions as unknown).exclude = config.exclude;
      }
      
      // Run axe-core analysis
      const axeResults = await axe.run(element, runOptions);
      
      // Calculate metrics
      const violationsByImpact = {
        critical: axeResults.violations.filter(v => v.impact === 'critical').length,
        serious: axeResults.violations.filter(v => v.impact === 'serious').length,
        moderate: axeResults.violations.filter(v => v.impact === 'moderate').length,
        minor: axeResults.violations.filter(v => v.impact === 'minor').length
      };
      
      const complianceScore = this.calculateComplianceScore(axeResults);
      const passed = this.evaluateThresholds(violationsByImpact, config.thresholds);
      
      const result: AccessibilityTestResult = {
        url: window.location.href,
        timestamp: new Date().toISOString(),
        testConfig: config,
        axeResults,
        summary: {
          violations: axeResults.violations.length,
          passes: axeResults.passes.length,
          incomplete: axeResults.incomplete.length,
          inapplicable: axeResults.inapplicable.length
        },
        violationsByImpact,
        complianceScore,
        passed
      };
      
      // Store in history
      this.testHistory.push(result);
      return result;
    } catch (error) {
      throw new Error(`Accessibility test failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Run accessibility test using Playwright page
   */
  async testPage(
    page: Page,
    config: AccessibilityTestConfig = this.defaultConfig
  ): Promise<AccessibilityTestResult> {
    try {
      // Inject axe-core into the page
      await page.addScriptTag({
        url: 'https://unpkg.com/axe-core@4.10.2/axe.min.js'
      });

      // Run axe analysis in the page context
      const runOptions = {
        runOnly: {
          type: 'tag',
          values: config.tags || ['wcag2a', 'wcag2aa']
        },
        rules: config.rules || {},
        ...(config.include && { include: config.include }),
        ...(config.exclude && { exclude: config.exclude })
      };
      
      const axeResults = await page.evaluate(async (options) => {
        return await (window as any).axe.run(document, options);
      }, runOptions);
      
      // Calculate metrics
      const violationsByImpact = {
        critical: axeResults.violations.filter((v: any) => v.impact === 'critical').length,
        serious: axeResults.violations.filter((v: any) => v.impact === 'serious').length,
        moderate: axeResults.violations.filter((v: any) => v.impact === 'moderate').length,
        minor: axeResults.violations.filter((v: any) => v.impact === 'minor').length
      };
      
      const complianceScore = this.calculateComplianceScore(axeResults);
      const passed = this.evaluateThresholds(violationsByImpact, config.thresholds);
      
      const result: AccessibilityTestResult = {
        url: page.url(),
        timestamp: new Date().toISOString(),
        testConfig: config,
        axeResults,
        summary: {
          violations: axeResults.violations.length,
          passes: axeResults.passes.length,
          incomplete: axeResults.incomplete.length,
          inapplicable: axeResults.inapplicable.length
        },
        violationsByImpact,
        complianceScore,
        passed
      };
      
      // Store in history
      this.testHistory.push(result);
      return result;
    } catch (error) {
      throw new Error(`Page accessibility test failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }
  
  /**
   * Set baseline results for regression testing
   */
  setBaseline(url: string, result: AccessibilityTestResult): void {
    this.baselineResults.set(url, result);
  }

  /**
   * Load baseline results from storage
   */
  async loadBaseline(baselinePath: string): Promise<void> {
    try {
      // In a real implementation, this would load from file system or database
      const baselineData = await fetch(baselinePath).then(response => response.json());
      if (Array.isArray(baselineData)) {
        baselineData.forEach((result: AccessibilityTestResult) => {
          this.baselineResults.set(result.url, result);
        });
      }
    } catch (error) {
      throw new Error(`Failed to load baseline: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Save baseline results to storage
   */
  async saveBaseline(baselinePath: string): Promise<void> {
    try {
      const baselineData = Array.from(this.baselineResults.values());
      // In a real implementation, this would save to file system or database
      const blob = new Blob([JSON.stringify(baselineData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = baselinePath;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      throw new Error(`Could not save baseline: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Compare current results with baseline for regression detection
   */
  detectRegressions(
    current: AccessibilityTestResult,
    baseline?: AccessibilityTestResult
  ): AccessibilityRegressionResult {
    const baselineResult = baseline || this.baselineResults.get(current.url);
    if (!baselineResult) {
      return {
        current,
        baseline: undefined,
        regressions: [],
        improvements: [],
        hasRegressions: false
      };
    }

    const regressions: AccessibilityRegressionResult['regressions'] = [];
    const improvements: AccessibilityRegressionResult['improvements'] = [];

    const currentViolations = new Map(
      current.axeResults.violations.map(v => [v.id, v.nodes.length])
    );

    const baselineViolations = new Map(
      baselineResult.axeResults.violations.map(v => [v.id, v.nodes.length])
    );

    for (const [ruleId, currentCount] of Array.from(currentViolations.entries())) {
      const baselineCount = baselineViolations.get(ruleId) || 0;
      if (currentCount > baselineCount) {
        const violation = current.axeResults.violations.find(v => v.id === ruleId);
        if (violation) {
          regressions.push({
            ruleId,
            description: violation.description,
            impact: violation.impact || 'unknown',
            newViolations: currentCount - baselineCount,
            previousViolations: baselineCount
          });
        }
      }
    }

    for (const [ruleId, baselineCount] of Array.from(baselineViolations.entries())) {
      const currentCount = currentViolations.get(ruleId) || 0;
      if (currentCount < baselineCount) {
        const violation = baselineResult.axeResults.violations.find(v => v.id === ruleId);
        if (violation) {
          improvements.push({
            ruleId,
            description: violation.description,
            impact: violation.impact || 'unknown',
            fixedViolations: baselineCount - currentCount
          });
        }
      }
    }

    return {
      current,
      baseline: baselineResult,
      regressions,
      improvements,
      hasRegressions: regressions.length > 0
    };
  }

  /**
   * Generate comprehensive test report
   */
  generateReport(
    results: AccessibilityTestResult[],
    format: 'json' | 'html' | 'junit' | 'sarif' = 'json'
  ): string {
    switch (format) {
      case 'json':
        return this.generateJSONReport(results);
      case 'html':
        return this.generateHTMLReport(results);
      case 'junit':
        return this.generateJUnitReport(results);
      case 'sarif':
        return this.generateSARIFReport(results);
      default:
        return this.generateJSONReport(results);
    }
  }

  /**
   * Calculate compliance score based on violations
   */
  private calculateComplianceScore(axeResults: AxeResults): number {
    const totalChecks = axeResults.violations.length + axeResults.passes.length;
    if (totalChecks === 0) return 100;

    const weightedViolations = axeResults.violations.reduce((sum, violation) => {
      const weight = this.getImpactWeight(violation.impact || 'unknown');
      return sum + (violation.nodes.length * weight);
    }, 0);

    const maxPossibleScore = totalChecks * 4;
    const score = Math.max(0, 100 - (weightedViolations / maxPossibleScore) * 100);
    return Math.round(score * 100) / 100;
  }

  /**
   * Get numeric weight for violation impact
   */
  private getImpactWeight(impact?: string): number {
    switch (impact) {
      case 'critical': return 4;
      case 'serious': return 3;
      case 'moderate': return 2;
      case 'minor': return 1;
      default: return 1;
    }
  }

  /**
   * Evaluate if results pass defined thresholds
   */
  private evaluateThresholds(
    violations: { critical: number; serious: number; moderate: number; minor: number },
    thresholds?: AccessibilityTestConfig['thresholds']
  ): boolean {
    if (!thresholds) return true;
    return (
      (thresholds.critical === undefined || violations.critical <= thresholds.critical) &&
      (thresholds.serious === undefined || violations.serious <= thresholds.serious) &&
      (thresholds.moderate === undefined || violations.moderate <= thresholds.moderate) &&
      (thresholds.minor === undefined || violations.minor <= thresholds.minor)
    );
  }

  /**
   * Generate JSON report
   */
  private generateJSONReport(results: AccessibilityTestResult[]): string {
    const report = {
      generatedAt: new Date().toISOString(),
      summary: {
        totalTests: results.length,
        passed: results.filter(r => r.passed).length,
        failed: results.filter(r => !r.passed).length,
        averageComplianceScore: results.reduce((sum, r) => sum + r.complianceScore, 0) / results.length
      },
      results
    };
    return JSON.stringify(report, null, 2);
  }

  /**
   * Generate HTML report
   */
  private generateHTMLReport(results: AccessibilityTestResult[]): string {
    const passed = results.filter(r => r.passed).length;
    const failed = results.filter(r => !r.passed).length;
    const avgScore = results.reduce((sum, r) => sum + r.complianceScore, 0) / results.length;
    return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Accessibility Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .summary { background: #f5f5f5; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .result { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }
        .passed { border-left: 5px solid #28a745; }
        .failed { border-left: 5px solid #dc3545; }
        .violation { background: #fff3cd; padding: 10px; margin: 5px 0; border-radius: 3px; }
        .critical { border-left: 3px solid #dc3545; }
        .serious { border-left: 3px solid #fd7e14; }
        .moderate { border-left: 3px solid #ffc107; }
        .minor { border-left: 3px solid #17a2b8; }
    </style>
</head>
<body>
    <h1>Accessibility Test Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Generated:</strong> ${new Date().toISOString()}</p>
        <p><strong>Total Tests:</strong> ${results.length}</p>
        <p><strong>Passed:</strong> ${passed}</p>
        <p><strong>Failed:</strong> ${failed}</p>
        <p><strong>Average Compliance Score:</strong> ${avgScore.toFixed(2)}%</p>
    </div>
    ${results.map(result => `
        <div class="result ${result.passed ? 'passed' : 'failed'}">
            <h3>${result.url}</h3>
            <p><strong>Compliance Score:</strong> ${result.complianceScore}%</p>
            <p><strong>Violations:</strong> ${result.summary.violations}</p>
            <p><strong>Passes:</strong> ${result.summary.passes}</p>
            ${result.axeResults.violations.map(violation => `
                <div class="violation ${violation.impact}">
                    <h4>${violation.description}</h4>
                    <p><strong>Impact:</strong> ${violation.impact}</p>
                    <p><strong>Nodes:</strong> ${violation.nodes.length}</p>
                    <p><strong>Help:</strong> <a href="${violation.helpUrl}" target="_blank">${violation.help}</a></p>
                </div>
            `).join('')}
        </div>
    `).join('')}
</body>
</html>`;
  }
  
  /**
   * Generate JUnit XML report
   */
  private generateJUnitReport(results: AccessibilityTestResult[]): string {
    const totalTests = results.length;
    const failures = results.filter(r => !r.passed).length;
    const time = results.reduce((sum, r) => sum + 1, 0); // Simplified time calculation
    return `<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="Accessibility Tests" tests="${totalTests}" failures="${failures}" time="${time}">
${results.map(result => `
    <testcase name="${result.url}" classname="AccessibilityTest" time="1">
        ${!result.passed ? `
            <failure message="Accessibility violations found">
                ${result.axeResults.violations.map(v => `${v.description}: ${v.nodes.length} violations`).join('\n')}
            </failure>
        ` : ''}
    </testcase>
`).join('')}
</testsuite>`;
  }
  
  /**
   * Generate SARIF report for security tools integration
   */
  private generateSARIFReport(results: AccessibilityTestResult[]): string {
    const sarif = {
      version: '2.1.0',
      $schema: 'https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json',
      runs: [{
        tool: {
          driver: {
            name: 'axe-core',
            version: '4.10.2',
            informationUri: 'https://github.com/dequelabs/axe-core'
          }
        },
        results: results.flatMap(result => 
          result.axeResults.violations.map(violation => ({
            ruleId: violation.id,
            message: {
              text: violation.description
            },
            level: this.mapImpactToLevel(violation.impact as string),
            locations: violation.nodes.map(node => ({
              physicalLocation: {
                artifactLocation: {
                  uri: result.url
                },
                region: {
                  snippet: {
                    text: node.html
                  }
                }
              }
            }))
          }))
        )
      }]
    };
    return JSON.stringify(sarif, null, 2);
  }
  
  /**
   * Map axe impact levels to SARIF levels
   */
  private mapImpactToLevel(impact?: string): string {
    switch (impact) {
      case 'critical': return 'error';
      case 'serious': return 'error';
      case 'moderate': return 'warning';
      case 'minor': return 'note';
      default: return 'note';
    }
  }
  
  /**
   * Get test history
   */
  getTestHistory(): AccessibilityTestResult[] {
    return [...this.testHistory];
  }
  
  /**
   * Clear test history
   */
  clearHistory(): void {
    this.testHistory = [];
  }
}

// Export singleton instance
export const accessibilityTester = new AutomatedAccessibilityTester();

// Export utility functions
export const runAccessibilityTest = (
  element: Element | Document,
  config?: AccessibilityTestConfig
) => accessibilityTester.testElement(element, config);

export const runPageAccessibilityTest = (
  page: Page,
  config?: AccessibilityTestConfig
) => accessibilityTester.testPage(page, config);

export default AutomatedAccessibilityTester;
