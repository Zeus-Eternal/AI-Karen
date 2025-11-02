#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// Find all .tsx files in src directory
function findTsxFiles(dir) {
  const files = [];
  const items = fs.readdirSync(dir);
  
  for (const item of items) {
    const fullPath = path.join(dir, item);
    const stat = fs.statSync(fullPath);
    
    if (stat.isDirectory() && !item.startsWith('.') && item !== 'node_modules') {
      files.push(...findTsxFiles(fullPath));
    } else if (item.endsWith('.tsx')) {
      files.push(fullPath);
    }
  }
  
  return files;
}

// Fix React imports and JSX issues
function fixReactImports(content) {
  let fixed = content;
  
  // Check if file contains JSX
  const hasJSX = /<[A-Z]/.test(fixed) || /<[a-z]/.test(fixed);
  
  if (!hasJSX) {
    return fixed; // No JSX, no need to fix
  }
  
  // Check if React is already imported
  const hasReactImport = /import\s+React/.test(fixed) || /import\s+\*\s+as\s+React/.test(fixed);
  
  if (!hasReactImport) {
    // Find the position to insert React import
    const lines = fixed.split('\n');
    let insertIndex = 0;
    
    // Find the first line that's not a comment, "use client", or empty
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (line === '"use client";' || line === "'use client';") {
        insertIndex = i + 1;
        continue;
      }
      if (line.startsWith('//') || line.startsWith('/*') || line === '') {
        continue;
      }
      if (line.startsWith('import')) {
        insertIndex = i;
        break;
      }
      // If we hit non-import content, insert before it
      insertIndex = i;
      break;
    }
    
    // Insert React import
    lines.splice(insertIndex, 0, 'import React from \'react\';');
    fixed = lines.join('\n');
  }
  
  return fixed;
}

// Main execution
const srcDir = path.join(__dirname, 'src');
const files = findTsxFiles(srcDir);

console.log(`Found ${files.length} .tsx files to check`);

let fixedCount = 0;

for (const file of files) {
  try {
    const content = fs.readFileSync(file, 'utf8');
    const fixed = fixReactImports(content);
    
    if (fixed !== content) {
      fs.writeFileSync(file, fixed);
      console.log(`Fixed: ${file}`);
      fixedCount++;
    }
  } catch (error) {
    console.error(`Error processing ${file}:`, error.message);
  }
}

console.log(`Fixed ${fixedCount} files`);