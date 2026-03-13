#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class VisualTestMaintenance {
  constructor() {
    this.baselineDir = path.join(process.cwd(), 'e2e-artifacts', 'visual-baselines');
    this.actualDir = path.join(process.cwd(), 'e2e-artifacts', 'visual-actual');
    this.diffDir = path.join(process.cwd(), 'e2e-artifacts', 'visual-diffs');
    this.reportDir = path.join(process.cwd(), 'e2e-artifacts', 'visual-reports');
    
    this.ensureDirectories();
  }

  ensureDirectories() {
    [this.baselineDir, this.actualDir, this.diffDir, this.reportDir].forEach(dir => {
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
    });
  }

  async updateBaselines() {
    console.log('🔄 Updating visual baselines...');
    
    try {
      // Run visual tests to generate new screenshots
      execSync('npx playwright test e2e/visual --update-snapshots', { 
        stdio: 'inherit',
        cwd: process.cwd()
      });
      
      console.log('✅ Visual baselines updated successfully');
    } catch (error) {
      console.error('❌ Failed to update baselines:', error.message);
      process.exit(1);
    }
  }

  async approveChanges(testNames = []) {
    console.log('✅ Approving visual changes...');
    
    const actualFiles = fs.readdirSync(this.actualDir).filter(f => f.endsWith('.png'));
    const filesToApprove = testNames.length > 0 
      ? actualFiles.filter(f => testNames.some(name => f.includes(name)))
      : actualFiles;
    
    let approvedCount = 0;
    
    for (const file of filesToApprove) {
      const actualPath = path.join(this.actualDir, file);
      const baselinePath = path.join(this.baselineDir, file);
      
      if (fs.existsSync(actualPath)) {
        fs.copyFileSync(actualPath, baselinePath);
        approvedCount++;
        console.log(`  ✓ Approved: ${file}`);
      }
    }
    
    console.log(`✅ Approved ${approvedCount} visual changes`);
  }

  async rejectChanges(testNames = []) {
    console.log('❌ Rejecting visual changes...');
    
    const actualFiles = fs.readdirSync(this.actualDir).filter(f => f.endsWith('.png'));
    const filesToReject = testNames.length > 0 
      ? actualFiles.filter(f => testNames.some(name => f.includes(name)))
      : actualFiles;
    
    let rejectedCount = 0;
    
    for (const file of filesToReject) {
      const actualPath = path.join(this.actualDir, file);
      const diffPath = path.join(this.diffDir, file.replace('.png', '-diff.png'));
      
      if (fs.existsSync(actualPath)) {
        fs.unlinkSync(actualPath);
        rejectedCount++;
        console.log(`  ✗ Rejected: ${file}`);
        
        if (fs.existsSync(diffPath)) {
          console.log(`    Diff available: ${diffPath}`);
        }
      }
    }
    
    console.log(`❌ Rejected ${rejectedCount} visual changes`);
  }

  async generateReport() {
    console.log('📊 Generating visual test report...');
    
    const actualFiles = fs.readdirSync(this.actualDir).filter(f => f.endsWith('.png'));
    const baselineFiles = fs.readdirSync(this.baselineDir).filter(f => f.endsWith('.png'));
    const diffFiles = fs.readdirSync(this.diffDir).filter(f => f.endsWith('-diff.png'));
    
    const report = {
      timestamp: new Date().toISOString(),
      summary: {
        totalTests: actualFiles.length,
        passedTests: 0,
        failedTests: 0,
        newBaselines: 0
      },
      testResults: []
    };
    
    for (const actualFile of actualFiles) {
      const testName = actualFile.replace('.png', '');
      const baselineExists = baselineFiles.includes(actualFile);
      const diffExists = diffFiles.includes(`${testName}-diff.png`);
      
      const result = {
        testName,
        status: 'unknown',
        baselinePath: baselineExists ? path.join(this.baselineDir, actualFile) : null,
        actualPath: path.join(this.actualDir, actualFile),
        diffPath: diffExists ? path.join(this.diffDir, `${testName}-diff.png`) : null
      };
      
      if (!baselineExists) {
        result.status = 'new';
        report.summary.newBaselines++;
      } else if (diffExists) {
        result.status = 'failed';
        report.summary.failedTests++;
      } else {
        result.status = 'passed';
        report.summary.passedTests++;
      }
      
      report.testResults.push(result);
    }
    
    // Generate HTML report
    const htmlReport = this.generateHtmlReport(report);
    const reportPath = path.join(this.reportDir, `visual-test-report-${Date.now()}.html`);
    fs.writeFileSync(reportPath, htmlReport);
    
    // Generate JSON report
    const jsonReportPath = path.join(this.reportDir, `visual-test-report-${Date.now()}.json`);
    fs.writeFileSync(jsonReportPath, JSON.stringify(report, null, 2));
    
    console.log(`📊 Report generated: ${reportPath}`);
    console.log(`📊 JSON report: ${jsonReportPath}`);
    
    // Print summary
    console.log('\n📈 Visual Test Summary:');
    console.log(`  Total Tests: ${report.summary.totalTests}`);
    console.log(`  ✅ Passed: ${report.summary.passedTests}`);
    console.log(`  ❌ Failed: ${report.summary.failedTests}`);
    console.log(`  🆕 New: ${report.summary.newBaselines}`);
    
    return report;
  }

  generateHtmlReport(report) {
    return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Visual Test Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
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
        .new { color: #007bff; }
        .total { color: #6c757d; }
        .results {
            padding: 30px;
        }
        .test-result {
            border: 1px solid #dee2e6;
            border-radius: 8px;
            margin-bottom: 20px;
            overflow: hidden;
        }
        .test-header {
            padding: 15px 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .test-name {
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
        .status-new {
            background: #d1ecf1;
            color: #0c5460;
        }
        .test-images {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            padding: 20px;
        }
        .image-container {
            text-align: center;
        }
        .image-container img {
            max-width: 100%;
            height: auto;
            border: 1px solid #dee2e6;
            border-radius: 4px;
        }
        .image-label {
            margin-top: 10px;
            font-weight: bold;
            color: #6c757d;
        }
        .timestamp {
            color: #6c757d;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Visual Test Report</h1>
            <p class="timestamp">Generated on ${new Date(report.timestamp).toLocaleString()}</p>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <div class="summary-number total">${report.summary.totalTests}</div>
                <div>Total Tests</div>
            </div>
            <div class="summary-card">
                <div class="summary-number passed">${report.summary.passedTests}</div>
                <div>Passed</div>
            </div>
            <div class="summary-card">
                <div class="summary-number failed">${report.summary.failedTests}</div>
                <div>Failed</div>
            </div>
            <div class="summary-card">
                <div class="summary-number new">${report.summary.newBaselines}</div>
                <div>New Baselines</div>
            </div>
        </div>
        
        <div class="results">
            <h2>Test Results</h2>
            ${report.testResults.map(result => `
                <div class="test-result">
                    <div class="test-header">
                        <div class="test-name">${result.testName}</div>
                        <div class="status-badge status-${result.status}">${result.status}</div>
                    </div>
                    ${result.status === 'failed' ? `
                        <div class="test-images">
                            ${result.baselinePath ? `
                                <div class="image-container">
                                    <img src="${result.baselinePath}" alt="Baseline">
                                    <div class="image-label">Baseline</div>
                                </div>
                            ` : ''}
                            <div class="image-container">
                                <img src="${result.actualPath}" alt="Actual">
                                <div class="image-label">Actual</div>
                            </div>
                            ${result.diffPath ? `
                                <div class="image-container">
                                    <img src="${result.diffPath}" alt="Diff">
                                    <div class="image-label">Difference</div>
                                </div>
                            ` : ''}
                        </div>
                    ` : result.status === 'new' ? `
                        <div class="test-images">
                            <div class="image-container">
                                <img src="${result.actualPath}" alt="New Baseline">
                                <div class="image-label">New Baseline</div>
                            </div>
                        </div>
                    ` : ''}
                </div>
            `).join('')}
        </div>
    </div>
</body>
</html>
    `;
  }

  async cleanup(daysOld = 7) {
    console.log(`🧹 Cleaning up files older than ${daysOld} days...`);
    
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - daysOld);
    
    let cleanedCount = 0;
    
    [this.actualDir, this.diffDir, this.reportDir].forEach(dir => {
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

  async compareDirectories() {
    console.log('🔍 Comparing baseline and actual directories...');
    
    const baselineFiles = new Set(fs.readdirSync(this.baselineDir).filter(f => f.endsWith('.png')));
    const actualFiles = new Set(fs.readdirSync(this.actualDir).filter(f => f.endsWith('.png')));
    
    const missingBaselines = [...actualFiles].filter(f => !baselineFiles.has(f));
    const orphanedBaselines = [...baselineFiles].filter(f => !actualFiles.has(f));
    
    if (missingBaselines.length > 0) {
      console.log('\n📋 Missing baselines:');
      missingBaselines.forEach(file => console.log(`  - ${file}`));
    }
    
    if (orphanedBaselines.length > 0) {
      console.log('\n🗑️  Orphaned baselines:');
      orphanedBaselines.forEach(file => console.log(`  - ${file}`));
    }
    
    if (missingBaselines.length === 0 && orphanedBaselines.length === 0) {
      console.log('✅ All baselines are in sync');
    }
    
    return { missingBaselines, orphanedBaselines };
  }
}

// CLI Interface
async function main() {
  const maintenance = new VisualTestMaintenance();
  const command = process.argv[2];
  const args = process.argv.slice(3);
  
  switch (command) {
    case 'update':
      await maintenance.updateBaselines();
      break;
      
    case 'approve':
      await maintenance.approveChanges(args);
      break;
      
    case 'reject':
      await maintenance.rejectChanges(args);
      break;
      
    case 'report':
      await maintenance.generateReport();
      break;
      
    case 'cleanup':
      const days = parseInt(args[0]) || 7;
      await maintenance.cleanup(days);
      break;
      
    case 'compare':
      await maintenance.compareDirectories();
      break;
      
    default:
      console.log(`
Visual Test Maintenance Tool

Usage:
  node visual-test-maintenance.js <command> [options]

Commands:
  update                    Update all visual baselines
  approve [test-names...]   Approve visual changes for specific tests (or all)
  reject [test-names...]    Reject visual changes for specific tests (or all)
  report                    Generate visual test report
  cleanup [days]            Clean up old files (default: 7 days)
  compare                   Compare baseline and actual directories

Examples:
  node visual-test-maintenance.js update
  node visual-test-maintenance.js approve login-page dashboard
  node visual-test-maintenance.js report
  node visual-test-maintenance.js cleanup 14
      `);
      break;
  }
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = VisualTestMaintenance;