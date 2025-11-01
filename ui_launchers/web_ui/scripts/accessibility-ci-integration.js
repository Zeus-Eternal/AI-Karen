#!/usr/bin/env node

/**
 * Accessibility CI/CD Integration Script
 * 
 * Integrates accessibility testing into CI/CD pipelines with regression detection,
 * threshold enforcement, and comprehensive reporting.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const { chromium } = require('playwright');

// Configuration
const CONFIG = {
  baseUrl: process.env.BASE_URL || 'http://localhost:8010',
  outputDir: process.env.OUTPUT_DIR || './accessibility-reports',
  baselineDir: process.env.BASELINE_DIR || './accessibility-baseline',
  thresholds: {
    critical: parseInt(process.env.A11Y_CRITICAL_THRESHOLD) || 0,
    serious: parseInt(process.env.A11Y_SERIOUS_THRESHOLD) || 0,
    moderate: parseInt(process.env.A11Y_MODERATE_THRESHOLD) || 3,
    minor: parseInt(process.env.A11Y_MINOR_THRESHOLD) || 8
  },
  failOnRegression: process.env.A11Y_FAIL_ON_REGRESSION !== 'false',
  generateBaseline: process.env.A11Y_GENERATE_BASELINE === 'true',
  reportFormats: (process.env.A11Y_REPORT_FORMATS || 'json,html,junit').split(','),
  testUrls: (process.env.A11Y_TEST_URLS || '/,/dashboard,/chat,/settings').split(','),
  timeout: parseInt(process.env.A11Y_TIMEOUT) || 30000,
  retries: parseInt(process.env.A11Y_RETRIES) || 2
};

// Colors for console output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function logSection(title) {
  log(`\n${'='.repeat(60)}`, 'bright');
  log(title, 'bright');
  log('='.repeat(60), 'bright');
}

// Ensure output directories exist
function ensureDirectories() {
  [CONFIG.outputDir, CONFIG.baselineDir].forEach(dir => {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
      log(`Created directory: ${dir}`, 'blue');
    }
  });
}

// Wait for server to be ready
async function waitForServer(url, timeout = 60000) {
  const startTime = Date.now();
  
  while (Date.now() - startTime < timeout) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        log(`Server is ready at ${url}`, 'green');
        return true;
      }
    } catch (error) {
      // Server not ready yet
    }
    
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  
  throw new Error(`Server at ${url} did not become ready within ${timeout}ms`);
}

// Run accessibility test on a single page
async function testPage(page, url, config = {}) {
  const fullUrl = `${CONFIG.baseUrl}${url}`;
  
  try {
    log(`Testing: ${fullUrl}`, 'cyan');
    
    // Navigate to page
    await page.goto(fullUrl, { waitUntil: 'networkidle' });
    
    // Wait for page to be fully loaded
    await page.waitForTimeout(2000);
    
    // Inject axe-core
    await page.addScriptTag({
      url: 'https://unpkg.com/axe-core@4.10.2/axe.min.js'
    });
    
    // Run axe analysis
    const axeResults = await page.evaluate(async (runOptions) => {
      return await window.axe.run(document, runOptions);
    }, {
      runOnly: {
        type: 'tag',
        values: config.tags || ['wcag2a', 'wcag2aa']
      },
      timeout: CONFIG.timeout,
      ...config
    });
    
    // Calculate metrics
    const violationsByImpact = {
      critical: axeResults.violations.filter(v => v.impact === 'critical').length,
      serious: axeResults.violations.filter(v => v.impact === 'serious').length,
      moderate: axeResults.violations.filter(v => v.impact === 'moderate').length,
      minor: axeResults.violations.filter(v => v.impact === 'minor').length
    };
    
    const complianceScore = calculateComplianceScore(axeResults);
    const passed = evaluateThresholds(violationsByImpact, CONFIG.thresholds);
    
    const result = {
      url: fullUrl,
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
    
    // Log results
    if (passed) {
      log(`✓ PASSED - Score: ${complianceScore}%`, 'green');
    } else {
      log(`✗ FAILED - Score: ${complianceScore}%`, 'red');
      log(`  Critical: ${violationsByImpact.critical}, Serious: ${violationsByImpact.serious}, Moderate: ${violationsByImpact.moderate}, Minor: ${violationsByImpact.minor}`, 'red');
    }
    
    return result;
    
  } catch (error) {
    log(`Error testing ${fullUrl}: ${error.message}`, 'red');
    throw error;
  }
}

// Calculate compliance score
function calculateComplianceScore(axeResults) {
  const totalChecks = axeResults.violations.length + axeResults.passes.length;
  if (totalChecks === 0) return 100;

  const weightedViolations = axeResults.violations.reduce((sum, violation) => {
    const weight = getImpactWeight(violation.impact);
    return sum + (violation.nodes.length * weight);
  }, 0);

  const maxPossibleScore = totalChecks * 4;
  const score = Math.max(0, 100 - (weightedViolations / maxPossibleScore) * 100);
  
  return Math.round(score * 100) / 100;
}

function getImpactWeight(impact) {
  switch (impact) {
    case 'critical': return 4;
    case 'serious': return 3;
    case 'moderate': return 2;
    case 'minor': return 1;
    default: return 1;
  }
}

// Evaluate thresholds
function evaluateThresholds(violations, thresholds) {
  return (
    violations.critical <= thresholds.critical &&
    violations.serious <= thresholds.serious &&
    violations.moderate <= thresholds.moderate &&
    violations.minor <= thresholds.minor
  );
}

// Load baseline results
function loadBaseline() {
  const baselinePath = path.join(CONFIG.baselineDir, 'baseline.json');
  
  if (!fs.existsSync(baselinePath)) {
    log('No baseline found, will create new baseline', 'yellow');
    return new Map();
  }
  
  try {
    const baselineData = JSON.parse(fs.readFileSync(baselinePath, 'utf8'));
    const baseline = new Map();
    
    if (Array.isArray(baselineData)) {
      baselineData.forEach(result => {
        baseline.set(result.url, result);
      });
    }
    
    log(`Loaded baseline with ${baseline.size} entries`, 'blue');
    return baseline;
  } catch (error) {
    log(`Error loading baseline: ${error.message}`, 'red');
    return new Map();
  }
}

// Save baseline results
function saveBaseline(results) {
  const baselinePath = path.join(CONFIG.baselineDir, 'baseline.json');
  
  try {
    fs.writeFileSync(baselinePath, JSON.stringify(results, null, 2));
    log(`Saved baseline to ${baselinePath}`, 'green');
  } catch (error) {
    log(`Error saving baseline: ${error.message}`, 'red');
    throw error;
  }
}

// Detect regressions
function detectRegressions(current, baseline) {
  const baselineResult = baseline.get(current.url);
  
  if (!baselineResult) {
    return {
      current,
      baseline: null,
      regressions: [],
      improvements: [],
      hasRegressions: false
    };
  }
  
  const regressions = [];
  const improvements = [];
  
  // Create maps for easier comparison
  const currentViolations = new Map(
    current.axeResults.violations.map(v => [v.id, v.nodes.length])
  );
  const baselineViolations = new Map(
    baselineResult.axeResults.violations.map(v => [v.id, v.nodes.length])
  );
  
  // Check for regressions
  for (const [ruleId, currentCount] of currentViolations) {
    const baselineCount = baselineViolations.get(ruleId) || 0;
    
    if (currentCount > baselineCount) {
      const violation = current.axeResults.violations.find(v => v.id === ruleId);
      regressions.push({
        ruleId,
        description: violation.description,
        impact: violation.impact || 'unknown',
        newViolations: currentCount - baselineCount,
        previousViolations: baselineCount
      });
    }
  }
  
  // Check for improvements
  for (const [ruleId, baselineCount] of baselineViolations) {
    const currentCount = currentViolations.get(ruleId) || 0;
    
    if (currentCount < baselineCount) {
      const violation = baselineResult.axeResults.violations.find(v => v.id === ruleId);
      improvements.push({
        ruleId,
        description: violation.description,
        impact: violation.impact || 'unknown',
        fixedViolations: baselineCount - currentCount
      });
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

// Generate reports
function generateReports(results, regressionResults) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  
  CONFIG.reportFormats.forEach(format => {
    try {
      let content;
      let filename;
      
      switch (format) {
        case 'json':
          content = generateJSONReport(results, regressionResults);
          filename = `accessibility-report-${timestamp}.json`;
          break;
        case 'html':
          content = generateHTMLReport(results, regressionResults);
          filename = `accessibility-report-${timestamp}.html`;
          break;
        case 'junit':
          content = generateJUnitReport(results);
          filename = `accessibility-report-${timestamp}.xml`;
          break;
        case 'sarif':
          content = generateSARIFReport(results);
          filename = `accessibility-report-${timestamp}.sarif`;
          break;
        default:
          log(`Unknown report format: ${format}`, 'yellow');
          continue;
      }
      
      const filepath = path.join(CONFIG.outputDir, filename);
      fs.writeFileSync(filepath, content);
      log(`Generated ${format.toUpperCase()} report: ${filepath}`, 'green');
      
    } catch (error) {
      log(`Error generating ${format} report: ${error.message}`, 'red');
    }
  });
}

function generateJSONReport(results, regressionResults) {
  const passed = results.filter(r => r.passed).length;
  const failed = results.filter(r => !r.passed).length;
  const avgScore = results.reduce((sum, r) => sum + r.complianceScore, 0) / results.length;
  const totalRegressions = regressionResults.reduce((sum, r) => sum + r.regressions.length, 0);
  const totalImprovements = regressionResults.reduce((sum, r) => sum + r.improvements.length, 0);
  
  return JSON.stringify({
    generatedAt: new Date().toISOString(),
    summary: {
      totalTests: results.length,
      passed,
      failed,
      averageComplianceScore: Math.round(avgScore * 100) / 100,
      totalRegressions,
      totalImprovements
    },
    thresholds: CONFIG.thresholds,
    results,
    regressions: regressionResults
  }, null, 2);
}

function generateHTMLReport(results, regressionResults) {
  const passed = results.filter(r => r.passed).length;
  const failed = results.filter(r => !r.passed).length;
  const avgScore = results.reduce((sum, r) => sum + r.complianceScore, 0) / results.length;
  const totalRegressions = regressionResults.reduce((sum, r) => sum + r.regressions.length, 0);
  
  return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Accessibility CI/CD Report</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background: #2563eb; color: white; padding: 30px; border-radius: 8px 8px 0 0; }
        .content { padding: 30px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .metric { background: #f8fafc; padding: 20px; border-radius: 6px; border-left: 4px solid #2563eb; }
        .metric-value { font-size: 2em; font-weight: bold; color: #1e293b; }
        .metric-label { color: #64748b; font-size: 0.9em; margin-top: 5px; }
        .result { border: 1px solid #e2e8f0; margin: 15px 0; border-radius: 6px; overflow: hidden; }
        .result-header { padding: 15px; background: #f8fafc; border-bottom: 1px solid #e2e8f0; }
        .result-content { padding: 15px; }
        .passed { border-left: 4px solid #10b981; }
        .failed { border-left: 4px solid #ef4444; }
        .regression { border-left: 4px solid #f59e0b; }
        .violation { background: #fef3c7; padding: 10px; margin: 8px 0; border-radius: 4px; border-left: 3px solid #f59e0b; }
        .critical { border-left-color: #ef4444; background: #fef2f2; }
        .serious { border-left-color: #f97316; background: #fff7ed; }
        .moderate { border-left-color: #eab308; background: #fefce8; }
        .minor { border-left-color: #06b6d4; background: #f0f9ff; }
        .badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.75em; font-weight: 500; }
        .badge-success { background: #dcfce7; color: #166534; }
        .badge-error { background: #fecaca; color: #991b1b; }
        .badge-warning { background: #fef3c7; color: #92400e; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Accessibility CI/CD Report</h1>
            <p>Generated on ${new Date().toLocaleString()}</p>
        </div>
        
        <div class="content">
            <div class="summary">
                <div class="metric">
                    <div class="metric-value">${results.length}</div>
                    <div class="metric-label">Total Tests</div>
                </div>
                <div class="metric">
                    <div class="metric-value ${passed === results.length ? 'text-green-600' : 'text-red-600'}">${passed}</div>
                    <div class="metric-label">Passed</div>
                </div>
                <div class="metric">
                    <div class="metric-value ${failed === 0 ? 'text-green-600' : 'text-red-600'}">${failed}</div>
                    <div class="metric-label">Failed</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${avgScore.toFixed(1)}%</div>
                    <div class="metric-label">Avg. Compliance</div>
                </div>
                <div class="metric">
                    <div class="metric-value ${totalRegressions === 0 ? 'text-green-600' : 'text-red-600'}">${totalRegressions}</div>
                    <div class="metric-label">Regressions</div>
                </div>
            </div>
            
            <h2>Test Results</h2>
            ${results.map(result => `
                <div class="result ${result.passed ? 'passed' : 'failed'}">
                    <div class="result-header">
                        <h3>${result.url}</h3>
                        <div>
                            <span class="badge ${result.passed ? 'badge-success' : 'badge-error'}">
                                ${result.passed ? 'PASSED' : 'FAILED'}
                            </span>
                            <span class="badge badge-warning">Score: ${result.complianceScore}%</span>
                        </div>
                    </div>
                    <div class="result-content">
                        <p><strong>Violations:</strong> ${result.summary.violations} | <strong>Passes:</strong> ${result.summary.passes}</p>
                        ${result.axeResults.violations.map(violation => `
                            <div class="violation ${violation.impact}">
                                <strong>${violation.description}</strong>
                                <br><small>Impact: ${violation.impact} | Nodes: ${violation.nodes.length}</small>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `).join('')}
            
            ${totalRegressions > 0 ? `
                <h2>Regressions Detected</h2>
                ${regressionResults.filter(r => r.hasRegressions).map(regression => `
                    <div class="result regression">
                        <div class="result-header">
                            <h3>${regression.current.url}</h3>
                            <span class="badge badge-warning">REGRESSION</span>
                        </div>
                        <div class="result-content">
                            ${regression.regressions.map(reg => `
                                <div class="violation ${reg.impact}">
                                    <strong>${reg.description}</strong>
                                    <br><small>New violations: ${reg.newViolations} (was ${reg.previousViolations})</small>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `).join('')}
            ` : ''}
        </div>
    </div>
</body>
</html>`;
}

function generateJUnitReport(results) {
  const totalTests = results.length;
  const failures = results.filter(r => !r.passed).length;
  
  return `<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="Accessibility Tests" tests="${totalTests}" failures="${failures}" time="${totalTests}">
${results.map(result => `
    <testcase name="${result.url}" classname="AccessibilityTest" time="1">
        ${!result.passed ? `
            <failure message="Accessibility violations found">
                Compliance Score: ${result.complianceScore}%
                Violations: ${result.summary.violations}
                ${result.axeResults.violations.map(v => `${v.description}: ${v.nodes.length} violations`).join('\n                ')}
            </failure>
        ` : ''}
    </testcase>
`).join('')}
</testsuite>`;
}

function generateSARIFReport(results) {
  return JSON.stringify({
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
          level: mapImpactToLevel(violation.impact),
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
  }, null, 2);
}

function mapImpactToLevel(impact) {
  switch (impact) {
    case 'critical': return 'error';
    case 'serious': return 'error';
    case 'moderate': return 'warning';
    case 'minor': return 'note';
    default: return 'note';
  }
}

// Main execution function
async function main() {
  try {
    logSection('Accessibility CI/CD Integration');
    
    log('Configuration:', 'blue');
    log(`  Base URL: ${CONFIG.baseUrl}`, 'reset');
    log(`  Output Directory: ${CONFIG.outputDir}`, 'reset');
    log(`  Test URLs: ${CONFIG.testUrls.join(', ')}`, 'reset');
    log(`  Thresholds: Critical=${CONFIG.thresholds.critical}, Serious=${CONFIG.thresholds.serious}, Moderate=${CONFIG.thresholds.moderate}, Minor=${CONFIG.thresholds.minor}`, 'reset');
    log(`  Fail on Regression: ${CONFIG.failOnRegression}`, 'reset');
    log(`  Generate Baseline: ${CONFIG.generateBaseline}`, 'reset');
    
    // Ensure directories exist
    ensureDirectories();
    
    // Wait for server to be ready
    await waitForServer(CONFIG.baseUrl);
    
    // Load baseline if not generating new one
    let baseline = new Map();
    if (!CONFIG.generateBaseline) {
      baseline = loadBaseline();
    }
    
    // Launch browser
    logSection('Running Accessibility Tests');
    const browser = await chromium.launch();
    const page = await browser.newPage();
    
    const results = [];
    const regressionResults = [];
    
    // Test each URL
    for (const url of CONFIG.testUrls) {
      let attempt = 0;
      let result = null;
      
      while (attempt <= CONFIG.retries && !result) {
        try {
          result = await testPage(page, url);
          results.push(result);
          
          // Check for regressions
          const regressionResult = detectRegressions(result, baseline);
          regressionResults.push(regressionResult);
          
          if (regressionResult.hasRegressions) {
            log(`  ⚠ Regressions detected: ${regressionResult.regressions.length}`, 'yellow');
          }
          if (regressionResult.improvements.length > 0) {
            log(`  ✓ Improvements found: ${regressionResult.improvements.length}`, 'green');
          }
          
        } catch (error) {
          attempt++;
          if (attempt <= CONFIG.retries) {
            log(`  Retry ${attempt}/${CONFIG.retries} for ${url}`, 'yellow');
          } else {
            log(`  Failed after ${CONFIG.retries} retries: ${error.message}`, 'red');
            throw error;
          }
        }
      }
    }
    
    await browser.close();
    
    // Generate or update baseline
    if (CONFIG.generateBaseline) {
      logSection('Generating Baseline');
      saveBaseline(results);
    }
    
    // Generate reports
    logSection('Generating Reports');
    generateReports(results, regressionResults);
    
    // Evaluate results
    logSection('Test Results Summary');
    const passed = results.filter(r => r.passed).length;
    const failed = results.filter(r => !r.passed).length;
    const totalRegressions = regressionResults.reduce((sum, r) => sum + r.regressions.length, 0);
    const avgScore = results.reduce((sum, r) => sum + r.complianceScore, 0) / results.length;
    
    log(`Total Tests: ${results.length}`, 'blue');
    log(`Passed: ${passed}`, passed === results.length ? 'green' : 'yellow');
    log(`Failed: ${failed}`, failed === 0 ? 'green' : 'red');
    log(`Average Compliance Score: ${avgScore.toFixed(2)}%`, avgScore >= 90 ? 'green' : avgScore >= 80 ? 'yellow' : 'red');
    log(`Regressions: ${totalRegressions}`, totalRegressions === 0 ? 'green' : 'red');
    
    // Determine exit code
    let exitCode = 0;
    
    if (failed > 0) {
      log('\n❌ Some accessibility tests failed', 'red');
      exitCode = 1;
    }
    
    if (CONFIG.failOnRegression && totalRegressions > 0) {
      log('\n❌ Accessibility regressions detected', 'red');
      exitCode = 1;
    }
    
    if (exitCode === 0) {
      log('\n✅ All accessibility tests passed', 'green');
    }
    
    process.exit(exitCode);
    
  } catch (error) {
    log(`\n❌ Accessibility testing failed: ${error.message}`, 'red');
    console.error(error);
    process.exit(1);
  }
}

// Handle command line arguments
if (require.main === module) {
  const command = process.argv[2];
  
  switch (command) {
    case 'test':
      main();
      break;
    case 'baseline':
      CONFIG.generateBaseline = true;
      main();
      break;
    case 'help':
    case '--help':
    case '-h':
      console.log(`
Accessibility CI/CD Integration

Usage:
  node scripts/accessibility-ci-integration.js [command]

Commands:
  test      Run accessibility tests (default)
  baseline  Generate new baseline
  help      Show this help

Environment Variables:
  BASE_URL                    Base URL for testing (default: http://localhost:8010)
  OUTPUT_DIR                  Output directory for reports (default: ./accessibility-reports)
  BASELINE_DIR               Baseline directory (default: ./accessibility-baseline)
  A11Y_CRITICAL_THRESHOLD    Critical violations threshold (default: 0)
  A11Y_SERIOUS_THRESHOLD     Serious violations threshold (default: 0)
  A11Y_MODERATE_THRESHOLD    Moderate violations threshold (default: 3)
  A11Y_MINOR_THRESHOLD       Minor violations threshold (default: 8)
  A11Y_FAIL_ON_REGRESSION    Fail on regression detection (default: true)
  A11Y_GENERATE_BASELINE     Generate new baseline (default: false)
  A11Y_REPORT_FORMATS        Report formats (default: json,html,junit)
  A11Y_TEST_URLS             URLs to test (default: /,/dashboard,/chat,/settings)
  A11Y_TIMEOUT               Test timeout in ms (default: 30000)
  A11Y_RETRIES               Number of retries (default: 2)

Examples:
  npm run test:accessibility:ci
  A11Y_GENERATE_BASELINE=true npm run test:accessibility:ci
  A11Y_FAIL_ON_REGRESSION=false npm run test:accessibility:ci
      `);
      break;
    default:
      main();
      break;
  }
}

module.exports = {
  main,
  testPage,
  detectRegressions,
  generateReports
};