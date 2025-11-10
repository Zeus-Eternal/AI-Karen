"use client";
/**
 * Tree Shaking Utilities & Optimizations (production‑grade)
 *
 * Goals
 * - Codify best‑practice import patterns for common libs
 * - Provide a static analyzer to flag inefficient imports
 * - Offer auto‑fix helpers for straightforward replacements
 * - Supply a bundler‑agnostic optimization preset (Webpack‑lean)
 *
 * Notes
 * - Safe for SSR: no global access on import
 * - No build‑tool hard deps; config object is export‑only
 */

// ---------------------------------------------------------------------------
// Optimized imports catalog (typed, numeric savings for arithmetic)
// ---------------------------------------------------------------------------
export const OPTIMIZED_IMPORTS = {
  lodash: {
    original: "import _ from 'lodash'",
    optimized: "import { debounce, throttle, cloneDeep } from 'lodash-es'",
    savingsKB: 70,
    notes: "Use lodash-es + named imports so ESM tree shaking works."
  },
  "date-fns": {
    original: "import * as dateFns from 'date-fns'",
    optimized: "import { format, parseISO, isValid } from 'date-fns'",
    savingsKB: 60,
    notes: "Import only used functions; avoid star imports."
  },
  "lucide-react": {
    original: "import * as Icons from 'lucide-react'",
    optimized: "import { Search, User, Settings } from 'lucide-react'",
    savingsKB: 200,
    notes: "Import specific icons to avoid bundling the entire icon set."
  },
  "@radix-ui": {
    original: "import * as Radix from '@radix-ui/react'",
    optimized: "import * as Dialog from '@radix-ui/react-dialog'",
    savingsKB: 50,
    notes: "Each Radix primitive is its own package—import only what you use."
  },
  "react-hook-form": {
    original: "import * as RHF from 'react-hook-form'",
    optimized: "import { useForm, Controller } from 'react-hook-form'",
    savingsKB: 20,
    notes: "Prefer named imports from entry point; avoid star."
  },
} as const;

export type OptimizedLib = keyof typeof OPTIMIZED_IMPORTS;

// ---------------------------------------------------------------------------
// Bundler (Webpack‑lean) tree shaking preset (export‑only)
// ---------------------------------------------------------------------------
export const TREE_SHAKING_CONFIG = {
  sideEffects: false,
  optimization: {
    usedExports: true,
    sideEffects: false,
    concatenateModules: true,
    minimize: true,
    moduleIds: "named" as const,
    chunkIds: "named" as const,
  },
  resolve: {
    mainFields: ["es2015", "module", "browser", "main"],
    alias: {
      lodash: "lodash-es",
      "date-fns": "date-fns/esm",
    },
  },
} as const;

// ---------------------------------------------------------------------------
// Analyzer
// ---------------------------------------------------------------------------
export interface TreeShakingIssue {
  type: "inefficient-import" | "unused-import" | "side-effect";
  severity: "error" | "warning" | "info";
  message: string;
  line: number;
  suggestion: string;
}

export interface TreeShakingSuggestion {
  type: "optimize-import" | "remove-unused" | "add-side-effects";
  library: string;
  original: string;
  optimized: string;
  estimatedSavings: string; // e.g. "~70KB"
  priority: "high" | "medium" | "low";
}

export interface TreeShakingReport {
  issues: TreeShakingIssue[];
  suggestions: TreeShakingSuggestion[];
  score: number; // 0..100
  potentialSavings: string; // e.g. "~330KB"
}

// Map issue keys → detection pattern and library key for suggestion lookup
const ISSUE_DEFS: Array<{
  key: string;
  lib: OptimizedLib;
  pattern: RegExp;
  message: string;
  severity: TreeShakingIssue["severity"];
  exampleSuggestion?: string;
}> = [
  {
    key: "lodash-full",
    lib: "lodash",
    pattern: /import\s+_\s+from\s+['"]lodash['"]/,
    message: "Full lodash import detected—bundles the entire library.",
    severity: "error",
    exampleSuggestion: "Use named ESM imports from 'lodash-es'.",
  },
  {
    key: "lodash-namespace",
    lib: "lodash",
    pattern: /import\s+\*\s+as\s+\w+\s+from\s+['"]lodash['"]/,
    message: "Namespace lodash import may hinder tree shaking.",
    severity: "warning",
  },
  {
    key: "date-fns-full",
    lib: "date-fns",
    pattern: /import\s+\*\s+as\s+\w+\s+from\s+['"]date-fns['"]/,
    message: "Full date-fns namespace import detected.",
    severity: "error",
  },
  {
    key: "lucide-full",
    lib: "lucide-react",
    pattern: /import\s+\*\s+as\s+\w+\s+from\s+['"]lucide-react['"]/,
    message: "Full lucide-react namespace import detected (all icons).",
    severity: "error",
  },
  {
    key: "react-hook-form-full",
    lib: "react-hook-form",
    pattern: /import\s+\*\s+as\s+\w+\s+from\s+['"]react-hook-form['"]/,
    message: "Star import of react-hook-form detected.",
    severity: "warning",
  },
];

export class TreeShakingAnalyzer {
  analyzeFile(content: string): TreeShakingReport {
    const issues: TreeShakingIssue[] = [];
    const suggestions: TreeShakingSuggestion[] = [];

    // Detect inefficient imports
    for (const def of ISSUE_DEFS) {
      if (def.pattern.test(content)) {
        issues.push({
          type: "inefficient-import",
          severity: def.severity,
          message: def.message,
          line: this.findPatternLine(content, def.pattern),
          suggestion:
            def.exampleSuggestion || `Prefer optimized import for ${def.lib}.`,
        });

        const opt = OPTIMIZED_IMPORTS[def.lib];
        suggestions.push({
          type: "optimize-import",
          library: def.lib,
          original: opt.original,
          optimized: opt.optimized,
          estimatedSavings: `~${opt.savingsKB}KB`,
          priority: def.severity === "error" ? "high" : "medium",
        });
      }
    }

    // Unused imports
    for (const name of this.findUnusedImports(content)) {
      issues.push({
        type: "unused-import",
        severity: "warning",
        message: `Unused import detected: ${name}`,
        line: this.findImportLine(content, name),
        suggestion: `Remove unused import: ${name}`,
      });
    }

    const score = this.calculateTreeShakingScore(issues);
    const potentialSavings = this.calculatePotentialSavings(suggestions);

    return { issues, suggestions, score, potentialSavings };
  }

  // Quick auto-fixer for simple patterns (idempotent string ops)
  suggestFixes(content: string): { fixed: string; changes: string[] } {
    let fixed = content;
    const changes: string[] = [];

    // lodash default → lodash-es named
    if (/import\s+_\s+from\s+['"]lodash['"]/.test(fixed)) {
      fixed = fixed.replace(
        /import\s+_\s+from\s+['"]lodash['"];?/g,
        OPTIMIZED_IMPORTS["lodash"].optimized + ";"
      );
      changes.push("Replace lodash default import with lodash-es named imports.");
    }

    // date-fns star → named
    if (/import\s+\*\s+as\s+\w+\s+from\s+['"]date-fns['"]/.test(fixed)) {
      fixed = fixed.replace(
        /import\s+\*\s+as\s+\w+\s+from\s+['"]date-fns['"];?/g,
        OPTIMIZED_IMPORTS["date-fns"].optimized + ";"
      );
      changes.push("Replace date-fns star import with named imports.");
    }

    // lucide star → named (generic example uses 3 icons)
    if (/import\s+\*\s+as\s+\w+\s+from\s+['"]lucide-react['"]/.test(fixed)) {
      fixed = fixed.replace(
        /import\s+\*\s+as\s+\w+\s+from\s+['"]lucide-react['"];?/g,
        OPTIMIZED_IMPORTS["lucide-react"].optimized + ";"
      );
      changes.push("Replace lucide-react star import with named icon imports.");
    }

    return { fixed, changes };
  }

  private findUnusedImports(content: string): string[] {
    // Capture default, namespace, and named import atoms
    const importRegex = /import\s+(?:{([^}]+)}|\*\s+as\s+(\w+)|(\w+))\s+from\s+['"][^'"]+['"];?/g;
    const unused: string[] = [];
    let match: RegExpExecArray | null;

    const withoutImports = content.replace(/import[\s\S]*?from\s+['"][^'"]+['"];?/g, "");

    while ((match = importRegex.exec(content)) !== null) {
      const [, named, namespace, deflt] = match;
      if (named) {
        for (const raw of named.split(",")) {
          const id = raw.trim().split(/\s+as\s+/i)[0].trim();
          if (!this.isTokenUsed(withoutImports, id)) unused.push(id);
        }
      } else if (namespace) {
        if (!this.isTokenUsed(withoutImports, namespace)) unused.push(namespace);
      } else if (deflt) {
        if (!this.isTokenUsed(withoutImports, deflt)) unused.push(deflt);
      }
    }

    return unused;
  }

  private isTokenUsed(content: string, token: string): boolean {
    const re = new RegExp(`(^|[^A-Za-z0-9_$])${token}(?![A-Za-z0-9_$])`);
    return re.test(content);
  }

  private findImportLine(content: string, term: string): number {
    const lines = content.split(/\r?\n/);
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes("import") && lines[i].includes(term)) return i + 1;
    }
    return 0;
  }

  private findPatternLine(content: string, pattern: RegExp): number {
    const lines = content.split(/\r?\n/);
    for (let i = 0; i < lines.length; i++) {
      if (pattern.test(lines[i])) return i + 1;
    }
    return 0;
  }

  private calculateTreeShakingScore(issues: TreeShakingIssue[]): number {
    let score = 100;
    for (const it of issues) {
      if (it.type === "inefficient-import") {
        score -= it.severity === "error" ? 20 : 10;
      } else if (it.type === "unused-import") {
        score -= 5;
      }
    }
    return Math.max(0, score);
  }

  private calculatePotentialSavings(suggestions: TreeShakingSuggestion[]): string {
    const totalKB = suggestions.reduce((sum, s) => {
      const m = s.estimatedSavings.match(/(~)?(\d+)KB/);
      return sum + (m ? parseInt(m[2], 10) : 0);
    }, 0);
    return totalKB > 0 ? `~${totalKB}KB` : "0KB";
  }
}

// ---------------------------------------------------------------------------
// Utility helpers
// ---------------------------------------------------------------------------
export const treeShakingUtils = {
  optimizeLodashImports(functions: string[]) {
    return `import { ${functions.join(", ")} } from 'lodash-es';`;
  },
  optimizeDateFnsImports(functions: string[]) {
    return `import { ${functions.join(", ")} } from 'date-fns';`;
  },
  optimizeIconImports(icons: string[]) {
    return `import { ${icons.join(", ")} } from 'lucide-react';`;
  },
  supportsTreeShaking(packageName: string): boolean {
    const list = [
      "lodash-es",
      "date-fns",
      "date-fns/esm",
      "lucide-react",
      "@radix-ui",
      "framer-motion",
      "react-hook-form",
    ];
    return list.some((pkg) => packageName.includes(pkg));
  },
};

export const treeShakingAnalyzer = new TreeShakingAnalyzer();
