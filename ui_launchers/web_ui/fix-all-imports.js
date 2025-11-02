#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const glob = require('glob');

console.log('Fixing all import issues comprehensively...');

function fixImports(content) {
  // Split into lines for processing
  const lines = content.split('\n');
  const fixedLines = [];
  let inImport = false;
  let importBuffer = '';
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();
    
    // Handle malformed imports that start with import but don't have proper structure
    if (trimmed.startsWith('import') && trimmed.includes('{') && !trimmed.includes('from')) {
      // This is likely a malformed import, try to fix it
      if (trimmed.includes('} from')) {
        // Already has from clause, just add it
        fixedLines.push(line);
      } else {
        // Missing from clause, start collecting import
        inImport = true;
        importBuffer = line;
      }
      continue;
    }
    
    // Handle continuation of imports
    if (inImport) {
      importBuffer += ' ' + trimmed;
      if (trimmed.includes('}')) {
        // End of import block
        if (!importBuffer.includes(' from ')) {
          // Add a placeholder from clause
          importBuffer += ' from "@/lib/placeholder";';
        }
        fixedLines.push(importBuffer);
        inImport = false;
        importBuffer = '';
      }
      continue;
    }
    
    // Handle standalone import items (missing import keyword)
    if (trimmed && !trimmed.startsWith('//') && !trimmed.startsWith('*') && 
        (trimmed.includes('} from ') || trimmed.match(/^\s*[A-Z][a-zA-Z0-9_,\s]*\s*$/))) {
      // This looks like it should be part of an import
      if (trimmed.includes('} from ')) {
        fixedLines.push('import { ' + line);
      } else {
        // Skip orphaned import items
        continue;
      }
    } else {
      fixedLines.push(line);
    }
  }
  
  // Handle any remaining import buffer
  if (inImport && importBuffer) {
    if (!importBuffer.includes(' from ')) {
      importBuffer += ' from "@/lib/placeholder";';
    }
    fixedLines.push(importBuffer);
  }
  
  let result = fixedLines.join('\n');
  
  // Additional fixes for common patterns
  result = result
    // Fix stray }); patterns
    .replace(/^\s*}\);\s*$/gm, '')
    // Fix malformed arrow functions
    .replace(/\(\)\s*=\s*>/g, '() =>')
    // Fix duplicate import keywords
    .replace(/import\s+import\s+/g, 'import ')
    // Fix missing import keywords
    .replace(/^(\s*)([A-Z][a-zA-Z0-9_,\s]*)\s*}\s*from\s+/gm, '$1import { $2} from ')
    // Clean up extra whitespace in imports
    .replace(/import\s*{\s*\n\s*}/g, 'import {}')
    // Fix trailing commas in imports
    .replace(/,(\s*}\s*from)/g, '$1');
  
  return result;
}

// Find all TypeScript/TSX files
const files = glob.sync('src/**/*.{ts,tsx}', { cwd: process.cwd() });

let fixedCount = 0;
files.forEach(file => {
  try {
    const content = fs.readFileSync(file, 'utf8');
    const fixed = fixImports(content);
    
    if (fixed !== content) {
      fs.writeFileSync(file, fixed);
      console.log(`Fixed: ${file}`);
      fixedCount++;
    }
  } catch (error) {
    console.error(`Error processing ${file}:`, error.message);
  }
});

console.log(`Fixed ${fixedCount} files out of ${files.length} total files.`);