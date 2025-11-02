#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const glob = require('glob');

console.log('Fixing duplicate import keywords...');

function fixDuplicateImports(content) {
  // Fix patterns like "import { import { ... }" 
  return content
    .replace(/import\s+{\s*import\s+{/g, 'import {')
    .replace(/import\s+{\s*import\s+/g, 'import ')
    .replace(/import\s+import\s+/g, 'import ');
}

// Find all TypeScript/TSX files
const files = glob.sync('src/**/*.{ts,tsx}', { cwd: process.cwd() });

let fixedCount = 0;
files.forEach(file => {
  try {
    const content = fs.readFileSync(file, 'utf8');
    const fixed = fixDuplicateImports(content);
    
    if (fixed !== content) {
      fs.writeFileSync(file, fixed);
      console.log(`Fixed: ${file}`);
      fixedCount++;
    }
  } catch (error) {
    console.error(`Error processing ${file}:`, error.message);
  }
});

console.log(`Fixed ${fixedCount} files with duplicate import keywords.`);