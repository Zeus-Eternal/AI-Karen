/**
 * Bundle analysis utilities for monitoring and optimizing bundle sizes
 */

export interface BundleStats {
  totalSize: number;
  gzippedSize: number;
  chunks: ChunkInfo[];
  assets: AssetInfo[];
  modules: ModuleInfo[];
}

export interface ChunkInfo {
  name: string;
  size: number;         // bytes
  files: string[];
  modules: string[];
}

export interface AssetInfo {
  name: string;
  size: number;         // bytes
  type: 'js' | 'css' | 'image' | 'font' | 'other';
  gzippedSize?: number; // bytes
}

export interface ModuleInfo {
  name: string;
  size: number;         // bytes
  chunks: string[];
  reasons: string[];
}

export interface BundleBudget {
  maxBundleSize: number;     // bytes
  maxChunkSize: number;      // bytes
  maxAssetSize: number;      // bytes
  warningThreshold: number;  // %
  errorThreshold: number;    // %
}

// Default bundle budgets based on performance best practices
export const DEFAULT_BUNDLE_BUDGETS: BundleBudget = {
  maxBundleSize: 250 * 1024, // 250KB
  maxChunkSize: 100 * 1024,  // 100KB
  maxAssetSize: 50 * 1024,   // 50KB
  warningThreshold: 80,      // 80%
  errorThreshold: 100,       // 100%
};

// Performance budgets for different types of applications
export const BUNDLE_BUDGETS = {
  mobile: {
    maxBundleSize: 150 * 1024, // 150KB for mobile
    maxChunkSize: 75 * 1024,
    maxAssetSize: 30 * 1024,
    warningThreshold: 75,
    errorThreshold: 90,
  },
  desktop: {
    maxBundleSize: 300 * 1024, // 300KB for desktop
    maxChunkSize: 150 * 1024,
    maxAssetSize: 75 * 1024,
    warningThreshold: 80,
    errorThreshold: 100,
  },
  enterprise: {
    maxBundleSize: 500 * 1024, // 500KB for enterprise apps
    maxChunkSize: 200 * 1024,
    maxAssetSize: 100 * 1024,
    warningThreshold: 85,
    errorThreshold: 110,
  },
} as const;

export type BudgetViolationType = 'bundle-size' | 'chunk-size' | 'asset-size';
export type BudgetSeverity = 'error' | 'warning';

export interface BudgetViolation {
  type: BudgetViolationType;
  severity: BudgetSeverity;
  message: string;
  actual: number;      // bytes
  budget: number;      // bytes
  percentage: number;  // %
  target?: string;     // chunk/asset name when applicable
}

export type BudgetWarning = BudgetViolation;

export interface BundleAnalysisResult {
  stats: BundleStats;
  violations: BudgetViolation[];
  warnings: BudgetWarning[];
  recommendations: string[];
  score: number; // 0..100
}

/** Utility: clamp to [0,100] */
const clampScore = (n: number) => Math.max(0, Math.min(100, n));

/** Utility: fast duplicate detection (O(n)) */
function findDuplicates(values: string[]): string[] {
  const seen = new Set<string>();
  const dups = new Set<string>();
  for (const v of values) (seen.has(v) ? dups.add(v) : seen.add(v));
  return [...dups];
}

export class BundleAnalyzer {
  private budgets: BundleBudget;

  constructor(budgets: BundleBudget = DEFAULT_BUNDLE_BUDGETS) {
    this.budgets = budgets;
  }

  /**
   * Analyze bundle stats and check against budgets
   */
  analyzeBundleStats(stats: BundleStats): BundleAnalysisResult {
    const violations: BudgetViolation[] = [];
    const warnings: BudgetWarning[] = [];

    // Check total bundle size
    const bundleSizeViolation = this.checkBundleSize(stats.totalSize);
    if (bundleSizeViolation) {
      (bundleSizeViolation.severity === 'error' ? violations : warnings).push(bundleSizeViolation);
    }

    // Check individual chunks
    stats.chunks.forEach((chunk) => {
      const chunkViolation = this.checkChunkSize(chunk);
      if (chunkViolation) {
        (chunkViolation.severity === 'error' ? violations : warnings).push(chunkViolation);
      }
    });

    // Check individual assets
    stats.assets.forEach((asset) => {
      const assetViolation = this.checkAssetSize(asset);
      if (assetViolation) {
        (assetViolation.severity === 'error' ? violations : warnings).push(assetViolation);
      }
    });

    return {
      stats,
      violations,
      warnings,
      recommendations: this.generateRecommendations(stats, violations, warnings),
      score: this.calculatePerformanceScore(stats, violations, warnings),
    };
  }

  private checkBundleSize(size: number): BudgetViolation | null {
    const percentage = (size / this.budgets.maxBundleSize) * 100;

    if (percentage >= this.budgets.errorThreshold) {
      return {
        type: 'bundle-size',
        severity: 'error',
        message: `Bundle size (${this.formatBytes(size)}) exceeds maximum allowed size (${this.formatBytes(this.budgets.maxBundleSize)})`,
        actual: size,
        budget: this.budgets.maxBundleSize,
        percentage,
      };
    }

    if (percentage >= this.budgets.warningThreshold) {
      return {
        type: 'bundle-size',
        severity: 'warning',
        message: `Bundle size (${this.formatBytes(size)}) is approaching maximum allowed size (${this.formatBytes(this.budgets.maxBundleSize)})`,
        actual: size,
        budget: this.budgets.maxBundleSize,
        percentage,
      };
    }

    return null;
  }

  private checkChunkSize(chunk: ChunkInfo): BudgetViolation | null {
    const percentage = (chunk.size / this.budgets.maxChunkSize) * 100;

    if (percentage >= this.budgets.errorThreshold) {
      return {
        type: 'chunk-size',
        severity: 'error',
        message: `Chunk "${chunk.name}" (${this.formatBytes(chunk.size)}) exceeds maximum allowed size (${this.formatBytes(this.budgets.maxChunkSize)})`,
        actual: chunk.size,
        budget: this.budgets.maxChunkSize,
        percentage,
        target: chunk.name,
      };
    }

    if (percentage >= this.budgets.warningThreshold) {
      return {
        type: 'chunk-size',
        severity: 'warning',
        message: `Chunk "${chunk.name}" (${this.formatBytes(chunk.size)}) is approaching maximum allowed size (${this.formatBytes(this.budgets.maxChunkSize)})`,
        actual: chunk.size,
        budget: this.budgets.maxChunkSize,
        percentage,
        target: chunk.name,
      };
    }

    return null;
  }

  private checkAssetSize(asset: AssetInfo): BudgetViolation | null {
    const percentage = (asset.size / this.budgets.maxAssetSize) * 100;

    if (percentage >= this.budgets.errorThreshold) {
      return {
        type: 'asset-size',
        severity: 'error',
        message: `Asset "${asset.name}" (${this.formatBytes(asset.size)}) exceeds maximum allowed size (${this.formatBytes(this.budgets.maxAssetSize)})`,
        actual: asset.size,
        budget: this.budgets.maxAssetSize,
        percentage,
        target: asset.name,
      };
    }

    if (percentage >= this.budgets.warningThreshold) {
      return {
        type: 'asset-size',
        severity: 'warning',
        message: `Asset "${asset.name}" (${this.formatBytes(asset.size)}) is approaching maximum allowed size (${this.formatBytes(this.budgets.maxAssetSize)})`,
        actual: asset.size,
        budget: this.budgets.maxAssetSize,
        percentage,
        target: asset.name,
      };
    }

    return null;
  }

  private generateRecommendations(
    stats: BundleStats,
    violations: BudgetViolation[],
    warnings: BudgetWarning[]
  ): string[] {
    const recommendations: string[] = [];

    // Large modules (top 5 > 10KB)
    const largeModules = [...stats.modules]
      .filter((m) => (m?.size ?? 0) > 10 * 1024)
      .sort((a, b) => b.size - a.size)
      .slice(0, 5);

    if (largeModules.length > 0) {
      recommendations.push(
        `Consider code-splitting or lazy-loading for large modules: ${largeModules
          .map((m) => `${m.name} (${this.formatBytes(m.size)})`)
          .join(', ')}`
      );
    }

    // Duplicate modules (exact name matches)
    const duplicates = findDuplicates(stats.modules.map((m) => m.name));
    if (duplicates.length > 0) {
      recommendations.push(
        `Potential duplicate modules detected: ${duplicates.join(', ')}`
      );
      recommendations.push(
        'Deduplicate via aliasing/resolution, ensure a single version in lockfile, and prefer ESM builds'
      );
    }

    // Gzip ratio insight
    if (stats.totalSize > 0) {
      const ratio = stats.gzippedSize / stats.totalSize;
      if (ratio > 0.35) {
        recommendations.push(
          `High gzip ratio (${Math.round(ratio * 100)}%). Verify minification/treeshaking; consider Brotli for static hosting`
        );
      }
    }

    // Bundle-level flags
    if (violations.some((v) => v.type === 'bundle-size')) {
      recommendations.push(
        'Adopt route-based code splitting to reduce initial payload'
      );
      recommendations.push(
        'Audit and remove unused dependencies (e.g., webpack-bundle-analyzer / rollup-plugin-visualizer)'
      );
      recommendations.push(
        'Prefer modular imports (e.g., lodash-es, date-fns) and ESM builds over CJS'
      );
    }

    // Chunk-level flags
    if (violations.some((v) => v.type === 'chunk-size')) {
      recommendations.push('Split large chunks into feature-focused chunks');
      recommendations.push('Lazy load heavy components/assets below the fold');
    }

    // Asset-level flags
    if (violations.some((v) => v.type === 'asset-size')) {
      recommendations.push(
        'Optimize large assets: compress images (WebP/AVIF), subset fonts, and remove unused CSS'
      );
    }

    return [...new Set(recommendations)]; // de-dup lines if any overlap
  }

  private calculatePerformanceScore(
    stats: BundleStats,
    violations: BudgetViolation[],
    warnings: BudgetWarning[]
  ): number {
    let score = 100;

    // Violations (errors)
    for (const v of violations) {
      if (v.severity === 'error') {
        // heavier penalty for bundle-size vs asset/chunk
        score -= v.type === 'bundle-size' ? 25 : 18;
      }
    }

    // Warnings
    for (const w of warnings) {
      if (w.severity === 'warning') {
        score -= w.type === 'bundle-size' ? 12 : 8;
      }
    }

    // Positive heuristics
    const chunkCount = stats.chunks.length;
    const hasGoodChunkSplitting = chunkCount >= 4 && chunkCount <= 12;
    if (hasGoodChunkSplitting) score += 5;

    // Good gzip ratio bonus
    if (stats.totalSize > 0) {
      const ratio = stats.gzippedSize / stats.totalSize;
      if (ratio < 0.30) score += 5;
    }

    return clampScore(score);
  }

  private formatBytes(bytes: number): string {
    if (!Number.isFinite(bytes) || bytes <= 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.min(sizes.length - 1, Math.floor(Math.log(bytes) / Math.log(k)));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  }
}

/** Factory for a preset analyzer */
export function createBundleAnalyzer(type: keyof typeof BUNDLE_BUDGETS): BundleAnalyzer {
  return new BundleAnalyzer(BUNDLE_BUDGETS[type]);
}

/** Default analyzer export */
export const bundleAnalyzer = new BundleAnalyzer();

/** Optional: compact summary for dashboards */
export function summarizeBundle(result: BundleAnalysisResult) {
  const errors = result.violations.length;
  const warns = result.warnings.length;
  const gzipRatio =
    result.stats.totalSize > 0
      ? +(result.stats.gzippedSize / result.stats.totalSize).toFixed(2)
      : 0;

  return {
    score: result.score,
    errors,
    warnings: warns,
    totalSize: result.stats.totalSize,
    gzippedSize: result.stats.gzippedSize,
    gzipRatio,
    biggestChunks: [...result.stats.chunks]
      .sort((a, b) => b.size - a.size)
      .slice(0, 3)
      .map((c) => ({ name: c.name, size: c.size })),
    biggestAssets: [...result.stats.assets]
      .sort((a, b) => b.size - a.size)
      .slice(0, 3)
      .map((a) => ({ name: a.name, size: a.size })),
  };
}
