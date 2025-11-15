#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

function fixReactRefreshWarnings(filePath) {
  try {
    if (!fs.existsSync(filePath)) {
      console.log('File not found: ' + filePath);
      return false;
    }

    const content = fs.readFileSync(filePath, 'utf8');
    
    // Check if this file has React Fast Refresh warnings
    if (!content.includes('export const') && !content.includes('export function')) {
      console.log('No utility exports found in: ' + filePath);
      return false;
    }

    // For test-providers.tsx, we'll add a comment to disable the warning
    // since separating would break the testing utilities structure
    let newContent = content;
    
    // Add eslint-disable comment at the top if not already present
    if (!content.includes('eslint-disable react-refresh/only-export-components')) {
      const importIndex = content.indexOf('import');
      if (importIndex !== -1) {
        const beforeImports = content.substring(0, importIndex);
        const afterImports = content.substring(importIndex);
        
        newContent = beforeImports + 
          '/* eslint-disable react-refresh/only-export-components */\n' +
          afterImports;
      }
    }

    if (newContent !== content) {
      // Create backup
      if (!fs.existsSync(filePath + '.backup')) {
        fs.writeFileSync(filePath + '.backup', content, 'utf8');
      }
      
      // Write new content
      fs.writeFileSync(filePath, newContent, 'utf8');
      
      console.log('Fixed React Fast Refresh warnings in: ' + path.relative(process.cwd(), filePath));
      return true;
    }

    return false;
  } catch (error) {
    console.error('Error processing ' + filePath + ': ' + error.message);
    return false;
  }
}

// Fix the specific file
const filePath = 'ui_launchers/KAREN-Theme-Default/src/test-utils/test-providers.tsx';
fixReactRefreshWarnings(filePath);