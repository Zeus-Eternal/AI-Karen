#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

function findTypeScriptFiles() {
  try {
    const output = execSync('find ui_launchers/KAREN-Theme-Default/src -name "*.ts" -o -name "*.tsx" | head -20', { encoding: 'utf8' });
    return output.trim().split('\n').filter(f => f.length > 0);
  } catch (error) {
    console.log('Error finding files:', error.message);
    return [];
  }
}

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
    return [];
  }
}

console.log('🔍 Verifying TypeScript any type fixes...\n');

const files = findTypeScriptFiles();
console.log(`Checking ${files.length} TypeScript files...\n`);

let totalIssues = 0;
let filesWithIssues = 0;

for (const file of files) {
  const issues = checkForAnyTypes(file);
  
  if (issues.length > 0) {
    filesWithIssues++;
    totalIssues += issues.length;
    
    console.log(`❌ ${path.relative(process.cwd(), file)}:`);
    issues.forEach(issue => {
      console.log(`  Line ${issue.line}:${issue.column} - ${issue.description}`);
    });
    console.log('');
  }
}

console.log('📊 Summary:');
console.log(`Files checked: ${files.length}`);
console.log(`Files with issues: ${filesWithIssues}`);
console.log(`Total any type issues: ${totalIssues}`);

if (totalIssues === 0) {
  console.log('\n🎉 All checked files are clean of any type issues!');
} else {
  console.log(`\n⚠️  ${totalIssues} any type issues found in ${filesWithIssues} files.`);
}