#!/usr/bin/env node

/**
 * Assistive Technology Testing Script
 * 
 * This script provides guidance and automation for testing with actual assistive technologies
 * like screen readers, voice control, and keyboard navigation tools.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Colors for console output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

// Assistive technology test configurations
const assistiveTechTests = {
  screenReader: {
    name: 'Screen Reader Testing',
    description: 'Test with NVDA, JAWS, VoiceOver, or Orca',
    tools: {
      windows: ['NVDA (Free)', 'JAWS (Commercial)', 'Narrator (Built-in)'],
      mac: ['VoiceOver (Built-in)', 'NVDA (via Parallels/VM)'],
      linux: ['Orca (Free)', 'NVDA (via Wine)'],
    },
    testScenarios: [
      'Navigate through page structure using headings',
      'Navigate through forms using form mode',
      'Navigate through tables using table navigation',
      'Test ARIA live regions and announcements',
      'Test focus management in modals and dialogs',
      'Test skip links and landmarks',
      'Verify all interactive elements are announced',
      'Test keyboard shortcuts and hotkeys',
    ],
    automatedChecks: [
      'All images have alt text or are marked decorative',
      'All form controls have labels',
      'All buttons have accessible names',
      'All links have descriptive text',
      'Proper heading hierarchy exists',
      'ARIA attributes are used correctly',
      'Live regions are properly configured',
    ],
  },
  
  keyboardNavigation: {
    name: 'Keyboard Navigation Testing',
    description: 'Test keyboard-only navigation and interaction',
    tools: {
      all: ['Built-in keyboard', 'On-screen keyboard', 'Switch devices'],
    },
    testScenarios: [
      'Tab through all interactive elements',
      'Use arrow keys for complex widgets',
      'Test Enter and Space key activation',
      'Test Escape key for closing dialogs',
      'Navigate menus with arrow keys',
      'Test keyboard shortcuts',
      'Verify focus indicators are visible',
      'Test focus trapping in modals',
    ],
    automatedChecks: [
      'All interactive elements are focusable',
      'Focus order is logical',
      'Focus indicators are visible',
      'No keyboard traps exist',
      'Skip links work properly',
      'Keyboard shortcuts don\'t conflict',
    ],
  },
  
  voiceControl: {
    name: 'Voice Control Testing',
    description: 'Test with voice control software',
    tools: {
      windows: ['Dragon NaturallySpeaking', 'Windows Speech Recognition'],
      mac: ['Voice Control (Built-in)', 'Dragon for Mac'],
      linux: ['Simon (Open source)', 'Julius (Open source)'],
    },
    testScenarios: [
      'Navigate using voice commands',
      'Activate buttons and links by name',
      'Fill out forms using voice input',
      'Navigate through lists and menus',
      'Test custom voice commands',
      'Verify all interactive elements are voice-accessible',
    ],
    automatedChecks: [
      'All interactive elements have accessible names',
      'Button and link text is descriptive',
      'Form labels are clear and unique',
      'No duplicate accessible names exist',
    ],
  },
  
  magnification: {
    name: 'Screen Magnification Testing',
    description: 'Test with screen magnification tools',
    tools: {
      windows: ['Windows Magnifier', 'ZoomText', 'MAGic'],
      mac: ['Zoom (Built-in)', 'ZoomText for Mac'],
      linux: ['Kmag', 'Virtual Magnifying Glass'],
    },
    testScenarios: [
      'Test at 200% magnification',
      'Test at 400% magnification',
      'Verify content reflows properly',
      'Test focus tracking with magnification',
      'Verify tooltips and popups are visible',
      'Test scrolling behavior',
    ],
    automatedChecks: [
      'Content is responsive to zoom',
      'Text doesn\'t get cut off',
      'Interactive elements remain accessible',
      'Focus indicators scale properly',
    ],
  },
};

// Test report template
const reportTemplate = {
  testDate: new Date().toISOString(),
  tester: '',
  assistiveTechnology: '',
  version: '',
  operatingSystem: '',
  browser: '',
  testResults: [],
  overallRating: '',
  criticalIssues: [],
  recommendations: [],
};

function generateTestReport(testType, results) {
  const report = { ...reportTemplate };
  report.assistiveTechnology = testType;
  report.testResults = results;
  
  const reportPath = path.join(__dirname, '..', 'reports', `assistive-tech-${testType}-${Date.now()}.json`);
  
  // Ensure reports directory exists
  const reportsDir = path.dirname(reportPath);
  if (!fs.existsSync(reportsDir)) {
    fs.mkdirSync(reportsDir, { recursive: true });
  }
  
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  log(`Test report saved to: ${reportPath}`, 'green');
  
  return reportPath;
}

function displayTestInstructions(testType) {
  const test = assistiveTechTests[testType];
  if (!test) {
    log(`Unknown test type: ${testType}`, 'red');
    return;
  }
  
  log(`\n${test.name}`, 'bright');
  log('='.repeat(test.name.length), 'bright');
  log(`\n${test.description}\n`, 'cyan');
  
  log('Available Tools:', 'yellow');
  Object.entries(test.tools).forEach(([platform, tools]) => {
    log(`  ${platform.toUpperCase()}:`, 'magenta');
    tools.forEach(tool => log(`    - ${tool}`, 'reset'));
  });
  
  log('\nTest Scenarios:', 'yellow');
  test.testScenarios.forEach((scenario, index) => {
    log(`  ${index + 1}. ${scenario}`, 'reset');
  });
  
  log('\nAutomated Checks:', 'yellow');
  test.automatedChecks.forEach((check, index) => {
    log(`  ${index + 1}. ${check}`, 'reset');
  });
  
  log('\nTesting Instructions:', 'bright');
  log('1. Start your development server: npm run dev', 'reset');
  log('2. Open your assistive technology tool', 'reset');
  log('3. Navigate to http://localhost:8000', 'reset');
  log('4. Follow the test scenarios above', 'reset');
  log('5. Document any issues found', 'reset');
  log('6. Run automated checks with: npm run test:accessibility', 'reset');
}

function runAutomatedAccessibilityTests() {
  log('\nRunning automated accessibility tests...', 'yellow');
  
  try {
    // Run the accessibility test suite
    execSync('npm run test -- --run src/__tests__/accessibility/', { 
      stdio: 'inherit',
      cwd: process.cwd()
    });
    
    log('\nAutomated accessibility tests completed!', 'green');
  } catch (error) {
    log('\nAutomated accessibility tests failed!', 'red');
    log(error.message, 'red');
  }
}

function generateAccessibilityChecklist() {
  const checklist = {
    'Keyboard Navigation': [
      '☐ All interactive elements are keyboard accessible',
      '☐ Tab order is logical and intuitive',
      '☐ Focus indicators are clearly visible',
      '☐ No keyboard traps exist',
      '☐ Skip links are present and functional',
      '☐ Keyboard shortcuts work as expected',
      '☐ Arrow key navigation works in complex widgets',
      '☐ Enter and Space keys activate buttons',
      '☐ Escape key closes modals and menus',
    ],
    
    'Screen Reader': [
      '☐ All content is announced correctly',
      '☐ Headings create a logical structure',
      '☐ All images have appropriate alt text',
      '☐ Form controls have clear labels',
      '☐ Error messages are announced',
      '☐ Status updates are announced via live regions',
      '☐ Tables have proper headers and captions',
      '☐ Lists are properly structured',
      '☐ Landmarks help with navigation',
    ],
    
    'Visual Design': [
      '☐ Color contrast meets WCAG AA standards',
      '☐ Text is readable at 200% zoom',
      '☐ Focus indicators have sufficient contrast',
      '☐ Information is not conveyed by color alone',
      '☐ Text spacing can be adjusted',
      '☐ Content reflows at different zoom levels',
    ],
    
    'Forms': [
      '☐ All form controls have labels',
      '☐ Required fields are clearly marked',
      '☐ Error messages are descriptive and helpful',
      '☐ Form validation is accessible',
      '☐ Fieldsets and legends are used appropriately',
      '☐ Help text is associated with form controls',
    ],
    
    'Interactive Elements': [
      '☐ Buttons have descriptive text or labels',
      '☐ Links have meaningful link text',
      '☐ Interactive elements have appropriate roles',
      '☐ State changes are communicated',
      '☐ Loading states are announced',
      '☐ Progress indicators are accessible',
    ],
    
    'Content Structure': [
      '☐ Page has a descriptive title',
      '☐ Language is specified',
      '☐ Heading hierarchy is logical',
      '☐ Content is organized with landmarks',
      '☐ Lists are used for grouped content',
      '☐ Tables are used for tabular data only',
    ],
  };
  
  log('\nAccessibility Testing Checklist', 'bright');
  log('='.repeat(32), 'bright');
  
  Object.entries(checklist).forEach(([category, items]) => {
    log(`\n${category}:`, 'yellow');
    items.forEach(item => log(`  ${item}`, 'reset'));
  });
  
  // Save checklist to file
  const checklistPath = path.join(__dirname, '..', 'docs', 'accessibility-checklist.md');
  let markdownContent = '# Accessibility Testing Checklist\n\n';
  
  Object.entries(checklist).forEach(([category, items]) => {
    markdownContent += `## ${category}\n\n`;
    items.forEach(item => markdownContent += `${item}\n`);
    markdownContent += '\n';
  });
  
  // Ensure docs directory exists
  const docsDir = path.dirname(checklistPath);
  if (!fs.existsSync(docsDir)) {
    fs.mkdirSync(docsDir, { recursive: true });
  }
  
  fs.writeFileSync(checklistPath, markdownContent);
  log(`\nChecklist saved to: ${checklistPath}`, 'green');
}

function showUsage() {
  log('\nAssistive Technology Testing Script', 'bright');
  log('Usage: node scripts/assistive-technology-test.js [command] [options]', 'cyan');
  
  log('\nCommands:', 'yellow');
  log('  screen-reader    Show screen reader testing instructions', 'reset');
  log('  keyboard         Show keyboard navigation testing instructions', 'reset');
  log('  voice-control    Show voice control testing instructions', 'reset');
  log('  magnification    Show screen magnification testing instructions', 'reset');
  log('  automated        Run automated accessibility tests', 'reset');
  log('  checklist        Generate accessibility testing checklist', 'reset');
  log('  all              Show all testing instructions', 'reset');
  log('  help             Show this help message', 'reset');
  
  log('\nExamples:', 'yellow');
  log('  node scripts/assistive-technology-test.js screen-reader', 'reset');
  log('  node scripts/assistive-technology-test.js automated', 'reset');
  log('  node scripts/assistive-technology-test.js checklist', 'reset');
}

// Main execution
function main() {
  const command = process.argv[2];
  
  switch (command) {
    case 'screen-reader':
      displayTestInstructions('screenReader');
      break;
      
    case 'keyboard':
      displayTestInstructions('keyboardNavigation');
      break;
      
    case 'voice-control':
      displayTestInstructions('voiceControl');
      break;
      
    case 'magnification':
      displayTestInstructions('magnification');
      break;
      
    case 'automated':
      runAutomatedAccessibilityTests();
      break;
      
    case 'checklist':
      generateAccessibilityChecklist();
      break;
      
    case 'all':
      Object.keys(assistiveTechTests).forEach(testType => {
        displayTestInstructions(testType);
        log('\n' + '='.repeat(80) + '\n', 'bright');
      });
      break;
      
    case 'help':
    case '--help':
    case '-h':
      showUsage();
      break;
      
    default:
      if (command) {
        log(`Unknown command: ${command}`, 'red');
      }
      showUsage();
      break;
  }
}

// Run the script
if (require.main === module) {
  main();
}

module.exports = {
  assistiveTechTests,
  generateTestReport,
  displayTestInstructions,
  runAutomatedAccessibilityTests,
  generateAccessibilityChecklist,
};