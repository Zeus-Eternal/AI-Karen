#!/usr/bin/env node

/**
 * Bundle analysis script for monitoring and optimizing bundle sizes
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

function colorize(text, color) {
  return `${colors[color]}${text}${colors.reset}`;
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function analyzeBundleSize() {
  console.log(colorize('\n🔍 Analyzing bundle size...', 'cyan'));
  
  try {
    // Build the application first
    console.log('Building application...');
    execSync('npm run build', { stdio: 'inherit' });
    
    // Check if .next directory exists
    const nextDir = path.join(process.cwd(), '.next');
    if (!fs.existsSync(nextDir)) {
      console.error(colorize('❌ .next directory not found. Build may have failed.', 'red'));
      process.exit(1);
    }
    
    // Analyze static directory
    const staticDir = path.join(nextDir, 'static');
    if (fs.existsSync(staticDir)) {
      analyzeStaticAssets(staticDir);
    }
    
    // Analyze chunks
    const chunksDir = path.join(staticDir, 'chunks');
    if (fs.existsSync(chunksDir)) {
      analyzeChunks(chunksDir);
    }
    
    // Generate bundle analyzer report
    console.log('\n📊 Generating detailed bundle analysis...');
    execSync('ANALYZE=true npm run build', { stdio: 'inherit' });
    
  } catch (error) {
    console.error(colorize('❌ Bundle analysis failed:', 'red'), error.message);
    process.exit(1);
  }
}

function analyzeStaticAssets(staticDir) {
  console.log(colorize('\n📦 Static Assets Analysis:', 'blue'));
  
  const assets = [];
  
  function scanDirectory(dir, relativePath = '') {
    const items = fs.readdirSync(dir);
    
    items.forEach(item => {
      const fullPath = path.join(dir, item);
      const itemRelativePath = path.join(relativePath, item);
      const stats = fs.statSync(fullPath);
      
      if (stats.isDirectory()) {
        scanDirectory(fullPath, itemRelativePath);
      } else {
        assets.push({
          name: itemRelativePath,
          size: stats.size,
          type: getAssetType(item),
        });
      }
    });
  }
  
  scanDirectory(staticDir);
  
  // Sort by size (largest first)
  assets.sort((a, b) => b.size - a.size);
  
  // Group by type
  const assetsByType = assets.reduce((acc, asset) => {
    if (!acc[asset.type]) acc[asset.type] = [];
    acc[asset.type].push(asset);
    return acc;
  }, {});
  
  // Display results
  Object.entries(assetsByType).forEach(([type, typeAssets]) => {
    const totalSize = typeAssets.reduce((sum, asset) => sum + asset.size, 0);
    console.log(colorize(`\n${type.toUpperCase()} files (${formatBytes(totalSize)}):`, 'yellow'));
    
    typeAssets.slice(0, 10).forEach(asset => {
      const sizeColor = asset.size > 100 * 1024 ? 'red' : asset.size > 50 * 1024 ? 'yellow' : 'green';
      console.log(`  ${asset.name}: ${colorize(formatBytes(asset.size), sizeColor)}`);
    });
    
    if (typeAssets.length > 10) {
      console.log(`  ... and ${typeAssets.length - 10} more files`);
    }
  });
}

function analyzeChunks(chunksDir) {
  console.log(colorize('\n🧩 Chunk Analysis:', 'blue'));
  
  const chunks = [];
  const items = fs.readdirSync(chunksDir);
  
  items.forEach(item => {
    const fullPath = path.join(chunksDir, item);
    const stats = fs.statSync(fullPath);
    
    if (stats.isFile() && item.endsWith('.js')) {
      chunks.push({
        name: item,
        size: stats.size,
        type: getChunkType(item),
      });
    }
  });
  
  // Sort by size (largest first)
  chunks.sort((a, b) => b.size - a.size);
  
  console.log('\nLargest chunks:');
  chunks.slice(0, 15).forEach(chunk => {
    const sizeColor = chunk.size > 100 * 1024 ? 'red' : chunk.size > 50 * 1024 ? 'yellow' : 'green';
    const typeColor = chunk.type === 'vendor' ? 'magenta' : chunk.type === 'page' ? 'cyan' : 'white';
    
    console.log(`  ${colorize(chunk.name, typeColor)}: ${colorize(formatBytes(chunk.size), sizeColor)} (${chunk.type})`);
  });
  
  // Summary
  const totalSize = chunks.reduce((sum, chunk) => sum + chunk.size, 0);
  const vendorChunks = chunks.filter(c => c.type === 'vendor');
  const pageChunks = chunks.filter(c => c.type === 'page');
  const appChunks = chunks.filter(c => c.type === 'app');
  
  console.log(colorize('\nChunk Summary:', 'bright'));
  console.log(`  Total chunks: ${chunks.length}`);
  console.log(`  Total size: ${formatBytes(totalSize)}`);
  console.log(`  Vendor chunks: ${vendorChunks.length} (${formatBytes(vendorChunks.reduce((sum, c) => sum + c.size, 0))})`);
  console.log(`  Page chunks: ${pageChunks.length} (${formatBytes(pageChunks.reduce((sum, c) => sum + c.size, 0))})`);
  console.log(`  App chunks: ${appChunks.length} (${formatBytes(appChunks.reduce((sum, c) => sum + c.size, 0))})`);
}

function getAssetType(filename) {
  const ext = path.extname(filename).toLowerCase();
  
  if (['.js', '.mjs'].includes(ext)) return 'javascript';
  if (['.css'].includes(ext)) return 'css';
  if (['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'].includes(ext)) return 'image';
  if (['.woff', '.woff2', '.ttf', '.eot'].includes(ext)) return 'font';
  if (['.json'].includes(ext)) return 'json';
  
  return 'other';
}

function getChunkType(filename) {
  if (filename.includes('vendor') || filename.includes('node_modules')) return 'vendor';
  if (filename.includes('pages/') || filename.includes('app/')) return 'page';
  if (filename.includes('_app') || filename.includes('main')) return 'app';
  if (filename.includes('webpack')) return 'webpack';
  if (filename.includes('framework')) return 'framework';
  
  return 'other';
}

function checkBundleBudgets() {
  console.log(colorize('\n💰 Bundle Budget Check:', 'blue'));
  
  const budgets = {
    maxBundleSize: 250 * 1024, // 250KB
    maxChunkSize: 100 * 1024,  // 100KB
    maxAssetSize: 50 * 1024,   // 50KB
  };
  
  // This would integrate with the actual bundle analysis
  // For now, just show the budgets
  console.log(`  Maximum bundle size: ${formatBytes(budgets.maxBundleSize)}`);
  console.log(`  Maximum chunk size: ${formatBytes(budgets.maxChunkSize)}`);
  console.log(`  Maximum asset size: ${formatBytes(budgets.maxAssetSize)}`);
  
  console.log(colorize('\n💡 Optimization Tips:', 'green'));
  console.log('  • Use dynamic imports for route-based code splitting');
  console.log('  • Lazy load heavy components and libraries');
  console.log('  • Optimize images and use modern formats (WebP, AVIF)');
  console.log('  • Remove unused dependencies and code');
  console.log('  • Use tree shaking for better dead code elimination');
  console.log('  • Consider using a CDN for static assets');
}

function generateReport() {
  const reportPath = path.join(process.cwd(), 'bundle-analysis-report.json');
  const report = {
    timestamp: new Date().toISOString(),
    analysis: 'Bundle analysis completed',
    recommendations: [
      'Implement lazy loading for heavy components',
      'Use dynamic imports for route splitting',
      'Optimize asset sizes and formats',
      'Remove unused dependencies',
    ],
  };
  
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  console.log(colorize(`\n📄 Report saved to: ${reportPath}`, 'green'));
}

// Main execution
if (require.main === module) {
  console.log(colorize('🚀 Bundle Size Analysis Tool', 'bright'));
  
  analyzeBundleSize();
  checkBundleBudgets();
  generateReport();
  
  console.log(colorize('\n✅ Bundle analysis complete!', 'green'));
}