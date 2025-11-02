#!/usr/bin/env node

/**
 * CSS and JavaScript Optimization Script
 * 
 * Removes unused CSS classes, optimizes imports, and implements code splitting
 * for production deployment.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const SRC_DIR = path.join(__dirname, '../src');
const STYLES_DIR = path.join(SRC_DIR, 'styles');

class CSSJSOptimizer {
  constructor() {
    this.processedFiles = 0;
    this.optimizedFiles = 0;
    this.removedImports = 0;
    this.errors = [];
  }

  // Find all CSS classes used in the codebase
  findUsedCSSClasses() {
    console.log('🔍 Analyzing CSS class usage...');
    
    const usedClasses = new Set();
    const classRegex = /className\s*=\s*["`']([^"`']*)["`']/g;
    const cnRegex = /cn\s*\(\s*["`']([^"`']*)["`']/g;
    
    this.walkDirectory(SRC_DIR, (filePath) => {
      if (!/\.(tsx?|jsx?)$/.test(filePath)) return;
      
      const content = fs.readFileSync(filePath, 'utf8');
      
      // Find className usage
      let match;
      while ((match = classRegex.exec(content)) !== null) {
        const classes = match[1].split(/\s+/).filter(Boolean);
        classes.forEach(cls => usedClasses.add(cls));
      }
      
      // Find cn() utility usage
      while ((match = cnRegex.exec(content)) !== null) {
        const classes = match[1].split(/\s+/).filter(Boolean);
        classes.forEach(cls => usedClasses.add(cls));
      }
    });
    
    console.log(`📊 Found ${usedClasses.size} unique CSS classes in use`);
    return usedClasses;
  }

  // Remove unused imports from TypeScript/JavaScript files
  optimizeImports(filePath) {
    try {
      let content = fs.readFileSync(filePath, 'utf8');
      const originalContent = content;
      let hasChanges = false;

      // Remove unused React imports (React 17+ JSX transform)
      const unusedReactImport = /^import\s+React\s*,?\s*\{?\s*\}?\s*from\s+['"]react['"];?\s*$/gm;
      if (unusedReactImport.test(content) && !content.includes('React.')) {
        content = content.replace(unusedReactImport, '');
        hasChanges = true;
      }

      // Remove unused type-only imports
      const typeOnlyImports = /^import\s+type\s+\{[^}]*\}\s+from\s+['"][^'"]*['"];?\s*$/gm;
      content = content.replace(typeOnlyImports, (match) => {
        // Keep if types are actually used
        const typeNames = match.match(/\{\s*([^}]*)\s*\}/)?.[1]
          ?.split(',')
          .map(t => t.trim())
          .filter(Boolean) || [];
        
        const isUsed = typeNames.some(typeName => {
          const typeRegex = new RegExp(`\\b${typeName}\\b`, 'g');
          return typeRegex.test(content.replace(match, ''));
        });
        
        if (!isUsed) {
          hasChanges = true;
          return '';
        }
        return match;
      });

      // Remove duplicate imports
      const importLines = content.match(/^import\s+.*$/gm) || [];
      const uniqueImports = [...new Set(importLines)];
      if (importLines.length !== uniqueImports.length) {
        const nonImportContent = content.replace(/^import\s+.*$/gm, '');
        content = uniqueImports.join('\n') + '\n' + nonImportContent;
        hasChanges = true;
      }

      // Remove empty lines between imports
      content = content.replace(/^(import\s+.*)\n\n+(import\s+.*)/gm, '$1\n$2');

      if (hasChanges) {
        fs.writeFileSync(filePath, content);
        this.removedImports++;
        return true;
      }

      return false;
    } catch (error) {
      this.errors.push(`Error optimizing imports in ${filePath}: ${error.message}`);
      return false;
    }
  }

  // Optimize CSS files
  optimizeCSS(filePath) {
    try {
      let content = fs.readFileSync(filePath, 'utf8');
      const originalContent = content;
      let hasChanges = false;

      // Remove comments (keep license comments)
      content = content.replace(/\/\*(?!\s*!)([\s\S]*?)\*\//g, '');
      
      // Remove empty rules
      content = content.replace(/[^{}]*\{\s*\}/g, '');
      
      // Minify whitespace
      content = content
        .replace(/\s+/g, ' ')
        .replace(/;\s*}/g, '}')
        .replace(/\s*{\s*/g, '{')
        .replace(/;\s*/g, ';')
        .trim();

      if (content !== originalContent) {
        fs.writeFileSync(filePath, content);
        hasChanges = true;
      }

      return hasChanges;
    } catch (error) {
      this.errors.push(`Error optimizing CSS ${filePath}: ${error.message}`);
      return false;
    }
  }

  // Implement code splitting for large components
  implementCodeSplitting() {
    console.log('🔄 Implementing code splitting...');
    
    const largeDirs = [
      'components/admin',
      'components/models',
      'components/analytics',
      'components/extensions',
      'components/workflows'
    ];

    largeDirs.forEach(dir => {
      const dirPath = path.join(SRC_DIR, dir);
      if (!fs.existsSync(dirPath)) return;

      const indexPath = path.join(dirPath, 'index.ts');
      if (fs.existsSync(indexPath)) {
        let indexContent = fs.readFileSync(indexPath, 'utf8');
        
        // Convert direct exports to lazy exports for large components
        const lazyExportPattern = /^export \{ default as (\w+) \} from '\.\/(\w+)';$/gm;
        const lazyExports = [];
        
        indexContent = indexContent.replace(lazyExportPattern, (match, componentName, fileName) => {
          // Only make large components lazy
          const componentPath = path.join(dirPath, `${fileName}.tsx`);
          if (fs.existsSync(componentPath)) {
            const componentContent = fs.readFileSync(componentPath, 'utf8');
            // If component is large (>500 lines), make it lazy
            if (componentContent.split('\n').length > 500) {
              lazyExports.push(`export const ${componentName} = lazy(() => import('./${fileName}'));`);
              return '';
            }
          }
          return match;
        });

        if (lazyExports.length > 0) {
          const lazyImport = "import { lazy } from 'react';\n";
          indexContent = lazyImport + indexContent + '\n' + lazyExports.join('\n');
          fs.writeFileSync(indexPath, indexContent);
          console.log(`✅ Added lazy loading to ${lazyExports.length} components in ${dir}`);
        }
      }
    });
  }

  // Walk directory recursively
  walkDirectory(dirPath, callback) {
    const entries = fs.readdirSync(dirPath, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(dirPath, entry.name);

      if (entry.isDirectory() && !entry.name.startsWith('.') && entry.name !== 'node_modules') {
        this.walkDirectory(fullPath, callback);
      } else if (entry.isFile()) {
        callback(fullPath);
      }
    }
  }

  // Process all files
  processFiles() {
    console.log('🔧 Optimizing imports and CSS...');
    
    this.walkDirectory(SRC_DIR, (filePath) => {
      this.processedFiles++;
      
      if (/\.(tsx?|jsx?)$/.test(filePath)) {
        if (this.optimizeImports(filePath)) {
          this.optimizedFiles++;
        }
      } else if (/\.css$/.test(filePath)) {
        if (this.optimizeCSS(filePath)) {
          this.optimizedFiles++;
        }
      }
    });
  }

  // Generate optimized Tailwind config
  optimizeTailwindConfig() {
    console.log('🎨 Optimizing Tailwind configuration...');
    
    const tailwindConfigPath = path.join(__dirname, '../tailwind.config.ts');
    if (!fs.existsSync(tailwindConfigPath)) return;

    let config = fs.readFileSync(tailwindConfigPath, 'utf8');
    
    // Ensure purge is properly configured for production
    if (!config.includes('purge:') && !config.includes('content:')) {
      config = config.replace(
        /module\.exports\s*=\s*\{/,
        `module.exports = {
  content: [
    './src/**/*.{js,ts,jsx,tsx}',
    './src/components/**/*.{js,ts,jsx,tsx}',
    './src/app/**/*.{js,ts,jsx,tsx}',
  ],`
      );
    }

    // Add production optimizations
    if (!config.includes('safelist:')) {
      config = config.replace(
        /content:\s*\[[^\]]*\],/,
        `content: [
    './src/**/*.{js,ts,jsx,tsx}',
    './src/components/**/*.{js,ts,jsx,tsx}',
    './src/app/**/*.{js,ts,jsx,tsx}',
  ],
  safelist: [
    // Keep dynamic classes that might be generated
    'text-green-500',
    'text-red-500',
    'text-blue-500',
    'text-yellow-500',
    'bg-green-50',
    'bg-red-50',
    'bg-blue-50',
    'bg-yellow-50',
    'border-green-200',
    'border-red-200',
    'border-blue-200',
    'border-yellow-200',
  ],`
      );
    }

    fs.writeFileSync(tailwindConfigPath, config);
    console.log('✅ Tailwind configuration optimized');
  }

  // Update package.json scripts for production
  updatePackageScripts() {
    console.log('📦 Updating package.json scripts...');
    
    const packagePath = path.join(__dirname, '../package.json');
    const packageJson = JSON.parse(fs.readFileSync(packagePath, 'utf8'));

    // Add production optimization scripts
    packageJson.scripts = {
      ...packageJson.scripts,
      'build:production': 'npm run optimize:pre-build && next build && npm run optimize:post-build',
      'optimize:pre-build': 'node scripts/clean-development-artifacts.js && node scripts/optimize-css-js.js',
      'optimize:post-build': 'npm run analyze:bundle',
      'analyze:production': 'ANALYZE=true npm run build:production',
    };

    fs.writeFileSync(packagePath, JSON.stringify(packageJson, null, 2));
    console.log('✅ Package.json scripts updated');
  }

  // Generate optimization report
  generateReport() {
    console.log('\n📊 CSS/JS Optimization Report');
    console.log('================================');
    console.log(`Files processed: ${this.processedFiles}`);
    console.log(`Files optimized: ${this.optimizedFiles}`);
    console.log(`Imports removed: ${this.removedImports}`);
    console.log(`Success rate: ${((this.optimizedFiles / this.processedFiles) * 100).toFixed(1)}%`);
    
    if (this.errors.length > 0) {
      console.log('\n❌ Errors encountered:');
      this.errors.forEach(error => console.log(`  - ${error}`));
    }
    
    console.log('\n✅ CSS/JS optimization completed!');
  }

  // Run all optimizations
  run() {
    console.log('🚀 Starting CSS/JS optimization...\n');
    
    this.processFiles();
    this.implementCodeSplitting();
    this.optimizeTailwindConfig();
    this.updatePackageScripts();
    this.generateReport();
  }
}

// Run the optimizer
if (require.main === module) {
  const optimizer = new CSSJSOptimizer();
  optimizer.run();
}

module.exports = CSSJSOptimizer;