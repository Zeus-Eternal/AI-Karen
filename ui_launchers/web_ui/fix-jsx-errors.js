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

// Fix JSX and React import issues
function fixJsxErrors(content) {
  let fixed = content;
  
  // Ensure React is imported if JSX is used and not already imported
  if (fixed.includes('<') && fixed.includes('>') && !fixed.includes('import React') && !fixed.includes('import * as React')) {
    // Find the first import statement
    const firstImportMatch = fixed.match(/^import\s+/m);
    if (firstImportMatch) {
      const insertIndex = fixed.indexOf(firstImportMatch[0]);
      fixed = fixed.slice(0, insertIndex) + 'import React from \'react\';\n' + fixed.slice(insertIndex);
    } else {
      // If no imports, add React import after "use client" or at the beginning
      const useClientMatch = fixed.match(/^["']use client["'];?\s*$/m);
      if (useClientMatch) {
        const insertIndex = fixed.indexOf(useClientMatch[0]) + useClientMatch[0].length;
        fixed = fixed.slice(0, insertIndex) + '\n\nimport React from \'react\';' + fixed.slice(insertIndex);
      } else {
        fixed = 'import React from \'react\';\n' + fixed;
      }
    }
  }
  
  // Fix "use client" directive format
  fixed = fixed.replace(/^'use client';/gm, '"use client";');
  
  // Ensure proper spacing after "use client"
  fixed = fixed.replace(/^"use client";\s*$/gm, '"use client";\n');
  
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
    const fixed = fixJsxErrors(content);
    
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