const fs = require('fs');

const content = fs.readFileSync('src/components/settings/BehaviorSettings.tsx', 'utf8');
const lines = content.split('\n');

let braceCount = 0;
let inFunction = false;
let functionStartLine = -1;

lines.forEach((line, index) => {
  const lineNum = index + 1;
  
  // Check for function start
  if (line.includes('export default function BehaviorSettings()')) {
    inFunction = true;
    functionStartLine = lineNum;
    console.log(`Function starts at line ${lineNum}`);
  }
  
  // Count braces
  for (const char of line) {
    if (char === '{') {
      braceCount++;
      if (inFunction) {
        console.log(`Line ${lineNum}: Opening brace, count: ${braceCount}`);
      }
    }
    if (char === '}') {
      braceCount--;
      if (inFunction) {
        console.log(`Line ${lineNum}: Closing brace, count: ${braceCount}`);
        if (braceCount === 0) {
          console.log(`Function ends at line ${lineNum}`);
          inFunction = false;
        }
      }
    }
  }
  
  // Check for return statement
  if (line.trim().startsWith('return (') && !inFunction) {
    console.log(`ERROR: Return statement at line ${lineNum} is outside function!`);
  }
});

console.log(`Final brace count: ${braceCount}`);