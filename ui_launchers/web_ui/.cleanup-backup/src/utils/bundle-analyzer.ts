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
  size: number;
  files: string[];
  modules: string[];
}

export interface AssetInfo {
  name: string;
  size: number;
  type: 'js' | 'css' | 'image' | 'font' | 'other';
  gzippedSize?: number;
}

export interface ModuleInfo {
  name: string;
  size: number;
  chunks: string[];
  reasons: string[];
}

export interface BundleBudget {
  maxBundleSize: number; // in bytes
  maxChunkSize: number;
  maxAssetSize: number;
  warningThreshold: number; // percentage
  errorThreshold: number; // percentage
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
      if (bundleSizeViolation.severity === 'error') {
        violations.push(bundleSizeViolation);
      } else {
        warnings.push(bundleSizeViolation);
      }
    }

    // Check individual chunks
    stats.chunks.forEach(chunk => {
      const chunkViolation = this.checkChunkSize(chunk);
      if (chunkViolation) {
        if (chunkViolation.severity === 'error') {
          violations.push(chunkViolation);
        } else {
          warnings.push(chunkViolation);
        }
      }
    });

    // Check individual assets
    stats.assets.forEach(asset => {
      const assetViolation = this.checkAssetSize(asset);
      if (assetViolation) {
        if (assetViolation.severity === 'error') {
          violations.push(assetViolation);
        } else {
          warnings.push(assetViolation);
        }
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

    // Analyze large modules
    const largeModules = stats.modules
      .filter(module => module.size > 10 * 1024) // > 10KB
      .sort((a, b) => b.size - a.size)
      .slice(0, 5);

    if (largeModules.length > 0) {
      recommendations.push(
        `Consider code splitting or lazy loading for large modules: ${largeModules
          .map(m => `${m.name} (${this.formatBytes(m.size)})`)
          .join(', ')}`
      );
    }

    // Check for duplicate modules
    const moduleNames = stats.modules.map(m => m.name);
    const duplicates = moduleNames.filter((name, index) => moduleNames.indexOf(name) !== index);
    if (duplicates.length > 0) {
      recommendations.push(
        `Potential duplicate modules detected: ${[...new Set(duplicates)].join(', ')}`
      );
    }

    // Bundle-specific recommendations
    if (violations.some(v => v.type === 'bundle-size')) {
      recommendations.push(
        'Consider implementing route-based code splitting to reduce initial bundle size'
      );
      recommendations.push(
        'Review and remove unused dependencies using tools like webpack-bundle-analyzer'
      );
    }

    // Chunk-specific recommendations
    if (violations.some(v => v.type === 'chunk-size')) {
      recommendations.push(
        'Split large chunks into smaller, more focused chunks'
      );
      recommendations.push(
        'Consider lazy loading heavy components or features'
      );
    }

    return recommendations;
  }

  private calculatePerformanceScore(
    stats: BundleStats,
    violations: BudgetViolation[],
    warnings: BudgetWarning[]
  ): number {
    let score = 100;

    // Deduct points for violations
    violations.forEach(violation => {
      if (violation.severity === 'error') {
        score -= 20;
      }
    });

    warnings.forEach(warning => {
      if (warning.severity === 'warning') {
        score -= 10;
      }
    });

    // Bonus points for good practices
    const hasGoodChunkSplitting = stats.chunks.length > 3 && stats.chunks.length < 10;
    if (hasGoodChunkSplitting) {
      score += 5;
    }

    const hasGoodGzipRatio = stats.gzippedSize / stats.totalSize < 0.3;
    if (hasGoodGzipRatio) {
      score += 5;
    }

    return Math.max(0, Math.min(100, score));
  }

  private formatBytes(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
}

export interface BudgetViolation {
  type: 'bundle-size' | 'chunk-size' | 'asset-size';
  severity: 'error' | 'warning';
  message: string;
  actual: number;
  budget: number;
  percentage: number;
  target?: string;
}

export type BudgetWarning = BudgetViolation;

export interface BundleAnalysisResult {
  stats: BundleStats;
  violations: BudgetViolation[];
  warnings: BudgetWarning[];
  recommendations: string[];
  score: number;
}

// Utility function to create bundle analyzer with specific budgets
export function createBundleAnalyzer(type: keyof typeof BUNDLE_BUDGETS): BundleAnalyzer {
  return new BundleAnalyzer(BUNDLE_BUDGETS[type]);
}

// Export default analyzer
export const bundleAnalyzer = new BundleAnalyzer();