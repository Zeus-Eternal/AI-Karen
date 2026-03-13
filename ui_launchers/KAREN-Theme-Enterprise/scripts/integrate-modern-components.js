#!/usr/bin/env node

/**
 * Modern Component Integration Script
 * Automatically updates existing pages to use modern components
 */

const fs = require('fs');
const path = require('path');
const glob = require('glob');

const PAGES_DIR = path.join(__dirname, '../src/app');
const COMPONENTS_DIR = path.join(__dirname, '../src/components');

// Component mapping for automatic replacement
const COMPONENT_REPLACEMENTS = {
  // Old import -> New import
  "import { Button } from '@/components/ui/button'": "import { Button } from '@/components/ui/polymorphic/button'",
  "import { Card } from '@/components/ui/card'": "import { Card } from '@/components/ui/compound/card'",
  "import { Modal } from '@/components/ui/modal'": "import { Modal } from '@/components/ui/compound/modal'",
  "import { Form } from '@/components/ui/form'": "import { Form } from '@/components/ui/compound/form'",
  
  // Layout components
  '<div className="flex': '<FlexContainer',
  '<div className="grid': '<GridContainer',
  '</div>': '</FlexContainer>',
  
  // CSS class replacements
  'className="flex items-center justify-between"': 'justify="between" align="center"',
  'className="flex items-center justify-center"': 'justify="center" align="center"',
  'className="flex items-center"': 'align="center"',
  'className="flex flex-col"': 'direction="column"',
  'className="grid grid-cols-': 'columns="',
};

// Layout component imports to add
const LAYOUT_IMPORTS = `
import { GridContainer } from '@/components/ui/layout/grid-container';
import { FlexContainer } from '@/components/ui/layout/flex-container';
import { ResponsiveContainer } from '@/components/ui/layout/responsive-container';
`;

/**
 * Process a single file for component integration
 */
function processFile(filePath) {
  console.log(`Processing: ${filePath}`);
  
  let content = fs.readFileSync(filePath, 'utf8');
  let modified = false;
  
  // Add layout imports if not present and file uses React
  if (content.includes('import React') || content.includes('from \'react\'')) {
    if (!content.includes('@/components/ui/layout/')) {
      const importIndex = content.lastIndexOf('import');
      const nextLineIndex = content.indexOf('\n', importIndex);
      content = content.slice(0, nextLineIndex) + LAYOUT_IMPORTS + content.slice(nextLineIndex);
      modified = true;
    }
  }
  
  // Apply component replacements
  for (const [oldPattern, newPattern] of Object.entries(COMPONENT_REPLACEMENTS)) {
    if (content.includes(oldPattern)) {
      content = content.replace(new RegExp(oldPattern, 'g'), newPattern);
      modified = true;
    }
  }
  
  // Write back if modified
  if (modified) {
    fs.writeFileSync(filePath, content, 'utf8');
    console.log(`✅ Updated: ${filePath}`);
  } else {
    console.log(`⏭️  No changes needed: ${filePath}`);
  }
}

/**
 * Find all TypeScript/TSX files in pages and components
 */
function findFiles() {
  const patterns = [
    path.join(PAGES_DIR, '**/*.tsx'),
    path.join(PAGES_DIR, '**/*.ts'),
    path.join(COMPONENTS_DIR, '**/*.tsx'),
    path.join(COMPONENTS_DIR, '**/*.ts'),
  ];
  
  let files = [];
  patterns.forEach(pattern => {
    files = files.concat(glob.sync(pattern));
  });
  
  // Filter out test files and node_modules
  return files.filter(file => 
    !file.includes('node_modules') && 
    !file.includes('.test.') && 
    !file.includes('.spec.') &&
    !file.includes('__tests__')
  );
}

/**
 * Main integration function
 */
function integrateModernComponents() {
  console.log('🚀 Starting modern component integration...\n');
  
  const files = findFiles();
  console.log(`Found ${files.length} files to process\n`);
  
  files.forEach(processFile);
  
  console.log('\n✨ Modern component integration complete!');
  console.log('\n📋 Next steps:');
  console.log('1. Run tests to ensure everything works');
  console.log('2. Check for any manual fixes needed');
  console.log('3. Update any custom component usage');
}

// Run the integration
if (require.main === module) {
  integrateModernComponents();
}

module.exports = { integrateModernComponents, processFile };