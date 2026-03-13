#!/usr/bin/env node

/**
 * Component Validation Script
 * 
 * This script runs at build time to validate that only
 * active components are being used in the codebase.
 */

const fs = require('fs');
const path = require('path');
const glob = require('glob');

// Import component registry
const { 
  validateComponentImports, 
  getDeprecatedComponents, 
  getLegacyComponents,
  COMPONENT_REGISTRY 
} = require('../src/lib/component-registry.ts');

// ANSI color codes for better output
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  white: '\x1b[37m'
};

function log(message, color = 'white') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function logSuccess(message) {
  log(`✅ ${message}`, 'green');
}

function logWarning(message) {
  log(`⚠️  ${message}`, 'yellow');
}

function logError(message) {
  log(`❌ ${message}`, 'red');
}

function logInfo(message) {
  log(`ℹ️  ${message}`, 'blue');
}

// Scan source files for component usage
function scanSourceFiles() {
  const sourceFiles = glob.sync('src/**/*.{ts,tsx,js,jsx}', {
    ignore: ['**/node_modules/**', '**/.next/**', '**/dist/**']
  });

  const componentUsage = new Map();
  const importStatements = new Map();

  sourceFiles.forEach(filePath => {
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      
      // Find import statements
      const importRegex = /import\s+.*?from\s+['"`]([^'"`]+)['"`]/g;
      let match;
      
      while ((match = importRegex.exec(content)) !== null) {
        const importPath = match[1];
        
        // Check if it's a component import
        if (importPath.includes('@/components/') || importPath.includes('../components/')) {
          const componentName = path.basename(importPath).replace(/\.(tsx?|jsx?)$/, '');
          
          if (!importStatements.has(componentName)) {
            importStatements.set(componentName, []);
          }
          importStatements.get(componentName).push(filePath);
        }
      }

      // Find component usage in JSX
      const jsxRegex = /<([A-Z][a-zA-Z0-9]*)/g;
      while ((match = jsxRegex.exec(content)) !== null) {
        const componentName = match[1];
        
        if (!componentUsage.has(componentName)) {
          componentUsage.set(componentName, []);
        }
        componentUsage.get(componentName).push(filePath);
      }
    } catch (error) {
      logWarning(`Failed to read file ${filePath}: ${error.message}`);
    }
  });

  return { componentUsage, importStatements };
}

// Validate component usage against registry
function validateComponents(componentUsage, importStatements) {
  const validation = validateComponentImports();
  const issues = [];

  // Check for deprecated components
  validation.deprecated.forEach(componentId => {
    const component = COMPONENT_REGISTRY[componentId];
    const usage = componentUsage.get(component.name) || [];
    
    if (usage.length > 0) {
      issues.push({
        type: 'deprecated',
        component: component.name,
        componentId,
        usage,
        message: `${component.name} is deprecated and will be removed in ${component.removedIn}`,
        migration: component.migrationPath
      });
    }
  });

  // Check for legacy components
  validation.legacy.forEach(componentId => {
    const component = COMPONENT_REGISTRY[componentId];
    const usage = componentUsage.get(component.name) || [];
    
    if (usage.length > 0) {
      issues.push({
        type: 'legacy',
        component: component.name,
        componentId,
        usage,
        message: `${component.name} is ${component.status} and should not be used`,
        migration: component.migrationPath
      });
    }
  });

  return issues;
}

// Generate validation report
function generateReport(issues, componentUsage, importStatements) {
  log('\n📊 Component Validation Report', 'cyan');
  log('='.repeat(50), 'cyan');

  // Summary
  const totalComponents = Object.keys(COMPONENT_REGISTRY).length;
  const activeComponents = Object.values(COMPONENT_REGISTRY).filter(c => c.status === 'active').length;
  const deprecatedComponents = Object.values(COMPONENT_REGISTRY).filter(c => c.status === 'deprecated').length;
  const legacyComponents = Object.values(COMPONENT_REGISTRY).filter(c => c.status === 'legacy' || c.status === 'removed').length;

  logInfo(`Total Components: ${totalComponents}`);
  logSuccess(`Active Components: ${activeComponents}`);
  logWarning(`Deprecated Components: ${deprecatedComponents}`);
  logError(`Legacy Components: ${legacyComponents}`);

  // Issues found
  if (issues.length > 0) {
    log(`\n🚨 Issues Found: ${issues.length}`, 'red');
    log('='.repeat(50), 'red');

    issues.forEach((issue, index) => {
      log(`\n${index + 1}. ${issue.type.toUpperCase()}: ${issue.component}`, 'red');
      log(`   Message: ${issue.message}`, 'yellow');
      log(`   Migration: ${issue.migration}`, 'blue');
      log(`   Used in:`, 'white');
      
      issue.usage.forEach(filePath => {
        log(`     - ${filePath}`, 'white');
      });
    });
  } else {
    logSuccess('\n✨ No component issues found! All components are up to date.');
  }

  // Component usage statistics
  log(`\n📈 Component Usage Statistics`, 'cyan');
  log('='.repeat(50), 'cyan');

  const sortedUsage = Array.from(componentUsage.entries())
    .sort((a, b) => b[1].length - a[1].length)
    .slice(0, 10); // Top 10 most used

  sortedUsage.forEach(([component, files]) => {
    log(`${component}: ${files.length} files`, 'white');
  });

  // Performance recommendations
  log(`\n💡 Performance Recommendations`, 'cyan');
  log('='.repeat(50), 'cyan');

  if (issues.length > 0) {
    logError('1. Remove all legacy/deprecated component usage');
    logInfo('2. Run bundle analyzer to identify large components');
    logInfo('3. Implement code splitting for better performance');
  } else {
    logSuccess('1. Component usage is optimal');
    logInfo('2. Consider lazy loading for large components');
    logInfo('3. Monitor component render times in production');
  }

  return issues.length === 0;
}

// Main execution
function main() {
  log('🔍 Starting Component Validation...', 'cyan');
  log('Scanning source files for component usage...\n');

  try {
    const { componentUsage, importStatements } = scanSourceFiles();
    const issues = validateComponents(componentUsage, importStatements);
    const isValid = generateReport(issues, componentUsage, importStatements);

    // Exit with appropriate code
    process.exit(isValid ? 0 : 1);
  } catch (error) {
    logError(`Validation failed: ${error.message}`);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = {
  scanSourceFiles,
  validateComponents,
  generateReport
};