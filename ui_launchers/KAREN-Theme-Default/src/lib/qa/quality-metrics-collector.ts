import { execSync } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';

/* -----------------------------
 * Types
 * --------------------------- */
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
    loadTime: number;        // ms
    interactionTime: number; // ms
    memoryUsage: number;     // MB
    errorRate: number;       // 0..1
  };
  accessibility: {
    score: number;     // 0..100
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
    score: number; // 0..100
  };
  codeQuality: {
    maintainabilityIndex: number; // 0..100
    technicalDebt: number;        // hours (heuristic)
    duplicateCode: number;        // %
    complexity: number;           // avg cyclomatic
  };
}

export interface QualityTrend {
  date: string;        // YYYY-MM-DD
  coverage: number;    // %
  passRate: number;    // %
  performance: number; // 0..100
  accessibility: number; // 0..100
  security: number;    // 0..100
}

export interface QualityGate {
  id: string;
  name: string;
  status: 'passed' | 'failed' | 'warning';
  threshold: number;
  actual: number;
  description: string;
  overridden?: boolean;
  overrideStatus?: 'passed' | 'failed' | 'warning';
  overrideNote?: string | null;
  overrideAt?: string | null;
  overrideBy?: string | null;
}

export type CacheEntry<T> = { data: T; timestamp: number };

export interface QualityGateOverrideRecord {
  status: QualityGate['status'];
  note?: string | null;
  overriddenAt: string;
  overriddenBy?: string | null;
}

export interface QualityGateOverrideInput {
  status?: QualityGate['status'];
  note?: string | null;
  overriddenBy?: string | null;
}

export interface MetricsCollectorConfig {
  projectRoot?: string;
  cacheTtlMs?: number;
  commands?: {
    coverage?: string;       // e.g., "npm run test:coverage -- --reporter=json"
    tests?: string;          // e.g., "npm run test:all -- --reporter=json"
    accessibility?: string;  // e.g., "npm run test:accessibility -- --reporter=json"
    audit?: string;          // e.g., "npm audit --json"
  };
  paths?: {
    unitCoverage?: string;         // coverage/unit/coverage-summary.json
    integrationCoverage?: string;  // coverage/integration/coverage-summary.json
    e2eCoverage?: string;          // coverage/e2e/coverage-summary.json
    visualTestsDir?: string;       // e2e/visual
    componentDir?: string;         // src/components
    testHistory?: string;          // test-results/test-history.json
    perfReportsDir?: string;       // e2e-artifacts/performance-results
    trendsDir?: string;            // qa-metrics
    trendsFile?: string;           // qa-metrics/trends.json
    gateOverrides?: string;        // qa-metrics/gate-overrides.json
  };
}

/* -----------------------------
 * Helpers
 * --------------------------- */
function safePathJoin(...parts: string[]) {
  return path.join(...parts);
}

function fileExists(p: string) {
  try { return fs.existsSync(p); } catch { return false; }
}

function readFileUtf8(p: string): string | null {
  try { return fs.readFileSync(p, 'utf8'); } catch { return null; }
}

function tryJson<T = any>(text: string | null): T | null {
  if (!text) return null;
  try { return JSON.parse(text) as T; } catch { return null; }
}

function clamp(n: number, min: number, max: number) {
  return Math.min(max, Math.max(min, n));
}

function percent(n: number) {
  return Math.round(n * 100);
}

function safeDivide(num: number, den: number) {
  if (!den || Number.isNaN(den)) return 0;
  return num / den;
}

function safeExec(cmd: string, cwd: string): { ok: boolean; out: string; err?: string } {
  try {
    const out = execSync(cmd, {
      cwd,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'pipe'],
      timeout: 5 * 60 * 1000, // 5 minutes guard
    });
    return { ok: true, out };
  } catch (e: any) {
    return { ok: false, out: e?.stdout?.toString?.() ?? '', err: e?.stderr?.toString?.() ?? e?.message ?? 'exec error' };
  }
}

/* -----------------------------
 * Collector
 * --------------------------- */
export class QualityMetricsCollector {
  private projectRoot: string;
  private metricsCache = new Map<string, CacheEntry<any>>();
  private cacheTimeout: number;
  private commands: Required<MetricsCollectorConfig['commands']>;
  private paths: Required<MetricsCollectorConfig['paths']>;

  constructor(cfg: MetricsCollectorConfig = {}) {
    this.projectRoot = cfg.projectRoot ?? process.cwd();
    this.cacheTimeout = cfg.cacheTtlMs ?? 5 * 60 * 1000;

    this.commands = {
      coverage: cfg.commands?.coverage ?? 'npm run test:coverage -- --reporter=json',
      tests: cfg.commands?.tests ?? 'npm run test:all -- --reporter=json',
      accessibility: cfg.commands?.accessibility ?? 'npm run test:accessibility -- --reporter=json',
      audit: cfg.commands?.audit ?? 'npm audit --json',
    };

    this.paths = {
      unitCoverage: cfg.paths?.unitCoverage ?? 'coverage/unit/coverage-summary.json',
      integrationCoverage: cfg.paths?.integrationCoverage ?? 'coverage/integration/coverage-summary.json',
      e2eCoverage: cfg.paths?.e2eCoverage ?? 'coverage/e2e/coverage-summary.json',
      visualTestsDir: cfg.paths?.visualTestsDir ?? 'e2e/visual',
      componentDir: cfg.paths?.componentDir ?? 'src/components',
      testHistory: cfg.paths?.testHistory ?? 'test-results/test-history.json',
      perfReportsDir: cfg.paths?.perfReportsDir ?? 'e2e-artifacts/performance-results',
      trendsDir: cfg.paths?.trendsDir ?? 'qa-metrics',
      trendsFile: cfg.paths?.trendsFile ?? 'qa-metrics/trends.json',
      gateOverrides: cfg.paths?.gateOverrides ?? 'qa-metrics/gate-overrides.json',
    };
  }

  /* Public API */
  async collectAllMetrics(): Promise<QualityMetrics> {
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

    return { testCoverage, testResults, performance, accessibility, security, codeQuality };
  }

  async generateQualityGates(metrics: QualityMetrics): Promise<QualityGate[]> {
    const passRate = metrics.testResults.total > 0
      ? Math.round((metrics.testResults.passed / metrics.testResults.total) * 100)
      : 0;

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
        actual: passRate,
        status: passRate >= 95 ? 'passed' : passRate >= 90 ? 'warning' : 'failed',
        description: 'Test pass rate must be at least 95%'
      },
      {
        id: 'performance',
        name: 'Performance',
        threshold: 2000, // ms
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
    const overrides = this.readGateOverrides();

    return gates.map((gate) => {
      const override = overrides[gate.id];
      if (!override) return gate;

      return {
        ...gate,
        overridden: true,
        overrideStatus: override.status,
        overrideNote: override.note ?? null,
        overrideAt: override.overriddenAt,
        overrideBy: override.overriddenBy ?? null,
        status: override.status,
      };
    });
  }

  async generateTrends(days: number = 30): Promise<QualityTrend[]> {
    try {
      const trendsPath = safePathJoin(this.projectRoot, this.paths.trendsFile);
      if (!fileExists(trendsPath)) return [];
      const trendsData = tryJson<QualityTrend[]>(readFileUtf8(trendsPath)) ?? [];
      const cutoffDate = new Date();
      cutoffDate.setDate(cutoffDate.getDate() - days);
      return trendsData
        .filter(t => new Date(t.date) >= cutoffDate)
        .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
    } catch {
      return [];
    }
  }

  async saveTrend(metrics: QualityMetrics): Promise<void> {
    try {
      const trendsDir = safePathJoin(this.projectRoot, this.paths.trendsDir);
      const trendsPath = safePathJoin(this.projectRoot, this.paths.trendsFile);
      if (!fileExists(trendsDir)) {
        fs.mkdirSync(trendsDir, { recursive: true });
      }
      let trends: QualityTrend[] = [];
      if (fileExists(trendsPath)) {
        trends = tryJson<QualityTrend[]>(readFileUtf8(trendsPath)) ?? [];
      }
      const today = new Date().toISOString().split('T')[0];

      const passRate = metrics.testResults.total > 0
        ? Math.round((metrics.testResults.passed / metrics.testResults.total) * 100)
        : 0;

      // Convert performance (lower is better) to score (higher is better)
      const performanceScore = clamp(100 - Math.min(100, metrics.performance.loadTime / 50), 0, 100);

      const newTrend: QualityTrend = {
        date: today,
        coverage: metrics.testCoverage.overall,
        passRate,
        performance: performanceScore,
        accessibility: metrics.accessibility.score,
        security: metrics.security.score
      };

      trends = trends.filter(t => t.date !== today);
      trends.push(newTrend);
      // keep last 90 entries by date
      trends.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
      if (trends.length > 90) {
        trends = trends.slice(-90);
      }
      fs.writeFileSync(trendsPath, JSON.stringify(trends, null, 2));
    } catch {
      // best-effort; ignore
    }
  }

  /* -----------------------------
   * Metric collectors
   * --------------------------- */

  private async collectTestCoverage(): Promise<QualityMetrics['testCoverage']> {
    const cacheKey = 'testCoverage';
    const cached = this.getCachedMetric<QualityMetrics['testCoverage']>(cacheKey);
    if (cached) return cached;

    // Run coverage (best-effort)
    safeExec(this.commands.coverage!, this.projectRoot);

    const unitCoverage = this.extractCoverageFromReport(this.paths.unitCoverage);
    const integrationCoverage = this.extractCoverageFromReport(this.paths.integrationCoverage);
    const e2eCoverage = this.extractCoverageFromReport(this.paths.e2eCoverage);
    const visualCoverage = this.extractVisualTestCoverage();

    const overall = Math.round(
      (unitCoverage + integrationCoverage + e2eCoverage + visualCoverage) / 4
    );

    const coverage = {
      unit: unitCoverage,
      integration: integrationCoverage,
      e2e: e2eCoverage,
      visual: visualCoverage,
      overall: clamp(overall, 0, 100),
    };

    this.setCachedMetric(cacheKey, coverage);
    return coverage;
  }

  private extractCoverageFromReport(reportPath: string): number {
    try {
      const fullPath = safePathJoin(this.projectRoot, reportPath);
      if (!fileExists(fullPath)) return 0;
      const coverageData = tryJson<any>(readFileUtf8(fullPath));
      if (!coverageData?.total?.lines?.pct && !coverageData?.total?.statements?.pct) return 0;
      // Prefer lines; fallback to statements
      const pct =
        Number(coverageData.total.lines?.pct ?? coverageData.total.statements?.pct ?? 0);
      return clamp(Math.round(pct), 0, 100);
    } catch {
      return 0;
    }
  }

  private extractVisualTestCoverage(): number {
    try {
      const visualTestDir = safePathJoin(this.projectRoot, this.paths.visualTestsDir);
      const componentDir = safePathJoin(this.projectRoot, this.paths.componentDir);
      if (!fileExists(visualTestDir) || !fileExists(componentDir)) return 0;

      const testFiles = (fs.readdirSync(visualTestDir) || [])
        .filter(f => f.endsWith('.spec.ts') || f.endsWith('.spec.tsx'));
      const componentFiles = this.getAllFiles(componentDir, '.tsx', '.ts');

      if (componentFiles.length === 0) return 0;
      const coverage = Math.round((testFiles.length / componentFiles.length) * 100);
      return clamp(coverage, 0, 100);
    } catch {
      return 0;
    }
  }

  private async collectTestResults(): Promise<QualityMetrics['testResults']> {
    const cacheKey = 'testResults';
    const cached = this.getCachedMetric<QualityMetrics['testResults']>(cacheKey);
    if (cached) return cached;

    const { ok, out } = safeExec(this.commands.tests!, this.projectRoot);
    const testData = ok ? tryJson<any>(out) : null;

    const total = Number(testData?.numTotalTests ?? 0);
    const passed = Number(testData?.numPassedTests ?? 0);
    const failed = Number(testData?.numFailedTests ?? 0);
    const skipped = Number(testData?.numPendingTests ?? 0);
    const flaky = this.detectFlakyTests();

    const results = { total, passed, failed, skipped, flaky };
    this.setCachedMetric(cacheKey, results);
    return results;
  }

  private detectFlakyTests(): number {
    try {
      const testHistoryPath = safePathJoin(this.projectRoot, this.paths.testHistory);
      if (!fileExists(testHistoryPath)) return 0;
      const history = tryJson<Record<string, Array<{ status: string }>>>(readFileUtf8(testHistoryPath)) ?? {};
      let flakyCount = 0;
      for (const testName of Object.keys(history)) {
        const results = (history[testName] || []).slice(-10);
        const hasPassed = results.some(r => r.status === 'passed');
        const hasFailed = results.some(r => r.status === 'failed');
        if (hasPassed && hasFailed) flakyCount++;
      }
      return flakyCount;
    } catch {
      return 0;
    }
  }

  private async collectPerformanceMetrics(): Promise<QualityMetrics['performance']> {
    const cacheKey = 'performance';
    const cached = this.getCachedMetric<QualityMetrics['performance']>(cacheKey);
    if (cached) return cached;

    try {
      const dir = safePathJoin(this.projectRoot, this.paths.perfReportsDir);
      if (!fileExists(dir)) {
        const perf = { loadTime: 0, interactionTime: 0, memoryUsage: 0, errorRate: 0 };
        this.setCachedMetric(cacheKey, perf);
        return perf;
      }
      const reportFiles = (fs.readdirSync(dir) || [])
        .filter(f => f.endsWith('.json'))
        .sort()
        .slice(-5);

      let totalLoad = 0, totalInter = 0, totalMem = 0, totalErr = 0, n = 0;
      for (const f of reportFiles) {
        const data = tryJson<any>(readFileUtf8(safePathJoin(dir, f)));
        if (data?.metrics) {
          totalLoad += Number(data.metrics.averageLoadTime ?? 0);
          totalInter += Number(data.metrics.averageInteractionTime ?? 0);
          totalMem += Number(data.metrics.peakMemoryUsage ?? 0);
          totalErr += Number(data.metrics.errorRate ?? 0);
          n++;
        }
      }
      const perf = n > 0
        ? {
            loadTime: Math.round(totalLoad / n),
            interactionTime: Math.round(totalInter / n),
            memoryUsage: Math.round(totalMem / n),
            errorRate: Math.round((totalErr / n) * 100) / 100
          }
        : { loadTime: 0, interactionTime: 0, memoryUsage: 0, errorRate: 0 };

      this.setCachedMetric(cacheKey, perf);
      return perf;
    } catch {
      const perf = { loadTime: 0, interactionTime: 0, memoryUsage: 0, errorRate: 0 };
      this.setCachedMetric(cacheKey, perf);
      return perf;
    }
  }

  private async collectAccessibilityMetrics(): Promise<QualityMetrics['accessibility']> {
    const cacheKey = 'accessibility';
    const cached = this.getCachedMetric<QualityMetrics['accessibility']>(cacheKey);
    if (cached) return cached;

    const { ok, out } = safeExec(this.commands.accessibility!, this.projectRoot);
    const a11yData = ok ? tryJson<any>(out) : null;

    const accessibility = {
      score: Math.round(Number(a11yData?.score ?? 0)),
      violations: Number(a11yData?.violations?.length ?? 0),
      warnings: Number(a11yData?.warnings?.length ?? 0),
      passes: Number(a11yData?.passes?.length ?? 0),
    };

    this.setCachedMetric(cacheKey, accessibility);
    return accessibility;
  }

  private async collectSecurityMetrics(): Promise<QualityMetrics['security']> {
    const cacheKey = 'security';
    const cached = this.getCachedMetric<QualityMetrics['security']>(cacheKey);
    if (cached) return cached;

    const { ok, out } = safeExec(this.commands.audit!, this.projectRoot);
    const auditData = ok ? tryJson<any>(out) : null;

    const vulnerabilities = {
      critical: Number(auditData?.metadata?.vulnerabilities?.critical ?? 0),
      high: Number(auditData?.metadata?.vulnerabilities?.high ?? 0),
      medium: Number(auditData?.metadata?.vulnerabilities?.medium ?? 0),
      low: Number(auditData?.metadata?.vulnerabilities?.low ?? 0),
    };

    const score = clamp(
      Math.round(
        100 - (vulnerabilities.critical * 20 +
               vulnerabilities.high * 10 +
               vulnerabilities.medium * 5 +
               vulnerabilities.low * 1)
      ),
      0,
      100
    );

    const security = { vulnerabilities, score };
    this.setCachedMetric(cacheKey, security);
    return security;
  }

  private async collectCodeQualityMetrics(): Promise<QualityMetrics['codeQuality']> {
    const cacheKey = 'codeQuality';
    const cached = this.getCachedMetric<QualityMetrics['codeQuality']>(cacheKey);
    if (cached) return cached;

    const maintainabilityIndex = this.calculateMaintainabilityIndex();
    const technicalDebt = this.calculateTechnicalDebt();
    const duplicateCode = this.calculateDuplicateCode();
    const complexity = this.calculateComplexity();

    const codeQuality = {
      maintainabilityIndex,
      technicalDebt,
      duplicateCode,
      complexity,
    };

    this.setCachedMetric(cacheKey, codeQuality);
    return codeQuality;
  }

  /* -----------------------------
   * Heuristics
   * --------------------------- */

  private calculateMaintainabilityIndex(): number {
    try {
      const srcDir = safePathJoin(this.projectRoot, 'src');
      const files = this.getAllFiles(srcDir, '.ts', '.tsx');
      if (files.length === 0) return 100;

      let totalLines = 0;
      for (const file of files) {
        const content = readFileUtf8(file) ?? '';
        totalLines += content.split('\n').length;
      }
      const avgLinesPerFile = totalLines / files.length;
      const mi = clamp(Math.round(100 - (avgLinesPerFile / 10)), 0, 100);
      return mi;
    } catch {
      return 0;
    }
  }

  private calculateTechnicalDebt(): number {
    try {
      const srcDir = safePathJoin(this.projectRoot, 'src');
      const files = this.getAllFiles(srcDir, '.ts', '.tsx');
      let debtHours = 0;

      for (const file of files) {
        const content = readFileUtf8(file) ?? '';
        const todoMatches = content.match(/\/\/\s*(TODO|FIXME|HACK)/gi) || [];
        debtHours += todoMatches.length * 1;

        const longFunctions = content.match(/function\s+\w+[^{]*{[^}]{500,}/g) || [];
        debtHours += longFunctions.length * 0.5;

        const lines = content.split('\n').length;
        if (lines > 500) debtHours += 2;
      }
      return Math.round(debtHours);
    } catch {
      return 0;
    }
  }

  private calculateDuplicateCode(): number {
    try {
      const srcDir = safePathJoin(this.projectRoot, 'src');
      const files = this.getAllFiles(srcDir, '.ts', '.tsx');
      const sigs = new Map<string, number>();
      let totalFunctions = 0;

      const fnRegex = /(?:function\s+\w+|const\s+\w+\s*=\s*(?:\([^)]*\)\s*=>|\([^)]*\)\s*:\s*[^=]*=>))/g;

      for (const file of files) {
        const content = readFileUtf8(file) ?? '';
        const matches = content.match(fnRegex) || [];
        for (const m of matches) {
          const signature = m.replace(/\s+/g, ' ').trim();
          sigs.set(signature, (sigs.get(signature) ?? 0) + 1);
          totalFunctions++;
        }
      }

      let duplicateFunctions = 0;
      for (const [, count] of sigs) {
        if (count > 1) duplicateFunctions += (count - 1);
      }
      const pct = totalFunctions > 0 ? (duplicateFunctions / totalFunctions) * 100 : 0;
      return Math.round(pct);
    } catch {
      return 0;
    }
  }

  private calculateComplexity(): number {
    try {
      const srcDir = safePathJoin(this.projectRoot, 'src');
      const files = this.getAllFiles(srcDir, '.ts', '.tsx');

      const decisionRegex = /\b(if|while|for|case|catch)\b|\|\||&&/g;
      const fnRegex = /(?:function\s+\w+|const\s+\w+\s*=\s*(?:\([^)]*\)\s*=>|\([^)]*\)\s*:\s*[^=]*=>))/g;

      let totalComplexity = 0;
      let totalFunctions = 0;

      for (const file of files) {
        const content = readFileUtf8(file) ?? '';
        const decisions = (content.match(decisionRegex) || []).length;
        const functions = (content.match(fnRegex) || []).length;
        if (functions > 0) {
          totalComplexity += decisions + functions; // base 1 per function + decisions
          totalFunctions += functions;
        }
      }
      const avg = totalFunctions > 0 ? totalComplexity / totalFunctions : 0;
      return Math.round(avg);
    } catch {
      return 0;
    }
  }

  /* -----------------------------
   * FS + Cache utils
   * --------------------------- */

  private getAllFiles(dir: string, ...extensions: string[]): string[] {
    const out: string[] = [];
    if (!fileExists(dir)) return out;

    const stack: string[] = [dir];
    while (stack.length) {
      const current = stack.pop()!;
      const items = fs.readdirSync(current);
      for (const item of items) {
        const full = safePathJoin(current, item);
        const stat = fs.statSync(full);
        if (stat.isDirectory()) {
          stack.push(full);
        } else if (extensions.some(ext => item.endsWith(ext))) {
          out.push(full);
        }
      }
    }
    return out;
  }

  private getCachedMetric<T>(key: string): T | null {
    const entry = this.metricsCache.get(key) as CacheEntry<T> | undefined;
    if (!entry) return null;
    if (Date.now() - entry.timestamp < this.cacheTimeout) {
      return entry.data;
    }
    this.metricsCache.delete(key);
    return null;
  }

  private setCachedMetric<T>(key: string, data: T): void {
    const entry: CacheEntry<T> = { data, timestamp: Date.now() };
    this.metricsCache.set(key, entry);
  }

  private overridesFilePath(): string {
    return safePathJoin(this.projectRoot, this.paths.gateOverrides);
  }

  private readGateOverrides(): Record<string, QualityGateOverrideRecord> {
    try {
      const file = this.overridesFilePath();
      if (!fileExists(file)) return {};
      const raw = tryJson<Record<string, QualityGateOverrideRecord>>(readFileUtf8(file));
      if (!raw || typeof raw !== 'object') return {};
      return Object.fromEntries(
        Object.entries(raw).filter(([key, value]) => !!key && !!value && typeof value.status === 'string')
      );
    } catch {
      return {};
    }
  }

  private writeGateOverrides(overrides: Record<string, QualityGateOverrideRecord>): void {
    try {
      const file = this.overridesFilePath();
      const dir = path.dirname(file);
      if (!fileExists(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      fs.writeFileSync(file, JSON.stringify(overrides, null, 2), 'utf8');
    } catch {
      // ignore write failures to avoid crashing route
    }
  }

  async overrideGate(id: string, override: QualityGateOverrideInput = {}): Promise<QualityGateOverrideRecord> {
    if (!id) {
      throw new Error('Gate id is required to override quality gates.');
    }

    const overrides = this.readGateOverrides();
    const record: QualityGateOverrideRecord = {
      status: override.status ?? 'passed',
      note: override.note ?? null,
      overriddenAt: new Date().toISOString(),
      overriddenBy: override.overriddenBy ?? null,
    };

    overrides[id] = record;
    this.writeGateOverrides(overrides);
    return record;
  }

  async clearGateOverride(id: string): Promise<void> {
    if (!id) return;
    const overrides = this.readGateOverrides();
    if (overrides[id]) {
      delete overrides[id];
      this.writeGateOverrides(overrides);
    }
  }

  async getGateOverrides(): Promise<Record<string, QualityGateOverrideRecord>> {
    return this.readGateOverrides();
  }
}

/* -----------------------------
 * Convenience: one-shot collector
 * --------------------------- */

export async function collectAll(projectRoot: string = process.cwd()) {
  const collector = new QualityMetricsCollector({ projectRoot });
  const metrics = await collector.collectAllMetrics();
  const gates = await collector.generateQualityGates(metrics);
  await collector.saveTrend(metrics);
  return { metrics, gates };
}
