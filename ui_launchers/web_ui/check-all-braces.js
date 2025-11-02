const fs = require('fs');

const problematicFiles = [
  'src/components/error-handling/ErrorBoundary.tsx',
  'src/components/plugins/DateTimePluginPage.tsx', 
  'src/components/settings/CopilotKitSettings.tsx',
  'src/components/settings/LLMSettings.tsx'
];

problematicFiles.forEach(filePath => {
  console.log(`\n=== Checking ${filePath} ===`);
  
  const content = fs.readFileSync(filePath, 'utf8');
  const lines = content.split('\n');
  
  let braceCount = 0;
  let inFunction = false;
  let functionStartLine = -1;
  let functionName = '';
  
  lines.forEach((line, index) => {
    const lineNum = index + 1;
    
    // Check for function start
    const functionMatch = line.match(/export\s+default\s+function\s+(\w+)/);
    if (functionMatch) {
      inFunction = true;
      functionStartLine = lineNum;
      functionName = functionMatch[1];
      console.log(`Function ${functionName} starts at line ${lineNum}`);
    }
    
    // Count braces
    for (const char of line) {
      if (char === '{') {
        braceCount++;
      }
      if (char === '}') {
        braceCount--;
        if (inFunction && braceCount === 0) {
          console.log(`Function ${functionName} ends at line ${lineNum}`);
          inFunction = false;
        }
      }
    }
    
    // Check for return statement
    if (line.trim().startsWith('return (') && !inFunction) {
      console.log(`ERROR: Return statement at line ${lineNum} is outside function!`);
    }
  });
  
  console.log(`Final brace count: ${braceCount}`);
  if (braceCount !== 0) {
    console.log(`WARNING: Unbalanced braces!`);
  }
});