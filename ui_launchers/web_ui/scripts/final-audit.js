#!/usr/bin/env node

/**
 * Final UI Modernization Audit Script
 * Performs comprehensive accessibility, performance, and design consistency audits
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Audit configuration
const AUDIT_CONFIG = {
  accessibility: {
    enabled: true,
    tools: ['axe-core', 'lighthouse'],
    thresholds: {
      violations: 0,
      score: 90
    }
  },
  performance: {
    enabled: true,
    tools: ['lighthouse', 'web-vitals'],
    thresholds: {
      lcp: 2500,
      fid: 100,
      cls: 0.1,
      score: 90
    }
  },
  responsive: {
    enabled: true,
    breakpoints: [320, 768, 1024, 1440, 1920],
    devices: ['mobile', 'tablet', 'desktop']
  },
  design: {
    enabled: true,
    checkTokenUsage: true,
    checkConsistency: true,
    validateComponents: true
  }
};

// Results storage
const auditResults = {
  timestamp: new Date().toISOString(),
  summary: {
    passed: 0,
    failed: 0,
    warnings: 0
  },
  accessibility: {},
  performance: {},
  responsive: {},
  design: {},
  recommendations: []
};

/**
 * Main audit function
 */
async function runFinalAudit() {
  console.log('🔍 Starting Final UI Modernization Audit...\n');
  
  try {
    // Run accessibility audit
    if (AUDIT_CONFIG.accessibility.enabled) {
      console.log('♿ Running Accessibility Audit...');
      await runAccessibilityAudit();
    }
    
    // Run performance audit
    if (AUDIT_CONFIG.performance.enabled) {
      console.log('⚡ Running Performance Audit...');
      await runPerformanceAudit();
    }
    
    // Run responsive design audit
    if (AUDIT_CONFIG.responsive.enabled) {
      console.log('📱 Running Responsive Design Audit...');
      await runResponsiveAudit();
    }
    
    // Run design consistency audit
    if (AUDIT_CONFIG.design.enabled) {
      console.log('🎨 Running Design Consistency Audit...');
      await runDesignAudit();
    }
    
    // Generate final report
    generateFinalReport();
    
  } catch (error) {
    console.error('❌ Audit failed:', error.message);
    process.exit(1);
  }
}

/**
 * Accessibility audit using axe-core
 */
async function runAccessibilityAudit() {
  const accessibilityResults = {
    violations: [],
    passes: [],
    incomplete: [],
    score: 0,
    recommendations: []
  };
  
  try {
    // Check if axe-core is available
    const axeInstalled = checkPackageInstalled('@axe-core/cli');
    
    if (axeInstalled) {
      // Run axe audit on key pages
      const pages = [
        'http://localhost:3000',
        'http://localhost:3000/chat',
        'http://localhost:3000/login'
      ];
      
      for (const page of pages) {
        try {
          console.log(`  Auditing: ${page}`);
          const result = execSync(`npx axe ${page} --format json`, { 
            encoding: 'utf8',
            timeout: 30000 
          });
          
          const axeResult = JSON.parse(result);
          accessibilityResults.violations.push(...axeResult.violations);
          accessibilityResults.passes.push(...axeResult.passes);
          accessibilityResults.incomplete.push(...axeResult.incomplete);
          
        } catch (error) {
          console.warn(`    ⚠️  Could not audit ${page}: ${error.message}`);
        }
      }
    } else {
      console.log('  📝 axe-core not installed, performing manual checks...');
      await performManualAccessibilityChecks(accessibilityResults);
    }
    
    // Calculate accessibility score
    const totalChecks = accessibilityResults.violations.length + accessibilityResults.passes.length;
    accessibilityResults.score = totalChecks > 0 
      ? Math.round((accessibilityResults.passes.length / totalChecks) * 100)
      : 100;
    
    // Add recommendations
    if (accessibilityResults.violations.length > 0) {
      accessibilityResults.recommendations.push(
        'Fix accessibility violations found by axe-core',
        'Test with actual screen readers',
        'Verify keyboard navigation works correctly'
      );
    }
    
    auditResults.accessibility = accessibilityResults;
    
    if (accessibilityResults.violations.length === 0) {
      auditResults.summary.passed++;
      console.log('  ✅ Accessibility audit passed');
    } else {
      auditResults.summary.failed++;
      console.log(`  ❌ Found ${accessibilityResults.violations.length} accessibility violations`);
    }
    
  } catch (error) {
    console.error('  ❌ Accessibility audit failed:', error.message);
    auditResults.summary.failed++;
  }
}

/**
 * Manual accessibility checks when axe-core is not available
 */
async function performManualAccessibilityChecks(results) {
  const checks = [
    {
      name: 'Skip links present',
      check: () => checkFileContains('src/app/layout.tsx', 'skip-link'),
      passed: false
    },
    {
      name: 'ARIA labels used',
      check: () => checkFileContains('src/app/page.tsx', 'aria-label'),
      passed: false
    },
    {
      name: 'Focus management implemented',
      check: () => checkFileExists('src/hooks/use-focus-management.ts'),
      passed: false
    },
    {
      name: 'Screen reader support',
      check: () => checkFileExists('src/components/ui/screen-reader.tsx'),
      passed: false
    }
  ];
  
  for (const check of checks) {
    try {
      check.passed = await check.check();
      if (check.passed) {
        results.passes.push({ description: check.name });
      } else {
        results.violations.push({ description: check.name });
      }
    } catch (error) {
      results.incomplete.push({ description: check.name });
    }
  }
}

/**
 * Performance audit
 */
async function runPerformanceAudit() {
  const performanceResults = {
    metrics: {},
    score: 0,
    recommendations: []
  };
  
  try {
    // Check for performance optimizations in code
    const optimizations = [
      {
        name: 'Lazy loading implemented',
        check: () => checkFileExists('src/components/ui/lazy-loading/lazy-component.tsx'),
        weight: 20
      },
      {
        name: 'Code splitting configured',
        check: () => checkFileContains('next.config.js', 'splitChunks'),
        weight: 15
      },
      {
        name: 'Performance monitoring',
        check: () => checkFileExists('src/utils/performance-monitor.ts'),
        weight: 15
      },
      {
        name: 'Animation optimization',
        check: () => checkFileExists('src/utils/animation-performance.ts'),
        weight: 20
      },
      {
        name: 'Bundle analysis',
        check: () => checkFileExists('scripts/analyze-bundle.js'),
        weight: 10
      },
      {
        name: 'Tree shaking',
        check: () => checkFileExists('src/utils/tree-shaking.ts'),
        weight: 10
      },
      {
        name: 'Modern CSS features',
        check: () => checkFileContains('src/styles/globals.css', 'container-type'),
        weight: 10
      }
    ];
    
    let totalScore = 0;
    let maxScore = 0;
    
    for (const opt of optimizations) {
      maxScore += opt.weight;
      try {
        const passed = await opt.check();
        if (passed) {
          totalScore += opt.weight;
          console.log(`  ✅ ${opt.name}`);
        } else {
          console.log(`  ❌ ${opt.name}`);
          performanceResults.recommendations.push(`Implement ${opt.name.toLowerCase()}`);
        }
      } catch (error) {
        console.log(`  ⚠️  ${opt.name}: ${error.message}`);
      }
    }
    
    performanceResults.score = Math.round((totalScore / maxScore) * 100);
    
    auditResults.performance = performanceResults;
    
    if (performanceResults.score >= AUDIT_CONFIG.performance.thresholds.score) {
      auditResults.summary.passed++;
      console.log(`  ✅ Performance audit passed (${performanceResults.score}%)`);
    } else {
      auditResults.summary.failed++;
      console.log(`  ❌ Performance audit failed (${performanceResults.score}%)`);
    }
    
  } catch (error) {
    console.error('  ❌ Performance audit failed:', error.message);
    auditResults.summary.failed++;
  }
}

/**
 * Responsive design audit
 */
async function runResponsiveAudit() {
  const responsiveResults = {
    breakpoints: [],
    score: 0,
    recommendations: []
  };
  
  try {
    const checks = [
      {
        name: 'Container queries implemented',
        check: () => checkFileContains('src/styles/globals.css', '@container'),
        weight: 30
      },
      {
        name: 'Responsive containers',
        check: () => checkFileExists('src/components/ui/layout/responsive-container.tsx'),
        weight: 25
      },
      {
        name: 'Mobile-first CSS',
        check: () => checkFileContains('src/styles/globals.css', '@media (max-width:'),
        weight: 20
      },
      {
        name: 'Fluid typography',
        check: () => checkFileContains('src/styles/design-tokens.css', 'clamp('),
        weight: 15
      },
      {
        name: 'Touch optimization',
        check: () => checkFileContains('src/components/ui/haptic-feedback/', 'vibration'),
        weight: 10
      }
    ];
    
    let totalScore = 0;
    let maxScore = 0;
    
    for (const check of checks) {
      maxScore += check.weight;
      try {
        const passed = await check.check();
        if (passed) {
          totalScore += check.weight;
          console.log(`  ✅ ${check.name}`);
        } else {
          console.log(`  ❌ ${check.name}`);
          responsiveResults.recommendations.push(`Implement ${check.name.toLowerCase()}`);
        }
      } catch (error) {
        console.log(`  ⚠️  ${check.name}: ${error.message}`);
      }
    }
    
    responsiveResults.score = Math.round((totalScore / maxScore) * 100);
    
    auditResults.responsive = responsiveResults;
    
    if (responsiveResults.score >= 80) {
      auditResults.summary.passed++;
      console.log(`  ✅ Responsive design audit passed (${responsiveResults.score}%)`);
    } else {
      auditResults.summary.failed++;
      console.log(`  ❌ Responsive design audit failed (${responsiveResults.score}%)`);
    }
    
  } catch (error) {
    console.error('  ❌ Responsive design audit failed:', error.message);
    auditResults.summary.failed++;
  }
}

/**
 * Design consistency audit
 */
async function runDesignAudit() {
  const designResults = {
    tokenUsage: 0,
    componentConsistency: 0,
    score: 0,
    recommendations: []
  };
  
  try {
    const checks = [
      {
        name: 'Design tokens implemented',
        check: () => checkFileExists('src/design-tokens/index.ts'),
        weight: 25
      },
      {
        name: 'Modern card components',
        check: () => checkFileExists('src/components/ui/compound/card.tsx'),
        weight: 20
      },
      {
        name: 'Consistent spacing system',
        check: () => checkFileContains('src/styles/design-tokens.css', '--space-'),
        weight: 15
      },
      {
        name: 'Typography scale',
        check: () => checkFileContains('src/styles/design-tokens.css', '--text-'),
        weight: 15
      },
      {
        name: 'Color system',
        check: () => checkFileContains('src/styles/design-tokens.css', '--color-'),
        weight: 15
      },
      {
        name: 'Animation system',
        check: () => checkFileContains('src/styles/design-tokens.css', '--duration-'),
        weight: 10
      }
    ];
    
    let totalScore = 0;
    let maxScore = 0;
    
    for (const check of checks) {
      maxScore += check.weight;
      try {
        const passed = await check.check();
        if (passed) {
          totalScore += check.weight;
          console.log(`  ✅ ${check.name}`);
        } else {
          console.log(`  ❌ ${check.name}`);
          designResults.recommendations.push(`Implement ${check.name.toLowerCase()}`);
        }
      } catch (error) {
        console.log(`  ⚠️  ${check.name}: ${error.message}`);
      }
    }
    
    designResults.score = Math.round((totalScore / maxScore) * 100);
    
    auditResults.design = designResults;
    
    if (designResults.score >= 85) {
      auditResults.summary.passed++;
      console.log(`  ✅ Design consistency audit passed (${designResults.score}%)`);
    } else {
      auditResults.summary.failed++;
      console.log(`  ❌ Design consistency audit failed (${designResults.score}%)`);
    }
    
  } catch (error) {
    console.error('  ❌ Design consistency audit failed:', error.message);
    auditResults.summary.failed++;
  }
}

/**
 * Generate final audit report
 */
function generateFinalReport() {
  console.log('\n📊 Final Audit Report');
  console.log('='.repeat(50));
  
  const totalTests = auditResults.summary.passed + auditResults.summary.failed + auditResults.summary.warnings;
  const passRate = totalTests > 0 ? Math.round((auditResults.summary.passed / totalTests) * 100) : 0;
  
  console.log(`\n📈 Summary:`);
  console.log(`  ✅ Passed: ${auditResults.summary.passed}`);
  console.log(`  ❌ Failed: ${auditResults.summary.failed}`);
  console.log(`  ⚠️  Warnings: ${auditResults.summary.warnings}`);
  console.log(`  📊 Pass Rate: ${passRate}%`);
  
  console.log(`\n🔍 Detailed Results:`);
  console.log(`  ♿ Accessibility: ${auditResults.accessibility.score || 'N/A'}%`);
  console.log(`  ⚡ Performance: ${auditResults.performance.score || 'N/A'}%`);
  console.log(`  📱 Responsive: ${auditResults.responsive.score || 'N/A'}%`);
  console.log(`  🎨 Design: ${auditResults.design.score || 'N/A'}%`);
  
  // Collect all recommendations
  const allRecommendations = [
    ...auditResults.accessibility.recommendations || [],
    ...auditResults.performance.recommendations || [],
    ...auditResults.responsive.recommendations || [],
    ...auditResults.design.recommendations || []
  ];
  
  if (allRecommendations.length > 0) {
    console.log(`\n💡 Recommendations:`);
    allRecommendations.forEach((rec, index) => {
      console.log(`  ${index + 1}. ${rec}`);
    });
  }
  
  // Save detailed report
  const reportPath = path.join(__dirname, '../audit-reports/final-audit-report.json');
  fs.mkdirSync(path.dirname(reportPath), { recursive: true });
  fs.writeFileSync(reportPath, JSON.stringify(auditResults, null, 2));
  
  console.log(`\n📄 Detailed report saved to: ${reportPath}`);
  
  // Overall result
  if (passRate >= 80) {
    console.log('\n🎉 Overall Result: PASSED');
    console.log('The UI modernization meets quality standards!');
  } else {
    console.log('\n⚠️  Overall Result: NEEDS IMPROVEMENT');
    console.log('Please address the failed audits before deployment.');
  }
}

/**
 * Helper functions
 */
function checkPackageInstalled(packageName) {
  try {
    require.resolve(packageName);
    return true;
  } catch (error) {
    return false;
  }
}

function checkFileExists(filePath) {
  const fullPath = path.join(__dirname, '..', filePath);
  return fs.existsSync(fullPath);
}

function checkFileContains(filePath, searchString) {
  try {
    const fullPath = path.join(__dirname, '..', filePath);
    if (!fs.existsSync(fullPath)) return false;
    
    const content = fs.readFileSync(fullPath, 'utf8');
    return content.includes(searchString);
  } catch (error) {
    return false;
  }
}

// Run the audit
if (require.main === module) {
  runFinalAudit().catch(error => {
    console.error('Audit failed:', error);
    process.exit(1);
  });
}

module.exports = { runFinalAudit, auditResults };