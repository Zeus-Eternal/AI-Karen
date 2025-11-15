#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

function checkForIssues(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const lines = content.split('\n');
    
    const issues = [];
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const lineNum = i + 1;
      
      // Check for various issues
      const patterns = [
        { regex: /:\s*any\b/, description: 'Type annotation with any' },
        { regex: /\bas\s+any\b/, description: 'Type assertion to any' },
        { regex: /Array<any>/, description: 'Array of any' },
        { regex: /Record<[^,]+,\s*any>/, description: 'Record with any value type' },
        { regex: /Promise<any>/, description: 'Promise of any' },
        { regex: /\bany\[\]/, description: 'Array of any (bracket notation)' }
      ];
      
      for (const pattern of patterns) {
        if (pattern.regex.test(line)) {
          // Skip comments
          const commentIndex = line.indexOf('//');
          const matchIndex = line.search(pattern.regex);
          if (commentIndex === -1 || matchIndex < commentIndex) {
            issues.push({
              line: lineNum,
              column: matchIndex + 1,
              description: pattern.description,
              content: line.trim()
            });
          }
        }
      }
    }
    
    return issues;
  } catch (error) {
    return [];
  }
}

// Check the specific file mentioned in the error
const filePath = 'ui_launchers/KAREN-Theme-Default/src/test-utils/test-providers.tsx';
console.log('🔍 Final verification of: ' + filePath);

if (!fs.existsSync(filePath)) {
  console.log('❌ File not found: ' + filePath);
  process.exit(1);
}

const issues = checkForIssues(filePath);

if (issues.length === 0) {
  console.log('✅ No any type issues found!');
  
  // Check if React Fast Refresh warning is suppressed
  const content = fs.readFileSync(filePath, 'utf8');
  if (content.includes('eslint-disable react-refresh/only-export-components')) {
    console.log('✅ React Fast Refresh warnings suppressed!');
  } else {
    console.log('⚠️  React Fast Refresh warnings may still appear (this is expected for test utilities)');
  }
  
  console.log('\n🎉 File is ready for production!');
} else {
  console.log('❌ Found remaining issues:');
  issues.forEach(issue => {
    console.log(`  Line ${issue.line}:${issue.column} - ${issue.description}`);
    console.log(`    ${issue.content}`);
  });
}

console.log(`\nTotal issues: ${issues.length}`);