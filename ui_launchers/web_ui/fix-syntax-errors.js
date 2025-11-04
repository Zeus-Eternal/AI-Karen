#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

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

// Fix common syntax errors
function fixSyntaxErrors(content) {
  let fixed = content;
  
  // Fix malformed button elements with aria-label issues
  fixed = fixed.replace(
    /<Button([^>]*?)aria-label="Button">([^<]*?)<\/Button>/g,
    '<Button$1>$2</Button>'
  );
  
  // Fix button elements that should be Button components
  fixed = fixed.replace(
    /<Button([^>]*?)variant="([^"]*?)"([^>]*?)aria-label="Button">/g,
    '<Button$1variant="$2"$3>'
  );
  
  // Fix onClick handlers with malformed syntax
  fixed = fixed.replace(
    /onClick=\{([^}]*?) = aria-label="[^"]*"> ([^}]*?)\}/g,
    'onClick={() => $2}'
  );
  
  // Fix className attributes with responsive classes
  fixed = fixed.replace(
    /className="([^"]*?)sm:w-auto md:w-full([^"]*)"/g,
    'className="$1$2"'
  );
  
  // Fix malformed input elements
  fixed = fixed.replace(
    /onChange=\{([^}]*?) = aria-label="[^"]*"> ([^}]*?)\}/g,
    'onChange={($1) => $2}'
  );
  
  // Fix malformed select elements
  fixed = fixed.replace(
    /onChange=\{([^}]*?): React\.ChangeEvent<HTML[^>]*?aria-label="[^"]*">\) => ([^}]*?)\}/g,
    'onChange={($1) => $2}'
  );
  
  // Fix button closing tags
  fixed = fixed.replace(
    /<\/Button>/g,
    '</Button>'
  );
  
  // Fix disabled attributes with malformed syntax
  fixed = fixed.replace(
    /disabled=\{([^}]*?) aria-label="[^"]*">\}/g,
    'disabled={$1}'
  );
  
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
    const fixed = fixSyntaxErrors(content);
    
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