#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

class PerformanceTestRunner {
  constructor() {
    this.resultsDir = path.join(process.cwd(), 'e2e-artifacts', 'performance-results');
    this.reportsDir = path.join(process.cwd(), 'e2e-artifacts', 'performance-reports');
    
    this.ensureDirectories();
  }

  ensureDirectories() {
    [this.resultsDir, this.reportsDir].forEach(dir => {
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
    });
  }

  async runLoadTests(options = {}) {
    console.log('🚀 Running Load Tests...');
    
    const testCommand = [
      'npx playwright test',
      'e2e/performance/load-testing.spec.ts',
      '--reporter=json',
      `--output=${path.join(this.resultsDir, 'load-test-results.json')}`,
      options.headed ? '--headed' : '',
      options.debug ? '--debug' : '',
      options.workers ? `--workers=${options.workers}` : '--workers=1'
    ].filter(Boolean).join(' ');
    
    try {
      const startTime = Date.now();
      execSync(testCommand, { stdio: 'inherit', cwd: process.cwd() });
      const duration = Date.now() - startTime;
      
      console.log(`✅ Load tests completed in ${duration}ms`);
      return { success: true, duration };
    } catch (error) {
      console.error('❌ Load tests failed:', error.message);
      return { success: false, error: error.message };
    }
  }

  async runStressTests(options = {}) {
    console.log('💪 Running Stress Tests...');
    
    const testCommand = [
      'npx playwright test',
      'e2e/performance/stress-testing.spec.ts',
      '--reporter=json',
      `--output=${path.join(this.resultsDir, 'stress-test-results.json')}`,
      options.headed ? '--headed' : '',
      options.debug ? '--debug' : '',
      '--workers=1' // Stress tests should run sequentially
    ].filter(Boolean).join(' ');
    
    try {
      const startTime = Date.now();
      execSync(testCommand, { stdio: 'inherit', cwd: process.cwd() });
      const duration = Date.now() - startTime;
      
      console.log(`✅ Stress tests completed in ${duration}ms`);
      return { success: true, duration };
    } catch (error) {
      console.error('❌ Stress tests failed:', error.message);
      return { success: false, error: error.message };
    }
  }

  async runBenchmarkTests(options = {}) {
    console.log('📊 Running Benchmark Tests...');
    
    const testCommand = [
      'npx playwright test',
      'e2e/performance/performance-benchmarking.spec.ts',
      '--reporter=json',
      `--output=${path.join(this.resultsDir, 'benchmark-test-results.json')}`,
      options.headed ? '--headed' : '',
      options.debug ? '--debug' : '',
      '--workers=1'
    ].filter(Boolean).join(' ');
    
    try {
      const startTime = Date.now();
      execSync(testCommand, { stdio: 'inherit', cwd: process.cwd() });
      const duration = Date.now() - startTime;
      
      console.log(`✅ Benchmark tests completed in ${duration}ms`);
      return { success: true, duration };
    } catch (error) {
      console.error('❌ Benchmark tests failed:', error.message);
      return { success: false, error: error.message };
    }
  }

  async runAllPerformanceTests(options = {}) {
    console.log('🎯 Running All Performance Tests...');
    
    const testSuites = [
      { name: 'Load Tests', runner: () => this.runLoadTests(options) },
      { name: 'Stress Tests', runner: () => this.runStressTests(options) },
      { name: 'Benchmark Tests', runner: () => this.runBenchmarkTests(options) }
    ];
    
    const results = {};
    const overallStartTime = Date.now();
    
    for (const suite of testSuites) {
      console.log(`\n--- Running ${suite.name} ---`);
      results[suite.name] = await suite.runner();
    }
    
    const overallDuration = Date.now() - overallStartTime;
    
    // Generate comprehensive report
    const report = await this.generatePerformanceReport(results, overallDuration);
    
    console.log('\n📈 Performance Test Summary:');
    console.log(`  Overall Duration: ${overallDuration}ms`);
    console.log(`  Load Tests: ${results['Load Tests'].success ? '✅ PASSED' : '❌ FAILED'}`);
    console.log(`  Stress Tests: ${results['Stress Tests'].success ? '✅ PASSED' : '❌ FAILED'}`);
    console.log(`  Benchmark Tests: ${results['Benchmark Tests'].success ? '✅ PASSED' : '❌ FAILED'}`);
    
    return report;
  }

  async generatePerformanceReport(testResults, overallDuration) {
    console.log('📋 Generating Performance Report...');
    
    const timestamp = new Date().toISOString();
    const reportData = {
      timestamp,
      overallDuration,
      testResults,
      summary: {
        totalSuites: Object.keys(testResults).length,
        passedSuites: Object.values(testResults).filter(r => r.success).length,
        failedSuites: Object.values(testResults).filter(r => !r.success).length
      },
      environment: {
        nodeVersion: process.version,
        platform: process.platform,
        arch: process.arch,
        memory: process.memoryUsage()
      }
    };
    
    // Load individual test results if available
    const resultFiles = [
      'load-test-results.json',
      'stress-test-results.json',
      'benchmark-test-results.json'
    ];
    
    reportData.detailedResults = {};
    
    for (const resultFile of resultFiles) {
      const resultPath = path.join(this.resultsDir, resultFile);
      if (fs.existsSync(resultPath)) {
        try {
          const resultContent = fs.readFileSync(resultPath, 'utf8');
          const testName = resultFile.replace('-results.json', '');
          reportData.detailedResults[testName] = JSON.parse(resultContent);
        } catch (error) {
          console.warn(`Failed to parse ${resultFile}:`, error.message);
        }
      }
    }
    
    // Generate HTML report
    const htmlReport = this.generateHtmlReport(reportData);
    const htmlReportPath = path.join(this.reportsDir, `performance-report-${Date.now()}.html`);
    fs.writeFileSync(htmlReportPath, htmlReport);
    
    // Generate JSON report
    const jsonReportPath = path.join(this.reportsDir, `performance-report-${Date.now()}.json`);
    fs.writeFileSync(jsonReportPath, JSON.stringify(reportData, null, 2));
    
    console.log(`📊 HTML Report: ${htmlReportPath}`);
    console.log(`📊 JSON Report: ${jsonReportPath}`);
    
    return reportData;
  }

  generateHtmlReport(reportData) {
    return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Performance Test Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            line-height: 1.6;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }
        .summary-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .summary-number {
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .passed { color: #28a745; }
        .failed { color: #dc3545; }
        .duration { color: #007bff; }
        .total { color: #6c757d; }
        .results {
            padding: 30px;
        }
        .test-suite {
            border: 1px solid #dee2e6;
            border-radius: 8px;
            margin-bottom: 20px;
            overflow: hidden;
        }
        .suite-header {
            padding: 15px 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .suite-name {
            font-weight: bold;
            font-size: 1.1em;
        }
        .status-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }
        .status-passed {
            background: #d4edda;
            color: #155724;
        }
        .status-failed {
            background: #f8d7da;
            color: #721c24;
        }
        .suite-details {
            padding: 20px;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }
        .metric:last-child {
            border-bottom: none;
        }
        .metric-label {
            font-weight: 500;
        }
        .metric-value {
            color: #6c757d;
        }
        .environment {
            background: #f8f9fa;
            padding: 20px;
            margin-top: 20px;
            border-radius: 8px;
        }
        .timestamp {
            color: #6c757d;
            font-size: 0.9em;
        }
        .error-details {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 4px;
            margin-top: 10px;
            font-family: monospace;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Performance Test Report</h1>
            <p class="timestamp">Generated on ${new Date(reportData.timestamp).toLocaleString()}</p>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <div class="summary-number total">${reportData.summary.totalSuites}</div>
                <div>Total Suites</div>
            </div>
            <div class="summary-card">
                <div class="summary-number passed">${reportData.summary.passedSuites}</div>
                <div>Passed</div>
            </div>
            <div class="summary-card">
                <div class="summary-number failed">${reportData.summary.failedSuites}</div>
                <div>Failed</div>
            </div>
            <div class="summary-card">
                <div class="summary-number duration">${(reportData.overallDuration / 1000).toFixed(1)}s</div>
                <div>Total Duration</div>
            </div>
        </div>
        
        <div class="results">
            <h2>Test Suite Results</h2>
            ${Object.entries(reportData.testResults).map(([suiteName, result]) => `
                <div class="test-suite">
                    <div class="suite-header">
                        <div class="suite-name">${suiteName}</div>
                        <div class="status-badge status-${result.success ? 'passed' : 'failed'}">
                            ${result.success ? 'PASSED' : 'FAILED'}
                        </div>
                    </div>
                    <div class="suite-details">
                        ${result.duration ? `
                            <div class="metric">
                                <span class="metric-label">Duration</span>
                                <span class="metric-value">${(result.duration / 1000).toFixed(2)}s</span>
                            </div>
                        ` : ''}
                        ${result.error ? `
                            <div class="error-details">
                                <strong>Error:</strong><br>
                                ${result.error}
                            </div>
                        ` : ''}
                    </div>
                </div>
            `).join('')}
        </div>
        
        <div class="environment">
            <h3>Environment Information</h3>
            <div class="metric">
                <span class="metric-label">Node.js Version</span>
                <span class="metric-value">${reportData.environment.nodeVersion}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Platform</span>
                <span class="metric-value">${reportData.environment.platform} (${reportData.environment.arch})</span>
            </div>
            <div class="metric">
                <span class="metric-label">Memory Usage</span>
                <span class="metric-value">${(reportData.environment.memory.heapUsed / 1024 / 1024).toFixed(2)} MB</span>
            </div>
        </div>
    </div>
</body>
</html>
    `;
  }

  async compareWithBaseline(currentResults, baselinePath) {
    if (!fs.existsSync(baselinePath)) {
      console.log('📊 No baseline found, creating new baseline...');
      fs.writeFileSync(baselinePath, JSON.stringify(currentResults, null, 2));
      return { isRegression: false, message: 'Baseline created' };
    }
    
    const baseline = JSON.parse(fs.readFileSync(baselinePath, 'utf8'));
    const comparison = {
      timestamp: new Date().toISOString(),
      current: currentResults,
      baseline: baseline,
      regressions: [],
      improvements: []
    };
    
    // Compare test suite durations
    for (const [suiteName, currentResult] of Object.entries(currentResults.testResults)) {
      const baselineResult = baseline.testResults[suiteName];
      
      if (baselineResult && currentResult.duration && baselineResult.duration) {
        const change = (currentResult.duration - baselineResult.duration) / baselineResult.duration;
        const changePercent = (change * 100).toFixed(2);
        
        if (change > 0.2) { // 20% slower
          comparison.regressions.push({
            suite: suiteName,
            metric: 'duration',
            current: currentResult.duration,
            baseline: baselineResult.duration,
            change: changePercent + '%'
          });
        } else if (change < -0.1) { // 10% faster
          comparison.improvements.push({
            suite: suiteName,
            metric: 'duration',
            current: currentResult.duration,
            baseline: baselineResult.duration,
            change: changePercent + '%'
          });
        }
      }
    }
    
    console.log('\n📊 Performance Comparison:');
    if (comparison.regressions.length > 0) {
      console.log('❌ Regressions detected:');
      comparison.regressions.forEach(reg => {
        console.log(`  ${reg.suite}: ${reg.change} slower`);
      });
    }
    
    if (comparison.improvements.length > 0) {
      console.log('✅ Improvements detected:');
      comparison.improvements.forEach(imp => {
        console.log(`  ${imp.suite}: ${Math.abs(parseFloat(imp.change))}% faster`);
      });
    }
    
    if (comparison.regressions.length === 0 && comparison.improvements.length === 0) {
      console.log('📊 No significant performance changes detected');
    }
    
    // Save comparison report
    const comparisonPath = path.join(this.reportsDir, `performance-comparison-${Date.now()}.json`);
    fs.writeFileSync(comparisonPath, JSON.stringify(comparison, null, 2));
    
    return {
      isRegression: comparison.regressions.length > 0,
      regressions: comparison.regressions,
      improvements: comparison.improvements,
      comparisonPath
    };
  }

  async cleanup(daysOld = 7) {
    console.log(`🧹 Cleaning up performance results older than ${daysOld} days...`);
    
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - daysOld);
    
    let cleanedCount = 0;
    
    [this.resultsDir, this.reportsDir].forEach(dir => {
      if (!fs.existsSync(dir)) return;
      
      const files = fs.readdirSync(dir);
      
      files.forEach(file => {
        const filePath = path.join(dir, file);
        const stats = fs.statSync(filePath);
        
        if (stats.mtime < cutoffDate) {
          fs.unlinkSync(filePath);
          cleanedCount++;
          console.log(`  🗑️  Removed: ${filePath}`);
        }
      });
    });
    
    console.log(`🧹 Cleaned up ${cleanedCount} old files`);
  }
}

// CLI Interface
async function main() {
  const runner = new PerformanceTestRunner();
  const command = process.argv[2];
  const options = {
    headed: process.argv.includes('--headed'),
    debug: process.argv.includes('--debug'),
    workers: process.argv.find(arg => arg.startsWith('--workers='))?.split('=')[1]
  };
  
  switch (command) {
    case 'load':
      await runner.runLoadTests(options);
      break;
      
    case 'stress':
      await runner.runStressTests(options);
      break;
      
    case 'benchmark':
      await runner.runBenchmarkTests(options);
      break;
      
    case 'all':
      await runner.runAllPerformanceTests(options);
      break;
      
    case 'cleanup':
      const days = parseInt(process.argv[3]) || 7;
      await runner.cleanup(days);
      break;
      
    default:
      console.log(`
Performance Test Runner

Usage:
  node performance-test-runner.js <command> [options]

Commands:
  load        Run load testing suite
  stress      Run stress testing suite  
  benchmark   Run benchmark testing suite
  all         Run all performance test suites
  cleanup     Clean up old test results and reports

Options:
  --headed    Run tests in headed mode
  --debug     Run tests in debug mode
  --workers=N Set number of workers

Examples:
  node performance-test-runner.js all
  node performance-test-runner.js load --headed
  node performance-test-runner.js cleanup 14
      `);
      break;
  }
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = PerformanceTestRunner;