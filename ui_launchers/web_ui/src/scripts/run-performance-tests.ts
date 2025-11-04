#!/usr/bin/env node
/**
 * Performance Test Runner
 *
 * Runs comprehensive performance tests and benchmarks for the optimization components.
 * Generates performance reports and recommendations.
 *
 * Usage:
 *   ts-node performance-test-runner.ts
 *   # or after build:
 *   node dist/performance-test-runner.js
 */

import { execSync } from 'child_process';
import { writeFileSync } from 'fs';
import { join } from 'path';

interface TestResult {
  name: string;
  duration: number;
  passed: boolean;
  metrics?: Record<string, any>;
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
  private startTime = 0;

  async runAllTests(): Promise<PerformanceReport> {
    this.startTime = Date.now();

    // --- Run individual test suites (update paths as needed) ---
    await this.runTestSuite(
      'HTTP Connection Pool',
      'src/lib/performance/__tests__/http-connection-pool.test.ts',
    );
    await this.runTestSuite(
      'Request/Response Cache',
      'src/lib/performance/__tests__/request-response-cache.test.ts',
    );
    await this.runTestSuite(
      'Performance Benchmarks',
      'src/lib/performance/__tests__/performance-benchmarks.test.ts',
    );

    // --- Generate + persist report ---
    const report = this.generateReport();
    this.saveReport(report);
    this.displaySummary(report);

    return report;
  }

  private async runTestSuite(name: string, testFile: string): Promise<void> {
    const suiteStart = Date.now();
    try {
      // --reporter=json gives a single JSON payload describing results
      const command = `npx vitest run ${testFile} --reporter=json`;
      const output = execSync(command, {
        encoding: 'utf8',
        cwd: process.cwd(),
        timeout: 120_000, // 2 minute timeout per suite
        stdio: ['ignore', 'pipe', 'pipe'],
      });

      const duration = Date.now() - suiteStart;

      const parsed = this.safeParseVitestJson(output);
      const passed = parsed ? parsed.numFailedTests === 0 && parsed.numFailedTestSuites === 0
                            : this.fallbackPassScan(output);

      this.results.push({
        name,
        duration,
        passed,
        metrics: this.extractMetricsFromOutput(output),
      });

      console.log(`${passed ? '✅' : '❌'} ${name}: ${passed ? 'PASSED' : 'FAILED'} (${duration}ms)\n`);
    } catch (err) {
      const duration = Date.now() - suiteStart;
      let msg = 'Unknown error';
      // Vitest often writes structured output to stdout and the error to stderr
      if (err && typeof err === 'object') {
        const anyErr = err as any;
        msg =
          anyErr?.message ??
          anyErr?.stderr?.toString?.() ??
          anyErr?.stdout?.toString?.() ??
          'Unknown error';
      }

      this.results.push({
        name,
        duration,
        passed: false,
        error: msg,
      });

      console.log(`❌ ${name}: FAILED (${duration}ms)\n${msg}\n`);
    }
  }

  private safeParseVitestJson(output: string): any | null {
    // Vitest JSON reporter generally emits a single JSON object.
    try {
      // Some environments might prepend log lines; try to locate leading '{'
      const firstBrace = output.indexOf('{');
      if (firstBrace >= 0) {
        const sliced = output.slice(firstBrace);
        return JSON.parse(sliced);
      }
      return JSON.parse(output);
    } catch {
      return null;
    }
  }

  private fallbackPassScan(output: string): boolean {
    // Very rough fallback in case JSON parsing fails.
    // If no "FAILED" and no "Error" tokens are found, assume pass.
    return !/FAILED|Error/i.test(output);
    }

  private extractMetricsFromOutput(output: string): Record<string, any> {
    // Lightweight pattern-based extraction; if your tests print structured
    // JSON (e.g., with console.log(JSON.stringify(...))), parse that instead.
    const metrics: Record<string, any> = {};

    // e.g., "1234 requests in 5000ms"
    if (/requests in/i.test(output)) {
      const m = output.match(/(\d+)\s+requests\s+in\s+(\d+)ms/i);
      if (m) {
        const requests = parseInt(m[1], 10);
        const durationMs = parseInt(m[2], 10);
        metrics.requests = requests;
        metrics.durationMs = durationMs;
        metrics.throughputRps = durationMs > 0 ? requests / (durationMs / 1000) : 0;
      }
    }

    // e.g., "Hit rate: 83.2%"
    if (/Hit rate:/i.test(output)) {
      const m = output.match(/Hit rate:\s+([\d.]+)%/i);
      if (m) metrics.hitRate = parseFloat(m[1]) / 100;
    }

    // e.g., "Connection reuse: 42"
    if (/Connection reuse:/i.test(output)) {
      const m = output.match(/Connection reuse:\s+(\d+)/i);
      if (m) metrics.connectionReuse = parseInt(m[1], 10);
    }

    return metrics;
  }

  private generateReport(): PerformanceReport {
    const totalDuration = Date.now() - this.startTime;
    const passedTests = this.results.filter((r) => r.passed).length;
    const failedTests = this.results.length - passedTests;

    return {
      timestamp: new Date().toISOString(),
      totalTests: this.results.length,
      passedTests,
      failedTests,
      totalDuration,
      results: this.results,
      recommendations: this.generateRecommendations(),
      summary: this.generateSummary(),
    };
  }

  private generateRecommendations(): string[] {
    const recs: string[] = [];
    const failed = this.results.filter((r) => !r.passed);

    if (failed.length > 0) {
      recs.push(`${failed.length} test suite(s) failed — investigate and fix issues.`);
    }

    const bench = this.results.find((r) => r.name === 'Performance Benchmarks');
    if (bench?.metrics) {
      if (typeof bench.metrics.throughputRps === 'number' && bench.metrics.throughputRps < 10) {
        recs.push('Request throughput is low — tune connection pool, batching, or concurrency.');
      }
      if (typeof bench.metrics.hitRate === 'number' && bench.metrics.hitRate < 0.7) {
        recs.push('Cache hit rate is < 70% — review cache keys, TTLs, warmup strategy, and invalidation.');
      }
    }

    if (recs.length === 0) {
      recs.push('All performance tests passed — system looks healthy.');
      recs.push('Consider running heavier load tests with increased concurrency.');
      recs.push('Monitor key metrics (p95 latency, error rate, saturation) in production.');
    }

    return recs;
  }

  private generateSummary(): PerformanceReport['summary'] {
    const connectionPool = this.results.find((r) => r.name === 'HTTP Connection Pool');
    const cache = this.results.find((r) => r.name === 'Request/Response Cache');
    const benchmarks = this.results.find((r) => r.name === 'Performance Benchmarks');

    const overall =
      this.results.every((r) => r.passed)
        ? 'Excellent'
        : this.results.filter((r) => r.passed).length >= Math.ceil(this.results.length * 0.8)
        ? 'Good'
        : 'Poor';

    return {
      connectionPoolPerformance: connectionPool?.passed ? 'Good' : 'Needs Attention',
      cacheEfficiency: cache?.passed ? 'Good' : 'Needs Attention',
      queryOptimization: benchmarks?.passed ? 'Good' : 'Needs Attention',
      overallRating: overall,
    };
  }

  private saveReport(report: PerformanceReport): void {
    const jsonPath = join(process.cwd(), 'performance-test-report.json');
    writeFileSync(jsonPath, JSON.stringify(report, null, 2));

    const mdPath = join(process.cwd(), 'performance-test-report.md');
    writeFileSync(mdPath, this.generateReadableReport(report));
  }

  private generateReadableReport(report: PerformanceReport): string {
    const { summary, results, recommendations } = report;

    const lines: string[] = [];
    lines.push(`# Performance Test Report`);
    lines.push('');
    lines.push(`**Generated:** ${new Date(report.timestamp).toLocaleString()}`);
    lines.push(`**Total Duration:** ${report.totalDuration}ms`);
    lines.push(`**Tests:** ${report.passedTests}/${report.totalTests} passed`);
    lines.push('');
    lines.push(`## Summary`);
    lines.push('');
    lines.push(`- **Connection Pool Performance:** ${summary.connectionPoolPerformance}`);
    lines.push(`- **Cache Efficiency:** ${summary.cacheEfficiency}`);
    lines.push(`- **Query Optimization:** ${summary.queryOptimization}`);
    lines.push(`- **Overall Rating:** ${summary.overallRating}`);
    lines.push('');
    lines.push(`## Test Results`);
    lines.push('');

    for (const r of results) {
      lines.push(`### ${r.name}`);
      lines.push(`- **Status:** ${r.passed ? '✅ PASSED' : '❌ FAILED'}`);
      lines.push(`- **Duration:** ${r.duration}ms`);
      if (r.metrics && Object.keys(r.metrics).length > 0) {
        lines.push(`- **Metrics:**`);
        for (const [k, v] of Object.entries(r.metrics)) {
          lines.push(`  - ${k}: ${v}`);
        }
      }
      if (r.error) {
        lines.push(`- **Error:** ${r.error}`);
      }
      lines.push('');
    }

    lines.push(`## Recommendations`);
    lines.push('');
    recommendations.forEach((rec, i) => lines.push(`${i + 1}. ${rec}`));
    lines.push('');

    return lines.join('\n');
  }

  private displaySummary(report: PerformanceReport): void {
    const line = '='.repeat(60);
    console.log(line);
    console.log('Performance Test Summary');
    console.log(line);
    console.log(`Total: ${report.totalTests}, Passed: ${report.passedTests}, Failed: ${report.failedTests}`);
    console.log(`Overall: ${report.summary.overallRating}`);
    if (report.recommendations.length) {
      console.log('\nRecommendations:');
      for (const rec of report.recommendations) {
        console.log(`- ${rec}`);
      }
    }
    console.log(line);
  }
}

// Run if executed directly
if (require.main === module) {
  const runner = new PerformanceTestRunner();
  runner
    .runAllTests()
    .then((report) => {
      process.exit(report.failedTests > 0 ? 1 : 0);
    })
    .catch((err) => {
      // eslint-disable-next-line no-console
      console.error('Performance tests crashed:', err instanceof Error ? err.stack || err.message : err);
      process.exit(1);
    });
}

export { PerformanceTestRunner, type PerformanceReport, type TestResult };
