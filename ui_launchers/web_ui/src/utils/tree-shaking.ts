/**
 * Tree shaking utilities and optimizations
 */

// Optimized imports for common libraries
export const OPTIMIZED_IMPORTS = {
  // Lodash - use individual functions instead of full library
  lodash: {
    original: "import _ from 'lodash'",
import {     optimized: "import { debounce, throttle, cloneDeep } from 'lodash-es'",
    savings: "~70KB",
  },
  
  // Date-fns - use individual functions
  'date-fns': {
    original: "import * as dateFns from 'date-fns'",
import {     optimized: "import { format, parseISO, isValid } from 'date-fns'",
    savings: "~60KB",
  },
  
  // Lucide React - use individual icons
  'lucide-react': {
    original: "import * as Icons from 'lucide-react'",
import {     optimized: "import { Search, User, Settings } from 'lucide-react'",
    savings: "~200KB",
  },
  
  // Radix UI - already optimized with individual packages
  '@radix-ui': {
    original: "import * as RadixUI from '@radix-ui/react'",
    optimized: "import * as Dialog from '@radix-ui/react-dialog'",
    savings: "~50KB per unused component",
  },
  
  // React Hook Form - use specific imports
  'react-hook-form': {
    original: "import * as RHF from 'react-hook-form'",
import {     optimized: "import { useForm, Controller } from 'react-hook-form'",
    savings: "~20KB",
  },
} as const;

// Tree shaking configuration for webpack
export const TREE_SHAKING_CONFIG = {
  // Mark packages as side-effect free
  sideEffects: false,
  
  // Optimization settings
  optimization: {
    usedExports: true,
    sideEffects: false,
    
    // Module concatenation for better tree shaking
    concatenateModules: true,
    
    // Dead code elimination
    minimize: true,
    
    // Preserve module names for better debugging
    moduleIds: 'named',
    chunkIds: 'named',
  },
  
  // Resolve configuration for better tree shaking
  resolve: {
    // Prefer ES modules over CommonJS
    mainFields: ['es2015', 'module', 'main'],
    
    // Alias for optimized versions
    alias: {
      'lodash': 'lodash-es',
      'date-fns': 'date-fns/esm',
    },
  },
};

// Utility to analyze import statements and suggest optimizations
export class TreeShakingAnalyzer {
  private importPatterns = new Map<string, RegExp>([
    ['lodash-full', /import\s+_\s+from\s+['"]lodash['"]/],
    ['lodash-namespace', /import\s+\*\s+as\s+\w+\s+from\s+['"]lodash['"]/],
    ['date-fns-full', /import\s+\*\s+as\s+\w+\s+from\s+['"]date-fns['"]/],
    ['lucide-full', /import\s+\*\s+as\s+\w+\s+from\s+['"]lucide-react['"]/],
    ['react-hook-form-full', /import\s+\*\s+as\s+\w+\s+from\s+['"]react-hook-form['"]/],
  ]);

  analyzeFile(content: string): TreeShakingReport {
    const issues: TreeShakingIssue[] = [];
    const suggestions: TreeShakingSuggestion[] = [];

    // Check for problematic import patterns
    for (const [issueType, pattern] of this.importPatterns) {
      if (pattern.test(content)) {
        const issue = this.createIssue(issueType, content);
        if (issue) {
          issues.push(issue);
          
          const suggestion = this.createSuggestion(issueType);
          if (suggestion) {
            suggestions.push(suggestion);
          }
        }
      }
    }

    // Check for unused imports
    const unusedImports = this.findUnusedImports(content);
    unusedImports.forEach(importName => {
      issues.push({
        type: 'unused-import',
        severity: 'warning',
        message: `Unused import detected: ${importName}`,
        line: this.findImportLine(content, importName),
        suggestion: `Remove unused import: ${importName}`,


    return {
      issues,
      suggestions,
      score: this.calculateTreeShakingScore(issues),
      potentialSavings: this.calculatePotentialSavings(suggestions),
    };
  }

  private createIssue(issueType: string, content: string): TreeShakingIssue | null {
    const issueMap: Record<string, Omit<TreeShakingIssue, 'line'>> = {
      'lodash-full': {
        type: 'inefficient-import',
        severity: 'error',
        message: 'Full lodash import detected - this includes the entire library (~70KB)',
import {         suggestion: 'Use individual function imports: import { debounce } from "lodash-es"',
      },
      'lodash-namespace': {
        type: 'inefficient-import',
        severity: 'warning',
        message: 'Namespace lodash import detected - may include unused functions',
        suggestion: 'Use individual function imports for better tree shaking',
      },
      'date-fns-full': {
        type: 'inefficient-import',
        severity: 'error',
        message: 'Full date-fns import detected - this includes the entire library (~60KB)',
import {         suggestion: 'Use individual function imports: import { format } from "date-fns"',
      },
      'lucide-full': {
        type: 'inefficient-import',
        severity: 'error',
        message: 'Full lucide-react import detected - this includes all icons (~200KB)',
import {         suggestion: 'Use individual icon imports: import { Search } from "lucide-react"',
      },
      'react-hook-form-full': {
        type: 'inefficient-import',
        severity: 'warning',
        message: 'Full react-hook-form import detected',
import {         suggestion: 'Use individual imports: import { useForm } from "react-hook-form"',
      },
    };

    const issue = issueMap[issueType];
    if (!issue) return null;

    return {
      ...issue,
      line: this.findImportLine(content, issueType),
    };
  }

  private createSuggestion(issueType: string): TreeShakingSuggestion | null {
    const optimizedImport = OPTIMIZED_IMPORTS[issueType as keyof typeof OPTIMIZED_IMPORTS];
    if (!optimizedImport) return null;

    return {
      type: 'optimize-import',
      library: issueType,
      original: optimizedImport.original,
      optimized: optimizedImport.optimized,
      estimatedSavings: optimizedImport.savings,
      priority: 'high',
    };
  }

  private findUnusedImports(content: string): string[] {
    const importRegex = /import\s+(?:{([^}]+)}|\*\s+as\s+(\w+)|(\w+))\s+from\s+['"]([^'"]+)['"]/g;
    const unusedImports: string[] = [];
    let match;

    while ((match = importRegex.exec(content)) !== null) {
      const [, namedImports, namespaceImport, defaultImport] = match;
      
      if (namedImports) {
        // Check named imports
        const imports = namedImports.split(',').map(imp => imp.trim());
        imports.forEach(imp => { 
          const importName = imp.split(' as ')[0].trim(); 
          if (!this.isImportUsed(content, importName)) { 
            unusedImports.push(importName); 
          } 
        });

      } else if (namespaceImport) {
        // Check namespace import
        if (!this.isImportUsed(content, namespaceImport)) {
          unusedImports.push(namespaceImport);
        }
      } else if (defaultImport) {
        // Check default import
        if (!this.isImportUsed(content, defaultImport)) {
          unusedImports.push(defaultImport);
        }
      }
    }

    return unusedImports;
  }

  private isImportUsed(content: string, importName: string): boolean {
    // Remove import statements to avoid false positives
    const contentWithoutImports = content.replace(/import\s+.*?from\s+['"][^'"]+['"];?\s*/g, '');
    
    // Check if import is used in the code
    const usageRegex = new RegExp(`\\b${importName}\\b`, 'g');
    return usageRegex.test(contentWithoutImports);
  }

  private findImportLine(content: string, searchTerm: string): number {
    const lines = content.split('\n');
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes('import') && lines[i].includes(searchTerm)) {
        return i + 1;
      }
    }
    return 0;
  }

  private calculateTreeShakingScore(issues: TreeShakingIssue[]): number {
    let score = 100;
    
    issues.forEach(issue => {
      if (issue.severity === 'error') {
        score -= 20;
      } else if (issue.severity === 'warning') {
        score -= 10;
      }

    return Math.max(0, score);
  }

  private calculatePotentialSavings(suggestions: TreeShakingSuggestion[]): string {
    let totalSavings = 0;
    
    suggestions.forEach(suggestion => {
      const savingsMatch = suggestion.estimatedSavings.match(/(\d+)KB/);
      if (savingsMatch) {
        totalSavings += parseInt(savingsMatch[1]);
      }

    return totalSavings > 0 ? `~${totalSavings}KB` : '0KB';
  }
}

export interface TreeShakingIssue {
  type: 'inefficient-import' | 'unused-import' | 'side-effect';
  severity: 'error' | 'warning' | 'info';
  message: string;
  line: number;
  suggestion: string;
}

export interface TreeShakingSuggestion {
  type: 'optimize-import' | 'remove-unused' | 'add-side-effects';
  library: string;
  original: string;
  optimized: string;
  estimatedSavings: string;
  priority: 'high' | 'medium' | 'low';
}

export interface TreeShakingReport {
  issues: TreeShakingIssue[];
  suggestions: TreeShakingSuggestion[];
  score: number;
  potentialSavings: string;
}

// Utility functions for common optimizations
export const treeShakingUtils = {
  // Generate optimized lodash imports
  optimizeLodashImports: (functions: string[]) => {
    return `import { ${functions.join(', ')} } from 'lodash-es';`;
  },

  // Generate optimized date-fns imports
  optimizeDateFnsImports: (functions: string[]) => {
    return `import { ${functions.join(', ')} } from 'date-fns';`;
  },

  // Generate optimized icon imports
  optimizeIconImports: (icons: string[]) => {
    return `import { ${icons.join(', ')} } from 'lucide-react';`;
  },

  // Check if a package supports tree shaking
  supportsTreeShaking: (packageName: string): boolean => {
    const treeShakablePackages = [
      'lodash-es',
      'date-fns',
      'lucide-react',
      '@radix-ui',
      'framer-motion',
      'react-hook-form',
    ];
    
    return treeShakablePackages.some(pkg => packageName.includes(pkg));
  },
};

export const treeShakingAnalyzer = new TreeShakingAnalyzer();