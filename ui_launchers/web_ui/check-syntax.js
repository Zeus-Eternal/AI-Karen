const fs = require('fs');
const path = require('path');

const problematicFiles = [
  'src/components/error-handling/ErrorBoundary.tsx',
  'src/components/plugins/DateTimePluginPage.tsx',
  'src/components/settings/CopilotKitSettings.tsx'
];

problematicFiles.forEach(filePath => {
  console.log(`\n=== Checking ${filePath} ===`);
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    
    // Check for basic syntax issues
    const lines = content.split('\n');
    let braceCount = 0;
    let parenCount = 0;
    let inFunction = false;
    
    lines.forEach((line, index) => {
      const lineNum = index + 1;
      
      // Count braces and parens
      for (const char of line) {
        if (char === '{') braceCount++;
        if (char === '}') braceCount--;
        if (char === '(') parenCount++;
        if (char === ')') parenCount--;
      }
      
      // Check for function declarations
      if (line.includes('function ') || line.includes('const ') || line.includes('export ')) {
        inFunction = true;
      }
      
      // Check for return statements
      if (line.trim().startsWith('return (') && inFunction) {
        console.log(`Line ${lineNum}: Found return statement, brace count: ${braceCount}, paren count: ${parenCount}`);
        if (braceCount < 0) {
          console.log(`  WARNING: Negative brace count at return statement!`);
        }
      }
      
      // Check for problematic patterns
      if (line.includes('} catch') && !line.includes('} catch (')) {
        console.log(`Line ${lineNum}: Potential missing opening brace before catch`);
      }
      
      if (line.includes('toast({') && !line.includes('});')) {
        // Look ahead for closing
        let found = false;
        for (let i = index + 1; i < Math.min(index + 10, lines.length); i++) {
          if (lines[i].includes('});')) {
            found = true;
            break;
          }
        }
        if (!found) {
          console.log(`Line ${lineNum}: Toast call may be missing closing });`);
        }
      }
    });
    
    console.log(`Final counts - Braces: ${braceCount}, Parens: ${parenCount}`);
    if (braceCount !== 0) console.log(`WARNING: Unbalanced braces!`);
    if (parenCount !== 0) console.log(`WARNING: Unbalanced parentheses!`);
    
  } catch (error) {
    console.log(`Error reading ${filePath}:`, error.message);
  }
});