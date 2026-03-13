/**
 * Performance Analysis Script for KAREN AI
 * Analyzes bundle size, performance metrics, and optimization opportunities
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const chalk = require('chalk');

// Configuration
const CONFIG = {
  maxBundleSize: {
    js: 244 * 1024, // 244KB gzipped
    css: 50 * 1024, // 50KB gzipped
    total: 500 * 1024, // 500KB total
  },
  performanceTargets: {
    lcp: 2500, // Largest Contentful Paint (ms)
    fid: 100, // First Input Delay (ms)
    cls: 0.1, // Cumulative Layout Shift
    fcp: 1800, // First Contentful Paint (ms)
    ttfb: 800, // Time to First Byte (ms)
  },
  outputPath: './reports',
  buildPath: './.next',
};

// Utility functions
const log = {
  info: (msg) => console.log(chalk.blue('ℹ'), msg),
  success: (msg) => console.log(chalk.green('✓'), msg),
  warning: (msg) => console.log(chalk.yellow('⚠'), msg),
  error: (msg) => console.log(chalk.red('✗'), msg),
  header: (msg) => console.log(chalk.bold.cyan('\n' + msg)),
};

// Create output directory
function ensureOutputDir() {
  if (!fs.existsSync(CONFIG.outputPath)) {
    fs.mkdirSync(CONFIG.outputPath, { recursive: true });
  }
}

// Analyze bundle size
function analyzeBundleSize() {
  log.header('📦 Bundle Size Analysis');
  
  const buildPath = path.join(CONFIG.buildPath, 'static');
  const results = {
    js: { files: [], total: 0 },
    css: { files: [], total: 0 },
    other: { files: [], total: 0 },
  };
  
  function analyzeDirectory(dirPath, type) {
    if (!fs.existsSync(dirPath)) return;
    
    const files = fs.readdirSync(dirPath);
    
    files.forEach(file => {
      const filePath = path.join(dirPath, file);
      const stats = fs.statSync(filePath);
      
      if (stats.isFile()) {
        const size = stats.size;
        const gzippedSize = getGzippedSize(filePath);
        
        results[type].files.push({
          name: file,
          size,
          gzippedSize,
          path: filePath,
        });
        
        results[type].total += gzippedSize;
      }
    });
  }
  
  // Analyze JavaScript files
  analyzeDirectory(path.join(buildPath, 'chunks'), 'js');
  analyzeDirectory(path.join(buildPath, 'webpack'), 'js');
  
  // Analyze CSS files
  analyzeDirectory(path.join(buildPath, 'css'), 'css');
  
  // Sort files by size (largest first)
  Object.keys(results).forEach(type => {
    results[type].files.sort((a, b) => b.gzippedSize - a.gzippedSize);
  });
  
  // Display results
  console.log('\nJavaScript Files (gzipped):');
  results.js.files.slice(0, 10).forEach(file => {
    const size = formatBytes(file.gzippedSize);
    const status = file.gzippedSize > 100 * 1024 ? 'warning' : 'success';
    log[status](`  ${file.name}: ${size}`);
  });
  
  console.log('\nCSS Files (gzipped):');
  results.css.files.forEach(file => {
    const size = formatBytes(file.gzippedSize);
    log.success(`  ${file.name}: ${size}`);
  });
  
  // Summary
  const totalSize = results.js.total + results.css.total;
  console.log('\nBundle Summary:');
  log.info(`  JavaScript: ${formatBytes(results.js.total)}`);
  log.info(`  CSS: ${formatBytes(results.css.total)}`);
  log.info(`  Total: ${formatBytes(totalSize)}`);
  
  // Check against targets
  if (totalSize > CONFIG.maxBundleSize.total) {
    log.warning(`Total bundle size exceeds target of ${formatBytes(CONFIG.maxBundleSize.total)}`);
  } else {
    log.success(`Total bundle size within target of ${formatBytes(CONFIG.maxBundleSize.total)}`);
  }
  
  return results;
}

// Get gzipped size of a file
function getGzippedSize(filePath) {
  try {
    const buffer = fs.readFileSync(filePath);
    const zlib = require('zlib');
    const gzipped = zlib.gzipSync(buffer);
    return gzipped.length;
  } catch (error) {
    log.error(`Failed to get gzipped size for ${filePath}: ${error.message}`);
    return 0;
  }
}

// Format bytes to human readable format
function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Run Lighthouse performance audit
async function runLighthouseAudit() {
  log.header('🚀 Lighthouse Performance Audit');
  
  try {
    // Start the development server if not running
    log.info('Starting development server...');
    const serverProcess = require('child_process').spawn('npm', ['run', 'dev'], {
      stdio: 'pipe',
      detached: true,
    });
    
    // Wait for server to start
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    // Run Lighthouse
    const lighthouse = require('lighthouse');
    const chromeLauncher = require('chrome-launcher');
    
    const chrome = await chromeLauncher.launch({ chromeFlags: ['--headless'] });
    const options = {
      logLevel: 'info',
      output: 'json',
      onlyCategories: ['performance'],
      port: chrome.port,
    };
    
    const runnerResult = await lighthouse('http://localhost:3000', options);
    const { lhr } = runnerResult;
    
    // Kill Chrome and server
    await chrome.kill();
    serverProcess.kill();
    
    // Extract performance metrics
    const performance = lhr.categories.performance.score * 100;
    const metrics = {
      lcp: lhr.audits['largest-contentful-paint'].numericValue,
      fid: lhr.audits['first-input-delay'].numericValue,
      cls: lhr.audits['cumulative-layout-shift'].numericValue,
      fcp: lhr.audits['first-contentful-paint'].numericValue,
      ttfb: lhr.audits['time-to-first-byte'].numericValue,
    };
    
    // Display results
    console.log('\nPerformance Metrics:');
    log.info(`  Performance Score: ${performance.toFixed(0)}/100`);
    log.info(`  Largest Contentful Paint: ${metrics.lcp.toFixed(0)}ms`);
    log.info(`  First Input Delay: ${metrics.fid.toFixed(0)}ms`);
    log.info(`  Cumulative Layout Shift: ${metrics.cls.toFixed(3)}`);
    log.info(`  First Contentful Paint: ${metrics.fcp.toFixed(0)}ms`);
    log.info(`  Time to First Byte: ${metrics.ttfb.toFixed(0)}ms`);
    
    // Check against targets
    let allPassed = true;
    
    if (metrics.lcp > CONFIG.performanceTargets.lcp) {
      log.warning(`LCP exceeds target of ${CONFIG.performanceTargets.lcp}ms`);
      allPassed = false;
    }
    
    if (metrics.fid > CONFIG.performanceTargets.fid) {
      log.warning(`FID exceeds target of ${CONFIG.performanceTargets.fid}ms`);
      allPassed = false;
    }
    
    if (metrics.cls > CONFIG.performanceTargets.cls) {
      log.warning(`CLS exceeds target of ${CONFIG.performanceTargets.cls}`);
      allPassed = false;
    }
    
    if (allPassed) {
      log.success('All performance targets met!');
    }
    
    // Save detailed report
    const reportPath = path.join(CONFIG.outputPath, 'lighthouse-report.json');
    fs.writeFileSync(reportPath, JSON.stringify(runnerResult, null, 2));
    log.info(`Detailed report saved to ${reportPath}`);
    
    return { performance, metrics };
    
  } catch (error) {
    log.error(`Lighthouse audit failed: ${error.message}`);
    return null;
  }
}

// Analyze Webpack bundle
function analyzeWebpackBundle() {
  log.header('📊 Webpack Bundle Analysis');
  
  try {
    const webpackBundleAnalyzer = require('webpack-bundle-analyzer');
    const bundlePath = path.join(CONFIG.buildPath, 'static', 'chunks', 'pages', '_app.js');
    
    if (!fs.existsSync(bundlePath)) {
      log.warning('Webpack bundle not found. Run build first.');
      return null;
    }
    
    // Generate bundle analysis
    const analyzer = new webpackBundleAnalyzer.BundleAnalyzerPlugin({
      analyzerMode: 'static',
      reportFilename: path.join(CONFIG.outputPath, 'bundle-report.html'),
      openAnalyzer: false,
    });
    
    log.info('Bundle analysis report generated');
    log.info(`Open ${path.join(CONFIG.outputPath, 'bundle-report.html')} for detailed analysis`);
    
    return true;
    
  } catch (error) {
    log.error(`Bundle analysis failed: ${error.message}`);
    return null;
  }
}

// Check for optimization opportunities
function checkOptimizationOpportunities() {
  log.header('💡 Optimization Opportunities');
  
  const opportunities = [];
  
  // Check for large dependencies
  try {
    const packageJson = require('../package.json');
    const dependencies = packageJson.dependencies || {};
    
    // Large dependencies that might need optimization
    const largeDeps = [
      '@mui/material',
      '@mui/icons-material',
      'moment',
      'lodash',
      'date-fns',
    ];
    
    largeDeps.forEach(dep => {
      if (dependencies[dep]) {
        opportunities.push({
          type: 'large-dependency',
          description: `Consider tree-shaking or replacing ${dep}`,
          priority: 'medium',
        });
      }
    });
  } catch (error) {
    log.warning('Could not analyze dependencies');
  }
  
  // Check for unused exports
  opportunities.push({
    type: 'unused-exports',
    description: 'Run webpack-bundle-analyzer to identify unused exports',
    priority: 'low',
  });
  
  // Check for image optimization
  opportunities.push({
    type: 'image-optimization',
    description: 'Ensure all images are optimized and in modern formats',
    priority: 'medium',
  });
  
  // Check for code splitting opportunities
  opportunities.push({
    type: 'code-splitting',
    description: 'Consider dynamic imports for large components',
    priority: 'high',
  });
  
  // Display opportunities
  opportunities.forEach((opp, index) => {
    const priority = opp.priority === 'high' ? 'error' : opp.priority === 'medium' ? 'warning' : 'info';
    log[priority](`${index + 1}. ${opp.description} (${opp.priority} priority)`);
  });
  
  return opportunities;
}

// Generate performance report
function generateReport(bundleAnalysis, lighthouseResults, opportunities) {
  log.header('📄 Generating Performance Report');
  
  const report = {
    timestamp: new Date().toISOString(),
    bundleSize: bundleAnalysis,
    performance: lighthouseResults,
    opportunities,
    recommendations: generateRecommendations(bundleAnalysis, lighthouseResults, opportunities),
  };
  
  const reportPath = path.join(CONFIG.outputPath, 'performance-report.json');
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  
  // Generate HTML report
  const htmlReport = generateHTMLReport(report);
  const htmlPath = path.join(CONFIG.outputPath, 'performance-report.html');
  fs.writeFileSync(htmlPath, htmlReport);
  
  log.success(`Performance report generated: ${reportPath}`);
  log.success(`HTML report generated: ${htmlPath}`);
  
  return report;
}

// Generate recommendations based on analysis
function generateRecommendations(bundleAnalysis, lighthouseResults, opportunities) {
  const recommendations = [];
  
  // Bundle size recommendations
  if (bundleAnalysis.js.total > CONFIG.maxBundleSize.js) {
    recommendations.push({
      category: 'bundle-size',
      priority: 'high',
      title: 'Reduce JavaScript Bundle Size',
      description: 'Consider code splitting, tree shaking, or removing unused dependencies',
    });
  }
  
  // Performance recommendations
  if (lighthouseResults && lighthouseResults.performance < 90) {
    recommendations.push({
      category: 'performance',
      priority: 'high',
      title: 'Improve Core Web Vitals',
      description: 'Focus on LCP, FID, and CLS metrics to improve user experience',
    });
  }
  
  // Opportunity-based recommendations
  opportunities.forEach(opp => {
    if (opp.priority === 'high') {
      recommendations.push({
        category: opp.type,
        priority: opp.priority,
        title: 'Optimization Opportunity',
        description: opp.description,
      });
    }
  });
  
  return recommendations;
}

// Generate HTML report
function generateHTMLReport(report) {
  return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KAREN AI Performance Report</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; border-bottom: 2px solid #007acc; padding-bottom: 10px; }
        h2 { color: #555; margin-top: 30px; }
        .metric { display: inline-block; margin: 10px; padding: 15px; background: #f8f9fa; border-radius: 6px; min-width: 150px; text-align: center; }
        .metric-value { font-size: 24px; font-weight: bold; color: #007acc; }
        .metric-label { font-size: 14px; color: #666; }
        .status-good { color: #28a745; }
        .status-warning { color: #ffc107; }
        .status-error { color: #dc3545; }
        .recommendation { margin: 10px 0; padding: 15px; border-left: 4px solid #007acc; background: #f8f9fa; }
        .priority-high { border-left-color: #dc3545; }
        .priority-medium { border-left-color: #ffc107; }
        .priority-low { border-left-color: #28a745; }
    </style>
</head>
<body>
    <div class="container">
        <h1>KAREN AI Performance Report</h1>
        <p>Generated on ${new Date(report.timestamp).toLocaleString()}</p>
        
        <h2>Performance Score</h2>
        <div class="metric">
            <div class="metric-value ${report.performance?.performance > 90 ? 'status-good' : report.performance?.performance > 70 ? 'status-warning' : 'status-error'}">
                ${report.performance?.performance.toFixed(0) || 'N/A'}/100
            </div>
            <div class="metric-label">Performance Score</div>
        </div>
        
        <h2>Bundle Size</h2>
        <div class="metric">
            <div class="metric-value ${report.bundleSize?.js.total < CONFIG.maxBundleSize.js ? 'status-good' : 'status-error'}">
                ${formatBytes(report.bundleSize?.js.total || 0)}
            </div>
            <div class="metric-label">JavaScript (gzipped)</div>
        </div>
        <div class="metric">
            <div class="metric-value ${report.bundleSize?.css.total < CONFIG.maxBundleSize.css ? 'status-good' : 'status-error'}">
                ${formatBytes(report.bundleSize?.css.total || 0)}
            </div>
            <div class="metric-label">CSS (gzipped)</div>
        </div>
        
        <h2>Core Web Vitals</h2>
        <div class="metric">
            <div class="metric-value ${report.performance?.metrics?.lcp < CONFIG.performanceTargets.lcp ? 'status-good' : 'status-warning'}">
                ${report.performance?.metrics?.lcp?.toFixed(0) || 'N/A'}ms
            </div>
            <div class="metric-label">Largest Contentful Paint</div>
        </div>
        <div class="metric">
            <div class="metric-value ${report.performance?.metrics?.fid < CONFIG.performanceTargets.fid ? 'status-good' : 'status-warning'}">
                ${report.performance?.metrics?.fid?.toFixed(0) || 'N/A'}ms
            </div>
            <div class="metric-label">First Input Delay</div>
        </div>
        <div class="metric">
            <div class="metric-value ${report.performance?.metrics?.cls < CONFIG.performanceTargets.cls ? 'status-good' : 'status-warning'}">
                ${report.performance?.metrics?.cls?.toFixed(3) || 'N/A'}
            </div>
            <div class="metric-label">Cumulative Layout Shift</div>
        </div>
        
        <h2>Recommendations</h2>
        ${report.recommendations?.map(rec => `
            <div class="recommendation priority-${rec.priority}">
                <h3>${rec.title}</h3>
                <p>${rec.description}</p>
                <small>Priority: ${rec.priority} | Category: ${rec.category}</small>
            </div>
        `).join('') || '<p>No recommendations at this time.</p>'}
    </div>
</body>
</html>
  `;
}

// Main execution function
async function main() {
  log.header('🔍 KAREN AI Performance Analysis');
  
  ensureOutputDir();
  
  try {
    // Run build if needed
    if (!fs.existsSync(CONFIG.buildPath)) {
      log.info('Running production build...');
      execSync('npm run build', { stdio: 'inherit' });
    }
    
    // Run analyses
    const bundleAnalysis = analyzeBundleSize();
    const lighthouseResults = await runLighthouseAudit();
    analyzeWebpackBundle();
    const opportunities = checkOptimizationOpportunities();
    
    // Generate report
    const report = generateReport(bundleAnalysis, lighthouseResults, opportunities);
    
    log.success('\nPerformance analysis completed!');
    log.info(`Reports generated in: ${CONFIG.outputPath}`);
    
  } catch (error) {
    log.error(`Analysis failed: ${error.message}`);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = {
  analyzeBundleSize,
  runLighthouseAudit,
  checkOptimizationOpportunities,
  generateReport,
};