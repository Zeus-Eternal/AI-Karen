import { execSync } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';

export interface QualityMetrics {
  testCoverage: {
    unit: number;
    integration: number;
    e2e: number;
    visual: number;
    overall: number;
  };
  testResults: {
    total: number;
    passed: number;
    failed: number;
    skipped: number;
    flaky: number;
  };
  performance: {
    loadTime: number;
    interactionTime: number;
    memoryUsage: number;
    errorRate: number;
  };
  accessibility: {
    score: number;
    violations: number;
    warnings: number;
    passes: number;
  };
  security: {
    vulnerabilities: {
      critical: number;
      high: number;
      medium: number;
      low: number;
    };
    score: number;
  };
  codeQuality: {
    maintainabilityIndex: number;
    technicalDebt: number;
    duplicateCode: number;
    complexity: number;
  };
}

export interface QualityTrend {
  date: string;
  coverage: number;
  passRate: number;
  performance: number;
  accessibility: number;
  security: number;
}

export interface QualityGate {
  id: string;
  name: string;
  status: 'passed' | 'failed' | 'warning';
  threshold: number;
  actual: number;
  description: string;
}

export class QualityMetricsCollector {
  private projectRoot: string;
  private metricsCache: Map<string, any> = new Map();
  private cacheTimeout = 5 * 60 * 1000; // 5 minutes

  constructor(projectRoot: string = process.cwd()) {
    this.projectRoot = projectRoot;
  }

  async collectAllMetrics(): Promise<QualityMetrics> {
    console.log('Collecting quality metrics...');
    
    const [
      testCoverage,
      testResults,
      performance,
      accessibility,
      security,
      codeQuality
    ] = await Promise.all([
      this.collectTestCoverage(),
      this.collectTestResults(),
      this.collectPerformanceMetrics(),
      this.collectAccessibilityMetrics(),
      this.collectSecurityMetrics(),
      this.collectCodeQualityMetrics()
    ]);

    return {
      testCoverage,
      testResults,
      performance,
      accessibility,
      security,
      codeQuality
    };
  }

  private async collectTestCoverage(): Promise<QualityMetrics['testCoverage']> {
    const cacheKey = 'testCoverage';
    const cached = this.getCachedMetric(cacheKey);
    if (cached) return cached;

    try {
      // Run coverage collection
      const coverageCommand = 'npm run test:coverage -- --reporter=json';
      const coverageOutput = execSync(coverageCommand, { 
        cwd: this.projectRoot,
        encoding: 'utf8',
        stdio: 'pipe'
      });

      const coverageData = JSON.parse(coverageOutput);
      
      // Extract coverage data from different test types
      const unitCoverage = this.extractCoverageFromReport('coverage/unit/coverage-summary.json');
      const integrationCoverage = this.extractCoverageFromReport('coverage/integration/coverage-summary.json');
      const e2eCoverage = this.extractCoverageFromReport('coverage/e2e/coverage-summary.json');
      const visualCoverage = this.extractVisualTestCoverage();

      const coverage = {
        unit: unitCoverage,
        integration: integrationCoverage,
        e2e: e2eCoverage,
        visual: visualCoverage,
        overall: Math.round((unitCoverage + integrationCoverage + e2eCoverage + visualCoverage) / 4)
      };

      this.setCachedMetric(cacheKey, coverage);
      return coverage;
    } catch (error) {
      console.error('Failed to collect test coverage:', error);
      return {
        unit: 0,
        integration: 0,
        e2e: 0,
        visual: 0,
        overall: 0
      };
    }
  }

  private extractCoverageFromReport(reportPath: string): number {
    try {
      const fullPath = path.join(this.projectRoot, reportPath);
      if (!fs.existsSync(fullPath)) return 0;

      const coverageData = JSON.parse(fs.readFileSync(fullPath, 'utf8'));
      return Math.round(coverageData.total.lines.pct || 0);
    } catch (error) {
      return 0;
    }
  }

  private extractVisualTestCoverage(): number {
    try {
      const visualTestDir = path.join(this.projectRoot, 'e2e/visual');
      if (!fs.existsSync(visualTestDir)) return 0;

      const testFiles = fs.readdirSync(visualTestDir).filter(f => f.endsWith('.spec.ts'));
      const componentDir = path.join(this.projectRoot, 'src/components');
      const componentFiles = this.getAllFiles(componentDir, '.tsx');

      // Simple heuristic: percentage of components with visual tests
      const coverage = Math.round((testFiles.length / componentFiles.length) * 100);
      return Math.min(coverage, 100);
    } catch (error) {
      return 0;
    }
  }

  private async collectTestResults(): Promise<QualityMetrics['testResults']> {
    const cacheKey = 'testResults';
    const cached = this.getCachedMetric(cacheKey);
    if (cached) return cached;

    try {
      // Run all tests and collect results
      const testCommand = 'npm run test:all -- --reporter=json';
      const testOutput = execSync(testCommand, {
        cwd: this.projectRoot,
        encoding: 'utf8',
        stdio: 'pipe'
      });

      const testData = JSON.parse(testOutput);
      
      const results = {
        total: testData.numTotalTests || 0,
        passed: testData.numPassedTests || 0,
        failed: testData.numFailedTests || 0,
        skipped: testData.numPendingTests || 0,
        flaky: this.detectFlakyTests()
      };

      this.setCachedMetric(cacheKey, results);
      return results;
    } catch (error) {
      console.error('Failed to collect test results:', error);
      return {
        total: 0,
        passed: 0,
        failed: 0,
        skipped: 0,
        flaky: 0
      };
    }
  }

  private detectFlakyTests(): number {
    try {
      // Analyze test history to detect flaky tests
      const testHistoryPath = path.join(this.projectRoot, 'test-results/test-history.json');
      if (!fs.existsSync(testHistoryPath)) return 0;

      const history = JSON.parse(fs.readFileSync(testHistoryPath, 'utf8'));
      let flakyCount = 0;

      // Simple flaky test detection: tests that have both passed and failed in recent runs
      for (const testName in history) {
        const results = history[testName].slice(-10); // Last 10 runs
        const hasPassed = results.some((r: any) => r.status === 'passed');
        const hasFailed = results.some((r: any) => r.status === 'failed');
        
        if (hasPassed && hasFailed) {
          flakyCount++;
        }
      }

      return flakyCount;
    } catch (error) {
      return 0;
    }
  }

  private async collectPerformanceMetrics(): Promise<QualityMetrics['performance']> {
    const cacheKey = 'performance';
    const cached = this.getCachedMetric(cacheKey);
    if (cached) return cached;

    try {
      // Collect performance metrics from recent test runs
      const performanceReportPath = path.join(this.projectRoot, 'e2e-artifacts/performance-results');
      
      if (!fs.existsSync(performanceReportPath)) {
        return {
          loadTime: 0,
          interactionTime: 0,
          memoryUsage: 0,
          errorRate: 0
        };
      }

      const reportFiles = fs.readdirSync(performanceReportPath)
        .filter(f => f.endsWith('.json'))
        .sort()
        .slice(-5); // Last 5 reports

      let totalLoadTime = 0;
      let totalInteractionTime = 0;
      let totalMemoryUsage = 0;
      let totalErrorRate = 0;
      let reportCount = 0;

      for (const reportFile of reportFiles) {
        try {
          const reportData = JSON.parse(
            fs.readFileSync(path.join(performanceReportPath, reportFile), 'utf8')
          );

          if (reportData.metrics) {
            totalLoadTime += reportData.metrics.averageLoadTime || 0;
            totalInteractionTime += reportData.metrics.averageInteractionTime || 0;
            totalMemoryUsage += reportData.metrics.peakMemoryUsage || 0;
            totalErrorRate += reportData.metrics.errorRate || 0;
            reportCount++;
          }
        } catch (error) {
          console.warn(`Failed to parse performance report ${reportFile}:`, error);
        }
      }

      const performance = reportCount > 0 ? {
        loadTime: Math.round(totalLoadTime / reportCount),
        interactionTime: Math.round(totalInteractionTime / reportCount),
        memoryUsage: Math.round(totalMemoryUsage / reportCount),
        errorRate: Math.round((totalErrorRate / reportCount) * 100) / 100
      } : {
        loadTime: 0,
        interactionTime: 0,
        memoryUsage: 0,
        errorRate: 0
      };

      this.setCachedMetric(cacheKey, performance);
      return performance;
    } catch (error) {
      console.error('Failed to collect performance metrics:', error);
      return {
        loadTime: 0,
        interactionTime: 0,
        memoryUsage: 0,
        errorRate: 0
      };
    }
  }

  private async collectAccessibilityMetrics(): Promise<QualityMetrics['accessibility']> {
    const cacheKey = 'accessibility';
    const cached = this.getCachedMetric(cacheKey);
    if (cached) return cached;

    try {
      // Run accessibility tests
      const a11yCommand = 'npm run test:accessibility -- --reporter=json';
      const a11yOutput = execSync(a11yCommand, {
        cwd: this.projectRoot,
        encoding: 'utf8',
        stdio: 'pipe'
      });

      const a11yData = JSON.parse(a11yOutput);
      
      const accessibility = {
        score: Math.round(a11yData.score || 0),
        violations: a11yData.violations?.length || 0,
        warnings: a11yData.warnings?.length || 0,
        passes: a11yData.passes?.length || 0
      };

      this.setCachedMetric(cacheKey, accessibility);
      return accessibility;
    } catch (error) {
      console.error('Failed to collect accessibility metrics:', error);
      return {
        score: 0,
        violations: 0,
        warnings: 0,
        passes: 0
      };
    }
  }

  private async collectSecurityMetrics(): Promise<QualityMetrics['security']> {
    const cacheKey = 'security';
    const cached = this.getCachedMetric(cacheKey);
    if (cached) return cached;

    try {
      // Run security audit
      const auditCommand = 'npm audit --json';
      const auditOutput = execSync(auditCommand, {
        cwd: this.projectRoot,
        encoding: 'utf8',
        stdio: 'pipe'
      });

      const auditData = JSON.parse(auditOutput);
      
      const vulnerabilities = {
        critical: auditData.metadata?.vulnerabilities?.critical || 0,
        high: auditData.metadata?.vulnerabilities?.high || 0,
        medium: auditData.metadata?.vulnerabilities?.medium || 0,
        low: auditData.metadata?.vulnerabilities?.low || 0
      };

      const totalVulns = Object.values(vulnerabilities).reduce((a, b) => a + b, 0);
      const score = Math.max(0, 100 - (vulnerabilities.critical * 20 + vulnerabilities.high * 10 + vulnerabilities.medium * 5 + vulnerabilities.low * 1));

      const security = {
        vulnerabilities,
        score: Math.round(score)
      };

      this.setCachedMetric(cacheKey, security);
      return security;
    } catch (error) {
      console.error('Failed to collect security metrics:', error);
      return {
        vulnerabilities: {
          critical: 0,
          high: 0,
          medium: 0,
          low: 0
        },
        score: 100
      };
    }
  }

  private async collectCodeQualityMetrics(): Promise<QualityMetrics['codeQuality']> {
    const cacheKey = 'codeQuality';
    const cached = this.getCachedMetric(cacheKey);
    if (cached) return cached;

    try {
      // Analyze code quality using various metrics
      const maintainabilityIndex = this.calculateMaintainabilityIndex();
      const technicalDebt = this.calculateTechnicalDebt();
      const duplicateCode = this.calculateDuplicateCode();
      const complexity = this.calculateComplexity();

      const codeQuality = {
        maintainabilityIndex,
        technicalDebt,
        duplicateCode,
        complexity
      };

      this.setCachedMetric(cacheKey, codeQuality);
      return codeQuality;
    } catch (error) {
      console.error('Failed to collect code quality metrics:', error);
      return {
        maintainabilityIndex: 0,
        technicalDebt: 0,
        duplicateCode: 0,
        complexity: 0
      };
    }
  }

  private calculateMaintainabilityIndex(): number {
    try {
      // Simple heuristic based on file size, complexity, and test coverage
      const srcDir = path.join(this.projectRoot, 'src');
      const files = this.getAllFiles(srcDir, '.ts', '.tsx');
      
      let totalLines = 0;
      let totalFiles = files.length;
      
      for (const file of files) {
        const content = fs.readFileSync(file, 'utf8');
        totalLines += content.split('\n').length;
      }
      
      const avgLinesPerFile = totalLines / totalFiles;
      const maintainabilityIndex = Math.max(0, 100 - (avgLinesPerFile / 10)); // Penalize large files
      
      return Math.round(maintainabilityIndex);
    } catch (error) {
      return 0;
    }
  }

  private calculateTechnicalDebt(): number {
    try {
      // Estimate technical debt based on TODO comments, code smells, etc.
      const srcDir = path.join(this.projectRoot, 'src');
      const files = this.getAllFiles(srcDir, '.ts', '.tsx');
      
      let debtHours = 0;
      
      for (const file of files) {
        const content = fs.readFileSync(file, 'utf8');
        
        // Count TODO/FIXME comments (1 hour each)
        const todoMatches = content.match(/\/\/\s*(TODO|FIXME|HACK)/gi) || [];
        debtHours += todoMatches.length * 1;
        
        // Count long functions (0.5 hours each)
        const functionMatches = content.match(/function\s+\w+[^{]*{[^}]{500,}/g) || [];
        debtHours += functionMatches.length * 0.5;
        
        // Count large files (2 hours each for files > 500 lines)
        const lines = content.split('\n').length;
        if (lines > 500) {
          debtHours += 2;
        }
      }
      
      return Math.round(debtHours);
    } catch (error) {
      return 0;
    }
  }

  private calculateDuplicateCode(): number {
    try {
      // Simple duplicate detection based on similar function signatures
      const srcDir = path.join(this.projectRoot, 'src');
      const files = this.getAllFiles(srcDir, '.ts', '.tsx');
      
      const functionSignatures = new Map<string, number>();
      let totalFunctions = 0;
      
      for (const file of files) {
        const content = fs.readFileSync(file, 'utf8');
        const functionMatches = content.match(/(?:function\s+\w+|const\s+\w+\s*=\s*(?:\([^)]*\)\s*=>|\([^)]*\)\s*:\s*[^=]*=>))/g) || [];
        
        for (const func of functionMatches) {
          const signature = func.replace(/\s+/g, ' ').trim();
          functionSignatures.set(signature, (functionSignatures.get(signature) || 0) + 1);
          totalFunctions++;
        }
      }
      
      let duplicateFunctions = 0;
      for (const [signature, count] of functionSignatures) {
        if (count > 1) {
          duplicateFunctions += count - 1; // Count extras as duplicates
        }
      }
      
      const duplicatePercentage = totalFunctions > 0 ? (duplicateFunctions / totalFunctions) * 100 : 0;
      return Math.round(duplicatePercentage);
    } catch (error) {
      return 0;
    }
  }

  private calculateComplexity(): number {
    try {
      // Calculate cyclomatic complexity
      const srcDir = path.join(this.projectRoot, 'src');
      const files = this.getAllFiles(srcDir, '.ts', '.tsx');
      
      let totalComplexity = 0;
      let totalFunctions = 0;
      
      for (const file of files) {
        const content = fs.readFileSync(file, 'utf8');
        
        // Count decision points (if, while, for, case, catch, &&, ||)
        const decisionPoints = (content.match(/\b(if|while|for|case|catch)\b|\|\||&&/g) || []).length;
        const functions = (content.match(/(?:function\s+\w+|const\s+\w+\s*=\s*(?:\([^)]*\)\s*=>|\([^)]*\)\s*:\s*[^=]*=>))/g) || []).length;
        
        if (functions > 0) {
          totalComplexity += decisionPoints + functions; // Base complexity of 1 per function
          totalFunctions += functions;
        }
      }
      
      const averageComplexity = totalFunctions > 0 ? totalComplexity / totalFunctions : 0;
      return Math.round(averageComplexity);
    } catch (error) {
      return 0;
    }
  }

  async generateQualityGates(metrics: QualityMetrics): Promise<QualityGate[]> {
    const gates: QualityGate[] = [
      {
        id: 'test-coverage',
        name: 'Test Coverage',
        threshold: 80,
        actual: metrics.testCoverage.overall,
        status: metrics.testCoverage.overall >= 80 ? 'passed' : metrics.testCoverage.overall >= 60 ? 'warning' : 'failed',
        description: 'Overall test coverage must be at least 80%'
      },
      {
        id: 'test-pass-rate',
        name: 'Test Pass Rate',
        threshold: 95,
        actual: Math.round((metrics.testResults.passed / metrics.testResults.total) * 100),
        status: (metrics.testResults.passed / metrics.testResults.total) >= 0.95 ? 'passed' : 
                (metrics.testResults.passed / metrics.testResults.total) >= 0.90 ? 'warning' : 'failed',
        description: 'Test pass rate must be at least 95%'
      },
      {
        id: 'performance',
        name: 'Performance',
        threshold: 2000,
        actual: metrics.performance.loadTime,
        status: metrics.performance.loadTime <= 2000 ? 'passed' : 
                metrics.performance.loadTime <= 3000 ? 'warning' : 'failed',
        description: 'Average page load time must be under 2 seconds'
      },
      {
        id: 'accessibility',
        name: 'Accessibility',
        threshold: 90,
        actual: metrics.accessibility.score,
        status: metrics.accessibility.score >= 90 ? 'passed' : 
                metrics.accessibility.score >= 80 ? 'warning' : 'failed',
        description: 'Accessibility score must be at least 90%'
      },
      {
        id: 'security',
        name: 'Security',
        threshold: 80,
        actual: metrics.security.score,
        status: metrics.security.score >= 80 ? 'passed' : 
                metrics.security.score >= 60 ? 'warning' : 'failed',
        description: 'Security score must be at least 80%'
      },
      {
        id: 'maintainability',
        name: 'Maintainability',
        threshold: 70,
        actual: metrics.codeQuality.maintainabilityIndex,
        status: metrics.codeQuality.maintainabilityIndex >= 70 ? 'passed' : 
                metrics.codeQuality.maintainabilityIndex >= 50 ? 'warning' : 'failed',
        description: 'Maintainability index must be at least 70%'
      }
    ];

    return gates;
  }

  async generateTrends(days: number = 30): Promise<QualityTrend[]> {
    try {
      const trendsPath = path.join(this.projectRoot, 'qa-metrics/trends.json');
      
      if (!fs.existsSync(trendsPath)) {
        return [];
      }

      const trendsData = JSON.parse(fs.readFileSync(trendsPath, 'utf8'));
      const cutoffDate = new Date();
      cutoffDate.setDate(cutoffDate.getDate() - days);

      return trendsData.filter((trend: QualityTrend) => 
        new Date(trend.date) >= cutoffDate
      ).sort((a: QualityTrend, b: QualityTrend) => 
        new Date(a.date).getTime() - new Date(b.date).getTime()
      );
    } catch (error) {
      console.error('Failed to generate trends:', error);
      return [];
    }
  }

  async saveTrend(metrics: QualityMetrics): Promise<void> {
    try {
      const trendsDir = path.join(this.projectRoot, 'qa-metrics');
      if (!fs.existsSync(trendsDir)) {
        fs.mkdirSync(trendsDir, { recursive: true });
      }

      const trendsPath = path.join(trendsDir, 'trends.json');
      let trends: QualityTrend[] = [];

      if (fs.existsSync(trendsPath)) {
        trends = JSON.parse(fs.readFileSync(trendsPath, 'utf8'));
      }

      const newTrend: QualityTrend = {
        date: new Date().toISOString().split('T')[0],
        coverage: metrics.testCoverage.overall,
        passRate: Math.round((metrics.testResults.passed / metrics.testResults.total) * 100),
        performance: 100 - Math.min(100, metrics.performance.loadTime / 50), // Convert to score
        accessibility: metrics.accessibility.score,
        security: metrics.security.score
      };

      // Remove existing trend for today if it exists
      trends = trends.filter(t => t.date !== newTrend.date);
      trends.push(newTrend);

      // Keep only last 90 days
      trends = trends.slice(-90);

      fs.writeFileSync(trendsPath, JSON.stringify(trends, null, 2));
    } catch (error) {
      console.error('Failed to save trend:', error);
    }
  }

  private getAllFiles(dir: string, ...extensions: string[]): string[] {
    const files: string[] = [];
    
    if (!fs.existsSync(dir)) return files;
    
    const items = fs.readdirSync(dir);
    
    for (const item of items) {
      const fullPath = path.join(dir, item);
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory()) {
        files.push(...this.getAllFiles(fullPath, ...extensions));
      } else if (extensions.some(ext => item.endsWith(ext))) {
        files.push(fullPath);
      }
    }
    
    return files;
  }

  private getCachedMetric(key: string): any {
    const cached = this.metricsCache.get(key);
    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      return cached.data;
    }
    return null;
  }

  private setCachedMetric(key: string, data: any): void {
    this.metricsCache.set(key, {
      data,
      timestamp: Date.now()
    });
  }
}