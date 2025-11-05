#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

function checkBraces(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const lines = content.split('\n');
    
    let braceStack = [];
    let parenStack = [];
    let bracketStack = [];
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const lineNum = i + 1;
      
      // Skip comments and strings (basic approach)
      let inString = false;
      let inComment = false;
      let stringChar = '';
      
      for (let j = 0; j < line.length; j++) {
        const char = line[j];
        const prevChar = j > 0 ? line[j-1] : '';
        const nextChar = j < line.length - 1 ? line[j+1] : '';
        
        // Handle strings
        if (!inComment && (char === '"' || char === "'" || char === '`')) {
          if (!inString) {
            inString = true;
            stringChar = char;
          } else if (char === stringChar && prevChar !== '\\') {
            inString = false;
            stringChar = '';
          }
          continue;
        }
        
        // Handle comments
        if (!inString && char === '/' && nextChar === '/') {
          inComment = true;
          break;
        }
        
        if (!inString && !inComment) {
          switch (char) {
            case '{':
              braceStack.push({ char, line: lineNum, col: j + 1 });
              break;
            case '}':
              if (braceStack.length === 0) {
                console.log(`${filePath}:${lineNum}:${j + 1} - Unmatched closing brace`);
              } else {
                braceStack.pop();
              }
              break;
            case '(':
              parenStack.push({ char, line: lineNum, col: j + 1 });
              break;
            case ')':
              if (parenStack.length === 0) {
                console.log(`${filePath}:${lineNum}:${j + 1} - Unmatched closing parenthesis`);
              } else {
                parenStack.pop();
              }
              break;
            case '[':
              bracketStack.push({ char, line: lineNum, col: j + 1 });
              break;
            case ']':
              if (bracketStack.length === 0) {
                console.log(`${filePath}:${lineNum}:${j + 1} - Unmatched closing bracket`);
              } else {
                bracketStack.pop();
              }
              break;
          }
        }
      }
    }
    
    // Report unclosed braces
    if (braceStack.length > 0) {
      console.log(`${filePath} - Unclosed braces:`);
      braceStack.forEach(brace => {
        console.log(`  Line ${brace.line}, Column ${brace.col}: ${brace.char}`);
      });
    }
    
    if (parenStack.length > 0) {
      console.log(`${filePath} - Unclosed parentheses:`);
      parenStack.forEach(paren => {
        console.log(`  Line ${paren.line}, Column ${paren.col}: ${paren.char}`);
      });
    }
    
    if (bracketStack.length > 0) {
      console.log(`${filePath} - Unclosed brackets:`);
      bracketStack.forEach(bracket => {
        console.log(`  Line ${bracket.line}, Column ${bracket.col}: ${bracket.char}`);
      });
    }
    
    if (braceStack.length === 0 && parenStack.length === 0 && bracketStack.length === 0) {
      console.log(`${filePath} - All braces, parentheses, and brackets are properly matched`);
    }
    
  } catch (error) {
    console.error(`Error reading ${filePath}:`, error.message);
  }
}

// Check the problematic files
const files = [
  'src/contexts/AuthContext.tsx',
  'src/contexts/HookContext.tsx',
  'src/hooks/use-download-status.ts',
  'src/hooks/useProviderNotifications.ts',
  'src/hooks/useTextSelection.ts'
];

files.forEach(file => {
  console.log(`\n=== Checking ${file} ===`);
  checkBraces(file);
});