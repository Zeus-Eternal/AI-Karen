#!/usr/bin/env node

/**
 * Tree shaking analysis script
 */

const fs = require('fs');
const path = require('path');
const { glob } = require('glob');

// Colors for console output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
};

function colorize(text, color) {
  return `${colors[color]}${text}${colors.reset}`;
}

// Problematic import patterns
const PROBLEMATIC_PATTERNS = [
  {
    name: 'Full Lodash Import',
    pattern: /import\s+_\s+from\s+['"]lodash['"]/g,
    severity: 'error',
    message: 'Full lodash import detected (~70KB)',
    suggestion: 'Use: import { debounce } from "lodash-es"',
  },
  {
    name: 'Lodash Namespace Import',
    pattern: /import\s+\*\s+as\s+\w+\s+from\s+['"]lodash['"]/g,
    severity: 'warning',
    message: 'Namespace lodash import may include unused functions',
    suggestion: 'Use individual function imports',
  },
  {
    name: 'Full Date-fns Import',
    pattern: /import\s+\*\s+as\s+\w+\s+from\s+['"]date-fns['"]/g,
    severity: 'error',
    message: 'Full date-fns import detected (~60KB)',
    suggestion: 'Use: import { format } from "date-fns"',
  },
  {
    name: 'Full Lucide Import',
    pattern: /import\s+\*\s+as\s+\w+\s+from\s+['"]lucide-react['"]/g,
    severity: 'error',
    message: 'Full lucide-react import detected (~200KB)',
    suggestion: 'Use: import { Search, User } from "lucide-react"',
  },
  {
    name: 'Full React Hook Form Import',
    pattern: /import\s+\*\s+as\s+\w+\s+from\s+['"]react-hook-form['"]/g,
    severity: 'warning',
    message: 'Full react-hook-form import detected',
    suggestion: 'Use: import { useForm } from "react-hook-form"',
  },
];

// Good import patterns
const GOOD_PATTERNS = [
  {
    name: 'Lodash ES Individual Imports',
    pattern: /import\s+{[^}]+}\s+from\s+['"]lodash-es['"]/g,
  },
  {
    name: 'Date-fns Individual Imports',
    pattern: /import\s+{[^}]+}\s+from\s+['"]date-fns['"]/g,
  },
  {
    name: 'Lucide Individual Imports',
    pattern: /import\s+{[^}]+}\s+from\s+['"]lucide-react['"]/g,
  },
];

async function analyzeTreeShaking() {
  console.log(colorize('\n🌳 Tree Shaking Analysis', 'cyan'));
  
  try {
    // Find all TypeScript and JavaScript files
    const files = await glob('src/**/*.{ts,tsx,js,jsx}', {
      cwd: process.cwd(),
      ignore: ['**/*.test.*', '**/*.spec.*', '**/node_modules/**'],
    });
    
    console.log(`\nAnalyzing ${files.length} files...`);
    
    const results = {
      totalFiles: files.length,
      issues: [],
      goodPatterns: [],
      summary: {
        errors: 0,
        warnings: 0,
        optimized: 0,
      },
    };
    
    for (const file of files) {
      const filePath = path.join(process.cwd(), file);
      const content = fs.readFileSync(filePath, 'utf8');
      
      // Check for problematic patterns
      for (const pattern of PROBLEMATIC_PATTERNS) {
        const matches = [...content.matchAll(pattern.pattern)];
        
        if (matches.length > 0) {
          matches.forEach(match => {
            const lineNumber = getLineNumber(content, match.index);
            results.issues.push({
              file,
              line: lineNumber,
              pattern: pattern.name,
              severity: pattern.severity,
              message: pattern.message,
              suggestion: pattern.suggestion,
              code: match[0],
            });
            
            if (pattern.severity === 'error') {
              results.summary.errors++;
            } else {
              results.summary.warnings++;
            }
          });
        }
      }
      
      // Check for good patterns
      for (const pattern of GOOD_PATTERNS) {
        const matches = [...content.matchAll(pattern.pattern)];
        if (matches.length > 0) {
          results.summary.optimized += matches.length;
          results.goodPatterns.push({
            file,
            pattern: pattern.name,
            count: matches.length,
          });
        }
      }
    }
    
    displayResults(results);
    generateReport(results);
    
  } catch (error) {
    console.error(colorize('❌ Tree shaking analysis failed:', 'red'), error.message);
    process.exit(1);
  }
}

function getLineNumber(content, index) {
  const lines = content.substring(0, index).split('\n');
  return lines.length;
}

function displayResults(results) {
  console.log(colorize('\n📊 Analysis Results:', 'blue'));
  
  // Summary
  console.log(colorize('\nSummary:', 'bright'));
  console.log(`  Files analyzed: ${results.totalFiles}`);
  console.log(`  ${colorize('Errors:', 'red')} ${results.summary.errors}`);
  console.log(`  ${colorize('Warnings:', 'yellow')} ${results.summary.warnings}`);
  console.log(`  ${colorize('Optimized imports:', 'green')} ${results.summary.optimized}`);
  
  // Issues
  if (results.issues.length > 0) {
    console.log(colorize('\n❌ Issues Found:', 'red'));
    
    const groupedIssues = results.issues.reduce((acc, issue) => {
      if (!acc[issue.severity]) acc[issue.severity] = [];
      acc[issue.severity].push(issue);
      return acc;
    }, {});
    
    // Show errors first
    if (groupedIssues.error) {
      console.log(colorize('\n🚨 Errors (High Impact):', 'red'));
      groupedIssues.error.forEach(issue => {
        console.log(`  ${colorize(issue.file, 'cyan')}:${issue.line}`);
        console.log(`    ${colorize(issue.message, 'red')}`);
        console.log(`    ${colorize('Suggestion:', 'yellow')} ${issue.suggestion}`);
        console.log(`    Code: ${colorize(issue.code.trim(), 'magenta')}`);
        console.log('');
      });
    }
    
    // Show warnings
    if (groupedIssues.warning) {
      console.log(colorize('\n⚠️  Warnings (Medium Impact):', 'yellow'));
      groupedIssues.warning.forEach(issue => {
        console.log(`  ${colorize(issue.file, 'cyan')}:${issue.line}`);
        console.log(`    ${issue.message}`);
        console.log(`    ${colorize('Suggestion:', 'yellow')} ${issue.suggestion}`);
        console.log('');
      });
    }
  } else {
    console.log(colorize('\n✅ No tree shaking issues found!', 'green'));
  }
  
  // Good patterns
  if (results.goodPatterns.length > 0) {
    console.log(colorize('\n✅ Optimized Imports Found:', 'green'));
    
    const patternCounts = results.goodPatterns.reduce((acc, pattern) => {
      if (!acc[pattern.pattern]) acc[pattern.pattern] = 0;
      acc[pattern.pattern] += pattern.count;
      return acc;
    }, {});
    
    Object.entries(patternCounts).forEach(([pattern, count]) => {
      console.log(`  ${pattern}: ${count} occurrences`);
    });
  }
  
  // Recommendations
  console.log(colorize('\n💡 Recommendations:', 'blue'));
  
  if (results.summary.errors > 0) {
    console.log('  🔴 High Priority:');
    console.log('    • Fix error-level import issues to reduce bundle size significantly');
    console.log('    • Use individual imports instead of full library imports');
  }
  
  if (results.summary.warnings > 0) {
    console.log('  🟡 Medium Priority:');
    console.log('    • Review warning-level imports for potential optimizations');
    console.log('    • Consider using more specific imports where possible');
  }
  
  console.log('  🟢 General Optimizations:');
  console.log('    • Use webpack-bundle-analyzer to identify large dependencies');
  console.log('    • Enable tree shaking in your build configuration');
  console.log('    • Consider using dynamic imports for code splitting');
  console.log('    • Remove unused dependencies from package.json');
  
  // Score calculation
  const totalIssues = results.summary.errors + results.summary.warnings;
  const score = Math.max(0, 100 - (results.summary.errors * 10) - (results.summary.warnings * 5));
  
  const scoreColor = score >= 80 ? 'green' : score >= 60 ? 'yellow' : 'red';
  console.log(colorize(`\n🎯 Tree Shaking Score: ${score}/100`, scoreColor));
}

function generateReport(results) {
  const reportPath = path.join(process.cwd(), 'tree-shaking-report.json');
  
  const report = {
    timestamp: new Date().toISOString(),
    summary: results.summary,
    issues: results.issues,
    goodPatterns: results.goodPatterns,
    recommendations: generateRecommendations(results),
    score: Math.max(0, 100 - (results.summary.errors * 10) - (results.summary.warnings * 5)),
  };
  
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  console.log(colorize(`\n📄 Detailed report saved to: ${reportPath}`, 'green'));
}

function generateRecommendations(results) {
  const recommendations = [];
  
  if (results.summary.errors > 0) {
    recommendations.push({
      priority: 'high',
      type: 'bundle-size',
      message: 'Fix error-level import issues to significantly reduce bundle size',
      impact: 'high',
    });
  }
  
  if (results.summary.warnings > 0) {
    recommendations.push({
      priority: 'medium',
      type: 'optimization',
      message: 'Review and optimize warning-level imports',
      impact: 'medium',
    });
  }
  
  recommendations.push({
    priority: 'low',
    type: 'maintenance',
    message: 'Regularly audit dependencies and remove unused packages',
    impact: 'low',
  });
  
  return recommendations;
}

// Main execution
if (require.main === module) {
  console.log(colorize('🚀 Tree Shaking Analysis Tool', 'bright'));
  analyzeTreeShaking().then(() => {
    console.log(colorize('\n✅ Tree shaking analysis complete!', 'green'));
  });
}

module.exports = { analyzeTreeShaking };