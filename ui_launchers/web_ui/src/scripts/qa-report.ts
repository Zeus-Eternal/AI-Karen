import { QualityMetricsCollector, QualityGate } from '../lib/qa/quality-metrics-collector';
import * as fs from 'fs';
import * as path from 'path';

// Helper to add color to console output
const colors = {
  reset: "\x1b[0m",
  red: "\x1b[31m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  blue: "\x1b[34m",
  bold: "\x1b[1m",
};

function colorize(text: string, color: keyof typeof colors) {
  return `${colors[color]}${text}${colors.reset}`;
}

function printMetric(label: string, value: any, unit: string = '') {
  console.log(`  ${label.padEnd(25)} ${colorize(String(value), 'blue')} ${unit}`);
}

function printGateStatus(gate: QualityGate) {
  let statusText;
  switch (gate.status) {
    case 'passed':
      statusText = colorize('PASSED', 'green');
      break;
    case 'failed':
      statusText = colorize('FAILED', 'red');
      break;
    case 'warning':
      statusText = colorize('WARNING', 'yellow');
      break;
  }
  console.log(
    `  ${gate.name.padEnd(20)} ${statusText.padEnd(15)} (Actual: ${gate.actual}, Threshold: ${gate.threshold})`
  );
}

async function runQAReport() {
  console.log(colorize('Running Quality Metrics Report...', 'bold'));

  const projectRoot = path.resolve(__dirname, '../.. empowering');
  const collector = new QualityMetricsCollector({ projectRoot });

  try {
    // 1. Collect Metrics
    const metrics = await collector.collectAllMetrics();

    // 2. Save latest.json
    const metricsDir = path.join(projectRoot, 'qa-metrics');
    if (!fs.existsSync(metricsDir)) {
      fs.mkdirSync(metricsDir, { recursive: true });
    }
    fs.writeFileSync(path.join(metricsDir, 'latest.json'), JSON.stringify(metrics, null, 2));
    console.log(colorize('\nMetrics saved to qa-metrics/latest.json', 'green'));

    // 3. Generate and print pretty table
    console.log(colorize('\n--- Quality Metrics Summary ---', 'bold'));

    console.log(colorize('\nTest Coverage:', 'yellow'));
    printMetric('Overall Coverage', `${metrics.testCoverage.overall}%`);

    console.log(colorize('\nTest Results:', 'yellow'));
    printMetric('Pass Rate', `${(metrics.testResults.passed / metrics.testResults.total * 100).toFixed(2)}%`);
    printMetric('Flaky Tests', metrics.testResults.flaky);

    console.log(colorize('\nPerformance:', 'yellow'));
    printMetric('Load Time', `${metrics.performance.loadTime}ms`);

    console.log(colorize('\nAccessibility:', 'yellow'));
    printMetric('A11y Score', metrics.accessibility.score);

    console.log(colorize('\nSecurity:', 'yellow'));
    printMetric('Security Score', metrics.security.score);
    printMetric('Critical Vulnerabilities', metrics.security.vulnerabilities.critical);

    console.log(colorize('\nCode Quality:', 'yellow'));
    printMetric('Maintainability Index', metrics.codeQuality.maintainabilityIndex);

    // 4. Check gates and exit status
    console.log(colorize('\n--- Quality Gates ---', 'bold'));
    const gates = await collector.generateQualityGates(metrics);
    let hasFailedGate = false;

    gates.forEach(gate => {
      printGateStatus(gate);
      if (gate.status === 'failed') {
        hasFailedGate = true;
      }
    });

    if (hasFailedGate) {
      console.error(colorize('\nOne or more quality gates failed. Build would be rejected in CI.', 'red'));
      process.exit(1);
    } else {
      console.log(colorize('\nAll quality gates passed!', 'green'));
      process.exit(0);
    }

  } catch (error) {
    console.error(colorize('\nAn error occurred while generating the QA report:', 'red'));
    console.error(error);
    process.exit(1);
  }
}

runQAReport();
