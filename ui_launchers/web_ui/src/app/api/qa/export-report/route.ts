import { NextRequest, NextResponse } from 'next/server';
import { QualityMetricsCollector } from '@/lib/qa/quality-metrics-collector';
import * as fs from 'fs';
import * as path from 'path';

const collector = new QualityMetricsCollector();

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { format = 'json', includeCharts = false } = body;
    
    // Collect all quality data
    const metrics = await collector.collectAllMetrics();
    const qualityGates = await collector.generateQualityGates(metrics);
    const trends = await collector.generateTrends(30);
    
    const reportData = {
      timestamp: new Date().toISOString(),
      metrics,
      qualityGates,
      trends,
      summary: {
        overallScore: Math.round(
          (metrics.testCoverage.overall + 
           (metrics.testResults.passed / metrics.testResults.total * 100) +
           metrics.accessibility.score +
           metrics.security.score +
           metrics.codeQuality.maintainabilityIndex) / 5
        ),
        passedGates: qualityGates.filter(g => g.status === 'passed').length,
        totalGates: qualityGates.length,
        criticalIssues: metrics.security.vulnerabilities.critical + metrics.accessibility.violations
      }
    };
    
    if (format === 'json') {
      return NextResponse.json(reportData, {
        headers: {
          'Content-Disposition': `attachment; filename="qa-report-${new Date().toISOString().split('T')[0]}.json"`
        }
      });
    }
    
    if (format === 'pdf') {
      // Generate PDF report
      const pdfContent = await generatePdfReport(reportData, includeCharts);
      
      return new NextResponse(pdfContent as BodyInit, {
        headers: {
          'Content-Type': 'application/pdf',
          'Content-Disposition': `attachment; filename="qa-report-${new Date().toISOString().split('T')[0]}.pdf"`
        }
      });
    }
    
    if (format === 'html') {
      const htmlContent = generateHtmlReport(reportData, includeCharts);
      
      return new NextResponse(htmlContent, {
        headers: {
          'Content-Type': 'text/html',
          'Content-Disposition': `attachment; filename="qa-report-${new Date().toISOString().split('T')[0]}.html"`
        }
      });
    }
    
    return NextResponse.json({ error: 'Unsupported format' }, { status: 400 });
  } catch (error) {
    console.error('Failed to export quality report:', error);
    return NextResponse.json(
      { error: 'Failed to export quality report' },
      { status: 500 }
    );
  }
}

async function generatePdfReport(reportData: any, includeCharts: boolean): Promise<Buffer> {
  // This would typically use a library like puppeteer or jsPDF
  // For now, return a simple text-based PDF placeholder
  const textContent = `
Quality Assurance Report
Generated: ${new Date(reportData.timestamp).toLocaleString()}

Overall Quality Score: ${reportData.summary.overallScore}%
Quality Gates Passed: ${reportData.summary.passedGates}/${reportData.summary.totalGates}
Critical Issues: ${reportData.summary.criticalIssues}

Test Coverage:
- Unit Tests: ${reportData.metrics.testCoverage.unit}%
- Integration Tests: ${reportData.metrics.testCoverage.integration}%
- E2E Tests: ${reportData.metrics.testCoverage.e2e}%
- Visual Tests: ${reportData.metrics.testCoverage.visual}%
- Overall: ${reportData.metrics.testCoverage.overall}%

Test Results:
- Total: ${reportData.metrics.testResults.total}
- Passed: ${reportData.metrics.testResults.passed}
- Failed: ${reportData.metrics.testResults.failed}
- Skipped: ${reportData.metrics.testResults.skipped}
- Flaky: ${reportData.metrics.testResults.flaky}

Performance:
- Load Time: ${reportData.metrics.performance.loadTime}ms
- Interaction Time: ${reportData.metrics.performance.interactionTime}ms
- Memory Usage: ${reportData.metrics.performance.memoryUsage}MB
- Error Rate: ${reportData.metrics.performance.errorRate}%

Accessibility:
- Score: ${reportData.metrics.accessibility.score}%
- Violations: ${reportData.metrics.accessibility.violations}
- Warnings: ${reportData.metrics.accessibility.warnings}
- Passes: ${reportData.metrics.accessibility.passes}

Security:
- Score: ${reportData.metrics.security.score}%
- Critical Vulnerabilities: ${reportData.metrics.security.vulnerabilities.critical}
- High Vulnerabilities: ${reportData.metrics.security.vulnerabilities.high}
- Medium Vulnerabilities: ${reportData.metrics.security.vulnerabilities.medium}
- Low Vulnerabilities: ${reportData.metrics.security.vulnerabilities.low}

Code Quality:
- Maintainability Index: ${reportData.metrics.codeQuality.maintainabilityIndex}%
- Technical Debt: ${reportData.metrics.codeQuality.technicalDebt}h
- Duplicate Code: ${reportData.metrics.codeQuality.duplicateCode}%
- Complexity: ${reportData.metrics.codeQuality.complexity}

Quality Gates:
${reportData.qualityGates.map((gate: any) => 
  `- ${gate.name}: ${gate.status.toUpperCase()} (${gate.actual}% vs ${gate.threshold}% threshold)`
).join('\n')}
  `;
  
  // Convert text to PDF buffer (simplified)
  return Buffer.from(textContent, 'utf8');
}

function generateHtmlReport(reportData: any, includeCharts: boolean): string {
  return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quality Assurance Report</title>
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
        .metrics {
            padding: 30px;
        }
        .metric-section {
            margin-bottom: 30px;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            overflow: hidden;
        }
        .metric-header {
            background: #f8f9fa;
            padding: 15px 20px;
            font-weight: bold;
            border-bottom: 1px solid #dee2e6;
        }
        .metric-content {
            padding: 20px;
        }
        .metric-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }
        .metric-row:last-child {
            border-bottom: none;
        }
        .quality-gates {
            padding: 30px;
            background: #f8f9fa;
        }
        .gate {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            margin-bottom: 10px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .gate-passed { border-left: 4px solid #28a745; }
        .gate-warning { border-left: 4px solid #ffc107; }
        .gate-failed { border-left: 4px solid #dc3545; }
        .status-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }
        .status-passed { background: #d4edda; color: #155724; }
        .status-warning { background: #fff3cd; color: #856404; }
        .status-failed { background: #f8d7da; color: #721c24; }
        .timestamp {
            color: #6c757d;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Quality Assurance Report</h1>
            <p class="timestamp">Generated on ${new Date(reportData.timestamp).toLocaleString()}</p>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <div class="summary-number" style="color: #007bff;">${reportData.summary.overallScore}%</div>
                <div>Overall Quality Score</div>
            </div>
            <div class="summary-card">
                <div class="summary-number" style="color: #28a745;">${reportData.summary.passedGates}</div>
                <div>Quality Gates Passed</div>
            </div>
            <div class="summary-card">
                <div class="summary-number" style="color: #6c757d;">${reportData.summary.totalGates}</div>
                <div>Total Quality Gates</div>
            </div>
            <div class="summary-card">
                <div class="summary-number" style="color: #dc3545;">${reportData.summary.criticalIssues}</div>
                <div>Critical Issues</div>
            </div>
        </div>
        
        <div class="metrics">
            <div class="metric-section">
                <div class="metric-header">Test Coverage</div>
                <div class="metric-content">
                    <div class="metric-row">
                        <span>Unit Tests</span>
                        <span>${reportData.metrics.testCoverage.unit}%</span>
                    </div>
                    <div class="metric-row">
                        <span>Integration Tests</span>
                        <span>${reportData.metrics.testCoverage.integration}%</span>
                    </div>
                    <div class="metric-row">
                        <span>E2E Tests</span>
                        <span>${reportData.metrics.testCoverage.e2e}%</span>
                    </div>
                    <div class="metric-row">
                        <span>Visual Tests</span>
                        <span>${reportData.metrics.testCoverage.visual}%</span>
                    </div>
                    <div class="metric-row" style="font-weight: bold;">
                        <span>Overall Coverage</span>
                        <span>${reportData.metrics.testCoverage.overall}%</span>
                    </div>
                </div>
            </div>
            
            <div class="metric-section">
                <div class="metric-header">Test Results</div>
                <div class="metric-content">
                    <div class="metric-row">
                        <span>Total Tests</span>
                        <span>${reportData.metrics.testResults.total}</span>
                    </div>
                    <div class="metric-row">
                        <span>Passed</span>
                        <span style="color: #28a745;">${reportData.metrics.testResults.passed}</span>
                    </div>
                    <div class="metric-row">
                        <span>Failed</span>
                        <span style="color: #dc3545;">${reportData.metrics.testResults.failed}</span>
                    </div>
                    <div class="metric-row">
                        <span>Skipped</span>
                        <span style="color: #ffc107;">${reportData.metrics.testResults.skipped}</span>
                    </div>
                    <div class="metric-row">
                        <span>Flaky</span>
                        <span style="color: #fd7e14;">${reportData.metrics.testResults.flaky}</span>
                    </div>
                </div>
            </div>
            
            <div class="metric-section">
                <div class="metric-header">Performance</div>
                <div class="metric-content">
                    <div class="metric-row">
                        <span>Load Time</span>
                        <span>${reportData.metrics.performance.loadTime}ms</span>
                    </div>
                    <div class="metric-row">
                        <span>Interaction Time</span>
                        <span>${reportData.metrics.performance.interactionTime}ms</span>
                    </div>
                    <div class="metric-row">
                        <span>Memory Usage</span>
                        <span>${reportData.metrics.performance.memoryUsage}MB</span>
                    </div>
                    <div class="metric-row">
                        <span>Error Rate</span>
                        <span>${reportData.metrics.performance.errorRate}%</span>
                    </div>
                </div>
            </div>
            
            <div class="metric-section">
                <div class="metric-header">Accessibility</div>
                <div class="metric-content">
                    <div class="metric-row">
                        <span>Score</span>
                        <span>${reportData.metrics.accessibility.score}%</span>
                    </div>
                    <div class="metric-row">
                        <span>Violations</span>
                        <span style="color: #dc3545;">${reportData.metrics.accessibility.violations}</span>
                    </div>
                    <div class="metric-row">
                        <span>Warnings</span>
                        <span style="color: #ffc107;">${reportData.metrics.accessibility.warnings}</span>
                    </div>
                    <div class="metric-row">
                        <span>Passes</span>
                        <span style="color: #28a745;">${reportData.metrics.accessibility.passes}</span>
                    </div>
                </div>
            </div>
            
            <div class="metric-section">
                <div class="metric-header">Security</div>
                <div class="metric-content">
                    <div class="metric-row">
                        <span>Score</span>
                        <span>${reportData.metrics.security.score}%</span>
                    </div>
                    <div class="metric-row">
                        <span>Critical Vulnerabilities</span>
                        <span style="color: #dc3545;">${reportData.metrics.security.vulnerabilities.critical}</span>
                    </div>
                    <div class="metric-row">
                        <span>High Vulnerabilities</span>
                        <span style="color: #dc3545;">${reportData.metrics.security.vulnerabilities.high}</span>
                    </div>
                    <div class="metric-row">
                        <span>Medium Vulnerabilities</span>
                        <span style="color: #ffc107;">${reportData.metrics.security.vulnerabilities.medium}</span>
                    </div>
                    <div class="metric-row">
                        <span>Low Vulnerabilities</span>
                        <span style="color: #6c757d;">${reportData.metrics.security.vulnerabilities.low}</span>
                    </div>
                </div>
            </div>
            
            <div class="metric-section">
                <div class="metric-header">Code Quality</div>
                <div class="metric-content">
                    <div class="metric-row">
                        <span>Maintainability Index</span>
                        <span>${reportData.metrics.codeQuality.maintainabilityIndex}%</span>
                    </div>
                    <div class="metric-row">
                        <span>Technical Debt</span>
                        <span>${reportData.metrics.codeQuality.technicalDebt}h</span>
                    </div>
                    <div class="metric-row">
                        <span>Duplicate Code</span>
                        <span>${reportData.metrics.codeQuality.duplicateCode}%</span>
                    </div>
                    <div class="metric-row">
                        <span>Complexity</span>
                        <span>${reportData.metrics.codeQuality.complexity}</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="quality-gates">
            <h2>Quality Gates</h2>
            ${reportData.qualityGates.map((gate: any) => `
                <div class="gate gate-${gate.status}">
                    <div>
                        <strong>${gate.name}</strong>
                        <div style="font-size: 0.9em; color: #6c757d;">
                            ${gate.actual}% (threshold: ${gate.threshold}%)
                        </div>
                    </div>
                    <div class="status-badge status-${gate.status}">
                        ${gate.status}
                    </div>
                </div>
            `).join('')}
        </div>
    </div>
</body>
</html>
  `;
}