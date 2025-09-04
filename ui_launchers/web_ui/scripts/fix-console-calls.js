#!/usr/bin/env node

/**
 * Script to replace direct console.error and console.warn calls with safe alternatives
 */

const fs = require('fs');
const path = require('path');
const glob = require('glob');

// Files to process
const srcDir = 'ui_launchers/web_ui/src';
const patterns = [
  `${srcDir}/**/*.ts`,
  `${srcDir}/**/*.tsx`,
];

// Exclude certain files
const excludePatterns = [
  '**/console-error-fix.ts',
  '**/safe-console.ts',
  '**/*.test.ts',
  '**/*.test.tsx',
  '**/ChatInterfaceTest.tsx',
];

function shouldExcludeFile(filePath) {
  return excludePatterns.some(pattern => {
    const regex = new RegExp(pattern.replace(/\*\*/g, '.*').replace(/\*/g, '[^/]*'));
    return regex.test(filePath);
  });
}

function processFile(filePath) {
  if (shouldExcludeFile(filePath)) {
    console.log(`Skipping excluded file: ${filePath}`);
    return;
  }

  const content = fs.readFileSync(filePath, 'utf8');
  let modified = false;
  let newContent = content;

  // Check if file already imports safe console
  const hasSafeConsoleImport = /import.*\{.*safe(Error|Warn|Info|Debug).*\}.*from.*['"]@\/lib\/safe-console['"]/.test(content);

  // Replace console.error calls
  const consoleErrorRegex = /console\.error\s*\(/g;
  if (consoleErrorRegex.test(content)) {
    newContent = newContent.replace(/console\.error\s*\(/g, 'safeError(');
    modified = true;
  }

  // Replace console.warn calls
  const consoleWarnRegex = /console\.warn\s*\(/g;
  if (consoleWarnRegex.test(content)) {
    newContent = newContent.replace(/console\.warn\s*\(/g, 'safeWarn(');
    modified = true;
  }

  // Add import if needed and modifications were made
  if (modified && !hasSafeConsoleImport) {
    // Find existing imports
    const importRegex = /^import.*from.*['"][^'"]*['"];?\s*$/gm;
    const imports = content.match(importRegex) || [];
    
    if (imports.length > 0) {
      // Add after last import
      const lastImport = imports[imports.length - 1];
      const lastImportIndex = content.lastIndexOf(lastImport);
      const insertIndex = lastImportIndex + lastImport.length;
      
      const safeConsoleImport = '\nimport { safeError, safeWarn } from "@/lib/safe-console";';
      newContent = content.slice(0, insertIndex) + safeConsoleImport + content.slice(insertIndex);
    } else {
      // Add at the beginning
      const safeConsoleImport = 'import { safeError, safeWarn } from "@/lib/safe-console";\n\n';
      newContent = safeConsoleImport + content;
    }
  }

  if (modified) {
    fs.writeFileSync(filePath, newContent);
    console.log(`✅ Updated: ${filePath}`);
  }
}

function main() {
  console.log('🔧 Fixing console calls in TypeScript files...\n');

  // Get all files
  const allFiles = [];
  patterns.forEach(pattern => {
    const files = glob.sync(pattern);
    allFiles.push(...files);
  });

  // Remove duplicates
  const uniqueFiles = [...new Set(allFiles)];

  console.log(`Found ${uniqueFiles.length} files to process\n`);

  // Process each file
  uniqueFiles.forEach(processFile);

  console.log('\n✨ Console call fixes complete!');
  console.log('\n📋 Next steps:');
  console.log('1. Review the changes');
  console.log('2. Test the application');
  console.log('3. Commit the changes');
}

if (require.main === module) {
  main();
}