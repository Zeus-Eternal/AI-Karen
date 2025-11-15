#!/usr/bin/env node

const fs = require('fs');

function checkForAnyTypes(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const lines = content.split('\n');
    
    const issues = [];
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const lineNum = i + 1;
      
      // Check for various 'any' patterns
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
    console.error('Error reading file:', error.message);
    return [];
  }
}

// Check the specific file
const filePath = process.argv[2] || 'ui_launchers/KAREN-Theme-Default/src/lib/auth/hot-reload-auth.ts';
console.log('Checking file:', filePath);

const issues = checkForAnyTypes(filePath);

if (issues.length === 0) {
  console.log('✅ No any type issues found!');
} else {
  console.log('❌ Found any type issues:');
  issues.forEach(issue => {
    console.log(`  Line ${issue.line}:${issue.column} - ${issue.description}`);
    console.log(`    ${issue.content}`);
  });
}

console.log(`\nTotal issues: ${issues.length}`);