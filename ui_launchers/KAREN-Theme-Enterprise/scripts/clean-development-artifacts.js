#!/usr/bin/env node

/**
 * Production Cleanup Script
 * 
 * Removes development artifacts, debug statements, and test content
 * from the web UI for production deployment.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const SRC_DIR = path.join(__dirname, '../src');
const BACKUP_DIR = path.join(__dirname, '../.cleanup-backup');

// Patterns to clean up
const CLEANUP_PATTERNS = {
  // Console statements (except safe-console usage)
  consoleStatements: /console\.(log|debug|info|warn|error)\s*\([^)]*\);?\s*$/gm,
  
  // Development-only imports
  developmentImports: /import.*['"].*\/(test-|debug-|dev-).*['"];?\s*$/gm,
  
  // Debug comments
  debugComments: /\/\*\s*(DEBUG|TODO|FIXME|HACK)[\s\S]*?\*\/\s*$/gm,
  
  // Development environment checks (keep production logic)
  devEnvironmentChecks: /if\s*\(\s*process\.env\.NODE_ENV\s*===\s*['"]development['"]\s*\)\s*\{[\s\S]*?\}/gm,
  
  // Test mode flags
  testModeFlags: /['"]test.*mode['"]|TEST_MODE|DEBUG_MODE/g,
  
  // Development feature flags
  devFeatureFlags: /['"]debug\.mode['"]:\s*true/g,
  
  // Placeholder text
  placeholderText: /placeholder.*text|lorem ipsum|sample.*data/gi,
  
  // Developer messages
  developerMessages: /developer.*message|development.*only|debug.*info/gi,
};

// Files to exclude from cleanup
const EXCLUDE_PATTERNS = [
  /node_modules/,
  /\.test\./,
  /\.spec\./,
  /__tests__/,
  /\.d\.ts$/,
  /safe-console/,
  /logger\.ts$/,
  /diagnostics\.ts$/,
];

// Files that need special handling
const SPECIAL_FILES = {
  'src/lib/featureFlagConfig.ts': {
    replacements: [
      {
        pattern: /development:\s*\{[\s\S]*?\}/,
        replacement: `development: {
    'debug.mode': false,
    'analytics.detailed': false,
    'voice.input': false,
    'accessibility.enhanced': true,
    'telemetry.enabled': false,
  }`
      },
      {
        pattern: /'debug\.mode':\s*true/g,
        replacement: "'debug.mode': false"
      }
    ]
  },
  'src/middleware.ts': {
    replacements: [
      {
        pattern: /console\.log\(`Missing chunk requested: \${pathname}\`\);/,
        replacement: '// Chunk missing - handled silently in production'
      }
    ]
  }
};

class ProductionCleaner {
  constructor() {
    this.processedFiles = 0;
    this.cleanedFiles = 0;
    this.errors = [];
  }

  shouldExcludeFile(filePath) {
    return EXCLUDE_PATTERNS.some(pattern => pattern.test(filePath));
  }

  createBackup() {
    console.log('📦 Creating backup...');
    if (fs.existsSync(BACKUP_DIR)) {
      fs.rmSync(BACKUP_DIR, { recursive: true, force: true });
    }
    fs.mkdirSync(BACKUP_DIR, { recursive: true });
    
    try {
      execSync(`cp -r "${SRC_DIR}" "${BACKUP_DIR}/"`, { stdio: 'inherit' });
      console.log('✅ Backup created successfully');
    } catch (error) {
      console.error('❌ Failed to create backup:', error.message);
      process.exit(1);
    }
  }

  cleanFile(filePath) {
    try {
      const relativePath = path.relative(SRC_DIR, filePath);
      
      if (this.shouldExcludeFile(relativePath)) {
        return false;
      }

      let content = fs.readFileSync(filePath, 'utf8');
      let originalContent = content;
      let hasChanges = false;

      // Apply special file handling
      const specialFile = SPECIAL_FILES[relativePath];
      if (specialFile) {
        specialFile.replacements.forEach(({ pattern, replacement }) => {
          const newContent = content.replace(pattern, replacement);
          if (newContent !== content) {
            content = newContent;
            hasChanges = true;
          }
        });
      }

      // Apply general cleanup patterns
      Object.entries(CLEANUP_PATTERNS).forEach(([patternName, pattern]) => {
        const matches = content.match(pattern);
        if (matches) {
          // Special handling for console statements - preserve safe-console usage
          if (patternName === 'consoleStatements') {
            const newContent = content.replace(pattern, (match) => {
              // Keep safe-console imports and usage
              if (match.includes('safeError') || match.includes('safeWarn') || 
                  match.includes('safeDebug') || match.includes('safeLog')) {
                return match;
              }
              // Keep logger usage
              if (match.includes('logger.')) {
                return match;
              }
              // Remove other console statements
              return '';
            });
            
            if (newContent !== content) {
              content = newContent;
              hasChanges = true;
            }
          } else {
            const newContent = content.replace(pattern, '');
            if (newContent !== content) {
              content = newContent;
              hasChanges = true;
            }
          }
        }
      });

      // Clean up empty lines and excessive whitespace
      if (hasChanges) {
        content = content
          .replace(/\n\s*\n\s*\n/g, '\n\n') // Remove excessive empty lines
          .replace(/^\s*\n/gm, '') // Remove empty lines at start of blocks
          .trim() + '\n'; // Ensure file ends with single newline
      }

      if (hasChanges) {
        fs.writeFileSync(filePath, content, 'utf8');
        console.log(`🧹 Cleaned: ${relativePath}`);
        return true;
      }

      return false;
    } catch (error) {
      this.errors.push(`Error cleaning ${filePath}: ${error.message}`);
      return false;
    }
  }

  processDirectory(dirPath) {
    const entries = fs.readdirSync(dirPath, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(dirPath, entry.name);

      if (entry.isDirectory()) {
        this.processDirectory(fullPath);
      } else if (entry.isFile() && /\.(ts|tsx|js|jsx)$/.test(entry.name)) {
        this.processedFiles++;
        if (this.cleanFile(fullPath)) {
          this.cleanedFiles++;
        }
      }
    }
  }

  optimizeBundles() {
    console.log('📦 Optimizing bundles...');
    
    // Update next.config.js for production optimization
    const nextConfigPath = path.join(__dirname, '../next.config.js');
    if (fs.existsSync(nextConfigPath)) {
      let nextConfig = fs.readFileSync(nextConfigPath, 'utf8');
      
      // Ensure production optimizations are enabled
      if (!nextConfig.includes('removeConsole: true')) {
        nextConfig = nextConfig.replace(
          /experimental:\s*\{/,
          `experimental: {
    removeConsole: process.env.NODE_ENV === 'production',`
        );
      }
      
      // Enable bundle analyzer in production builds
      if (!nextConfig.includes('ANALYZE')) {
        nextConfig = nextConfig.replace(
          /module\.exports\s*=\s*nextConfig/,
          `// Enable bundle analysis
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
});

module.exports = withBundleAnalyzer(nextConfig);`
        );
      }
      
      fs.writeFileSync(nextConfigPath, nextConfig);
      console.log('✅ Next.js config optimized for production');
    }
  }

  removeUnusedImports() {
    console.log('🔍 Removing unused imports...');
    
    try {
      // Use TypeScript compiler to find unused imports
      execSync('npx tsc --noEmit --skipLibCheck', { 
        cwd: path.join(__dirname, '..'),
        stdio: 'pipe' 
      });
    } catch (error) {
      // TypeScript errors are expected, we just want to trigger the check
    }

    // Run ESLint to remove unused imports
    try {
      execSync('npx eslint src --fix --rule "no-unused-vars: error"', {
        cwd: path.join(__dirname, '..'),
        stdio: 'inherit'
      });
      console.log('✅ Unused imports removed');
    } catch (error) {
      console.warn('⚠️ Some ESLint issues may need manual fixing');
    }
  }

  generateReport() {
    console.log('\n📊 Production Cleanup Report');
    console.log('================================');
    console.log(`Files processed: ${this.processedFiles}`);
    console.log(`Files cleaned: ${this.cleanedFiles}`);
    console.log(`Success rate: ${((this.cleanedFiles / this.processedFiles) * 100).toFixed(1)}%`);
    
    if (this.errors.length > 0) {
      console.log('\n❌ Errors encountered:');
      this.errors.forEach(error => console.log(`  - ${error}`));
    }
    
    console.log('\n✅ Production cleanup completed!');
    console.log(`💾 Backup available at: ${BACKUP_DIR}`);
  }

  run() {
    console.log('🚀 Starting production cleanup...\n');
    
    this.createBackup();
    this.processDirectory(SRC_DIR);
    this.optimizeBundles();
    this.removeUnusedImports();
    this.generateReport();
  }
}

// Run the cleaner
if (require.main === module) {
  const cleaner = new ProductionCleaner();
  cleaner.run();
}

module.exports = ProductionCleaner;