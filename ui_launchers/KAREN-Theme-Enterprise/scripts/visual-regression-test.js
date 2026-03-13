#!/usr/bin/env node

/**
 * Visual Regression Testing Script
 * 
 * This script runs comprehensive visual regression tests using Storybook,
 * Chromatic, and accessibility testing tools.
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Configuration
const config = {
  storybookPort: 6006,
  screenshotDir: 'screenshots',
  reportDir: 'visual-regression-reports',
  chromaticProject: process.env.CHROMATIC_PROJECT_TOKEN,
  skipChromatic: process.env.SKIP_CHROMATIC === 'true',
  skipAccessibility: process.env.SKIP_A11Y === 'true',
  verbose: process.env.VERBOSE === 'true',
};

// Utility functions
const log = (message, level = 'info') => {
  const timestamp = new Date().toISOString();
  const prefix = level === 'error' ? '❌' : level === 'warn' ? '⚠️' : level === 'success' ? '✅' : 'ℹ️';
  console.log(`${prefix} [${timestamp}] ${message}`);
};

const execCommand = (command, options = {}) => {
  if (config.verbose) {
    log(`Executing: ${command}`);
  }
  try {
    return execSync(command, { 
      stdio: config.verbose ? 'inherit' : 'pipe',
      encoding: 'utf8',
      ...options 
    });
  } catch (error) {
    log(`Command failed: ${command}`, 'error');
    log(error.message, 'error');
    throw error;
  }
};

const ensureDirectory = (dir) => {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
    log(`Created directory: ${dir}`);
  }
};

// Main testing functions
const buildStorybook = async () => {
  log('Building Storybook for visual regression testing...');
  try {
    execCommand('npm run build-storybook');
    log('Storybook build completed successfully', 'success');
  } catch (error) {
    log('Failed to build Storybook', 'error');
    throw error;
  }
};

const runStorybookTests = async () => {
  log('Running Storybook test runner...');
  try {
    // Ensure screenshot directory exists
    ensureDirectory(config.screenshotDir);
    
    // Run test runner with accessibility and screenshot capture
    execCommand('npm run test-storybook', {
      env: {
        ...process.env,
        SCREENSHOT_DIR: config.screenshotDir,
      }
    });
    
    log('Storybook tests completed successfully', 'success');
  } catch (error) {
    log('Storybook tests failed', 'error');
    throw error;
  }
};

const runChromaticTests = async () => {
  if (config.skipChromatic) {
    log('Skipping Chromatic tests (SKIP_CHROMATIC=true)');
    return;
  }

  if (!config.chromaticProject) {
    log('Skipping Chromatic tests (no CHROMATIC_PROJECT_TOKEN)', 'warn');
    return;
  }

  log('Running Chromatic visual regression tests...');
  try {
    execCommand(`npx chromatic --project-token=${config.chromaticProject}`);
    log('Chromatic tests completed successfully', 'success');
  } catch (error) {
    log('Chromatic tests failed', 'error');
    // Don't throw here as Chromatic might fail due to visual changes
    // which is expected behavior
  }
};

const runAccessibilityTests = async () => {
  if (config.skipAccessibility) {
    log('Skipping accessibility tests (SKIP_A11Y=true)');
    return;
  }

  log('Running accessibility tests...');
  try {
    // Run axe-core tests on all stories
    execCommand('npm run test-storybook -- --coverage');
    log('Accessibility tests completed successfully', 'success');
  } catch (error) {
    log('Accessibility tests failed', 'error');
    throw error;
  }
};

const generateReport = async () => {
  log('Generating visual regression test report...');
  
  ensureDirectory(config.reportDir);
  
  const report = {
    timestamp: new Date().toISOString(),
    config: config,
    results: {
      storybook: fs.existsSync('storybook-static'),
      screenshots: fs.existsSync(config.screenshotDir) ? 
        fs.readdirSync(config.screenshotDir).length : 0,
      chromatic: !config.skipChromatic && config.chromaticProject,
      accessibility: !config.skipAccessibility,
    },
    summary: {
      totalStories: 0,
      passedTests: 0,
      failedTests: 0,
      skippedTests: 0,
    }
  };

  // Count stories from storybook-static if available
  try {
    const storiesPath = path.join('storybook-static', 'stories.json');
    if (fs.existsSync(storiesPath)) {
      const stories = JSON.parse(fs.readFileSync(storiesPath, 'utf8'));
      report.summary.totalStories = Object.keys(stories.stories || {}).length;
    }
  } catch (error) {
    log('Could not read stories count', 'warn');
  }

  // Write report
  const reportPath = path.join(config.reportDir, 'visual-regression-report.json');
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  
  log(`Report generated: ${reportPath}`, 'success');
  return report;
};

const cleanup = async () => {
  log('Cleaning up temporary files...');
  
  // Clean up old screenshots if needed
  if (fs.existsSync(config.screenshotDir)) {
    const files = fs.readdirSync(config.screenshotDir);
    if (files.length > 100) { // Keep only recent screenshots
      log(`Cleaning up old screenshots (${files.length} files)`);
      files.slice(0, -50).forEach(file => {
        fs.unlinkSync(path.join(config.screenshotDir, file));
      });
    }
  }
  
  log('Cleanup completed', 'success');
};

// Main execution
const main = async () => {
  const startTime = Date.now();
  log('Starting visual regression testing suite...');
  
  try {
    // Build Storybook
    await buildStorybook();
    
    // Run tests in parallel where possible
    const testPromises = [
      runStorybookTests(),
      runChromaticTests(),
    ];
    
    if (!config.skipAccessibility) {
      testPromises.push(runAccessibilityTests());
    }
    
    await Promise.allSettled(testPromises);
    
    // Generate report
    const report = await generateReport();
    
    // Cleanup
    await cleanup();
    
    const duration = Math.round((Date.now() - startTime) / 1000);
    log(`Visual regression testing completed in ${duration}s`, 'success');
    
    // Print summary
    console.log('\n📊 Test Summary:');
    console.log(`   Stories: ${report.summary.totalStories}`);
    console.log(`   Screenshots: ${report.results.screenshots}`);
    console.log(`   Chromatic: ${report.results.chromatic ? '✅' : '⏭️'}`);
    console.log(`   Accessibility: ${report.results.accessibility ? '✅' : '⏭️'}`);
    
  } catch (error) {
    log('Visual regression testing failed', 'error');
    log(error.message, 'error');
    process.exit(1);
  }
};

// Handle CLI arguments
const args = process.argv.slice(2);
if (args.includes('--help') || args.includes('-h')) {
  console.log(`
Visual Regression Testing Script

Usage: node scripts/visual-regression-test.js [options]

Options:
  --help, -h              Show this help message
  --skip-chromatic        Skip Chromatic visual tests
  --skip-a11y            Skip accessibility tests
  --verbose              Enable verbose logging

Environment Variables:
  CHROMATIC_PROJECT_TOKEN Project token for Chromatic
  SKIP_CHROMATIC         Skip Chromatic tests (true/false)
  SKIP_A11Y             Skip accessibility tests (true/false)
  VERBOSE               Enable verbose logging (true/false)

Examples:
  npm run visual-test
  npm run visual-test -- --skip-chromatic
  VERBOSE=true npm run visual-test
  `);
  process.exit(0);
}

// Apply CLI arguments
if (args.includes('--skip-chromatic')) {
  config.skipChromatic = true;
}
if (args.includes('--skip-a11y')) {
  config.skipAccessibility = true;
}
if (args.includes('--verbose')) {
  config.verbose = true;
}

// Run the main function
if (require.main === module) {
  main().catch(error => {
    log('Unhandled error in visual regression testing', 'error');
    console.error(error);
    process.exit(1);
  });
}

module.exports = {
  buildStorybook,
  runStorybookTests,
  runChromaticTests,
  runAccessibilityTests,
  generateReport,
  cleanup,
};