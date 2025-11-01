#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

class QAAutomation {
  constructor() {
    this.projectRoot = process.cwd();
    this.qaDir = path.join(this.projectRoot, 'qa-automation');
    this.reportsDir = path.join(this.qaDir, 'reports');
    this.configDir = path.join(this.qaDir, 'config');
    
    this.ensureDirectories();
  }

  ensureDirectories() {
    [this.qaDir, this.reportsDir, this.configDir].forEach(dir => {
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
    });
  }

  async runQualityChecks(options = {}) {
    console.log('🔍 Running comprehensive quality checks...');
    
    const checks = [
      { name: 'Unit Tests', runner: () => this.runUnitTests(options) },
      { name: 'Integration Tests', runner: () => this.runIntegrationTests(options) },
      { name: 'E2E Tests', runner: () => this.runE2ETests(options) },
      { name: 'Visual Tests', runner: () => this.runVisualTests(options) },
      { name: 'Performance Tests', runner: () => this.runPerformanceTests(options) },
      { name: 'Accessibility Tests', runner: () => this.runAccessibilityTests(options) },
      { name: 'Security Audit', runner: () => this.runSecurityAudit(options) },
      { name: 'Code Quality Analysis', runner: () => this.runCodeQualityAnalysis(options) }
    ];

    const results = {};
    const startTime = Date.now();

    for (const check of checks) {
      console.log(`\n--- Running ${check.name} ---`);
      try {
        results[check.name] = await check.runner();
        console.log(`✅ ${check.name}: ${results[check.name].success ? 'PASSED' : 'FAILED'}`);
      } catch (error) {
        results[check.name] = { success: false, error: error.message };
        console.log(`❌ ${check.name}: FAILED - ${error.message}`);
      }
    }

    const duration = Date.now() - startTime;
    
    // Generate comprehensive report
    const report = await this.generateQualityReport(results, duration);
    
    // Check quality gates
    const gateResults = await this.checkQualityGates(results);
    
    console.log('\n📊 Quality Check Summary:');
    console.log(`  Duration: ${(duration / 1000).toFixed(2)}s`);
    console.log(`  Passed Checks: ${Object.values(results).filter(r => r.success).length}/${Object.keys(results).length}`);
    console.log(`  Quality Gates: ${gateResults.passed}/${gateResults.total} passed`);
    
    if (gateResults.failed.length > 0) {
      console.log('\n❌ Failed Quality Gates:');
      gateResults.failed.forEach(gate => {
        console.log(`  - ${gate.name}: ${gate.actual} (required: ${gate.threshold})`);
      });
    }

    return {
      results,
      report,
      gateResults,
      duration,
      success: gateResults.failed.length === 0
    };
  }

  async runUnitTests(options = {}) {
    try {
      const command = [
        'npm run test:unit',
        '--coverage',
        '--reporter=json',
        options.watch ? '--watch' : '',
        options.verbose ? '--verbose' : ''
      ].filter(Boolean).join(' ');

      const output = execSync(command, {
        cwd: this.projectRoot,
        encoding: 'utf8',
        stdio: options.silent ? 'pipe' : 'inherit'
      });

      const results = this.parseTestResults(output);
      
      return {
        success: results.failed === 0,
        total: results.total,
        passed: results.passed,
        failed: results.failed,
        coverage: results.coverage,
        duration: results.duration
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        total: 0,
        passed: 0,
        failed: 0
      };
    }
  }

  async runIntegrationTests(options = {}) {
    try {
      const command = [
        'npm run test:integration',
        '--reporter=json',
        options.verbose ? '--verbose' : ''
      ].filter(Boolean).join(' ');

      const output = execSync(command, {
        cwd: this.projectRoot,
        encoding: 'utf8',
        stdio: options.silent ? 'pipe' : 'inherit'
      });

      const results = this.parseTestResults(output);
      
      return {
        success: results.failed === 0,
        total: results.total,
        passed: results.passed,
        failed: results.failed,
        duration: results.duration
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  async runE2ETests(options = {}) {
    try {
      const command = [
        'npx playwright test',
        'e2e/user-workflows',
        '--reporter=json',
        options.headed ? '--headed' : '',
        options.debug ? '--debug' : ''
      ].filter(Boolean).join(' ');

      const output = execSync(command, {
        cwd: this.projectRoot,
        encoding: 'utf8',
        stdio: options.silent ? 'pipe' : 'inherit'
      });

      const results = this.parsePlaywrightResults(output);
      
      return {
        success: results.failed === 0,
        total: results.total,
        passed: results.passed,
        failed: results.failed,
        duration: results.duration
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  async runVisualTests(options = {}) {
    try {
      const command = [
        'npx playwright test',
        'e2e/visual',
        '--reporter=json',
        options.updateSnapshots ? '--update-snapshots' : ''
      ].filter(Boolean).join(' ');

      const output = execSync(command, {
        cwd: this.projectRoot,
        encoding: 'utf8',
        stdio: options.silent ? 'pipe' : 'inherit'
      });

      const results = this.parsePlaywrightResults(output);
      
      return {
        success: results.failed === 0,
        total: results.total,
        passed: results.passed,
        failed: results.failed,
        visualDiffs: results.visualDiffs || 0,
        duration: results.duration
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  async runPerformanceTests(options = {}) {
    try {
      const command = [
        'node',
        'scripts/performance-test-runner.js',
        'all',
        options.headed ? '--headed' : ''
      ].filter(Boolean).join(' ');

      const output = execSync(command, {
        cwd: this.projectRoot,
        encoding: 'utf8',
        stdio: options.silent ? 'pipe' : 'inherit'
      });

      // Parse performance results
      const results = this.parsePerformanceResults(output);
      
      return {
        success: results.success,
        loadTime: results.loadTime,
        interactionTime: results.interactionTime,
        memoryUsage: results.memoryUsage,
        errorRate: results.errorRate,
        duration: results.duration
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  async runAccessibilityTests(options = {}) {
    try {
      const command = [
        'npx playwright test',
        'e2e/accessibility',
        '--reporter=json'
      ].join(' ');

      const output = execSync(command, {
        cwd: this.projectRoot,
        encoding: 'utf8',
        stdio: options.silent ? 'pipe' : 'inherit'
      });

      const results = this.parseAccessibilityResults(output);
      
      return {
        success: results.violations === 0,
        score: results.score,
        violations: results.violations,
        warnings: results.warnings,
        passes: results.passes,
        duration: results.duration
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  async runSecurityAudit(options = {}) {
    try {
      const auditCommand = 'npm audit --json';
      const auditOutput = execSync(auditCommand, {
        cwd: this.projectRoot,
        encoding: 'utf8',
        stdio: 'pipe'
      });

      const auditData = JSON.parse(auditOutput);
      
      const vulnerabilities = auditData.metadata?.vulnerabilities || {};
      const totalVulns = Object.values(vulnerabilities).reduce((a, b) => a + b, 0);
      
      return {
        success: vulnerabilities.critical === 0 && vulnerabilities.high === 0,
        vulnerabilities: {
          critical: vulnerabilities.critical || 0,
          high: vulnerabilities.high || 0,
          medium: vulnerabilities.medium || 0,
          low: vulnerabilities.low || 0
        },
        totalVulnerabilities: totalVulns,
        score: Math.max(0, 100 - (vulnerabilities.critical * 20 + vulnerabilities.high * 10))
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  async runCodeQualityAnalysis(options = {}) {
    try {
      // Run ESLint
      const lintCommand = 'npx eslint src --format json';
      let lintResults = [];
      
      try {
        const lintOutput = execSync(lintCommand, {
          cwd: this.projectRoot,
          encoding: 'utf8',
          stdio: 'pipe'
        });
        lintResults = JSON.parse(lintOutput);
      } catch (lintError) {
        // ESLint exits with non-zero code when issues are found
        if (lintError.stdout) {
          lintResults = JSON.parse(lintError.stdout);
        }
      }

      const errorCount = lintResults.reduce((sum, file) => sum + file.errorCount, 0);
      const warningCount = lintResults.reduce((sum, file) => sum + file.warningCount, 0);
      
      // Run TypeScript compiler check
      let typeCheckSuccess = true;
      try {
        execSync('npx tsc --noEmit', {
          cwd: this.projectRoot,
          stdio: 'pipe'
        });
      } catch (error) {
        typeCheckSuccess = false;
      }

      return {
        success: errorCount === 0 && typeCheckSuccess,
        linting: {
          errors: errorCount,
          warnings: warningCount,
          files: lintResults.length
        },
        typeCheck: typeCheckSuccess,
        maintainabilityScore: this.calculateMaintainabilityScore(lintResults)
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  parseTestResults(output) {
    try {
      const data = JSON.parse(output);
      return {
        total: data.numTotalTests || 0,
        passed: data.numPassedTests || 0,
        failed: data.numFailedTests || 0,
        coverage: data.coverageMap ? this.extractCoverage(data.coverageMap) : 0,
        duration: data.testResults?.reduce((sum, result) => sum + (result.perfStats?.end - result.perfStats?.start || 0), 0) || 0
      };
    } catch (error) {
      return { total: 0, passed: 0, failed: 0, coverage: 0, duration: 0 };
    }
  }

  parsePlaywrightResults(output) {
    try {
      const data = JSON.parse(output);
      return {
        total: data.stats?.total || 0,
        passed: data.stats?.passed || 0,
        failed: data.stats?.failed || 0,
        duration: data.stats?.duration || 0,
        visualDiffs: data.stats?.visualDiffs || 0
      };
    } catch (error) {
      return { total: 0, passed: 0, failed: 0, duration: 0 };
    }
  }

  parsePerformanceResults(output) {
    // Extract performance metrics from output
    const loadTimeMatch = output.match(/Average load time: (\d+)ms/);
    const interactionTimeMatch = output.match(/Average interaction time: (\d+)ms/);
    const memoryMatch = output.match(/Peak memory usage: (\d+)MB/);
    const errorRateMatch = output.match(/Error rate: ([\d.]+)%/);

    return {
      success: !output.includes('FAILED'),
      loadTime: loadTimeMatch ? parseInt(loadTimeMatch[1]) : 0,
      interactionTime: interactionTimeMatch ? parseInt(interactionTimeMatch[1]) : 0,
      memoryUsage: memoryMatch ? parseInt(memoryMatch[1]) : 0,
      errorRate: errorRateMatch ? parseFloat(errorRateMatch[1]) : 0,
      duration: 0
    };
  }

  parseAccessibilityResults(output) {
    // Parse accessibility test results
    const scoreMatch = output.match(/Accessibility score: (\d+)%/);
    const violationsMatch = output.match(/Violations: (\d+)/);
    const warningsMatch = output.match(/Warnings: (\d+)/);
    const passesMatch = output.match(/Passes: (\d+)/);

    return {
      score: scoreMatch ? parseInt(scoreMatch[1]) : 0,
      violations: violationsMatch ? parseInt(violationsMatch[1]) : 0,
      warnings: warningsMatch ? parseInt(warningsMatch[1]) : 0,
      passes: passesMatch ? parseInt(passesMatch[1]) : 0,
      duration: 0
    };
  }

  extractCoverage(coverageMap) {
    // Extract overall coverage percentage from coverage map
    let totalLines = 0;
    let coveredLines = 0;

    for (const file in coverageMap) {
      const fileCoverage = coverageMap[file];
      if (fileCoverage.s) {
        totalLines += Object.keys(fileCoverage.s).length;
        coveredLines += Object.values(fileCoverage.s).filter(count => count > 0).length;
      }
    }

    return totalLines > 0 ? Math.round((coveredLines / totalLines) * 100) : 0;
  }

  calculateMaintainabilityScore(lintResults) {
    // Simple maintainability score based on linting results
    const totalIssues = lintResults.reduce((sum, file) => sum + file.errorCount + file.warningCount, 0);
    const totalFiles = lintResults.length;
    
    if (totalFiles === 0) return 100;
    
    const issuesPerFile = totalIssues / totalFiles;
    return Math.max(0, Math.round(100 - (issuesPerFile * 10)));
  }

  async checkQualityGates(results) {
    const gates = [
      {
        name: 'Unit Test Coverage',
        check: () => results['Unit Tests']?.coverage >= 80,
        threshold: 80,
        actual: results['Unit Tests']?.coverage || 0
      },
      {
        name: 'Test Pass Rate',
        check: () => {
          const unitTests = results['Unit Tests'] || {};
          const passRate = unitTests.total > 0 ? (unitTests.passed / unitTests.total) * 100 : 0;
          return passRate >= 95;
        },
        threshold: 95,
        actual: (() => {
          const unitTests = results['Unit Tests'] || {};
          return unitTests.total > 0 ? Math.round((unitTests.passed / unitTests.total) * 100) : 0;
        })()
      },
      {
        name: 'Performance Load Time',
        check: () => (results['Performance Tests']?.loadTime || 0) <= 2000,
        threshold: 2000,
        actual: results['Performance Tests']?.loadTime || 0
      },
      {
        name: 'Accessibility Score',
        check: () => (results['Accessibility Tests']?.score || 0) >= 90,
        threshold: 90,
        actual: results['Accessibility Tests']?.score || 0
      },
      {
        name: 'Security Vulnerabilities',
        check: () => {
          const security = results['Security Audit'] || {};
          return (security.vulnerabilities?.critical || 0) === 0 && (security.vulnerabilities?.high || 0) === 0;
        },
        threshold: 0,
        actual: (() => {
          const security = results['Security Audit'] || {};
          return (security.vulnerabilities?.critical || 0) + (security.vulnerabilities?.high || 0);
        })()
      },
      {
        name: 'Code Quality',
        check: () => {
          const codeQuality = results['Code Quality Analysis'] || {};
          return codeQuality.linting?.errors === 0 && codeQuality.typeCheck === true;
        },
        threshold: 0,
        actual: results['Code Quality Analysis']?.linting?.errors || 0
      }
    ];

    const passed = gates.filter(gate => gate.check());
    const failed = gates.filter(gate => !gate.check());

    return {
      total: gates.length,
      passed: passed.length,
      failed: failed.map(gate => ({
        name: gate.name,
        threshold: gate.threshold,
        actual: gate.actual
      }))
    };
  }

  async generateQualityReport(results, duration) {
    const timestamp = new Date().toISOString();
    const report = {
      timestamp,
      duration,
      results,
      summary: {
        totalChecks: Object.keys(results).length,
        passedChecks: Object.values(results).filter(r => r.success).length,
        failedChecks: Object.values(results).filter(r => !r.success).length
      }
    };

    // Save report
    const reportPath = path.join(this.reportsDir, `qa-report-${Date.now()}.json`);
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

    console.log(`📊 Quality report saved: ${reportPath}`);
    return report;
  }

  async setupContinuousQuality() {
    console.log('⚙️  Setting up continuous quality monitoring...');

    // Create pre-commit hook
    const preCommitHook = `#!/bin/sh
# Quality checks before commit
echo "Running quality checks..."
node scripts/qa-automation.js quick-check
if [ $? -ne 0 ]; then
  echo "Quality checks failed. Commit aborted."
  exit 1
fi
`;

    const hooksDir = path.join(this.projectRoot, '.git', 'hooks');
    if (fs.existsSync(hooksDir)) {
      fs.writeFileSync(path.join(hooksDir, 'pre-commit'), preCommitHook);
      execSync('chmod +x .git/hooks/pre-commit', { cwd: this.projectRoot });
      console.log('✅ Pre-commit hook installed');
    }

    // Create GitHub Actions workflow
    const workflowContent = `
name: Quality Assurance

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  quality-check:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Run quality checks
      run: node scripts/qa-automation.js full-check
    
    - name: Upload quality report
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: quality-report
        path: qa-automation/reports/
`;

    const workflowDir = path.join(this.projectRoot, '.github', 'workflows');
    if (!fs.existsSync(workflowDir)) {
      fs.mkdirSync(workflowDir, { recursive: true });
    }
    
    fs.writeFileSync(path.join(workflowDir, 'quality-assurance.yml'), workflowContent);
    console.log('✅ GitHub Actions workflow created');

    console.log('⚙️  Continuous quality monitoring setup complete');
  }
}

// CLI Interface
async function main() {
  const qa = new QAAutomation();
  const command = process.argv[2];
  const options = {
    verbose: process.argv.includes('--verbose'),
    silent: process.argv.includes('--silent'),
    headed: process.argv.includes('--headed'),
    debug: process.argv.includes('--debug'),
    watch: process.argv.includes('--watch'),
    updateSnapshots: process.argv.includes('--update-snapshots')
  };

  switch (command) {
    case 'full-check':
      const fullResults = await qa.runQualityChecks(options);
      process.exit(fullResults.success ? 0 : 1);
      break;

    case 'quick-check':
      // Run essential checks only
      const quickResults = await qa.runQualityChecks({ ...options, quick: true });
      process.exit(quickResults.success ? 0 : 1);
      break;

    case 'setup':
      await qa.setupContinuousQuality();
      break;

    default:
      console.log(`
QA Automation Tool

Usage:
  node qa-automation.js <command> [options]

Commands:
  full-check    Run all quality checks
  quick-check   Run essential quality checks only
  setup         Setup continuous quality monitoring

Options:
  --verbose     Verbose output
  --silent      Silent mode
  --headed      Run tests in headed mode
  --debug       Debug mode
  --watch       Watch mode for tests
  --update-snapshots  Update visual test snapshots

Examples:
  node qa-automation.js full-check --verbose
  node qa-automation.js quick-check --silent
  node qa-automation.js setup
      `);
      break;
  }
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = QAAutomation;