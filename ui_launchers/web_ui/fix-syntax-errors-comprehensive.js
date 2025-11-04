#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// Files that have syntax errors based on the build output
const filesToFix = [
  'src/hooks/useProviderNotifications.ts',
  'src/lib/api-client.ts',
  'src/lib/connection/connection-manager.ts',
  'src/lib/enhanced-api-client.ts',
  'src/lib/error-handler.ts'
];

function fixSyntaxErrors() {
  filesToFix.forEach(filePath => {
    const fullPath = path.join(__dirname, filePath);
    if (!fs.existsSync(fullPath)) {
      console.log(`File not found: ${fullPath}`);
      return;
    }

    let content = fs.readFileSync(fullPath, 'utf8');
    let modified = false;

    // Common syntax error patterns and fixes
    const fixes = [
      // Missing closing bracket for function calls
      {
        pattern: /(\s+)(timeout:\s*\d+,\s*retryAttempts:\s*\d+,)\s*\n\s*return\s*\{/g,
        replacement: '$1$2\n$1});\n\n$1return {'
      },
      // Missing closing bracket for fetch calls
      {
        pattern: /(\s+)(credentials:\s*"include",)\s*\n\s*\}\s*catch/g,
        replacement: '$1$2\n$1});\n$1} catch'
      },
      // Missing closing bracket for object literals in console.log
      {
        pattern: /(\s+)(headers:\s*\{[^}]+\},)\s*\n\s*\}\)\s*;\s*\n\s*return\s*\{/g,
        replacement: '$1$2\n$1});\n\n$1return {'
      },
      // Missing closing bracket for error interceptor
      {
        pattern: /(\s+)(return\s+error;)\s*\n\s*\}\)\s*;\s*\n\s*\}\s*\n\s*\/\/\s*Add\s+request\s+interceptor/g,
        replacement: '$1$2\n$1});\n$1}\n\n$1// Add request interceptor'
      }
    ];

    fixes.forEach(fix => {
      const newContent = content.replace(fix.pattern, fix.replacement);
      if (newContent !== content) {
        content = newContent;
        modified = true;
        console.log(`Applied fix to ${filePath}`);
      }
    });

    if (modified) {
      fs.writeFileSync(fullPath, content);
      console.log(`Fixed syntax errors in ${filePath}`);
    } else {
      console.log(`No fixes applied to ${filePath}`);
    }
  });
}

fixSyntaxErrors();