#!/usr/bin/env node

/**
 * Console Error Health Check - Quick verification script
 */

const fs = require('fs');
const path = require('path');

function healthCheck() {
  console.log('🏥 Console Error Health Check\n');
  
  const checks = [];
  
  // Check 1: Layout has early script
  try {
    const layout = fs.readFileSync('ui_launchers/KAREN-Theme-Default/src/app/layout.tsx', 'utf8');
    const hasEarlyScript = layout.includes('console-error-fix') && layout.includes('beforeInteractive');
    checks.push({
      name: 'Early Console Fix Script',
      status: hasEarlyScript ? 'PASS' : 'FAIL',
      details: hasEarlyScript ? 'Script loads before Next.js hydration' : 'Missing early script in layout.tsx'
    });
  } catch (e) {
    checks.push({
      name: 'Early Console Fix Script',
      status: 'ERROR',
      details: 'Could not read layout.tsx'
    });
  }
  
  // Check 2: Safe console utilities exist
  try {
    const safeConsole = fs.readFileSync('ui_launchers/KAREN-Theme-Default/src/lib/safe-console.ts', 'utf8');
    const hasUtilities = safeConsole.includes('safeError') && safeConsole.includes('SafeConsole');
    checks.push({
      name: 'Safe Console Utilities',
      status: hasUtilities ? 'PASS' : 'FAIL',
      details: hasUtilities ? 'Safe console methods available' : 'Safe console utilities incomplete'
    });
  } catch (e) {
    checks.push({
      name: 'Safe Console Utilities',
      status: 'ERROR',
      details: 'Could not read safe-console.ts'
    });
  }
  
  // Check 3: Global console fix exists
  try {
    const consoleFix = fs.readFileSync('ui_launchers/KAREN-Theme-Default/src/lib/console-error-fix.ts', 'utf8');
    const hasGlobalFix = consoleFix.includes('initializeConsoleErrorFix') && 
                        consoleFix.includes('console-error.js');
    checks.push({
      name: 'Global Console Fix',
      status: hasGlobalFix ? 'PASS' : 'FAIL',
      details: hasGlobalFix ? 'Global interceptor override active' : 'Global fix incomplete'
    });
  } catch (e) {
    checks.push({
      name: 'Global Console Fix',
      status: 'ERROR',
      details: 'Could not read console-error-fix.ts'
    });
  }
  
  // Check 4: ChatInterface uses safe console
  try {
    const chatInterface = fs.readFileSync('ui_launchers/KAREN-Theme-Default/src/components/ChatInterface/ChatInterface.tsx', 'utf8');
    const usesSafeConsole = chatInterface.includes('safeError') &&
                           !chatInterface.includes('console.error(');
    checks.push({
      name: 'ChatInterface Safe Console',
      status: usesSafeConsole ? 'PASS' : 'WARN',
      details: usesSafeConsole ? 'ChatInterface uses safe console methods' : 'May still have direct console calls'
    });
  } catch (e) {
    checks.push({
      name: 'ChatInterface Safe Console',
      status: 'ERROR',
      details: 'Could not read ChatInterface.tsx'
    });
  }
  
  // Check 5: Error boundary exists
  try {
    const safeChatWrapper = fs.readFileSync('ui_launchers/KAREN-Theme-Default/src/components/chat/SafeChatWrapper.tsx', 'utf8');
    const hasErrorBoundary = safeChatWrapper.includes('componentDidCatch') && 
                            safeChatWrapper.includes('safeError');
    checks.push({
      name: 'Error Boundary',
      status: hasErrorBoundary ? 'PASS' : 'FAIL',
      details: hasErrorBoundary ? 'SafeChatWrapper error boundary active' : 'Error boundary incomplete'
    });
  } catch (e) {
    checks.push({
      name: 'Error Boundary',
      status: 'ERROR',
      details: 'Could not read SafeChatWrapper.tsx'
    });
  }
  
  // Check 6: Test component available
  try {
    const testComponent = fs.readFileSync('ui_launchers/KAREN-Theme-Default/src/components/chat/ChatInterfaceTest.tsx', 'utf8');
    const hasTestComponent = testComponent.includes('testConsoleError') && 
                            testComponent.includes('ChatInterfaceTest');
    checks.push({
      name: 'Test Component',
      status: hasTestComponent ? 'PASS' : 'FAIL',
      details: hasTestComponent ? 'ChatInterfaceTest component available' : 'Test component incomplete'
    });
  } catch (e) {
    checks.push({
      name: 'Test Component',
      status: 'ERROR',
      details: 'Could not read ChatInterfaceTest.tsx'
    });
  }
  
  // Display results
  console.log('📊 Health Check Results:\n');
  
  checks.forEach(check => {
    const icon = check.status === 'PASS' ? '✅' : 
                 check.status === 'WARN' ? '⚠️' : '❌';
    console.log(`${icon} ${check.name}: ${check.status}`);
    console.log(`   ${check.details}\n`);
  });
  
  // Summary
  const passed = checks.filter(c => c.status === 'PASS').length;
  const warned = checks.filter(c => c.status === 'WARN').length;
  const failed = checks.filter(c => c.status === 'FAIL').length;
  const errors = checks.filter(c => c.status === 'ERROR').length;
  
  console.log('📈 Summary:');
  console.log(`✅ Passed: ${passed}`);
  if (warned > 0) console.log(`⚠️  Warnings: ${warned}`);
  if (failed > 0) console.log(`❌ Failed: ${failed}`);
  if (errors > 0) console.log(`🚨 Errors: ${errors}`);
  
  const overallStatus = errors > 0 ? 'CRITICAL' :
                       failed > 0 ? 'NEEDS_ATTENTION' :
                       warned > 0 ? 'GOOD_WITH_WARNINGS' : 'EXCELLENT';
  
  console.log(`\n🎯 Overall Status: ${overallStatus}`);
  
  if (overallStatus === 'EXCELLENT') {
    console.log('\n🎉 All console error fixes are properly implemented!');
    console.log('   Your application should be protected from console interceptor issues.');
  } else if (overallStatus === 'GOOD_WITH_WARNINGS') {
    console.log('\n👍 Console error fixes are mostly implemented.');
    console.log('   Check warnings above for minor improvements.');
  } else {
    console.log('\n⚠️  Some console error fixes need attention.');
    console.log('   Review failed checks above and fix issues.');
  }
  
  console.log('\n🧪 Next Steps:');
  console.log('1. Run the application and test the ChatInterface');
  console.log('2. Use ChatInterfaceTest component to validate fixes');
  console.log('3. Monitor browser console for [SAFE] messages');
  console.log('4. Check for absence of console interceptor errors');
}

if (require.main === module) {
  healthCheck();
}