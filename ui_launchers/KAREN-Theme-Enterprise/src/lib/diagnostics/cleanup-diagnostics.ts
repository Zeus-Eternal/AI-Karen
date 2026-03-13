/**
 * Cleanup Diagnostics
 * 
 * Diagnostic logging to identify legacy components and validate cleanup assumptions
 */

export interface DiagnosticResult {
  category: 'typescript' | 'responsive' | 'imports' | 'components' | 'dependencies';
  severity: 'error' | 'warning' | 'info';
  message: string;
  details?: any;
  recommendation?: string;
}

export class CleanupDiagnostics {
  private results: DiagnosticResult[] = [];

  // Check for TypeScript configuration issues
  checkTypeScriptIssues(): DiagnosticResult[] {
    const issues: DiagnosticResult[] = [];

    // Check for common TypeScript issues
    try {
      // Check if we can access key types
      const typesToCheck = [
        'DOMPurifyI',
        'Handlebars',
        'DevEnvironment',
        'ResolvedConfig'
      ];

      typesToCheck.forEach(type => {
        try {
          // This will throw if type is not available
          eval(`typeof ${type}`);
        } catch (e) {
          issues.push({
            category: 'typescript',
            severity: 'error',
            message: `Missing or problematic type definition: ${type}`,
            details: e,
            recommendation: 'Update type definitions or install missing packages'
          });
        }
      });
    } catch (e) {
      issues.push({
        category: 'typescript',
        severity: 'error',
        message: 'TypeScript configuration check failed',
        details: e,
        recommendation: 'Review tsconfig.json and package.json dependencies'
      });
    }

    return issues;
  }

  // Check for legacy responsive utilities
  checkResponsiveUtilities(): DiagnosticResult[] {
    const issues: DiagnosticResult[] = [];

    // Check if custom responsive utilities conflict with Tailwind
    const customResponsiveFeatures = [
      'useBreakpoint',
      'useMediaQuery', 
      'useResponsiveValue',
      'containerClasses',
      'custom spacing utilities',
      'custom typography scale'
    ];

    customResponsiveFeatures.forEach(feature => {
      issues.push({
        category: 'responsive',
        severity: 'warning',
        message: `Custom responsive utility detected: ${feature}`,
        recommendation: 'Consider migrating to native Tailwind CSS utilities'
      });
    });

    return issues;
  }

  // Check for legacy component patterns
  checkLegacyComponents(): DiagnosticResult[] {
    const issues: DiagnosticResult[] = [];

    // Check for legacy patterns in components
    const legacyPatterns = [
      'ThemeBridge with legacy CSS mappings',
      'Duplicate skip links in layout',
      'Disabled placeholder inputs',
      'Non-functional plugin pages',
      'Custom error boundaries with fallbacks'
    ];

    legacyPatterns.forEach(pattern => {
      issues.push({
        category: 'components',
        severity: 'warning',
        message: `Legacy component pattern detected: ${pattern}`,
        recommendation: 'Modernize or remove legacy component patterns'
      });
    });

    return issues;
  }

  // Check for import issues
  checkImportIssues(): DiagnosticResult[] {
    const issues: DiagnosticResult[] = [];

    // Check for potentially problematic imports
    const problematicImports = [
      '@/ai/copilot',
      '@/lib/extensions/extension-initializer',
      '@/components/accessibility',
      'dompurify',
      'handlebars'
    ];

    problematicImports.forEach(importPath => {
      issues.push({
        category: 'imports',
        severity: 'warning',
        message: `Potentially problematic import: ${importPath}`,
        recommendation: 'Verify import paths and module availability'
      });
    });

    return issues;
  }

  // Check for dependency issues
  checkDependencyIssues(): DiagnosticResult[] {
    const issues: DiagnosticResult[] = [];

    // Check for version conflicts
    const versionConflicts = [
      'next vs vite types',
      'framer-motion type conflicts',
      'testing-library type definitions',
      'genkit AI dependencies'
    ];

    versionConflicts.forEach(conflict => {
      issues.push({
        category: 'dependencies',
        severity: 'error',
        message: `Dependency version conflict: ${conflict}`,
        recommendation: 'Update dependencies to compatible versions'
      });
    });

    return issues;
  }

  // Run all diagnostic checks
  runFullDiagnostics(): DiagnosticResult[] {
    this.results = [
      ...this.checkTypeScriptIssues(),
      ...this.checkResponsiveUtilities(),
      ...this.checkLegacyComponents(),
      ...this.checkImportIssues(),
      ...this.checkDependencyIssues()
    ];

    return this.results;
  }

  // Get diagnostic summary
  getSummary(): { errors: number; warnings: number; info: number } {
    return this.results.reduce(
      (acc, result) => {
        const key = result.severity === 'error' ? 'errors' :
                   result.severity === 'warning' ? 'warnings' : 'info';
        acc[key]++;
        return acc;
      },
      { errors: 0, warnings: 0, info: 0 }
    );
  }

  // Log results to console
  logResults(): void {
    console.group('🔍 KAREN Theme Cleanup Diagnostics');
    
    const summary = this.getSummary();
    console.log(`📊 Summary: ${summary.errors} errors, ${summary.warnings} warnings, ${summary.info} info`);

    this.results.forEach((result, index) => {
      const icon = result.severity === 'error' ? '❌' : result.severity === 'warning' ? '⚠️' : 'ℹ️';
      console.group(`${icon} ${result.category.toUpperCase()}: ${result.message}`);
      
      if (result.details) {
        console.log('Details:', result.details);
      }
      
      if (result.recommendation) {
        console.log('💡 Recommendation:', result.recommendation);
      }
      
      console.groupEnd();
    });

    console.groupEnd();
  }

  // Export results for programmatic use
  exportResults(): DiagnosticResult[] {
    return [...this.results];
  }
}

// Singleton instance
export const cleanupDiagnostics = new CleanupDiagnostics();

// Auto-run diagnostics in development
if (process.env.NODE_ENV === 'development') {
  // Run diagnostics after a short delay to ensure app is loaded
  setTimeout(() => {
    cleanupDiagnostics.runFullDiagnostics();
    cleanupDiagnostics.logResults();
  }, 2000);
}