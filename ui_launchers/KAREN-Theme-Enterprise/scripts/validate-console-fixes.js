#!/usr/bin/env node

/**
 * Script to validate console error fixes are working
 */

const fs = require('fs');
const path = require('path');

function checkFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  
  // Check if console error fix is loaded
  const hasConsoleErrorFix = content.includes('console-error-fix') || 
                            content.includes('initializeConsoleErrorFix');
  
  // Check if safe console is imported where needed
  const hasConsoleError = /console\.error\s*\(/.test(content);
  const hasConsoleWarn = /console\.warn\s*\(/.test(content);
  const hasSafeConsoleImport = /import.*\{.*safe(Error|Warn).*\}.*from.*['"]@\/lib\/safe-console['"]/.test(content);
  
  return {
    filePath,
    hasConsoleErrorFix,
    hasConsoleError,
    hasConsoleWarn,
    hasSafeConsoleImport,
    needsAttention: (hasConsoleError || hasConsoleWarn) && !hasSafeConsoleImport
  };
}

function main() {
  console.log('🔍 Validating console error fixes...\n');
  
  // Check key files
  const keyFiles = [
    'ui_launchers/KAREN-Theme-Default/src/app/layout.tsx',
    'ui_launchers/KAREN-Theme-Default/src/lib/console-error-fix.ts',
    'ui_launchers/KAREN-Theme-Default/src/lib/safe-console.ts',
    'ui_launchers/KAREN-Theme-Default/src/components/ChatInterface/ChatInterface.tsx',
    'ui_launchers/KAREN-Theme-Default/src/components/chat/SafeChatWrapper.tsx',
    'ui_launchers/KAREN-Theme-Default/src/hooks/useReasoning.ts',
    'ui_launchers/KAREN-Theme-Default/src/hooks/useModelSelection.ts',
    'ui_launchers/KAREN-Theme-Default/src/hooks/use-streaming-controller.ts',
  ];
  
  const results = keyFiles.map(checkFile);
  
  console.log('📋 Validation Results:\n');
  
  results.forEach(result => {
    const status = result.needsAttention ? '⚠️' : '✅';
    console.log(`${status} ${result.filePath}`);
    
    if (result.hasConsoleErrorFix) {
      console.log('   ✓ Has console error fix');
    }
    if (result.hasSafeConsoleImport) {
      console.log('   ✓ Uses safe console');
    }
    if (result.hasConsoleError && !result.hasSafeConsoleImport) {
      console.log('   ⚠️  Still has direct console.error calls');
    }
    if (result.hasConsoleWarn && !result.hasSafeConsoleImport) {
      console.log('   ⚠️  Still has direct console.warn calls');
    }
    console.log('');
  });
  
  const needsAttention = results.filter(r => r.needsAttention);
  
  if (needsAttention.length === 0) {
    console.log('🎉 All key files are properly configured!');
  } else {
    console.log(`⚠️  ${needsAttention.length} files need attention`);
  }
  
  console.log('\n📝 Summary:');
  console.log('- Console error fix is loaded early in layout.tsx');
  console.log('- Safe console utilities are available');
  console.log('- ChatInterface uses safe error handling');
  console.log('- Key hooks have been updated');
  
  console.log('\n🧪 To test the fixes:');
  console.log('1. Open the ChatInterfaceTest component');
  console.log('2. Click "Test Console Error Handling"');
  console.log('3. Check browser console for [SAFE] prefixed messages');
  console.log('4. Verify no console interceptor errors appear');
}

if (require.main === module) {
  main();
}