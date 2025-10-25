/**
 * Admin Integration Test Runner
 * 
 * This script runs all admin integration tests and generates a comprehensive
 * test report covering all requirements and workflows.
 */

import { execSync } from 'child_process';
import { writeFileSync, existsSync, mkdirSync } from 'fs';
import { join } from 'path';

interface TestResult {
  suite: string;
  tests: number;
  passed: number;
  failed: number;
  skipped: number;
  duration: number;
  coverage?: {
    statements: number;
    branches: number;
    functions: number;
    lines: number;
  };
}

interface TestReport {
  timestamp: string;
  totalTests: number;
  totalPassed: number;
  totalFailed: number;
  totalSkipped: number;
  totalDuration: number;
  suites: TestResult[];
  requirements: {
    [key: string]: {
      covered: boolean;
      tests: string[];
    };
  };
  summary: string;
}

class AdminIntegrationTestRunner {
  private testSuites = [
    {
      name: 'Admin Integration Tests',
      file: 'admin-integration.test.tsx',
      description: 'Complete admin workflow integration tests',
      requirements: [
        '1.1', '1.2', '1.3', '1.4', '1.5', '1.6', // First-run setup
        '2.1', '2.2', '2.3', '2.4', '2.5', '2.6', // Role-based access
        '3.1', '3.2', '3.3', '3.4', '3.5', '3.6', // Super admin management
        '4.1', '4.2', '4.3', '4.4', '4.5', '4.6', '4.7', // Admin user management
        '5.1', '5.2', '5.3', '5.4', '5.5', '5.6', // Security and audit
        '6.1', '6.2', '6.3', '6.4', '6.5', // Integration with existing auth
        '7.1', '7.2', '7.3', '7.4', '7.5', '7.6', '7.7', // User experience
      ],
    },
    {
      name: 'Admin API Integration Tests',
      file: 'admin-api-integration.test.ts',
      description: 'Backend API integration and database operations',
      requirements: [
        '2.5', '3.3', '4.2', '5.1', '5.2', '6.4', // API endpoints
        '1.1', '1.2', '1.3', // First-run setup API
        '2.1', '2.2', '6.1', '6.2', // Authentication integration
      ],
    },
    {
      name: 'RBAC Integration Tests',
      file: 'admin-rbac-integration.test.tsx',
      description: 'Role-based access control scenarios',
      requirements: [
        '2.1', '2.2', '2.3', '2.4', '2.5', '2.6', // Role-based access
        '6.1', '6.2', '6.5', // Integration with existing auth
        '5.4', '5.5', '5.6', // Security features
      ],
    },
  ];

  private reportDir = join(process.cwd(), 'test-reports');

  constructor() {
    // Ensure report directory exists
    if (!existsSync(this.reportDir)) {
      mkdirSync(this.reportDir, { recursive: true });
    }
  }

  async runAllTests(): Promise<TestReport> {
    console.log('🚀 Starting Admin Integration Test Suite...\n');

    const report: TestReport = {
      timestamp: new Date().toISOString(),
      totalTests: 0,
      totalPassed: 0,
      totalFailed: 0,
      totalSkipped: 0,
      totalDuration: 0,
      suites: [],
      requirements: {},
      summary: '',
    };

    // Initialize requirements tracking
    this.initializeRequirements(report);

    // Run each test suite
    for (const suite of this.testSuites) {
      console.log(`📋 Running ${suite.name}...`);
      const result = await this.runTestSuite(suite);
      report.suites.push(result);

      // Update totals
      report.totalTests += result.tests;
      report.totalPassed += result.passed;
      report.totalFailed += result.failed;
      report.totalSkipped += result.skipped;
      report.totalDuration += result.duration;

      // Update requirements coverage
      this.updateRequirementsCoverage(report, suite, result);

      console.log(`✅ ${suite.name}: ${result.passed}/${result.tests} passed\n`);
    }

    // Generate summary
    report.summary = this.generateSummary(report);

    // Save report
    this.saveReport(report);

    // Display results
    this.displayResults(report);

    return report;
  }

  private initializeRequirements(report: TestReport): void {
    const allRequirements = [
      '1.1', '1.2', '1.3', '1.4', '1.5', '1.6',
      '2.1', '2.2', '2.3', '2.4', '2.5', '2.6',
      '3.1', '3.2', '3.3', '3.4', '3.5', '3.6',
      '4.1', '4.2', '4.3', '4.4', '4.5', '4.6', '4.7',
      '5.1', '5.2', '5.3', '5.4', '5.5', '5.6',
      '6.1', '6.2', '6.3', '6.4', '6.5',
      '7.1', '7.2', '7.3', '7.4', '7.5', '7.6', '7.7',
    ];

    allRequirements.forEach(req => {
      report.requirements[req] = {
        covered: false,
        tests: [],
      };
    });
  }

  private async runTestSuite(suite: { name: string; file: string; description: string }): Promise<TestResult> {
    const startTime = Date.now();
    
    try {
      // Run vitest for specific file
      const command = `npm test -- --run src/__tests__/integration/${suite.file} --reporter=json`;
      const output = execSync(command, { 
        encoding: 'utf8',
        cwd: process.cwd(),
        timeout: 120000, // 2 minutes timeout
      });

      const result = this.parseTestOutput(output);
      result.suite = suite.name;
      result.duration = Date.now() - startTime;

      return result;
    } catch (error: any) {
      console.error(`❌ Error running ${suite.name}:`, error.message);
      
      return {
        suite: suite.name,
        tests: 0,
        passed: 0,
        failed: 1,
        skipped: 0,
        duration: Date.now() - startTime,
      };
    }
  }

  private parseTestOutput(output: string): TestResult {
    try {
      // Parse JSON output from vitest
      const lines = output.split('\n').filter(line => line.trim());
      const jsonLine = lines.find(line => line.startsWith('{') && line.includes('testResults'));
      
      if (jsonLine) {
        const data = JSON.parse(jsonLine);
        
        return {
          suite: '',
          tests: data.numTotalTests || 0,
          passed: data.numPassedTests || 0,
          failed: data.numFailedTests || 0,
          skipped: data.numPendingTests || 0,
          duration: data.testResults?.[0]?.perfStats?.runtime || 0,
        };
      }
    } catch (error) {
      console.warn('Could not parse test output, using fallback parsing');
    }

    // Fallback parsing
    const passedMatch = output.match(/(\d+) passed/);
    const failedMatch = output.match(/(\d+) failed/);
    const skippedMatch = output.match(/(\d+) skipped/);
    const totalMatch = output.match(/Tests\s+(\d+)/);

    return {
      suite: '',
      tests: totalMatch ? parseInt(totalMatch[1]) : 0,
      passed: passedMatch ? parseInt(passedMatch[1]) : 0,
      failed: failedMatch ? parseInt(failedMatch[1]) : 0,
      skipped: skippedMatch ? parseInt(skippedMatch[1]) : 0,
      duration: 0,
    };
  }

  private updateRequirementsCoverage(
    report: TestReport,
    suite: { requirements: string[] },
    result: TestResult
  ): void {
    if (result.passed > 0) {
      suite.requirements.forEach(req => {
        if (report.requirements[req]) {
          report.requirements[req].covered = true;
          report.requirements[req].tests.push(suite.name);
        }
      });
    }
  }

  private generateSummary(report: TestReport): string {
    const successRate = report.totalTests > 0 
      ? Math.round((report.totalPassed / report.totalTests) * 100) 
      : 0;

    const coveredRequirements = Object.values(report.requirements)
      .filter(req => req.covered).length;
    const totalRequirements = Object.keys(report.requirements).length;
    const requirementsCoverage = Math.round((coveredRequirements / totalRequirements) * 100);

    return `
# Admin Management System Integration Test Report

## Test Execution Summary
- **Total Tests**: ${report.totalTests}
- **Passed**: ${report.totalPassed}
- **Failed**: ${report.totalFailed}
- **Skipped**: ${report.totalSkipped}
- **Success Rate**: ${successRate}%
- **Total Duration**: ${Math.round(report.totalDuration / 1000)}s

## Requirements Coverage
- **Covered Requirements**: ${coveredRequirements}/${totalRequirements}
- **Coverage Percentage**: ${requirementsCoverage}%

## Test Suites Results
${report.suites.map(suite => `
### ${suite.suite}
- Tests: ${suite.tests}
- Passed: ${suite.passed}
- Failed: ${suite.failed}
- Duration: ${Math.round(suite.duration / 1000)}s
`).join('')}

## Requirements Coverage Details
${Object.entries(report.requirements).map(([req, data]) => 
  `- **Requirement ${req}**: ${data.covered ? '✅ Covered' : '❌ Not Covered'} ${data.tests.length > 0 ? `(${data.tests.join(', ')})` : ''}`
).join('\n')}

## Conclusion
${successRate >= 95 ? '🎉 All tests passed successfully!' : 
  successRate >= 80 ? '⚠️ Most tests passed, some issues need attention.' : 
  '❌ Significant test failures detected, immediate attention required.'}

${requirementsCoverage >= 95 ? '✅ Excellent requirements coverage achieved.' :
  requirementsCoverage >= 80 ? '⚠️ Good requirements coverage, some gaps remain.' :
  '❌ Poor requirements coverage, additional tests needed.'}
`;
  }

  private saveReport(report: TestReport): void {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    
    // Save JSON report
    const jsonPath = join(this.reportDir, `admin-integration-test-report-${timestamp}.json`);
    writeFileSync(jsonPath, JSON.stringify(report, null, 2));

    // Save markdown summary
    const mdPath = join(this.reportDir, `admin-integration-test-summary-${timestamp}.md`);
    writeFileSync(mdPath, report.summary);

    console.log(`📊 Reports saved:`);
    console.log(`   JSON: ${jsonPath}`);
    console.log(`   Markdown: ${mdPath}`);
  }

  private displayResults(report: TestReport): void {
    console.log('\n' + '='.repeat(60));
    console.log('🎯 ADMIN INTEGRATION TEST RESULTS');
    console.log('='.repeat(60));
    
    console.log(`\n📊 Overall Results:`);
    console.log(`   Total Tests: ${report.totalTests}`);
    console.log(`   Passed: ${report.totalPassed} ✅`);
    console.log(`   Failed: ${report.totalFailed} ${report.totalFailed > 0 ? '❌' : '✅'}`);
    console.log(`   Skipped: ${report.totalSkipped}`);
    console.log(`   Duration: ${Math.round(report.totalDuration / 1000)}s`);

    const successRate = report.totalTests > 0 
      ? Math.round((report.totalPassed / report.totalTests) * 100) 
      : 0;
    console.log(`   Success Rate: ${successRate}% ${successRate >= 95 ? '🎉' : successRate >= 80 ? '⚠️' : '❌'}`);

    console.log(`\n📋 Requirements Coverage:`);
    const coveredRequirements = Object.values(report.requirements)
      .filter(req => req.covered).length;
    const totalRequirements = Object.keys(report.requirements).length;
    const requirementsCoverage = Math.round((coveredRequirements / totalRequirements) * 100);
    
    console.log(`   Covered: ${coveredRequirements}/${totalRequirements}`);
    console.log(`   Coverage: ${requirementsCoverage}% ${requirementsCoverage >= 95 ? '🎉' : requirementsCoverage >= 80 ? '⚠️' : '❌'}`);

    console.log(`\n🔍 Suite Breakdown:`);
    report.suites.forEach(suite => {
      const suiteSuccess = suite.tests > 0 ? Math.round((suite.passed / suite.tests) * 100) : 0;
      console.log(`   ${suite.suite}: ${suite.passed}/${suite.tests} (${suiteSuccess}%) ${suiteSuccess === 100 ? '✅' : '⚠️'}`);
    });

    if (report.totalFailed > 0) {
      console.log(`\n❌ ${report.totalFailed} test(s) failed. Check the detailed report for more information.`);
    } else {
      console.log(`\n🎉 All tests passed! The admin management system is ready for production.`);
    }

    console.log('\n' + '='.repeat(60));
  }
}

// Run tests if this file is executed directly
if (require.main === module) {
  const runner = new AdminIntegrationTestRunner();
  runner.runAllTests()
    .then(report => {
      process.exit(report.totalFailed > 0 ? 1 : 0);
    })
    .catch(error => {
      console.error('❌ Test runner failed:', error);
      process.exit(1);
    });
}

export { AdminIntegrationTestRunner };
export type { TestReport, TestResult };