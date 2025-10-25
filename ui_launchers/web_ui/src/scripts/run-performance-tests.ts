#!/usr/bin/env node
/**
 * Performance Test Runner
 * 
 * Runs comprehensive performance tests and benchmarks for the optimization components.
 * Generates performance reports and recommendations.
 * 
 * Requirements: 1.4, 4.4
 */

import { execSync } from 'child_process';
import { writeFileSync } from 'fs';
import { join } from 'path';

interface TestResult {
  name: string;
  duration: number;
  passed: boolean;
  metrics?: any;
  error?: string;
}

interface PerformanceReport {
  timestamp: string;
  totalTests: number;
  passedTests: number;
  failedTests: number;
  totalDuration: number;
  results: TestResult[];
  recommendations: string[];
  summary: {
    connectionPoolPerformance: string;
    cacheEfficiency: string;
    queryOptimization: string;
    overallRating: string;
  };
}

class PerformanceTestRunner {
  private results: TestResult[] = [];
  private startTime: number = 0;

  async runAllTests(): Promise<PerformanceReport> {
    console.log('🚀 Starting Performance Test Suite...\n');
    this.startTime = Date.now();

    // Run individual test suites
    await this.runTestSuite('HTTP Connection Pool', 'src/lib/performance/__tests__/http-connection-pool.test.ts');
    await this.runTestSuite('Request/Response Cache', 'src/lib/performance/__tests__/request-response-cache.test.ts');
    await this.runTestSuite('Performance Benchmarks', 'src/lib/performance/__tests__/performance-benchmarks.test.ts');

    // Generate report
    const report = this.generateReport();
    
    // Save report
    this.saveReport(report);
    
    // Display summary
    this.displaySummary(report);

    return report;
  }

  private async runTestSuite(name: string, testFile: string): Promise<void> {
    console.log(`📋 Running ${name} tests...`);
    
    try {
      const startTime = Date.now();
      
      // Run the test file using vitest
      const command = `npx vitest run ${testFile} --reporter=json`;
      const output = execSync(command, { 
        encoding: 'utf8',
        cwd: process.cwd(),
        timeout: 60000, // 1 minute timeout
      });

      const duration = Date.now() - startTime;
      
      // Parse test results (simplified)
      const passed = !output.includes('FAILED') && !output.includes('Error');
      
      this.results.push({
        name,
        duration,
        passed,
        metrics: this.extractMetrics(output),
      });

      console.log(`✅ ${name}: ${passed ? 'PASSED' : 'FAILED'} (${duration}ms)\n`);

    } catch (error) {
      const duration = Date.now() - this.startTime;
      
      this.results.push({
        name,
        duration,
        passed: false,
        error: error instanceof Error ? error.message : String(error),
      });

      console.log(`❌ ${name}: FAILED (${duration}ms)`);
      console.log(`   Error: ${error}\n`);
    }
  }

  private extractMetrics(output: string): any {
    // Extract performance metrics from test output
    // This is a simplified implementation - in practice, you'd parse structured output
    const metrics: any = {};
    
    if (output.includes('requests in')) {
      const match = output.match(/(\d+) requests in (\d+)ms/);
      if (match) {
        metrics.requests = parseInt(match[1]);
        metrics.duration = parseInt(match[2]);
        metrics.throughput = metrics.requests / (metrics.duration / 1000);
      }
    }
    
    if (output.includes('Hit rate:')) {
      const match = output.match(/Hit rate: ([\d.]+)%/);
      if (match) {
        metrics.hitRate = parseFloat(match[1]) / 100;
      }
    }
    
    if (output.includes('Connection reuse:')) {
      const match = output.match(/Connection reuse: (\d+)/);
      if (match) {
        metrics.connectionReuse = parseInt(match[1]);
      }
    }

    return metrics;
  }

  private generateReport(): PerformanceReport {
    const totalDuration = Date.now() - this.startTime;
    const passedTests = this.results.filter(r => r.passed).length;
    const failedTests = this.results.length - passedTests;

    const recommendations = this.generateRecommendations();
    const summary = this.generateSummary();

    return {
      timestamp: new Date().toISOString(),
      totalTests: this.results.length,
      passedTests,
      failedTests,
      totalDuration,
      results: this.results,
      recommendations,
      summary,
    };
  }

  private generateRecommendations(): string[] {
    const recommendations: string[] = [];
    
    // Analyze results and generate recommendations
    const failedTests = this.results.filter(r => !r.passed);
    if (failedTests.length > 0) {
      recommendations.push(`${failedTests.length} test suite(s) failed - investigate and fix issues`);
    }

    // Check performance metrics
    const benchmarkResult = this.results.find(r => r.name === 'Performance Benchmarks');
    if (benchmarkResult?.metrics) {
      if (benchmarkResult.metrics.throughput < 10) {
        recommendations.push('Request throughput is low - consider optimizing connection pool settings');
      }
      
      if (benchmarkResult.metrics.hitRate < 0.7) {
        recommendations.push('Cache hit rate is below 70% - review caching strategy and TTL settings');
      }
    }

    // General recommendations
    if (recommendations.length === 0) {
      recommendations.push('All performance tests passed - system is performing well');
      recommendations.push('Consider running load tests with higher concurrency');
      recommendations.push('Monitor performance metrics in production environment');
    }

    return recommendations;
  }

  private generateSummary(): PerformanceReport['summary'] {
    const connectionPoolResult = this.results.find(r => r.name === 'HTTP Connection Pool');
    const cacheResult = this.results.find(r => r.name === 'Request/Response Cache');
    const benchmarkResult = this.results.find(r => r.name === 'Performance Benchmarks');

    return {
      connectionPoolPerformance: connectionPoolResult?.passed ? 'Good' : 'Needs Attention',
      cacheEfficiency: cacheResult?.passed ? 'Good' : 'Needs Attention',
      queryOptimization: benchmarkResult?.passed ? 'Good' : 'Needs Attention',
      overallRating: this.results.every(r => r.passed) ? 'Excellent' : 
                     this.results.filter(r => r.passed).length >= this.results.length * 0.8 ? 'Good' : 'Poor',
    };
  }

  private saveReport(report: PerformanceReport): void {
    const reportPath = join(process.cwd(), 'performance-test-report.json');
    writeFileSync(reportPath, JSON.stringify(report, null, 2));
    
    // Also save a human-readable version
    const readableReport = this.generateReadableReport(report);
    const readablePath = join(process.cwd(), 'performance-test-report.md');
    writeFileSync(readablePath, readableReport);
    
    console.log(`📊 Performance report saved to:`);
    console.log(`   JSON: ${reportPath}`);
    console.log(`   Markdown: ${readablePath}\n`);
  }

  private generateReadableReport(report: PerformanceReport): string {
    const { summary, results, recommendations } = report;
    
    let markdown = `# Performance Test Report\n\n`;
    markdown += `**Generated:** ${new Date(report.timestamp).toLocaleString()}\n`;
    markdown += `**Total Duration:** ${report.totalDuration}ms\n`;
    markdown += `**Tests:** ${report.passedTests}/${report.totalTests} passed\n\n`;

    // Summary
    markdown += `## Summary\n\n`;
    markdown += `- **Connection Pool Performance:** ${summary.connectionPoolPerformance}\n`;
    markdown += `- **Cache Efficiency:** ${summary.cacheEfficiency}\n`;
    markdown += `- **Query Optimization:** ${summary.queryOptimization}\n`;
    markdown += `- **Overall Rating:** ${summary.overallRating}\n\n`;

    // Test Results
    markdown += `## Test Results\n\n`;
    results.forEach(result => {
      markdown += `### ${result.name}\n`;
      markdown += `- **Status:** ${result.passed ? '✅ PASSED' : '❌ FAILED'}\n`;
      markdown += `- **Duration:** ${result.duration}ms\n`;
      
      if (result.metrics) {
        markdown += `- **Metrics:**\n`;
        Object.entries(result.metrics).forEach(([key, value]) => {
          markdown += `  - ${key}: ${value}\n`;
        });
      }
      
      if (result.error) {
        markdown += `- **Error:** ${result.error}\n`;
      }
      
      markdown += `\n`;
    });

    // Recommendations
    markdown += `## Recommendations\n\n`;
    recommendations.forEach((rec, index) => {
      markdown += `${index + 1}. ${rec}\n`;
    });

    return markdown;
  }

  private displaySummary(report: PerformanceReport): void {
    console.log('📈 Performance Test Summary');
    console.log('=' .repeat(50));
    console.log(`Total Tests: ${report.totalTests}`);
    console.log(`Passed: ${report.passedTests}`);
    console.log(`Failed: ${report.failedTests}`);
    console.log(`Duration: ${report.totalDuration}ms`);
    console.log(`Overall Rating: ${report.summary.overallRating}`);
    console.log('');

    if (report.recommendations.length > 0) {
      console.log('🔍 Recommendations:');
      report.recommendations.forEach((rec, index) => {
        console.log(`${index + 1}. ${rec}`);
      });
    }
  }
}

// Run the tests if this script is executed directly
if (require.main === module) {
  const runner = new PerformanceTestRunner();
  
  runner.runAllTests()
    .then((report) => {
      process.exit(report.failedTests > 0 ? 1 : 0);
    })
    .catch((error) => {
      console.error('❌ Performance test runner failed:', error);
      process.exit(1);
    });
}

export { PerformanceTestRunner, type PerformanceReport };