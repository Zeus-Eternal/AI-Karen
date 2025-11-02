#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// List of files with known syntax errors
const filesToFix = [
  'src/components/ChatInterface/hooks/useChatMessages.ts',
  'src/components/ChatInterface/hooks/useChatSettings.ts',
  'src/components/ChatInterface/hooks/useChatState.ts',
  'src/components/ChatInterface/utils/copilotUtils.ts',
  'src/components/ChatInterface/utils/exportUtils.ts',
  'src/components/auth/UserProfile.tsx',
  'src/components/chat/copilot/CopilotKitProvider.tsx'
];

function fixSyntaxErrors() {
  filesToFix.forEach(filePath => {
    if (!fs.existsSync(filePath)) {
      console.log(`File not found: ${filePath}`);
      return;
    }

    let content = fs.readFileSync(filePath, 'utf8');
    let modified = false;

    // Common fixes
    const fixes = [
      // Fix missing closing braces for function calls
      { pattern: /(\s+)(safeDebug\([^}]+)\n(\s+)([^}])/g, replacement: '$1$2\n$3});$1$4' },
      { pattern: /(\s+)(safeError\([^}]+)\n(\s+)([^}])/g, replacement: '$1$2\n$3});$1$4' },
      { pattern: /(\s+)(safeWarn\([^}]+)\n(\s+)([^}])/g, replacement: '$1$2\n$3});$1$4' },
      
      // Fix missing closing braces for objects
      { pattern: /(\s+)(\w+:\s*[^,}]+),?\n\n(\s+)([a-zA-Z])/g, replacement: '$1$2\n$3});\n\n$3$4' },
      
      // Fix missing closing parentheses
      { pattern: /(\s+)(\.sort\([^}]+)\n(\s+)([^}])/g, replacement: '$1$2\n$3});\n\n$3$4' },
      
      // Fix missing semicolons in object literals
      { pattern: /(\s+)(\w+:\s*[^,}]+)\n\n(\s+)([a-zA-Z])/g, replacement: '$1$2,\n$3});\n\n$3$4' }
    ];

    fixes.forEach(fix => {
      const newContent = content.replace(fix.pattern, fix.replacement);
      if (newContent !== content) {
        content = newContent;
        modified = true;
      }
    });

    if (modified) {
      fs.writeFileSync(filePath, content);
      console.log(`Fixed syntax errors in: ${filePath}`);
    } else {
      console.log(`No automatic fixes applied to: ${filePath}`);
    }
  });
}

fixSyntaxErrors();