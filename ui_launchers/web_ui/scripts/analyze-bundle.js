#!/usr/bin/env node

/**
 * Bundle Size Analyzer
 * 
 * Analyzes the production bundle to identify optimization opportunities,
 * large dependencies, and provides recommendations for bundle size reduction.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('📊 Starting bundle analysis...');

// Configuration
const config = {
  buildDir: '.next',
  outputFile: 'bundle-analysis.json',
  thresholds: {
    large_chunk: 500 * 1024, // 500KB
    huge_chunk: 1024 * 1024, // 1MB
    total_js: 2 * 1024 * 1024, // 2MB
    total_css: 500 * 1024 // 500KB
  },
  recommendations: {
    enable: true,
    maxRecommendations: 10
  }
};

// Utility functions
function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function getFileSize(filePath) {
  try {
    const stats = fs.statSync(filePath);
    return stats.size;
  } catch (error) {
    return 0;
  }
}

function analyzeJavaScriptBundles() {
  console.log('🔍 Analyzing JavaScript bundles...');
  
  const staticDir = path.join(config.buildDir, 'static');
  const chunksDir = path.join(staticDir, 'chunks');
  
  if (!fs.existsSync(chunksDir)) {
    console.log('⚠️  Chunks directory not found');
    return { files: [], totalSize: 0, analysis: {} };
  }
  
  const jsFiles = [];
  
  function scanDirectory(dir, prefix = '') {
    const items = fs.readdirSync(dir);
    
    for (const item of items) {
      const fullPath = path.join(dir, item);
      const relativePath = path.join(prefix, item);
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory()) {
        scanDirectory(fullPath, relativePath);
      } else if (item.endsWith('.js')) {
        jsFiles.push({
          name: item,
          path: relativePath,
          fullPath: fullPath,
          size: stat.size,
          sizeFormatted: formatBytes(stat.size),
          type: classifyJSFile(item)
        });
      }
    }
  }
  
  scanDirectory(chunksDir);
  
  // Sort by size (largest first)
  jsFiles.sort((a, b) => b.size - a.size);
  
  const totalSize = jsFiles.reduce((sum, file) => sum + file.size, 0);
  
  // Analyze bundle composition
  const analysis = {
    totalFiles: jsFiles.length,
    totalSize: totalSize,
    totalSizeFormatted: formatBytes(totalSize),
    largeChunks: jsFiles.filter(f => f.size > config.thresholds.large_chunk),
    hugeChunks: jsFiles.filter(f => f.size > config.thresholds.huge_chunk),
    byType: {}
  };
  
  // Group by type
  jsFiles.forEach(file => {
    if (!analysis.byType[file.type]) {
      analysis.byType[file.type] = {
        count: 0,
        totalSize: 0,
        files: []
      };
    }
    
    analysis.byType[file.type].count++;
    analysis.byType[file.type].totalSize += file.size;
    analysis.byType[file.type].files.push(file);
  });
  
  // Format type analysis
  Object.keys(analysis.byType).forEach(type => {
    analysis.byType[type].totalSizeFormatted = formatBytes(analysis.byType[type].totalSize);
    analysis.byType[type].percentage = ((analysis.byType[type].totalSize / totalSize) * 100).toFixed(1);
  });
  
  return { files: jsFiles, totalSize, analysis };
}

function classifyJSFile(filename) {
  if (filename.includes('framework-') || filename.includes('main-')) {
    return 'framework';
  } else if (filename.includes('vendor') || filename.includes('node_modules')) {
    return 'vendor';
  } else if (filename.includes('commons') || filename.includes('shared')) {
    return 'shared';
  } else if (filename.includes('runtime') || filename.includes('webpack')) {
    return 'runtime';
  } else if (/^\d+\./.test(filename)) {
    return 'dynamic';
  } else if (filename.includes('pages') || filename.includes('app')) {
    return 'pages';
  } else {
    return 'other';
  }
}

function analyzeCSSBundles() {
  console.log('🎨 Analyzing CSS bundles...');
  
  const staticDir = path.join(config.buildDir, 'static');
  const cssDir = path.join(staticDir, 'css');
  
  if (!fs.existsSync(cssDir)) {
    console.log('⚠️  CSS directory not found');
    return { files: [], totalSize: 0, analysis: {} };
  }
  
  const cssFiles = fs.readdirSync(cssDir)
    .filter(file => file.endsWith('.css'))
    .map(file => {
      const fullPath = path.join(cssDir, file);
      const size = getFileSize(fullPath);
      
      return {
        name: file,
        path: path.join('static/css', file),
        fullPath: fullPath,
        size: size,
        sizeFormatted: formatBytes(size),
        type: classifyCSSFile(file)
      };
    })
    .sort((a, b) => b.size - a.size);
  
  const totalSize = cssFiles.reduce((sum, file) => sum + file.size, 0);
  
  const analysis = {
    totalFiles: cssFiles.length,
    totalSize: totalSize,
    totalSizeFormatted: formatBytes(totalSize),
    largeFiles: cssFiles.filter(f => f.size > 50 * 1024), // 50KB
    byType: {}
  };
  
  // Group by type
  cssFiles.forEach(file => {
    if (!analysis.byType[file.type]) {
      analysis.byType[file.type] = {
        count: 0,
        totalSize: 0,
        files: []
      };
    }
    
    analysis.byType[file.type].count++;
    analysis.byType[file.type].totalSize += file.size;
    analysis.byType[file.type].files.push(file);
  });
  
  // Format type analysis
  Object.keys(analysis.byType).forEach(type => {
    analysis.byType[type].totalSizeFormatted = formatBytes(analysis.byType[type].totalSize);
    analysis.byType[type].percentage = ((analysis.byType[type].totalSize / totalSize) * 100).toFixed(1);
  });
  
  return { files: cssFiles, totalSize, analysis };
}

function classifyCSSFile(filename) {
  if (filename.includes('app') || filename.includes('global')) {
    return 'global';
  } else if (filename.includes('vendor') || filename.includes('framework')) {
    return 'vendor';
  } else if (/^\d+\./.test(filename)) {
    return 'dynamic';
  } else {
    return 'component';
  }
}

function analyzeStaticAssets() {
  console.log('📁 Analyzing static assets...');
  
  const publicDir = 'public';
  const assets = [];
  
  if (!fs.existsSync(publicDir)) {
    return { files: [], totalSize: 0, analysis: {} };
  }
  
  function scanAssets(dir, prefix = '') {
    const items = fs.readdirSync(dir);
    
    for (const item of items) {
      const fullPath = path.join(dir, item);
      const relativePath = path.join(prefix, item);
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory()) {
        scanAssets(fullPath, relativePath);
      } else {
        const ext = path.extname(item).toLowerCase();
        if (['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico', '.woff', '.woff2', '.ttf', '.otf'].includes(ext)) {
          assets.push({
            name: item,
            path: relativePath,
            fullPath: fullPath,
            size: stat.size,
            sizeFormatted: formatBytes(stat.size),
            type: getAssetType(ext)
          });
        }
      }
    }
  }
  
  scanAssets(publicDir);
  
  // Sort by size
  assets.sort((a, b) => b.size - a.size);
  
  const totalSize = assets.reduce((sum, asset) => sum + asset.size, 0);
  
  const analysis = {
    totalFiles: assets.length,
    totalSize: totalSize,
    totalSizeFormatted: formatBytes(totalSize),
    largeAssets: assets.filter(a => a.size > 100 * 1024), // 100KB
    byType: {}
  };
  
  // Group by type
  assets.forEach(asset => {
    if (!analysis.byType[asset.type]) {
      analysis.byType[asset.type] = {
        count: 0,
        totalSize: 0,
        files: []
      };
    }
    
    analysis.byType[asset.type].count++;
    analysis.byType[asset.type].totalSize += asset.size;
    analysis.byType[asset.type].files.push(asset);
  });
  
  // Format type analysis
  Object.keys(analysis.byType).forEach(type => {
    analysis.byType[type].totalSizeFormatted = formatBytes(analysis.byType[type].totalSize);
    analysis.byType[type].percentage = ((analysis.byType[type].totalSize / totalSize) * 100).toFixed(1);
  });
  
  return { files: assets, totalSize, analysis };
}

function getAssetType(extension) {
  const imageExts = ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico'];
  const fontExts = ['.woff', '.woff2', '.ttf', '.otf'];
  
  if (imageExts.includes(extension)) {
    return 'image';
  } else if (fontExts.includes(extension)) {
    return 'font';
  } else {
    return 'other';
  }
}

function generateRecommendations(jsAnalysis, cssAnalysis, assetsAnalysis) {
  console.log('💡 Generating optimization recommendations...');
  
  const recommendations = [];
  
  // JavaScript recommendations
  if (jsAnalysis.totalSize > config.thresholds.total_js) {
    recommendations.push({
      type: 'javascript',
      priority: 'high',
      title: 'Large JavaScript Bundle Size',
      description: `Total JavaScript size (${formatBytes(jsAnalysis.totalSize)}) exceeds recommended threshold (${formatBytes(config.thresholds.total_js)})`,
      suggestions: [
        'Enable code splitting for route-based chunks',
        'Use dynamic imports for non-critical components',
        'Analyze and remove unused dependencies',
        'Consider using a smaller alternative for large libraries'
      ]
    });
  }
  
  if (jsAnalysis.analysis.hugeChunks.length > 0) {
    recommendations.push({
      type: 'javascript',
      priority: 'high',
      title: 'Huge JavaScript Chunks Detected',
      description: `Found ${jsAnalysis.analysis.hugeChunks.length} chunks larger than ${formatBytes(config.thresholds.huge_chunk)}`,
      suggestions: [
        'Split large chunks using dynamic imports',
        'Move vendor libraries to separate chunks',
        'Use React.lazy() for component-level code splitting',
        'Consider lazy loading for non-critical features'
      ],
      files: jsAnalysis.analysis.hugeChunks.slice(0, 3).map(f => f.name)
    });
  }
  
  // Check for duplicate dependencies
  const vendorFiles = jsAnalysis.analysis.byType.vendor?.files || [];
  if (vendorFiles.length > 5) {
    recommendations.push({
      type: 'javascript',
      priority: 'medium',
      title: 'Multiple Vendor Chunks',
      description: `Found ${vendorFiles.length} vendor chunks, which may indicate duplicate dependencies`,
      suggestions: [
        'Configure webpack to merge vendor chunks',
        'Use webpack-bundle-analyzer to identify duplicates',
        'Consider using a single vendor chunk for better caching',
        'Remove unused dependencies from package.json'
      ]
    });
  }
  
  // CSS recommendations
  if (cssAnalysis.totalSize > config.thresholds.total_css) {
    recommendations.push({
      type: 'css',
      priority: 'medium',
      title: 'Large CSS Bundle Size',
      description: `Total CSS size (${formatBytes(cssAnalysis.totalSize)}) exceeds recommended threshold (${formatBytes(config.thresholds.total_css)})`,
      suggestions: [
        'Enable CSS purging to remove unused styles',
        'Use critical CSS extraction for above-the-fold content',
        'Consider using CSS-in-JS for component-specific styles',
        'Optimize Tailwind CSS configuration'
      ]
    });
  }
  
  // Asset recommendations
  const largeImages = assetsAnalysis.analysis.byType.image?.files.filter(f => f.size > 500 * 1024) || [];
  if (largeImages.length > 0) {
    recommendations.push({
      type: 'assets',
      priority: 'medium',
      title: 'Large Image Assets',
      description: `Found ${largeImages.length} images larger than 500KB`,
      suggestions: [
        'Optimize images using next/image component',
        'Convert images to WebP or AVIF format',
        'Implement responsive images with srcset',
        'Use lazy loading for below-the-fold images'
      ],
      files: largeImages.slice(0, 3).map(f => f.name)
    });
  }
  
  // Font recommendations
  const fontFiles = assetsAnalysis.analysis.byType.font?.files || [];
  const totalFontSize = fontFiles.reduce((sum, f) => sum + f.size, 0);
  if (totalFontSize > 200 * 1024) {
    recommendations.push({
      type: 'assets',
      priority: 'low',
      title: 'Large Font Assets',
      description: `Total font size (${formatBytes(totalFontSize)}) could be optimized`,
      suggestions: [
        'Use font-display: swap for better loading performance',
        'Subset fonts to include only needed characters',
        'Preload critical fonts in document head',
        'Consider using system fonts for better performance'
      ]
    });
  }
  
  // General performance recommendations
  recommendations.push({
    type: 'performance',
    priority: 'low',
    title: 'General Performance Optimizations',
    description: 'Additional optimizations to consider',
    suggestions: [
      'Enable gzip/brotli compression on your server',
      'Use a CDN for static assets',
      'Implement service worker for caching',
      'Enable HTTP/2 server push for critical resources',
      'Monitor Core Web Vitals in production'
    ]
  });
  
  return recommendations.slice(0, config.recommendations.maxRecommendations);
}

function displayResults(jsAnalysis, cssAnalysis, assetsAnalysis, recommendations) {
  console.log('\n📊 Bundle Analysis Results');
  console.log('═'.repeat(60));
  
  // JavaScript Analysis
  console.log('\n🟨 JavaScript Bundles:');
  console.log(`  Total Files: ${jsAnalysis.analysis.totalFiles}`);
  console.log(`  Total Size: ${jsAnalysis.analysis.totalSizeFormatted}`);
  console.log(`  Large Chunks (>${formatBytes(config.thresholds.large_chunk)}): ${jsAnalysis.analysis.largeChunks.length}`);
  console.log(`  Huge Chunks (>${formatBytes(config.thresholds.huge_chunk)}): ${jsAnalysis.analysis.hugeChunks.length}`);
  
  if (jsAnalysis.files.length > 0) {
    console.log('\n  Top 5 Largest JavaScript Files:');
    jsAnalysis.files.slice(0, 5).forEach((file, index) => {
      console.log(`    ${index + 1}. ${file.name} - ${file.sizeFormatted} (${file.type})`);
    });
  }
  
  // CSS Analysis
  console.log('\n🟦 CSS Bundles:');
  console.log(`  Total Files: ${cssAnalysis.analysis.totalFiles}`);
  console.log(`  Total Size: ${cssAnalysis.analysis.totalSizeFormatted}`);
  
  if (cssAnalysis.files.length > 0) {
    console.log('\n  CSS Files:');
    cssAnalysis.files.forEach((file, index) => {
      console.log(`    ${index + 1}. ${file.name} - ${file.sizeFormatted} (${file.type})`);
    });
  }
  
  // Assets Analysis
  console.log('\n🟩 Static Assets:');
  console.log(`  Total Files: ${assetsAnalysis.analysis.totalFiles}`);
  console.log(`  Total Size: ${assetsAnalysis.analysis.totalSizeFormatted}`);
  
  Object.entries(assetsAnalysis.analysis.byType).forEach(([type, data]) => {
    console.log(`  ${type}: ${data.count} files, ${data.totalSizeFormatted} (${data.percentage}%)`);
  });
  
  // Overall Summary
  const totalSize = jsAnalysis.totalSize + cssAnalysis.totalSize + assetsAnalysis.totalSize;
  console.log('\n📈 Overall Summary:');
  console.log(`  Total Bundle Size: ${formatBytes(totalSize)}`);
  console.log(`  JavaScript: ${formatBytes(jsAnalysis.totalSize)} (${((jsAnalysis.totalSize / totalSize) * 100).toFixed(1)}%)`);
  console.log(`  CSS: ${formatBytes(cssAnalysis.totalSize)} (${((cssAnalysis.totalSize / totalSize) * 100).toFixed(1)}%)`);
  console.log(`  Assets: ${formatBytes(assetsAnalysis.totalSize)} (${((assetsAnalysis.totalSize / totalSize) * 100).toFixed(1)}%)`);
  
  // Recommendations
  if (recommendations.length > 0) {
    console.log('\n💡 Optimization Recommendations:');
    recommendations.forEach((rec, index) => {
      console.log(`\n  ${index + 1}. ${rec.title} (${rec.priority} priority)`);
      console.log(`     ${rec.description}`);
      if (rec.files && rec.files.length > 0) {
        console.log(`     Affected files: ${rec.files.join(', ')}`);
      }
      console.log('     Suggestions:');
      rec.suggestions.forEach(suggestion => {
        console.log(`       • ${suggestion}`);
      });
    });
  }
}

function saveAnalysisReport(jsAnalysis, cssAnalysis, assetsAnalysis, recommendations) {
  const report = {
    timestamp: new Date().toISOString(),
    summary: {
      totalSize: jsAnalysis.totalSize + cssAnalysis.totalSize + assetsAnalysis.totalSize,
      javascript: {
        totalSize: jsAnalysis.totalSize,
        totalFiles: jsAnalysis.analysis.totalFiles,
        percentage: ((jsAnalysis.totalSize / (jsAnalysis.totalSize + cssAnalysis.totalSize + assetsAnalysis.totalSize)) * 100).toFixed(1)
      },
      css: {
        totalSize: cssAnalysis.totalSize,
        totalFiles: cssAnalysis.analysis.totalFiles,
        percentage: ((cssAnalysis.totalSize / (jsAnalysis.totalSize + cssAnalysis.totalSize + assetsAnalysis.totalSize)) * 100).toFixed(1)
      },
      assets: {
        totalSize: assetsAnalysis.totalSize,
        totalFiles: assetsAnalysis.analysis.totalFiles,
        percentage: ((assetsAnalysis.totalSize / (jsAnalysis.totalSize + cssAnalysis.totalSize + assetsAnalysis.totalSize)) * 100).toFixed(1)
      }
    },
    javascript: jsAnalysis,
    css: cssAnalysis,
    assets: assetsAnalysis,
    recommendations: recommendations,
    thresholds: config.thresholds
  };
  
  const reportPath = path.join(config.buildDir, config.outputFile);
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  
  console.log(`\n📄 Detailed analysis report saved to: ${reportPath}`);
  return report;
}

// Main execution
async function main() {
  try {
    if (!fs.existsSync(config.buildDir)) {
      console.error(`❌ Build directory ${config.buildDir} not found. Please run 'npm run build' first.`);
      process.exit(1);
    }
    
    console.log(`🔧 Analyzing build in: ${config.buildDir}`);
    
    // Analyze different bundle types
    const jsAnalysis = analyzeJavaScriptBundles();
    const cssAnalysis = analyzeCSSBundles();
    const assetsAnalysis = analyzeStaticAssets();
    
    // Generate recommendations
    const recommendations = generateRecommendations(jsAnalysis, cssAnalysis, assetsAnalysis);
    
    // Display results
    displayResults(jsAnalysis, cssAnalysis, assetsAnalysis, recommendations);
    
    // Save detailed report
    const report = saveAnalysisReport(jsAnalysis, cssAnalysis, assetsAnalysis, recommendations);
    
    console.log('\n🎉 Bundle analysis completed successfully!');
    console.log('\n📋 Next steps:');
    console.log('  1. Review the recommendations above');
    console.log('  2. Check the detailed report for more information');
    console.log('  3. Implement suggested optimizations');
    console.log('  4. Re-run analysis to measure improvements');
    console.log('  5. Monitor bundle size in CI/CD pipeline');
    
    // Exit with error code if bundle is too large
    const totalSize = jsAnalysis.totalSize + cssAnalysis.totalSize;
    if (totalSize > config.thresholds.total_js + config.thresholds.total_css) {
      console.log('\n⚠️  Bundle size exceeds recommended thresholds');
      process.exit(1);
    }
    
  } catch (error) {
    console.error('❌ Bundle analysis failed:', error);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = {
  main,
  analyzeJavaScriptBundles,
  analyzeCSSBundles,
  analyzeStaticAssets,
  generateRecommendations,
  config
};